"""Wheelchair routes on the walking network (osm_walk_network), described in words.

Cost of an edge = its length times a penalty:
  stairs                        not used at all
  steeper than a ramp (8.33%)   x 6     (DEM estimate; ADA ramp limit)
  5% - 8.33%                    x 1.6   (ADA walkway limit is 5%)
  road with sidewalk=no         x 3
  road, sidewalk not mapped     x 1.4   (we do not know a sidewalk exists)
  unpaved / rough surface       x 2
  raised kerb at either end     x 4
Footways, sidewalks, paths and crossings carry no extra penalty.

route() returns the easiest route and the shortest route, so the answer can say what the detour
buys ("120 feet longer, avoids 2 stairways"). It is a computed suggestion from map data, never
checked on site; the text says so.
"""

from __future__ import annotations

import math
from functools import cache

import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .core import PROCESSED

COMPASS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
ROUGH = {
    "gravel",
    "dirt",
    "grass",
    "ground",
    "unpaved",
    "sand",
    "mud",
    "pebblestone",
    "rock",
    "woodchips",
    "fine_gravel",
    "compacted",
    "sett",
    "cobblestone",
    "unhewn_cobblestone",
}
ROADS = {
    "residential",
    "service",
    "unclassified",
    "tertiary",
    "secondary",
    "primary",
    "trunk",
    "living_street",
    "road",
    "track",
}
FT = 3.28084


def penalty(e: dict) -> float:
    if e["steps"]:
        return math.inf
    p = 1.0
    g = e.get("grade")
    if g is not None and not (isinstance(g, float) and math.isnan(g)):
        p *= 6 if g > 8.33 else 1.6 if g > 5 else 1
    if e["highway"] in ROADS and e["footway"] is None:
        sw = (e.get("sidewalk") or "").lower()
        p *= 3 if sw in ("no", "none") else 1.4 if sw in ("", "separate") else 1
    if (e.get("surface") or "") in ROUGH:
        p *= 2
    if e.get("raised_kerb"):
        p *= 4
    return p


def is_crossing(e: dict) -> bool:
    return e.get("footway") == "crossing" or e.get("highway") == "crossing"


def _yes(v) -> bool:
    return v is True or v == "yes"


def blind_penalty(e: dict) -> float:
    """Extra weight for crossings a blind traveller would avoid: unmarked or unsignalised ones.
    Signals with sound or vibration are preferred; tactile paving helps find the kerb edge."""
    if not is_crossing(e):
        return 1.0
    kind = (e.get("crossing") or "").lower()
    if _yes(e.get("sound")) or _yes(e.get("vibration")):
        p = 1.0
    elif e.get("signals") is True or kind == "traffic_signals":
        p = 1.3
    elif kind in ("marked", "zebra", "uncontrolled"):
        p = 2.0
    else:  # unmarked or not mapped
        p = 3.5
    return p * (0.9 if e.get("tactile") is True else 1.0)


@cache
def network(region: str):
    """(graph, node table, KD-tree) for a region, built once per process."""
    nodes = pd.read_parquet(PROCESSED / region / "walk_nodes.parquet")
    edges = pd.read_parquet(PROCESSED / region / "walk_edges.parquet")
    raised = set(nodes.node_id[nodes.kerb == "raised"])
    g = nx.Graph()
    for e in edges.to_dict("records"):
        e["raised_kerb"] = e["u"] in raised or e["v"] in raised
        e["grade"] = None if pd.isna(e["grade"]) else float(e["grade"])
        for k in ("crossing", "sound", "vibration"):
            e[k] = None if pd.isna(e.get(k)) else e.get(k)
        for k in ("signals", "tactile"):
            e[k] = None if pd.isna(e.get(k)) else bool(e.get(k))
        cost = e["length_m"] * penalty(e)
        if g.has_edge(e["u"], e["v"]) and g[e["u"]][e["v"]]["cost"] <= cost:
            continue
        g.add_edge(e["u"], e["v"], cost=cost, cost_blind=cost * blind_penalty(e), **e)
    nodes = nodes[nodes.node_id.isin(g.nodes)].reset_index(drop=True)
    lat0 = math.radians(nodes.lat.mean())
    xy = np.c_[nodes.lon.values * math.cos(lat0), nodes.lat.values] * 111_320
    _name_sidewalks(g, nodes, lat0)
    return g, nodes, cKDTree(xy), lat0


