"""Event calendars published as iCal feeds (WordPress "The Events Calendar" sites expose ?ical=1).

Raw:        the .ics file, via web.snapshot (data/raw/web/<source>/)
Normalized: data/processed/<region>/<source>.events.parquet in the event schema of the plan.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

import pandas as pd
from icalendar import Calendar

from ..core import RAW, log, out_dir
from .web import snapshot

ACCESS_WORDS = re.compile(r"wheelchair|accessib|ada\b|asl\b|sensory|adaptive|disabilit|captio|"
                          r"mobility|ramp|elevator|inclusive", re.I)


def _iso(v) -> str | None:
    if v is None:
        return None
    v = v.dt
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


def _cats(v) -> str:
    groups = v if isinstance(v, list) else [v] if v is not None else []
    return ",".join(str(c) for g in groups for c in getattr(g, "cats", [g]))


def run(name: str, spec: dict, region: str) -> None:
    rows = []
    for url in spec["urls"]:
        rec = snapshot(name, url)
        if not rec.get("file"):
            log.warning("[%s] %s: %s %s", region, name, rec["status"], url)
            continue
        cal = Calendar.from_ical((RAW.parent.parent / rec["file"]).read_bytes())
        for ev in cal.walk("VEVENT"):
            desc = str(ev.get("DESCRIPTION", ""))
            title = str(ev.get("SUMMARY", ""))
            end = _iso(ev.get("DTEND")) or _iso(ev.get("DTSTART"))
            geo = ev.get("GEO")
            rows.append({
                "event_id": f"{name}:{ev.get('UID')}", "title": title, "description": desc,
                "start": _iso(ev.get("DTSTART")), "end": end,
                "recurrence": str(ev.get("RRULE").to_ical().decode()) if ev.get("RRULE") else None,
                "venue": str(ev.get("LOCATION", "")) or None,
                "lat": geo.latitude if geo else None, "lon": geo.longitude if geo else None,
                "url": str(ev.get("URL", "")) or url,
                "categories": _cats(ev.get("CATEGORIES")),
                "access_mentions": sorted({m.lower() for m in ACCESS_WORDS.findall(title + " " + desc)}),
                "is_disability_focused": spec.get("disability_focused", False),
                "source": name, "feed_url": url, "raw_file": rec["file"],
                "retrieved_at": rec["retrieved_at"], "region": region,
            })
    df = pd.DataFrame(rows)
    if len(df):
        end = pd.to_datetime(df["end"].str[:10], errors="coerce")
        df["expires_at"] = (end + timedelta(days=1)).dt.date.astype(str)
    df.to_parquet(out_dir(region) / f"{name}.events.parquet", index=False)
    log.info("[%s] %s: %d events", region, name, len(df))
