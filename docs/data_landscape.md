# Data landscape: every way to get wheelchair-accessibility data for Cincinnati + Oxford

Organised by **what a wheelchair user needs to know**, then by **how we can get it**.
Status: ✅ in pipeline · 🔜 next · 💡 later · ❌ not viable. Probed endpoints on 2026-11-07.

## 1. What information matters (the target schema)

| Need | Attributes | Why |
|---|---|---|
| Can I move along this path? | sidewalk present, surface, smoothness/cracks, running slope, cross slope, width, obstructions | ADA 403 accessible route |
| Can I get on/off the sidewalk? | curb ramp present, ramp condition, detectable warning, kerb height | Most common barrier |
| Can I cross? | crossing marked, signal, audible/accessible ped signal (APS), refuge island | Safety |
| Can I get in? | step-free entrance, door width, automatic door, ramp, elevator | ADA 404/206 |
| Can I use it? | accessible restroom, seating, counters, parking stalls | Destination usability |
| Can I get there by transit? | stop accessibility, boarding pad, shelter, paratransit area, real-time elevator/service alerts | Mobility |
| Is it passable *today*? | construction, snow/ice, temporary closures, reported hazards | Temporal |
| What is it like? | lived-experience text, reviews | Context the LLM needs |

## 2. Sources by acquisition method

### A. Open geodata (structured, high value, legal to use) ✅ first
| Source | Gives | Region | Status |
|---|---|---|---|
| OpenStreetMap (Overpass) | POI `wheelchair`, footway surface/incline/width, kerbs, crossings, steps, barriers, entrances | both | ✅ |
| CAGIS sidewalk assets (833k polygons) | sidewalk + **curb ramp polygons** (from 2024 aerials), detectable warnings (sparse) | Hamilton Co. | ✅ |
| CAGIS public steps | 160 city stairways (Cincinnati is hilly) | Cincinnati | ✅ |
| CAGIS traffic signals | signalised crossings | Cincinnati | ✅ |
| CAGIS elevation ImageServer (2 ft) | slope of every segment via `getSamples` | Hamilton Co. | 🔜 |
| USGS 3DEP 1 m DEM / Ohio OGRIP LiDAR | slope for Oxford; cross-slope from point clouds | both | 🔜 |
| ODOT TIMS + ADA curb-ramp inventory (state routes) | ramps on state highways (US-27 through Oxford) | both | 🔜 |
| Overture Maps places / Foursquare OS Places | complete POI list = denominator for coverage | both | 🔜 |
| Butler County / City of Oxford GIS | not found publicly; **request** sidewalk + ramp layers | Oxford | 🔜 email |

### B. Government operational data (real-world barrier reports)
| Source | Gives | Status |
|---|---|---|
| Cincinnati 311 (`gcej-gmiw`, 2.29 M requests since 2000) | hazardous sidewalk, obstructions, curb repair, "ACCESSIBILITY", APS repair, accessible parking signs, icy streets, with dates and status | ✅ |
| Cincinnati building permits (`uhjb-xac9`) | renovations (ADA upgrades are triggered by alterations) | 💡 |
| Right-of-way / construction permits (CAGIS `Construction_Coordination`) | temporary sidewalk closures | 💡 |
| ADA transition plans (City of Cincinnati, Oxford, ODOT, Miami) - PDFs | barrier inventories, planned fixes | 🔜 PDF to LLM extraction |
| DOJ ADA settlements (ADA.gov, Project Civic Access) | documented violations | 💡 |
| Census ACS S1810 / CDC Disability & Health | disability prevalence by tract (who is affected, equity analysis) | 🔜 |

### C. Transit
| Source | Gives | Status |
|---|---|---|
| Metro GTFS (Mobility DB mdb-307) | `wheelchair_boarding` (96% coded 2: verify meaning with SORTA) | ✅ |
| Metro GTFS-RT alerts (mdb-1490) | detours, stop closures, live | 🔜 poll + archive |
| BCRTA GTFS (mdb-240) | Oxford stops; stale (2019), no accessibility field | ✅ stale, request new |
| TANK GTFS (N. Kentucky) | cross-river trips | 💡 |
| Cincinnati Connector streetcar | level boarding (in Metro feed?) | 💡 check |
| Access (Metro paratransit), BCARE (BCRTA) | service areas, eligibility | 💡 manual |