def _name_sidewalks(g, nodes: pd.DataFrame, lat0: float) -> None:
    """OSM draws sidewalks as separate, unnamed lines. Name each after the nearest named street
    within 25 m, so directions can say 'the High Street sidewalk'."""
    pos = dict(zip(nodes.node_id, zip(nodes.lon, nodes.lat, strict=True), strict=True))

    def mid(a, b):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        return ((x1 + x2) / 2 * math.cos(lat0) * 111_320, (y1 + y2) / 2 * 111_320)

    named = [(a, b, d["name"]) for a, b, d in g.edges(data=True) if d["name"] and d["highway"] in ROADS]
    if not named:
        return
    tree = cKDTree([mid(a, b) for a, b, _ in named])
    for a, b, d in g.edges(data=True):
        if d["name"] is None and d["footway"] == "sidewalk":
            dist, i = tree.query(mid(a, b))
            if dist <= 25:
                d["name"] = f"the {named[i][2]} sidewalk"


def _snap(region: str, lat: float, lon: float) -> tuple[int, float]:
    g, nodes, tree, lat0 = network(region)
    d, i = tree.query([lon * math.cos(lat0) * 111_320, lat * 111_320])
    return int(nodes.node_id[i]), float(d)


def _bearing(a, b) -> float:
    (x1, y1), (x2, y2) = a, b
    return (math.degrees(math.atan2((x2 - x1) * math.cos(math.radians(y1)), y2 - y1)) + 360) % 360


def _turn(prev: float, new: float) -> str:
    d = (new - prev + 540) % 360 - 180
    if abs(d) < 30:
        return "continue"
    if abs(d) > 150:
        return "turn around"
    side = "right" if d > 0 else "left"
    return f"turn {side}" if abs(d) > 60 else f"bear {side}"


def _legs(g, nodes_xy: dict, path: list[int]) -> list[dict]:
    """Group consecutive edges with the same street or path name into legs."""
    legs = []
    for a, b in zip(path, path[1:], strict=False):
        e = g[a][b]
        name = e["name"] or {
            "footway": "the sidewalk"
            if e["footway"] == "sidewalk"
            else "the crosswalk"
            if e["footway"] == "crossing"
            else "a footpath",
            "crossing": "the crosswalk",
            "path": "a path",
            "pedestrian": "a pedestrian walkway",
            "service": "a service drive",
            "cycleway": "a bike path",
        }.get(e["highway"], "an unnamed way")
        if e["footway"] == "crossing" or e["highway"] == "crossing":
            name = "the crosswalk"
        brg = _bearing(nodes_xy[a], nodes_xy[b])
        if legs and legs[-1]["name"] == name:
            leg = legs[-1]
        else:
            leg = {
                "name": name,
                "length_m": 0.0,
                "start_bearing": brg,
                "end_bearing": brg,
                "steep": 0,
                "max_grade": 0.0,
            }
            legs.append(leg)
        leg["length_m"] += e["length_m"]
        leg["end_bearing"] = brg
        if (
            e["highway"] in ROADS
            and e["footway"] is None
            and (e.get("sidewalk") or "") in ("", "no", "none", "separate")
        ):
            leg["road_m"] = leg.get("road_m", 0.0) + e["length_m"]
        if name == "the crosswalk":
            c = leg.setdefault("cross", {"signals": False, "audible": False, "tactile": False, "kind": None})
            c["signals"] |= e.get("signals") is True or (e.get("crossing") or "") == "traffic_signals"
            c["audible"] |= _yes(e.get("sound")) or _yes(e.get("vibration"))
            c["tactile"] |= e.get("tactile") is True
            c["kind"] = c["kind"] or e.get("crossing")
        if e["grade"] is not None:
            leg["max_grade"] = max(leg["max_grade"], e["grade"])
            leg["steep"] += e["grade"] > 8.33
    # fold tiny legs (under 8 m) into their neighbours so directions stay readable
    out = []
    for leg in legs:
        if out and leg["length_m"] < 8 and leg["name"] != "the crosswalk":
            out[-1]["length_m"] += leg["length_m"]
            out[-1]["end_bearing"] = leg["end_bearing"]
            continue
        if out and out[-1]["name"] == leg["name"]:  # e.g. two crosswalk pieces in a row
            if "cross" in leg:
                c = out[-1].setdefault("cross", dict(leg["cross"]))
                for k in ("signals", "audible", "tactile"):
                    c[k] |= leg["cross"][k]
                c["kind"] = c["kind"] or leg["cross"]["kind"]
            out[-1]["length_m"] += leg["length_m"]
            out[-1]["end_bearing"] = leg["end_bearing"]
            out[-1]["steep"] += leg["steep"]
            out[-1]["max_grade"] = max(out[-1]["max_grade"], leg["max_grade"])
            continue
        out.append(leg)
    return out


