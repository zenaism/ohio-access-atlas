"""Website snapshots: venue access pages, government pages, trail sites, guides.

Raw:        data/raw/web/<source>/<sha12>.<ext>  (exact bytes received) + manifest.jsonl (one line per
            fetch: url, status, content type, sha256, retrieved_at, file)
Normalized: data/processed/<region>/<source>.docs.parquet (one row per page or PDF: clean text,
            title, url, dates) -> later chunked into the document index and read by LLM extraction.

Spec keys:  urls: seed pages · follow: URL prefixes whose links we also fetch (one hop)
            assets: also save linked PDFs and images (trail-map posters) · max_pages (default 40)
            author_type: official | business | community | guide
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..core import RAW, USER_AGENT, log, now, out_dir

logging.getLogger("pypdf").setLevel(logging.ERROR)  # noisy about harmless xref quirks

WEB = RAW / "web"
DOC_EXT = (".pdf",)
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")
MAP_WORDS = re.compile(r"map|trail|poster|brochure|guide|access", re.I)
SKIP_WORDS = re.compile(r"logo|icon|qr|badge|favicon|sprite|avatar|/v1/(fill|crop|fit)/", re.I)
DROP = ["script", "style", "noscript", "nav", "header", "footer", "form", "svg", "iframe"]

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT
_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


def _allowed(url: str) -> bool:
    root = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if root not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = _session.get(root + "/robots.txt", timeout=20)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except requests.RequestException:
            rp.parse([])
        _robots[root] = rp
    return _robots[root].can_fetch(USER_AGENT, url)


def _ext(url: str, ctype: str) -> str:
    path = urlparse(url).path.lower()
    for e in DOC_EXT + IMG_EXT:
        if path.endswith(e):
            return e
    if "pdf" in ctype:
        return ".pdf"
    if "calendar" in ctype:
        return ".ics"
    if "json" in ctype:
        return ".json"
    return ".html"


_browser = None


def _render(url: str, shot: Path) -> tuple[int, str, bytes]:
    """Load a JavaScript-built page in headless Chromium; also save a full-page screenshot
    (trail maps drawn in the browser are only visible that way)."""
    global _browser
    if _browser is None:
        from playwright.sync_api import sync_playwright
        _browser = sync_playwright().start().chromium.launch()
    page = _browser.new_page(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
    try:
        resp = page.goto(url, wait_until="load", timeout=90_000)
        page.wait_for_timeout(4000)  # late widgets (Wix, React) render after the load event
        page.screenshot(path=str(shot), full_page=True)
        return (resp.status if resp else 0), page.url, page.content().encode()
    finally:
        page.close()


def snapshot(source: str, url: str, render: bool = False) -> dict:
    """Fetch once per source (cached via the manifest); return the manifest record."""
    d = WEB / source
    d.mkdir(parents=True, exist_ok=True)
    manifest = d / "manifest.jsonl"
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            rec = json.loads(line)
            if (rec["url"] == url and rec.get("rendered", False) == render
                    and not str(rec["status"]).startswith("error")):  # errors are retried
                return rec
    rec = {"url": url, "retrieved_at": now(), "rendered": render}
    if not _allowed(url):
        rec.update(status="robots_disallowed")
    elif render:
        try:
            tmp = d / "_shot.png"
            status, final, body = _render(url, tmp)
            sha = hashlib.sha256(body).hexdigest()
            f, shot = d / f"{sha[:12]}.rendered.html", d / f"{sha[:12]}.screenshot.png"
            f.write_bytes(body)
            tmp.replace(shot)
            rec.update(status=status, final_url=final, content_type="text/html", sha256=sha, bytes=len(body),
                       file=str(f.relative_to(RAW.parent.parent)),
                       screenshot=str(shot.relative_to(RAW.parent.parent)))
        except Exception as e:  # timeouts, crashes: logged in the manifest, run continues
            rec.update(status=f"error: {type(e).__name__}")
    else:
        try:
            r = _session.get(url, timeout=60)
            ctype = r.headers.get("content-type", "")
            rec.update(status=r.status_code, final_url=r.url, content_type=ctype)
            if r.ok:
                sha = hashlib.sha256(r.content).hexdigest()
                f = d / f"{sha[:12]}{_ext(r.url, ctype)}"
                f.write_bytes(r.content)
                rec.update(sha256=sha, file=str(f.relative_to(RAW.parent.parent)), bytes=len(r.content))
        except requests.RequestException as e:
            rec.update(status=f"error: {type(e).__name__}")
        time.sleep(1.0)
    with manifest.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def _clean_html(html: bytes, base: str) -> tuple[str, str, list[str]]:
    soup = BeautifulSoup(html, "lxml")
    if (b := soup.find("base", href=True)) is not None:  # relative links resolve against <base href>
        base = urljoin(base, b["href"])
    title = (soup.title.get_text(" ", strip=True) if soup.title else "")[:300]
    links = [urldefrag(urljoin(base, a["href"]))[0] for a in soup.find_all("a", href=True)]
    links += [urljoin(base, i["src"]) for i in soup.find_all("img", src=True)]
    for tag in soup(DROP):
        tag.decompose()
    # <main> is often a sign-up widget on JS sites; keep it only if it holds most of the page text
    body = soup.body or soup
    main = soup.find("main") or soup.find("article")
    if main is None or len(main.get_text(strip=True)) < 0.5 * len(body.get_text(strip=True)):
        main = body
    text = re.sub(r"\n\s*\n+", "\n\n", main.get_text("\n", strip=True))
    return title, text, links


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    try:
        return "\n\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    except Exception as e:  # damaged PDFs: keep the raw file, note the failure
        return f"[pdf text extraction failed: {type(e).__name__}]"


def run(name: str, spec: dict, region: str) -> None:
    todo, seen, docs = list(spec["urls"]), set(), []
    follow, max_pages = spec.get("follow", []), spec.get("max_pages", 40)
    hop = {u: 0 for u in todo}
    seed_hosts = {urlparse(u).netloc for u in todo}
    while todo and len(seen) < max_pages:
        url = todo.pop(0)
        if url in seen:
            continue
        seen.add(url)
        is_page = not urlparse(url).path.lower().endswith(DOC_EXT + IMG_EXT)
        rec = snapshot(name, url, render=bool(spec.get("render")) and is_page)
        if not rec.get("file"):
            log.warning("[%s] %s: %s %s", region, name, rec["status"], url)
            continue
        data = (RAW.parent.parent / rec["file"]).read_bytes()
        ext = Path(rec["file"]).suffix  # ".rendered.html" -> ".html"
        title, text, links = "", "", []
        if ext == ".html":
            title, text, links = _clean_html(data, rec.get("final_url", url))
        elif ext == ".pdf":
            title, text = Path(urlparse(url).path).name, _pdf_text(data)
        docs.append({"doc_id": f"{name}:{rec['sha256'][:12]}", "source": name, "url": url,
                     "screenshot": rec.get("screenshot"),
                     "title": title, "text": text, "content_type": ext.lstrip("."),
                     "raw_file": rec["file"], "retrieved_at": rec["retrieved_at"],
                     "author_type": spec.get("author_type", "official"), "region": region,
                     "chars": len(text)})
        if hop[url] >= 1:
            continue
        for host in spec.get("asset_hosts", []):  # sites (Wix) that keep images in embedded JSON
            links += re.findall(rf"https://{re.escape(host)}/[^\"'\s\\)]+?\.(?:jpe?g|png|webp|pdf)",
                                data.decode("utf8", "ignore"))
        for link in dict.fromkeys(links):
            lext = urlparse(link).path.lower()
            same_site = urlparse(link).netloc in seed_hosts | set(spec.get("asset_hosts", []))
            pdf = lext.endswith(DOC_EXT)
            # images only when they look like trail maps / posters / guides on the source's own site
            img = (lext.endswith(IMG_EXT) and same_site and not SKIP_WORDS.search(lext)
                   and (MAP_WORDS.search(lext) or urlparse(link).netloc in spec.get("asset_hosts", [])))
            asset = spec.get("assets") and (pdf or img)
            page = not lext.endswith(DOC_EXT + IMG_EXT) and any(link.startswith(p) for p in follow)
            if link not in hop and (asset or page):
                hop[link] = 1
                todo.append(link)
    df = pd.DataFrame(docs)
    df.to_parquet(out_dir(region) / f"{name}.docs.parquet", index=False)
    log.info("[%s] %s: %d documents (%d pdf, %d image), %d chars of text", region, name, len(df),
             (df.content_type == "pdf").sum() if len(df) else 0,
             df.content_type.isin([e.lstrip(".") for e in IMG_EXT]).sum() if len(df) else 0,
             df.chars.sum() if len(df) else 0)

