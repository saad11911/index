#!/usr/bin/env python3
"""Bitcoin seasonality vs. halving cycle vs. Fed policy — reproducible analysis.

Outputs CSV tables to results/ and a summary JSON. Run after build_dataset.py.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parent
D, R = ROOT / "data", ROOT / "results"
R.mkdir(exist_ok=True)
rng = np.random.default_rng(20260921)
NBOOT = 20_000

# ----------------------------------------------------------------------------- data
px = pd.read_csv(D / "btc_daily.csv", parse_dates=["date"]).set_index("date")["close"]
LAST = px.index.max()
eth = pd.read_csv(D / "raw_coinmetrics_eth.csv", parse_dates=["date"]).set_index("date")["PriceUSD"]
halvings = pd.to_datetime(pd.read_csv(D / "halvings.csv")["date"]).tolist()
fed = pd.read_csv(D / "fed_policy_changes.csv", parse_dates=["date"])
fomc = pd.read_csv(D / "fomc_meetings.csv", parse_dates=["date"])

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
summary = {"data_last_date": str(LAST.date()), "last_close": float(px.iloc[-1])}

# ----------------------------------------------------------------------------- monthly returns
m_close = px.resample("ME").last()
m_ret = m_close.pct_change().dropna()
m_ret = m_ret[m_ret.index >= "2011-01-31"]
partial_month = LAST != (LAST + pd.offsets.MonthEnd(0))
complete = m_ret.copy()
if partial_month:
    complete = complete.iloc[:-1]
mt = pd.DataFrame({"ret": complete, "year": complete.index.year, "month": complete.index.month})
heat = mt.pivot(index="year", columns="month", values="ret")
heat.columns = MONTHS
if partial_month:
    heat.loc[LAST.year, MONTHS[LAST.month - 1]] = m_ret.iloc[-1]  # shown, flagged as partial
heat.to_csv(R / "monthly_returns_heatmap.csv", float_format="%.4f")
summary["partial_month"] = {"month": str(m_ret.index[-1].strftime("%Y-%m")), "ret_to_date": float(m_ret.iloc[-1])} if partial_month else None


def boot_ci(x, fn, n=NBOOT):
    x = np.asarray(x)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    s = fn(x[idx], axis=1)
    return float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def month_table(df, label):
    rows = []
    for mo in range(1, 13):
        x = df.loc[df.month == mo, "ret"].values
        lx = np.log1p(x)
        t, p = stats.ttest_1samp(lx, 0)
        try:
            w = stats.wilcoxon(x).pvalue
        except ValueError:
            w = np.nan
        lo, hi = boot_ci(x, np.mean)
        mlo, mhi = boot_ci(x, np.median)
        rows.append(dict(month=MONTHS[mo - 1], n=len(x), mean=x.mean(), median=np.median(x),
                         hit_rate=(x > 0).mean(), geo_mean=np.expm1(lx.mean()), std=x.std(ddof=1),
                         t_logret=t, p_t=p, p_wilcoxon=w, mean_ci_lo=lo, mean_ci_hi=hi,
                         median_ci_lo=mlo, median_ci_hi=mhi, best=x.max(), worst=x.min()))
    out = pd.DataFrame(rows).set_index("month")
    out.to_csv(R / f"month_stats_{label}.csv", float_format="%.4f")
    return out


def permutation_family(df, target_months, n=NBOOT):
    """Max-|t| permutation test: is the target month's mean log-return unusual given 12 looks?"""
    lx = np.log1p(df["ret"].values)
    mo = df["month"].values
    def tstats(labels):
        return np.array([stats.ttest_1samp(lx[labels == k], 0).statistic for k in range(1, 13)])
    obs = tstats(mo)
    maxes = np.empty(n)
    for i in range(n):
        maxes[i] = np.abs(tstats(rng.permutation(mo))).max()
    return {MONTHS[k - 1]: dict(t=float(obs[k - 1]), p_familywise=float((maxes >= abs(obs[k - 1])).mean()),
                                p_single=float(stats.ttest_1samp(lx[mo == k], 0).pvalue)) for k in target_months}


