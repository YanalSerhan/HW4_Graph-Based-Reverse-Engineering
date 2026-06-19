"""
Tests for token_experiment.py
"""
import os
from unittest.mock import patch, MagicMock
import graph_rev_eng.services.token_experiment as te

def test_reduction_calculation(tmp_path):
    def mock_call_openai(prompt):
        if "Codebase:" in prompt:
            return 100, 200
        else:
            return 50, 150
            
    # Create dummy files for rglob and exists to find
    dummy_py = tmp_path / "dummy.py"
    dummy_py.write_text("dummy", encoding="utf-8")

    with patch("graph_rev_eng.services.token_experiment.call_openai", side_effect=mock_call_openai), \
         patch("graph_rev_eng.services.token_experiment.Path.write_text") as mock_write, \
         patch("graph_rev_eng.services.token_experiment.Path.rglob", return_value=[dummy_py]), \
         patch("graph_rev_eng.services.token_experiment.Path.exists", return_value=True), \
         patch("graph_rev_eng.services.token_experiment.Path.read_text", return_value="dummy content"):
        
        te.main()
        
        mock_write.assert_called_once()
        content = mock_write.call_args[0][0]
        
        assert "| Naive RAG | 100 | 200 | 300 | $0.000135 |" in content
        assert "| Graph-guided | 50 | 150 | 200 | $0.000097 |" in content
        assert "50.0%" in content
        assert "25.0%" in content
        assert "33.3%" in content
        assert "27.8%" in content

def test_call_openai():
    # Test call_openai with a mocked urlopen
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"usage": {"prompt_tokens": 10, "completion_tokens": 20}}'
    mock_response.__enter__.return_value = mock_response
    
    with patch.dict(os.environ, {"LLM_API_KEY": "sk-test"}), \
         patch("urllib.request.urlopen", return_value=mock_response):
        in_toks, out_toks = te.call_openai("Hello")
        assert in_toks == 10
        assert out_toks == 20

import urllib.error
import pytest

def test_call_openai_httperror():
    # Test call_openai HTTPError handling
    mock_error = urllib.error.HTTPError(url="", code=400, msg="Bad Request", hdrs=None, fp=MagicMock())
    mock_error.read.return_value = b"Custom error message"
    
    with patch.dict(os.environ, {"LLM_API_KEY": "sk-test"}), \
         patch("urllib.request.urlopen", side_effect=mock_error):
        with pytest.raises(urllib.error.HTTPError):
            te.call_openai("Hello")
