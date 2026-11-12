"""Overture Maps places: the full list of named places, used as the base layer that
access facts from other sources attach to. Overture has no accessibility fields itself."""

from __future__ import annotations

import duckdb
import geopandas as gpd
import pandas as pd
from shapely import wkb

from ..core import RAW, WGS84, area, log, now, out_dir

S3 = "s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*"


def run(name: str, spec: dict, region: str) -> None:
    poly = area(region)
    xmin, ymin, xmax, ymax = poly.bounds
    cache = RAW / "overture" / f"{spec['release']}_{region}.parquet"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():  # bbox pushdown reads only the row groups we need (~1-2 min)
        con = duckdb.connect()
        con.sql("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
        con.sql(f"""
            COPY (
              SELECT id, names.primary AS name, basic_category, taxonomy.primary AS category,
                     array_to_string(taxonomy.hierarchy, '>') AS hierarchy, confidence, operating_status,
                     websites[1] AS website, phones[1] AS phone,
                     addresses[1].freeform AS address, addresses[1].locality AS locality,
                     addresses[1].postcode AS postcode,
                     array_to_string(list_distinct([s.dataset FOR s IN sources]), ',') AS datasets,
                     ST_AsWKB(geometry) AS wkb
              FROM read_parquet('{S3.format(release=spec["release"])}', hive_partitioning=1)
              WHERE bbox.xmin BETWEEN {xmin} AND {xmax} AND bbox.ymin BETWEEN {ymin} AND {ymax}
            ) TO '{cache}' (FORMAT parquet)""")
    df = pd.read_parquet(cache)
    gdf = gpd.GeoDataFrame(
        df.drop(columns="wkb"), geometry=df["wkb"].map(lambda b: wkb.loads(bytes(b))), crs=WGS84
    )
    gdf = gdf[gdf.within(poly)].copy()
    gdf.insert(0, "entity_id", "overture:" + gdf.pop("id"))
    gdf["region"], gdf["retrieved_at"], gdf["license"] = region, now(), spec["license"]
    gdf.to_parquet(out_dir(region) / f"{name}.entities.parquet")
    log.info(
        "[%s] %s: %d places (%d with confidence >= 0.5)",
        region,
        name,
        len(gdf),
        (gdf.confidence >= 0.5).sum(),
    )
