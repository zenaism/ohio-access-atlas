"""Running slope of every OSM pedestrian segment, sampled from a DEM ImageServer.

Samples elevation every `step_m` metres along each segment (via ArcGIS getSamples) and
reports the steepest sub-segment grade and the end-to-end grade. Bridges/tunnels/steps are
skipped: a bare-earth DEM is wrong on structures, and steps are already barriers.
Accuracy caveat: 1 m DEM vertical noise of about 0.1 m over 10 m gives about 1% grade
error. Validate against field measurements before trusting values near the 5% / 8.33%
thresholds.
"""
from __future__ import annotations

import contextlib
import json

import geopandas as gpd
import numpy as np
import pandas as pd

from ..core import METRIC, WGS84, fetch, now, observations, out_dir, save
from ..signals import incline

BATCH = 300
SKIP = ("bridge", "tunnel", "covered", "indoor")


def _segments(region: str) -> gpd.GeoDataFrame:
    ent = gpd.read_parquet(out_dir(region) / "osm.entities.parquet")
    seg = ent[(ent.entity_type == "path_segment") & (ent.category != "highway=steps")].copy()
    tags = seg["tags"].map(json.loads)
    seg = seg[~tags.map(lambda t: any(t.get(k) not in (None, "no") for k in SKIP))]
    return seg.to_crs(METRIC)


def _sample_points(seg: gpd.GeoDataFrame, step: float) -> pd.DataFrame:
    rows = []
    for eid, line in zip(seg.entity_id, seg.geometry, strict=True):
        n = max(int(line.length // step), 1)
        for d in np.linspace(0, line.length, n + 1):
            p = line.interpolate(d)
            rows.append((eid, d, p.x, p.y))
    pts = pd.DataFrame(rows, columns=["entity_id", "dist", "x", "y"])
    ll = gpd.GeoSeries(gpd.points_from_xy(pts.x, pts.y), crs=METRIC).to_crs(WGS84)
    pts["lon"], pts["lat"] = ll.x.round(6), ll.y.round(6)
    return pts


def _elevations(url: str, pts: pd.DataFrame, to_m: float) -> np.ndarray:
    z = np.full(len(pts), np.nan)
    for i in range(0, len(pts), BATCH):
        b = pts.iloc[i:i + BATCH]
        geom = {"points": b[["lon", "lat"]].values.tolist(), "spatialReference": {"wkid": 4326}}
        d = json.loads(fetch(f"{url}/getSamples", method="POST", min_interval=0.2, data={
            "geometry": json.dumps(geom, separators=(",", ":")), "geometryType": "esriGeometryMultipoint",
            "returnFirstValueOnly": "true", "f": "json"}))
        for s in d.get("samples", []):
            with contextlib.suppress(ValueError, TypeError):  # "NoData" outside coverage
                z[i + s["locationId"]] = float(s["value"]) * to_m
    return z


def run(name: str, spec: dict, region: str) -> pd.DataFrame:
    retrieved, step = now(), spec.get("step_m", 10)
    seg = _segments(region)
    seg = seg[seg.length >= spec.get("min_length_m", 5)]
    pts = _sample_points(seg, step)
    if spec.get("dem") == "3dep_local":   # downloaded tiles (see atlas.dem)
        from ..dem import sample
        pts["z"] = sample(region, pts.lon.values, pts.lat.values)
    else:                                  # remote ImageServer
        pts["z"] = _elevations(spec["url"], pts, spec.get("to_metres", 1.0))

    def grades(g):
        g = g.dropna(subset=["z"])
        if len(g) < 2:
            return pd.Series({"max_grade": np.nan, "avg_grade": np.nan})
        dz, dd = np.diff(g.z.values), np.diff(g.dist.values)
        return pd.Series({"max_grade": np.max(np.abs(dz / dd)) * 100,
                          "avg_grade": abs(g.z.values[-1] - g.z.values[0]) / g.dist.values[-1] * 100})

    gr = pts.groupby("entity_id")[["dist", "z"]].apply(grades)
    seg = seg.set_index("entity_id").join(gr).dropna(subset=["max_grade"]).reset_index().to_crs(WGS84)
    long = pd.concat([
        seg.assign(attribute="incline_max_dem", value=seg.max_grade.round(1).astype(str) + "%"),
        seg.assign(attribute="incline_avg_dem", value=seg.avg_grade.round(1).astype(str) + "%"),
    ], ignore_index=True)
    long = gpd.GeoDataFrame(long, geometry="geometry", crs=WGS84)
    obs = observations(
        long, entity_id=long.entity_id, entity_type="path_segment", name=long["name"],
        category=long.category, attribute=long.attribute, value=long.value,
        signal=[incline(v) for v in long.value], source=name, source_ref=spec["url"],
        retrieved_at=retrieved, license=spec["license"], region=region)
    save(region, name, seg[["entity_id", "category", "max_grade", "avg_grade", "geometry"]], obs)
    return obs
