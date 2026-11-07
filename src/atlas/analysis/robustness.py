"""RQ1 robustness: correct 311 counts for reporting behaviour, and check spatial dependence.

Reporting bias (after Liu, Bhandaram & Garg 2023, Nature Computational Science):
  While a problem stays unfixed, every passer-by who notices it could report it. Repeat reports
  of the SAME problem therefore measure how readily people in an area report, independent of
  how many problems the area has. A repeat = same request type, within DUP_M metres of an earlier
  report, filed while that report was still open (at most CAP_DAYS after it).
  Reporting rate model: repeats ~ Poisson(rate * open days), rate depends on tract covariates.
  Naive reports per resident = (true incidents per resident) x (reporting propensity), so the
  implied incidence rate ratio = naive rate ratio / reporting rate ratio.

Spatial checks:
  Moran's I (queen contiguity, 999 permutations) on model residuals; if residuals cluster,
  standard errors are refitted clustered by city neighbourhood (SNA) instead of by tract.
"""

from __future__ import annotations

import esda
import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from libpysal.weights import Queen

from ..core import METRIC, out_dir
from .equity import COVARS, REGION, _scaled

DUP_TYPES = ["SIDEWALK, REPAIR HAZ", "SIDEWALK, OBSTRUCTIONS", "CURBS, REPAIR"]
DUP_M, CAP_DAYS = 20, 180
END = pd.Timestamp("2026-11-07")


def incidents(t: gpd.GeoDataFrame) -> pd.DataFrame:
    """One row per first report of a problem, with the number of repeat reports it attracted."""
    r = gpd.read_parquet(out_dir(REGION) / "cincy_311.entities.parquet").to_crs(METRIC)
    r = r[r.sr_type_desc.isin(DUP_TYPES)].copy()
    r = gpd.sjoin(r, t[["GEOID", "geometry"]], how="inner").drop(columns="index_right")
    r["t0"] = pd.to_datetime(r.date_created)
    r["t1"] = pd.to_datetime(r.date_status_change).where(r.sr_status_flag == "CLOSED", END)
    r["t1"] = np.minimum(r.t1, r.t0 + pd.Timedelta(days=CAP_DAYS))
    r = r.sort_values("t0").reset_index(drop=True)

    # pairs (earlier i, later j) of the same type within DUP_M metres
    pairs = gpd.sjoin(
        r[["sr_type_desc", "t0", "t1", "geometry"]],
        r[["sr_type_desc", "t0", "geometry"]],
        predicate="dwithin",
        distance=DUP_M,
    )
    pairs = pairs[
        (pairs.index != pairs.index_right)
        & (pairs.sr_type_desc_left == pairs.sr_type_desc_right)
        & (pairs.t0_right > pairs.t0_left)
        & (pairs.t0_right <= pairs.t1)
    ]
    # each repeat is credited to its earliest open "parent"; parents that are themselves repeats are dropped
    parent = pairs.reset_index().sort_values("t0_left").groupby("index_right")["index"].first()
    is_repeat = r.index.isin(parent.index)
    first = r[~is_repeat].copy()
    first["repeats"] = parent[parent.isin(first.index)].value_counts().reindex(first.index, fill_value=0)
    first["open_days"] = (first.t1 - first.t0).dt.days.clip(lower=0) + 0.5
    first["year"] = first.t0.dt.year
    first["period"] = pd.cut(first.year, [2004, 2015, 2020, 2025, 2027], right=False).astype(str)
    cols = ["sr_number", "sr_type_desc", "period", "repeats", "open_days", "GEOID", "neighborhood"]
    return pd.DataFrame(first[cols]).merge(pd.DataFrame(t.drop(columns="geometry")), on="GEOID", how="left")


def _table(m, name: str) -> pd.DataFrame:
    ci = np.exp(m.conf_int())
    out = pd.DataFrame({name: np.exp(m.params), "ci_low": ci[0], "ci_high": ci[1], "p": m.pvalues})
    return out.loc[[c for c in COVARS if c in out.index]].round(3)


def reporting_rate_model(inc: pd.DataFrame):
    x = _scaled(inc).dropna(subset=COVARS)
    f = f"repeats ~ {' + '.join(COVARS)} + C(sr_type_desc) + C(period)"
    groups = x.GEOID.astype("category").cat.codes
    return smf.glm(f, data=x, family=sm.families.Poisson(), offset=np.log(x.open_days)).fit(
        cov_type="cluster", cov_kwds={"groups": groups}
    ), x


def _nb_fit(x: pd.DataFrame, y: str, exposure: str, extra: str = "", cluster: str | None = None):
    x = _scaled(x).dropna(subset=[*COVARS, exposure]).query(f"{exposure} > 0")
    f = f"{y} ~ {' + '.join(COVARS)}{extra}"
    kw = (
        {"cov_type": "cluster", "cov_kwds": {"groups": x[cluster].astype("category").cat.codes}}
        if cluster
        else {}
    )
    return smf.negativebinomial(f, data=x, exposure=x[exposure]).fit(disp=0, maxiter=300, **kw), x


def pearson(m) -> np.ndarray:
    """Pearson residuals of a statsmodels negative-binomial fit: (y - mu) / sqrt(mu + alpha mu^2)."""
    mu, y, a = m.predict(), m.model.endog, m.params["alpha"]
    return (y - mu) / np.sqrt(mu + a * mu**2)


