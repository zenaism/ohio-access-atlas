# Ohio Access Atlas maps

**Open the interactive maps** (icons, legend, filters, clickable facts with sources):

- [Cincinnati map](https://zenaism.github.io/ohio-access-atlas/data/map/cincinnati.html)
- [Oxford map](https://zenaism.github.io/ohio-access-atlas/data/map/oxford.html)

They are served by GitHub Pages from this folder and update whenever `make map` output is pushed.

**Google Places accessibility:** the same Cincinnati and Oxford maps keep their original
Leaflet/USGS basemap and render saved Google Place details from
`google_places_enriched.geojson`. The maps make no live Places API requests and do not need a
browser API key. Run `scripts/google_places_private.py` to fetch missing matches and Place Details,
save a resumable private cache, and regenerate the existing map pages. `make map` rebuilds the
combined file from the saved private cache or the existing combined file. The combined file
contains all Atlas features, matched Place IDs, and returned Google detail fields. Google data is
included in the public map file; remove it from the published repository when it is no longer
needed. Deleting a file in a later commit does not remove copies from Git history.
`google_place_matches.csv` remains a compact join of Atlas records and matched Place IDs.

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

## Visitor ratings (optional)

Click a place on the map and the popup asks **"How accessible was it for you?"**: one tap on 1 to 5 stars saves
the rating. Optional one-tap extras then appear: Entrance / Restroom / Parking / Inside as **Good** or **Hard**,
and "I use" (wheelchair, cane or walker, blind or low vision, other). Nothing to type; every tap saves, and tapping
again changes it. The same widget is in each place's Details in the list, for keyboard and screen-reader users
(map markers are not in the tab order). Cards show the visitor average ("★ 4.3 visitors (3)"), Details shows a
breakdown, and the list can be sorted by **Highest visitor rating**. Visitor ratings stay separate from the
sourced rating.

Ratings are stored in Supabase (Postgres):

1. Create a free project at supabase.com, open **SQL editor**, paste `supabase/ratings.sql`, run it.
2. Copy the project URL and the **publishable** (anon) key from **Project Settings → API** into
   `config/ratings.yaml`. Never use the secret / service_role key: these two values are published in the pages.
3. `make map` and push. With an empty `config/ratings.yaml` the form is hidden.

Raw ratings (including comments) cannot be read from the browser; the page can only call
`submit_rating()` (validated, one rating per place per browser, which can be changed, at most 40 a day) and read
the per-place averages in `rating_summary`. `score` there is a Bayesian average (a 3-star prior worth 3 ratings),
used for sorting so one 5-star vote does not top the list. No IP address or account is stored. Download raw rows
for analysis from the Supabase table editor (CSV).

## Files

| File | What it is |
|---|---|
| `cincinnati.html`, `oxford.html`, `index.html` | Interactive viewers (one city each, or both) |
| `cincinnati_atlas.geojson`, `oxford_atlas.geojson` | Full map data: every fact with quote, source and date |
| `google_places_enriched.geojson` | Combined Atlas feature collection with matched Google Place details; map pages are rendered from this file |
| `google_place_matches.csv` | Atlas features joined to matched Google Place IDs |
| `github/*.geojson` | Simplified copies styled for GitHub's map preview |
| `review.csv` | Everything that could not be placed on the map, and why |

Rebuild everything with `make map`.
