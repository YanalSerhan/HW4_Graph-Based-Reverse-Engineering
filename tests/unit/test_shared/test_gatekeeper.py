from unittest.mock import MagicMock

import pytest

from graph_rev_eng.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


def test_gatekeeper_success():
    config = RateLimitConfig(rpm=10, rph=100, concurrent=5, retry_after=0, max_retries=1)
    gatekeeper = ApiGatekeeper(config)
    mock_api = MagicMock(return_value={"status": "ok"})

    result = gatekeeper.execute(mock_api)
    assert result == {"status": "ok"}
    assert mock_api.call_count == 1

def test_gatekeeper_retries_and_fails():
    config = RateLimitConfig(rpm=10, rph=100, concurrent=5, retry_after=0, max_retries=2)
    gatekeeper = ApiGatekeeper(config)
    mock_api = MagicMock(side_effect=Exception("API Error"))

    with pytest.raises(Exception, match="API Error"):
        gatekeeper.execute(mock_api)

    assert mock_api.call_count == 3

def test_gatekeeper_backpressure():
    config = RateLimitConfig(rpm=10, rph=100, concurrent=5, retry_after=0, max_retries=1)
    gatekeeper = ApiGatekeeper(config)
    gatekeeper.queue_depth = 100

    with pytest.raises(Exception, match="Gatekeeper queue is full"):
        gatekeeper.execute(MagicMock())

def test_gatekeeper_queue_status():
    config = RateLimitConfig(rpm=10, rph=100, concurrent=5, retry_after=0, max_retries=1)
    gatekeeper = ApiGatekeeper(config)
    gatekeeper.queue_depth = 5
    status = gatekeeper.get_queue_status()
    assert status.queue_depth == 5
    assert not status.backpressure

def test_config_from_dict():
    config = RateLimitConfig.from_dict({"requests_per_minute": 50})
    assert config.rpm == 50
    assert config.rph == 500