def _feet(m: float) -> str:
    ft = m * FT
    return f"{max(10, round(ft / 10) * 10)} feet" if ft < 1000 else f"{ft / 5280:.1f} miles"


def _crossing_words(c: dict) -> tuple[str, str]:
    """(what to do, details) for a crossing, e.g. ("Cross at the traffic signal", "audible signal")."""
    extra = "; tactile paving at the curb" if c.get("tactile") else ""
    if c.get("signals"):
        sig = "audible signal" if c.get("audible") else "no audible signal mapped"
        return "Cross at the traffic signal", sig + extra
    kind = c.get("kind")
    if kind in ("marked", "zebra", "uncontrolled"):
        return "Cross at the marked crosswalk", "no signal" + extra
    if kind == "unmarked":
        return "Cross at an unmarked crossing", "no signal" + extra
    return "Cross the street", "crossing type not mapped" + extra


def _describe(legs: list[dict]) -> list[str]:
    steps = []
    for i, leg in enumerate(legs):
        heading = COMPASS[round(leg["start_bearing"] / 45) % 8]
        if leg["name"] == "the crosswalk":
            head, detail = _crossing_words(leg.get("cross") or {})
            s = f"{head}, {_feet(leg['length_m'])} ({detail})"
        elif i == 0:
            s = f"Head {heading} on {leg['name']} for {_feet(leg['length_m'])}"
        else:
            t = _turn(legs[i - 1]["end_bearing"], leg["start_bearing"])
            verb = "Continue" if t == "continue" else t.capitalize()
            s = f"{verb} onto {leg['name']} for {_feet(leg['length_m'])}"
        if leg.get("road_m", 0) > 0.5 * leg["length_m"]:
            s += "; no sidewalk mapped here"
        if leg["steep"]:
            n = leg["steep"]
            s += f"; caution: {n} short section{'s' if n > 1 else ''} steeper than a ramp"
        steps.append(s + ".")
    return steps


def _summary(g, path: list[int]) -> dict:
    es = [g[a][b] for a, b in zip(path, path[1:], strict=False)]
    grades = [e["grade"] for e in es if e["grade"] is not None]
    return {
        "length_m": round(sum(e["length_m"] for e in es), 1),
        "steep_sections": sum(gr > 8.33 for gr in grades),
        "steps": sum(bool(e["steps"]) for e in es),
        "road_without_sidewalk_m": round(
            sum(
                e["length_m"]
                for e in es
                if e["highway"] in ROADS
                and e["footway"] is None
                and (e.get("sidewalk") or "") in ("", "no", "none", "separate")
            ),
            1,
        ),
        "raised_kerbs": sum(bool(e.get("raised_kerb")) for e in es),
        "crossings": _crossing_counts(es),
    }


