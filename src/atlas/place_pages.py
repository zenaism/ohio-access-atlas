# ruff: noqa: E501  (embedded HTML template)
"""One plain page per place, plus an A–Z index per city.

Why: a map app is hard work with a screen reader. These pages carry the same information as the
place's card and details (what is known, arriving, getting there, every fact with its quote and
source, upcoming events, who to ask) as ordinary headings, lists and links. They load fast on a
phone, can be sent by text message, and give the future assistant a stable page to cite.

Output: data/map/places/<region>/<link_id>.html and data/map/places/<region>/index.html
"""

from __future__ import annotations

import shutil
from html import escape
from pathlib import Path

from .map_viewer import ICONS, RATING_HELP, RATINGS

SITE = "https://zenaism.github.io/ohio-access-atlas/data/map"
REPO = "https://github.com/zenaism/ohio-access-atlas"
MARK = {"yes": "✓", "partly": "~", "no": "✕", "not known": "?"}
ACCESS = {
    "audio_description": "audio described",
    "asl": "ASL interpreted",
    "sensory_friendly": "sensory-friendly",
}


def _access(e: dict) -> str:
    a = [ACCESS.get(x, x) for x in e.get("access") or []]
    if a:
        return f" <strong>({', '.join(a)})</strong>"
    return " (listed as accessible)" if e.get("accessible_tag") else ""


def _when(start: str) -> str:
    """2026-12-05T14:00 -> Saturday, December 5, 2026, 2 PM"""
    from datetime import datetime

    d = datetime.fromisoformat(start[:16])
    t = d.strftime("%-I:%M %p").replace(":00 ", " ") if len(start) > 10 and start[11:16] != "00:00" else ""
    return d.strftime("%A, %B %-d, %Y") + (f", {t}" if t else "")


CSS = """
:root{color-scheme:light;--ink:#1b1f24;--muted:#4b5563;--line:#e5e7eb;--link:#0a58ca}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:#fff}
a{color:var(--link)} a:focus-visible,button:focus-visible{outline:3px solid #1d4ed8;outline-offset:2px}
.skip{position:absolute;left:-9999px} .skip:focus{left:12px;top:12px;background:#fff;padding:8px;z-index:9}
header,main,footer{max-width:760px;margin:0 auto;padding:16px 20px}
header{border-bottom:1px solid var(--line)} header p{margin:0;color:var(--muted);font-size:14px}
h1{font-size:1.7rem;line-height:1.25;margin:.4rem 0 .3rem} h2{font-size:1.2rem;margin:1.8rem 0 .5rem}
.rating{display:inline-flex;gap:8px;align-items:center;font-weight:600}
.rating i{font-style:normal;width:22px;height:22px;border-radius:50%;display:inline-grid;place-items:center;font-size:13px}
.type{color:var(--muted)}
.keys{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px 8px}
.keys li{background:#f3f4f6;border-radius:999px;padding:3px 10px}
.keys b{display:inline-block;width:1.1em}
.facts{list-style:none;padding:0} .facts>li{border-top:1px solid var(--line);padding:10px 0}
.facts h3{font-size:1rem;margin:0 0 .2rem} .q{color:var(--muted);font-style:italic;margin:.25rem 0}
.src{font-size:14px} .note{color:var(--muted);font-size:14px}
.old{color:#9a3412;font-weight:600}
.actions{display:flex;flex-wrap:wrap;gap:8px 16px;margin:12px 0}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:14px;margin-top:2rem}
.az{columns:2;column-gap:28px} .az li{break-inside:avoid;margin:2px 0}
@media (max-width:560px){.az{columns:1}}
"""


