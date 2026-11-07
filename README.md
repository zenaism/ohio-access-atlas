<div align="center">

# Ohio Access Atlas

**A multi-source, provenance-tracked map of wheelchair accessibility for Cincinnati and Oxford, Ohio**

[**Quick start**](#quick-start) · [**A look at the data**](#a-look-at-the-data) · [**What's inside**](#whats-inside) · [**Data format**](#data-format) · [**First findings**](#first-findings) · [**Project layout**](#project-layout) · [**Sources**](SOURCES.md)

![Licence: to be decided](https://img.shields.io/badge/licence-TBD-lightgrey) ![Data: mixed licences](https://img.shields.io/badge/data-ODbL%20%2B%20public%20sources-lightgrey) ![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-lightgrey) ![Status: research](https://img.shields.io/badge/status-research-lightgrey)

<img src="docs/figures/slope_walk.gif" width="95%" alt="Animation: a dot climbs Warner Street in Cincinnati while its elevation profile and 10 m grades build up against the ADA walkway and ramp limits"/>

<sub>One real street, one real terrain model. A dot climbs Warner Street, Cincinnati, sampling the USGS 1 m elevation model every 10 m. <b>Top:</b> the elevation profile. <b>Bottom:</b> the grade of each 10 m stretch against the ADA limits for walkways (5%) and ramps (8.33%). The atlas does this for every one of 23,934 path segments in both cities.</sub>

| **355k** observations | **12** configured sources | **2** cities | **24,639** accessibility 311 reports | **14,970** city curb ramps | **23,934** path segments with slope |
|:-:|:-:|:-:|:-:|:-:|:-:|

</div>

## Why

- **Open maps miss what wheelchair users need.** Only about 4% of Cincinnati's curb ramps appear in OpenStreetMap, and fewer than 2% of mapped places carry a `wheelchair` tag.
- **No single source is enough.** City GIS has ramp locations but no condition; 311 has problems but only where people complain; OSM has routes but few attributes. The atlas puts all of them in one schema so they can be compared and combined.
- **Every fact is traceable.** Each row records its source, URL, retrieval date and licence, and every raw response is cached, so any table can be rebuilt and audited.
- **It is the data layer for an assistant.** The atlas grounds a small language model that answers wheelchair users' questions and says "I don't know" when the data is missing.

## A look at the data

<img src="docs/figures/atlas_overview.png" width="100%" alt="Three maps of Cincinnati: city curb ramps versus OpenStreetMap kerbs, path slope classes, and density of 311 accessibility complaints"/>

<sub><b>Left:</b> the city's curb-ramp inventory (blue) against the kerbs mapped in OpenStreetMap (orange). <b>Middle:</b> the steepest 10 m stretch of every path segment. <b>Right:</b> where residents report sidewalk, curb, ramp and signal problems.</sub>

<table>
<tr>
<td width="50%"><img src="docs/figures/ramps_vs_osm.gif" alt="Animation: one 1.4 km square of Cincinnati, first showing the few OpenStreetMap kerbs, then the 747 city curb ramps fading in"/></td>
<td width="50%"><img src="docs/figures/reports_timelapse.gif" alt="Animation: 311 accessibility complaints in Cincinnati appearing year by year from 2004 to 2026, with a bar chart of reports per year"/></td>
</tr>
<tr>
<td><sub><b>What a router knows vs. what exists.</b> In this square OpenStreetMap has a handful of kerbs; the city's inventory has 747 curb ramps.</sub></td>
<td><sub><b>22 years of complaints.</b> 24,639 sidewalk, curb, ramp, parking and signal requests. Volume quadruples from 2025.</sub></td>
</tr>
</table>

## What's inside

| Layer | Source | Cincinnati | Oxford |
|---|---|--:|--:|
| Places, footways, kerbs, crossings, steps, barriers | OpenStreetMap (Overpass) | 27,796 | 3,894 |
| Path slope (steepest 10 m stretch, end-to-end grade) | USGS 3DEP 1 m DEM, sampled locally | 40,124 | 7,744 |
| Curb ramps (polygons from 2024 aerials) | CAGIS sidewalk assets | 14,970 | – |
| Sidewalk and walkway polygons | CAGIS sidewalk assets | 220,792 | – |
| Public stairways | CAGIS | 160 | – |
| Traffic signals | CAGIS | 5,324 | – |
| Accessibility 311 requests, 2004–2026 | Open Data Cincy (`gcej-gmiw`) | 24,639 | – |
| Transit stops, `wheelchair_boarding` | Metro / BCRTA GTFS | 2,320 | 61 |
| Lived-experience posts (needs API keys) | Reddit | – | – |

Every source is an entry in [`config/sources.yaml`](config/sources.yaml). Any new ArcGIS layer or Socrata dataset is a few lines of config, no code. Regions are pinned to OpenStreetMap boundary relations (Cincinnati `R183453`, Oxford `R182574`), never matched by name.

## Quick start

```bash
make setup     # venv + install
make data      # fetch every no-credential source for both cities (~30 min, cached after)
make dem       # download USGS 1 m DEM tiles (3.4 GB) and compute slope per path segment
make report    # coverage tables -> data/processed/<region>/report.md
make equity    # RQ1 analysis   -> data/processed/cincinnati/equity_report.md
make figure    # this README's figure and animations
make test

.venv/bin/atlas sources                              # list configured sources
.venv/bin/atlas fetch cincy_311 --region cincinnati  # refresh one source
```

## Data format

Every source is reduced to one long table: **one row = one claim about one attribute of one place**.

| Column | Example |
|---|---|
| `entity_id` | `cagis_curb_ramps:48213`, `osm:way/706070710` |
| `entity_type` | `curb_ramp`, `path_segment`, `poi`, `transit_stop`, `reported_issue` |
| `attribute`, `value` | `incline_max_dem` = `7.4%` |
| `signal` | `supports` · `limited` · `barrier` · `unknown` |
| `source`, `source_ref` | `slope_3dep_local`, link back to the record |
| `observed_at`, `retrieved_at` | when the source recorded it, when we fetched it |
| `license`, `region`, `lat`, `lon` | |

`signal` comes from transparent ADA-based rules in [`signals.py`](src/atlas/signals.py): running slope ≤ 5% for walkways and ≤ 8.33% for ramps (ADA 403.3, 405.2), clear width ≥ 0.915 m (ADA 403.5). Full native records are kept beside the observations as GeoParquet.

## First findings

| Finding | Number |
|---|---|
| City curb ramps with an OSM kerb within 10 m | **4.1%** (3.7% at 5 m, 4.7% at 20 m) |
| Path segments with a stretch steeper than 8.33% | **17.4%** Cincinnati, 5.3% Oxford |
| DEM slope vs. slope mapped in OSM (Oxford, 396 segments) | same side of 5% in **89%** |
| Hazardous-sidewalk 311 reports per resident, per +$10k median income | **+10%** (rate ratio 1.10, 95% CI 1.05–1.15) |
| … per +10 points Black residents | **−8%** (0.92, 0.87–0.98) |
| 311 closing time by tract income, race, disability or slope | no difference (all hazard ratios 0.98–1.00, n.s.) |
| Curb ramps per road km, per +1% average slope | **−6%** (0.94, 0.91–0.96) |

| How fast an open problem gets repeat reports (Liu et al. 2023 method, 954 repeats) | no difference by income, race, disability or slope |
| Hazardous-sidewalk problems per resident after that correction, per +$10k income | **+14%** (1.14, 1.09–1.20) |
| Residual spatial clustering (Moran's I, tract models) | 0.32–0.40, p = 0.001; results hold with neighbourhood-clustered errors |

First-pass results (108 tracts, 18,007 repair requests). The income gap in sidewalk reports is **not** explained by reporting behaviour: richer tracts appear to have more reported hazards per resident, not just more eager reporters. Residuals cluster in space, so a spatial model is the next step. See [`docs/research_plan.md`](docs/research_plan.md) for threats to validity.

## Project layout

```
config/
  regions.yaml          cities, pinned to OSM boundary relations
  sources.yaml          every data source: connector, query, mapping, licence
src/atlas/
  core.py               cached HTTP, region boundaries, observation schema
  signals.py            ADA-based supports / limited / barrier rules
  dem.py                USGS 1 m DEM tiles: find, download, sample locally
  connectors/           one per protocol: overpass, arcgis, socrata, gtfs, slope, reddit
  analysis/equity.py    RQ1: 311 response time, reporting rate, curb ramp supply
  analysis/robustness.py  RQ1: reporting-bias correction, spatial checks
  report.py             coverage and cross-source agreement tables
  cli.py                `atlas fetch | report | dem | equity | sources`
scripts/
  make_readme_figure.py   static overview map
  make_readme_gifs.py     the three animations
docs/
  research_plan.md      research questions, method, threats to validity
  data_landscape.md     every way to get accessibility data, prioritised
  literature/           verified literature notes, 7 topics
  figures/
tests/                  ADA rule tests
data/                   gitignored: raw/ (HTTP cache), dem/ (tiles), processed/<region>/
SOURCES.md              list of every data source with its URL
```

## Licences and ethics

- OSM-derived data is **ODbL 1.0**: a released dataset must stay ODbL and credit OpenStreetMap contributors.
- Redlining maps (Mapping Inequality) are CC BY-NC-SA. Cincinnati is not in that dataset, so the atlas does not use them yet.
- Reddit text is never redistributed; only post IDs and salted author hashes are stored.
- Check each source's `license` field before releasing data.

## Status

Research code, not a product. The data layer and RQ1 first pass are done; wheelchair rides for ground truth (RQ2), the uncertainty map (RQ3) and the LLM benchmark (RQ4) are next.
