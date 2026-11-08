<div align="center">

# Ohio Access Atlas

**A multi-source, provenance-tracked map of wheelchair accessibility for Cincinnati and Oxford, Ohio**

[**Quick start**](#quick-start) · [**A look at the data**](#a-look-at-the-data) · [**What data do we have?**](#what-data-do-we-have) · [**Data format**](#data-format) · [**What did we calculate?**](#what-did-we-calculate-and-why) · [**First findings**](#first-findings) · [**Project layout**](#project-layout) · [**Sources**](SOURCES.md)

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-lightgrey)

<img src="docs/figures/slope_walk.gif" width="95%" alt="Animation: a dot climbs Warner Street in Cincinnati while its elevation profile and 10 m grades build up against the ADA walkway and ramp limits"/>

<sub>One real street and a terrain model. A dot climbs Warner Street, sampling the USGS 1 m elevation model about every 10 m. <b>Top:</b> elevation along the street. <b>Bottom:</b> estimated steepness of each stretch, compared with ADA slope guidelines. This is an estimate from terrain data, not a measurement of the sidewalk itself.</sub>

| **355,568** observation rows, including two Oxford slope methods | **12** configured sources | **2** Ohio cities | **24,639** Cincinnati 311 requests | **14,970** Cincinnati curb-ramp features | **23,934** path segments with local DEM slope |
|:-:|:-:|:-:|:-:|:-:|:-:|

</div>

## Why

