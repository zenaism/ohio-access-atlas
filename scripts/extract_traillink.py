# ruff: noqa: E501  (long regex and source text)
"""TrailLink 'wheelchair accessible trails' city pages -> one record per trail.

Reads the rendered pages saved by the web connector and writes data/extracted/traillink_trails.jsonl.
Each record keeps the exact text block it came from (evidence) and which city pages listed it.
TrailLink's own caveat applies: a trail tagged wheelchair accessible may not be accessible along its
whole length, so these records rate 'listed as wheelchair accessible by TrailLink', not 'accessible'.
"""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(
    r"\n([^\n]{2,80})\n([\d.,]+) mi\nState: ([A-Z, ]+)\n([A-Za-z ,]+)(?=\n|$)"
)  # lookahead: entries share newlines


def main() -> None:
    docs = pd.concat(
        [pd.read_parquet(f) for f in glob.glob(str(ROOT / "data/processed/*/web_trails_*.docs.parquet"))]
    )
    pages = docs[docs.url.str.contains("traillink.com/cityactivity/")].drop_duplicates("url")
    trails: dict[str, dict] = {}
    for p in pages.itertuples():
        city = re.search(r"cityactivity/([a-z-]+?)-wheelchair", p.url).group(1)
        # the listing ends where the detail table starts ("Trail Image / Trail Name / ...")
        listing = p.text.split("\nTrail Image\n")[0]
        for m in BLOCK.finditer(listing):
            name, miles, states, surface = (g.strip() for g in m.groups())
            rec = trails.setdefault(
                name,
                {
                    "trail": name,
                    "length_mi": float(miles.replace(",", "")),
                    "states": [s.strip() for s in states.split(",")],
                    "surface": [s.strip() for s in surface.split(",")],
                    "paved": all(s.strip() in {"Asphalt", "Concrete"} for s in surface.split(",")),
                    "traillink_tag": "wheelchair accessible",
                    "listed_on": [],
                    "evidence": m.group(0).strip(),
                    "source_urls": [],
                    "doc_ids": [],
                    "retrieved_at": p.retrieved_at,
                    "caveat": "TrailLink: not all trails marked wheelchair friendly are accessible along their whole length",
                },
            )
            if city not in rec["listed_on"]:
                rec["listed_on"].append(city)
                rec["source_urls"].append(p.url)
                rec["doc_ids"].append(p.doc_id)
    out = ROOT / "data/extracted/traillink_trails.jsonl"
    rows = sorted(trails.values(), key=lambda r: (-len(r["listed_on"]), r["trail"]))
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    ohio = [r for r in rows if "OH" in r["states"]]
    print(
        f"{len(rows)} trails ({len(ohio)} in Ohio, {sum(r['paved'] for r in rows)} fully paved) "
        f"from {len(pages)} city pages -> {out.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
