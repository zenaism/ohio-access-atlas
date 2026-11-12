"""Read browser-safe Google Places configuration for the public atlas maps."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def browser_api_key() -> str:
    value = os.environ.get("GOOGLE_MAPS_BROWSER_API_KEY", "").strip()
    if value:
        return value
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("GOOGLE_MAPS_BROWSER_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def matched_place_ids(records: dict) -> dict[str, str]:
    """Return matched IDs from either the IDs-only file or the legacy private cache."""
    ids = {}
    for link_id, record in records.items():
        if isinstance(record, str) and record:
            ids[link_id] = record
        elif isinstance(record, dict) and record.get("matched") and isinstance(record.get("google_id"), str):
            ids[link_id] = record["google_id"]
    return ids


def public_place_ids() -> dict[str, str]:
    ids_path = ROOT / "data/private/google_place_ids.json"
    if ids_path.exists():
        return matched_place_ids(json.loads(ids_path.read_text()).get("places", {}))
    legacy_path = ROOT / "data/private/google_accessibility.json"
    if legacy_path.exists():
        return matched_place_ids(json.loads(legacy_path.read_text()).get("places", {}))
    return {}
