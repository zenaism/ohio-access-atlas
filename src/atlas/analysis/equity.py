"""RQ1: is accessibility infrastructure, and the city's response to accessibility
complaints, equitable across Cincinnati neighbourhoods?

Three analyses, each controlling for terrain (Cincinnati is hilly):
  A. Response time: how fast 311 accessibility requests are closed (Cox model, stratified
     by request type and period so that only like requests are compared; SE clustered by tract).
  B. Reporting: hazardous-sidewalk reports per resident (negative binomial, offset = population,
     control = sidewalk area). Reports reflect who complains as well as need; read with care.
  C. Supply: city curb ramps per km of road (negative binomial, offset = road km).

Covariates (tract, ACS 5-year via Esri Living Atlas): median income, % Black, % with a disability,
mean path slope (our DEM), and HOLC 1930s grade (point-level for requests, share of area for tracts).
"""

from __future__ import annotations

import json
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from lifelines import CoxPHFitter

from ..connectors.arcgis import features
from ..core import METRIC, WGS84, boundary, fetch, log, out_dir

REGION = "cincinnati"
ESRI = "https://P3ePLMYs2RVChkJx.svcs.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/{}/FeatureServer/2"
ACS = {  # service -> {field: our name}
    "ACS_Race_and_Hispanic_Origin_View_Boundaries": {
        "B03002_001E": "pop",
        "B03002_calc_pctBlackE": "pct_black",
        "B03002_calc_pctNHWhiteE": "pct_white",
    },
    "ACS_Median_Household_Income_View_Boundaries": {"B19049_001E": "median_income"},
    "ACS_Disability_Status_View_Boundaries": {"B18101_calc_pctDE": "pct_disability"},
}
HOLC = "https://services8.arcgis.com/4eSmkZn4Z1xN6dXf/ArcGIS/rest/services/mappinginequality/FeatureServer/0"

# Requests about fixing or clearing accessibility infrastructure (weather, litter, incident
# reports and investigation duplicates are excluded: their closing time means something else).
REPAIR_TYPES = [
    "SIDEWALK, REPAIR HAZ",
    "SIDEWALK, OBSTRUCTIONS",
    "CURBS, REPAIR",
    "SIDEWALK, BUSHES ENCUMBERING",
    "SIGN, HANDICAP PARKING SIGNS",
    "SIGN, ACCESSIBLE PARKING SIGN",
    "DEFAULT, ACCESSIBILITY",
    "SIGNAL, AUDIBLE SIGNAL REPAIR",
    "SIDEWALK, NEW",
    "CURBS, CURBS NEW",
]
PERIODS = [2004, 2010, 2015, 2020, 2023, 2025, 2027]  # bins; 2025+ volume jump gets its own period


def tracts() -> gpd.GeoDataFrame:
    """Hamilton County tracts with >= 50% of their area inside the city, plus ACS covariates."""
    t = None
    for service, cols in ACS.items():
        g = features(ESRI.format(service), "GEOID LIKE '39061%'", ["GEOID", *cols], REGION)
        g = g.rename(columns=cols)[["GEOID", *cols.values(), "geometry"]]
        t = g if t is None else t.merge(g.drop(columns="geometry"), on="GEOID")
    t = t.to_crs(METRIC)
    city = gpd.GeoSeries([boundary(REGION)], crs=WGS84).to_crs(METRIC).iloc[0]
    t["share_in_city"] = t.intersection(city).area / t.area
    t = t[t.share_in_city >= 0.5].copy()
    t["area_km2"] = t.area / 1e6
    return t


def holc() -> gpd.GeoDataFrame:
    """HOLC polygons. NOTE: Cincinnati is not in Mapping Inequality (checked 2026-11-07: 13 Ohio
    cities, no Cincinnati), so this returns an empty frame and the HOLC terms drop out."""
    g = features(HOLC, "city = 'Cincinnati' AND state = 'OH'", ["city", "grade", "label"], REGION)
    if g.empty or "grade" not in g:
        return gpd.GeoDataFrame({"grade": []}, geometry=[], crs=METRIC)
    return g[g.grade.isin(list("ABCD"))].to_crs(METRIC)