ms_all = month_table(mt, "2011_2025")
ms_13 = month_table(mt[mt.year >= 2013], "2013_2025")
summary["perm_family_2011"] = permutation_family(mt, [10, 11, 12, 9, 2, 4, 7])
summary["perm_family_2013"] = permutation_family(mt[mt.year >= 2013], [10, 11, 12, 9, 2, 4, 7])

# 2-month and Q4 windows
q = pd.DataFrame({"close": m_close})
q["year"] = q.index.year; q["month"] = q.index.month
def window_ret(y, m0, m1):
    a = m_close[(m_close.index.year == y) & (m_close.index.month == m0 - 1)] if m0 > 1 else m_close[(m_close.index.year == y - 1) & (m_close.index.month == 12)]
    b = m_close[(m_close.index.year == y) & (m_close.index.month == m1)]
    if len(a) and len(b):
        return b.iloc[0] / a.iloc[0] - 1
    return np.nan
yrs = list(range(2011, LAST.year + 1))
win = pd.DataFrame(index=yrs)
win["OctNov"] = [window_ret(y, 10, 11) for y in yrs]
win["Q4"] = [window_ret(y, 10, 12) for y in yrs]
win["Q1"] = [window_ret(y, 1, 3) for y in yrs]
win["Q2"] = [window_ret(y, 4, 6) for y in yrs]
win["Q3"] = [window_ret(y, 7, 9) for y in yrs]
win["FullYear"] = [window_ret(y, 1, 12) for y in yrs]
win.to_csv(R / "window_returns_by_year.csv", float_format="%.4f")

# Is Oct-Nov special among all 2-month windows? (bootstrap of mean 2-month log return by start month)
two = np.log(m_close).diff(2).dropna()
two = two[two.index >= "2011-02-28"]
two = two[two.index <= complete.index[-1]]
two_by_end = pd.DataFrame({"r": two, "end_month": two.index.month})
tw = two_by_end.groupby("end_month")["r"].agg(["mean", "median", "count", lambda s: (s > 0).mean()])
tw.columns = ["mean_log", "median_log", "n", "hit"]
tw.index = [MONTHS[i - 1] for i in tw.index]
tw.to_csv(R / "two_month_windows_by_end_month.csv", float_format="%.4f")

# ----------------------------------------------------------------------------- halving cycle
def cycle_year(y):
    base = {2012: 0, 2013: 1, 2014: 2, 2015: 3, 2016: 0, 2017: 1, 2018: 2, 2019: 3,
            2020: 0, 2021: 1, 2022: 2, 2023: 3, 2024: 0, 2025: 1, 2026: 2}
    return base.get(y, np.nan)
mt["cycle_year"] = mt.year.map(cycle_year)
cy = mt.groupby(["cycle_year", "month"])["ret"].agg(["mean", "median", "count", lambda s: (s > 0).mean()])
cy.columns = ["mean", "median", "n", "hit"]
cy = cy.reset_index(); cy["month"] = cy.month.map(lambda k: MONTHS[k - 1])
cy.to_csv(R / "month_stats_by_cycle_year.csv", index=False, float_format="%.4f")
win["cycle_year"] = [cycle_year(y) for y in win.index]
cyw = win.groupby("cycle_year")[["OctNov", "Q4", "Q1", "Q2", "Q3", "FullYear"]].agg(["mean", "median", "count"])
cyw.to_csv(R / "window_returns_by_cycle_year.csv", float_format="%.4f")

# Oct/Nov with and without the post-halving (H+1) years
def sub(df, mo, cond):
    x = df.loc[(df.month == mo) & cond, "ret"]
    return dict(n=int(len(x)), mean=float(x.mean()), median=float(x.median()), hit=float((x > 0).mean()))
decomp = {}
for mo, name in [(10, "Oct"), (11, "Nov"), (12, "Dec")]:
    decomp[name] = {
        "all_2011_2025": sub(mt, mo, mt.year >= 2011),
        "all_2013_2025": sub(mt, mo, mt.year >= 2013),
        "excl_H+1_years": sub(mt, mo, mt.cycle_year != 1),
        "H+1_only": sub(mt, mo, mt.cycle_year == 1),
        "H+2_only": sub(mt, mo, mt.cycle_year == 2),
        "H+2_and_H+3": sub(mt, mo, mt.cycle_year.isin([2, 3])),
        "H0_only": sub(mt, mo, mt.cycle_year == 0),
    }
