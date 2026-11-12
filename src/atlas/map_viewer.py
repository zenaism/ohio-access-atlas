# ruff: noqa: E501  (embedded HTML/JS template)
"""Self-contained HTML viewer for the atlas GeoJSON (Leaflet from a CDN; data embedded).

Shape (pictogram) = layer, colour = access rating. Colours are the Okabe-Ito palette, which stays
distinguishable for the common forms of colour blindness; the legend names every icon and colour.
"""

from __future__ import annotations

import json

RATINGS = {  # value -> (label, colour)
    "accessible": ("Accessible (step-free entry and accessible restroom, or paved trail)", "#0072B2"),
    "partial": ("Partly accessible / some access features", "#E69F00"),
    "not_accessible": ("Not accessible", "#D55E00"),
    "unknown": ("No accessibility information yet", "#8C8C8C"),
}

# 20x20 white pictograms drawn on a coloured disc
ICONS = {
    "culture": (
        "Museums, venues & attractions",
        '<path d="M10 3 17 7H3z" fill="#fff"/><path d="M5 8v6M8.3 8v6M11.7 8v6M15 8v6" stroke="#fff" '
        'stroke-width="1.6"/><path d="M3 15.5h14" stroke="#fff" stroke-width="1.8"/>',
    ),
    "park": (
        "Parks & gardens",
        '<circle cx="10" cy="8" r="5" fill="#fff"/><path d="M10 11v6" stroke="#fff" stroke-width="2"/>',
    ),
    "restroom": (
        "Public restrooms",
        '<text x="10" y="14" text-anchor="middle" font-size="9" font-weight="700" '
        'font-family="Arial,sans-serif" fill="#fff">WC</text>',
    ),
    "adaptive_recreation": (
        "Adaptive recreation (all-terrain chairs, accessible launches)",
        '<circle cx="11" cy="4" r="1.8" fill="#fff"/><path d="M10.5 6.5v5h4l2 4" '
        'stroke="#fff" stroke-width="1.7" fill="none"/><circle cx="8.5" cy="13" r="4" '
        'stroke="#fff" stroke-width="1.7" fill="none"/>',
    ),
    "lodging": (
        "Accessible lodging",
        '<path d="M3 15V6M3 12h14v3M17 15v-3" stroke="#fff" stroke-width="1.8" fill="none"/>'
        '<circle cx="6.5" cy="9.5" r="1.6" fill="#fff"/><path d="M9 11V8.5h6.5a1.5 1.5 0 0 1 1.5 1.5v1" '
        'fill="#fff"/>',
    ),
    "event": (
        "Upcoming events (grouped by venue)",
        '<rect x="3.5" y="5" width="13" height="11" rx="1.5" stroke="#fff" stroke-width="1.7" fill="none"/>'
        '<path d="M3.5 8.5h13M7 3v3.5M13 3v3.5" stroke="#fff" stroke-width="1.7"/>',
    ),
    "trail": ("Trails (line colour = surface rating)", None),
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Ohio Access Atlas map</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 .leaflet-tile-pane{filter:grayscale(.85) brightness(1.06) contrast(.9)}  /* calm basemap so markers stand out */
 html,body,#map{height:100%;margin:0;font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif}
 .bar{position:absolute;top:10px;left:56px;z-index:1000;background:#fff;padding:6px 8px;border-radius:6px;
      box-shadow:0 1px 4px rgba(0,0,0,.3);font-size:13px}
 .bar button{margin-right:4px;padding:4px 10px;border:1px solid #bbb;border-radius:4px;background:#f6f6f6;cursor:pointer}
 .legend{background:#fff;padding:10px 12px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.3);font-size:12.5px;
         line-height:1.35;max-width:300px}
 .legend h4{margin:2px 0 6px;font-size:13px}
 .legend label{display:flex;align-items:center;gap:7px;margin:3px 0;cursor:pointer}
 .legend .sw{display:inline-block;width:14px;height:14px;border-radius:50%;flex:none}
 .legend .ln{display:inline-block;width:22px;height:4px;border-radius:2px;flex:none}
 .legend .note{color:#555;margin-top:6px;font-size:11.5px}
 .pop{max-height:360px;overflow-y:auto;padding-right:4px} .pop h3{margin:0 0 4px;font-size:15px} .pop .rt{display:inline-block;padding:1px 7px;border-radius:9px;color:#fff;font-size:11.5px}
 .pop table{border-collapse:collapse;margin-top:6px;font-size:12px} .pop td{border-top:1px solid #eee;padding:3px 4px;vertical-align:top}
 .pop .q{color:#555;font-style:italic} .pop ul{padding-left:16px;margin:4px 0;font-size:12px}
</style></head><body>
<div id="map"></div>
<div class="bar"><button onclick="go('cincinnati')">Cincinnati</button><button onclick="go('oxford')">Oxford</button>
 <span id="count"></span></div>
<script>
const DATA = __DATA__, RATINGS = __RATINGS__, ICONS = __ICONS__;
const map = L.map('map', {zoomControl:true});
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19,
  attribution:'Map tiles &copy; OpenStreetMap contributors. Data: OpenStreetMap (ODbL), Overture Maps, venue and agency websites, TrailLink, Census geocoder. Built by the Ohio Access Atlas project.'}).addTo(map);
const groups = {}; Object.keys(ICONS).forEach(k => groups[k] = L.layerGroup().addTo(map));
function icon(layer, rating){
  const c = RATINGS[rating][1], g = ICONS[layer][1];
  return L.divIcon({className:'', iconSize:[26,26], iconAnchor:[13,13], popupAnchor:[0,-12],
    html:`<svg width="26" height="26" viewBox="0 0 26 26"><circle cx="13" cy="13" r="12" fill="${c}" stroke="#fff" stroke-width="1.5"/><g transform="translate(3 3)">${g}</g></svg>`});
}
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function popup(p){
  const r = RATINGS[p.access_rating];
  let h = `<div class="pop"><h3>${esc(p.name)}</h3><span class="rt" style="background:${r[1]}">${esc(r[0])}</span>`;
  if (p.facts && p.facts.length){
    h += '<table>' + p.facts.map(f => `<tr><td><b>${esc(f.attribute)}</b><br>${esc(f.value)}</td><td>${esc(f.detail)}`
      + (f.quote ? `<div class="q">“${esc(f.quote.slice(0,220))}”</div>` : '')
      + (f.source ? `<div><a href="${esc(f.source)}" target="_blank">source</a>${f.date ? ' · ' + esc(f.date) : ''}</div>` : '')
      + '</td></tr>').join('') + '</table>';
  }
  if (p.events){
    h += `<div><b>${p.event_count} upcoming event(s)</b>${p.disability_focused ? ' · includes disability-focused' : ''}</div><ul>`
      + p.events.slice(0,12).map(e => `<li>${esc(e.start.replace('T',' '))} · <a href="${esc(e.url)}" target="_blank">${esc(e.title)}</a>${e.accessible_tag ? ' (tagged accessible)' : ''}</li>`).join('')
      + (p.events.length > 12 ? `<li>… ${p.event_count - 12} more</li>` : '') + '</ul>';
  }
  return h + `<div class="q" style="margin-top:4px">matched to: ${esc(p.matched_to)}</div></div>`;
}
let n = 0;
for (const region of Object.keys(DATA)){
  for (const f of DATA[region].features){
    const p = f.properties; n++;
    const layer = p.layer === 'trail'
      ? L.geoJSON(f, {style:{color:RATINGS[p.access_rating][1], weight:4, opacity:.9}})
      : L.marker([f.geometry.coordinates[1], f.geometry.coordinates[0]], {icon:icon(p.layer, p.access_rating), title:p.name});
    layer.bindPopup(popup(p), {maxWidth:380}); groups[p.layer].addLayer(layer);
  }
}
document.getElementById('count').textContent = ` ${n} features · generated ${DATA.cincinnati.generated}`;
const legend = L.control({position:'bottomright'});
legend.onAdd = () => {
  const d = L.DomUtil.create('div','legend'); L.DomEvent.disableClickPropagation(d);
  let h = '<h4>What the icons mean</h4>';
  for (const [k,[label,g]] of Object.entries(ICONS)){
    const sym = g ? `<svg width="22" height="22" viewBox="0 0 26 26"><circle cx="13" cy="13" r="12" fill="#444"/><g transform="translate(3 3)">${g}</g></svg>`
                  : '<span class="ln" style="background:#444"></span>';
    h += `<label><input type="checkbox" checked data-k="${k}">${sym}<span>${label}</span></label>`;
  }
  h += '<h4 style="margin-top:8px">What the colours mean</h4>';
  for (const [k,[label,c]] of Object.entries(RATINGS)) h += `<label style="cursor:default"><span class="sw" style="background:${c}"></span>${label}</label>`;
  h += '<div class="note">Untick a layer to hide it. Click any icon for the facts, the quoted source text and its date. Grey means we have no information, not that the place is inaccessible.</div>';
  d.innerHTML = h;
  d.querySelectorAll('input').forEach(i => i.onchange = () => i.checked ? map.addLayer(groups[i.dataset.k]) : map.removeLayer(groups[i.dataset.k]));
  return d;
};
legend.addTo(map);
const VIEW = {cincinnati:[[39.10,-84.51],12], oxford:[[39.535,-84.755],13]};
function go(r){ map.setView(VIEW[r][0], VIEW[r][1]); }
go('cincinnati');
</script></body></html>
"""


def render(data: dict) -> str:
    return (
        TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__RATINGS__", json.dumps(RATINGS))
        .replace("__ICONS__", json.dumps(ICONS))
    )