def _page(title: str, body: str, canonical: str, up: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><link rel="canonical" href="{canonical}">
<style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header><p>{up}</p></header>
<main id="main">{body}</main>
<footer><p>Ohio Access Atlas, a Miami University research project. Information comes from the sources linked
on each page and may be out of date; please call ahead. <a href="{REPO}/issues/new">Report a problem</a>.</p></footer>
</body></html>
"""


def _rating(r: str) -> str:
    label, colour, sym, glyph = RATINGS[r]
    return (
        f'<p class="rating"><i aria-hidden="true" style="background:{colour};color:{glyph}">{sym}</i>'
        f"{label}</p>"
    )


def _getting_there(g: dict) -> str:
    if not g:
        return ""
    li = []
    if g.get("arrival"):
        li.append(f"<li><strong>Arriving:</strong> {escape(g['arrival'])}</li>")
    if g.get("bus_stop") and "bus stop" not in g.get("arrival", ""):
        b = g["bus_stop"]
        ft = max(50, round(b["metres"] * 3.28084 / 50) * 50)
        li.append(f"<li>Nearest bus stop: {escape(b['name'])}, about {ft} feet.</li>")
    elif not g.get("bus_stop"):
        li.append("<li>No bus stop within half a mile.</li>")
    if g.get("steep_sections"):
        n = g["steep_sections"]
        li.append(
            f"<li>{n} path section{'s' if n > 1 else ''} steeper than a ramp (8.33%) within 500 feet; "
            f"steepest about {g['steepest_pct']}%.</li>"
        )
    elif "steep_sections" in g:
        li.append("<li>No path steeper than a ramp (8.33%) within 500 feet.</li>")
    for k, one, many in [
        ("stairs", "mapped stairway", "mapped stairways"),
        ("curb_ramps", "city-mapped curb ramp", "city-mapped curb ramps"),
        (
            "accessible_signals",
            "crossing with accessible signals (sound or vibration)",
            "crossings with accessible signals (sound or vibration)",
        ),
        ("tactile_paving", "spot with tactile paving", "spots with tactile paving"),
    ]:
        if g.get(k):
            li.append(f"<li>{g[k]} {one if g[k] == 1 else many} within 500 feet.</li>")
    if g.get("reports_12m"):
        li.append(
            f"<li>{g['reports_12m']} sidewalk or curb problem report{'s' if g['reports_12m'] > 1 else ''} "
            f"to 311 in the past year ({g['reports_open']} still open).</li>"
        )
    out = (
        "<h2>Getting there</h2><ul>" + "".join(li) + "</ul>"
        '<p class="note">Computed from map data, not checked on site. Distances in this list are '
        "straight-line; slopes are estimated from elevation data.</p>"
    )
    r = g.get("route")
    if r:
        out += (
            f"<h2>Step-free route from {escape(r['from'])}</h2>"
            f"<p>About {r['length_feet']:,} feet. {escape(r['compared_with_shortest'])} "
            f"{escape(r.get('crossings_text', ''))}</p>"
            "<ol>" + "".join(f"<li>{escape(d)}</li>" for d in r["directions"]) + "</ol>"
            '<p class="note">Suggested from OpenStreetMap paths and USGS elevation; avoids mapped stairs and '
            "steep sections. Not checked on site: sidewalks and curb ramps may be missing from the map.</p>"
        )
        b = r.get("blind")
        if b:
            out += (
                "<h2>Route with safer crossings (for blind or low-vision travelers)</h2>"
                f"<p>About {b['length_feet']:,} feet. Prefers crossings with traffic signals and avoids unmarked "
                f"ones. {escape(b['crossings_text'])}</p>"
                "<ol>" + "".join(f"<li>{escape(d)}</li>" for d in b["directions"]) + "</ol>"
            )
    return out


def _facts(p: dict) -> str:
    fs = p.get("facts") or []
    if not fs:
        return ""
    out = []
    for f in fs:
        h = f"<li><h3>{escape(str(f['attribute']))}: {escape(str(f['value']))}</h3>"
        if f.get("detail"):
            h += f"<p>{escape(str(f['detail']))}</p>"
        if f.get("quote"):
            h += f'<p class="q">“{escape(str(f["quote"])[:400])}”</p>'
        if f.get("source"):
            h += (
                f'<p class="src"><a href="{escape(f["source"])}">Source</a>'
                + (f" · {escape(str(f['date']))}" if f.get("date") else "")
                + "</p>"
            )
        out.append(h + "</li>")
    return '<h2>What the sources say</h2><ul class="facts">' + "".join(out) + "</ul>"


def _events(p: dict, today: str) -> str:
    evs = [e for e in p.get("events") or [] if e.get("start", "")[:10] >= today]
    if not evs:
        return ""
    li = "".join(
        f'<li>{escape(_when(e["start"]))}: <a href="{escape(e["url"])}">{escape(e["title"])}</a>'
        + _access(e)
        + "</li>"
        for e in evs[:25]
    )
    return f"<h2>Upcoming events ({len(evs)})</h2><ul>{li}</ul>"


def _contacts(p: dict) -> str:
    c = p.get("contacts") or {}
    items = [f'<a href="mailto:{escape(e)}">{escape(e)}</a>' for e in c.get("emails", [])]
    items += [
        f'<a href="tel:{"".join(ch for ch in t if ch.isdigit())}">{escape(t)}</a>'
        for t in c.get("phones", [])
    ]
    return f"<h2>Ask before you go</h2><p>{' · '.join(items)}</p>" if items else ""


def place_html(f: dict, region: str, generated: str) -> str:
    p = f["properties"]
    lon, lat = f["geometry"]["coordinates"] if f["geometry"]["type"] == "Point" else (None, None)
    city = region.title()
    keys = p.get("keys") or []
    body = f"<h1>{escape(p['name'])}</h1>"
    body += _rating(p["access_rating"])
    body += f'<p class="type">{escape(ICONS[p["layer"]][0])}, {city}. {escape(RATING_HELP[p["access_rating"]].capitalize())}.</p>'
    if p.get("notice"):
        body += f'<p class="old"><strong>Notice:</strong> {escape(p["notice"])}</p>'
    if p.get("newest_source") and p["newest_source"] < "2023":
        body += f'<p class="old">Newest source is from {p["newest_source"][:4]}; it may be out of date.</p>'
    if keys:
        body += (
            '<h2>What is known</h2><ul class="keys">'
            + "".join(
                f'<li><b aria-hidden="true">{MARK[v]}</b>{escape(k)}: {escape(v)}</li>' for k, v in keys
            )
            + "</ul>"
        )
    body += f"<h2>Summary</h2><p>{escape(p.get('summary') or '')}</p>"
    body += _getting_there(p.get("getting_there") or {})
    body += _facts(p)
    body += _events(p, generated)
    body += _contacts(p)
    links = [f'<a href="../../{region}.html#place={escape(p["link_id"])}">Show on the map</a>']
    if lat is not None:
        links.append(
            f'<a href="https://www.google.com/maps/dir/?api=1&amp;destination={lat},{lon}&amp;travelmode=walking">'
            "Directions in Google Maps</a>"
        )
    links.append(f'<a href="{REPO}/issues/new?title={escape("Report: " + p["name"])}">Report a problem</a>')
    body += '<h2>Links</h2><p class="actions">' + "".join(links) + "</p>"
    body += f'<p class="note">Data as of {generated}.</p>'
    up = f'<a href="index.html">All places in {city}</a> · <a href="../../{region}.html">{city} map</a>'
    return _page(
        f"{p['name']}: accessibility, {city}", body, f"{SITE}/places/{region}/{p['link_id']}.html", up
    )


def index_html(fc: dict, region: str) -> str:
    city = region.title()
    by_layer: dict[str, list] = {}
    for f in fc["features"]:
        by_layer.setdefault(f["properties"]["layer"], []).append(f["properties"])
    order = [
        "culture",
        "park",
        "adaptive_recreation",
        "lodging",
        "building",
        "food_drink",
        "service",
        "trail",
        "event",
        "restroom",
    ]
    body = f"<h1>All places in {city}</h1>"
    body += (
        f"<p>{len(fc['features'])} places, grouped by type and sorted A to Z. Each name opens a page with what is "
        "known about wheelchair and blind or low vision access, how to get there, and the sources.</p>"
    )
    if any(e.get("access") for f in fc["features"] for e in f["properties"].get("events") or []):
        body += (
            '<p><a href="shows.html">Audio-described, ASL and sensory-friendly performances by date</a></p>'
        )
    body += (
        "<p>Jump to: "
        + " · ".join(
            f'<a href="#{k}">{escape(ICONS[k][0])} ({len(by_layer[k])})</a>' for k in order if k in by_layer
        )
        + "</p>"
    )
    for k in order:
        if k not in by_layer:
            continue
        items = sorted(by_layer[k], key=lambda p: p["name"].lower())
        body += (
            f'<h2 id="{k}">{escape(ICONS[k][0])}</h2><ul class="az">'
            + "".join(
                f'<li><a href="{escape(p["link_id"])}.html">{escape(p["name"])}</a>, '
                f"{RATINGS[p['access_rating']][0].lower()}</li>"
                for p in items
            )
            + "</ul>"
        )
    up = f'<a href="../../{region}.html">{city} map</a>'
    return _page(f"All places in {city}: Ohio Access Atlas", body, f"{SITE}/places/{region}/index.html", up)


def shows_html(fc: dict, region: str) -> str | None:
    """Audio-described, ASL-interpreted and sensory-friendly performances by date."""
    city, today = region.title(), fc["generated"]
    rows = sorted(
        ((e["start"], e["title"]), e, f["properties"])
        for f in fc["features"]
        for e in f["properties"].get("events") or []
        if e.get("access") and e["start"][:10] >= today
    )
    if not rows:
        return None
    body = f"<h1>Accessible performances in {city}</h1>"
    body += (
        "<p>Audio-described, sign language (ASL) interpreted and sensory-friendly performances that theatres "
        f"list on their own websites, soonest first ({len(rows)} upcoming). Book through the theatre and say "
        "you need the service; dates can change.</p>"
    )
    month = None
    for (start, _), e, p in rows:
        if start[:7] != month:
            from datetime import date as _d

            label = _d.fromisoformat(start[:10]).strftime("%B %Y")
            body += ("</ul>" if month else "") + f"<h2>{label}</h2><ul>"
            month = start[:7]
        body += (
            f'<li><strong>{escape(_when(start))}</strong>: <a href="{escape(e["url"])}">{escape(e["title"])}</a>'
            f'{_access(e)}, at <a href="{escape(p["link_id"])}.html">{escape(p["name"])}</a></li>'
        )
    body += "</ul>"
    up = f'<a href="index.html">All places in {city}</a> · <a href="../../{region}.html">{city} map</a>'
    return _page(f"Accessible performances in {city}", body, f"{SITE}/places/{region}/shows.html", up)


def write(data: dict[str, dict], out: Path) -> list[Path]:
    written = []
    for region, fc in data.items():
        d = out / "places" / region
        if d.exists():
            shutil.rmtree(d)  # places can disappear between builds; start clean
        d.mkdir(parents=True)
        for f in fc["features"]:
            path = d / f"{f['properties']['link_id']}.html"
            path.write_text(place_html(f, region, fc["generated"]))
            written.append(path)
        (d / "index.html").write_text(index_html(fc, region))
        written.append(d / "index.html")
        shows = shows_html(fc, region)
        if shows:
            (d / "shows.html").write_text(shows)
            written.append(d / "shows.html")
    return written
