import time

import pytest

from graph_rev_eng.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


def test_gatekeeper_backpressure():
    config = RateLimitConfig(rpm=10, rph=100, concurrent=5, retry_after=1, max_retries=1)
    gatekeeper = ApiGatekeeper(config)

    def dummy_api_call():
        return type(
            "Response",
            (),
            {
                "text": "Success",
                "model": "test",
                "input_tokens": 10,
                "output_tokens": 10,
            },
        )()

    res = gatekeeper.execute(dummy_api_call)
    assert res.text == "Success"

    gatekeeper.queue_depth = gatekeeper.max_queue_depth
    with pytest.raises(Exception, match="Gatekeeper queue is full"):
        gatekeeper.execute(dummy_api_call)

def test_gatekeeper_rate_limit_wait(monkeypatch):
    config = RateLimitConfig(rpm=1, rph=10, concurrent=1, retry_after=1, max_retries=1)
    gatekeeper = ApiGatekeeper(config)

    sleeps = []
    def mock_sleep(s):
        sleeps.append(s)
        gatekeeper.request_timestamps_minute.popleft()

    monkeypatch.setattr(time, "sleep", mock_sleep)

    def dummy_api_call():
        return type("Response", (), {"text": "Success"})()

    gatekeeper.execute(dummy_api_call)
    assert len(gatekeeper.request_timestamps_minute) == 1

    gatekeeper.execute(dummy_api_call)
    assert len(sleeps) == 1
