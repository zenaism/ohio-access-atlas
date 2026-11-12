"""Per-source inventory: what each source gave us, how much, and in which categories.

Rebuilt from the files on disk every run (nothing is typed by hand), so it never drifts:
  docs/source_inventory.md   readable table, committed
  data/source_inventory.csv  same rows, for analysis
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from .core import PROCESSED, RAW, ROOT, config

IMG = {"jpg", "jpeg", "png", "webp", "gif"}
COUNTS = [
    "records",
    "pages",
    "pdfs",
    "images",
    "text_chars",
    "facts",
    "places",
    "failed_fetches",
    "robots_skipped",
]


def _top(counter: Counter, n: int = 6) -> str:
    return ", ".join(f"{k} {v:,}" for k, v in counter.most_common(n))


def _manifest(source: str) -> tuple[int, int, str]:
    """(failed fetches, robots-disallowed, last retrieved) from the raw download log."""
    f = RAW / "web" / source / "manifest.jsonl"
    if not f.exists():
        return 0, 0, ""
    recs = [json.loads(line) for line in f.read_text().splitlines()]
    failed = sum(1 for r in recs if not r.get("file") and not str(r["status"]).startswith("robots"))
    robots = sum(1 for r in recs if str(r["status"]).startswith("robots"))
    return failed, robots, max((r["retrieved_at"] for r in recs), default="")[:10]


def build() -> pd.DataFrame:
    facts_file = ROOT / "data/extracted/venue_facts.jsonl"
    facts = pd.read_json(facts_file, lines=True) if facts_file.exists() else pd.DataFrame()
    if len(facts):
        facts["source"] = facts["doc_id"].str.split(":").str[0]
    rows = []
    for source, spec in config("sources").items():
        for region in spec["regions"]:
            d = PROCESSED / region
            row = {"source": source, "type": spec["type"], "region": region}
            ent, obs = d / f"{source}.entities.parquet", d / f"{source}.obs.parquet"
            docs, events = d / f"{source}.docs.parquet", d / f"{source}.events.parquet"
            if ent.exists():
                e = pd.read_parquet(ent, columns=None)
                row["records"] = len(e)
                col = next((c for c in ("entity_type", "basic_category") if c in e), None)
                row["categories"] = _top(Counter(e[col].fillna("unknown"))) if col else ""
            if obs.exists():
                o = pd.read_parquet(obs, columns=["attribute"])
                row["facts"] = len(o)
                row["attributes"] = _top(Counter(o["attribute"]), 5)
            if docs.exists():
                x = pd.read_parquet(docs, columns=["content_type", "chars", "retrieved_at"])
                row["pages"] = int((x.content_type == "html").sum())
                row["pdfs"] = int((x.content_type == "pdf").sum())
                row["images"] = int(x.content_type.isin(IMG).sum())
                row["text_chars"] = int(x.chars.sum())
            if events.exists():
                ev = pd.read_parquet(events, columns=["start"])
                row["records"] = len(ev)
                upcoming = int((ev.start >= pd.Timestamp.now().strftime("%Y-%m-%d")).sum())
                row["categories"] = f"events; {upcoming} upcoming"
            if len(facts):
                f = facts[(facts.source == source) & (facts.region == region)]
                if len(f):
                    row["facts"] = len(f)
                    row["attributes"] = _top(Counter(f.attribute), 5)
                    row["places"] = f.place.nunique()
            failed, robots, last = _manifest(source)
            row.update(failed_fetches=failed, robots_skipped=robots)
            if not last and any(p.exists() for p in (ent, obs, docs, events)):
                newest = max(p.stat().st_mtime for p in (ent, obs, docs, events) if p.exists())
                last = pd.Timestamp(newest, unit="s").strftime("%Y-%m-%d")
            row["last_retrieved"] = last
            row["collected"] = any(p.exists() for p in (ent, obs, docs, events))
            rows.append(row)
    cols = [
        "source",
        "type",
        "region",
        "collected",
        "records",
        "categories",
        "pages",
        "pdfs",
        "images",
        "text_chars",
        "facts",
        "attributes",
        "places",
        "failed_fetches",
        "robots_skipped",
        "last_retrieved",
    ]
    return pd.DataFrame(rows).reindex(columns=cols)


def poster_rows() -> pd.DataFrame:
    rows = []
    for f in sorted((ROOT / "data/manual/posters").glob("*/extraction.json")):
        d = json.loads(f.read_text())
        n = len(d.get("trails") or d.get("segments") or d.get("wheelchair_accessible_symbols") or [])
        rows.append(
            {
                "poster folder": f.parent.name,
                "title": d.get("poster") or d.get("poster_set"),
                "items read": n,
                "files kept": len([p for p in f.parent.rglob("*") if p.is_file()]) - 1,
                "checked by a person": d.get("verified_by_human", False),
            }
        )
    return pd.DataFrame(rows)


EXTRACTED = {  # file -> (what it holds, script that writes it)
    "venue_facts.jsonl": (
        "accessibility facts with verbatim quotes, one per line",
        "scripts/venue_facts_2026_11.py",
    ),
    "traillink_trails.jsonl": (
        "trails TrailLink tags as wheelchair accessible",
        "scripts/extract_traillink.py",
    ),
    "page_events.jsonl": (
        "dated events read from calendar pages without feeds",
        "scripts/extract_page_events.py",
    ),
    "miami_events_classified.jsonl": (
        "upcoming Miami events sorted by usefulness",
        "scripts/classify_miami_events.py",
    ),
}


def extracted_rows() -> pd.DataFrame:
    rows = []
    for name, (what, script) in EXTRACTED.items():
        f = ROOT / "data/extracted" / name
        n = len(f.read_text().splitlines()) if f.exists() else 0
        rows.append({"file": f"data/extracted/{name}", "rows": n, "what": what, "made by": script})
    return pd.DataFrame(rows)


def write() -> Path:
    df = build()
    df.to_csv(ROOT / "data/source_inventory.csv", index=False)
    show = df.copy()
    for c in COUNTS:
        show[c] = show[c].map(lambda v: "" if pd.isna(v) or v == 0 else f"{int(v):,}")
    show["collected"] = show["collected"].map({True: "yes", False: "no"})
    show = show.fillna("")
    out = ROOT / "docs/source_inventory.md"
    out.write_text(
        "# Source inventory\n\n"
        "Generated by `make inventory` from the files on disk; do not edit by hand.\n\n"
        "- **records**: places, features or events kept. **facts**: one detail about one thing "
        "(for web sources: facts read from the pages, each with a verbatim quote).\n"
        "- **categories / attributes**: the most common kinds, with counts.\n"
        "- **failed fetches**: pages that returned an error; "
        "**robots skipped**: pages the site asks bots not to fetch.\n\n"
        + show.to_markdown(index=False)
        + "\n\n## Extracted outputs\n\n"
        + extracted_rows().to_markdown(index=False)
        + "\n\n## Posters and maps read by hand\n\n"
        + poster_rows().to_markdown(index=False)
        + "\n"
    )
    return out
