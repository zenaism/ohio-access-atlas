"""Any ArcGIS REST FeatureServer/MapServer layer (CAGIS, ODOT, county/city GIS, campus GIS).

Fetches object IDs inside the region's bounding box, then features in ID chunks. ID
chunking works on old MapServers that do not support resultOffset pagination.
"""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from ..core import WGS84, boundary, clip, fetch, now, observations, save
from ..signals import signal


def _query(url: str, **params) -> dict:
    d = json.loads(fetch(f"{url}/query", method="POST", data={"f": "json", **params}))
    if "error" in d:
        raise RuntimeError(f"{url}: {d['error']}")
    return d


def features(url: str, where: str, fields: list[str] | None, region: str) -> gpd.GeoDataFrame:
    meta = json.loads(fetch(url, params={"f": "json"}))
    chunk = min(int(meta.get("maxRecordCount") or 1000), 1000)
    minx, miny, maxx, maxy = boundary(region).bounds
    spatial = {"geometry": f"{minx},{miny},{maxx},{maxy}", "geometryType": "esriGeometryEnvelope",
               "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "where": where}
    ids = sorted(_query(url, returnIdsOnly="true", **spatial).get("objectIds") or [])
    oid = meta.get("objectIdField") or "OBJECTID"
    out_fields = ",".join(dict.fromkeys([oid, *(fields or [])])) if fields else "*"

    frames = []
    for i in range(0, len(ids), chunk):
        gj = fetch(f"{url}/query", method="POST", data={
            "f": "geojson", "objectIds": ",".join(map(str, ids[i:i + chunk])),
            "outFields": out_fields, "outSR": 4326})
        g = gpd.read_file(gj.decode()) if gj.strip() else None
        if g is not None and not g.empty:
            frames.append(g)
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs=WGS84)
    gdf = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=WGS84)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    return clip(gdf, region).rename(columns={oid: "native_id"})


def run(name: str, spec: dict, region: str) -> pd.DataFrame:
    retrieved = now()
    gdf = features(spec["url"], spec.get("where", "1=1"), spec.get("fields"), region)
    o = spec["observe"]
    value, sig = mapped(gdf, o)
    obs = observations(
        gdf, entity_id=f"{name}:" + gdf["native_id"].astype(str), entity_type=spec["entity"],
        attribute=o["attribute"], value=value, signal=sig, source=name,
        source_ref=spec["url"] + "/query?objectIds=" + gdf["native_id"].astype(str) + "&outFields=*&f=html",
        observed_at=_edited(gdf), retrieved_at=retrieved, license=spec["license"], region=region)
    save(region, name, gdf, obs)
    return obs


def mapped(df: pd.DataFrame, o: dict):
    """(value, signal) for an `observe:` spec: constant value or a column."""
    if "value_field" in o:
        value = df[o["value_field"]]
        return value, o.get("signal") or [signal(o["attribute"], v) for v in value]
    return o["value"], o.get("signal") or signal(o["attribute"], o["value"])


def _edited(gdf: gpd.GeoDataFrame):
    for c in ("LASTEDITEDDATE", "LAST_EDITED_DATE", "EditDate"):
        if c in gdf:
            s = gdf[c]
            s = pd.to_datetime(s, unit="ms", errors="coerce") if pd.api.types.is_numeric_dtype(s) \
                else pd.to_datetime(s, errors="coerce")
            return s.dt.strftime("%Y-%m-%d")
    return None
