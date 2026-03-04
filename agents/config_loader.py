"""Configuration loader for NosVers Agent Ecosystem."""

import os
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    """Load YAML configuration file."""
    # Resolve relative to project root
    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Copy config.yaml.example to config.yaml and fill in your values."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _ensure_dirs(config)
    return config


def _ensure_dirs(config: dict):
    """Create required directories if they don't exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = config.get("paths", {})
    for key in ("reports_dir", "logs_dir", "content_seeds_dir"):
        dir_path = paths.get(key, "")
        if dir_path:
            full_path = os.path.join(base_dir, dir_path)
            os.makedirs(full_path, exist_ok=True)
