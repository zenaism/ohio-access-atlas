"""Any Socrata (SODA) dataset with lat/lon columns, e.g. Open Data Cincy 311."""

from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from ..core import WGS84, clip, fetch, now, observations, save
from .arcgis import mapped

PAGE = 50_000


def rows(domain: str, dataset: str, where: str, fields: list[str]) -> pd.DataFrame:
    url, out, offset = f"https://{domain}/resource/{dataset}.json", [], 0
    while True:
        page = json.loads(
            fetch(
                url,
                params={
                    "$where": where,
                    "$select": ",".join(fields),
                    "$order": ":id",
                    "$limit": PAGE,
                    "$offset": offset,
                },
            )
        )
        out += page
        if len(page) < PAGE:
            return pd.DataFrame(out)
        offset += PAGE


def run(name: str, spec: dict, region: str) -> pd.DataFrame:
    retrieved = now()
    df = rows(spec["domain"], spec["dataset"], " ".join(spec["where"].split()), spec["fields"])
    # the portal returns a few duplicate request numbers
    df = df.dropna(subset=["latitude", "longitude"]).drop_duplicates("sr_number")
    gdf = gpd.GeoDataFrame(
        df, crs=WGS84, geometry=gpd.points_from_xy(df.longitude.astype(float), df.latitude.astype(float))
    )
    gdf = clip(gdf, region)
    value, sig = mapped(gdf, spec["observe"])
    obs = observations(
        gdf,
        entity_id=f"{name}:" + gdf["sr_number"],
        entity_type=spec["entity"],
        attribute=spec["observe"]["attribute"],
        value=value,
        signal=sig,
        source=name,
        source_ref=f"https://{spec['domain']}/resource/{spec['dataset']}.json?sr_number=" + gdf["sr_number"],
        observed_at=gdf["date_created"].str[:10],
        retrieved_at=retrieved,
        license=spec["license"],
        region=region,
    )
    save(region, name, gdf, obs)
    return obs
