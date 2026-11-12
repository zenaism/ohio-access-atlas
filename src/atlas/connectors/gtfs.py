"""Transit stop accessibility from a static GTFS feed (stops.txt wheelchair_boarding)."""

from __future__ import annotations

import io
import zipfile

import geopandas as gpd
import pandas as pd

from ..core import WGS84, clip, fetch, now, observations, save
from ..signals import signal


def run(name: str, spec: dict, region: str) -> pd.DataFrame:
    retrieved = now()
    z = zipfile.ZipFile(io.BytesIO(fetch(spec["url"])))
    stops = pd.read_csv(z.open("stops.txt"), dtype=str)
    feed = pd.read_csv(z.open("feed_info.txt"), dtype=str).iloc[0] if "feed_info.txt" in z.namelist() else {}
    # column is optional in GTFS; absent or empty means "no information"
    stops["wheelchair_boarding"] = (
        stops["wheelchair_boarding"].fillna("0") if "wheelchair_boarding" in stops else "0"
    )
    gdf = gpd.GeoDataFrame(
        stops,
        crs=WGS84,
        geometry=gpd.points_from_xy(stops.stop_lon.astype(float), stops.stop_lat.astype(float)),
    )
    gdf = clip(gdf, region)
    obs = observations(
        gdf,
        entity_id=f"{name}:" + gdf["stop_id"],
        entity_type="transit_stop",
        name=gdf["stop_name"],
        category="public_transport=platform",
        attribute="wheelchair_boarding",
        value=gdf["wheelchair_boarding"],
        signal=[signal("wheelchair_boarding", v) for v in gdf["wheelchair_boarding"]],
        source=name,
        source_ref=spec["url"],
        observed_at=feed.get("feed_start_date"),
        retrieved_at=retrieved,
        license=spec["license"],
        region=region,
    )
    save(region, name, gdf, obs)
    return obs
