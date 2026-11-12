#!/bin/bash
# Weekly refresh: re-download calendars and theatre schedules, rebuild the maps, publish.
#
#   scripts/refresh.sh            refresh, test, commit the map/data files and push
#   NO_PUSH=1 scripts/refresh.sh  refresh and test only (nothing is committed)
#
# Only the generated files below are committed, never other work in progress, and only on main.
set -euo pipefail
cd "$(dirname "$0")/.."
export ATLAS_MAX_AGE_DAYS="${ATLAS_MAX_AGE_DAYS:-6}"   # copies older than this are fetched again
PY=.venv/bin/python
OUTPUTS=(data/map data/extracted docs/source_inventory.md data/source_inventory.csv)

echo "== $(date '+%Y-%m-%d %H:%M') refresh (pages older than ${ATLAS_MAX_AGE_DAYS} days are re-fetched)"
for source in events_ical_cincinnati events_ical_oxford events_cincy_parks web_access_performances; do
  $PY -m atlas.cli fetch "$source" || echo "WARNING: $source failed; keeping the last good copy"
done
make extract map inventory
make test

if git diff --quiet -- "${OUTPUTS[@]}" && [ -z "$(git ls-files --others --exclude-standard -- "${OUTPUTS[@]}")" ]; then
  echo "== nothing changed"
  exit 0
fi
if [ -n "${NO_PUSH:-}" ]; then
  echo "== changes ready (NO_PUSH set, not committed):"
  git status --short -- "${OUTPUTS[@]}" | head -20
  exit 0
fi
if [ "$(git branch --show-current)" != "main" ]; then
  echo "== not on main; leaving the changes uncommitted"
  exit 1
fi
git add -- "${OUTPUTS[@]}"
git commit -q -m "Weekly refresh $(date +%Y-%m-%d): events and accessible performances" -- "${OUTPUTS[@]}"
git push -q origin main
echo "== published"
