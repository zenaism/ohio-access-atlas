"""Dated accessible performances (audio description, ASL, sensory-friendly / relaxed) from theatres'
own pages saved by the `web_access_performances` source.

Parsers are written per site because each prints its schedule differently; every event keeps the
exact lines it came from (`quote`) and the run fails loudly if a quote is not in the saved page.

Output: data/extracted/access_performances.jsonl (same shape as page_events.jsonl, plus `access`).
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data/processed/cincinnati/web_access_performances.docs.parquet"
OUT = ROOT / "data/extracted/access_performances.jsonl"
TODAY = date.today().isoformat()
MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}
KINDS = {
    "audio_description": "audio description",
    "asl": "ASL interpreted",
    "sensory_friendly": "sensory-friendly",
}


def season_year(month: int, first_year: int) -> int:
    """A 26-27 season runs from late summer 2026 to summer 2027."""
    return first_year if month >= 8 else first_year + 1


def clock(h: str, m: str | None, ampm: str) -> str:
    hour = int(h) % 12 + (12 if ampm.lower().startswith("p") else 0)
    return f"{hour:02d}:{int(m or 0):02d}"


def event(venue, title, start, kinds, quote, doc, url):
    return {
        "event_id": f"access:{venue}:{start}:{title}",  # same page saved under two URLs -> one event
        "title": title,
        "start": start,
        "end": start,
        "date_text": quote.split("\n")[-1] if "\n" in quote else quote,
        "venue": venue,
        "access": sorted(kinds),
        "is_disability_focused": False,
        "site_tagged_accessible": True,
        "region": "cincinnati",
        "url": url,
        "doc_id": doc.doc_id,
        "quote": quote,
        "extracted_by": "scripts/extract_access_performances.py",
        "extracted_at": TODAY,
        "verified_by_human": False,
    }


# ------------------------------------------------------------- Playhouse --------
PLAY_DATE = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.?,? (?P<mon>[A-Z][a-z]{2})[a-z]*\.? (?P<day>\d{1,2}),? "
    r"(?:at )?(?P<h>\d{1,2})(?::(?P<m>\d{2}))? ?(?P<ap>[ap])\.?m\.?$",
    re.I,
)
PLAY_SECTIONS = [
    ("Relaxed Performances", "sensory_friendly"),
    ("Audio-Described Performances", "audio_description"),
    ("Signed ASL Performances", "asl"),
]


def playhouse(doc) -> list[dict]:
    lines = [ln.strip() for ln in doc.text.split("\n") if ln.strip()]
    m = re.search(r"(\d{2})-(\d{2}) season performance dates", doc.text)
    first = 2000 + int(m.group(1)) if m else date.today().year
    out, kind, title = [], None, None
    for ln in lines:
        sec = next((k for head, k in PLAY_SECTIONS if ln.endswith(head)), None)
        if sec:
            kind, title = sec, None
            continue
        if kind is None:
            continue
        if ln.startswith("Hearing Enhancement System"):
            break
        d = PLAY_DATE.match(ln)
        if d and title:
            mon = MONTHS[d["mon"].lower()]
            start = (
                f"{season_year(mon, first)}-{mon:02d}-{int(d['day']):02d}T{clock(d['h'], d['m'], d['ap'])}"
            )
            out.append(
                event(
                    "Cincinnati Playhouse in the Park",
                    title,
                    start,
                    {kind},
                    f"{title}\n{ln}",
                    doc,
                    "https://cincyplay.com/visit/accessibility",
                )
            )
        elif (
            not ln.isupper()
            and "season performance dates" not in ln
            and len(ln) < 70
            and not ln.startswith(("This service", "Signed performances", "Our sensory", "The Playhouse"))
        ):
            title = ln
    return out


# ------------------------------------------------------- Children's Theatre -----
TCT_DATE = re.compile(
    r"^[–-] (?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, (?P<mon>[A-Z][a-z]+) (?P<day>\d{1,2}) "
    r"at (?P<h>\d{1,2})(?::(?P<m>\d{2}))? ?(?P<ap>[AP])M$"
)


def childrens_theatre(doc) -> list[dict]:
    t = doc.text
    i = t.find("Which MainStage performances are signed & audio described?")
    if i < 0:
        return []
    block = t[i : t.find("School performances", i)]
    lines = [ln.strip() for ln in block.split("\n")[1:] if ln.strip()]
    first = (
        int(re.search(r"(20\d\d)[–-](20\d\d) season", t).group(1))
        if re.search(r"(20\d\d)[–-](20\d\d) season", t)
        else date.today().year
    )
    out, title = [], None
    for ln in lines:
        d = TCT_DATE.match(ln)
        if d and title:
            mon = MONTHS[d["mon"][:3].lower()]
            start = (
                f"{season_year(mon, first)}-{mon:02d}-{int(d['day']):02d}T{clock(d['h'], d['m'], d['ap'])}"
            )
            out.append(
                event(
                    "Children's Theatre of Cincinnati (Emery Theater)",
                    title,
                    start,
                    {"audio_description", "asl"},
                    f"{title}\n{ln}",
                    doc,
                    "https://thechildrenstheatre.com/accessibility/",
                )
            )
        else:
            title = ln
    return out


# ------------------------------------------------------- Cincinnati Shakespeare --
SHAKES_DATE = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) - (?P<mon>[A-Z][a-z]{2}) (?P<day>\d{1,2}), "
    r"(?P<y>20\d\d) - (?P<h>\d{1,2}):(?P<m>\d{2}) (?P<ap>[AP])M$"
)
SHAKES_TAGS = {
    "Audio Description Service Available": "audio_description",
    "Sign Language Interpreted": "asl",
    "Sensory Friendly Performance": "sensory_friendly",
}


def shakespeare(doc) -> list[dict]:
    title = re.sub(r"\s*\|\s*Cincy Shakes.*$", "", doc.title or "").strip()
    lines = [ln.strip() for ln in doc.text.split("\n") if ln.strip()]
    out = []
    for i, ln in enumerate(lines):
        d = SHAKES_DATE.match(ln)
        if not d:
            continue
        tags, kept = [], []  # labels share a line: "Opening Night | Audio Description Service Available"
        for nxt in lines[i + 1 : i + 6]:
            if nxt == "Book" or SHAKES_DATE.match(nxt):
                break
            hit = [x.strip() for x in nxt.split("|") if x.strip() in SHAKES_TAGS]
            if hit:
                tags += hit
                kept.append(nxt)
        if tags:
            mon = MONTHS[d["mon"].lower()]
            start = f"{d['y']}-{mon:02d}-{int(d['day']):02d}T{clock(d['h'], d['m'], d['ap'])}"
            out.append(
                event(
                    "Cincinnati Shakespeare Company",
                    title,
                    start,
                    {SHAKES_TAGS[x] for x in tags},
                    "\n".join([ln, *kept]),
                    doc,
                    doc.url,
                )
            )
    return out


def main() -> None:
    d = pd.read_parquet(DOCS).drop_duplicates("doc_id")
    rows = []
    for doc in d.itertuples():
        if "cincyplay.com/visit/accessibility" in doc.url:
            rows += playhouse(doc)
        elif "thechildrenstheatre.com" in doc.url:
            rows += childrens_theatre(doc)
        elif "cincyshakes.com/on-stage/" in doc.url:
            rows += shakespeare(doc)
    texts = dict(zip(d.doc_id, d.text, strict=True))
    bad = []
    for r in rows:  # every quoted line must be in the saved page, in order
        page = [ln.strip() for ln in texts[r["doc_id"]].split("\n")]
        q = r["quote"].split("\n")
        if not any(page[i : i + len(q)] == q for i in range(len(page))) and not all(x in page for x in q):
            bad.append(r)
    if bad:
        raise SystemExit(f"{len(bad)} events whose quote is not in the page, e.g. {bad[0]['quote']!r}")
    rows = sorted({r["event_id"]: r for r in rows}.values(), key=lambda r: r["start"])
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    up = [r for r in rows if r["start"][:10] >= TODAY]
    by = pd.Series([f"{r['venue']}: {'+'.join(r['access'])}" for r in up]).value_counts()
    print(f"{len(rows)} accessible performances ({len(up)} upcoming) -> {OUT.relative_to(ROOT)}")
    print(by.to_string())


if __name__ == "__main__":
    main()
