"""The assistant's knowledge base: one DuckDB file built from the published map data.

Tables
  places  one row per place on the map (name, region, layer, rating, point, summary, notice, page URL)
  facts   one row per fact with its value, detail, verbatim quote, source URL and date
  events  one row per upcoming event, with access kinds (audio_description, asl, sensory_friendly)

Built from data/map/*_atlas.geojson, so the assistant answers from exactly what the map shows.
Rebuild with `python -m atlas.assistant.kb` (or `make kb`).
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

from ..core import ROOT

DB = ROOT / "data/kb/atlas.duckdb"
SITE = "https://zenaism.github.io/ohio-access-atlas/data/map"


def _rows(region: str):
    fc = json.loads((ROOT / f"data/map/{region}_atlas.geojson").read_text())
    places, facts, events = [], [], []
    for f in fc["features"]:
        p, g = f["properties"], f["geometry"]
        coords = g["coordinates"]
        if g["type"] == "Point":
            lon, lat = coords
        else:  # trails: first vertex is good enough for "near me"
            flat = coords[0] if g["type"] == "LineString" else coords[0][0]
            lon, lat = flat[0], flat[1]
        gt = p.get("getting_there") or {}
        places.append(
            {
                "link_id": p["link_id"],
                "name": p["name"],
                "region": region,
                "layer": p["layer"],
                "rating": p["access_rating"],
                "lat": lat,
                "lon": lon,
                "summary": p.get("summary") or "",
                "notice": p.get("notice"),
                "keys": json.dumps(p.get("keys") or []),
                "arrival": gt.get("arrival"),
                "getting_there": json.dumps(gt),
                "newest_source": p.get("newest_source"),
                "contacts": json.dumps(p.get("contacts") or {}),
                "page": f"{SITE}/places/{region}/{p['link_id']}.html",
                "generated": fc["generated"],
            }
        )
        for x in p.get("facts") or []:
            facts.append(
                {
                    "link_id": p["link_id"],
                    "attribute": str(x.get("attribute", "")),
                    "value": str(x.get("value", "")),
                    "detail": str(x.get("detail") or ""),
                    "quote": str(x.get("quote") or ""),
                    "source": str(x.get("source") or ""),
                    "date": str(x.get("date") or ""),
                }
            )
        for e in p.get("events") or []:
            events.append(
                {
                    "link_id": p["link_id"],
                    "title": e["title"],
                    "start": e["start"],
                    "url": e.get("url") or "",
                    "access": ",".join(e.get("access") or []),
                    "accessible_tag": bool(e.get("accessible_tag")),
                    "disability_focused": bool(e.get("disability_focused")),
                }
            )
    return places, facts, events


def _organizations(have: set[str]) -> tuple[list, list]:
    """Facts about organizations and region-wide programs (park systems, festivals, the campus, bus
    systems): no single map point, but the assistant should still know them."""
    import re

    from ..export_map import LABELS

    f = ROOT / "data/extracted/venue_facts.jsonl"
    rows = [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []
    places, facts = [], []
    for name in dict.fromkeys(r["place"] for r in rows):
        if name in have:
            continue
        mine = [r for r in rows if r["place"] == name]
        lid = "org-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48]
        places.append(
            {
                "link_id": lid,
                "name": name,
                "region": mine[0]["region"],
                "layer": "organization",
                "rating": "unknown",
                "lat": None,
                "lon": None,
                "summary": "; ".join(
                    f"{LABELS.get(r['attribute'], r['attribute'])}: {r['detail'] or r['value']}"
                    for r in mine[:4]
                ),
                "notice": None,
                "keys": "[]",
                "arrival": None,
                "getting_there": "{}",
                "newest_source": None,
                "contacts": "{}",
                "page": mine[0]["url"],
                "generated": None,
            }
        )
        for r in mine:
            facts.append(
                {
                    "link_id": lid,
                    "attribute": LABELS.get(r["attribute"], r["attribute"]),
                    "value": r["value"],
                    "detail": r["detail"] or "",
                    "quote": r["evidence_quote"],
                    "source": r["url"],
                    "date": (r.get("observed_at") or "")[:7],
                }
            )
    return places, facts


def build(path: Path = DB) -> Path:
    places, facts, events = [], [], []
    for region in ("cincinnati", "oxford"):
        a, b, c = _rows(region)
        places += a
        facts += b
        events += c
    a, b = _organizations({p["name"] for p in places})
    places += a
    facts += b
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    for name, rows in (("places", places), ("facts", facts), ("events", events)):
        df = pd.DataFrame(rows)  # noqa: F841 (read by DuckDB through the variable name)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM df")
    con.close()
    tmp.replace(path)  # never leave a half-built file behind
    return path


def connect(path: Path = DB, rebuild: bool = False) -> duckdb.DuckDBPyConnection:
    """Read-only connection; builds the file first if it is missing or older than the map data."""
    newest = max((ROOT / "data/map").glob("*_atlas.geojson"), key=lambda f: f.stat().st_mtime).stat().st_mtime
    if rebuild or not path.exists() or path.stat().st_mtime < newest:
        build(path)
    return duckdb.connect(str(path), read_only=True)


if __name__ == "__main__":
    p = build()
    con = duckdb.connect(str(p), read_only=True)
    n = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("places", "facts", "events")}
    print(f"{p.relative_to(ROOT)}: {n}")
