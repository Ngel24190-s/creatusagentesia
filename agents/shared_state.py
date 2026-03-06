"""Shared state manager for inter-agent communication."""

import os
import json
from datetime import datetime, timezone
from agents.config_loader import load_config


def _state_path() -> str:
    config = load_config()
    state_file = config.get("paths", {}).get("shared_state", "shared_state.json")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(state_file):
        state_file = os.path.join(base_dir, state_file)
    return state_file


def _default_state() -> dict:
    return {
        "last_run": None,
        "content_audit": {"status": "pending", "report": None},
        "media_audit": {"status": "pending", "report": None},
        "social_queue": {"status": "draft", "posts": None},
        "blockers": [],
    }


def load_state() -> dict:
    """Load shared state from JSON file, or return default."""
    path = _state_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            # Corrupt state file — back it up and start fresh
            backup = path + ".corrupt"
            os.replace(path, backup)
            return _default_state()
    return _default_state()


def save_state(state: dict, update_timestamp: bool = True):
    """Persist shared state to JSON file."""
    path = _state_path()
    if update_timestamp:
        state["last_run"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def update_section(section: str, **kwargs):
    """Update a specific section of the shared state."""
    state = load_state()
    if section not in state:
        state[section] = {}
    state[section].update(kwargs)
    save_state(state)


def add_blocker(description: str, agent: str):
    """Add a blocker that requires human attention."""
    state = load_state()
    if "blockers" not in state or not isinstance(state["blockers"], list):
        state["blockers"] = []
    state["blockers"].append({
        "description": description,
        "agent": agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_state(state)


def clear_blockers():
    """Clear all resolved blockers."""
    state = load_state()
    state["blockers"] = []
    save_state(state, update_timestamp=False)
