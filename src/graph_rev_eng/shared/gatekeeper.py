"""
API Gatekeeper module.
"""
import time
import logging
from collections import deque
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

class RateLimitConfig:
    """Configuration for rate limits."""
    def __init__(self, rpm: int, rph: int, concurrent: int, retry_after: int, max_retries: int):
        self.rpm = rpm
        self.rph = rph
        self.concurrent = concurrent
        self.retry_after = retry_after
        self.max_retries = max_retries

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RateLimitConfig":
        """Creates a RateLimitConfig from a dictionary."""
        return cls(
            rpm=data.get("requests_per_minute", 30),
            rph=data.get("requests_per_hour", 500),
            concurrent=data.get("concurrent_max", 5),
            retry_after=data.get("retry_after_seconds", 30),
            max_retries=data.get("max_retries", 3)
        )

class QueueStatus:
    """Status of the gatekeeper queue."""
    def __init__(self, queue_depth: int, backpressure: bool):
        self.queue_depth = queue_depth
        self.backpressure = backpressure

class ApiGatekeeper:
    """Gatekeeper to enforce rate limits and handle retries for API calls."""
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_timestamps_minute: deque = deque()
        self.request_timestamps_hour: deque = deque()
        self.max_queue_depth = 100
        self.queue_depth = 0

    def _cleanup_timestamps(self, current_time: float) -> None:
        """Removes expired timestamps from the tracking deques."""
        while self.request_timestamps_minute and current_time - self.request_timestamps_minute[0] > 60:
            self.request_timestamps_minute.popleft()
        while self.request_timestamps_hour and current_time - self.request_timestamps_hour[0] > 3600:
            self.request_timestamps_hour.popleft()

    def _wait_for_rate_limit(self) -> None:
        """Blocks execution until a request can be made without exceeding limits."""
        while True:
            current_time = time.time()
            self._cleanup_timestamps(current_time)
            if (len(self.request_timestamps_minute) < self.config.rpm and 
                len(self.request_timestamps_hour) < self.config.rph):
                break
            time.sleep(1)

    def execute(self, api_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Executes an API call safely, enforcing rate limits and retrying on failure."""
        if self.queue_depth >= self.max_queue_depth:
            raise Exception("Gatekeeper queue is full. Backpressure applied.")
            
        self.queue_depth += 1
        try:
            retries = 0
            while retries <= self.config.max_retries:
                self._wait_for_rate_limit()
                
                current_time = time.time()
                self.request_timestamps_minute.append(current_time)
                self.request_timestamps_hour.append(current_time)
                
                try:
                    # api_call is expected to return an object with token/cost attributes or a standard dict
                    response = api_call(*args, **kwargs)
                    
                    # Log metrics safely
                    model = getattr(response, "model", "unknown") if hasattr(response, "model") else "unknown"
                    inp_tok = getattr(response, "input_tokens", 0) if hasattr(response, "input_tokens") else 0
                    out_tok = getattr(response, "output_tokens", 0) if hasattr(response, "output_tokens") else 0
                    cost = getattr(response, "cost", 0.0) if hasattr(response, "cost") else 0.0
                    
                    logger.info(
                        "API Call Success",
                        extra={
                            "timestamp": current_time,
                            "model": model,
                            "input_tokens": inp_tok,
                            "output_tokens": out_tok,
                            "cost": cost,
                            "success": True
                        }
                    )
                    return response
                except Exception as e:
                    retries += 1
                    logger.warning(
                        "API Call Failed",
                        extra={
                            "timestamp": current_time,
                            "error": str(e),
                            "success": False
                        }
                    )
                    if retries > self.config.max_retries:
                        logger.error("Max retries exceeded.")
                        raise
                    time.sleep(self.config.retry_after)
        finally:
            self.queue_depth -= 1

    def get_queue_status(self) -> QueueStatus:
        """Returns the current queue status."""
        return QueueStatus(
            queue_depth=self.queue_depth,
            backpressure=self.queue_depth >= self.max_queue_depth
        )
