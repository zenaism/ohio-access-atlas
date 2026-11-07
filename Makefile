PY := .venv/bin/python

setup:            ## create venv and install
	python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev,reddit,analysis]"

data:             ## fetch all no-credential sources for all regions
	$(PY) -m atlas.cli fetch all --region all

report:           ## coverage + cross-source tables -> data/processed/<region>/report.md
	$(PY) -m atlas.cli report --region all

dem:              ## download USGS 1 m DEM tiles (~3.4 GB) and compute slopes locally
	$(PY) -m atlas.cli dem --region all && $(PY) -m atlas.cli fetch slope_3dep_local --region all

equity:           ## RQ1 analysis -> data/processed/cincinnati/equity_report.md
	$(PY) -m atlas.cli equity

figure:           ## README figure + animations -> docs/figures/
	$(PY) scripts/make_readme_figure.py && $(PY) scripts/make_readme_gifs.py

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check src tests

.PHONY: setup data report dem equity figure test lint
