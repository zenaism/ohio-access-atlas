# ruff: noqa: E501  (embedded HTML/JS template)
"""Self-contained HTML viewer for the atlas GeoJSON (Leaflet from a CDN; data embedded).

Designed list-first so it works without sight: the list of places (left) is the main interface for
screen readers and keyboards; the map (right) is a visual companion whose markers are kept out of
the tab order. Ratings are always given as text plus a symbol, never by colour alone. Colours are
Okabe-Ito (colour-blind safe); marker glyphs meet 3:1 contrast against their disc.
"""

from __future__ import annotations

import json

RATINGS = {  # value -> (label, colour, symbol, glyph colour on the disc)
    "accessible": ("Accessible", "#0072B2", "✓", "#ffffff"),
    "partial": ("Partly accessible", "#E69F00", "~", "#1a1a1a"),
    "not_accessible": ("Not accessible", "#D55E00", "✕", "#ffffff"),
    "unknown": ("No information yet", "#767676", "?", "#ffffff"),
}
RATING_HELP = {
    "accessible": "step-free entry and an accessible restroom are stated, or the trail is paved",
    "partial": "some access features are stated",
    "not_accessible": "a source says it is not accessible",
    "unknown": "no source yet; this does not mean it is inaccessible",
}

# 20x20 pictograms; "currentColor" takes the glyph colour of the rating
ICONS = {
    "culture": ("Museum or attraction", '<path d="M10 3 17 7H3z" fill="currentColor"/><path d="M5 8v6M8.3 8v6M11.7 8v6M15 8v6" stroke="currentColor" stroke-width="1.6"/><path d="M3 15.5h14" stroke="currentColor" stroke-width="1.8"/>'),
    "park": ("Park or garden", '<circle cx="10" cy="8" r="5" fill="currentColor"/><path d="M10 11v6" stroke="currentColor" stroke-width="2"/>'),
    "restroom": ("Restroom", '<text x="10" y="14" text-anchor="middle" font-size="9" font-weight="700" font-family="Arial,sans-serif" fill="currentColor">WC</text>'),
    "adaptive_recreation": ("Adaptive recreation", '<circle cx="11" cy="4" r="1.8" fill="currentColor"/><path d="M10.5 6.5v5h4l2 4" stroke="currentColor" stroke-width="1.7" fill="none"/><circle cx="8.5" cy="13" r="4" stroke="currentColor" stroke-width="1.7" fill="none"/>'),
    "lodging": ("Lodging", '<path d="M3 15V6M3 12h14v3M17 15v-3" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="6.5" cy="9.5" r="1.6" fill="currentColor"/><path d="M9 11V8.5h6.5a1.5 1.5 0 0 1 1.5 1.5v1" fill="currentColor"/>'),
    "event": ("Event venue", '<rect x="3.5" y="5" width="13" height="11" rx="1.5" stroke="currentColor" stroke-width="1.7" fill="none"/><path d="M3.5 8.5h13M7 3v3.5M13 3v3.5" stroke="currentColor" stroke-width="1.7"/>'),
    "building": ("Building (campus or public)", '<path d="M4 17V5l6-2 6 2v12" stroke="currentColor" stroke-width="1.7" fill="none"/><path d="M8.5 17v-4h3v4M7 7.5h2M11 7.5h2M7 10.5h2M11 10.5h2" stroke="currentColor" stroke-width="1.5"/>'),
    "food_drink": ("Food and drink", '<path d="M6 3v6a2 2 0 0 0 2 2v6M8 3v5M4 3v5a2 2 0 0 0 2 2" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/><path d="M14 17V3c-2 1.5-2.5 4-2.5 7H14" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'),
    "service": ("Shop or service", '<path d="M4 7h12l-1 10H5z" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/><path d="M7.5 7V5.5a2.5 2.5 0 0 1 5 0V7" stroke="currentColor" stroke-width="1.6" fill="none"/>'),
    "trail": ("Trail", '<path d="M3 16c3-2 3-6 7-7s4-4 7-6" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round"/>'),
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>__TITLE__ · Ohio Access Atlas</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Wheelchair accessibility of places, restrooms, trails and events, with sources.">
<meta name="theme-color" content="#ffffff">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
 :root{--ink:#111827;--muted:#6b7280;--line:#eceef1;--soft:#f6f7f9;--accent:#111827;--focus:#2563eb;--side:380px;--head:60px;
       --shadow:0 1px 2px rgba(17,24,39,.06),0 4px 16px rgba(17,24,39,.08);--r:14px}
 *{box-sizing:border-box} [hidden]{display:none!important} html,body{height:100%;margin:0}
 body{font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--ink);background:#fff;
      display:flex;flex-direction:column;-webkit-font-smoothing:antialiased}
 a{color:var(--ink);text-underline-offset:2px} :focus-visible{outline:2.5px solid var(--focus);outline-offset:2px;border-radius:6px}
 .vh{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
 .skip{position:absolute;left:12px;top:-80px;background:#fff;padding:10px 14px;border-radius:10px;z-index:4000;box-shadow:var(--shadow);font-weight:600}
 .skip:focus{top:10px}
 button,.btn{font:inherit;font-size:14px;line-height:1;padding:9px 12px;border-radius:10px;border:1px solid var(--line);background:#fff;color:var(--ink);
   cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:7px;transition:background .15s,border-color .15s}
 button:hover,.btn:hover{background:var(--soft)} .ghost{border-color:transparent;background:transparent;padding:7px 8px;color:#374151}
 .primary{background:var(--accent);border-color:var(--accent);color:#fff} .primary:hover{background:#1f2937}
 svg.i{width:18px;height:18px;flex:none}
 /* top bar */
 header{height:var(--head);flex:none;display:flex;align-items:center;gap:12px;padding:0 14px;border-bottom:1px solid var(--line);background:#fff;z-index:1200}
 .brand{min-width:0;flex:1} header h1{font-size:16px;font-weight:650;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.01em}
 header .sub{margin:0;font-size:12px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis} header .sub a{color:var(--muted)}
 .search{position:relative;width:min(340px,34vw)} .search svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--muted)}
 .search input{width:100%;font:inherit;font-size:14px;padding:10px 12px 10px 36px;border-radius:10px;border:1px solid var(--line);background:var(--soft)}
 .search input:focus{background:#fff}
 /* layout */
 .app{flex:1;min-height:0;display:grid;grid-template-columns:var(--side) 1fr;position:relative}
 body.list-closed .app{grid-template-columns:0 1fr}
 .side{min-height:0;display:flex;flex-direction:column;border-right:1px solid var(--line);background:#fff;overflow:hidden}
 body.list-closed .side{visibility:hidden}
 .sheet-bar{display:none}
 .side-body{overflow-y:auto;padding:14px 16px 24px;flex:1}
 .filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px}
 .filters select{font:inherit;font-size:14px;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:#fff;flex:1;min-width:160px}
 .filters label.cb{display:flex;gap:8px;align-items:center;font-size:13.5px;color:#374151;width:100%}
 #status{font-size:12.5px;color:var(--muted);margin:6px 0 8px}
 ol#list{list-style:none;margin:0;padding:0}
 .card{padding:14px 2px;border-top:1px solid var(--line)} .card:first-child{border-top:0}
 .card h3{font-size:15.5px;font-weight:620;margin:0;line-height:1.3;letter-spacing:-.005em} .card h3:focus{outline:2.5px solid var(--focus)}
 .meta{font-size:12.5px;color:var(--muted);margin:3px 0 0;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center}
 .rb{display:inline-flex;align-items:center;gap:6px;color:#374151;font-weight:550}
 .rb i{font-style:normal;width:16px;height:16px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:700}
 .sum{margin:7px 0 8px;font-size:14px;color:#374151}
 .actions{display:flex;gap:2px;flex-wrap:wrap;margin-left:-8px}
 .det{margin:6px 0 0;padding:10px 12px;background:var(--soft);border-radius:12px;font-size:13.5px}
 .det table{border-collapse:collapse;width:100%} .det th,.det td{text-align:left;vertical-align:top;padding:6px 4px;border-bottom:1px solid #e5e7eb}
 .det tr:last-child th,.det tr:last-child td{border-bottom:0} .det th{width:36%;font-weight:600} .q{color:var(--muted);font-style:italic}
 .det ul{margin:4px 0;padding-left:18px}
 .old{color:#92400e} .det .links{display:flex;gap:2px;flex-wrap:wrap;margin:8px 0 0 -8px}
 #more{width:100%;justify-content:center;margin-top:12px}
 /* map */
 .mapwrap{position:relative;min-height:0} #map{position:absolute;inset:0;background:#eef0f2}
 .leaflet-tile-pane{filter:grayscale(.9) brightness(1.07) contrast(.88)}
 .leaflet-bar{border:0!important;box-shadow:var(--shadow)!important;border-radius:12px!important;overflow:hidden}
 .leaflet-bar a{width:36px!important;height:36px!important;line-height:36px!important;border-bottom:1px solid var(--line)!important;color:var(--ink)!important}
 .leaflet-control-attribution{font-size:10.5px;background:rgba(255,255,255,.8)!important;border-radius:8px 0 0 0}
 .leaflet-popup-content-wrapper{border-radius:14px;box-shadow:var(--shadow)} .leaflet-popup-content{margin:12px 14px;font-size:14px}
 .leaflet-popup-content h3{margin:0 0 4px;font-size:15px}
 .mc{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;background:#fff;color:var(--ink);font-weight:650;font-size:13px;
     box-shadow:0 0 0 4px rgba(17,24,39,.10),0 2px 6px rgba(17,24,39,.18)}
 .edge{position:absolute;left:0;top:14px;z-index:1100;width:26px;height:52px;padding:0;justify-content:center;border:1px solid var(--line);
       border-left:0;border-radius:0 12px 12px 0;background:#fff;box-shadow:var(--shadow);color:#374151}
 .edge:hover{background:var(--soft);width:30px} .edge svg{transition:transform .2s}
 body.list-closed .edge svg{transform:rotate(180deg)}
 .side{transition:none} .app{transition:grid-template-columns .22s ease}
 .legend{position:absolute;right:12px;bottom:28px;z-index:1000;background:#fff;border-radius:var(--r);box-shadow:var(--shadow);font-size:13px;max-width:330px}
 .legend summary{list-style:none;cursor:pointer;padding:9px 14px;font-weight:600;display:flex;gap:8px;align-items:center}
 .legend summary::-webkit-details-marker{display:none}
 .legend[open] summary{border-bottom:1px solid var(--line)} .legend-body{padding:8px 14px 12px}
 .legend ul{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:6px} .legend li{display:flex;gap:9px;align-items:center}
 .legend .rb{min-width:150px}
 /* tablet */
 @media (max-width:1100px){ :root{--side:330px} .search{width:min(280px,30vw)} }
 /* phone: map full screen, list as a bottom sheet */
 @media (max-width:720px){
   :root{--head:auto}
   header{flex-wrap:wrap;padding:10px 12px;gap:8px}
   .brand{flex:1 1 100%} header h1{font-size:15.5px} header .sub{white-space:normal}
   .search{flex:1 1 auto;width:auto;min-width:0}
   #near{flex:none}
   .edge{display:none}
   .app{display:block}
   .mapwrap{position:absolute;inset:0}
   .side{position:fixed;left:0;right:0;bottom:0;z-index:1500;border:0;border-radius:18px 18px 0 0;box-shadow:0 -6px 24px rgba(17,24,39,.16);
         height:72vh;transform:translateY(calc(72vh - 64px - env(safe-area-inset-bottom)));transition:transform .25s ease;visibility:visible!important}
   body.sheet-open .side{transform:translateY(0)}
   .sheet-bar{display:flex;width:100%;border:0;border-radius:18px 18px 0 0;padding:10px 16px 14px;justify-content:space-between;align-items:center;
              flex-direction:column;gap:8px;background:#fff;font-weight:600}
   .sheet-bar::before{content:"";width:40px;height:4px;border-radius:4px;background:#d1d5db}
   .sheet-bar span{display:flex;width:100%;justify-content:space-between}
   body:not(.sheet-open) .side-body{visibility:hidden}
   .legend{bottom:calc(76px + env(safe-area-inset-bottom));right:10px;max-width:calc(100vw - 20px)}
   .leaflet-bottom .leaflet-control-attribution{margin-bottom:64px;font-size:9.5px}
 }
 @media (prefers-reduced-motion:reduce){ *{transition:none!important} }
</style></head><body>
<a class="skip" href="#list-h">Skip to the list of places</a>
<header>
 <div class="brand"><h1>__TITLE__</h1><p class="sub">Data as of <span id="asof"></span>__NAV__</p></div>
 <div class="search" role="search">
  <svg class="i" viewBox="0 0 20 20" aria-hidden="true"><circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="m14 14 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
  <label for="q" class="vh">Search places, trails and venues</label>
  <input id="q" type="search" placeholder="Search" autocomplete="off"></div>
 <button id="near" class="primary" type="button">
  <svg class="i" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3" fill="currentColor"/><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>Near me</button>
</header>
<main class="app">
 <section class="side" id="side" aria-labelledby="list-h">
  <button class="sheet-bar" id="sheet" type="button" aria-controls="side-body" aria-expanded="false"><span><span id="sheet-label">Places</span><span>Show list</span></span></button>
  <div class="side-body" id="side-body">
   <h2 id="list-h" tabindex="-1" class="vh">Places</h2>
   <div class="filters">
    <label for="need" class="vh">Show</label><select id="need"></select>
    <label for="when" class="vh">When</label><select id="when" hidden>
     <option value="0">Any date</option><option value="1">Today</option><option value="7">Next 7 days</option><option value="30">Next 30 days</option></select>
    <label class="cb"><input type="checkbox" id="known"> Only places with accessibility information</label>
   </div>
   <p id="status" role="status" aria-live="polite"></p>
   <ol id="list"></ol>
   <button id="more" type="button" hidden>Show more</button>
  </div>
 </section>
 <section class="mapwrap" aria-label="Map. Visual companion: every place on the map is also in the list.">
  <button id="toggle" class="edge" type="button" aria-controls="side" aria-expanded="true">
   <svg class="i" viewBox="0 0 20 20" aria-hidden="true"><path d="M12.5 4.5 7 10l5.5 5.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
   <span class="vh" id="toggle-label">Hide list</span></button>
  <div id="map"></div>
  <details class="legend" id="legend"><summary>
   <svg class="i" viewBox="0 0 20 20" aria-hidden="true"><circle cx="5" cy="6" r="2" fill="currentColor"/><path d="M9 6h8M9 14h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="5" cy="14" r="2" fill="currentColor"/></svg>Legend</summary>
   <div class="legend-body" id="legend-body"></div></details>
 </section>
</main>
<script>
const DATA = __DATA__, RATINGS = __RATINGS__, HELP = __HELP__, ICONS = __ICONS__;
const PAGE = 30;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const svg = (layer, colour, size=20) => `<svg aria-hidden="true" width="${size}" height="${size}" viewBox="0 0 20 20" style="color:${colour}">${ICONS[layer][1]}</svg>`;
const badge = r => `<span class="rb"><i aria-hidden="true" style="background:${RATINGS[r][1]};color:${RATINGS[r][3]}">${RATINGS[r][2]}</i>${RATINGS[r][0]}</span>`;
document.getElementById('asof').textContent = Object.values(DATA)[0].generated;

// ---------- map ----------
const PHONE_EARLY = window.matchMedia('(max-width:720px)');
const map = L.map('map', {zoomControl:false, keyboard:true});
L.control.zoom({position:'topright'}).addTo(map);
L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:18, maxNativeZoom:16, attribution: PHONE_EARLY.matches
    ? 'Basemap: U.S. Geological Survey · Data: OpenStreetMap, Overture, venue sites'
    : 'Basemap: map services and data available from U.S. Geological Survey, National Geospatial Program | Data: OpenStreetMap (ODbL), Overture Maps, venue and agency websites, TrailLink, Census geocoder'}).addTo(map);
const cluster = L.markerClusterGroup({showCoverageOnHover:false, maxClusterRadius:45, disableClusteringAtZoom:15,
  iconCreateFunction: c => L.divIcon({html:`<div class="mc">${c.getChildCount()}</div>`, className:'', iconSize:[34,34]})}).addTo(map);
const trails = L.layerGroup().addTo(map);
function markerIcon(layer, r){
  const [_, col, sym, glyph] = RATINGS[r];
  return L.divIcon({className:'', iconSize:[30,30], iconAnchor:[15,15], popupAnchor:[0,-14],
    html:`<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="13" fill="${col}" stroke="#fff" stroke-width="2"/>
      <g transform="translate(5 4)" style="color:${glyph}">${ICONS[layer][1]}</g>
      <circle cx="24" cy="24" r="5.5" fill="#fff" stroke="#1b1f24" stroke-width="1"/>
      <text x="24" y="27" text-anchor="middle" font-size="8" font-weight="700" font-family="Arial,sans-serif" fill="#1b1f24">${sym}</text></svg>`});
}
// markers are mouse/touch only; keyboard and screen-reader users get the list (same content)
new MutationObserver(() => document.querySelectorAll('#map .leaflet-marker-icon:not([data-q])').forEach(e => {
  e.setAttribute('tabindex','-1'); e.setAttribute('aria-hidden','true'); e.dataset.q = 1; })).observe(document.getElementById('map'), {childList:true, subtree:true});

// ---------- items ----------
const ITEMS = [];
for (const region of Object.keys(DATA)) for (const f of DATA[region].features){
  const p = f.properties, i = ITEMS.length;
  const pts = p.layer === 'trail'
    ? (f.geometry.type === 'LineString' ? [f.geometry.coordinates] : (f.geometry.coordinates || [])).flat().map(c => [c[1], c[0]])
    : [[f.geometry.coordinates[1], f.geometry.coordinates[0]]];
  const leaf = p.layer === 'trail'
    ? L.geoJSON(f, {style:{color:RATINGS[p.access_rating][1], weight:5, opacity:.9}}).addTo(trails)
    : L.marker(pts[0], {icon:markerIcon(p.layer, p.access_rating), keyboard:false, title:p.name});
  if (p.layer !== 'trail') cluster.addLayer(leaf);
  leaf.bindPopup(() => `<h3>${esc(p.name)}</h3>${badge(p.access_rating)}<p>${esc(p.summary)}</p><button type="button" onclick="openCard(${i})">Details in the list</button>`, {maxWidth:320});
  ITEMS.push({i, p, pts, leaf, dist:null, dir:'', text:(p.name + ' ' + p.summary).toLowerCase()});
}
const VIEW = {cincinnati:[[39.10,-84.51],12], oxford:[[39.535,-84.755],13]};
if (PHONE_EARLY.matches) map.attributionControl.setPrefix(false);
// ---------- collapsible list (desktop/tablet) and bottom sheet (phone) ----------
const PHONE = window.matchMedia('(max-width:720px)');
const toggleBtn = document.getElementById('toggle'), sheetBtn = document.getElementById('sheet');
function setList(open){
  document.body.classList.toggle('list-closed', !open);
  toggleBtn.setAttribute('aria-expanded', open);
  document.getElementById('toggle-label').textContent = open ? 'Hide list' : 'Show list';
  toggleBtn.title = open ? 'Hide list' : 'Show list';
  try { localStorage.setItem('atlas-list-open', open ? '1' : '0'); } catch (e) {}
  setTimeout(() => map.invalidateSize(), 220);
}
function setSheet(open){
  document.body.classList.toggle('sheet-open', open);
  sheetBtn.setAttribute('aria-expanded', open);
  sheetBtn.querySelector('span span:last-child').textContent = open ? 'Hide list' : 'Show list';
}
toggleBtn.onclick = () => setList(document.body.classList.contains('list-closed'));
sheetBtn.onclick = () => setSheet(!document.body.classList.contains('sheet-open'));
document.querySelector('.skip').onclick = () => { PHONE.matches ? setSheet(true) : setList(true); };
let saved = null; try { saved = localStorage.getItem('atlas-list-open'); } catch (e) {}
if (saved === '0' && !PHONE.matches) setList(false);

map.setView(...VIEW[Object.keys(DATA)[0]]);

// ---------- filters ----------
const NEEDS = {
  'All places': () => true,
  'Accessible restrooms': it => it.p.layer === 'restroom' && ['accessible','partial'].includes(it.p.access_rating),
  'Any restroom': it => it.p.layer === 'restroom',
  'Museums & attractions': it => it.p.layer === 'culture',
  'Buildings & campus': it => it.p.layer === 'building',
  'Food & drink': it => it.p.layer === 'food_drink',
  'Shops & services': it => it.p.layer === 'service',
  'Parks & gardens': it => it.p.layer === 'park',
  'Trails': it => it.p.layer === 'trail',
  'Events': it => it.p.layer === 'event' || !!(it.p.events && it.p.events.length),
  'Adaptive recreation': it => it.p.layer === 'adaptive_recreation',
  'Lodging': it => it.p.layer === 'lodging',
};
const need = document.getElementById('need'), known = document.getElementById('known'), q = document.getElementById('q'), when = document.getElementById('when');
Object.keys(NEEDS).forEach(k => need.add(new Option(k, k)));
const RANK = {accessible:0, partial:1, not_accessible:2, unknown:3};
const LAYER_RANK = {culture:0, park:1, adaptive_recreation:2, lodging:3, building:4, food_drink:5, service:6, trail:7, event:8, restroom:9};
const TODAY = new Date().toISOString().slice(0, 10);
const addDays = n => new Date(Date.now() + n * 864e5).toISOString().slice(0, 10);
function windowEvents(it){
  const ev = it.p.events || [], d = +when.value;
  if (!d) return ev;
  const end = d === 1 ? TODAY : addDays(d);
  return ev.filter(e => e.start.slice(0, 10) >= TODAY && e.start.slice(0, 10) <= end);
}
const OLD = String(new Date().getFullYear() - 3);   // sources older than 3 years get a warning
let here = null, shown = PAGE, hereMarker = null;

function metres(a, b){ const R=6371000, r=Math.PI/180, dLa=(b[0]-a[0])*r, dLo=(b[1]-a[1])*r;
  const h=Math.sin(dLa/2)**2+Math.cos(a[0]*r)*Math.cos(b[0]*r)*Math.sin(dLo/2)**2; return 2*R*Math.asin(Math.sqrt(h)); }
function bearing(a, b){ const r=Math.PI/180, y=Math.sin((b[1]-a[1])*r)*Math.cos(b[0]*r),
  x=Math.cos(a[0]*r)*Math.sin(b[0]*r)-Math.sin(a[0]*r)*Math.cos(b[0]*r)*Math.cos((b[1]-a[1])*r);
  return ['north','northeast','east','southeast','south','southwest','west','northwest'][Math.round(((Math.atan2(y,x)/r)+360)%360/45)%8]; }
const fmt = m => m < 300 ? `${Math.round(m*3.28084/50)*50} feet` : `${(m/1609.34).toFixed(m < 16000 ? 1 : 0)} miles`;

function current(){
  const t = q.value.trim().toLowerCase();
  let list = ITEMS.filter(NEEDS[need.value]).filter(it => !known.checked || it.p.access_rating !== 'unknown')
                  .filter(it => !t || it.text.includes(t))
                  .filter(it => need.value !== 'Events' || windowEvents(it).length);
  if (here) list.sort((a, b) => a.dist - b.dist);
  else list.sort((a, b) => RANK[a.p.access_rating] - RANK[b.p.access_rating] || LAYER_RANK[a.p.layer] - LAYER_RANK[b.p.layer] || a.p.name.localeCompare(b.p.name));
  return list;
}
function directions(it){ const [la, lo] = here ? it.near : it.pts[0];
  return `https://www.google.com/maps/dir/?api=1&destination=${la},${lo}&travelmode=walking`; }
function details(it){
  const p = it.p; let h = '';
  if (p.facts && p.facts.length){
    h += `<table><caption class="vh">Accessibility facts for ${esc(p.name)}</caption><thead><tr><th scope="col">Feature</th><th scope="col">What the source says</th></tr></thead><tbody>`
      + p.facts.map(f => `<tr><th scope="row">${esc(f.attribute)}: ${esc(f.value)}</th><td>${esc(f.detail)}`
      + (f.quote ? `<div class="q">“${esc(f.quote.slice(0, 240))}”</div>` : '')
      + (f.source ? `<div><a href="${esc(f.source)}" target="_blank" rel="noopener">Source<span class="vh"> for ${esc(f.attribute)} (opens in a new tab)</span></a>${f.date ? ' · ' + esc(f.date) : ''}</div>` : '')
      + '</td></tr>').join('') + '</tbody></table>';
  }
  const evs = windowEvents(it);
  if (evs.length){
    h += `<p><strong>${evs.length} upcoming event${evs.length > 1 ? 's' : ''}</strong></p><ul>`
      + evs.slice(0, 10).map(e => `<li>${esc(e.start.replace('T', ' '))}: <a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>${e.accessible_tag ? ' (listed as accessible)' : ''}</li>`).join('') + '</ul>';
  }
  const c = p.contacts || {emails:[], phones:[]};
  if (c.emails.length || c.phones.length)
    h += '<p><strong>Ask before you go:</strong> ' + [...c.emails.map(e => `<a href="mailto:${esc(e)}">${esc(e)}</a>`), ...c.phones.map(t => `<a href="tel:${esc(t.replace(/\D/g,''))}">${esc(t)}</a>`)].join(' · ') + '</p>';
  const issue = 'https://github.com/zenaism/ohio-access-atlas/issues/new?title=' + encodeURIComponent('Report: ' + p.name)
    + '&body=' + encodeURIComponent(`Place: ${p.name}\nLink: ${placeUrl(it)}\n\nWhat is wrong or missing? (for example: ramp broken, restroom not accessible, new information)\n\n`);
  h += `<div class="links"><button type="button" class="ghost" data-a="copy">Copy link<span class="vh"> to ${esc(p.name)}</span></button>`
    + `<a class="btn ghost" href="${issue}" target="_blank" rel="noopener">Report a problem<span class="vh"> with ${esc(p.name)} (opens GitHub in a new tab)</span></a></div>`;
  return h || '<p>No further details yet.</p>';
}
function card(it){
  const p = it.p, li = document.createElement('li'); li.className = 'card'; li.id = 'card-' + it.i;
  const where = it.dist != null ? `<span>${fmt(it.dist)} ${it.dir}</span>` : '';
  const evs = windowEvents(it);
  const evline = p.events && p.layer !== 'event' && evs.length ? `<span>${evs.length} upcoming event${evs.length > 1 ? 's' : ''}</span>` : '';
  const old = p.newest_source && p.newest_source < OLD ? `<span class="old">Source from ${p.newest_source.slice(0, 4)}, may be out of date</span>` : '';
  li.innerHTML = `<h3 tabindex="-1">${esc(p.name)}</h3>
    <p class="meta">${badge(p.access_rating)}<span>${ICONS[p.layer][0]}</span>${where}${evline}${old}</p>
    <p class="sum">${esc(p.summary)}</p>
    <div class="actions">
      <button type="button" class="ghost" data-a="map">Show on map<span class="vh">: ${esc(p.name)}</span></button>
      <a class="btn ghost" href="${directions(it)}" target="_blank" rel="noopener">Directions<span class="vh"> to ${esc(p.name)} in Google Maps (opens in a new tab)</span></a>
      <button type="button" class="ghost" data-a="det" aria-expanded="false" aria-controls="det-${it.i}">Details<span class="vh">: ${esc(p.name)}</span></button>
    </div>
    <div class="det" id="det-${it.i}" hidden></div>`;
  li.querySelector('[data-a=map]').onclick = () => showOnMap(it);
  li.querySelector('[data-a=det]').onclick = e => toggle(it, e.currentTarget);
  return li;
}
function toggle(it, btn, force){
  const box = document.getElementById('det-' + it.i), open = force ?? btn.getAttribute('aria-expanded') !== 'true';
  btn.setAttribute('aria-expanded', open); box.hidden = !open;
  if (open && !box.innerHTML){ box.innerHTML = details(it); box.querySelector('[data-a=copy]').onclick = () => copyLink(it); }
}
function render(announce){
  const list = current(), ol = document.getElementById('list'); ol.innerHTML = '';
  list.slice(0, shown).forEach(it => ol.appendChild(card(it)));
  const more = document.getElementById('more'); more.hidden = list.length <= shown;
  more.textContent = `Show ${Math.min(PAGE, list.length - shown)} more of ${list.length - shown} remaining`;
  if (announce !== false){
    const t = q.value.trim();
    document.getElementById('sheet-label').textContent = `${list.length} place${list.length === 1 ? '' : 's'}`;
    document.getElementById('status').textContent = `${list.length} place${list.length === 1 ? '' : 's'}`
      + (t ? ` matching “${t}”` : '') + (here ? ', nearest first' : ', best documented first') + '.';
  }
}
function showOnMap(it){
  if (PHONE.matches) setSheet(false);
  if (it.p.layer === 'trail'){ map.fitBounds(it.leaf.getBounds(), {maxZoom:15}); it.leaf.openPopup(); return; }
  cluster.zoomToShowLayer(it.leaf, () => it.leaf.openPopup());
}
function openCard(i){
  map.closePopup();
  const it = ITEMS[i]; let idx = current().indexOf(it);
  if (idx < 0){ q.value = ''; need.value = 'All places'; known.checked = false; idx = current().indexOf(it); }
  if (idx >= shown){ shown = idx + 1; }
  render(false);
  const li = document.getElementById('card-' + i); toggle(it, li.querySelector('[data-a=det]'), true);
  if (PHONE.matches) setSheet(true); else setList(true);
  li.scrollIntoView({block:'start'}); li.querySelector('h3').focus();
}
[need, known, when].forEach(el => el.onchange = () => { when.hidden = need.value !== 'Events'; shown = PAGE; render(); });
q.oninput = () => { shown = PAGE; render(); };
document.getElementById('more').onclick = () => {
  const first = shown; shown += PAGE; render(false);
  const cards = document.querySelectorAll('#list .card'); if (cards[first]) cards[first].querySelector('h3').focus();
};
// ---------- share links ----------
function placeUrl(it){ return location.href.split('#')[0] + '#place=' + encodeURIComponent(it.p.link_id); }
function copyLink(it){
  const url = placeUrl(it), st = document.getElementById('status');
  (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject())
    .then(() => { st.textContent = `Link to ${it.p.name} copied.`; })
    .catch(() => { st.textContent = `Copy this link: ${url}`; });
}
function openFromHash(){
  const m = location.hash.match(/^#place=(.+)$/); if (!m) return;
  const it = ITEMS.find(x => x.p.link_id === decodeURIComponent(m[1])); if (!it) return;
  openCard(it.i); showOnMap(it);
}
window.addEventListener('hashchange', openFromHash);
// ---------- near me ----------
function setHere(latlng, note){
  here = latlng;
  ITEMS.forEach(it => { let best = Infinity, near = it.pts[0];
    for (const pt of it.pts){ const d = metres(here, pt); if (d < best){ best = d; near = pt; } }
    it.dist = best; it.near = near; it.dir = bearing(here, near); });
  if (hereMarker) map.removeLayer(hereMarker);
  if (!map.getPane('here')) map.createPane('here').style.zIndex = 650;
  hereMarker = L.circleMarker(here, {pane:'here', radius:9, color:'#fff', weight:3, fillColor:'#d6006f', fillOpacity:1})
    .addTo(map).bindTooltip('You are here', {permanent:true, direction:'right', offset:[10,0]});
  map.setView(here, Math.max(map.getZoom(), 14));
  shown = PAGE; render();
  if (PHONE.matches) setSheet(true); else setList(true);
  document.getElementById('status').textContent += ' ' + note + ' Distances are straight-line, not routes.';
}
document.getElementById('near').onclick = () => {
  const centre = () => { const c = map.getCenter(); setHere([c.lat, c.lng], 'Location not shared, so distances are from the centre of the map.'); };
  if (!navigator.geolocation) return centre();
  document.getElementById('status').textContent = 'Finding your location…';
  navigator.geolocation.getCurrentPosition(pos => setHere([pos.coords.latitude, pos.coords.longitude], 'Measured from your location.'),
    centre, {enableHighAccuracy:true, timeout:8000, maximumAge:60000});
};
// ---------- legend ----------
document.getElementById('legend-body').innerHTML = '<ul>'
  + Object.entries(RATINGS).map(([k, r]) => `<li>${badge(k)}<span>${HELP[k]}</span></li>`).join('') + '</ul><ul>'
  + Object.entries(ICONS).map(([k, [label]]) => `<li>${svg(k, '#374151', 18)}<span>${label}${k === 'trail' ? ' (coloured line)' : ''}</span></li>`).join('')
  + '<li><span class="mc" style="width:22px;height:22px;font-size:11px;box-shadow:none">5</span><span>Group of nearby places: zoom in</span></li></ul>';
render();
openFromHash();
</script></body></html>
"""


def render(data: dict, title: str = "Ohio Access Atlas", nav: str = "") -> str:
    """data = {region: FeatureCollection}; nav = extra HTML after the date (e.g. a link to the other city)."""
    return (
        TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__TITLE__", title)
        .replace("__NAV__", nav)
        .replace("__RATINGS__", json.dumps(RATINGS, ensure_ascii=False))
        .replace("__HELP__", json.dumps(RATING_HELP))
        .replace("__ICONS__", json.dumps(ICONS))
    )