def tract_neighbourhood(t: gpd.GeoDataFrame) -> pd.Series:
    """Majority 311 neighbourhood label of each tract (city statistical neighbourhoods)."""
    r = gpd.read_parquet(out_dir(REGION) / "cincy_311.entities.parquet", columns=["neighborhood", "geometry"])
    r = gpd.sjoin(r.to_crs(METRIC), t[["GEOID", "geometry"]])
    return r.groupby("GEOID").neighborhood.agg(lambda s: s.mode().iat[0] if len(s.mode()) else "unknown")


def moran(t: gpd.GeoDataFrame, values: pd.Series, label: str) -> dict:
    g = t[["GEOID", "geometry"]].merge(values.rename("v"), left_on="GEOID", right_index=True).dropna()
    w = Queen.from_dataframe(g, use_index=False, silence_warnings=True)
    w.transform = "r"
    mi = esda.Moran(g.v.values, w, permutations=999)
    return {"variable": label, "n": len(g), "moran_I": round(mi.I, 3), "p_perm": round(mi.p_sim, 3)}


def run(t: gpd.GeoDataFrame, r: pd.DataFrame) -> str:
    inc = incidents(t)
    rate, xr = reporting_rate_model(inc)
    n_rep = int(inc.repeats.sum())

    # naive vs corrected: hazardous-sidewalk FIRST reports (incidents) per resident
    haz = inc[inc.sr_type_desc == "SIDEWALK, REPAIR HAZ"].groupby("GEOID").size().rename("n_inc")
    tt = t.drop(columns="geometry").merge(haz, on="GEOID", how="left").fillna({"n_inc": 0})
    tt["log_sidewalk"] = np.log1p(tt.sidewalk_m2)
    naive, xn = _nb_fit(tt, "n_inc", "pop", " + log_sidewalk")
    # tract reporting propensity from the rate model (covariate part only), used as extra exposure
    beta = rate.params[COVARS]
    xn = xn.assign(propensity=np.exp(xn[COVARS].values @ beta.values))
    corr = smf.negativebinomial(
        f"n_inc ~ {' + '.join(COVARS)} + log_sidewalk", data=xn, exposure=xn["pop"] * xn.propensity
    ).fit(disp=0, maxiter=300)

    def ci(m, name):
        tb = _table(m, name)
        return (
            tb[name].map("{:.3f}".format)
            + " ("
            + tb.ci_low.map("{:.2f}".format)
            + "–"
            + tb.ci_high.map("{:.2f}".format)
            + ")"
        )

    comp = pd.concat(
        {n: ci(m, n) for n, m in [("naive RR", naive), ("reporting RR", rate), ("corrected RR", corr)]},
        axis=1,
    )

    # spatial checks
    nb_by_tract = tract_neighbourhood(t)
    tt = tt.merge(nb_by_tract.rename("sna"), left_on="GEOID", right_index=True, how="left")
    ramp, xramp = _nb_fit(t.drop(columns="geometry"), "n_ramps", "road_km")
    resp = r[r.closed == 1].assign(ld=np.log(r.days))
    resp["resid"] = resp.ld - resp.groupby(["sr_type_desc", "period"], observed=True).ld.transform("mean")
    morans = pd.DataFrame(
        [
            moran(
                t,
                xn.set_index("GEOID").n_inc / xn.set_index("GEOID")["pop"],
                "B: incidents per resident (raw)",
            ),
            moran(t, pd.Series(pearson(corr), index=xn.GEOID), "B: corrected model residuals"),
            moran(t, pd.Series(pearson(ramp), index=xramp.GEOID), "C: ramp model residuals"),
            moran(t, resp.groupby("GEOID").resid.mean(), "A: mean response-time residual"),
        ]
    )
    corr_sna, _ = _nb_fit(tt, "n_inc", "pop", " + log_sidewalk", cluster="sna")
    ramp_tt = t.drop(columns="geometry").merge(nb_by_tract.rename("sna"), left_on="GEOID", right_index=True)
    ramp_sna, _ = _nb_fit(ramp_tt, "n_ramps", "road_km", cluster="sna")

    parts = [
        "## D. Reporting-bias correction (repeat-report method, Liu et al. 2023)",
        f"Problems (first reports) of {', '.join(DUP_TYPES)}: {len(inc):,}; repeat reports found: {n_rep:,} "
        f"(same type, <= {DUP_M} m, filed while the first was open, <= {CAP_DAYS} days).",
        "Reporting RR > 1 = people in such tracts report an open problem faster. "
        "Corrected RR = incidents per resident after dividing out reporting propensity.",
        "",
        comp.to_markdown(),
        "",
        "## E. Spatial dependence (Moran's I, queen contiguity, 999 permutations)",
        "",
        morans.to_markdown(index=False),
        "",
        "## F. Refit with SE clustered by neighbourhood (SNA) instead of tract",
        "",
        "Hazardous-sidewalk incidents per resident (naive):",
        "",
        _table(corr_sna, "rate_ratio").to_markdown(),
        "",
        "Curb ramps per road km:",
        "",
        _table(ramp_sna, "rate_ratio").to_markdown(),
        "",
    ]
    return "\n".join(parts)
