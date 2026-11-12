# ruff: noqa: E501  (verbatim source text is long by nature)
"""Events read from saved calendar pages that have no feed (first batch, 2026-11-11).

Read by Claude in a Claude Code session. Every field below is copied from the page text; the
validator checks that the title, date text and location text each appear verbatim in the saved
page, and drops any event that fails. Output: data/extracted/page_events.jsonl
"""
from __future__ import annotations

import glob
import json
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from atlas.connectors.web import archived_doc

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = "web_programs_cincinnati:aea761ad0028"
GREAT = "web_programs_cincinnati:9a5f21f8734e"
BUTLER_DD_MOVIE = "web_disability_events:7a7e8d96c679"

# (title, date_text as printed, start ISO, end ISO or None, location as printed, cost, audience, doc, disability_focused)
EVENTS = [
    ("Power Soccer Fall Practices", "Saturday, Nov 14th, 2026 10:00am", "2026-11-14T10:00", None,
     "1641 Blue Rock St, Cincinnati, OH 45223", None, None, BRIDGE, True),
    ("CrossFit (Cincinnati) Program", "Thursday, Nov 12th, 2026 6:30pm", "2026-11-12T18:30", None,
     "8980 Blue Ash Rd, Blue Ash, OH 45242", None, None, BRIDGE, True),
    ("CrossFit (Northern Kentucky) Program", "Wednesday, Nov 11th, 2026 6:30pm", "2026-11-11T18:30", None,
     "111 Beech St suite b, Newport, KY 41071", None, None, BRIDGE, True),
    ("Homeschool Science: Fire to Feast", "Wednesday, November 11", "2026-11-11T10:00", "2026-11-11T12:00",
     "Mitchell Memorial Forest | Pine Meadow", "$9", "Homeschool, ages 6+", GREAT, False),
    ("Creature Chronicles for Kids", "Thursday, November 12", "2026-11-12T10:00", "2026-11-12T11:00",
     "Miami Whitewater Forest | Visitor Center", "Free", "Preschool, ages 2-5", GREAT, False),
    ("Camp Root Ball", "Friday, November 13", "2026-11-13T18:00", "2026-11-13T21:30",
     "Sharonville Convention Center", None, "Adults (fundraiser, tickets)", GREAT, False),
    ("Storytime on the Farm", "Friday, November 13", "2026-11-13T10:30", "2026-11-13T11:15",
     "Winton Woods Farm & Equestrian Center | Hayloft Barn", None, "Preschool", GREAT, False),
    ("Neighborhood Nature Fest", "Saturday, November 14", "2026-11-14T12:00", "2026-11-14T16:00",
     "Nature Center at The Summit", None, "All Ages", GREAT, False),
    # Butler County Board of DD calendar (2026-11-12)
    ("Sensory Friendly Screening – The Polar Express", "December 9, 2026", "2026-12-09T09:45", "2026-12-09T12:00",
     "Fitton Center for Creative Arts", None,
     "Lights and sound turned down; doors 9:45, movie 10:15", BUTLER_DD_MOVIE, True),
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def main() -> None:
    docs = pd.concat([pd.read_parquet(f) for f in glob.glob(str(ROOT / "data/processed/*/web_*.docs.parquet"))])
    text = {r.doc_id: norm(r.text) for r in docs.itertuples()}
    url = dict(zip(docs.doc_id, docs.url, strict=False))
    for doc in {e[7] for e in EVENTS} - set(text):  # page changed since: check against the archived version
        hit = archived_doc(doc)
        if hit:
            url[doc], text[doc] = hit[0], norm(hit[1])
    out, bad = [], []
    for title, date_text, start, end, loc, cost, audience, doc, focused in EVENTS:
        t = text.get(doc, "")
        missing = [f for f, v in (("title", title), ("date", date_text), ("location", loc)) if norm(v) not in t]
        if missing:
            bad.append((title, missing))
            continue
        out.append({"event_id": f"page:{doc}:{start}:{title}", "title": title, "start": start, "end": end or start,
                    "date_text": date_text, "venue": loc, "cost": cost, "audience": audience,
                    "is_disability_focused": focused, "region": "cincinnati", "url": url[doc], "doc_id": doc,
                    "expires_at": (date.fromisoformat((end or start)[:10]) + timedelta(days=1)).isoformat(),
                    "extracted_by": "claude (Claude Code session)", "extracted_at": "2026-11-11",
                    "verified_by_human": False})
    dest = ROOT / "data/extracted/page_events.jsonl"
    dest.write_text("".join(json.dumps(r) + "\n" for r in out))
    print(f"{len(out)} events written to {dest.relative_to(ROOT)}; {len(bad)} rejected {bad}")


if __name__ == "__main__":
    main()
