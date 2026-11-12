"""USGS 3DEP 1 m DEM tiles: discover, download (parallel, resumable), sample locally.

Local sampling replaces thousands of getSamples calls against a public server, and pins
the exact tiles (project + publication date) used, which is good for reproducibility.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from pyproj import Transformer

from .core import ROOT, USER_AGENT, boundary, log

DEM_DIR = ROOT / "data" / "dem"
TNM = "https://tnmaccess.nationalmap.gov/api/v1/products"
PREFERRED_PROJECT = "OH_Statewide_Phase3_2021"  # one consistent LiDAR collection where available


def tiles(region: str) -> list[dict]:
    """One product per 10 km tile: the preferred Ohio project if present, else the newest."""
    items = requests.get(
        TNM,
        timeout=120,
        params={
            "datasets": "Digital Elevation Model (DEM) 1 meter",
            "bbox": ",".join(map(str, boundary(region).bounds)),
            "max": 200,
        },
    ).json()["items"]
    best: dict[str, dict] = {}
    for it in items:
        key = re.search(r"x\d+y\d+", it["title"]).group(0)
        rank = (PREFERRED_PROJECT in it["title"], it["publicationDate"])
        if key not in best or rank > best[key]["_rank"]:
            best[key] = {**it, "_rank": rank}
    return sorted(best.values(), key=lambda t: t["title"])


def _download(t: dict) -> Path:
    path = DEM_DIR / Path(t["downloadURL"]).name
    if path.exists() and path.stat().st_size == t["sizeInBytes"]:
        return path
    tmp = path.with_suffix(".part")
    with requests.get(t["downloadURL"], stream=True, timeout=120, headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 22):
                f.write(chunk)
    tmp.rename(path)
    log.info("downloaded %s (%.0f MB)", path.name, t["sizeInBytes"] / 1e6)
    return path


def download(region: str, workers: int = 4) -> list[Path]:
    DEM_DIR.mkdir(parents=True, exist_ok=True)
    ts = tiles(region)
    log.info("[%s] %d DEM tiles, %.2f GB", region, len(ts), sum(t["sizeInBytes"] for t in ts) / 1e9)
    cols = ("title", "publicationDate", "sizeInBytes", "downloadURL")
    pd.DataFrame([{k: t[k] for k in cols} for t in ts]).to_csv(  # provenance: exact tiles used
        DEM_DIR / f"{region}_tiles.csv", index=False
    )
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(_download, ts))


def sample(region: str, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Elevation (m) at WGS84 points from the region's downloaded tiles; NaN where no data."""
    z = np.full(len(lon), np.nan)
    files = pd.read_csv(DEM_DIR / f"{region}_tiles.csv").downloadURL.map(lambda u: DEM_DIR / Path(u).name)
    for f in files:
        with rasterio.open(f) as src:
            x, y = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True).transform(lon, lat)
            b = src.bounds
            m = np.isnan(z) & (x >= b.left) & (x < b.right) & (y > b.bottom) & (y <= b.top)
            if not m.any():
                continue
            vals = np.fromiter((v[0] for v in src.sample(zip(x[m], y[m], strict=True))), float, m.sum())
            if src.nodata is not None:
                vals[vals == src.nodata] = np.nan
            z[m] = vals
    return z
