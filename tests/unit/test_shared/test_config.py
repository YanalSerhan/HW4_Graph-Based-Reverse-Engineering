"""
Tests for config.py
"""
import os
import json
from unittest.mock import patch
import pytest

from graph_rev_eng.shared.config import ConfigManager

def test_config_value_loading(tmp_path):
    # Mock CONFIG_DIR
    setup_data = {"version": "1.00", "log_level": "DEBUG"}
    rate_limits_data = {"rate_limits": {"version": "1.00", "services": {"default": {"rpm_limit": 50}}}}
    
    (tmp_path / "setup.json").write_text(json.dumps(setup_data), encoding="utf-8")
    (tmp_path / "rate_limits.json").write_text(json.dumps(rate_limits_data), encoding="utf-8")
    
    with patch("graph_rev_eng.shared.config.CONFIG_DIR", tmp_path), \
         patch.dict(os.environ, {"LLM_API_KEY": "env_key"}, clear=True):
        
        # We need to bypass singleton pattern for tests or reset it
        ConfigManager._instance = None
        manager = ConfigManager.get_instance()
        
        # Test loading a value that exists in setup
        assert manager.get_log_level() == "DEBUG"
        
        # Test loading a value with default fallback (e.g. get_setup_version fallback)
        manager._setup_data = {}
        assert manager.get_log_level() == "INFO"
        assert manager.get_setup_version() == "1.00"
        
        # Test get_rate_limits
        assert manager.get_rate_limits() == {"rpm_limit": 50}
        
        # Test get_api_key from env
        assert manager.get_api_key("LLM_API_KEY") == "env_key"

def test_config_version_mismatch(tmp_path):
    setup_data = {"version": "99.99.99"} # Mismatched version
    rate_limits_data = {"rate_limits": {"version": "1.00"}}
    
    (tmp_path / "setup.json").write_text(json.dumps(setup_data), encoding="utf-8")
    (tmp_path / "rate_limits.json").write_text(json.dumps(rate_limits_data), encoding="utf-8")
    
    with patch("graph_rev_eng.shared.config.CONFIG_DIR", tmp_path):
        ConfigManager._instance = None
        with pytest.raises(ValueError, match="setup.json version mismatch"):
            ConfigManager.get_instance()
