"""Build the atlas map: one GeoJSON per region + a self-contained HTML viewer + a review list.

  data/map/<region>_atlas.geojson   FeatureCollection (WGS84), one feature per place/trail/event venue
  data/map/atlas_viewer.html        open by double-click: icons per layer, colour per access rating, legend
  data/map/review.csv               everything that could not be placed, and why

Nothing is placed by fuzzy guessing: fact places are pinned in config/place_matches.yaml; event venues
are matched by exact name, by a park name in the event text, or by street address (U.S. Census
geocoder). Whatever fails goes to review.csv.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import string
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml
from shapely.geometry import mapping
from shapely.ops import unary_union

from .core import METRIC, PROCESSED, ROOT, WGS84, area, fetch, log

MAP = ROOT / "data/map"
TODAY = date.today().isoformat()
LAYERS = ["culture", "park", "trail", "restroom", "adaptive_recreation", "lodging", "event"]
ENTRANCE, RESTROOM = "entrance_step_free", "restroom_accessible"
LABELS = {  # plain-language attribute names for popups
    "entrance_step_free": "Step-free entrance",
    "automatic_door": "Automatic door",
    "elevator": "Elevator / lift",
    "accessible_route_inside": "Getting around inside",
    "ramp_steep": "Steep ramp",
    "restroom_accessible": "Accessible restroom",
    "restroom_family": "Family / universal restroom",
    "adult_changing_table": "Adult changing table",
    "wheelchair_loan": "Wheelchair loan",
    "scooter_or_ecv": "Scooter / ECV",
    "accessible_parking": "Accessible parking",
    "drop_off": "Drop-off",
    "accessible_seating": "Wheelchair seating",
    "companion_admission": "Companion admission",
    "seating_rest": "Places to rest",
    "sensory_friendly": "Sensory-friendly",
    "quiet_room": "Quiet room",
    "asl_interpretation": "ASL",
    "captioning": "Captioning",
    "assistive_listening": "Assistive listening",
    "service_animals": "Service animals",
    "braille": "Braille",
    "large_print": "Large print",
    "audio_description": "Audio description",
    "tactile": "Touch / tactile",
    "accessibility_map": "Accessibility map / guide",
    "accessibility_contact": "Accessibility contact",
    "transit_access": "Transit",
    "trail_surface": "Path surface",
    "all_terrain_chair": "All-terrain wheelchair",
    "adaptive_recreation": "Adaptive recreation",
    "accessible_lodging": "Accessible rooms",
    "mobility_device_policy": "Mobility devices",
}


# ---------------------------------------------------------------- gazetteer ----
def gazetteer(region: str) -> gpd.GeoDataFrame:
    """Named places for exact-name lookups; OSM first (better geometry), Overture second."""
    parts = []
    for f, src, cat, rank in [
        ("osm_destinations", "osm", "category", 0),
        ("osm", "osm", "category", 1),
        ("overture_places", "overture", "basic_category", 2),
    ]:
        x = gpd.read_parquet(PROCESSED / region / f"{f}.entities.parquet")
        if f == "osm":
            x = x[x.entity_type == "poi"]
        parts.append(
            gpd.GeoDataFrame(
                {
                    "entity_id": x.entity_id.values,
                    "name": x.name.values,
                    "category": x[cat].fillna("").values,
                    "rank": rank,
                    "src": src,
                },
                geometry=x.geometry.values,
                crs=WGS84,
            )
        )
    g = pd.concat(parts, ignore_index=True)
    g = g[g.name.fillna("") != ""].copy()
    g["key"] = g.name.str.lower().str.replace("’", "'").str.strip()
    g["area_m2"] = g.geometry.to_crs(METRIC).area
    return g


def lookup(g: gpd.GeoDataFrame, name: str, category: str | None = None):
    m = g[g.key == name.lower().replace("’", "'").strip()]
    if category:
        m = m[m.category.str.contains(category, case=False)]
    if m.empty:
        return None
    best = m.sort_values(["rank", "area_m2"], ascending=[True, False]).iloc[0]
    return best


def point(geom):
    return geom if geom.geom_type == "Point" else geom.representative_point()


def census_geocode(address: str):
    """U.S. Census one-line geocoder (free, public). Only venue street addresses are sent."""
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    try:
        res = json.loads(
            fetch(
                url,
                params={"address": address, "benchmark": "Public_AR_Current", "format": "json"},
                timeout=60,
            )
        )
        m = res["result"]["addressMatches"]
        return (m[0]["coordinates"]["x"], m[0]["coordinates"]["y"]) if m else None
    except Exception as e:  # network or format problem: send to review, never guess
        log.warning("geocode failed for %r: %s", address, e)
        return None


# ---------------------------------------------------------------- ratings ------
def rate(facts: pd.DataFrame) -> str:
    """accessible = step-free entry AND accessible restroom stated; partial = some positive access facts;
    not_accessible = entry explicitly 'no'; unknown = nothing stated."""
    if facts.empty:
        return "unknown"
    v = {a: set(facts[facts.attribute == a].value) for a in facts.attribute.unique()}
    if "no" in v.get(ENTRANCE, set()):
        return "not_accessible"
    if "yes" in v.get(ENTRANCE, set()) and "yes" in v.get(RESTROOM, set()):
        return "accessible"
    return "partial" if (facts.value.isin(["yes", "limited"])).any() else "unknown"


def osm_rating(tags: dict) -> str:
    w = tags.get("wheelchair") or tags.get("toilets:wheelchair")
    return {
        "yes": "accessible",
        "designated": "accessible",
        "limited": "partial",
        "no": "not_accessible",
    }.get(w or "", "unknown")


def fact_list(facts: pd.DataFrame) -> list[dict]:
    return [
        {
            "attribute": LABELS.get(r.attribute, r.attribute),
            "value": r.value,
            "detail": r.detail,
            "quote": r.evidence_quote,
            "source": r.url,
            "date": r.observed_at
            if isinstance(r.observed_at, str) and r.observed_at
            else str(r.extracted_at)[:10],
        }
        for r in facts.sort_values("attribute").itertuples()
    ]


# ---------------------------------------------------------------- builders -----
def place_features(g, facts, matches, review):
    feats = []
    for place, spec in matches.items():
        if place.startswith("_"):
            continue
        f = facts[facts.place == place]
        if f.empty:
            continue
        region = f.region.iloc[0]
        if "skip" in spec:
            review.append({"region": region, "item": place, "kind": "fact place", "reason": spec["skip"]})
            continue
        hit = lookup(g, spec["name"], spec.get("category"))
        if hit is None:
            review.append(
                {
                    "region": region,
                    "item": place,
                    "kind": "fact place",
                    "reason": f"no exact gazetteer match for {spec['name']!r}",
                }
            )
            continue
        feats.append(
            {
                "geometry": point(hit.geometry),
                "properties": {
                    "name": spec.get("label", place),
                    "layer": spec["layer"],
                    "access_rating": rate(f),
                    "facts": fact_list(f),
                    "matched_to": f"{hit.entity_id} ({hit.name})",
                    "region": region,
                },
            }
        )
    for spec in matches.get("_extra", []):
        region = spec.get("region", "")
        hit = lookup(g, spec["name"], spec.get("category"))
        if hit is None:
            review.append(
                {
                    "region": region,
                    "item": spec["name"],
                    "kind": "poster point",
                    "reason": "no exact gazetteer match",
                }
            )
            continue
        feats.append(
            {
                "geometry": point(hit.geometry),
                "properties": {
                    "name": spec["label"],
                    "layer": spec["layer"],
                    "access_rating": "accessible",
                    "facts": [
                        {
                            "attribute": "Wheelchair symbol",
                            "value": "yes",
                            "detail": spec["fact"],
                            "quote": "",
                            "source": spec["source"],
                            "date": "2019-11",
                        }
                    ],
                    "matched_to": f"{hit.entity_id} ({hit.name})",
                    "region": region,
                },
            }
        )
    return feats


def restroom_features(region):
    e = gpd.read_parquet(PROCESSED / region / "osm_destinations.entities.parquet")
    e = e[e.entity_type == "restroom"]
    feats = []
    for r in e.itertuples():
        t = json.loads(r.tags)
        if t.get("amenity") != "toilets":
            continue
        rating = osm_rating(t)
        facts = [
            {
                "attribute": k,
                "value": t[k],
                "detail": "",
                "quote": "",
                "source": f"https://www.openstreetmap.org/{r.entity_id[4:]}",
                "date": "",
            }
            for k in (
                "wheelchair",
                "toilets:wheelchair",
                "changing_table",
                "unisex",
                "fee",
                "opening_hours",
                "access",
            )
            if k in t
        ]
        feats.append(
            {
                "geometry": point(r.geometry),
                "properties": {
                    "name": r.name or "Public restroom",
                    "layer": "restroom",
                    "access_rating": rating,
                    "facts": facts,
                    "matched_to": r.entity_id,
                    "region": region,
                },
            }
        )
    return feats


def norm_trail(s: str) -> str:
    """'Wolf Creek Trail (OH)' and 'Wolf Creek Trail' -> 'wolf creek'."""
    s = re.sub(r"\(.*?\)", "", s.lower().replace("’", "'"))
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(w for w in s.split() if w not in {"trail", "the"})


def trail_features(matches, review):
    parts = []
    for region in ("cincinnati", "oxford"):
        o = gpd.read_parquet(PROCESSED / region / "osm_destinations.entities.parquet")
        parts.append(o[(o.entity_type == "trail") & (o.name.fillna("") != "")])
    osm = pd.concat(parts, ignore_index=True).drop_duplicates("entity_id")
    osm["key"] = osm.name.map(norm_trail)
    poly = unary_union([area("cincinnati"), area("oxford")])
    aliases = {norm_trail(k): v for k, v in matches.get("_trail_aliases", {}).items()}

    def geometry_of(names):
        keys = {norm_trail(n) for n in names}
        m = osm[osm.key.isin(keys)]
        if m.empty:
            return None, m
        geom = unary_union(list(m.geometry)).intersection(poly)
        if geom.is_empty:
            return None, m
        return gpd.GeoSeries([geom], crs=WGS84).to_crs(METRIC).simplify(3).to_crs(WGS84).iloc[0], m

    feats = []
    tl = pd.read_json(
        ROOT / "data/extracted/traillink_trails.jsonl", lines=True, convert_dates=False, dtype=False
    )
    for r in tl.itertuples():
        alias = aliases.get(norm_trail(r.trail))
        geom, m = geometry_of([r.trail] + ([alias] if alias else []))
        if geom is None:
            review.append(
                {
                    "region": "both",
                    "item": r.trail,
                    "kind": "TrailLink trail",
                    "reason": "no OSM path with this name inside either area (most are outside it)",
                }
            )
            continue
        day = str(r.retrieved_at)[:10]
        feats.append(
            {
                "geometry": geom,
                "properties": {
                    "name": r.trail,
                    "layer": "trail",
                    "access_rating": "accessible" if r.paved else "partial",
                    "facts": [
                        {
                            "attribute": "Path surface",
                            "value": "yes" if r.paved else "limited",
                            "detail": f"{', '.join(r.surface)}; {r.length_mi} mi total (all states)",
                            "quote": r.evidence.replace("\n", " · "),
                            "source": r.source_urls[0],
                            "date": day,
                        },
                        {
                            "attribute": "Listed as",
                            "value": "yes",
                            "detail": "wheelchair accessible on TrailLink. " + r.caveat,
                            "quote": "",
                            "source": r.source_urls[0],
                            "date": day,
                        },
                    ],
                    "matched_to": f"{len(m)} OSM ways/relations named {sorted(set(m.name))}",
                    "region": None,
                },
            }
        )
    for spec in matches.get("_extra_trails", []):
        geom, m = geometry_of([spec["osm_name"]])
        if geom is None:
            review.append(
                {
                    "region": "both",
                    "item": spec["osm_name"],
                    "kind": "extra trail",
                    "reason": "no OSM path with this name",
                }
            )
            continue
        feats.append(
            {
                "geometry": geom,
                "properties": {
                    "name": spec["label"],
                    "layer": "trail",
                    "access_rating": spec["rating"],
                    "facts": spec["facts"],
                    "matched_to": f"{len(m)} OSM ways named {spec['osm_name']!r}",
                    "region": None,
                },
            }
        )
    return feats


def event_features(region, g, matches, facts_feats, review):
    aliases = matches.get("_venue_aliases", {})
    rated = {
        f["properties"]["matched_to"].split(" ")[0]: f["properties"]["access_rating"] for f in facts_feats
    }
    ev = []
    d = PROCESSED / region
    for f in d.glob("events_*.events.parquet"):
        x = pd.read_parquet(f)
        ev.append(x.assign(feed=f.name.split(".")[0]))
    pe = ROOT / "data/extracted/page_events.jsonl"
    if pe.exists():
        p = pd.read_json(pe, lines=True, convert_dates=False, dtype=False)
        ev.append(p[p.region == region].assign(feed="page_events", description=""))
    if not ev:
        return []
    ev = pd.concat(ev, ignore_index=True)
    ev = ev[ev.start.astype(str).str[:10] >= TODAY]
    if region == "oxford":  # keep only Miami events sorted as open to the public
        cls = pd.read_json(
            ROOT / "data/extracted/miami_events_classified.jsonl",
            lines=True,
            convert_dates=False,
            dtype=False,
        )
        public = set(cls[cls["class"] == "public_leisure"].event_id)
        ev = ev[(ev.feed != "events_ical_oxford") | ev.event_id.isin(public)]
    text_aliases = matches.get("_event_text_aliases", {})
    park_names = sorted(  # multi-word names only: one-word names ("Cincinnati") are towns, not venues
        {
            n
            for n in g[g.category.str.contains("park|museum|garden|nature_reserve")].name
            if len(n) >= 8 and " " in n.strip()
        },
        key=len,
        reverse=True,
    )
    venues: dict[str, dict] = {}
    for r in ev.itertuples():
        hit, how = None, ""
        segs = [s.strip() for s in re.split(r"[|,]", str(r.venue or "")) if s.strip()]
        first = segs[0] if segs else ""
        if first and not re.match(r"\d", first):  # first part is the venue name; addresses go to geocoder
            name = aliases.get(first.lower(), first)
            hit = lookup(g, name)
            how = f"venue name {first!r}" if hit is not None else ""
        if hit is None and r.feed == "events_cincy_parks":
            text = f"{r.title} {r.description}"
            pn = next((n for n in park_names if n in text), None)
            pn = pn or next((v for k, v in text_aliases.items() if k in text), None)
            if pn:
                hit, how = lookup(g, pn), f"park named in event text: {pn!r}"
        if hit is None and r.venue and re.search(r"\d", str(r.venue)):
            xy = census_geocode(str(r.venue))
            if xy:
                from shapely.geometry import Point

                hit = pd.Series(
                    {
                        "entity_id": f"census:{r.venue}",
                        "name": f"Event venue, {str(r.venue).split(',')[0].strip()}",
                        "geometry": Point(*xy),
                    }
                )
                how = "street address (Census geocoder)"
        if hit is None:
            review.append(
                {
                    "region": region,
                    "item": f"{r.title} ({str(r.start)[:10]})",
                    "kind": "event",
                    "reason": f"venue not placed: {r.venue!r}",
                }
            )
            continue
        if not area(region).contains(point(hit.geometry)):
            review.append(
                {"region": region, "item": r.title, "kind": "event", "reason": "venue outside area"}
            )
            continue
        v = venues.setdefault(hit.entity_id, {"hit": hit, "how": how, "events": []})
        v["events"].append(
            {
                "title": str(r.title).strip(),
                "start": str(r.start)[:16],
                "url": r.url,
                "accessible_tag": getattr(r, "site_tagged_accessible", None) is True
                or "wheelchair-accessible" in str(getattr(r, "feed_url", "")),
                "disability_focused": getattr(r, "is_disability_focused", None) is True,
            }
        )
    place_by_eid = {f["properties"]["matched_to"].split(" ")[0]: f for f in facts_feats}
    feats = []
    for eid, v in venues.items():
        evs = sorted(v["events"], key=lambda e: e["start"])
        if eid in place_by_eid:  # the venue is already a place on the map: list its events there
            pp = place_by_eid[eid]["properties"]
            pp["events"], pp["event_count"] = evs[:40], len(evs)
            pp["disability_focused"] = any(e["disability_focused"] for e in evs)
            continue
        tag = any(e["accessible_tag"] for e in evs)
        rating = rated.get(eid, "partial" if tag else "unknown")
        feats.append(
            {
                "geometry": point(v["hit"].geometry),
                "properties": {
                    "name": v["hit"]["name"],
                    "layer": "event",
                    "access_rating": rating,
                    "events": evs[:40],
                    "event_count": len(evs),
                    "disability_focused": any(e["disability_focused"] for e in evs),
                    "facts": [],
                    "matched_to": f"{eid} via {v['how']}",
                    "region": region,
                },
            }
        )
    return feats


# ---------------------------------------------------------------- output -------
def region_of(geom) -> str | None:
    hits = [r for r in ("cincinnati", "oxford") if area(r).intersects(geom)]
    if len(hits) <= 1:
        return hits[0] if hits else None
    return max(hits, key=lambda r: area(r).intersection(geom).length or area(r).contains(geom))


def collection(region: str, feats: list) -> dict:
    return {
        "type": "FeatureCollection",
        "name": f"{region}_atlas",
        "generated": TODAY,
        "rating_rule": rate.__doc__.strip(),
        "features": [
            {
                "type": "Feature",
                "id": f"{region}:{i}",
                "geometry": mapping(f["geometry"]),
                "properties": {**f["properties"], "region": region},
            }
            for i, f in enumerate(feats)
        ],
    }


def write() -> list[Path]:
    MAP.mkdir(parents=True, exist_ok=True)
    review, written, data = [], [], {}
    g = pd.concat([gazetteer("cincinnati"), gazetteer("oxford")], ignore_index=True)
    g = g.drop_duplicates("entity_id")
    facts = pd.read_json(
        ROOT / "data/extracted/venue_facts.jsonl", lines=True, convert_dates=False, dtype=False
    )
    matches = yaml.safe_load((ROOT / "config/place_matches.yaml").read_text())
    places = place_features(g, facts, matches, review)
    shared = places + trail_features(matches, review)
    for region in ("cincinnati", "oxford"):
        feats = [f for f in shared if region_of(f["geometry"]) == region]
        taken = {f["properties"]["matched_to"].split(" ")[0] for f in feats}
        extra = [
            f for f in building_features(region) if f["properties"]["matched_to"].split(" ")[0] not in taken
        ]
        taken |= {f["properties"]["matched_to"].split(" ")[0] for f in extra}
        extra += tagged_poi_features(region, taken)
        feats += extra + restroom_features(region)
        hosts = [f for f in feats if f["properties"]["layer"] != "restroom"]  # events attach to these
        feats += event_features(region, g, matches, hosts, review)
        enrich(feats, g)
        add_getting_there(feats, region)
        add_arrival(feats, region)
        seen: dict[str, int] = {}
        for f in feats:  # same name at the same spot (OSM node + way): keep links unique
            k = f["properties"]["link_id"]
            seen[k] = seen.get(k, 0) + 1
            if seen[k] > 1:
                f["properties"]["link_id"] = f"{k}-{seen[k]}"
        fc = collection(region, feats)
        p = MAP / f"{region}_atlas.geojson"
        p.write_text(json.dumps(fc, ensure_ascii=False))
        written.append(p)
        data[region] = fc
        counts = pd.Series([f["properties"]["layer"] for f in fc["features"]]).value_counts().to_dict()
        log.info("[%s] map: %d features %s", region, len(fc["features"]), counts)
    pd.DataFrame(review).drop_duplicates().to_csv(MAP / "review.csv", index=False)
    from .map_viewer import render

    # one page per city (for GitHub Pages links) + an index page with both
    other = {"cincinnati": "oxford", "oxford": "cincinnati"}
    for region in data:
        page = MAP / f"{region}.html"
        nav = f' · <a href="{other[region]}.html">Switch to the {other[region].title()} map</a>'
        page.write_text(render({region: data[region]}, f"{region.title()} accessibility map", nav))
        written.append(page)
    (MAP / "index.html").write_text(render(data, "Ohio Access Atlas: Cincinnati and Oxford"))
    old = MAP / "atlas_viewer.html"
    if old.exists():
        old.unlink()  # replaced by index.html
    written += write_github(data)
    return [*written, MAP / "review.csv", MAP / "index.html"]


# ------------------------------------------------- GitHub preview copies -------
# GitHub draws .geojson files as maps and understands the "simplestyle" properties below, so these
# copies show a colour per rating and an icon per layer right in the repository, no hosting needed.
GH_COLOUR = {"accessible": "#0072B2", "partial": "#E69F00", "not_accessible": "#D55E00", "unknown": "#8C8C8C"}
GH_SYMBOL = {
    "building": "building",
    "food_drink": "restaurant",
    "service": "shop",
    "culture": "museum",
    "park": "park",
    "restroom": "toilet",
    "adaptive_recreation": "wheelchair",
    "lodging": "lodging",
    "event": "star",
}
GH_RATING = {
    "accessible": "Accessible",
    "partial": "Partly accessible",
    "not_accessible": "Not accessible",
    "unknown": "No information yet",
}
GH_LAYER = {
    "building": "Building (campus or public)",
    "food_drink": "Food & drink",
    "service": "Shop or service",
    "culture": "Museum / venue / attraction",
    "park": "Park or garden",
    "restroom": "Public restroom",
    "adaptive_recreation": "Adaptive recreation",
    "lodging": "Accessible lodging",
    "event": "Event venue",
    "trail": "Trail",
}


def github_copy(fc: dict) -> dict:
    feats = []
    for f in fc["features"]:
        p = f["properties"]
        q = {"Name": p["name"], "Type": GH_LAYER[p["layer"]], "Accessibility": GH_RATING[p["access_rating"]]}
        for i, fact in enumerate(p.get("facts", [])[:6], 1):
            detail = f" ({fact['detail']})" if fact.get("detail") else ""
            q[f"Fact {i}"] = f"{fact['attribute']}: {fact['value']}{detail}"[:200]
        if p.get("events"):
            q["Upcoming events"] = f"{p['event_count']}: " + "; ".join(
                f"{e['start'][:10]} {e['title']}" for e in p["events"][:3]
            )
        srcs = [x["source"] for x in p.get("facts", []) if str(x.get("source", "")).startswith("http")]
        if srcs:
            q["Source"] = srcs[0]
        if p["layer"] == "trail":
            q.update({"stroke": GH_COLOUR[p["access_rating"]], "stroke-width": 4, "stroke-opacity": 0.9})
        else:
            q.update(
                {
                    "marker-color": GH_COLOUR[p["access_rating"]],
                    "marker-symbol": GH_SYMBOL[p["layer"]],
                    "marker-size": "small" if p["layer"] == "restroom" else "medium",
                }
            )
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": q})
    return {"type": "FeatureCollection", "features": feats}


def write_github(data: dict) -> list[Path]:
    out = MAP / "github"
    out.mkdir(exist_ok=True)
    paths = []
    for region, fc in data.items():
        p = out / f"{region}.geojson"
        p.write_text(json.dumps(github_copy(fc), ensure_ascii=False, indent=0))
        paths.append(p)
    return paths


# ------------------------------------------------------ plain-language layer ---
# Every feature gets a one-sentence summary, contacts and (for restrooms) a name a screen-reader
# user can tell apart. Built only from the facts already on the feature: nothing new is claimed.
SUMMARY_ORDER = [
    "entrance_step_free",
    "restroom_accessible",
    "adult_changing_table",
    "elevator",
    "wheelchair_loan",
    "all_terrain_chair",
    "accessible_parking",
    "accessible_seating",
    "accessible_lodging",
    "trail_surface",
    "accessible_route_inside",
    "ramp_steep",
]
LABEL_TO_ATTR = {v: k for k, v in LABELS.items()}
# The short "what is known" line on each card: (key, card label). Entrance and restroom are always
# shown (as "not known" when missing) because they are what a wheelchair user asks first.
KEY_FACTS = [
    ("entrance", "Entrance"),
    ("restroom", "Restroom"),
    ("inside", "Inside"),
    ("elevator", "Elevator"),
    ("adult_changing_table", "Adult changing table"),
    ("accessible_rooms", "Accessible rooms"),
    ("accessible_parking", "Parking"),
    ("accessible_seating", "Wheelchair seating"),
    ("wheelchair_loan", "Wheelchair loan"),
    ("braille", "Braille"),
    ("audio_description", "Audio description"),
    ("large_print", "Large print"),
    ("tactile", "Touch"),
    ("service_animals", "Service animals"),
]
KEY_SOURCES = {  # fact attribute (label or OSM tag) -> key
    "Step-free entrance": "entrance",
    "Accessible entrance": "entrance",
    "wheelchair": "entrance",
    "entrance:wheelchair": "entrance",
    "Accessible restroom": "restroom",
    "toilets:wheelchair": "restroom",
    "Elevator / lift": "elevator",
    "Getting around inside": "inside",
    "Adult changing table": "adult_changing_table",
    "Accessible rooms": "accessible_rooms",
    "Accessible parking": "accessible_parking",
    "Wheelchair seating": "accessible_seating",
    "Wheelchair loan": "wheelchair_loan",
    "Braille": "braille",
    "Audio description": "audio_description",
    "Large print": "large_print",
    "Touch / tactile": "tactile",
    "Service animals": "service_animals",
}
WORD = {"yes": "yes", "designated": "yes", "limited": "partly", "no": "no"}


def key_facts(p: dict) -> list[list[str]]:
    """[[label, yes|partly|no|not known], ...] for places; empty for restrooms, trails and events."""
    if p["layer"] in ("restroom", "trail", "event"):
        return []
    got: dict[str, str] = {}
    for f in p.get("facts", []):
        k = KEY_SOURCES.get(f["attribute"])
        v = WORD.get(str(f.get("value", "")).split(";")[-1])
        if k and v and (k not in got or got[k] == "no" and v != "no"):
            got[k] = v
    if p["layer"] == "food_drink" or p["layer"] == "service":
        got.setdefault("restroom", "not known")
    out = [
        [lab, got.get(k, "not known")] for k, lab in KEY_FACTS if k in got or k in ("entrance", "restroom")
    ]
    return out if any(v != "not known" for _, v in out) else []


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")


def _phrase(attr: str, value: str, detail: str) -> str | None:
    label = LABELS.get(attr, attr).lower()
    d = f" ({detail})" if detail and len(detail) <= 70 else ""
    if attr == "ramp_steep":
        return f"caution: a ramp steeper than ADA guidance{d}" if value == "yes" else None
    if value == "yes":
        return f"{label}{d}"
    if value == "limited":
        return f"{label} limited{d}"
    if value == "no":
        return f"no {label}{d}"
    return None


def summarise(p: dict) -> str:
    if p.get("summary_text"):
        return p["summary_text"]
    facts = p.get("facts", [])
    if p["layer"] == "event":
        nxt = p["events"][0] if p.get("events") else None
        s = f"{p['event_count']} upcoming event{'s' if p['event_count'] != 1 else ''}"
        return s + (f"; next: {nxt['title']} on {nxt['start'][:10]}." if nxt else ".")
    if p["layer"] == "restroom":
        tags = {f["attribute"]: f["value"] for f in facts}
        w = tags.get("toilets:wheelchair") or tags.get("wheelchair")
        parts = [
            {
                "yes": "wheelchair accessible",
                "designated": "wheelchair accessible",
                "limited": "partly wheelchair accessible",
                "no": "not wheelchair accessible",
            }.get(w or "", "no accessibility information yet")
        ]
        if tags.get("changing_table") == "yes":
            parts.append("has a changing table")
        if tags.get("fee") == "yes":
            parts.append("fee required")
        if tags.get("opening_hours"):
            parts.append(f"hours {tags['opening_hours']}")
        return "Public restroom: " + ", ".join(parts) + " (OpenStreetMap)."
    if p["layer"] == "trail":
        surf = next((f for f in facts if f["attribute"] == "Path surface"), None)
        if surf:
            m = re.match(r"(?P<s>[^;]+); (?P<mi>[\d.]+) mi", surf.get("detail", ""))
            kind = "Paved trail" if surf["value"] == "yes" else "Partly paved trail"
            if m:
                return (
                    f"{kind} ({m['s'].lower()}), {m['mi']} miles long in total; listed as wheelchair "
                    "accessible by TrailLink, which warns not every section may be."
                )
            return f"{kind}: {surf.get('detail', '')}."
    by_attr: dict[str, dict] = {}
    for f in facts:
        a = LABEL_TO_ATTR.get(f["attribute"], f["attribute"])
        by_attr.setdefault(a, f)
    parts = [
        x
        for a in SUMMARY_ORDER
        if a in by_attr
        for x in [_phrase(a, by_attr[a]["value"], by_attr[a].get("detail", ""))]
        if x
    ]
    if not parts and facts:  # facts outside the main list (e.g. a map symbol): say them as they are
        parts = [f"{f['attribute'].lower()}: {f.get('detail') or f['value']}" for f in facts[:3]]
    if not parts:
        return "No accessibility information yet."
    dates = sorted(str(f.get("date")) for f in facts if re.match(r"\d{4}", str(f.get("date") or "")))
    sentence = "; ".join(parts[:5])
    return (
        sentence[0].upper() + sentence[1:] + "." + (f" Sources dated up to {dates[-1][:7]}." if dates else "")
    )


def contacts(p: dict) -> dict:
    text = " ".join(
        f"{f.get('detail', '')} {f.get('quote', '')}"
        for f in p.get("facts", [])
        if f.get("attribute") in ("Accessibility contact", "accessibility_contact")
    )
    return {"emails": sorted(set(EMAIL.findall(text))), "phones": sorted(set(PHONE.findall(text)))}


def enrich(feats: list, g: gpd.GeoDataFrame) -> None:
    landmark = (
        r"^(leisure|tourism|historic|natural|boundary)=|^amenity=(library|community_centre|theatre|"
        r"arts_centre|townhall|place_of_worship|school|university|college|marketplace|fountain|shelter)"
    )
    named = g[
        (g.src == "osm")
        & g.category.str.contains(landmark)
        & (g.name.str.len() > 3)
        & ~g.category.str.contains("parking")
        & ~g.name.str.contains(r"\bparking\b|\blot\b", case=False)
    ]
    pts = gpd.GeoDataFrame(named[["name"]], geometry=named.geometry.map(point), crs=WGS84).to_crs(METRIC)

    street_parts = []
    for region in (
        "cincinnati",
        "oxford",
    ):  # named streets and paths (city network) + named trails (wider area)
        for f, kind in (("osm", "path_segment"), ("osm_destinations", "trail")):
            x = gpd.read_parquet(
                PROCESSED / region / f"{f}.entities.parquet", columns=["name", "entity_type", "geometry"]
            )
            street_parts.append(
                x[(x.entity_type == kind) & (x.name.fillna("").str.len() > 3)][["name", "geometry"]]
            )
    streets = gpd.GeoDataFrame(pd.concat(street_parts, ignore_index=True), crs=WGS84).to_crs(METRIC)

    def nearest_name(here, layer, radius):
        idx = list(layer.sindex.query(here.buffer(radius)))
        if not idx:
            return None
        cand = layer.iloc[idx]
        return cand.iloc[cand.distance(here).argmin()]["name"]

    for f in feats:
        p = f["properties"]
        p["name"] = p["name"].split("; ")[
            -1
        ]  # "Miami University; Souers Recital Hall" -> "Souers Recital Hall"
        if p["layer"] == "restroom" and p["name"].lower() in ("public restroom", "toilets", "restroom", ""):
            here = gpd.GeoSeries([point(f["geometry"])], crs=WGS84).to_crs(METRIC).iloc[0]
            best = nearest_name(here, pts, 500) or nearest_name(here, streets, 150)
            if best:
                p["name"] = f"Restroom near {best}"
        p["summary"] = summarise(p)
        p["keys"] = key_facts(p)
        dates = sorted(
            str(x.get("date")) for x in p.get("facts", []) if re.match(r"\d{4}", str(x.get("date") or ""))
        )
        p["newest_source"] = dates[-1][:7] if dates else None
        c = point(f["geometry"])
        slug = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")[:48]
        p["link_id"] = f"{slug}-{hashlib.md5(f'{c.y:.4f},{c.x:.4f}'.encode()).hexdigest()[:5]}"
        p["contacts"] = contacts(p)


# ------------------------------------------- OSM buildings and tagged places ----
FOOD = {"restaurant", "cafe", "fast_food", "bar", "pub", "ice_cream", "food_court", "biergarten"}


def building_features(region: str) -> list:
    """Named buildings whose entrances say whether a wheelchair can use them (OSM)."""
    f = PROCESSED / region / "osm_entrances.entities.parquet"
    if not f.exists():
        return []
    b = gpd.read_parquet(f)
    out = []
    for r in b.itertuples():
        total = r.entrances_yes + r.entrances_limited + r.entrances_no
        if not total:
            continue
        if r.entrances_yes:
            rating, text = (
                "partial",
                (
                    f"{r.entrances_yes} of {total} mapped entrance{'s' if total > 1 else ''} "
                    "wheelchair accessible (OpenStreetMap); restrooms and inside not recorded."
                ),
            )
        elif r.entrances_limited:
            rating, text = (
                "partial",
                f"{r.entrances_limited} of {total} mapped entrances partly wheelchair accessible "
                "(OpenStreetMap).",
            )
        else:
            rating, text = (
                "not_accessible",
                (
                    f"None of the {total} mapped entrances is wheelchair accessible "
                    "(OpenStreetMap); other entrances may not be mapped."
                ),
            )
        out.append(
            {
                "geometry": r.geometry.representative_point(),
                "properties": {
                    "name": r.name,
                    "layer": "building",
                    "access_rating": rating,
                    "summary_text": text,
                    "facts": [
                        {
                            "attribute": "Accessible entrance",
                            "value": "yes" if r.entrances_yes else "no",
                            "detail": f"{r.entrances_yes} yes, {r.entrances_limited} limited, "
                            f"{r.entrances_no} no of {total} mapped entrances",
                            "quote": "",
                            "source": f"https://www.openstreetmap.org/{r.entity_id[4:]}",
                            "date": TODAY[:7],
                        }
                    ],
                    "matched_to": f"{r.entity_id} ({r.name})",
                    "region": region,
                },
            }
        )
    return out


def tagged_poi_features(region: str, taken: set) -> list:
    """Restaurants, cafes, shops, libraries, hotels... that carry an OSM wheelchair tag."""
    e = gpd.read_parquet(PROCESSED / region / "osm.entities.parquet")
    e = e[e.entity_type == "poi"]
    out = []
    for r in e.itertuples():
        t = json.loads(r.tags)
        w = t.get("wheelchair")
        if not w or not r.name or r.entity_id in taken or t.get("amenity") == "toilets":
            continue
        a, tour = t.get("amenity"), t.get("tourism")
        layer = (
            "food_drink"
            if a in FOOD
            else "lodging"
            if tour in ("hotel", "motel", "guest_house")
            else "culture"
            if tour in ("museum", "attraction", "gallery") or a in ("theatre", "arts_centre")
            else "building"
            if a in ("library", "townhall", "community_centre", "place_of_worship")
            or t.get("building") in ("university", "college", "civic")
            else "service"
        )
        rating = osm_rating(t)
        words = {
            "accessible": "wheelchair accessible",
            "partial": "partly wheelchair accessible",
            "not_accessible": "not wheelchair accessible",
        }.get(rating, "accessibility unknown")
        extra = "; accessible toilet" if t.get("toilets:wheelchair") == "yes" else ""
        out.append(
            {
                "geometry": point(r.geometry),
                "properties": {
                    "name": r.name,
                    "layer": layer,
                    "access_rating": rating,
                    "summary_text": f"Tagged {words} on OpenStreetMap{extra}."
                    + (f" Hours {t['opening_hours']}." if t.get("opening_hours") else ""),
                    "facts": [
                        {
                            "attribute": k,
                            "value": t[k],
                            "detail": "",
                            "quote": "",
                            "source": f"https://www.openstreetmap.org/{r.entity_id[4:]}",
                            "date": "",
                        }
                        for k in (
                            "wheelchair",
                            "wheelchair:description",
                            "toilets:wheelchair",
                            "entrance:wheelchair",
                            "opening_hours",
                            "phone",
                            "website",
                        )
                        if k in t
                    ],
                    "matched_to": f"{r.entity_id} ({r.name})",
                    "region": region,
                },
            }
        )
    return out


# ------------------------------------------------------------ getting there ----
# Nearby conditions around each place, from data already collected. These are counts within a
# radius, not a route: they tell a wheelchair user what to expect near the door.
NEAR_M = 150  # about 500 feet
STEEP = 8.33  # ADA maximum ramp running slope, percent


def _metric(gdf):
    return gdf.to_crs(METRIC) if gdf.crs else gdf.set_crs(WGS84).to_crs(METRIC)


def getting_there_layers(region: str) -> dict:
    d, L = PROCESSED / region, {}
    gt = "gtfs_metro" if region == "cincinnati" else "gtfs_bcrta"
    s = gpd.read_parquet(d / f"{gt}.entities.parquet")
    if "geometry" not in s or s.geometry.isna().all():
        s = gpd.GeoDataFrame(
            s, geometry=gpd.points_from_xy(s.stop_lon.astype(float), s.stop_lat.astype(float)), crs=WGS84
        )
    L["stops"] = _metric(s[["stop_name", "wheelchair_boarding", "geometry"]].copy())
    L["feed"] = gt
    sl = gpd.read_parquet(d / "slope_3dep_local.entities.parquet")
    L["steep"] = _metric(sl[sl.max_grade > STEEP][["max_grade", "geometry"]])
    net = gpd.read_parquet(d / "osm.entities.parquet")
    net = net[net.entity_type == "path_segment"]
    steps = [net[net.tags.str.contains('"highway": "steps"')][["geometry"]]]
    if (d / "cagis_public_steps.entities.parquet").exists():
        steps.append(gpd.read_parquet(d / "cagis_public_steps.entities.parquet")[["geometry"]])
    net_all = gpd.read_parquet(d / "osm.entities.parquet")
    xs = net_all[net_all.entity_type.isin(["crossing", "kerb", "path_segment"])]
    snd = xs.tags.str.contains('"traffic_signals:sound": "yes"') | xs.tags.str.contains(
        '"traffic_signals:vibration": "yes"'
    )
    L["aps"] = _metric(xs[snd][["geometry"]])
    L["tactile"] = _metric(xs[xs.tags.str.contains('"tactile_paving": "yes"')][["geometry"]])
    L["stairs"] = _metric(gpd.GeoDataFrame(pd.concat(steps, ignore_index=True), crs=WGS84))
    if (d / "cagis_curb_ramps.entities.parquet").exists():
        r = gpd.read_parquet(d / "cagis_curb_ramps.entities.parquet")
        L["ramps"] = _metric(gpd.GeoDataFrame(geometry=r.geometry.representative_point(), crs=r.crs))
    if (d / "cincy_311.entities.parquet").exists():
        i = gpd.read_parquet(d / "cincy_311.entities.parquet")
        since = (pd.Timestamp(TODAY) - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
        i = i[i.date_created.astype(str) >= since]
        L["reports"] = _metric(i[["sr_type_desc", "sr_status_flag", "geometry"]])
    return L


def add_getting_there(feats: list, region: str) -> None:
    L = getting_there_layers(region)
    for f in feats:
        p = f["properties"]
        if p["layer"] == "trail":
            continue
        here = gpd.GeoSeries([point(f["geometry"])], crs=WGS84).to_crs(METRIC).iloc[0]
        zone = here.buffer(NEAR_M)
        g = {}
        st = L["stops"]
        idx = list(st.sindex.query(here.buffer(800)))
        if idx:
            c = st.iloc[idx]
            dist = c.distance(here)
            best = c.iloc[dist.argmin()]
            g["bus_stop"] = {
                "name": _stop(best.stop_name),
                "metres": round(float(dist.min())),
                "boarding": str(best.wheelchair_boarding),
            }
        steep = L["steep"].iloc[list(L["steep"].sindex.query(zone, predicate="intersects"))]
        g["steep_sections"] = len(steep)
        g["steepest_pct"] = round(float(steep.max_grade.max()), 1) if len(steep) else None
        g["stairs"] = len(list(L["stairs"].sindex.query(zone, predicate="intersects")))
        if "ramps" in L:
            g["curb_ramps"] = len(list(L["ramps"].sindex.query(zone, predicate="intersects")))
        g["accessible_signals"] = len(list(L["aps"].sindex.query(zone, predicate="intersects")))
        g["tactile_paving"] = len(list(L["tactile"].sindex.query(zone, predicate="intersects")))
        if "reports" in L:
            rep = L["reports"].iloc[list(L["reports"].sindex.query(zone, predicate="intersects"))]
            g["reports_12m"] = len(rep)
            g["reports_open"] = int((rep.sr_status_flag == "OPEN").sum())
        parts = []
        if "bus_stop" in g:
            b = g["bus_stop"]
            ft = round(b["metres"] * 3.28084 / 50) * 50
            note = (
                " (feed marks wheelchair boarding)"
                if b["boarding"] == "1"
                else " (2019 schedule data, no accessibility field)"
                if L["feed"] == "gtfs_bcrta"
                else ""
            )
            parts.append(f"nearest bus stop {b['name']}, about {ft} ft{note}")
        else:
            parts.append("no bus stop within half a mile")
        if g["steep_sections"]:
            parts.append(
                f"{g['steep_sections']} path section{'s' if g['steep_sections'] > 1 else ''} steeper than "
                f"8.33% within 500 ft (steepest {g['steepest_pct']}%, estimated from elevation data)"
            )
        else:
            parts.append("no path section steeper than 8.33% within 500 ft (estimated from elevation data)")
        if g["stairs"]:
            parts.append(f"{g['stairs']} mapped stairway{'s' if g['stairs'] > 1 else ''} within 500 ft")
        if "curb_ramps" in g:
            parts.append(
                f"{g['curb_ramps']} city-mapped curb ramp{'s' if g['curb_ramps'] != 1 else ''} within 500 ft"
            )
        if g.get("reports_12m"):
            parts.append(
                f"{g['reports_12m']} sidewalk or curb problem report{'s' if g['reports_12m'] > 1 else ''} "
                f"to 311 nearby in the past year ({g['reports_open']} still open)"
            )
        g["text"] = "Getting there: " + "; ".join(parts) + "."
        p["getting_there"] = g


# ---------------------------------------------------------------- arrival ----
# A short description in words of how to reach the door, for people who cannot see the map.
# Computed from mapped entrances, bus stops and the venue's own entrance text; never a route.
COMPASS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
DOORS = {
    "automatic": "automatic door",
    "sliding": "sliding door",
    "revolving": "revolving door",
    "hinged": "hinged door",
    "swinging": "hinged door",
    "no": "open doorway",
}


def _towards(a, b) -> str:
    """8-point compass direction from point a to point b (metric CRS)."""
    ang = (math.degrees(math.atan2(b.x - a.x, b.y - a.y)) + 360) % 360
    return COMPASS[round(ang / 45) % 8]


def _stop(name: str) -> str:
    """CENTRAL PKWY & EZZARD CHARLES DR -> Central Pkwy & Ezzard Charles Dr."""
    return string.capwords(name) if name.isupper() else name


def _feet(m: float) -> str:
    return f"about {max(50, round(m * 3.28084 / 50) * 50)} feet"


def add_arrival(feats: list, region: str) -> None:
    d = PROCESSED / region
    e = gpd.read_parquet(d / "osm.entities.parquet")
    ent = e[e.entity_type == "entrance"].copy()
    ent["t"] = ent.tags.map(json.loads)
    ent["wc"] = ent.t.map(lambda t: (t.get("wheelchair") or "").split(";")[-1])
    ent = _metric(ent[ent.wc.isin(["yes", "designated", "limited", "no"])])
    bld = d / "osm_entrances.entities.parquet"
    bld = _metric(gpd.read_parquet(bld)) if bld.exists() else None
    gt = "gtfs_metro" if region == "cincinnati" else "gtfs_bcrta"
    s = gpd.read_parquet(d / f"{gt}.entities.parquet")
    if "geometry" not in s or s.geometry.isna().all():
        s = gpd.GeoDataFrame(
            s, geometry=gpd.points_from_xy(s.stop_lon.astype(float), s.stop_lat.astype(float)), crs=WGS84
        )
    stops = _metric(s)
    for f in feats:
        p = f["properties"]
        if p["layer"] in ("trail", "restroom", "event"):
            continue
        here = gpd.GeoSeries([point(f["geometry"])], crs=WGS84).to_crs(METRIC).iloc[0]
        centre, mine = here, None
        if bld is not None:
            oid = p.get("matched_to", "").split(" ")[0]
            hit = bld[bld.entity_id == oid]
            if hit.empty:
                hit = bld[bld.contains(here)]
            if not hit.empty:
                centre, mine = hit.geometry.iloc[0].centroid, set(json.loads(hit.entrance_ids.iloc[0]))
        near = ent[ent.entity_id.isin(mine)] if mine else ent.iloc[list(ent.sindex.query(here.buffer(80)))]
        parts, door_pt = [], None
        ok = near[near.wc.isin(["yes", "designated"])]
        if len(ok):
            best = ok.iloc[ok.distance(here).argmin()]
            door_pt = best.geometry
            t = best.t
            bits = []
            if centre.distance(door_pt) > 8:
                bits.append(f"on the {_towards(centre, door_pt)} side")
            if t.get("addr:street"):
                bits.append(f"on {t['addr:street']}")
            what = t.get("name") or ("main entrance" if t.get("entrance") == "main" else "entrance")
            door = DOORS.get(t.get("door", ""))
            parts.append(
                f"A wheelchair-accessible {what} is mapped "
                + " ".join(bits)
                + (f", {door}" if door else "")
                + "."
            )
            if len(ok) > 1:
                parts.append(f"{len(ok)} accessible entrances are mapped in all.")
            mains = near[(near.t.map(lambda x: x.get("entrance")) == "main") & (near.wc == "no")]
            if len(mains):
                parts.append("The main entrance is mapped as not accessible; use the accessible one.")
        elif len(near[near.wc == "no"]):
            parts.append(
                f"{len(near)} nearby entrance{'s are' if len(near) > 1 else ' is'} mapped as not "
                "wheelchair accessible; no accessible entrance is mapped. Call ahead."
            )
        said = [x for x in p.get("facts", []) if x["attribute"] == "Step-free entrance" and x.get("detail")]
        if said:
            parts.append(f"The venue says: {said[0]['detail']}.")
        target = door_pt or here
        idx = list(stops.sindex.query(target.buffer(800)))
        if idx:
            c = stops.iloc[idx]
            dist = c.distance(target)
            st = c.iloc[dist.argmin()]
            parts.append(
                f"From the {_stop(st.stop_name)} bus stop, "
                f"the {'accessible entrance' if door_pt is not None else 'place'} is {_feet(dist.min())} "
                f"to the {_towards(st.geometry, target)}, in a straight line."
            )
        if not parts:
            continue
        p.setdefault("getting_there", {})["arrival"] = " ".join(parts)
