"""OpenStreetMap via Overpass: POIs, pedestrian network, and point features."""

from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point

from ..core import WGS84, config, fetch, now, observations, save
from ..signals import signal

URL = "https://overpass-api.de/api/interpreter"

POI_KEYS = [
    "amenity",
    "shop",
    "tourism",
    "leisure",
    "healthcare",
    "office",
    "public_transport",
    "railway",
    "building",
    "craft",
    "historic",
]
# Tags emitted as observations. Everything else is kept in the entity table's `tags`.
OBS_TAGS = {
    "wheelchair",
    "wheelchair:description",
    "toilets:wheelchair",
    "entrance:wheelchair",
    "ramp:wheelchair",
    "automatic_door",
    "step_count",
    "kerb",
    "surface",
    "smoothness",
    "incline",
    "width",
    "est_width",
    "sidewalk:width",
    "sidewalk:surface",
    "sidewalk:both:surface",
    "sidewalk:left:surface",
    "sidewalk:right:surface",
    "sidewalk:smoothness",
    "tactile_paving",
    "handrail",
    "barrier",
    "elevator",
    "lit",
    "crossing",
    "crossing:signals",
    "traffic_signals:sound",
    "capacity:disabled",
    "parking_space",
}

QUERIES = {
    "pois": "(" + "".join(f'nwr["name"]["{k}"](area.a);' for k in POI_KEYS) + ");out tags center;",
    "network": (
        '(way["highway"~"^(footway|path|pedestrian|steps|living_street|corridor|elevator)$"]'
        '(area.a);way["highway"]["sidewalk"](area.a);way["highway"]["sidewalk:both"](area.a);'
        'way["highway"]["sidewalk:left"](area.a);way["highway"]["sidewalk:right"](area.a););'
        "out tags geom;"
    ),
    "points": (
        '(node["kerb"](area.a);node["highway"="crossing"](area.a);node["barrier"](area.a);'
        'node["highway"="elevator"](area.a);node["entrance"](area.a);'
        'nwr["amenity"="parking_space"](area.a);nwr["amenity"="toilets"](area.a););out tags center;'
    ),
}


def _geom(el):
    if el.get("geometry"):
        return LineString([(p["lon"], p["lat"]) for p in el["geometry"]])
    if "lat" in el:
        return Point(el["lon"], el["lat"])
    c = el.get("center")
    return Point(c["lon"], c["lat"]) if c else None


def _entity_type(layer: str, t: dict) -> str:
    if layer == "pois":
        return "poi"
    if layer == "network":
        return "path_segment"
    for key, et in (("kerb", "kerb"), ("entrance", "entrance"), ("barrier", "barrier")):
        if key in t:
            return et
    return "crossing" if t.get("highway") == "crossing" else "poi"


def _category(t: dict) -> str:
    return next((f"{k}={t[k]}" for k in [*POI_KEYS, "highway", "barrier", "entrance"] if k in t), "")


def run(name: str, spec: dict, region: str) -> pd.DataFrame:
    area = f"area({3600000000 + config('regions')[region]['osm_relation']})->.a;"
    retrieved, rows = now(), {}
    for layer, q in QUERIES.items():
        payload = {"data": f"[out:json][timeout:600];{area}{q}"}
        for el in json.loads(fetch(URL, method="POST", data=payload, timeout=900))["elements"]:
            eid = f"osm:{el['type']}/{el['id']}"
            if eid in rows or (geom := _geom(el)) is None:
                continue
            t = el.get("tags", {})
            rows[eid] = {
                "entity_id": eid,
                "entity_type": _entity_type(layer, t),
                "name": t.get("name", ""),
                "category": _category(t),
                "tags": json.dumps(t, sort_keys=True),
                "osm_version": el.get("version"),
                "geometry": geom,
            }
    ent = gpd.GeoDataFrame(list(rows.values()), crs=WGS84)

    # explode to one row per accessibility tag (plus highway=steps as a barrier)
    long = (
        ent.assign(
            tag=ent["tags"]
            .map(json.loads)
            .map(
                lambda t: [(k, v) for k, v in t.items() if k in OBS_TAGS or (k == "highway" and v == "steps")]
            )
        )
        .explode("tag")
        .dropna(subset=["tag"])
    )
    long["attribute"], long["value"] = long["tag"].str[0], long["tag"].str[1]
    obs = observations(
        long,
        entity_id=long.entity_id,
        entity_type=long.entity_type,
        name=long.name,
        category=long.category,
        attribute=long.attribute,
        value=long.value,
        signal=[signal(a, v) for a, v in zip(long.attribute, long.value, strict=True)],
        source=name,
        source_ref="https://www.openstreetmap.org/" + long.entity_id.str[4:],
        retrieved_at=retrieved,
        license=spec["license"],
        region=region,
    )
    save(region, name, ent, obs)
    return obs
