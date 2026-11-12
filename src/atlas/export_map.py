"""Build the atlas map: one GeoJSON per region + a self-contained HTML viewer + a review list.

  data/map/<region>_atlas.geojson   FeatureCollection (WGS84), one feature per place/trail/event venue
  data/map/atlas_viewer.html        open by double-click: icons per layer, colour per access rating, legend
  data/map/review.csv               everything that could not be placed, and why

Nothing is placed by fuzzy guessing: fact places are pinned in config/place_matches.yaml; event venues
are matched by exact name, by a park name in the event text, or by street address (U.S. Census
geocoder). Whatever fails goes to review.csv.
"""

from __future__ import annotations

import json
import re
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

                hit = pd.Series({"entity_id": f"census:{r.venue}", "name": r.venue, "geometry": Point(*xy)})
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
    feats = []
    for eid, v in venues.items():
        evs = sorted(v["events"], key=lambda e: e["start"])
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
        feats += restroom_features(region) + event_features(region, g, matches, places, review)
        enrich(feats, g)
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
    named = g[g.category.str.contains("park|museum|garden|attraction|library|theatre|stadium|zoo|nature")]
    named = named[
        (named.name.str.len() > 3)
        & ~named.category.str.contains("parking", case=False)
        & ~named.name.str.contains(r"\bparking\b|\blot\b", case=False)
    ]
    pts = gpd.GeoDataFrame(named[["name"]], geometry=named.geometry.map(point), crs=WGS84).to_crs(METRIC)
    anyp = g[
        (g.name.str.len() > 3)
        & ~g.category.str.contains("parking", case=False)
        & ~g.name.str.contains(r"^parking|\bparking\b|\blot\b", case=False)
    ]
    allpts = gpd.GeoDataFrame(anyp[["name"]], geometry=anyp.geometry.map(point), crs=WGS84).to_crs(METRIC)

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
            best = nearest_name(here, pts, 400) or nearest_name(here, allpts, 250)
            if best:
                p["name"] = f"Restroom near {best}"
        p["summary"] = summarise(p)
        p["contacts"] = contacts(p)
