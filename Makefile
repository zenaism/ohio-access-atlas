PY := .venv/bin/python

setup:            ## create venv and install
	python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev,reddit,analysis,web,routing]" && .venv/bin/python -m playwright install chromium

data:             ## fetch all no-credential sources for all regions
	$(PY) -m atlas.cli fetch all --region all

report:           ## coverage + cross-source tables -> data/processed/<region>/report.md
	$(PY) -m atlas.cli report --region all

dem:              ## download USGS 1 m DEM tiles (~3.4 GB) and compute slopes locally
	$(PY) -m atlas.cli dem --region all && $(PY) -m atlas.cli fetch slope_3dep_local --region all

extract:          ## rebuild data/extracted/* from saved pages (quotes are re-checked every run)
	$(PY) scripts/venue_facts_2026_11.py && $(PY) scripts/extract_traillink.py && \
	$(PY) scripts/extract_page_events.py && $(PY) scripts/classify_miami_events.py && \
	$(PY) scripts/extract_access_performances.py && $(PY) scripts/extract_enjoyoxford_restaurants.py

refresh:          ## weekly: re-fetch calendars + theatre schedules, rebuild, commit map/data, push (NO_PUSH=1 to test)
	scripts/refresh.sh

kb:               ## assistant knowledge base (DuckDB) from the map data -> data/kb/atlas.duckdb
	$(PY) -m atlas.assistant.kb

eval:             ## tools-only run of the question bank -> eval/results/tools_baseline.md
	$(PY) scripts/eval_tools.py

map:              ## GeoJSON per region, the two maps, text page per place, review.csv
	$(PY) -m atlas.cli map

inventory:        ## per-source summary -> docs/source_inventory.md + data/source_inventory.csv
	$(PY) -m atlas.cli inventory

equity:           ## RQ1 analysis -> data/processed/cincinnati/equity_report.md
	$(PY) -m atlas.cli equity

figure:           ## README figure + animations -> docs/figures/
	$(PY) scripts/make_readme_figure.py && $(PY) scripts/make_readme_gifs.py

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check src tests

.PHONY: setup data report dem equity extract map inventory figure test lint refresh kb eval
