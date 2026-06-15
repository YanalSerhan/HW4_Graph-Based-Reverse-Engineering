"""
Configuration manager for the SDK.
"""
import json
import os
from pathlib import Path

def load_setup_config() -> dict:
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "setup.json"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_rate_limits() -> dict:
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "rate_limits.json"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