- **Open maps miss details wheelchair users need.** In our Cincinnati data, **99 of 6,235 named OpenStreetMap places (1.6%) have a `wheelchair` tag**. **4.1% of CAGIS curb ramps have an OSM kerb node within 10 metres**. The second number is a proximity comparison, not proof that OSM mapped only 4.1% of all ramps. These figures are calculated by the [coverage and comparison code](src/atlas/report.py) from the [OSM data](https://overpass-api.de/api/interpreter) and [CAGIS curb-ramp layer](https://cagisonline.hamilton-co.org/arcgis/rest/services/DTE/DOTE_Versioned/FeatureServer/0). Run `make report` to create the detailed local report.
- **No single source is enough.** [CAGIS](https://cagisonline.hamilton-co.org/arcgis/rest/services/DTE/DOTE_Versioned/FeatureServer/0) gives ramp locations, but not whether each ramp works well today; [Cincinnati 311](https://data.cincinnati-oh.gov/resource/gcej-gmiw.json) records reported problems, but only where and when people report them; [OpenStreetMap](https://overpass-api.de/api/interpreter) maps paths and places, but often lacks accessibility details. We compare sources because each tells us a different part of the picture.
- **We keep track of where facts came from.** Records include source details and collection dates, and original web responses are cached so results can be checked and rebuilt.
- **It is a research data layer for a planned assistant.** The atlas is not yet a route planner or a working question-answering model. The research goal is to build an assistant that uses evidence and says "unknown" when information is missing.

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

## What data do we have?

The sources below are the sources represented in the current processed dataset. A source may provide many features, and a feature may produce one or more observation rows.

| What the data describes | Where it came from | Cincinnati | Oxford |
|---|---|--:|--:|
| Places, walking paths, kerbs, crossings, steps, and other mapped features | [OpenStreetMap via Overpass](https://overpass-api.de/api/interpreter) | 27,796 accessibility observations | 3,894 accessibility observations |
| Path steepness estimated from terrain | [USGS 3DEP 1 m DEM products](https://tnmaccess.nationalmap.gov/api/v1/products), sampled locally | 40,124 observations on 20,062 path segments | 7,744 observations on 3,872 path segments |
| A second Oxford path-steepness estimate, from the USGS elevation service | [USGS National Map elevation service](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer) | – | 7,744 observations on the same 3,872 segments |
| Curb-ramp locations | [CAGIS sidewalk asset layer](https://cagisonline.hamilton-co.org/arcgis/rest/services/DTE/DOTE_Versioned/FeatureServer/0) | 14,970 | – |
| Sidewalk and walkway polygons | [CAGIS sidewalk asset layer](https://cagisonline.hamilton-co.org/arcgis/rest/services/DTE/DOTE_Versioned/FeatureServer/0) | 220,792 | – |
| Public stairways | [CAGIS public-steps layer](https://cagisonline.hamilton-co.org/arcgis/rest/services/Cincinnati/PS_Maintenance/MapServer/1) | 160 | – |
| Traffic signals | [CAGIS traffic-signal layer](https://cagisonline.hamilton-co.org/arcgis/rest/services/DTE/DOTE_Traffic_Engineering/FeatureServer/8) | 5,324 | – |
| Accessibility-related service requests | [Cincinnati 311 dataset `gcej-gmiw`](https://data.cincinnati-oh.gov/resource/gcej-gmiw.json) | 24,639 requests | – |
| Transit stops and the feed's wheelchair-boarding code | [Cincinnati Metro GTFS](https://files.mobilitydatabase.org/mdb-307/latest.zip) | 2,320 | – |
| Transit stops from an older feed | [BCRTA GTFS](https://files.mobilitydatabase.org/mdb-240/latest.zip) | – | 61 |

These are **not all equivalent measures**: for example, CAGIS ramp counts are mapped ramp features, OSM counts above are observation rows, and slope counts include two calculated attributes per path. Adding every row gives **355,568 observation rows**, including both Oxford slope methods; it does not mean there are that many unique streets or places.

The Cincinnati equity analysis also uses population, race, disability, and household-income estimates from the U.S. Census American Community Survey, accessed through [Esri's ACS race service](https://p3eplmys2rvchkjx.svcs.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/ACS_Race_and_Hispanic_Origin_View_Boundaries/FeatureServer/2), [income service](https://p3eplmys2rvchkjx.svcs.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/ACS_Median_Household_Income_View_Boundaries/FeatureServer/2), and [disability service](https://p3eplmys2rvchkjx.svcs.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/ACS_Disability_Status_View_Boundaries/FeatureServer/2). It also uses public road geometries from [OpenStreetMap via Overpass](https://overpass-api.de/api/interpreter) to calculate road length by census tract. These analysis inputs are not included in the 355,568 source-observation total. Reddit is configured as an optional source, but there are no Reddit posts in the processed dataset. Google data is not used.

### Other websites we are considering

These are ideas for possible future data, not sources in the current processed dataset:

- **Google Places API:** could help compare details such as accessible entrances or restrooms. This would use Google's API, not scrape Google search results.
- **Reddit:** an optional collector is already in the code for public accessibility discussions. It needs API credentials, and no Reddit data has been collected yet.
- **AllTrails:** we are not planning to scrape it because automated access is blocked and its terms may not allow it. For trail details, we can use official sources such as [Great Parks of Hamilton County](https://www.greatparks.org/) and [Ohio Department of Natural Resources](https://ohiodnr.gov/).

See [`SOURCES.md`](SOURCES.md) for all current and possible data sources.

### Where to find the data

Processed files are saved under [`data/processed/`](data/processed/) in `cincinnati/` and `oxford/`. Each source generally has:

- `*.entities.parquet`: the original mapped features or records.
- `*.obs.parquet`: facts extracted into the shared observation format.
- `report.md`: a generated summary of coverage and source comparisons.
- Cincinnati also has `equity_tracts.parquet`, `equity_requests.parquet`, and `equity_report.md`.

The DEM raster files are under [`data/dem/`](data/dem/); the tile lists are [`cincinnati_tiles.csv`](data/dem/cincinnati_tiles.csv) and [`oxford_tiles.csv`](data/dem/oxford_tiles.csv). Raw web responses are cached under `data/raw/`.

**These local data outputs are ignored by Git** (except the small DEM tile manifests). They are created by running the collection and analysis commands; a fresh clone will not include the large processed dataset or raw caches. See [`config/sources.yaml`](config/sources.yaml) for each configured source, query, region, and output mapping, and [`SOURCES.md`](SOURCES.md) for source links and notes.

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

In simple terms, an observation is one recorded claim about one thing: for example, “this path is tagged as asphalt” or “this transit stop has this boarding code.” The row keeps the source and a link or ID so the claim can be traced back.

The `signal` column is a **simple screening label**, not a final accessibility decision. Rules in [`signals.py`](src/atlas/signals.py) compare some recorded values with ADA-based guidelines: for example, path slope against 5% and 8.33% limits, or width against 0.915 m and 1.525 m. Known surface, step, kerb, and wheelchair tags also get simple labels. Missing or unclear values are `unknown`. A ramp or sidewalk being present does not tell us its condition, and terrain slope is not the same as a field measurement of the path.

The full source feature is kept separately from its observation rows as GeoParquet.

## What did we calculate, and why?

1. **Slope along mapped paths.** The code takes an OpenStreetMap walking path, samples elevation from a USGS 1 m DEM at roughly 10 m intervals, and calculates `grade (%) = elevation change / horizontal distance × 100`. It saves the steepest sampled stretch and the overall end-to-end grade. This helps identify potentially steep paths. It is an estimate: the DEM describes terrain, can be noisy, and may not capture the sidewalk surface.
2. **Simple accessibility signals.** Recorded tags and measurements are translated into `supports`, `limited`, `barrier`, or `unknown`. This gives reports a consistent way to summarize values; it does not certify ADA compliance or guarantee a route works for a particular person.
3. **Coverage and overlap.** The report counts how often OSM has tags such as wheelchair access, surface, width, or incline, and checks whether city ramp features have an OSM kerb or crossing nearby at 5, 10, and 20 metres. The purpose is to show what each source knows and where information is missing. Nearby features are not necessarily the same real-world ramp.
4. **Cincinnati neighborhood analysis.** The equity analysis groups requests, ramps, sidewalk area, population, and other measures by census tract. It estimates complaint rates per resident, ramp counts per road kilometre, and how long repair requests take to close. A separate repeat-report method and spatial checks test whether patterns might reflect reporting behavior or geographic clustering. These are associations in observational data, not proof of cause.

The pipeline does **not** yet produce a complete wheelchair-routing network, validate every label against a field audit, or train the proposed language model. Those are research goals, not completed calculations.

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
  sources.yaml          every data source: connector, query, and output mapping
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
