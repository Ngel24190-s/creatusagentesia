"""Centralized logging for NosVers Agent Ecosystem."""

import os
import logging
from agents.config_loader import load_config


_logger = None


def get_logger(name: str = "nosvers") -> logging.Logger:
    """Get or create the shared logger."""
    global _logger
    if _logger is not None:
        return _logger.getChild(name) if name != "nosvers" else _logger

    config = load_config()
    log_cfg = config.get("logging", {})
    log_level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    log_file = log_cfg.get("log_file", "logs/nosvers_agents.log")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(log_file):
        log_file = os.path.join(base_dir, log_file)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    _logger = logging.getLogger("nosvers")
    _logger.setLevel(log_level)

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(log_level)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    _logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(
        "[%(name)s] %(levelname)s: %(message)s"
    ))
    _logger.addHandler(ch)

    return _logger.getChild(name) if name != "nosvers" else _logger
