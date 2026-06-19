"""
Tests for OpenAILLM.
"""

from unittest.mock import MagicMock, patch

from graph_rev_eng.services.llm import OpenAILLM


def test_llm_empty_api_key():
    gatekeeper = MagicMock()
    llm = OpenAILLM(gatekeeper, api_key="")

    res = llm("Hello")
    assert "[STUB] Missing API Key" in res


def test_llm_successful_response():
    gatekeeper = MagicMock()
    gatekeeper.execute.side_effect = lambda func: func()
    llm = OpenAILLM(gatekeeper, api_key="sk-fake")

    mock_response = MagicMock()
    mock_response.read.return_value = (
        b'{"choices": [{"message": {"content": "mocked response"}}], '
        b'"usage": {"prompt_tokens": 10, "completion_tokens": 20}}'
    )
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = llm("Hello")

    assert res == "mocked response"


def test_llm_routes_through_gatekeeper():
    gatekeeper = MagicMock()
    # We want the gatekeeper to just return what we give it
    gatekeeper.execute.side_effect = lambda func: func()

    llm = OpenAILLM(gatekeeper, api_key="sk-fake")

    mock_response = MagicMock()
    mock_response.read.return_value = (
        b'{"choices": [{"message": {"content": "gatekeeper test"}}], '
        b'"usage": {"prompt_tokens": 1, "completion_tokens": 1}}'
    )
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = llm("Hello")

    assert res == "gatekeeper test"
    gatekeeper.execute.assert_called_once()