summary["oct_nov_decomposition"] = decomp

# Halving-aligned paths, peaks and troughs per cycle
cycles = []
paths = {}
for i, h in enumerate(halvings):
    nxt = halvings[i + 1] if i + 1 < len(halvings) else LAST + pd.Timedelta(days=1)
    seg = px[(px.index >= h) & (px.index < nxt)]
    first = seg[seg.index < h + pd.Timedelta(days=900)]  # cycle peak = high within 900 days of the halving
    pk_date, pk = first.idxmax(), first.max()
    post = seg[seg.index > pk_date]
    tr_date, tr = (post.idxmin(), post.min()) if len(post) else (pd.NaT, np.nan)
    pre = px[(px.index < h)]
    prior_low_date = pre[pre.index >= (halvings[i - 1] if i else px.index[0])].idxmin() if i else pre.idxmin()
    cycles.append(dict(halving=h.date(), halving_price=float(px.asof(h)), peak_date=pk_date.date(), peak=float(pk),
                       days_halving_to_peak=(pk_date - h).days, gain_halving_to_peak=float(pk / px.asof(h) - 1),
                       trough_date=tr_date.date() if pd.notna(tr_date) else None, trough=float(tr) if pd.notna(tr) else None,
                       days_peak_to_trough=(tr_date - pk_date).days if pd.notna(tr_date) else None,
                       drawdown_peak_to_trough=float(tr / pk - 1) if pd.notna(tr_date) else None,
                       complete=bool(i + 1 < len(halvings))))
    rel = (seg / px.asof(h)); rel.index = (rel.index - h).days
    paths[str(h.year)] = rel
cyc = pd.DataFrame(cycles); cyc.to_csv(R / "halving_cycles.csv", index=False, float_format="%.4f")
pd.DataFrame(paths).to_csv(R / "halving_aligned_paths.csv", float_format="%.5f")

# Peak-aligned analogs (price / cycle peak vs days since peak)
peak_paths = {}
for c in cycles:
    pk = pd.Timestamp(c["peak_date"]); seg = px[(px.index >= pk) & (px.index <= pk + pd.Timedelta(days=600))]
    rel = seg / c["peak"]; rel.index = (rel.index - pk).days
    peak_paths[str(pk.year)] = rel
pp = pd.DataFrame(peak_paths); pp.to_csv(R / "peak_aligned_paths.csv", float_format="%.5f")
cur_days = (LAST - pd.Timestamp(cycles[-1]["peak_date"])).days
analog = {}
for k, s in peak_paths.items():
    if k == str(pd.Timestamp(cycles[-1]["peak_date"]).year):
        continue
    s = s.dropna()
    at = float(s.asof(cur_days)) if cur_days in s.index or s.index.max() >= cur_days else None
    fwd = s[(s.index > cur_days) & (s.index <= cur_days + 107)]  # ~ to Dec 31
    trough_after = float(fwd.min() / s.asof(cur_days) - 1) if len(fwd) else None
    end_after = float(fwd.iloc[-1] / s.asof(cur_days) - 1) if len(fwd) else None
    analog[k] = dict(price_over_peak_at_same_day=at, next_107d_min_change=trough_after, next_107d_end_change=end_after,
                     days_to_trough_from_peak=int(s.idxmin()))
summary["peak_analog"] = dict(days_since_2025_peak=int(cur_days), current_price_over_peak=float(px.iloc[-1] / cycles[-1]["peak"]), analogs=analog)

