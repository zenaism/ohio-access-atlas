"""Load, normalize, and join saved Google Places data for the public atlas maps."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOOGLE_PLACES_FILE = ROOT / "data/map/google_places_enriched.geojson"
PRIVATE_DETAILS_FILE = ROOT / "data/private/google_place_details.json"
LEGACY_DETAILS_FILE = ROOT / "data/private/google_accessibility.json"
PLACE_MATCH_CSV_FIELDS = (
    "region",
    "link_id",
    "name",
    "layer",
    "access_rating",
    "google_place_id",
    "atlas_feature_json",
)


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
    if LEGACY_DETAILS_FILE.exists():
        return matched_place_ids(json.loads(LEGACY_DETAILS_FILE.read_text()).get("places", {}))
    if GOOGLE_PLACES_FILE.exists():
        features = json.loads(GOOGLE_PLACES_FILE.read_text()).get("features", [])
        return {
            feature["properties"]["link_id"]: feature["properties"]["google_place_id"]
            for feature in features
            if feature.get("properties", {}).get("google_place_id")
        }
    return {}


def legacy_google_place(record: dict) -> dict | None:
    """Convert the old accessibility cache to the Places API detail shape."""
    place_id = record.get("google_id")
    if not record.get("matched") or not isinstance(place_id, str):
        return None
    accessibility = record.get("accessibility") or {}
    fields = {
        "hasWheelchairAccessibleEntrance": "wheelchairAccessibleEntrance",
        "hasWheelchairAccessibleRestroom": "wheelchairAccessibleRestroom",
        "hasWheelchairAccessibleParking": "wheelchairAccessibleParking",
        "hasWheelchairAccessibleSeating": "wheelchairAccessibleSeating",
    }
    return {
        "id": place_id,
        "displayName": {"text": record.get("google_name", "")},
        "googleMapsUri": record.get("url"),
        "accessibilityOptions": {
            api_field: accessibility[legacy_field]
            for api_field, legacy_field in fields.items()
            if legacy_field in accessibility
        },
        "legacyMatchDistanceMeters": record.get("distance_m"),
    }


def saved_google_place_details(place_ids: dict[str, str]) -> dict[str, dict]:
    """Load saved details, preferring API responses over the legacy accessibility cache."""
    details: dict[str, dict] = {}
    if GOOGLE_PLACES_FILE.exists():
        features = json.loads(GOOGLE_PLACES_FILE.read_text()).get("features", [])
        for feature in features:
            properties = feature.get("properties", {})
            link_id = properties.get("link_id")
            detail = properties.get("google_place")
            if (
                link_id in place_ids
                and properties.get("google_place_id") == place_ids[link_id]
                and isinstance(detail, dict)
                and detail.get("id") == place_ids[link_id]
            ):
                details[link_id] = detail
    if PRIVATE_DETAILS_FILE.exists():
        records = json.loads(PRIVATE_DETAILS_FILE.read_text()).get("places", {})
        for link_id, detail in records.items():
            if (
                link_id in place_ids
                and isinstance(detail, dict)
                and detail.get("id") == place_ids[link_id]
            ):
                details[link_id] = detail
    if LEGACY_DETAILS_FILE.exists():
        records = json.loads(LEGACY_DETAILS_FILE.read_text()).get("places", {})
        for link_id, record in records.items():
            if link_id not in place_ids or record.get("google_id") != place_ids[link_id]:
                continue
            details.setdefault(link_id, legacy_google_place(record))
    return {link_id: detail for link_id, detail in details.items() if detail is not None}


def enrich_google_places(
    data: dict,
    place_ids: dict[str, str],
    details: dict[str, dict],
) -> dict:
    """Attach matched IDs and saved Google details to Atlas features."""
    for collection in data.values():
        for feature in collection["features"]:
            properties = feature["properties"]
            link_id = properties["link_id"]
            place_id = place_ids.get(link_id)
            if not place_id:
                continue
            properties["google_place_id"] = place_id
            detail = details.get(link_id)
            if detail and detail.get("id") == place_id:
                properties["google_place"] = detail
    return data


def place_match_rows(data: dict, place_ids: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for region, collection in data.items():
        for feature in collection["features"]:
            properties = feature["properties"]
            place_id = place_ids.get(properties["link_id"])
            if not place_id:
                continue
            rows.append(
                {
                    "region": region,
                    "link_id": properties["link_id"],
                    "name": properties.get("name", ""),
                    "layer": properties.get("layer", ""),
                    "access_rating": properties.get("access_rating", ""),
                    "google_place_id": place_id,
                    "atlas_feature_json": json.dumps(
                        feature, ensure_ascii=False, separators=(",", ":")
                    ),
                }
            )
    return rows
