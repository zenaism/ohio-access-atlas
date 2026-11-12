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
    "trail": ("Trail", '<path d="M3 16c3-2 3-6 7-7s4-4 7-6" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round"/>'),
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>__TITLE__ · Ohio Access Atlas</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Wheelchair accessibility of places, restrooms, trails and events, with sources.">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
 :root{--ink:#1b1f24;--muted:#555d66;--line:#e3e6ea;--bg:#f5f6f8;--navy:#14213d;--focus:#ffbf47}
 *{box-sizing:border-box} html,body{height:100%;margin:0}
 body{font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg);display:flex;flex-direction:column}
 a{color:#0b5cad} :focus-visible{outline:3px solid var(--focus);outline-offset:2px}
 .vh{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
 .skip{position:absolute;left:8px;top:-60px;background:#fff;padding:8px 12px;border-radius:6px;z-index:3000;font-weight:600}
 .skip:focus{top:8px}
 header{background:var(--navy);color:#fff;padding:12px 18px;display:flex;flex-wrap:wrap;gap:10px 24px;align-items:center;justify-content:space-between}
 header h1{font-size:20px;margin:0;letter-spacing:.2px} header .sub{margin:2px 0 0;font-size:13px;color:#c9d2e3} header .sub a{color:#fff}
 .tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
 .tools input{width:min(320px,70vw);padding:9px 12px;border-radius:8px;border:0;font-size:15px}
 button,.btn{font:inherit;font-size:14px;padding:8px 12px;border-radius:8px;border:1px solid #c4cad2;background:#fff;color:var(--ink);cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px}
 button:hover,.btn:hover{background:#eef2f7} .primary{background:#ffbf47;border-color:#ffbf47;font-weight:600}
 main{flex:1;display:grid;grid-template-columns:minmax(330px,420px) 1fr;min-height:0}
 .side{overflow-y:auto;background:var(--bg);border-right:1px solid var(--line);padding:14px}
 .filters{display:grid;gap:8px;margin-bottom:10px} .filters select{font:inherit;padding:7px 8px;border-radius:8px;border:1px solid #c4cad2;width:100%}
 .filters label.cb{display:flex;gap:8px;align-items:center;font-size:14px}
 #status{font-size:13px;color:var(--muted);margin:2px 0 6px;min-height:1.2em}
 ol#list{list-style:none;margin:0;padding:0;display:grid;gap:10px}
 .card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
 .card .top{display:flex;gap:10px;align-items:flex-start}
 .card h3{font-size:16px;margin:0 0 2px;line-height:1.25} .card h3:focus{outline:3px solid var(--focus)}
 .meta{font-size:13px;color:var(--muted);margin:0;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center}
 .badge{display:inline-flex;gap:4px;align-items:center;font-weight:600;font-size:12.5px;border-radius:999px;padding:1px 9px}
 .sum{margin:8px 0;font-size:14px}
 .actions{display:flex;gap:6px;flex-wrap:wrap}
 .det{margin-top:10px;border-top:1px solid var(--line);padding-top:8px;font-size:13.5px}
 .det table{border-collapse:collapse;width:100%} .det th,.det td{text-align:left;vertical-align:top;padding:5px 4px;border-bottom:1px solid #eef0f2}
 .det th{width:34%;font-weight:600} .q{color:var(--muted);font-style:italic} .det ul{margin:4px 0;padding-left:18px}
 #more{width:100%;justify-content:center;margin-top:10px}
 .mapwrap{position:relative;min-height:0} #map{position:absolute;inset:0}
 .leaflet-tile-pane{filter:grayscale(.75) brightness(1.05) contrast(.92)}
 .legend{position:absolute;right:12px;bottom:26px;z-index:1000;background:#fff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.18);padding:10px 14px;font-size:13px;max-width:340px}
 .legend summary{font-weight:700;cursor:pointer} .legend ul{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:5px}
 .legend li{display:flex;gap:8px;align-items:center} .legend .badge{white-space:nowrap;flex:none}
 .leaflet-control-attribution{font-size:10.5px}
 .mc{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;background:#fff;border:2px solid #1b1f24;font-weight:700;color:#1b1f24;box-shadow:0 0 0 5px rgba(27,31,36,.12)}
 .leaflet-popup-content{margin:12px 14px;font-size:14px} .leaflet-popup-content h3{margin:0 0 4px;font-size:15px}
 @media (max-width:860px){ main{grid-template-columns:1fr;grid-template-rows:48vh auto} .mapwrap{order:-1;min-height:48vh}
   .side{border-right:0;overflow:visible} .legend{max-width:220px} .legend:not([open]){padding:8px 12px} }
</style></head><body>
<a class="skip" href="#list-h">Skip to the list of places</a>
<header>
 <div><h1>__TITLE__</h1><p class="sub">Wheelchair accessibility, with sources · data as of <span id="asof"></span>__NAV__</p></div>
 <div class="tools" role="search">
  <label for="q" class="vh">Search places, trails and venues</label>
  <input id="q" type="search" placeholder="Search places, trails, venues" autocomplete="off">
  <button id="near" class="primary" type="button">Near me</button>
 </div>
</header>
<main>
 <section class="side" aria-labelledby="list-h">
  <h2 id="list-h" tabindex="-1" class="vh">Places</h2>
  <div class="filters">
   <label for="need">Show</label>
   <select id="need"></select>
   <label class="cb"><input type="checkbox" id="known"> Only places with accessibility information</label>
  </div>
  <p id="status" role="status" aria-live="polite"></p>
  <ol id="list"></ol>
  <button id="more" type="button" hidden>Show more</button>
 </section>
 <section class="mapwrap" aria-label="Map. Visual companion: every place on the map is also in the list.">
  <div id="map"></div>
  <details class="legend" id="legend" open><summary>Legend</summary><div id="legend-body"></div></details>
 </section>
</main>
<script>
const DATA = __DATA__, RATINGS = __RATINGS__, HELP = __HELP__, ICONS = __ICONS__;
const PAGE = 30;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const svg = (layer, colour, size=20) => `<svg aria-hidden="true" width="${size}" height="${size}" viewBox="0 0 20 20" style="color:${colour}">${ICONS[layer][1]}</svg>`;
const badge = r => `<span class="badge" style="background:${RATINGS[r][1]};color:${RATINGS[r][3]}"><span aria-hidden="true">${RATINGS[r][2]}</span>${RATINGS[r][0]}</span>`;
document.getElementById('asof').textContent = Object.values(DATA)[0].generated;
if (window.matchMedia('(max-width:860px)').matches) document.getElementById('legend').open = false;

// ---------- map ----------
const map = L.map('map', {zoomControl:true, keyboard:true});
L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:18, maxNativeZoom:16, attribution:'Basemap: map services and data available from U.S. Geological Survey, National Geospatial Program | Data: OpenStreetMap (ODbL), Overture Maps, venue and agency websites, TrailLink, Census geocoder'}).addTo(map);
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
map.setView(...VIEW[Object.keys(DATA)[0]]);

// ---------- filters ----------
const NEEDS = {
  'All places': () => true,
  'Accessible restrooms': it => it.p.layer === 'restroom' && ['accessible','partial'].includes(it.p.access_rating),
  'Any restroom': it => it.p.layer === 'restroom',
  'Museums & attractions': it => it.p.layer === 'culture',
  'Parks & gardens': it => it.p.layer === 'park',
  'Trails': it => it.p.layer === 'trail',
  'Events': it => it.p.layer === 'event',
  'Adaptive recreation': it => it.p.layer === 'adaptive_recreation',
  'Lodging': it => it.p.layer === 'lodging',
};
const need = document.getElementById('need'), known = document.getElementById('known'), q = document.getElementById('q');
Object.keys(NEEDS).forEach(k => need.add(new Option(k, k)));
const RANK = {accessible:0, partial:1, not_accessible:2, unknown:3};
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
                  .filter(it => !t || it.text.includes(t));
  if (here) list.sort((a, b) => a.dist - b.dist);
  else list.sort((a, b) => RANK[a.p.access_rating] - RANK[b.p.access_rating] || a.p.name.localeCompare(b.p.name));
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
  if (p.events && p.events.length){
    h += `<p><strong>${p.event_count} upcoming event${p.event_count > 1 ? 's' : ''}</strong></p><ul>`
      + p.events.slice(0, 10).map(e => `<li>${esc(e.start.replace('T', ' '))}: <a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>${e.accessible_tag ? ' (listed as accessible)' : ''}</li>`).join('') + '</ul>';
  }
  const c = p.contacts || {emails:[], phones:[]};
  if (c.emails.length || c.phones.length)
    h += '<p><strong>Ask before you go:</strong> ' + [...c.emails.map(e => `<a href="mailto:${esc(e)}">${esc(e)}</a>`), ...c.phones.map(t => `<a href="tel:${esc(t.replace(/\D/g,''))}">${esc(t)}</a>`)].join(' · ') + '</p>';
  return h || '<p>No further details yet.</p>';
}
function card(it){
  const p = it.p, li = document.createElement('li'); li.className = 'card'; li.id = 'card-' + it.i;
  const where = it.dist != null ? `<span>${fmt(it.dist)} ${it.dir}</span>` : '';
  li.innerHTML = `<div class="top">${svg(p.layer, '#14213d', 22)}<div>
      <h3 tabindex="-1">${esc(p.name)}</h3>
      <p class="meta"><span>${ICONS[p.layer][0]}</span>${badge(p.access_rating)}${where}</p></div></div>
    <p class="sum">${esc(p.summary)}</p>
    <div class="actions">
      <button type="button" data-a="map">Show on map<span class="vh">: ${esc(p.name)}</span></button>
      <a class="btn" href="${directions(it)}" target="_blank" rel="noopener">Directions<span class="vh"> to ${esc(p.name)} in Google Maps (opens in a new tab)</span></a>
      <button type="button" data-a="det" aria-expanded="false" aria-controls="det-${it.i}">Details<span class="vh">: ${esc(p.name)}</span></button>
    </div>
    <div class="det" id="det-${it.i}" hidden></div>`;
  li.querySelector('[data-a=map]').onclick = () => showOnMap(it);
  li.querySelector('[data-a=det]').onclick = e => toggle(it, e.currentTarget);
  return li;
}
function toggle(it, btn, force){
  const box = document.getElementById('det-' + it.i), open = force ?? btn.getAttribute('aria-expanded') !== 'true';
  btn.setAttribute('aria-expanded', open); box.hidden = !open; if (open && !box.innerHTML) box.innerHTML = details(it);
}
function render(announce){
  const list = current(), ol = document.getElementById('list'); ol.innerHTML = '';
  list.slice(0, shown).forEach(it => ol.appendChild(card(it)));
  const more = document.getElementById('more'); more.hidden = list.length <= shown;
  more.textContent = `Show ${Math.min(PAGE, list.length - shown)} more of ${list.length - shown} remaining`;
  if (announce !== false){
    const t = q.value.trim();
    document.getElementById('status').textContent = `${list.length} place${list.length === 1 ? '' : 's'}`
      + (t ? ` matching “${t}”` : '') + (here ? ', nearest first' : ', best documented first') + '.';
  }
}
function showOnMap(it){
  if (window.matchMedia('(max-width:860px)').matches) document.getElementById('map').scrollIntoView({behavior:'smooth'});
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
  li.scrollIntoView({block:'start'}); li.querySelector('h3').focus();
}
[need, known].forEach(el => el.onchange = () => { shown = PAGE; render(); });
q.oninput = () => { shown = PAGE; render(); };
document.getElementById('more').onclick = () => {
  const first = shown; shown += PAGE; render(false);
  const cards = document.querySelectorAll('#list .card'); if (cards[first]) cards[first].querySelector('h3').focus();
};
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
  + Object.entries(ICONS).map(([k, [label]]) => `<li>${svg(k, '#14213d', 18)}<span>${label}${k === 'trail' ? ' (coloured line)' : ''}</span></li>`).join('')
  + '<li><span class="mc" style="width:22px;height:22px;font-size:11px;box-shadow:none">5</span><span>Group of nearby places: zoom in</span></li></ul>';
render();
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
