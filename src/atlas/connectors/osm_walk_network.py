"""Walking network for routing: every walkable OSM way inside the city limits, split into edges
between consecutive nodes, with the details a wheelchair route needs.

Output (data/processed/<region>/):
  walk_nodes.parquet  node_id, lon, lat, z (metres, USGS 3DEP), kerb (raised/lowered/flush/...)
  walk_edges.parquet  u, v, way_id, highway, name, length_m, grade (percent, from node
                      elevations), steps, bridge, sidewalk, surface, foot

Grades come from the local 3DEP tiles (`make dem`); they describe the ground, so they are left
empty on bridges and tunnels, where the DEM is wrong.
"""

from __future__ import annotations

import json
import math

import pandas as pd

from ..core import config, fetch, log, out_dir
from .overpass import URL

WALKABLE = (
    "footway|path|pedestrian|steps|living_street|corridor|residential|service|unclassified|"
    "tertiary|secondary|primary|trunk|cycleway|track|elevator|crossing|road"
)
Q = """[out:json][timeout:900];{area}
way["highway"~"^({walk})$"]["foot"!~"^(no|private)$"]["access"!~"^(no|private)$"](area.a)->.w;
.w out body geom;
(node(w.w)["kerb"];node(w.w)["highway"="crossing"];node(w.w)["crossing"];node(w.w)["tactile_paving"];
 node(w.w)["highway"="traffic_signals"];);
out tags;"""


def _metres(lon1, lat1, lon2, lat2) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _crossing(way: dict, na: dict, nb: dict) -> dict:
    """Crossing details that matter to blind travellers, from the crossing way or its nodes."""
    node = next((n for n in (na, nb) if n.get("highway") == "crossing" or "crossing" in n), {})
    tags = {**node, **way} if way.get("footway") == "crossing" or way.get("highway") == "crossing" else node
    signals = (
        tags.get("crossing") == "traffic_signals"
        or tags.get("crossing:signals") == "yes"
        or (na.get("highway") == "traffic_signals" or nb.get("highway") == "traffic_signals")
    )
    tactile = "yes" in {na.get("tactile_paving"), nb.get("tactile_paving"), tags.get("tactile_paving")}
    return {
        "crossing": tags.get("crossing") or ("traffic_signals" if signals and tags else None),
        "signals": bool(signals) if tags else None,
        "sound": tags.get("traffic_signals:sound"),
        "vibration": tags.get("traffic_signals:vibration"),
        "tactile": tactile,
    }


def run(name: str, spec: dict, region: str) -> None:
    area = f"area({3600000000 + config('regions')[region]['osm_relation']})->.a;"
    raw = fetch(URL, method="POST", data={"data": Q.format(area=area, walk=WALKABLE)}, timeout=1200)
    els = json.loads(raw)["elements"]
    ntags = {e["id"]: e.get("tags", {}) for e in els if e["type"] == "node"}
    kerb = {k: t.get("kerb") for k, t in ntags.items()}
    nodes, edges = {}, []
    for w in (e for e in els if e["type"] == "way"):
        t = w.get("tags", {})
        if t.get("highway") == "trunk" and t.get("sidewalk") in (None, "no", "none"):
            continue  # trunk roads without a sidewalk are not walkable
        ids, geom = w.get("nodes", []), w.get("geometry", [])
        if len(ids) != len(geom) or len(ids) < 2:
            continue
        for nid, g in zip(ids, geom, strict=True):
            nodes[nid] = (g["lon"], g["lat"])
        for (a, ga), (b, gb) in zip(
            zip(ids, geom, strict=True), zip(ids[1:], geom[1:], strict=True), strict=False
        ):
            edges.append(
                {
                    "u": a,
                    "v": b,
                    "way_id": w["id"],
                    "highway": t.get("highway"),
                    "name": t.get("name") or t.get("ref"),
                    "length_m": _metres(ga["lon"], ga["lat"], gb["lon"], gb["lat"]),
                    "steps": t.get("highway") == "steps",
                    "bridge": any(
                        t.get(k) not in (None, "no") for k in ("bridge", "tunnel", "covered", "indoor")
                    ),
                    "sidewalk": t.get("sidewalk") or t.get("sidewalk:both"),
                    "footway": t.get("footway"),
                    "surface": t.get("surface"),
                    "wheelchair": t.get("wheelchair"),
                    "incline": t.get("incline"),
                    # crossings: the way's own tags, or those of the crossing node at either end
                    **_crossing(t, ntags.get(a, {}), ntags.get(b, {})),
                }
            )
    nd = pd.DataFrame([(k, x, y) for k, (x, y) in nodes.items()], columns=["node_id", "lon", "lat"])
    nd["kerb"] = nd.node_id.map(kerb)
    try:
        from ..dem import sample

        nd["z"] = sample(region, nd.lon.values, nd.lat.values)
    except Exception as e:  # no DEM tiles: routes still work, without slope
        log.warning("[%s] %s: no elevation (%s); grades left empty", region, name, e)
        nd["z"] = float("nan")
    ed = pd.DataFrame(edges)
    z = nd.set_index("node_id").z
    dz = (ed.v.map(z) - ed.u.map(z)).abs()
    # grade over at least 10 m so tiny edges do not turn DEM noise into cliffs
    ed["grade"] = (dz / ed.length_m.clip(lower=10) * 100).where(~ed.bridge).round(1)
    d = out_dir(region)
    nd.to_parquet(d / "walk_nodes.parquet", index=False)
    ed.to_parquet(d / "walk_edges.parquet", index=False)
    log.info(
        "[%s] %s: %d nodes, %d edges (%.0f km), %d steps edges, %.0f%% with grade",
        region,
        name,
        len(nd),
        len(ed),
        ed.length_m.sum() / 1000,
        ed.steps.sum(),
        ed.grade.notna().mean() * 100,
    )
