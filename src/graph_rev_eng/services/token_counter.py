"""
TokenCounter — counts and accumulates LLM token usage across a session.

Rationale: accurate token accounting is the only objective measure of the
graph-based retrieval efficiency advantage. Every LLM call must flow through
this counter so cost analysis in Phase 6 has ground-truth data.

Token estimation uses a character-based heuristic (÷ 4) when tiktoken is
unavailable, matching the ~4 chars/token average for English technical text.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN_ESTIMATE = 4


@dataclass
class TokenUsage:
    """Snapshot of token consumption for a single LLM invocation."""

    agent_name: str
    prompt_tokens: int
    completion_tokens: int
    model: str = "unknown"

    @property
    def total_tokens(self) -> int:
        """Sum of prompt and completion tokens."""
        return self.prompt_tokens + self.completion_tokens


class TokenCounter:
    """
    Tracks token usage per agent and accumulates session totals.

    Design: stateful accumulator — cleared only when reset() is called.
    This keeps a single TokenCounter alive across the entire agent pipeline
    so the final report has accurate totals.
    """

    def __init__(self) -> None:
        self._records: list[TokenUsage] = []
        self._lock = threading.Lock()

    def record(self, usage: TokenUsage) -> None:
        """Appends a TokenUsage record and logs the event."""
        with self._lock:
            self._records.append(usage)
        logger.info(
            "Token usage recorded: agent=%s model=%s prompt=%d completion=%d total=%d",
            usage.agent_name,
            usage.model,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimates token count for a text string.

        Tries tiktoken first (exact count); falls back to character heuristic
        so the service works without the optional dependency installed.
        """
        try:
            import tiktoken  # optional dependency

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)

    @property
    def total_prompt_tokens(self) -> int:
        """Sum of all prompt tokens recorded this session."""
        with self._lock:
            return sum(r.prompt_tokens for r in self._records)

    @property
    def total_completion_tokens(self) -> int:
        """Sum of all completion tokens recorded this session."""
        with self._lock:
            return sum(r.completion_tokens for r in self._records)

    @property
    def total_tokens(self) -> int:
        """Grand total of all tokens recorded this session."""
        return self.total_prompt_tokens + self.total_completion_tokens

    def by_agent(self, agent_name: str) -> list[TokenUsage]:
        """Returns all records for a named agent."""
        with self._lock:
            return [r for r in self._records if r.agent_name == agent_name]

    def summary(self) -> dict[str, int]:
        """Returns a dict summary of session-level token totals."""
        with self._lock:
            return {
                "total_prompt_tokens": sum(r.prompt_tokens for r in self._records),
                "total_completion_tokens": sum(r.completion_tokens for r in self._records),
                "total_tokens": sum(r.total_tokens for r in self._records),
                "call_count": len(self._records),
            }

    def reset(self) -> None:
        """Clears all accumulated records — use at session boundaries."""
        with self._lock:
            self._records.clear()
        logger.info("TokenCounter reset.")
