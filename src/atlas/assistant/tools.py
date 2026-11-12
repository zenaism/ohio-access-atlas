"""Lookup tools the assistant calls. Plain Python on the DuckDB knowledge base, so they can be
tested and evaluated without any language model.

Every result carries its evidence: the place's text page, and for each fact the source URL, date
and verbatim quote. The assistant may only say what these results say; "not known" is an answer.

TOOL_SPECS describes each tool (name, purpose, JSON-schema input) for a future agent loop.
"""

from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta

from .kb import connect

COMPASS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
RATING_ORDER = {"accessible": 0, "partial": 1, "not_accessible": 2, "unknown": 3}

# need -> how to recognise it: fact labels whose value says yes/limited, or a test on the place row
NEEDS = {
    "accessible_restroom": {
        "facts": ["Accessible restroom", "toilets:wheelchair", "Family / universal restroom"],
        "restroom_layer": True,
    },
    "adult_changing_table": {"facts": ["Adult changing table"]},
    "step_free_entrance": {"facts": ["Step-free entrance", "Accessible entrance", "entrance:wheelchair"]},
    "elevator": {"facts": ["Elevator / lift"]},
    "accessible_parking": {"facts": ["Accessible parking"]},
    "wheelchair_seating": {"facts": ["Wheelchair seating"]},
    "wheelchair_loan": {"facts": ["Wheelchair loan", "Scooter / ECV"]},
    "all_terrain_chair": {"facts": ["All-terrain wheelchair"]},
    "accessible_path": {"facts": ["Path surface"], "layers": ["trail"]},
    "accessible_lodging": {"facts": ["Accessible rooms"]},
    "braille": {"facts": ["Braille"]},
    "audio_description": {"facts": ["Audio description"]},
    "large_print": {"facts": ["Large print"]},
    "touch": {"facts": ["Touch / tactile"]},
    "service_animals": {"facts": ["Service animals"]},
    "sensory_friendly": {"facts": ["Sensory-friendly", "Quiet room"]},
    "listed_wheelchair_accessible": {"facts": ["Listed wheelchair accessible", "wheelchair"]},
    "mobility_service": {"facts": ["Mobility service"]},
    "paratransit": {"facts": ["Transit"]},
}
POSITIVE = ("yes", "designated", "limited")


def _con():
    return connect()


def _miles(lat1, lon1, lat2, lon2) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _direction(lat1, lon1, lat2, lon2) -> str:
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.cos(math.radians(lon2 - lon1))
    return COMPASS[round(((math.degrees(math.atan2(y, x)) + 360) % 360) / 45) % 8]


def _ids_with_need(con, need: str) -> set[str]:
    spec = NEEDS[need]
    ids = set()
    if spec.get("facts"):
        attrs, vals = ",".join("?" * len(spec["facts"])), ",".join("?" * len(POSITIVE))
        q = (
            f"SELECT DISTINCT link_id FROM facts WHERE attribute IN ({attrs}) "
            f"AND split_part(value, ';', -1) IN ({vals})"
        )
        ids |= {r[0] for r in con.execute(q, [*spec["facts"], *POSITIVE]).fetchall()}
    if spec.get("restroom_layer"):
        q = "SELECT link_id FROM places WHERE layer='restroom' AND rating IN ('accessible','partial')"
        ids |= {r[0] for r in con.execute(q).fetchall()}
    if spec.get("layers"):
        q = f"SELECT link_id FROM places WHERE layer IN ({','.join('?' * len(spec['layers']))})"
        ids |= {r[0] for r in con.execute(q, spec["layers"]).fetchall()}
    return ids


def _brief(row: dict, here: tuple[float, float] | None = None) -> dict:
    out = {
        "link_id": row["link_id"],
        "name": row["name"],
        "region": row["region"],
        "type": row["layer"],
        "rating": row["rating"],
        "what_is_known": json.loads(row["keys"]),
        "summary": row["summary"],
        "notice": row["notice"],
        "newest_source": row["newest_source"],
        "page": row["page"],
    }
    if here:
        out["miles"] = round(_miles(here[0], here[1], row["lat"], row["lon"]), 2)
        out["direction"] = _direction(here[0], here[1], row["lat"], row["lon"])
    return out