def _crossing_counts(es: list[dict]) -> dict:
    """Count crossings once per street crossed (consecutive crossing edges are one crossing)."""
    out = {"total": 0, "signals": 0, "audible": 0, "marked": 0, "unmarked_or_unknown": 0, "tactile": 0}
    prev = False
    for e in es:
        cur = is_crossing(e)
        if cur and not prev:
            out["total"] += 1
            kind = (e.get("crossing") or "").lower()
            if e.get("signals") is True or kind == "traffic_signals":
                out["signals"] += 1
                out["audible"] += _yes(e.get("sound")) or _yes(e.get("vibration"))
            elif kind in ("marked", "zebra", "uncontrolled"):
                out["marked"] += 1
            else:
                out["unmarked_or_unknown"] += 1
            out["tactile"] += e.get("tactile") is True
        prev = cur
    return out


def crossing_sentence(c: dict) -> str:
    if not c or not c["total"]:
        return "No street crossings."
    parts = []
    if c["signals"]:
        parts.append(f"{c['signals']} with traffic signals ({c['audible']} audible)")
    if c["marked"]:
        parts.append(f"{c['marked']} marked without a signal")
    if c["unmarked_or_unknown"]:
        parts.append(f"{c['unmarked_or_unknown']} unmarked or not mapped")
    n = c["total"]
    return f"{n} street crossing{'s' if n > 1 else ''}: " + ", ".join(parts) + "."


def route(
    region: str, from_lat: float, from_lon: float, to_lat: float, to_lon: float, profile: str = "wheelchair"
) -> dict | None:
    """Easiest wheelchair route between two points, with directions in words, plus a comparison
    with the shortest route. profile="blind" also prefers signalised (ideally audible) crossings
    and avoids unmarked ones. None when either end is more than 150 m from the network or no
    step-free route exists."""
    g, nodes, _, _ = network(region)
    a, da = _snap(region, from_lat, from_lon)
    b, db = _snap(region, to_lat, to_lon)
    if da > 150 or db > 150:
        return None
    try:
        easy = nx.shortest_path(g, a, b, weight="cost_blind" if profile == "blind" else "cost")
    except nx.NetworkXNoPath:
        return None
    if not math.isfinite(nx.path_weight(g, easy, "cost")):
        return None  # only reachable by stairs
    short = nx.shortest_path(g, a, b, weight="length_m")
    xy = dict(zip(nodes.node_id, zip(nodes.lon, nodes.lat, strict=True), strict=True))
    legs = _legs(g, xy, easy)
    s_easy, s_short = _summary(g, easy), _summary(g, short)
    extra = s_easy["length_m"] - s_short["length_m"]
    why = []
    for key, word in (("steps", "stair section"), ("steep_sections", "steep section")):
        n = s_short[key] - s_easy[key]
        if n > 0:
            why.append(f"{n} {word}{'s' if n > 1 else ''}")
    compare = (
        f"About {_feet(extra)} longer than the shortest way, to avoid " + " and ".join(why) + "."
        if extra > 15 and why
        else "This is also the shortest way."
    )
    return {
        "length_feet": round(s_easy["length_m"] * FT),
        "steep_sections": s_easy["steep_sections"],
        "steps": s_easy["steps"],
        "raised_kerbs": s_easy["raised_kerbs"],
        "crossings": s_easy["crossings"],
        "crossings_text": crossing_sentence(s_easy["crossings"]),
        "profile": profile,
        "road_without_sidewalk_feet": round(s_easy["road_without_sidewalk_m"] * FT),
        "directions": _describe(legs),
        "compared_with_shortest": compare,
        "shortest": {
            "length_feet": round(s_short["length_m"] * FT),
            "steps": s_short["steps"],
            "steep_sections": s_short["steep_sections"],
        },
        "line": [[round(xy[n][0], 6), round(xy[n][1], 6)] for n in easy],
        "snap_feet": [round(da * FT), round(db * FT)],
        "note": "Computed from OpenStreetMap paths and USGS elevation; not checked on site. "
        "Slopes are estimates; sidewalks and curb ramps may be missing from the map.",
    }