def roads_km(t: gpd.GeoDataFrame) -> pd.Series:
    """Public road length per tract from OSM (motorways and service roads excluded)."""
    rel = 3600000000 + 183453
    q = (
        f'[out:json][timeout:600];area({rel})->.a;way["highway"~"^(primary|secondary|tertiary|'
        f'residential|unclassified|living_street)$"](area.a);out geom;'
    )
    els = json.loads(fetch("https://overpass-api.de/api/interpreter", method="POST", data={"data": q}))[
        "elements"
    ]
    from shapely.geometry import LineString

    lines = gpd.GeoDataFrame(
        geometry=[
            LineString([(p["lon"], p["lat"]) for p in e["geometry"]])
            for e in els
            if len(e.get("geometry", [])) > 1
        ],
        crs=WGS84,
    ).to_crs(METRIC)
    pieces = gpd.overlay(lines, t[["GEOID", "geometry"]], how="intersection", keep_geom_type=True)
    return pieces.assign(km=pieces.length / 1000).groupby("GEOID").km.sum()


def build() -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    d = out_dir(REGION)
    t, h = tracts(), holc()

    # terrain: mean steepest-stretch grade of path segments in the tract
    seg = gpd.read_parquet(d / "slope_3dep_local.entities.parquet").to_crs(METRIC)
    seg["geometry"] = seg.representative_point()
    t = t.merge(
        gpd.sjoin(seg, t[["GEOID", "geometry"]]).groupby("GEOID").max_grade.mean().rename("mean_slope"),
        on="GEOID",
        how="left",
    )

    # HOLC share of tract area
    ov = (
        gpd.overlay(t[["GEOID", "geometry"]], h[["grade", "geometry"]], how="intersection")
        if len(h)
        else None
    )
    if ov is None:
        t[[f"holc_share_{g}" for g in "ABCD"]] = 0.0
    else:
        share = (
            ov.assign(a=ov.area)
            .pivot_table(index="GEOID", columns="grade", values="a", aggfunc="sum")
            .reindex(columns=list("ABCD"))
            .fillna(0)
            .div(t.set_index("GEOID").area, axis=0)
        )
        t = t.merge(share.add_prefix("holc_share_").reset_index(), on="GEOID", how="left").fillna(
            {f"holc_share_{g}": 0 for g in "ABCD"}
        )

    # supply: curb ramps, sidewalk area, road length
    ramps = gpd.read_parquet(d / "cagis_curb_ramps.entities.parquet").to_crs(METRIC)
    ramps["geometry"] = ramps.representative_point()
    t = t.merge(
        gpd.sjoin(ramps, t[["GEOID", "geometry"]]).groupby("GEOID").size().rename("n_ramps"),
        on="GEOID",
        how="left",
    )
    sw = gpd.read_parquet(d / "cagis_sidewalks.entities.parquet", columns=["geometry"]).to_crs(METRIC)
    sw = sw.assign(a=sw.area, geometry=sw.representative_point())
    t = t.merge(
        gpd.sjoin(sw, t[["GEOID", "geometry"]]).groupby("GEOID").a.sum().rename("sidewalk_m2"),
        on="GEOID",
        how="left",
    )
    t = t.merge(roads_km(t).rename("road_km"), on="GEOID", how="left")
    t = t.fillna({"n_ramps": 0, "sidewalk_m2": 0})

    # requests: tract + HOLC grade at the request's point
    r = gpd.read_parquet(d / "cincy_311.entities.parquet").to_crs(METRIC)
    r = r[r.sr_type_desc.isin(REPAIR_TYPES)]
    r = gpd.sjoin(r, t[["GEOID", "geometry"]], how="inner").drop(columns="index_right")
    if len(h):
        r = gpd.sjoin(r, h[["grade", "geometry"]], how="left").drop(columns="index_right")
        r = r[~r.index.duplicated()]
    else:
        r["grade"] = None
    r["holc"] = r.grade.fillna("ungraded").replace({"A": "AB", "B": "AB"})
    created = pd.to_datetime(r.date_created)
    end = pd.to_datetime(r.date_status_change).where(r.sr_status_flag == "CLOSED", pd.Timestamp("2026-11-07"))
    r["days"] = (end - created).dt.days.clip(lower=0) + 0.5  # same-day closures > 0 for the model
    r["closed"] = (r.sr_status_flag == "CLOSED").astype(int)
    r["period"] = pd.cut(
        created.dt.year,
        PERIODS,
        right=False,
        labels=[f"{a}-{b - 1}" for a, b in zip(PERIODS, PERIODS[1:], strict=False)],
    )
    keep = ["sr_number", "sr_type_desc", "period", "days", "closed", "holc", "GEOID"]
    r = pd.DataFrame(r[keep]).merge(pd.DataFrame(t.drop(columns="geometry")), on="GEOID", how="left")

    t.to_parquet(d / "equity_tracts.parquet")
    r.to_parquet(d / "equity_requests.parquet", index=False)
    log.info("equity: %d tracts, %d requests", len(t), len(r))
    return t, r


