"""
Configuration manager for the SDK.
"""

import json
import logging.config
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from .version import check_config_version

# Load environment variables from .env if present
load_dotenv()

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


class ConfigManager:
    """Manages application configuration, loading from JSON files and environment variables."""

    _instance = None

    def __init__(self):
        self._setup_data = self._load_json("setup.json")
        self._rate_limits_data = self._load_json("rate_limits.json")

        if not check_config_version(self._setup_data):
            raise ValueError("setup.json version mismatch")

        rate_limits = self._rate_limits_data.get("rate_limits", {})
        if not check_config_version(rate_limits):
            raise ValueError("rate_limits.json version mismatch")

        self._init_logging()

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Returns the singleton instance of the ConfigManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_json(self, filename: str) -> dict[str, Any]:
        filepath = CONFIG_DIR / filename
        if not filepath.exists():
            return {}
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    def _init_logging(self) -> None:
        logging_config = self._load_json("logging_config.json")
        if logging_config:
            logging.config.dictConfig(logging_config)

    def get_setup_version(self) -> str:
        """Returns the configured setup version."""
        return str(self._setup_data.get("version", "1.00"))

    def get_log_level(self) -> str:
        """Returns the configured log level."""
        return str(self._setup_data.get("log_level", "INFO"))

    def get_rate_limits(self, service: str = "default") -> dict[str, Any]:
        """Returns the rate limit configuration for the specified service."""
        return dict(
            self._rate_limits_data.get("rate_limits", {}).get("services", {}).get(service, {})
        )

    def get_api_key(self, key_name: str) -> str:
        """Retrieves an API key from the environment. Throws an error if empty or missing."""
        return os.environ.get(key_name, "")
