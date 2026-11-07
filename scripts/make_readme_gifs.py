"""Render the README animations into docs/figures/:

  slope_walk.gif        a dot climbs a real street; elevation and 10 m grades build up vs ADA limits
  ramps_vs_osm.gif      one neighbourhood: OSM kerbs, then the city's curb ramps fade in
  reports_timelapse.gif 311 accessibility complaints, year by year, 2004-2026

Needs `make data` and `make dem` first.  Run: .venv/bin/python scripts/make_readme_gifs.py
"""

from __future__ import annotations

import json

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation, PillowWriter
from shapely.geometry import box

from atlas.core import METRIC, PROCESSED, ROOT, WGS84, boundary
from atlas.dem import sample

SURFACE, INK, INK2, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#d9d8d4", "#ecebe7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
CLS = [
    (5, "#86b6ef", "≤ 5% ADA walkway"),
    (8.33, "#3987e5", "5–8.33% ramp-steep"),
    (1e9, "#104281", "> 8.33% too steep for a ramp"),
]
OUT = ROOT / "docs" / "figures"
D = PROCESSED / "cincinnati"
plt.rcParams.update(
    {
        "font.family": "Helvetica Neue",
        "font.size": 10,
        "text.color": INK,
        "axes.edgecolor": RULE,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
    }
)


def color_for(g):
    return next(c for lim, c, _ in CLS if abs(g) <= lim)


def save(anim, name, fps):
    anim.save(OUT / name, writer=PillowWriter(fps=fps), dpi=90, savefig_kwargs={"facecolor": SURFACE})
    print("saved", name, round((OUT / name).stat().st_size / 1e6, 2), "MB")


# 1. slope walk ------------------------------------------------------------------------------
def slope_walk(eid="osm:way/239199506"):  # Warner Street: a mix of grades
    seg = gpd.read_parquet(D / "slope_3dep_local.entities.parquet")
    names = pd.read_parquet(D / "osm.entities.parquet", columns=["entity_id", "name"])
    line = seg[seg.entity_id == eid].to_crs(METRIC).geometry.iloc[0]
    name = names.set_index("entity_id").name[eid]
    dist = np.arange(0, line.length, 10.0)
    pts = gpd.GeoSeries([line.interpolate(d) for d in dist], crs=METRIC)
    ll = pts.to_crs(WGS84)
    z = sample("cincinnati", ll.x.values, ll.y.values)
    grade = np.diff(z) / 10 * 100
    if z[-1] < z[0]:  # walk uphill
        dist, pts, z, grade = dist, pts[::-1].reset_index(drop=True), z[::-1], -grade[::-1]
    ctx = seg.to_crs(METRIC)
    ctx = ctx[ctx.intersects(line.buffer(350))]

    fig = plt.figure(figsize=(9.6, 4.4), facecolor=SURFACE)
    axm = fig.add_axes([0.01, 0.06, 0.36, 0.74])
    axz = fig.add_axes([0.45, 0.53, 0.42, 0.28])
    axg = fig.add_axes([0.45, 0.14, 0.42, 0.30], sharex=axz)
    steep = (np.abs(grade) > 8.33).mean() * 100
    fig.text(
        0.01, 0.93, f"{name}, Cincinnati: how steep is it, 10 m at a time?", fontsize=13, fontweight="bold"
    )
    fig.text(
        0.01,
        0.875,
        f"Elevation from the USGS 1 m terrain model. {steep:.0f}% of its 10 m stretches are "
        "steeper than an ADA ramp may be.",
        fontsize=9.5,
        color=INK2,
    )
    axm.set_axis_off()
    axm.set_aspect("equal")
    ctx.plot(ax=axm, color=RULE, linewidth=0.8)
    gpd.GeoSeries([line], crs=METRIC).plot(ax=axm, color=INK2, linewidth=1.2)
    for ax in (axz, axg):
        ax.set_facecolor(SURFACE)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
    axz.set_ylabel("Elevation (m)")
    axz.set_xlim(0, dist[-1])
    axz.set_ylim(np.nanmin(z) - 2, np.nanmax(z) + 2)
    axg.set_ylabel("Grade per 10 m (%)")
    axg.set_xlabel("Distance along the street (m)")
    axg.set_ylim(0, max(np.nanmax(np.abs(grade)) * 1.15, 10))
    for lim, label in ((5, "5% walkway limit"), (8.33, "8.33% ramp limit")):
        axg.axhline(lim, color=INK, linewidth=0.9, linestyle=(0, (4, 3)), zorder=4)
        axg.text(1.01, lim, label, transform=axg.get_yaxis_transform(), va="center", fontsize=8.5, color=INK2)
    plt.setp(axz.get_xticklabels(), visible=False)
    (prof,) = axz.plot([], [], color=BLUE, linewidth=2)
    bars = axg.bar(dist[:-1] + 5, np.zeros(len(grade)), width=8.5, color=[color_for(g) for g in grade])
    (done,) = axm.plot([], [], color=BLUE, linewidth=3, solid_capstyle="round")
    (dot,) = axm.plot([], [], "o", color=ORANGE, markersize=9, markeredgecolor=SURFACE, markeredgewidth=1.5)
    n, hold = len(dist), 10

    def frame(i):
        k = min(i, n - 1)
        prof.set_data(dist[: k + 1], z[: k + 1])
        for j, b in enumerate(bars):
            b.set_height(abs(grade[j]) if j < k else 0)
        done.set_data(pts.x[: k + 1], pts.y[: k + 1])
        dot.set_data([pts.x[k]], [pts.y[k]])
        return prof, dot, done, *bars

    save(FuncAnimation(fig, frame, frames=n + hold, blit=False), "slope_walk.gif", fps=8)
    plt.close(fig)


