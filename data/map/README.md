# Ohio Access Atlas maps

**Open the interactive maps** (icons, legend, filters, clickable facts with sources):

- [Cincinnati map](https://zenaism.github.io/ohio-access-atlas/data/map/cincinnati.html)
- [Oxford map](https://zenaism.github.io/ohio-access-atlas/data/map/oxford.html)

They are served by GitHub Pages from this folder and update whenever `make map` output is pushed.

**Quick preview inside GitHub:** click [github/cincinnati.geojson](github/cincinnati.geojson) or
[github/oxford.geojson](github/oxford.geojson). GitHub draws them as maps; click a marker for its facts.

## How the maps work

- **List first.** The list of places on the left is the main way to use the map with a screen reader or
  keyboard. Each place has a one-sentence summary, its rating in words, distance and direction after
  "Near me", a "Directions" link, and expandable details with every quoted source and date.
- **The map is a visual companion.** Markers are kept out of the keyboard tab order; everything on the
  map is also in the list.
- **Ratings use words and symbols, not only colour:**

| Badge | Meaning |
|---|---|
| ✓ Accessible (blue) | step-free entry and an accessible restroom are stated, or the trail is paved |
| ~ Partly accessible (orange) | some access features are stated |
| ✕ Not accessible (red-orange) | a source says it is not accessible |
| ? No information yet (grey) | no source yet; this does not mean it is inaccessible |

- Icons show the kind of place: museum/attraction, park, restroom (WC), adaptive recreation, lodging,
  event venue; trails are coloured lines. Numbered white circles are groups of nearby places.
- Checked with the axe accessibility engine: no violations on any page.

## Files

| File | What it is |
|---|---|
| `cincinnati.html`, `oxford.html`, `index.html` | Interactive viewers (one city each, or both) |
| `cincinnati_atlas.geojson`, `oxford_atlas.geojson` | Full map data: every fact with quote, source and date |
| `github/*.geojson` | Simplified copies styled for GitHub's map preview |
| `review.csv` | Everything that could not be placed on the map, and why |

Rebuild everything with `make map`.
