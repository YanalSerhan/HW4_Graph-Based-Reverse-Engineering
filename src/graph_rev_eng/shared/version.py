__version__ = "1.00"

def check_config_version(config: dict) -> bool:
    """Validates that config version matches the package version."""
    return config.get("version") == __version__
