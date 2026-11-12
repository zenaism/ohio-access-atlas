"""Calendars on Mura CMS sites (City of Cincinnati Parks): the JSON feed the calendar page itself
loads, read once for all events and once per tagged category (e.g. the site's own "Accessible" tag).

Raw:        data/raw/web/<source>/*.json via web.snapshot (exact bytes + manifest)
Normalized: data/processed/<region>/<source>.events.parquet
"""
from __future__ import annotations

import json
import re
from datetime import timedelta
from urllib.parse import urlencode

import pandas as pd
from bs4 import BeautifulSoup

from ..core import RAW, log, out_dir
from .web import snapshot

ACCESS = re.compile(r"wheelchair|accessib|ada\b|asl\b|sensory|adaptive|disabilit", re.I)


def _items(name: str, spec: dict, extra: dict) -> tuple[list[dict], dict]:
    params = {"calendarid": spec["calendar_id"], "start": spec["start"], "end": spec["end"], **extra}
    rec = snapshot(name, f"{spec['api']}?{urlencode(params)}")
    if not rec.get("file"):
        raise RuntimeError(f"{name}: {rec['status']}")
    return json.loads((RAW.parent.parent / rec["file"]).read_text())["data"], rec


def run(name: str, spec: dict, region: str) -> None:
    items, rec = _items(name, spec, {})
    tagged: dict[str, set] = {}
    for label, cat in spec.get("categories", {}).items():
        for it in _items(name, spec, {"categoryid": cat})[0]:
            tagged.setdefault(it["contentid"], set()).add(label)
    rows = []
    for it in items:
        desc = BeautifulSoup(it.get("summary") or "", "lxml").get_text(" ", strip=True)
        rows.append({
            "event_id": f"{name}:{it['contentid']}:{it['displaystart']}", "title": it["title"],
            "description": desc, "start": it["displaystart"],
            "end": it.get("displaystop") or it["displaystart"],
            "recurrence": None, "venue": None, "lat": None, "lon": None,
            "url": spec["site"] + it["filename"].rstrip("/") + "/",
            "categories": ",".join(sorted(tagged.get(it["contentid"], set()))),
            "site_tagged_accessible": "Accessible" in tagged.get(it["contentid"], set()),
            "access_mentions": sorted({m.lower() for m in ACCESS.findall(it["title"] + " " + desc)}),
            "is_disability_focused": False, "source": name, "feed_url": rec["url"], "raw_file": rec["file"],
            "retrieved_at": rec["retrieved_at"], "region": region,
        })
    df = pd.DataFrame(rows)
    if len(df):
        df["expires_at"] = (pd.to_datetime(df["end"].str[:10]) + timedelta(days=1)).dt.date.astype(str)
    df.to_parquet(out_dir(region) / f"{name}.events.parquet", index=False)
    log.info("[%s] %s: %d events, %d tagged Accessible by the site", region, name, len(df),
             int(df.site_tagged_accessible.sum()) if len(df) else 0)
