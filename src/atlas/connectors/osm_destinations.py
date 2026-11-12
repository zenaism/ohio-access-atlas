"""OpenStreetMap destinations in the buffered region: trails, parks, restrooms, culture and
recreation. The `osm` source covers the street network inside city limits; this one reaches the
parks and trails people travel to."""
from __future__ import annotations

import json

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point

from ..core import WGS84, area, fetch, now, observations, save
from ..signals import signal
from .overpass import OBS_TAGS, URL

OBS = OBS_TAGS | {"changing_table", "changing_table:adult", "unisex", "fee", "opening_hours",
                  "access", "trail_visibility", "sac_scale", "mtb:scale", "length", "distance"}

# (layer, overpass statements); {b} = bbox
LAYERS = {
    "trail": ('way["highway"~"^(path|footway|cycleway|track|bridleway)$"]["name"]({b});'
              'relation["route"~"^(hiking|foot|bicycle|walking)$"]({b});'),
    "park": 'nwr["leisure"~"^(park|nature_reserve|garden|playground|dog_park|fishing)$"]["name"]({b});'
            'nwr["boundary"="protected_area"]["name"]({b});',
    "restroom": 'nwr["amenity"="toilets"]({b});nwr["changing_table"]({b});',
    "culture": ('nwr["tourism"~"^(museum|gallery|attraction|zoo|aquarium|theme_park|viewpoint|picnic_site)$"]'
                '({b});nwr["amenity"~"^(theatre|arts_centre|library|cinema|community_centre|place_of_worship)$"]'
                '["name"]({b});'),
    "recreation": ('nwr["leisure"~"^(sports_centre|stadium|swimming_pool|fitness_centre|pitch|ice_rink|'
                   'bowling_alley)$"]["name"]({b});'),
}


def _geom(el):
    if el["type"] == "relation":
        lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                 for m in el.get("members", []) if m.get("geometry") and len(m["geometry"]) > 1]
        return MultiLineString(lines) if lines else None
    if el.get("geometry") and len(el["geometry"]) > 1:
        return LineString([(p["lon"], p["lat"]) for p in el["geometry"]])
    if "lat" in el:
        return Point(el["lon"], el["lat"])
    c = el.get("center")
    return Point(c["lon"], c["lat"]) if c else None


def run(name: str, spec: dict, region: str) -> None:
    poly = area(region)
    xmin, ymin, xmax, ymax = poly.bounds
    b = f"{ymin},{xmin},{ymax},{xmax}"
    retrieved, rows = now(), {}
    for layer, stmts in LAYERS.items():
        # trails need line geometry; everything else a centre point
        out = "out tags geom;" if layer == "trail" else "out tags center;"
        q = f"[out:json][timeout:900];({stmts.format(b=b)});{out}"
        for el in json.loads(fetch(URL, method="POST", data={"data": q}, timeout=1200))["elements"]:
            eid = f"osm:{el['type']}/{el['id']}"
            if eid in rows or (g := _geom(el)) is None:
                continue
            t = el.get("tags", {})
            rows[eid] = {"entity_id": eid, "entity_type": layer, "name": t.get("name", ""),
                         "category": next((f"{k}={t[k]}" for k in ("route", "highway", "leisure", "amenity",
                                           "tourism", "boundary") if k in t), ""),
                         "tags": json.dumps(t, sort_keys=True), "geometry": g}
    ent = gpd.GeoDataFrame(list(rows.values()), crs=WGS84)
    ent = ent[ent.intersects(poly)].copy()
    long = ent.assign(tag=ent["tags"].map(json.loads).map(
        lambda t: [(k, v) for k, v in t.items() if k in OBS])).explode("tag").dropna(subset=["tag"])
    long["attribute"], long["value"] = long["tag"].str[0], long["tag"].str[1]
    obs = observations(
        long, entity_id=long.entity_id, entity_type=long.entity_type, name=long.name,
        category=long.category, attribute=long.attribute, value=long.value,
        signal=[signal(a, v) for a, v in zip(long.attribute, long.value, strict=True)],
        source=name, source_ref="https://www.openstreetmap.org/" + long.entity_id.str[4:],
        retrieved_at=retrieved, license=spec["license"], region=region)
    save(region, name, ent, obs)