### D. Business / venue accessibility (entrances, restrooms)
| Source | Gives | Terms |
|---|---|---|
| Google Places API `accessibilityOptions` | entrance, restroom, parking, seating | ⚠️ can't store long-term; use as **evaluation** comparison only, keep place_id |
| Yelp Fusion attributes | "wheelchair accessible" | ⚠️ restrictive |
| Wheelmap / accessibility.cloud | aggregated OSM + partner data | 💡 API key |
| Venue websites (Cincinnati Zoo, Paycor, GABP, TQL, Museum Center, CVG, Union Terminal Amtrak, Miami's Millett/Armstrong) | detailed access guides | 🔜 per-POI web search, then LLM extraction into the schema |
| Visitor bureaus (Cincinnati USA, Enjoy Oxford) | listings | 💡 |
| NPS API (W. H. Taft NHS) | structured accessibility fields | 💡 |
| Parks: Cincinnati Parks, Great Parks (ArcGIS trails), Hueston Woods SP (ODNR) | accessible trails, surfaces | 🔜 |

### E. Universities (Oxford is mostly Miami)
| Source | Gives |
|---|---|
| Miami University: campus map accessibility layer, Student Disability Services, Facilities GIS | accessible entrances, elevators, routes on campus. **Ask your department/advisor for an internal contact.** |
| Miami "Oxford Sidewalk App" (ArcGIS, 20 condition points) | prior student audit; contact owner |
| UC / Xavier accessibility maps | Cincinnati campuses |

### F. Text / lived experience
| Source | Notes |
|---|---|
| Reddit (local + disability subs) ✅ | anonymised; IDs only for release |
| Google/Yelp reviews mentioning wheelchair | ⚠️ terms; snippets via API only |
| Local news (Enquirer, WCPO, Cincinnati Business Courier) on sidewalks/ADA | 💡 article-level metadata + quotes |
| City council / Oxford council minutes (sidewalk complaints) | 💡 public records |
| YouTube wheelchair vlogs in Cincinnati | 💡 transcripts |
| Facebook groups, Nextdoor | ❌ no API, privacy |

### G. Imagery and sensing (strongest novelty for a paper)
| Method | Gives |
|---|---|
| Mapillary (CC-BY-SA) images + object detections | curb cuts, crosswalks, signals; street-level verification |
| Aerial ortho (OGRIP 6 in, CAGIS 2024) + **Tile2Net** | sidewalk network where none is mapped (Oxford) |
| Google Street View | ⚠️ ToS; manual audits only (like Project Sidewalk) |
| **Wheelchair-mounted IMU / phone** (your lab's sensing work fits here) | surface roughness, vibration, slope measured by actual rides |
| LiDAR point clouds | cross-slope, curb height |

### H. Primary collection (ground truth, required for evaluation)
| Method | Notes |
|---|---|
| Field audit of a stratified sample (~200 segments/ramps/entrances) | Kobo/ArcGIS Survey123 form matching our schema; inter-rater agreement |
| Project Sidewalk deployment for Oxford | contact UW Makeability Lab; crowdsourced labels from Street View |
| StreetComplete / MapRoulette campaign | students add kerb/surface tags **to OSM** (open contribution back) |
| Interviews / survey with wheelchair users (SDS, local orgs) | needs, validation of the model. **Needs IRB.** |

## 3. Priorities

1. **Done:** OSM, CAGIS ramps/steps/sidewalks/signals, 311, GTFS.
2. **Next 2 weeks:** slopes (CAGIS elevation + 3DEP), GTFS-RT archiving, ACS tracts, ADA transition plan PDFs, Overture POIs.
3. **Then:** per-POI web extraction (LLM to schema, with a human-validated sample), Mapillary.
4. **In parallel (long lead time):** IRB, field audit protocol, emails to BCRTA, City of Oxford, Miami SDS/Facilities, SORTA, CAGIS.

## 4. Rules for every new source
- Add it to `config/sources.yaml` (generic connectors: `arcgis`, `socrata`, `gtfs`, `overpass`).
- Record license and retrieval date; the raw response is cached in `data/raw/`.
- Never store what the terms forbid (Google content, Reddit usernames).
- Note what the source **cannot** tell us (e.g. CAGIS ramps have location, not condition).
