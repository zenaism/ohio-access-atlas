# Ohio Access Atlas maps

**Open the interactive maps** (icons, legend, filters, clickable facts with sources):

- [Cincinnati map](https://zenaism.github.io/ohio-access-atlas/data/map/cincinnati.html)
- [Oxford map](https://zenaism.github.io/ohio-access-atlas/data/map/oxford.html)

They are served by GitHub Pages from this folder and update whenever `make map` output is pushed.

**Quick preview inside GitHub:** click [github/cincinnati.geojson](github/cincinnati.geojson) or
[github/oxford.geojson](github/oxford.geojson). GitHub draws them as maps; click a marker for its facts.

## Legend

| Marker colour | Meaning |
|---|---|
| Blue `#0072B2` | Accessible: step-free entry and accessible restroom stated, or a paved trail |
| Orange `#E69F00` | Partly accessible / some access features stated |
| Red-orange `#D55E00` | Not accessible |
| Grey `#8C8C8C` | No accessibility information yet (not the same as inaccessible) |

| Icon (GitHub preview) | Category |
|---|---|
| Museum | Museums, venues and attractions |
| Park | Parks and gardens |
| Toilet (small marker) | Public restrooms |
| Wheelchair | Adaptive recreation: all-terrain chair loans, accessible launches |
| Bed | Accessible lodging |
| Star | Venue with upcoming events |
| Coloured line | Trail (blue = paved, orange = partly paved) |

## Files

| File | What it is |
|---|---|
| `cincinnati.html`, `oxford.html`, `index.html` | Interactive viewers (one city each, or both) |
| `cincinnati_atlas.geojson`, `oxford_atlas.geojson` | Full map data: every fact with quote, source and date |
| `github/*.geojson` | Simplified copies styled for GitHub's map preview |
| `review.csv` | Everything that could not be placed on the map, and why |

Rebuild everything with `make map`.
