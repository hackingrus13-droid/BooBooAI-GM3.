from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "config.json"
PRIVATE_RULES = Path(__file__).resolve().parents[1] / "config" / "private_rules.local.json"


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {} if default is None else default.copy()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"configuration root must be an object: {path}")
    return data


def load_config(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or DEFAULT_CONFIG)


def load_private_rules() -> dict[str, Any]:
    # The contents are deliberately never logged or returned by diagnostics.
    return load_json(PRIVATE_RULES, {"rules": []})


def privacy_mode(config: dict[str, Any]) -> str:
    return str(config.get("privacy", {}).get("network_mode", "OFFLINE")).upper()


def permission(config: dict[str, Any], capability: str) -> str:
    return str(config.get("permissions", {}).get(capability, "DENY")).upper()
