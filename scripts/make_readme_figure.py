"""Render docs/figures/atlas_overview.png: three views of what the atlas knows about Cincinnati.

Run after `make data` and `atlas fetch slope_3dep_local`:
    .venv/bin/python scripts/make_readme_figure.py
"""

from __future__ import annotations

import json

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

from atlas.core import METRIC, PROCESSED, ROOT, WGS84, boundary

# Reference palette (dataviz skill): slots 1-2 validated all-pairs in light mode.
SURFACE, INK, INK2, RULE = "#fcfcfb", "#0b0b0b", "#52514e", "#d9d8d4"
BLUE, ORANGE = "#2a78d6", "#eb6834"
SLOPE = {"≤ 5% (ADA walkway)": "#86b6ef", "5–8.33% (ramp-steep)": "#3987e5", "> 8.33% (too steep)": "#104281"}
SEQ = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])

d = PROCESSED / "cincinnati"
city = gpd.GeoSeries([boundary("cincinnati")], crs=WGS84).to_crs(METRIC)


def pts(path, mask=None):
    g = gpd.read_parquet(path)
    g = g[mask(g)] if mask else g
    g = g.to_crs(METRIC)
    return g.assign(geometry=g.representative_point())


ramps = pts(d / "cagis_curb_ramps.entities.parquet")
osm = gpd.read_parquet(d / "osm.entities.parquet")
kerbs = osm[osm.entity_type == "kerb"].to_crs(METRIC)
slope = gpd.read_parquet(d / "slope_3dep_local.entities.parquet").to_crs(METRIC)
slope["cls"] = pd.cut(slope.max_grade, [-1, 5, 8.33, 1e9], labels=list(SLOPE))
reports = pts(d / "cincy_311.entities.parquet")

plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10, "text.color": INK})
fig, axes = plt.subplots(1, 3, figsize=(15, 5.4), facecolor=SURFACE)
fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.2, wspace=0.04)
for ax in axes:
    ax.set_facecolor(SURFACE)
    city.boundary.plot(ax=ax, color=RULE, linewidth=0.8)
    ax.set_axis_off()
    ax.set_aspect("equal")


def title(ax, head, sub):
    ax.set_title(head, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=22)
    ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=9.5, color=INK2)


# 1. curb ramps: city inventory vs OSM
ax = axes[0]
ramps.plot(ax=ax, color=BLUE, markersize=0.6, alpha=0.6, linewidth=0)
kerbs.plot(ax=ax, color=ORANGE, markersize=3, linewidth=0)
title(ax, "OSM knows 4% of the city's curb ramps", "Curb ramps, Cincinnati")
ax.legend(
    handles=[
        Line2D([], [], marker="o", ls="", color=BLUE, label=f"City inventory (CAGIS): {len(ramps):,}"),
        Line2D([], [], marker="o", ls="", color=ORANGE, label=f"OSM kerb nodes: {len(kerbs):,}"),
    ],
    loc="upper left",
    bbox_to_anchor=(0, 0),
    frameon=False,
    fontsize=9,
    labelcolor=INK,
)

# 2. slope
ax = axes[1]
for label, color in SLOPE.items():
    slope[slope.cls == label].plot(ax=ax, color=color, linewidth=0.5)
share = (slope.max_grade > 8.33).mean() * 100
title(
    ax,
    f"{share:.0f}% of paths have a stretch too steep for ADA",
    "Steepest 10 m stretch per path segment (USGS 1 m DEM)",
)
ax.legend(
    handles=[
        Line2D([], [], color=c, lw=2.5, label=f"{lbl}: {(slope.cls == lbl).sum():,}")
        for lbl, c in SLOPE.items()
    ],
    loc="upper left",
    bbox_to_anchor=(0, 0),
    frameon=False,
    fontsize=9,
    labelcolor=INK,
)

# 3. 311 reports
ax = axes[2]
hb = ax.hexbin(
    reports.geometry.x,
    reports.geometry.y,
    gridsize=45,
    cmap=SEQ,
    mincnt=1,
    bins="log",
    linewidths=0.2,
    edgecolors=SURFACE,
)
yr = pd.to_datetime(reports.date_created).dt.year
title(
    ax,
    f"{len(reports):,} accessibility complaints to 311",
    f"Sidewalk, curb, ramp and signal requests, {yr.min()}–{yr.max()}",
)
cax = ax.inset_axes([0.0, -0.1, 0.45, 0.035])
cb = fig.colorbar(hb, cax=cax, orientation="horizontal")
cb.set_label("Reports per hexagon (log scale)", color=INK2, fontsize=9)
cb.outline.set_visible(False)
cb.ax.tick_params(colors=INK2, labelsize=8)

fig.text(
    0.01,
    0.015,
    "Data: City of Cincinnati / CAGIS, Open Data Cincy, © OpenStreetMap contributors (ODbL), "
    "USGS 3DEP. Retrieved Nov 2026.",
    fontsize=8,
    color=INK2,
)
out = ROOT / "docs" / "figures"
out.mkdir(parents=True, exist_ok=True)
fig.savefig(out / "atlas_overview.png", dpi=160, bbox_inches="tight", facecolor=SURFACE)
print(json.dumps({"saved": str(out / "atlas_overview.png"), "ramps": len(ramps), "kerbs": len(kerbs)}))
