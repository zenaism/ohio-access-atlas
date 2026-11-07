"""Coverage and cross-source agreement tables (paper Table 1/2 material)."""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from .core import METRIC, WGS84, load_obs, out_dir

MATCH_TOLERANCES = (5, 10, 20)  # metres; report sensitivity, not a single cut-off


def _osm_completeness(d) -> pd.DataFrame:
    ent = pd.read_parquet(d / "osm.entities.parquet", columns=["entity_type", "category", "tags"])
    tags = ent["tags"].map(json.loads)
    groups = {
        "POIs": ent.entity_type == "poi",
        "Footways/paths": ent.category.isin(["highway=footway", "highway=path", "highway=pedestrian"]),
        "Crossings": ent.entity_type == "crossing",
    }
    keys = {"POIs": ["wheelchair", "toilets:wheelchair", "entrance:wheelchair"],
            "Footways/paths": ["surface", "smoothness", "incline", "width"],
            "Crossings": ["kerb", "tactile_paving", "crossing:signals", "traffic_signals:sound"]}
    rows = []
    for g, mask in groups.items():
        n = int(mask.sum())
        for k in keys[g]:
            hit = int(tags[mask].map(lambda t, k=k: k in t).sum())
            rows.append({"feature": g, "n": n, "tag": k, "tagged": hit,
                         "pct": round(100 * hit / n, 1) if n else 0.0})
    return pd.DataFrame(rows)


def _ramps_in_osm(obs: pd.DataFrame) -> pd.DataFrame | None:
    """Share of city curb ramps with an OSM crossing/kerb node within each tolerance.

    OSM crossing nodes sit on the road centreline, so on wide streets the true pair can
    exceed 10 m: read the crossing column as a lower bound.
    """
    ramps = obs[obs.source == "cagis_curb_ramps"]
    osm = obs[(obs.source == "osm") & obs.entity_type.isin(["kerb", "crossing"])].drop_duplicates("entity_id")
    if ramps.empty or osm.empty:
        return None

    def g(df):
        return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=WGS84).to_crs(METRIC)

    r = g(ramps)[["geometry"]]
    rows = []
    for et in ("kerb", "crossing"):
        target = g(osm[osm.entity_type == et])[["geometry"]]
        d = gpd.sjoin_nearest(r, target, how="left", distance_col="d")
        d = d[~d.index.duplicated()]["d"]
        rows.append({"osm_feature": et, **{f"<= {m} m": f"{(d <= m).mean() * 100:.1f}%"
                                           for m in MATCH_TOLERANCES}})
    return pd.DataFrame(rows)


def write(region: str) -> str:
    d, obs = out_dir(region), load_obs(region)
    if obs.empty:
        return f"no data for {region}"
    by_src = obs.pivot_table(index="source", columns="signal", values="entity_id", aggfunc="count",
                             fill_value=0)
    by_src.insert(0, "entities", obs.groupby("source").entity_id.nunique())
    parts = [f"# {region}: data report", "", "## Observations by source and signal", "",
             by_src.to_markdown(), ""]
    if (d / "osm.entities.parquet").exists():
        parts += ["## OSM tag completeness", "", _osm_completeness(d).to_markdown(index=False), ""]
    if (m := _ramps_in_osm(obs)) is not None:
        parts += [f"## Cross-source: {int((obs.source == 'cagis_curb_ramps').sum())} city curb ramps (CAGIS) "
                  "with an OSM feature nearby", "", m.to_markdown(index=False), ""]
    if (obs.source == "cincy_311").any():
        r = obs[obs.source == "cincy_311"]
        parts += ["## 311 accessibility-related requests", "",
                  r.value.value_counts().to_frame("requests").to_markdown(), "",
                  f"Date range: {r.observed_at.min()} .. {r.observed_at.max()}", ""]
    gt = obs[obs.attribute == "wheelchair_boarding"]
    if not gt.empty:
        parts += ["## Transit stops: wheelchair_boarding", "",
                  gt.groupby(["source", "value"], dropna=False).size().to_frame("stops").to_markdown(), ""]
    md = "\n".join(parts)
    (d / "report.md").write_text(md)
    return md
