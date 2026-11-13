"""Match existing atlas places, save Google Places details, and refresh the same map pages."""

from __future__ import annotations

import json
import math
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "data/private"
URL = "https://places.googleapis.com/v1/places:searchText"
MASK = "places.id,places.displayName,places.location"
DETAILS_URL = "https://places.googleapis.com/v1/places/{}"
DETAILS_MASK = "id,displayName,formattedAddress,googleMapsUri,accessibilityOptions,attributions"
DETAILS_FILE = PRIVATE / "google_place_details.json"
CITY = {"cincinnati": "Cincinnati, OH", "oxford": "Oxford, OH"}


def key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("GOOGLE_MAPS_API_KEY=") and line.split("=", 1)[1].strip():
            return line.split("=", 1)[1].strip()
    sys.exit("GOOGLE_MAPS_API_KEY missing in .env")


def metres(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371008.8 * math.asin(math.sqrt(a))


STOP = {
    "the",
    "of",
    "and",
    "at",
    "a",
    "cincinnati",
    "oxford",
    "ohio",
    "oh",
    "inc",
    "llc",
    "co",
    "center",
    "hall",
    "park",
    "saint",
    "st",
    "cafe",
    "building",
    "company",
}


def same_name(a: str, b: str) -> bool:
    """Share at least one distinctive word (catches 'McKie Field Building' vs 'Hayden Park')."""
    import re

    def words(s: str) -> set[str]:
        return {
            w[:5]
            for w in re.findall(r"[a-z0-9]+", s.lower().replace("’", "'"))
            if w not in STOP and len(w) > 2
        }

    return bool(words(a) & words(b)) or a.lower() in b.lower() or b.lower() in a.lower()


def search(k: str, name: str, region: str, lat: float, lon: float) -> dict:
    body = {
        "textQuery": f"{name}, {CITY[region]}",
        "pageSize": 1,
        "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": 300.0}},
    }
    r = requests.post(
        URL,
        json=body,
        timeout=30,
        headers={"X-Goog-Api-Key": k, "X-Goog-FieldMask": MASK, "Content-Type": "application/json"},
    )
    if r.status_code != 200:
        raise SystemExit(f"Google returned {r.status_code}: {r.text[:300]}")
    time.sleep(0.1)
    return r.json()


def fetch() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from atlas.google_places import public_place_ids

    existing = public_place_ids()
    ids_file = PRIVATE / "google_place_ids.json"
    if ids_file.exists():
        checked = set(json.loads(ids_file.read_text()).get("checked", []))
    else:
        legacy_file = PRIVATE / "google_accessibility.json"
        checked = (
            set(json.loads(legacy_file.read_text()).get("places", {}))
            if legacy_file.exists()
            else set()
        )
    checked.update(existing)
    k, out, calls = key(), {}, 0
    for region in ("cincinnati", "oxford"):
        for f in json.loads((ROOT / f"data/map/{region}_atlas.geojson").read_text())["features"]:
            p, g = f["properties"], f["geometry"]
            if p["layer"] in ("restroom", "trail", "event") or g["type"] != "Point":
                continue
            link_id = p["link_id"]
            if link_id in existing:
                out[link_id] = existing[link_id]
                continue
            if link_id in checked:
                continue
            lon, lat = g["coordinates"]
            res = (search(k, p["name"], region, lat, lon).get("places") or [None])[0]
            calls += 1
            checked.add(link_id)
            if res:
                d = metres(lat, lon, res["location"]["latitude"], res["location"]["longitude"])
                if d <= 150 and same_name(p["name"], res["displayName"]["text"]):
                    out[link_id] = res["id"]
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (PRIVATE / "google_place_ids.json").write_text(
        json.dumps(
            {
                "fetched": date.today().isoformat(),
                "note": "Matched Place IDs are stored here; details are cached privately and exported with the Atlas map.",
                "places": out,
                "checked": sorted(checked),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"{calls} new places looked up; {len(out)} matched within 150 m.")
    return out


def fetch_place_details(
    k: str,
    place_ids: dict[str, str],
    max_requests: int | None = None,
) -> tuple[dict[str, dict], list[str], list[tuple[str, int | str]]]:
    """Fetch and persist detail responses, resuming from the private cache when possible."""
    cache = json.loads(DETAILS_FILE.read_text()) if DETAILS_FILE.exists() else {}
    records = cache.get("places", {})
    requests_made = 0
    failures = []
    for link_id, place_id in place_ids.items():
        existing = records.get(link_id)
        if isinstance(existing, dict) and existing.get("id") == place_id:
            continue
        if max_requests is not None and requests_made >= max_requests:
            break
        response = requests.get(
            DETAILS_URL.format(place_id),
            timeout=30,
            headers={"X-Goog-Api-Key": k, "X-Goog-FieldMask": DETAILS_MASK},
        )
        requests_made += 1
        if response.status_code != 200:
            failures.append((link_id, response.status_code))
            time.sleep(0.1)
            continue
        detail = response.json()
        if detail.get("id") != place_id:
            failures.append((link_id, "Place ID mismatch"))
            time.sleep(0.1)
            continue
        records[link_id] = detail
        DETAILS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary = DETAILS_FILE.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"fetched": date.today().isoformat(), "field_mask": DETAILS_MASK, "places": records},
                indent=2,
                ensure_ascii=False,
            )
        )
        temporary.replace(DETAILS_FILE)
        time.sleep(0.1)
    unresolved = [
        link_id
        for link_id, place_id in place_ids.items()
        if not isinstance(records.get(link_id), dict) or records[link_id].get("id") != place_id
    ]
    return records, unresolved, failures


if __name__ == "__main__":
    if "--areas" in sys.argv:
        raise SystemExit(
            "--areas is no longer supported; Google matches are for places already on the atlas."
        )
    google = fetch()
    details, unresolved, failures = fetch_place_details(key(), google)
    print(f"Saved Google Places details for {len(google) - len(unresolved)} of {len(google)} matches.")
    if unresolved:
        print(f"{len(unresolved)} matches remain without full Place Details.")
    if failures:
        summary = ", ".join(f"{link_id} ({status})" for link_id, status in failures)
        print(f"Google Place Details failed for {len(failures)} match(es): {summary}")
    sys.path.insert(0, str(ROOT / "src"))
    from atlas.export_map import write

    pages = [path for path in write() if path.name in {"cincinnati.html", "oxford.html", "index.html"}]
    print(f"Updated existing map pages with {len(details)} saved Google detail records.")
    for page in pages:
        print(page.relative_to(ROOT))
    if failures:
        raise SystemExit(1)
