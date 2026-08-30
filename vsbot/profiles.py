"""Multi-profile config storage (JSON, human-editable, no extra dependency).

Different characters/farm spots need different hunt regions, key layouts
and thresholds - a single flat config forces re-entering all of that every
time you switch. Profiles are just named JSON snapshots of a BotConfig.
"""

import json
import os

from .paths import data_path

PROFILES_DIR = data_path("profiles")


def _safe_name(name):
    cleaned = "".join(c for c in name.strip() if c.isalnum() or c in "-_ ")
    return cleaned.strip() or "profile"


def list_profiles():
    if not os.path.isdir(PROFILES_DIR):
        return []
    return sorted(
        os.path.splitext(f)[0] for f in os.listdir(PROFILES_DIR) if f.lower().endswith(".json")
    )


def save_profile(name, data: dict):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    safe = _safe_name(name)
    path = os.path.join(PROFILES_DIR, safe + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return safe


def load_profile(name):
    path = os.path.join(PROFILES_DIR, _safe_name(name) + ".json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_profile(name):
    path = os.path.join(PROFILES_DIR, _safe_name(name) + ".json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