# ----------------------------------------------------------------------------- Fed regimes
def regime(d):
    if d < pd.Timestamp("2015-12-16"): return "ZIRP/QE (0-0.25%)"
    if d < pd.Timestamp("2018-12-20"): return "Hiking cycle"
    if d < pd.Timestamp("2019-07-31"): return "Hold at peak"
    if d < pd.Timestamp("2019-10-31"): return "Cutting"
    if d < pd.Timestamp("2020-03-03"): return "Hold after cuts"
    if d < pd.Timestamp("2022-03-16"): return "ZIRP/QE (0-0.25%)"
    if d < pd.Timestamp("2023-07-27"): return "Hiking cycle"
    if d < pd.Timestamp("2024-09-18"): return "Hold at peak"
    if d < pd.Timestamp("2024-12-19"): return "Cutting"
    if d < pd.Timestamp("2025-09-17"): return "Hold after cuts"
    if d < pd.Timestamp("2025-12-11"): return "Cutting"
    if d < pd.Timestamp("2026-09-16"): return "Hold after cuts"
    return "Hiking cycle"
mt["regime"] = [regime(d) for d in mt.index]
reg = mt.groupby("regime")["ret"].agg(["count", "mean", "median", lambda s: (s > 0).mean(), "std"])
reg.columns = ["n_months", "mean", "median", "hit", "std"]
reg["ann_vol"] = reg["std"] * np.sqrt(12)
reg.to_csv(R / "monthly_returns_by_fed_regime.csv", float_format="%.4f")
q4 = mt[mt.month.isin([10, 11])].groupby("regime")["ret"].agg(["count", "mean", "median", lambda s: (s > 0).mean()])
q4.columns = ["n_months", "mean", "median", "hit"]
q4.to_csv(R / "oct_nov_returns_by_fed_regime.csv", float_format="%.4f")

# Fed funds upper bound by month-end + 12m change in policy rate vs BTC 12m return
ub = pd.Series(fed.set_index("date")["target_upper"]).reindex(pd.date_range("2010-01-01", LAST)).ffill().fillna(0.25)
ffr_m = ub.resample("ME").last()
lvl = pd.DataFrame({"btc_12m": m_close.pct_change(12), "ffr_chg_12m": ffr_m.diff(12), "ffr": ffr_m}).dropna()
lvl = lvl[lvl.index >= "2013-01-31"]
summary["ffr_vs_btc"] = dict(corr_btc12m_vs_ffr_chg12m=float(lvl["btc_12m"].corr(lvl["ffr_chg_12m"])),
                             spearman=float(stats.spearmanr(lvl["btc_12m"], lvl["ffr_chg_12m"]).statistic), n=int(len(lvl)))
lvl.to_csv(R / "ffr_vs_btc_12m.csv", float_format="%.4f")

# FOMC decision-day event study (close t-1 -> t, t+1, t+5, t+21)
ev = []
for _, r in fomc.iterrows():
    d = r["date"]
    if d < px.index.min() + pd.Timedelta(days=30) or d + pd.Timedelta(days=21) > LAST:
        continue
    base = px.asof(d - pd.Timedelta(days=1))
    ev.append(dict(date=d.date(), decision=r["decision"], r0=px.asof(d) / base - 1, r1=px.asof(d + pd.Timedelta(days=1)) / base - 1,
                   r5=px.asof(d + pd.Timedelta(days=5)) / base - 1, r21=px.asof(d + pd.Timedelta(days=21)) / base - 1))
ev = pd.DataFrame(ev); ev.to_csv(R / "fomc_event_returns.csv", index=False, float_format="%.4f")
es = ev.groupby("decision")[["r0", "r1", "r5", "r21"]].agg(["mean", "median", "count"])
es.to_csv(R / "fomc_event_study.csv", float_format="%.4f")
hit = ev.groupby("decision")[["r0", "r1", "r5", "r21"]].agg(lambda s: (s > 0).mean())
hit.to_csv(R / "fomc_event_hit_rates.csv", float_format="%.3f")
# unconditional comparison: random 1/2/6/22-day returns
lr = np.log(px).diff().dropna(); lr = lr[lr.index >= "2013-01-01"]
summary["fomc_event"] = {k: dict(mean_r1=float(es.loc[k, ("r1", "mean")]), median_r1=float(es.loc[k, ("r1", "median")]),
                                 mean_r21=float(es.loc[k, ("r21", "mean")]), n=int(es.loc[k, ("r1", "count")])) for k in es.index}
