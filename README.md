<div align="center">

# Ohio Access Atlas

**Wheelchair and blind / low-vision access information for Cincinnati and Oxford, Ohio: collected, sourced, and mapped.**
A Miami University research project.

**Maps:** [Cincinnati](https://zenaism.github.io/ohio-access-atlas/data/map/cincinnati.html) · [Oxford](https://zenaism.github.io/ohio-access-atlas/data/map/oxford.html)
**Text-only, screen-reader friendly:** [All Cincinnati places](https://zenaism.github.io/ohio-access-atlas/data/map/places/cincinnati/index.html) · [All Oxford places](https://zenaism.github.io/ohio-access-atlas/data/map/places/oxford/index.html)

<img src="docs/figures/atlas_overview.png" width="100%" alt="Three maps of Cincinnati: city curb ramps versus OpenStreetMap kerbs, path slope classes, and density of 311 accessibility complaints"/>

</div>

## What it is

- **A map and a list** of about 600 places (museums, theatres, parks, trails, campus buildings, restrooms, restaurants, events) saying what is known about step-free entrances, restrooms, elevators, seating, braille, audio description and more, with **how to get there** from the nearest bus stop.
- **Every fact has a source.** Facts read from venue websites keep a word-for-word quote and a link; anything computed (slopes, distances) is labelled as computed. Places with no information say so: unknown does not mean inaccessible.
- **A data layer for a planned assistant** that answers questions from wheelchair users and blind users with evidence, and says "I don't know" when the data is missing.

## Where the data comes from

| What | Source | Amount |
|---|---|--:|
| Places, paths, crossings, kerbs, entrances, accessibility tags | [OpenStreetMap](https://www.openstreetmap.org/) | 48,000 features |
| Business and place names | [Overture Maps](https://overturemaps.org/) | 95,600 places |
| Venue accessibility (entrances, restrooms, elevators, braille, audio description…) | Venue and agency websites, PDFs and guides | 192 quoted facts, 41 venues |
| Trails | TrailLink, park sites, trail posters read by hand | 47 trails, 3 posters |
| Events, incl. accessible and disability-focused | Cincinnati Parks, Miami University and other calendars | ~700 upcoming |
| Path steepness | [USGS 3DEP elevation](https://www.usgs.gov/3d-elevation-program) | 23,900 path sections |
| Curb ramps, sidewalks, public stairs, signals (Cincinnati) | [CAGIS](https://cagisonline.hamilton-co.org/) | 241,000 records |
| Sidewalk, curb and signal problem reports (Cincinnati) | [Cincinnati 311](https://data.cincinnati-oh.gov/) | 24,600 reports |
| Bus stops | Cincinnati Metro and BCRTA (GTFS) | 2,381 stops |
| Basemap | [USGS The National Map](https://www.usgs.gov/programs/national-geospatial-program/national-map) (public domain) | |

Per-source counts, categories and failed pages: [`docs/source_inventory.md`](docs/source_inventory.md). All sources, including ones not yet collected (Google Places, Reddit, Yelp, Facebook): [`SOURCES.md`](SOURCES.md).

## First findings (Cincinnati)

- Only **1.6%** of named places in OpenStreetMap say anything about wheelchair access.
- Only **4.1%** of the city's 14,970 curb ramps have a mapped kerb within 10 m in OpenStreetMap.
- **17.4%** of path sections have a stretch steeper than the ADA ramp limit (8.33%); Oxford 5.3%.
- Areas with $10,000 higher median income file about **10% more** hazardous-sidewalk reports per resident (95% CI 5–15%); details and limits in [`docs/research_plan.md`](docs/research_plan.md).

## Run it

```bash
make setup       # Python venv, packages, headless browser
make data        # download the open sources for both cities (cached)
make extract     # turn saved pages into facts, trails and events
make map         # build data/map: GeoJSON, the two maps and the text pages
make inventory   # refresh docs/source_inventory.md
make test
```

Downloaded and processed data stay on your computer (`data/raw`, `data/processed`); the map files, extracted facts and posters are in git.

## Layout

```
config/       regions, sources, attribute vocabulary, place name matches
src/atlas/    connectors/ (one per source type), export_map.py, map_viewer.py, place_pages.py, analysis/
scripts/      fact extraction from saved pages (quotes are checked against the page text)
data/map/     the published maps, GeoJSON and text pages
data/extracted/, data/manual/posters/   facts, trails, events, and posters read by hand
docs/         research plan, source inventory, data landscape, literature notes
```