# 2. ramps vs OSM ----------------------------------------------------------------------------
def ramps_vs_osm(size_m=1400):
    ramps = gpd.read_parquet(D / "cagis_curb_ramps.entities.parquet").to_crs(METRIC)
    ramps["geometry"] = ramps.representative_point()
    osm = gpd.read_parquet(D / "osm.entities.parquet")
    kerbs = osm[osm.entity_type == "kerb"].to_crs(METRIC)
    net = gpd.read_parquet(D / "slope_3dep_local.entities.parquet").to_crs(METRIC)
    # densest square of city ramps (grid search on a 700 m lattice)
    xs, ys = ramps.geometry.x, ramps.geometry.y
    edges = [np.arange(xs.min(), xs.max(), size_m / 2), np.arange(ys.min(), ys.max(), size_m / 2)]
    h, xe, ye = np.histogram2d(xs, ys, bins=edges)
    hk, _, _ = np.histogram2d(kerbs.geometry.x, kerbs.geometry.y, bins=edges)
    # the typical case, not downtown: most city ramps where OSM has (almost) no kerbs
    i, j = np.unravel_index(np.argmax(np.where(hk <= 2, h, 0)), h.shape)
    win = box(xe[i] - size_m / 4, ye[j] - size_m / 4, xe[i] + size_m * 0.75, ye[j] + size_m * 0.75)
    r, k, nw = ramps[ramps.within(win)], kerbs[kerbs.within(win)], net.clip(win)

    fig, ax = plt.subplots(figsize=(6.4, 6.4), facecolor=SURFACE)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.02)
    ax.set_axis_off()
    ax.set_xlim(win.bounds[0], win.bounds[2])
    ax.set_ylim(win.bounds[1], win.bounds[3])
    nw.plot(ax=ax, color=RULE, linewidth=0.9)
    title = fig.text(0.02, 0.93, "", fontsize=13, fontweight="bold")
    sub = fig.text(0.02, 0.885, "", fontsize=10, color=INK2)
    ko = ax.scatter(
        k.geometry.x, k.geometry.y, s=36, color=ORANGE, edgecolor=SURFACE, linewidth=0.8, zorder=3
    )
    ro = ax.scatter(r.geometry.x, r.geometry.y, s=14, color=BLUE, alpha=0, linewidth=0, zorder=2)
    phase1, fade, hold = 10, 10, 16

    def frame(f):
        if f < phase1:
            title.set_text(f"OpenStreetMap: {len(k)} kerbs mapped here")
            sub.set_text("What a router built on open data knows about this 1.4 km square of Cincinnati")
            ro.set_alpha(0)
        else:
            a = min(1, (f - phase1 + 1) / fade)
            ro.set_alpha(0.85 * a)
            title.set_text(f"City inventory: {len(r)} curb ramps in the same square")
            sub.set_text(
                "Orange: OpenStreetMap kerbs   Blue: city curb ramps (CAGIS, traced from 2024 aerials)"
            )
        return ro, ko, title, sub

    save(FuncAnimation(fig, frame, frames=phase1 + fade + hold), "ramps_vs_osm.gif", fps=6)
    plt.close(fig)