summary["fomc_event"]["unconditional_mean_2d"] = float(np.expm1(lr.rolling(2).sum().mean()))
summary["fomc_event"]["unconditional_mean_22d"] = float(np.expm1(lr.rolling(22).sum().mean()))

# ----------------------------------------------------------------------------- volatility & trend-state conditioning
dl = np.log(px).diff().dropna(); dl = dl[dl.index >= "2013-01-01"]
vol = dl.groupby(dl.index.month).std() * np.sqrt(365)
vol.index = MONTHS; vol.to_csv(R / "realized_vol_by_month.csv", float_format="%.4f")

ma200 = px.rolling(200).mean()
ath = px.cummax()
state = []
for y in range(2013, LAST.year + 1):
    d = pd.Timestamp(f"{y}-09-30") if pd.Timestamp(f"{y}-09-30") <= LAST else LAST
    p = px.asof(d)
    state.append(dict(year=y, asof=d.date(), price=p, above_200dma=bool(p > ma200.asof(d)), pct_vs_200dma=p / ma200.asof(d) - 1,
                      trailing_12m=p / px.asof(d - pd.DateOffset(years=1)) - 1, drawdown_from_ath=p / ath.asof(d) - 1,
                      ytd=p / px.asof(pd.Timestamp(f"{y-1}-12-31")) - 1, cycle_year=cycle_year(y),
                      oct=heat.loc[y, "Oct"] if y in heat.index and "Oct" in heat.columns else np.nan,
                      nov=heat.loc[y, "Nov"] if y in heat.index else np.nan,
                      q4=win.loc[y, "Q4"] if y in win.index else np.nan))
st = pd.DataFrame(state); st.to_csv(R / "sept30_state_vs_q4.csv", index=False, float_format="%.4f")
hist = st[st.year < LAST.year]
def cond(mask, name):
    s = hist[mask]
    return {name: dict(n=int(len(s)), years=[int(v) for v in s.year], oct_mean=float(s.oct.mean()), oct_hit=float((s.oct > 0).mean()),
                       nov_mean=float(s.nov.mean()), nov_hit=float((s.nov > 0).mean()), q4_mean=float(s.q4.mean()), q4_median=float(s.q4.median()), q4_hit=float((s.q4 > 0).mean()))}
cond_tbl = {}
cond_tbl.update(cond(hist.above_200dma, "above_200dma_on_sep30"))
cond_tbl.update(cond(~hist.above_200dma, "below_200dma_on_sep30"))
cond_tbl.update(cond(hist.trailing_12m > 0, "trailing_12m_positive"))
cond_tbl.update(cond(hist.trailing_12m <= 0, "trailing_12m_negative"))
cond_tbl.update(cond(hist.drawdown_from_ath < -0.30, "drawdown_worse_than_30pct"))
cond_tbl.update(cond(hist.drawdown_from_ath >= -0.30, "drawdown_better_than_30pct"))
cond_tbl.update(cond(hist.ytd < 0, "ytd_negative_on_sep30"))
cond_tbl.update(cond(hist.ytd >= 0, "ytd_positive_on_sep30"))
summary["conditioning"] = cond_tbl
summary["state_2026"] = st[st.year == LAST.year].drop(columns=["oct", "nov", "q4"]).iloc[0].apply(lambda v: v.item() if hasattr(v, "item") else str(v) if isinstance(v, (pd.Timestamp,)) else v).to_dict()
summary["state_2026"]["asof"] = str(summary["state_2026"]["asof"])

# ----------------------------------------------------------------------------- ETH cross-check
em = eth.resample("ME").last().pct_change().dropna(); em = em[(em.index >= "2016-01-31") & (em.index <= complete.index[-1])]
et = pd.DataFrame({"ret": em, "month": em.index.month}).groupby("month")["ret"].agg(["mean", "median", "count", lambda s: (s > 0).mean()])
et.columns = ["mean", "median", "n", "hit"]; et.index = MONTHS
et.to_csv(R / "eth_month_stats_2016_2025.csv", float_format="%.4f")

