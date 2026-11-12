"""PRIVATE, LOCAL ONLY: Google Places accessibility for our places, plus a private copy of the map.

Google's terms do not allow storing Places content (except place IDs) or showing it on a
non-Google map. Everything this script writes goes to data/private/, which is git-ignored and
must never be committed or published. The public map in data/map/ is not touched.

  1. For each place on the map (not restrooms, trails or events), one Text Search request with
     a location bias at our point; the match is accepted only within 150 m.
     Responses are cached in data/private/raw/ so reruns cost nothing.
  2. data/private/google_accessibility.json: Google's four wheelchair fields per place.
  3. data/private/map/<region>.html and <region>_atlas.geojson: the map with Google's answers
     added as facts (source "Google Maps"), for local viewing only.

Needs GOOGLE_MAPS_API_KEY in .env.
"""

from __future__ import annotations

import hashlib
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
MASK = "places.id,places.displayName,places.location,places.accessibilityOptions,places.googleMapsUri"
FIELDS = {
    "wheelchairAccessibleEntrance": ("Step-free entrance", "entrance_step_free"),
    "wheelchairAccessibleRestroom": ("Accessible restroom", "restroom_accessible"),
    "wheelchairAccessibleParking": ("Accessible parking", "accessible_parking"),
    "wheelchairAccessibleSeating": ("Wheelchair seating", "accessible_seating"),
}
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
    cache = (
        PRIVATE
        / "raw"
        / (hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:20] + ".json")
    )
    if cache.exists():
        return json.loads(cache.read_text())
    r = requests.post(
        URL,
        json=body,
        timeout=30,
        headers={"X-Goog-Api-Key": k, "X-Goog-FieldMask": MASK, "Content-Type": "application/json"},
    )
    if r.status_code != 200:
        raise SystemExit(f"Google returned {r.status_code}: {r.text[:300]}")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(r.text)
    time.sleep(0.1)
    return r.json()


def fetch() -> dict:
    k, out, calls = key(), {}, 0
    for region in ("cincinnati", "oxford"):
        for f in json.loads((ROOT / f"data/map/{region}_atlas.geojson").read_text())["features"]:
            p, g = f["properties"], f["geometry"]
            if p["layer"] in ("restroom", "trail", "event") or g["type"] != "Point":
                continue
            lon, lat = g["coordinates"]
            res = (search(k, p["name"], region, lat, lon).get("places") or [None])[0]
            calls += 1
            rec = {"name": p["name"], "region": region, "matched": False}
            if res:
                d = metres(lat, lon, res["location"]["latitude"], res["location"]["longitude"])
                rec.update(
                    google_name=res["displayName"]["text"],
                    distance_m=round(d),
                    google_id=res["id"],
                    url=res.get("googleMapsUri"),
                    accessibility=res.get("accessibilityOptions") or {},
                )
                rec["matched"] = d <= 150 and same_name(p["name"], rec["google_name"])
            out[p["link_id"]] = rec
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (PRIVATE / "google_accessibility.json").write_text(
        json.dumps(
            {
                "fetched": date.today().isoformat(),
                "note": "PRIVATE: Google Places content; do not commit or publish.",
                "places": out,
            },
            indent=1,
            ensure_ascii=False,
        )
    )
    m = [r for r in out.values() if r["matched"]]
    print(
        f"{calls} places looked up; {len(m)} matched within 150 m; "
        f"{sum(bool(r['accessibility']) for r in m)} with accessibility answers"
    )
    return out


def private_map(google: dict) -> None:
    """Copy of the public map with Google's answers added as facts; rating and key line recomputed."""
    sys.path.insert(0, str(ROOT / "src"))
    import pandas as pd

    from atlas.export_map import LABEL_TO_ATTR, key_facts, rate, summarise
    from atlas.map_viewer import render

    out_dir = PRIVATE / "map"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = {}
    for region in ("cincinnati", "oxford"):
        fc = json.loads((ROOT / f"data/map/{region}_atlas.geojson").read_text())
        for f in fc["features"]:
            p = f["properties"]
            gr = google.get(p["link_id"])
            if not gr or not gr["matched"] or not gr.get("accessibility"):
                continue
            for field, (label, _attr) in FIELDS.items():
                if field in gr["accessibility"]:
                    p["facts"].append(
                        {
                            "attribute": label,
                            "value": "yes" if gr["accessibility"][field] else "no",
                            "detail": "Google Maps (private copy)",
                            "quote": "",
                            "source": gr.get("url") or "",
                            "date": google.get("_fetched", date.today().isoformat())[:7],
                        }
                    )
            rows = [
                (LABEL_TO_ATTR.get(x["attribute"], x["attribute"]), str(x["value"]).split(";")[-1])
                for x in p["facts"]
            ]
            new = rate(pd.DataFrame(rows, columns=["attribute", "value"]))
            # Google can fill in or upgrade a rating; it never downgrades one our sources support
            if p["access_rating"] == "unknown" or new == "accessible":
                p["access_rating"] = new
            p.pop("summary_text", None)
            p["summary"] = summarise(p)
            p["keys"] = key_facts(p)
        (out_dir / f"{region}_atlas.geojson").write_text(json.dumps(fc, ensure_ascii=False))
        data[region] = fc
        title = f"{region.title()} accessibility map (PRIVATE, with Google data)"
        (out_dir / f"{region}.html").write_text(render({region: fc}, title, " · private copy, do not share"))
    print(f"private map written to {out_dir.relative_to(ROOT)}/ (git-ignored)")


if __name__ == "__main__":
    g = fetch()
    private_map(g)