def _places(con, where: str = "TRUE", params: list | None = None) -> list[dict]:
    cur = con.execute(f"SELECT * FROM places WHERE {where}", params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]


def _words(s: str) -> list[str]:
    stop = {"the", "a", "an", "of", "in", "at", "and", "is", "to", "for", "on", "my", "me", "near"}
    return [w for w in re.findall(r"[a-z0-9']+", str(s or "").lower()) if w not in stop and len(w) > 1]


# ------------------------------------------------------------------ tools ----
def search_places(
    query: str = "",
    region: str | None = None,
    place_type: str | None = None,
    need: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Places whose name, summary or facts match the words, best match first.
    Filters: region ('cincinnati'/'oxford'), place_type (map layer), need (see NEEDS)."""
    con = _con()
    where, params = ["TRUE"], []
    if region:
        where.append("region = ?")
        params.append(region)
    if place_type:
        where.append("layer = ?")
        params.append(place_type)
    rows = _places(con, " AND ".join(where), params)
    if need:
        ok = _ids_with_need(con, need)
        rows = [r for r in rows if r["link_id"] in ok]
    words = _words(query)
    text = {}
    if words:
        for lid, blob in con.execute(
            "SELECT link_id, string_agg(lower(attribute||' '||detail), ' ') FROM facts GROUP BY link_id"
        ).fetchall():
            text[lid] = blob
    # rare words count more: "smale" identifies a place, "park" does not
    names = [r["name"].lower() for r in _places(con)]
    weight = {w: 1 / math.log(2 + sum(w in n for n in names)) for w in words}
    scored = []
    for r in rows:
        name = r["name"].lower()
        if words:
            in_name = sum(weight[w] for w in words if w in name)
            body = r["summary"].lower() + " " + text.get(r["link_id"], "")
            in_body = sum(weight[w] for w in words if w in body)
            if in_name == 0 and in_body == 0:
                continue
            exact = 3 if " ".join(words) in name else 0
            score = exact + 2 * in_name + 0.5 * in_body
        else:
            score = 0
        scored.append((-score, RATING_ORDER[r["rating"]], -len(json.loads(r["keys"])), r["name"], r))
    scored.sort(key=lambda t: t[:4])
    return [_brief(t[4]) for t in scored[:limit]]


def nearest(
    lat: float,
    lon: float,
    need: str | None = None,
    place_type: str | None = None,
    max_miles: float = 5.0,
    limit: int = 5,
) -> list[dict]:
    """Closest places to a point that meet a need (e.g. accessible_restroom), with miles and direction.
    Straight-line distance, not a route."""
    con = _con()
    rows = _places(
        con, "lat IS NOT NULL" + (" AND layer = ?" if place_type else ""), [place_type] if place_type else []
    )
    if need:
        ok = _ids_with_need(con, need)
        rows = [r for r in rows if r["link_id"] in ok]
    hits = sorted(((_miles(lat, lon, r["lat"], r["lon"]), r) for r in rows), key=lambda t: t[0])
    return [_brief(r, (lat, lon)) for d, r in hits if d <= max_miles][:limit]


def get_place(name_or_id: str, region: str | None = None) -> dict | None:
    """Everything known about one place: facts with source, date and quote; arriving and getting
    there; upcoming events; who to ask. Accepts a link_id or a name."""
    con = _con()
    rows = _places(con, "link_id = ?", [name_or_id])
    if not rows:
        hit = search_places(name_or_id, region=region, limit=1)
        rows = _places(con, "link_id = ?", [hit[0]["link_id"]]) if hit else []
    if not rows:
        return None
    r = rows[0]
    out = _brief(r)
    cur = con.execute(
        "SELECT attribute, value, detail, quote, source, date FROM facts WHERE link_id = ?", [r["link_id"]]
    )
    out["facts"] = [dict(zip([d[0] for d in cur.description], x, strict=True)) for x in cur.fetchall()]
    out["getting_there"] = json.loads(r["getting_there"])
    out["contacts"] = json.loads(r["contacts"])
    out["events"] = find_events(link_id=r["link_id"], limit=10)
    out["data_as_of"] = r["generated"]
    return out


def find_events(
    region: str | None = None,
    start: str | None = None,
    end: str | None = None,
    access: list[str] | None = None,
    disability_focused: bool | None = None,
    query: str = "",
    link_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Upcoming events, soonest first. start/end are dates (YYYY-MM-DD; default today to +30 days).
    access: any of audio_description, asl, sensory_friendly."""
    con = _con()
    start = start or date.today().isoformat()
    end = end or (date.fromisoformat(start) + timedelta(days=30)).isoformat()
    where = ["substr(e.start, 1, 10) BETWEEN ? AND ?"]
    params: list = [start, end]
    if region:
        where.append("p.region = ?")
        params.append(region)
    if link_id:
        where.append("e.link_id = ?")
        params.append(link_id)
    if disability_focused:
        where.append("e.disability_focused")
    if access:
        where.append("(" + " OR ".join("e.access LIKE ?" for _ in access) + ")")
        params += [f"%{a}%" for a in access]
    for w in _words(query):
        where.append("lower(e.title) LIKE ?")
        params.append(f"%{w}%")
    cur = con.execute(
        f"""SELECT e.title, e.start, e.url, e.access, e.accessible_tag, e.disability_focused,
                   p.name AS place, p.link_id, p.rating, p.page
            FROM events e JOIN places p USING (link_id) WHERE {" AND ".join(where)}
            ORDER BY e.start, e.title LIMIT ?""",
        [*params, limit],
    )
    cols = [d[0] for d in cur.description]
    out = []
    for x in cur.fetchall():
        e = dict(zip(cols, x, strict=True))
        e["access"] = [a for a in e["access"].split(",") if a]
        out.append(e)
    return out


TOOL_SPECS = [
    {
        "name": "search_places",
        "description": "Find places by name or words, optionally filtered by region, type and access need. "
        "Use to identify a place the user names, or to list places that meet a need.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "region": {"type": "string", "enum": ["cincinnati", "oxford"]},
                "place_type": {
                    "type": "string",
                    "enum": [
                        "culture",
                        "park",
                        "trail",
                        "restroom",
                        "adaptive_recreation",
                        "lodging",
                        "building",
                        "food_drink",
                        "service",
                        "event",
                        "organization",
                    ],
                },
                "need": {"type": "string", "enum": sorted(NEEDS)},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "nearest",
        "description": "Closest places to a latitude/longitude that meet an access need, with straight-line "
        "miles and compass direction. Use for 'near me' or 'near <place>' (get the place's point first).",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lon": {"type": "number"},
                "need": {"type": "string", "enum": sorted(NEEDS)},
                "place_type": {"type": "string"},
                "max_miles": {"type": "number"},
                "limit": {"type": "integer"},
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "name": "get_place",
        "description": "All facts about one place with source, date and verbatim quote, how to get there, "
        "upcoming events and contacts. Answer only from these; say 'not known' for anything missing.",
        "input_schema": {
            "type": "object",
            "properties": {"name_or_id": {"type": "string"}, "region": {"type": "string"}},
            "required": ["name_or_id"],
        },
    },
    {
        "name": "find_events",
        "description": "Upcoming events by date range, region, words, and access kind "
        "(audio_description, asl, sensory_friendly) or disability focus.",
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": ["cincinnati", "oxford"]},
                "start": {"type": "string", "description": "YYYY-MM-DD"},
                "end": {"type": "string", "description": "YYYY-MM-DD"},
                "access": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["audio_description", "asl", "sensory_friendly"]},
                },
                "disability_focused": {"type": "boolean"},
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
]
TOOLS = {
    "search_places": search_places,
    "nearest": nearest,
    "get_place": get_place,
    "find_events": find_events,
}
