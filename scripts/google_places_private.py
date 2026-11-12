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


def private_map(google: dict, extra: dict | None = None) -> None:
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
        for gid, n in (extra or {}).items():
            if n["region"] != region:
                continue
            facts = [
                {
                    "attribute": label,
                    "value": "yes" if n["accessibility"][field] else "no",
                    "detail": "Google Maps (private copy)",
                    "quote": "",
                    "source": n["url"] or "",
                    "date": date.today().isoformat()[:7],
                }
                for field, (label, _a) in FIELDS.items()
                if field in n["accessibility"]
            ]
            props = {
                "name": n["name"],
                "layer": LAYER.get(n["type"] or "", "food_drink"),
                "facts": facts,
                "matched_to": f"google:{gid} ({n['name']})",
                "region": region,
                "contacts": {"emails": [], "phones": []},
                "link_id": "g-" + gid[-10:].lower(),
                "newest_source": date.today().isoformat()[:7],
                "details": {"address": n["address"], "sources": {"address": "Google Maps"}},
            }
            rows = [(LABEL_TO_ATTR.get(x["attribute"], x["attribute"]), x["value"]) for x in facts]
            props["access_rating"] = rate(pd.DataFrame(rows, columns=["attribute", "value"]))
            props["summary"] = summarise(props)
            props["keys"] = key_facts(props)
            fc["features"].append(
                {
                    "type": "Feature",
                    "id": f"{region}:g{gid}",
                    "geometry": {"type": "Point", "coordinates": [n["lon"], n["lat"]]},
                    "properties": props,
                }
            )
        (out_dir / f"{region}_atlas.geojson").write_text(json.dumps(fc, ensure_ascii=False))
        data[region] = fc
        title = f"{region.title()} accessibility map (PRIVATE, with Google data)"
        (out_dir / f"{region}.html").write_text(render({region: fc}, title, " · private copy, do not share"))
    print(f"private map written to {out_dir.relative_to(ROOT)}/ (git-ignored)")


# ---------------------------------------------------------------- area searches ----
# Places we do not have yet, in the areas people ask about. One request per query (no paging),
# accessibility tier only; well under the daily quota.
AREA_QUERIES = [
    ("cincinnati", "coffee shop in Over-the-Rhine, Cincinnati"),
    ("cincinnati", "restaurant in Over-the-Rhine, Cincinnati"),
    ("cincinnati", "bar in Over-the-Rhine, Cincinnati"),
    ("cincinnati", "brewery in Over-the-Rhine, Cincinnati"),
    ("cincinnati", "Findlay Market vendors, Cincinnati"),
    ("cincinnati", "coffee shop in downtown Cincinnati"),
    ("cincinnati", "restaurant in downtown Cincinnati"),
    ("cincinnati", "hotel in downtown Cincinnati"),
    ("cincinnati", "pharmacy in downtown Cincinnati"),
    ("cincinnati", "grocery store in Cincinnati"),
    ("cincinnati", "restaurant in Northside, Cincinnati"),
    ("cincinnati", "brewery in Northside, Cincinnati"),
    ("cincinnati", "coffee shop in Northside, Cincinnati"),
    ("cincinnati", "restaurant on Ludlow Avenue, Clifton, Cincinnati"),
    ("cincinnati", "coffee shop in Clifton, Cincinnati"),
    ("cincinnati", "Skyline Chili Ludlow Avenue Cincinnati"),
    ("cincinnati", "restaurant in Hyde Park, Cincinnati"),
    ("cincinnati", "restaurant in Mount Adams, Cincinnati"),
    ("cincinnati", "restaurant at The Banks, Cincinnati"),
    ("oxford", "restaurant in Uptown Oxford, Ohio"),
    ("oxford", "coffee shop in Oxford, Ohio"),
    ("oxford", "bar in Uptown Oxford, Ohio"),
    ("oxford", "hotel in Oxford, Ohio"),
    ("oxford", "pharmacy in Oxford, Ohio"),
    ("oxford", "grocery store in Oxford, Ohio"),
]
AREA_MASK = MASK + ",places.primaryType,places.formattedAddress"
LAYER = {
    "lodging": "lodging",
    "hotel": "lodging",
    "pharmacy": "service",
    "drugstore": "service",
    "grocery_store": "service",
    "supermarket": "service",
    "convenience_store": "service",
}


def area_search(k: str, query: str) -> list[dict]:
    body = {"textQuery": query, "pageSize": 20}
    cache = (
        PRIVATE
        / "raw"
        / ("area-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:20] + ".json")
    )
    if cache.exists():
        return json.loads(cache.read_text()).get("places", [])
    r = requests.post(
        URL,
        json=body,
        timeout=30,
        headers={"X-Goog-Api-Key": k, "X-Goog-FieldMask": AREA_MASK, "Content-Type": "application/json"},
    )
    if r.status_code != 200:
        raise SystemExit(f"Google returned {r.status_code} for {query!r}: {r.text[:300]}")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(r.text)
    time.sleep(0.2)
    return r.json().get("places", [])


def new_places(google: dict) -> dict:
    """Places from area searches that are not on our map yet and have accessibility answers."""
    sys.path.insert(0, str(ROOT / "src"))
    from shapely.geometry import Point

    from atlas.core import area

    k, known_ids = key(), {v.get("google_id") for v in google.values() if v.get("matched")}
    ours = []
    for region in ("cincinnati", "oxford"):
        for f in json.loads((ROOT / f"data/map/{region}_atlas.geojson").read_text())["features"]:
            if f["geometry"]["type"] == "Point":
                lon, lat = f["geometry"]["coordinates"]
                ours.append((f["properties"]["name"], lat, lon))
    found = {}
    for region, q in AREA_QUERIES:
        for res in area_search(k, q):
            loc = res["location"]
            if res["id"] in known_ids or res["id"] in found or not res.get("accessibilityOptions"):
                continue
            if not area(region).contains(Point(loc["longitude"], loc["latitude"])):
                continue
            name = res["displayName"]["text"]
            if any(
                metres(lat, lon, loc["latitude"], loc["longitude"]) < 40 and same_name(n, name)
                for n, lat, lon in ours
            ):
                continue  # already on our map under another source
            found[res["id"]] = {
                "name": name,
                "region": region,
                "lat": loc["latitude"],
                "lon": loc["longitude"],
                "type": res.get("primaryType"),
                "address": res.get("formattedAddress"),
                "url": res.get("googleMapsUri"),
                "accessibility": res["accessibilityOptions"],
                "query": q,
            }
    (PRIVATE / "google_new_places.json").write_text(
        json.dumps(
            {
                "fetched": date.today().isoformat(),
                "note": "PRIVATE: Google Places content; do not commit or publish.",
                "queries": len(AREA_QUERIES),
                "places": found,
            },
            indent=1,
            ensure_ascii=False,
        )
    )
    print(f"{len(AREA_QUERIES)} area searches; {len(found)} new places with accessibility answers")
    return found


if __name__ == "__main__":
    g = fetch()
    extra = new_places(g) if "--areas" in sys.argv else {}
    private_map(g, extra)
