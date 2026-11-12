"""Config, polite cached HTTP, region boundaries, and the observation schema."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
import yaml
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
RAW, PROCESSED = ROOT / "data" / "raw", ROOT / "data" / "processed"
USER_AGENT = "ohio-access-atlas/0.1 (academic accessibility research, Miami University)"
WGS84, METRIC = "EPSG:4326", "EPSG:32616"  # UTM 16N covers both regions

log = logging.getLogger("atlas")

# One row = one claim about one attribute of one entity, with provenance.
OBS_COLUMNS = [
    "entity_id",  # "<source>:<native id>"
    "entity_type",  # poi | path_segment | crossing | kerb | curb_ramp | barrier | entrance |
    # transit_stop | sidewalk_polygon | reported_issue | text
    "name",
    "category",
    "attribute",
    "value",
    "signal",  # supports | limited | barrier | unknown (see signals.py)
    "source",
    "source_ref",
    "observed_at",  # when the source says the fact was recorded (may be null)
    "retrieved_at",  # when we fetched it
    "license",
    "region",
    "lat",
    "lon",
]


@cache
def config(name: str) -> dict:
    return yaml.safe_load((ROOT / "config" / f"{name}.yaml").read_text())


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def out_dir(region: str) -> Path:
    d = PROCESSED / region
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- HTTP ----------------------------------------------------------------------------

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT


def _expired(path: Path) -> bool:
    """With ATLAS_MAX_AGE_DAYS set (weekly refresh), cached responses older than that are fetched again."""
    max_age = os.environ.get("ATLAS_MAX_AGE_DAYS")
    return bool(max_age) and time.time() - path.stat().st_mtime > float(max_age) * 86400


def fetch(
    url: str,
    *,
    method: str = "GET",
    params=None,
    data=None,
    timeout: int = 600,
    retries: int = 4,
    min_interval: float = 1.0,
) -> bytes:
    """GET/POST with an on-disk cache keyed by the full request.

    The cache is the raw-data archive: every processed table can be rebuilt offline
    from exactly the bytes we received.
    """
    key = hashlib.sha256(json.dumps([method, url, params, data], sort_keys=True).encode()).hexdigest()[:20]
    path = RAW / f"{key}.bin"
    if path.exists() and not _expired(path):
        return path.read_bytes()
    RAW.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            r = _session.request(method, url, params=params, data=data, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            if r.status_code >= 400:  # other client errors will not fix themselves
                raise RuntimeError(f"HTTP {r.status_code} for {r.url[:200]}")
            path.write_bytes(r.content)
            time.sleep(min_interval)  # be polite to public servers
            return r.content
        except requests.RequestException as e:
            if attempt == retries:
                raise
            log.warning("%s failed (%s), retry %d/%d", url, e, attempt, retries)
            time.sleep(20 * attempt)
    raise AssertionError("unreachable")


# --- Regions -------------------------------------------------------------------------


@cache
def boundary(region: str):
    """Exact administrative polygon (shapely, WGS84) from the region's OSM relation."""
    rel = config("regions")[region]["osm_relation"]
    gj = json.loads(
        fetch(
            "https://nominatim.openstreetmap.org/lookup",
            params={"osm_ids": f"R{rel}", "format": "geojson", "polygon_geojson": 1},
        )
    )
    return shape(gj["features"][0]["geometry"])


@cache
def area(region: str):
    """City boundary grown by the region's `buffer_km` (destinations just outside town count)."""
    km = config("regions")[region].get("buffer_km", 0)
    b = gpd.GeoSeries([boundary(region)], crs=WGS84).to_crs(METRIC).buffer(km * 1000)
    return b.to_crs(WGS84).iloc[0]


def clip(gdf: gpd.GeoDataFrame, region: str) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    return gdf[gdf.intersects(boundary(region))].copy()


# --- Observations --------------------------------------------------------------------


def observations(gdf: gpd.GeoDataFrame, **cols) -> pd.DataFrame:
    """Build schema rows from a GeoDataFrame; `cols` are columns or constants."""
    pts = gdf.geometry.to_crs(METRIC).representative_point().to_crs(WGS84)
    df = pd.DataFrame({k: v for k, v in cols.items()}, index=gdf.index)
    df["lat"], df["lon"] = pts.y.round(7), pts.x.round(7)
    for c in OBS_COLUMNS:
        if c not in df:
            df[c] = None
    return df[OBS_COLUMNS].reset_index(drop=True)


def save(region: str, source: str, entities: gpd.GeoDataFrame | None, obs: pd.DataFrame) -> None:
    d = out_dir(region)
    if entities is not None and not entities.empty:
        entities.to_parquet(d / f"{source}.entities.parquet")
    obs.to_parquet(d / f"{source}.obs.parquet", index=False)
    log.info(
        "[%s] %s: %d entities, %d observations",
        region,
        source,
        0 if entities is None else len(entities),
        len(obs),
    )


def load_obs(region: str) -> pd.DataFrame:
    files = sorted(out_dir(region).glob("*.obs.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True) if files else pd.DataFrame()
