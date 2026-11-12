"""Oxford restaurants that Enjoy Oxford (the visitor bureau) lists with the feature "Wheelchair
Accessible", from the listing pages saved by the `web_oxford_restaurants` source.

The tag is self-reported by each business and gives no detail (entrance? restroom?), so the map
shows it as "listed as wheelchair accessible", never as a full rating. Listings without the tag are
kept with `wheelchair_tag: false`: that means "not stated", not "not accessible".

Output: data/extracted/oxford_restaurants.jsonl
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data/processed/oxford/web_oxford_restaurants.docs.parquet"
OUT = ROOT / "data/extracted/oxford_restaurants.jsonl"


def field(lines: list[str], name: str) -> str | None:
    """The line after 'Name:' (the pages print each label and value on separate lines)."""
    for i, ln in enumerate(lines[:-1]):
        if ln == f"{name}:":
            return lines[i + 1]
    return None


def main() -> None:
    d = pd.read_parquet(DOCS).drop_duplicates("url")
    d = d[d.url.str.contains("/restaurant/")]
    rows = []
    for r in d.itertuples():
        lines = [ln.strip() for ln in r.text.split("\n") if ln.strip()]
        name = field(lines, "Restaurant Name")
        if not name:
            continue
        features = field(lines, "Features") or ""
        posted = re.match(r"(\d\d)/(\d\d)/(\d{4})", lines[1] if len(lines) > 1 else "")
        rows.append(
            {
                "name": name,
                "address": field(lines, "Address"),
                "phone": field(lines, "Phone Number"),
                "features": [f.strip() for f in features.split(",") if f.strip()],
                "wheelchair_tag": "Wheelchair Accessible" in features,
                "quote": f"Features:\n{features}" if features else "",
                "listing_date": f"{posted.group(3)}-{posted.group(1)}-{posted.group(2)}" if posted else None,
                "url": r.url,
                "doc_id": r.doc_id,
                "region": "oxford",
                "extracted_by": "scripts/extract_enjoyoxford_restaurants.py",
                "extracted_at": date.today().isoformat(),
            }
        )
    for x in rows:  # the quoted lines must be in the page as saved
        page = [ln.strip() for ln in d[d.doc_id == x["doc_id"]].text.iloc[0].split("\n")]
        q = x["quote"].split("\n") if x["quote"] else []
        if q and not any(page[i : i + 2] == q for i in range(len(page))):
            raise SystemExit(f"quote not in page: {x['name']}")
    rows = sorted({x["url"]: x for x in rows}.values(), key=lambda x: x["name"].lower())
    OUT.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    tagged = [x["name"] for x in rows if x["wheelchair_tag"]]
    print(f"{len(rows)} listings, {len(tagged)} tagged Wheelchair Accessible -> {OUT.relative_to(ROOT)}")
    print(", ".join(tagged))


if __name__ == "__main__":
    main()