# 3. 311 time-lapse --------------------------------------------------------------------------
def reports_timelapse():
    rep = gpd.read_parquet(D / "cincy_311.entities.parquet").to_crs(METRIC)
    rep["year"] = pd.to_datetime(rep.date_created).dt.year
    years = list(range(rep.year.min(), rep.year.max() + 1))
    counts = rep.year.value_counts().reindex(years, fill_value=0)
    city = gpd.GeoSeries([boundary("cincinnati")], crs=WGS84).to_crs(METRIC)

    fig = plt.figure(figsize=(7.2, 6.2), facecolor=SURFACE)
    ax = fig.add_axes([0.02, 0.27, 0.96, 0.6])
    axb = fig.add_axes([0.08, 0.06, 0.88, 0.15])
    ax.set_axis_off()
    ax.set_aspect("equal")
    city.boundary.plot(ax=ax, color=RULE, linewidth=0.8)
    fig.text(
        0.02, 0.94, "22 years of accessibility complaints to Cincinnati 311", fontsize=13, fontweight="bold"
    )
    fig.text(
        0.02,
        0.905,
        "Sidewalk hazards, obstructions, curbs, ramps, accessible parking and audible signals",
        fontsize=9.5,
        color=INK2,
    )
    old = ax.scatter([], [], s=1.2, color="#b7d3f6", linewidth=0)
    new = ax.scatter([], [], s=5, color=BLUE, linewidth=0)
    label = ax.text(
        0.98, 0.04, "", transform=ax.transAxes, ha="right", fontsize=26, fontweight="bold", color=INK
    )
    count = ax.text(0.98, 0.0, "", transform=ax.transAxes, ha="right", fontsize=10, color=INK2)
    axb.set_facecolor(SURFACE)
    axb.spines[["top", "right", "left"]].set_visible(False)
    axb.set_yticks([])
    bars = axb.bar(years, np.zeros(len(years)), color="#b7d3f6", width=0.75)
    axb.set_ylim(0, counts.max() * 1.15)
    axb.set_xticks([y for y in years if y % 4 == 0 or y == years[-1]])
    axb.tick_params(labelsize=8.5)
    axb.set_title("Reports per year", loc="left", fontsize=9, color=INK2)
    hold = 8

    def frame(f):
        i = min(f, len(years) - 1)
        y = years[i]
        prev, cur = rep[rep.year < y], rep[rep.year == y]
        old.set_offsets(np.c_[prev.geometry.x, prev.geometry.y] if len(prev) else np.empty((0, 2)))
        new.set_offsets(np.c_[cur.geometry.x, cur.geometry.y] if len(cur) else np.empty((0, 2)))
        label.set_text(str(y))
        count.set_text(f"{counts[y]:,} this year · {int(counts.loc[:y].sum()):,} total")
        for j, b in enumerate(bars):
            b.set_height(counts.iloc[j] if j <= i else 0)
            b.set_color(BLUE if j == i else "#b7d3f6")
        return old, new, label, count, *bars

    save(FuncAnimation(fig, frame, frames=len(years) + hold), "reports_timelapse.gif", fps=3)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    slope_walk()
    ramps_vs_osm()
    reports_timelapse()
    print(json.dumps({"out": str(OUT)}))
