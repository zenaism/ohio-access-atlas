"""OpenStreetMap entrances that say whether a wheelchair can use them, grouped by the building they
belong to. Miami University's campus is mapped this way in detail, which fills the gap left by the
current campus parking map (it no longer marks accessible entrances).

Output entities: one row per named building that has at least one entrance with a wheelchair tag:
name, building tags, polygon, counts of entrances tagged yes / limited / no, and the entrance ids.
"""

from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from ..core import WGS84, config, fetch, now, observations, save
from .overpass import URL

Q = """[out:json][timeout:600];{area}
node["entrance"]["wheelchair"](area.a)->.e;
node["entrance"]["entrance:wheelchair"](area.a)->.e2;
(.e;.e2;)->.ents;
.ents out tags;
way(bn.ents)["building"];
out body geom;"""


def run(name: str, spec: dict, region: str) -> None:
    area = f"area({3600000000 + config('regions')[region]['osm_relation']})->.a;"
    els = json.loads(fetch(URL, method="POST", data={"data": Q.format(area=area)}, timeout=900))["elements"]
    ents = {e["id"]: e.get("tags", {}) for e in els if e["type"] == "node"}
    rows = []
    for w in (e for e in els if e["type"] == "way"):
        t = w.get("tags", {})
        if not t.get("name") or not w.get("geometry") or len(w["geometry"]) < 4:
            continue
        mine = [n for n in w.get("nodes", []) if n in ents]
        vals = [ents[n].get("wheelchair") or ents[n].get("entrance:wheelchair") for n in mine]
        rows.append(
            {
                "entity_id": f"osm:way/{w['id']}",
                "entity_type": "building",
                "name": t["name"],
                "category": f"building={t.get('building')}",
                "tags": json.dumps(t, sort_keys=True),
                "entrances_yes": sum(v in ("yes", "designated") for v in vals),
                "entrances_limited": sum(v == "limited" for v in vals),
                "entrances_no": sum(v == "no" for v in vals),
                "entrance_ids": json.dumps([f"osm:node/{n}" for n in mine]),
                "geometry": Polygon([(p["lon"], p["lat"]) for p in w["geometry"]]),
            }
        )
    ent = gpd.GeoDataFrame(rows, crs=WGS84) if rows else gpd.GeoDataFrame(columns=["geometry"], crs=WGS84)
    if ent.empty:
        save(region, name, ent, pd.DataFrame())
        return
    ent = ent.drop_duplicates("entity_id")
    ent["value"] = ent.apply(
        lambda r: f"{r.entrances_yes} yes, {r.entrances_limited} limited, {r.entrances_no} no", axis=1
    )
    obs = observations(
        ent,
        entity_id=ent.entity_id,
        entity_type="building",
        name=ent.name,
        category=ent.category,
        attribute="entrance_wheelchair_counts",
        value=ent.value,
        signal=["supports" if y else "barrier" for y in ent.entrances_yes],
        source=name,
        source_ref="https://www.openstreetmap.org/" + ent.entity_id.str[4:],
        retrieved_at=now(),
        license=spec["license"],
        region=region,
    )
    save(region, name, ent.drop(columns="value"), obs)