# ----------------------------------------------------------------------------- S&P 500 seasonality context (Shiller monthly averages)
sp = pd.read_csv(D / "raw_sp500_monthly_shiller.csv", parse_dates=["Date"]).set_index("Date")["SP500"]
spr = sp.pct_change().dropna(); spr = spr[spr.index >= "1950-01-01"]
spt = pd.DataFrame({"ret": spr, "month": spr.index.month}).groupby("month")["ret"].agg(["mean", "median", "count", lambda s: (s > 0).mean()])
spt.columns = ["mean", "median", "n", "hit"]; spt.index = MONTHS
spt.to_csv(R / "sp500_month_stats_1950_2026.csv", float_format="%.4f")

# ----------------------------------------------------------------------------- which periodicity? (2/3/4/5/6-year groupings)
from scipy.signal import lombscargle
ann = np.log(m_close.resample("YE").last()).diff().dropna()
ann = ann[(ann.index.year >= 2012) & (ann.index.year <= LAST.year - 1)]  # 2012+ so every year has a clean halving phase
yrs_a = ann.index.year.values; v = ann.values
def r2_groups(vals, labels):
    gm = pd.Series(vals).groupby(labels).transform("mean").values
    return 1 - ((vals - gm) ** 2).sum() / ((vals - vals.mean()) ** 2).sum()
per = {}
for P in [2, 3, 4, 5, 6]:
    lab = yrs_a % P
    obs = r2_groups(v, lab)
    perm = np.array([r2_groups(v, rng.permutation(lab)) for _ in range(NBOOT // 2)])
    k = P
    adj = 1 - (1 - obs) * (len(v) - 1) / max(len(v) - k, 1)
    per[f"{P}y"] = dict(r2=float(obs), adj_r2=float(adj), p_perm=float((perm >= obs).mean()), n_years=int(len(v)),
                        group_means={int(g): float(np.expm1(v[lab == g].mean())) for g in sorted(set(lab))})
summary["periodicity_annual_returns"] = per
# Lomb-Scargle periodogram of detrended log price (monthly, 2011..)
lp = np.log(m_close[m_close.index >= "2011-01-31"]).values
t = np.arange(len(lp), dtype=float)
detr = lp - np.polyval(np.polyfit(t, lp, 1), t)
periods = np.arange(6, 97, 1.0)
pgram = lombscargle(t, detr - detr.mean(), 2 * np.pi / periods, normalize=True)
top = periods[np.argsort(pgram)[::-1][:5]]
summary["periodogram_top_periods_months"] = [float(x) for x in top]
pd.DataFrame({"period_months": periods, "power": pgram}).to_csv(R / "periodogram_detrended_logprice.csv", index=False, float_format="%.5f")

# ----------------------------------------------------------------------------- key headline numbers
oct_ = mt[mt.month == 10]; nov_ = mt[mt.month == 11]
summary["headline"] = dict(
    oct_hit_2013_2025=f"{int((oct_[oct_.year>=2013].ret>0).sum())}/{int((oct_.year>=2013).sum())}",
    nov_hit_2013_2025=f"{int((nov_[nov_.year>=2013].ret>0).sum())}/{int((nov_.year>=2013).sum())}",
    oct_median_2013_2025=float(oct_[oct_.year >= 2013].ret.median()), nov_median_2013_2025=float(nov_[nov_.year >= 2013].ret.median()),
    q4_by_year={int(y): (None if pd.isna(v) else float(v)) for y, v in win["Q4"].items()},
    octnov_by_year={int(y): (None if pd.isna(v) else float(v)) for y, v in win["OctNov"].items()},
    best_month_by_median_2013=str(ms_13["median"].idxmax()), best_month_by_mean_2013=str(ms_13["mean"].idxmax()),
    worst_month_by_median_2013=str(ms_13["median"].idxmin()),
)
summary["cycles"] = [{k: (str(v) if not isinstance(v, (int, float, bool, type(None))) else v) for k, v in c.items()} for c in cycles]
summary["realized_vol_by_month"] = {k: float(v) for k, v in vol.items()}
json.dump(summary, open(R / "summary.json", "w"), indent=2, default=str)
print(json.dumps(summary, indent=1, default=str)[:20000])
