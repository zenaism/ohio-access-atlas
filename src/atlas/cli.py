"""atlas fetch <source|all> --region <region|all>  |  atlas report --region <region|all>"""

from __future__ import annotations

import argparse
import importlib
import logging

from .core import config, log


def _run(source: str, region: str) -> None:
    spec = config("sources")[source]
    if region not in spec["regions"]:
        return
    importlib.import_module(f"atlas.connectors.{spec['type']}").run(source, spec, region)


def main() -> None:
    ap = argparse.ArgumentParser(prog="atlas")
    ap.add_argument("command", choices=["fetch", "report", "sources", "dem", "equity", "inventory", "map"])
    ap.add_argument("source", nargs="?", default="all")
    ap.add_argument("--region", default="all")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    sources = config("sources")
    regions = list(config("regions")) if a.region == "all" else [a.region]
    if a.command == "sources":
        for k, s in sources.items():
            print(f"{k:24} {s['type']:9} {','.join(s['regions'])}")
        return
    if a.command == "map":
        from .export_map import write as write_map

        for f in write_map():
            print(f)
        return
    if a.command == "inventory":
        from .inventory import write

        print(write())
        return
    if a.command == "equity":
        from .analysis.equity import run

        print(run())
        return
    if a.command == "dem":
        from .dem import download

        for r in regions:
            download(r)
        return
    if a.command == "report":
        from .report import write

        for r in regions:
            print(write(r))
        return
    # `all` = every source that needs no credentials; failures are logged, not fatal
    todo = [s for s, v in sources.items() if not v.get("credentials")] if a.source == "all" else [a.source]
    for r in regions:
        for s in todo:
            try:
                _run(s, r)
            except Exception:
                log.exception("[%s] %s failed", r, s)


if __name__ == "__main__":
    main()