def _scaled(df: pd.DataFrame) -> pd.DataFrame:
    """Interpretable units: per $10k income, per 10 percentage points, per 1% slope."""
    return df.assign(
        income_10k=df.median_income / 1e4,
        black_10pp=df.pct_black / 10,
        disability_10pp=df.pct_disability / 10,
        slope_pct=df.mean_slope,
    )


COVARS = ["income_10k", "black_10pp", "disability_10pp", "slope_pct"]


def response_model(r: pd.DataFrame) -> pd.DataFrame:
    """Cox PH: hazard ratio < 1 means requests in such places are closed more slowly."""
    x = _scaled(r).dropna(subset=COVARS)
    x = pd.concat(
        [x, pd.get_dummies(x.holc, prefix="holc", dtype=float).drop(columns="holc_AB", errors="ignore")],
        axis=1,
    )
    cols = COVARS + [c for c in x if c.startswith("holc_") and c != "holc" and x[c].std() > 0]
    cph = CoxPHFitter()
    cph.fit(
        x[["days", "closed", "sr_type_desc", "period", "GEOID", *cols]],
        duration_col="days",
        event_col="closed",
        strata=["sr_type_desc", "period"],
        cluster_col="GEOID",
        robust=True,
    )
    s = cph.summary
    return (
        pd.DataFrame(
            {
                "hazard_ratio": s["exp(coef)"],
                "ci_low": s["exp(coef) lower 95%"],
                "ci_high": s["exp(coef) upper 95%"],
                "p": s["p"],
            }
        )
        .round(3)
        .assign(n=len(x))
    )


def _nb(t: pd.DataFrame, y: str, exposure: str, extra: str = "") -> pd.DataFrame:
    x = _scaled(t).dropna(subset=[*COVARS, exposure]).query(f"{exposure} > 0")
    holc = [c for c in ("holc_share_C", "holc_share_D") if x[c].std() > 0]
    f = f"{y} ~ {' + '.join(COVARS + holc)}{extra}"
    m = smf.negativebinomial(f, data=x, exposure=x[exposure]).fit(disp=0, maxiter=200)
    ci = np.exp(m.conf_int())
    out = pd.DataFrame({"rate_ratio": np.exp(m.params), "ci_low": ci[0], "ci_high": ci[1], "p": m.pvalues})
    return out.drop(index=["Intercept", "alpha"], errors="ignore").round(3).assign(n=len(x))


def reporting_model(t: pd.DataFrame, r: pd.DataFrame) -> pd.DataFrame:
    n = r[r.sr_type_desc == "SIDEWALK, REPAIR HAZ"].groupby("GEOID").size().rename("n_haz")
    x = t.drop(columns="geometry").merge(n, on="GEOID", how="left").fillna({"n_haz": 0})
    x["log_sidewalk"] = np.log1p(x.sidewalk_m2)
    return _nb(x, "n_haz", "pop", " + log_sidewalk")


def ramp_model(t: pd.DataFrame) -> pd.DataFrame:
    return _nb(t.drop(columns="geometry"), "n_ramps", "road_km")


def run() -> str:
    warnings.filterwarnings("ignore", category=FutureWarning, module="lifelines")
    t, r = build()
    parts = [
        "# RQ1 equity analysis: Cincinnati (first pass)",
        "",
        f"Tracts: {len(t)} (>= 50% inside city). Repair requests: {len(r)} "
        f"({int(r.closed.sum())} closed). Data retrieved 2026-11-07.",
        "",
        "## A. Response time (Cox, strata = request type x period, SE clustered by tract)",
        "Hazard ratio < 1 = closed more slowly. HOLC reference = grades A/B.",
        "",
        response_model(r).to_markdown(),
        "",
        "## B. Hazardous-sidewalk reports per resident (negative binomial)",
        "Rate ratio > 1 = more reports per resident, controlling for sidewalk area.",
        "",
        reporting_model(t, r).to_markdown(),
        "",
        "## C. City curb ramps per road km (negative binomial)",
        "",
        ramp_model(t).to_markdown(),
        "",
        "Units: income per $10k; % Black and % disability per 10 percentage points; slope per 1%; "
        "HOLC share per 100% of tract area.",
    ]
    from .robustness import run as robustness

    md = "\n".join(parts) + "\n\n" + robustness(t, r)
    (out_dir(REGION) / "equity_report.md").write_text(md)
    return md
