#!/usr/bin/env python3
"""Charts for the Bitcoin seasonality / cycle / Fed analysis (reads results/ and data/)."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import os
THEME = os.environ.get("CHART_THEME", "light")
D, R = ROOT / "data", ROOT / "results"
C = ROOT / ("charts" if THEME == "light" else "charts_dark")
C.mkdir(exist_ok=True)

# palettes: the dataviz reference instance (light) and its dark-surface steps, on the report's ink-green ground
PALETTES = {
    "light": dict(SURF="#fcfcfb", INK="#0b0b0b", INK2="#52514e", MUTED="#8a8983", GRID="#e6e5e1",
                  S1="#2a78d6", S2="#eb6834", S3="#1baf7a", S4="#eda100", DIV_NEG="#e34948", DIV_MID="#f0efec", DIV_POS="#2a78d6",
                  BAR_GRAY="#c9c8c3", SPAN_ALPHA=0.10, Q4SPAN="#e6e5e1", Q4ALPHA=0.5,
                  TINT={"ZIRP": "#e3efe9", "ZIRP/QE": "#e3efe9", "Hiking": "#fbe3da", "Hold": "#fcfcfb", "Cut": "#dbe9f9"}),
    "dark": dict(SURF="#0B1411", INK="#ECE8DE", INK2="#C9C5B9", MUTED="#8C988E", GRID="#26332D",
                 S1="#3987e5", S2="#d95926", S3="#199e70", S4="#c98500", DIV_NEG="#e66767", DIV_MID="#343f39", DIV_POS="#3987e5",
                 BAR_GRAY="#3b4842", SPAN_ALPHA=0.20, Q4SPAN="#ECE8DE", Q4ALPHA=0.07,
                 TINT={"ZIRP": "#1F6E5259", "ZIRP/QE": "#1F6E5259", "Hiking": "#B23A3A59", "Hold": "#0B1411", "Cut": "#2a78d659"}),
}
P = PALETTES[THEME]
SURF, INK, INK2, MUTED, GRID = P["SURF"], P["INK"], P["INK2"], P["MUTED"], P["GRID"]
S1, S2, S3, S4 = P["S1"], P["S2"], P["S3"], P["S4"]
DIV_NEG, DIV_MID, DIV_POS = P["DIV_NEG"], P["DIV_MID"], P["DIV_POS"]
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.linewidth": 1, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 1,
    "axes.spines.top": False, "axes.spines.right": False, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "semibold",
    "axes.titlelocation": "left", "legend.frameon": False, "figure.dpi": 100,
})
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
S = json.load(open(R / "summary.json"))
px = pd.read_csv(D / "btc_daily.csv", parse_dates=["date"]).set_index("date")["close"]
LAST = px.index.max()


def save(fig, name):
    fig.savefig(C / name, dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


# 1. heatmap of monthly returns ------------------------------------------------------------
heat = pd.read_csv(R / "monthly_returns_heatmap.csv", index_col=0) * 100
cmap = LinearSegmentedColormap.from_list("div", [DIV_NEG, DIV_MID, DIV_POS])
fig, ax = plt.subplots(figsize=(11, 7.2))
vals = heat.values.astype(float)
clipped = np.clip(vals, -50, 50)
ax.imshow(clipped, cmap=cmap, norm=TwoSlopeNorm(vmin=-50, vcenter=0, vmax=50), aspect="auto")
ax.set_xticks(range(12)); ax.set_xticklabels(MONTHS); ax.set_yticks(range(len(heat.index))); ax.set_yticklabels(heat.index)
ax.tick_params(length=0); ax.grid(False)
for i in range(vals.shape[0]):
    for j in range(vals.shape[1]):
        v = vals[i, j]
        if np.isnan(v):
            continue
        dark = abs(clipped[i, j]) > 28
        txt = f"{v:+.0f}" if abs(v) < 100 else f"{v:+.0f}"
        ax.text(j, i, txt, ha="center", va="center", fontsize=8.5, color=("white" if dark else INK) if THEME == "light" else INK)
# white 2px gaps between cells
for k in range(13):
    ax.axvline(k - 0.5, color=SURF, lw=2)
for k in range(len(heat.index) + 1):
    ax.axhline(k - 0.5, color=SURF, lw=2)
part = S.get("partial_month")
sub = "Color clipped at ±50%. Oct: 10 of 13 positive since 2013. Nov: 8 of 13, but its mean is one outlier (Nov 2013 +451%)."
if part:
    sub += f"  {part['month']} is month-to-date (through {S['data_last_date']})."
fig.suptitle("Bitcoin monthly returns, % (2011 – Sep 2026)", x=0.125, y=0.955, ha="left", fontsize=12, fontweight="bold")
ax.set_title(sub, fontsize=9, color=INK2, fontweight="normal", pad=8)
save(fig, "01_monthly_returns_heatmap.png")

# 2. month stats: median with bootstrap CI + hit rate ----------------------------------------
ms = pd.read_csv(R / "month_stats_2013_2025.csv", index_col=0)
fig, ax = plt.subplots(figsize=(10, 5.2))
x = np.arange(12)
colors = [S1 if m in ("Oct", "Nov") else P["BAR_GRAY"] for m in ms.index]
ax.bar(x, ms["median"] * 100, width=0.62, color=colors, zorder=3)
ax.errorbar(x, ms["median"] * 100, yerr=[(ms["median"] - ms["median_ci_lo"]) * 100, (ms["median_ci_hi"] - ms["median"]) * 100],
            fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3, zorder=4)
ax.axhline(0, color=INK2, lw=1)
ax.set_xticks(x); ax.set_xticklabels(ms.index); ax.set_ylabel("Median monthly return, % (bootstrap 95% CI)")
for i, m in enumerate(ms.index):
    ax.text(i, ms.loc[m, "median_ci_hi"] * 100 + 1.5, f"{ms.loc[m, 'hit_rate']*100:.0f}%", ha="center", fontsize=8.5, color=INK2)
ax.set_title("Median return by calendar month, 2013 – 2025 (labels: share of years positive)")
ax.set_ylim(-20, 42)
save(fig, "02_month_medians_ci.png")

# 3. Oct / Nov / Dec by halving-cycle year -------------------------------------------------
cy = pd.read_csv(R / "month_stats_by_cycle_year.csv")
heat_y = pd.read_csv(R / "monthly_returns_heatmap.csv", index_col=0)
cyc_map = {2012: 0, 2013: 1, 2014: 2, 2015: 3, 2016: 0, 2017: 1, 2018: 2, 2019: 3, 2020: 0, 2021: 1, 2022: 2, 2023: 3, 2024: 0, 2025: 1}
labels = ["Halving year\n(2012, 16, 20, 24)", "Year after\n(2013, 17, 21, 25)", "Two years after\n(2014, 18, 22 → 2026)", "Three years after\n(2015, 19, 23)"]
fig, ax = plt.subplots(figsize=(10.5, 5.4))
w = 0.24
for k, (mo, col) in enumerate([("Oct", S1), ("Nov", S2), ("Dec", S3)]):
    meds = [cy[(cy.cycle_year == c) & (cy.month == mo)]["median"].iloc[0] * 100 for c in range(4)]
    ax.bar(np.arange(4) + (k - 1) * w, meds, width=w - 0.03, color=col, label=f"{mo} (median)", zorder=3)
    for c in range(4):
        ys = [heat_y.loc[y, mo] * 100 for y in heat_y.index if cyc_map.get(y) == c and not np.isnan(heat_y.loc[y, mo])]
        ax.scatter(np.full(len(ys), c + (k - 1) * w), np.clip(ys, -60, 80), s=22, color=col, edgecolor=SURF, linewidth=1.5, zorder=4)
ax.axhline(0, color=INK2, lw=1)
ax.set_xticks(range(4)); ax.set_xticklabels(labels); ax.set_ylabel("Monthly return, % (dots = individual years, clipped at +80)")
ax.set_ylim(-60, 85); ax.legend(loc="upper right", ncol=3)
ax.set_title("The Q4 effect lives in halving years and the year after — 'two years after' (2026's phase) has been negative")
save(fig, "03_q4_months_by_cycle_year.png")

# 4. Q4 return by year, colored by cycle phase ---------------------------------------------
win = pd.read_csv(R / "window_returns_by_year.csv", index_col=0)
win = win[win.index >= 2012].dropna(subset=["Q4"])
phase_col = {0: S1, 1: S2, 2: DIV_NEG, 3: S3}
phase_lab = {0: "Halving year", 1: "Year after halving", 2: "Two years after (bear phase)", 3: "Three years after (recovery)"}
fig, ax = plt.subplots(figsize=(10.5, 5))
vals = np.clip(win["Q4"] * 100, -60, 120)
ax.bar(win.index.astype(str), vals, color=[phase_col[cyc_map[y]] for y in win.index], width=0.62, zorder=3)
for y, v, full in zip(win.index.astype(str), vals, win["Q4"] * 100):
    ax.text(y, v + (3 if v >= 0 else -9), f"{full:+.0f}%", ha="center", fontsize=8.5, color=INK2)
ax.axhline(0, color=INK2, lw=1); ax.set_ylim(-70, 135); ax.set_ylabel("Oct 1 – Dec 31 return, % (bars clipped at +120)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=phase_col[k], label=phase_lab[k]) for k in range(4)], loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4, fontsize=9)
ax.set_title("Fourth-quarter return by year and halving-cycle phase")
save(fig, "04_q4_return_by_year.png")

# 5. halving-aligned paths --------------------------------------------------------------------
paths = pd.read_csv(R / "halving_aligned_paths.csv", index_col=0)
fig, ax = plt.subplots(figsize=(10.5, 5.6))
cols = {"2012": S4, "2016": S3, "2020": S2, "2024": S1}
for k in ["2012", "2016", "2020", "2024"]:
    s = paths[k].dropna(); s = s[s.index <= 1460]
    ax.plot(s.index, s.values, lw=2 if k == "2024" else 1.6, color=cols[k], label=f"{k} halving", solid_capstyle="round")
    ax.text(s.index[-1] + 15, s.values[-1], f"{k}", color=INK2, fontsize=9, va="center")
ax.set_yscale("log"); ax.set_xlabel("Days since halving"); ax.set_ylabel("Price ÷ price on halving day (log scale)")
cur = (LAST - pd.Timestamp("2024-04-20")).days
ax.axvline(cur, color=INK2, lw=1); ax.text(cur + 12, 0.72, f"now: day {cur}", color=INK2, fontsize=9)
ax.legend(loc="upper left")
ax.set_title("Each cycle, aligned on its halving: peaks landed 371 / 525 / 546 / 534 days after the halving")
save(fig, "05_halving_aligned_paths.png")

# 6. peak-aligned drawdown analogs ------------------------------------------------------------
pp = pd.read_csv(R / "peak_aligned_paths.csv", index_col=0)
fig, ax = plt.subplots(figsize=(10.5, 5.6))
cols = {"2013": S4, "2017": S3, "2021": S2, "2025": S1}
for k in ["2013", "2017", "2021", "2025"]:
    s = pp[k].dropna(); s = s[s.index <= 480]
    ax.plot(s.index, s.values * 100, lw=2.2 if k == "2025" else 1.6, color=cols[k], label=f"{k} peak")
    ax.text(s.index[-1] + 6, s.values[-1] * 100, k, color=INK2, fontsize=9, va="center")
d = S["peak_analog"]["days_since_2025_peak"]
ax.axvspan(364, 406, color=DIV_NEG, alpha=P["SPAN_ALPHA"], lw=0)
ax.text(385, 96, "prior cycle lows:\nday 364–406 after peak", ha="center", fontsize=8.5, color=INK2)
ax.axvline(d, color=INK2, lw=1); ax.text(d - 6, 88, f"now: day {d}", ha="right", fontsize=9, color=INK2)
ax.set_xlabel("Days since cycle peak"); ax.set_ylabel("Price as % of cycle peak"); ax.set_ylim(0, 105)
ax.legend(loc="upper right")
ax.set_title("Bear phases aligned on the cycle peak: this one is far shallower, but the calendar window for prior lows is Oct–Nov 2026")
save(fig, "06_peak_aligned_drawdowns.png")

# 7. Fed regimes vs BTC (two stacked panels, one axis each) ----------------------------------
fed = pd.read_csv(D / "fed_policy_changes.csv", parse_dates=["date"])
ub = fed.set_index("date")["target_upper"].reindex(pd.date_range("2013-01-01", LAST)).ffill().fillna(0.25)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.2], "hspace": 0.08})
p = px[px.index >= "2013-01-01"]
a1.plot(p.index, p.values, color=S1, lw=1.6); a1.set_yscale("log"); a1.set_ylabel("BTC, USD (log)")
regimes = [("2013-01-01", "2015-12-16", "ZIRP"), ("2015-12-16", "2018-12-20", "Hiking"), ("2018-12-20", "2019-07-31", "Hold"),
           ("2019-07-31", "2019-10-31", "Cut"), ("2019-10-31", "2020-03-03", "Hold"), ("2020-03-03", "2022-03-16", "ZIRP/QE"),
           ("2022-03-16", "2023-07-27", "Hiking"), ("2023-07-27", "2024-09-18", "Hold"), ("2024-09-18", "2024-12-19", "Cut"),
           ("2024-12-19", "2025-09-17", "Hold"), ("2025-09-17", "2025-12-11", "Cut"), ("2025-12-11", "2026-09-16", "Hold"),
           ("2026-09-16", str(LAST.date()), "Hiking")]
tint = P["TINT"]
for s0, s1, lab in regimes:
    a1.axvspan(pd.Timestamp(s0), pd.Timestamp(s1), color=tint[lab], lw=0, zorder=0)
    if lab != "Hold":
        a1.text(pd.Timestamp(s0) + (pd.Timestamp(s1) - pd.Timestamp(s0)) / 2, 150, lab, ha="center", fontsize=8, color=INK2)
for h in ["2016-07-09", "2020-05-11", "2024-04-20"]:
    a1.axvline(pd.Timestamp(h), color=S2, lw=1, ls=(0, (4, 3))); a1.text(pd.Timestamp(h), 22, " halving", color=S2, fontsize=8)
a1.set_title("Bitcoin vs. Fed policy regime (shading: green = zero rates/QE, red = hiking, blue = cutting) — no regime owns the cycle")
a2.step(ub.index, ub.values, where="post", color=INK2, lw=1.6); a2.set_ylabel("Fed funds target\nupper bound, %"); a2.set_ylim(0, 6)
save(fig, "07_btc_vs_fed_regimes.png")

# 8. realized volatility by month -------------------------------------------------------------
vol = pd.read_csv(R / "realized_vol_by_month.csv", index_col=0).iloc[:, 0] * 100
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.bar(range(12), vol.values, color=[S1 if m in ("Nov", "Dec") else P["BAR_GRAY"] for m in vol.index], width=0.62, zorder=3)
ax.set_xticks(range(12)); ax.set_xticklabels(vol.index); ax.set_ylabel("Annualized realized volatility, %")
ax.set_title("October is the calmest month; November–December are where the big moves (both directions) happen (2013 – 2026)")
save(fig, "08_realized_vol_by_month.png")

# 9. 2026 path vs prior 'two years after' analogs (Jan 1 = 100) ------------------------------
fig, ax = plt.subplots(figsize=(10.5, 5.4))
cols = {2014: S4, 2018: S3, 2022: S2, 2026: S1}
for y in [2014, 2018, 2022, 2026]:
    s = px[(px.index >= f"{y}-01-01") & (px.index <= f"{y}-12-31")]
    base = px.asof(pd.Timestamp(f"{y-1}-12-31"))
    rel = s / base * 100; doy = (s.index - pd.Timestamp(f"{y}-01-01")).days
    ax.plot(doy, rel.values, color=cols[y], lw=2.2 if y == 2026 else 1.6, label=str(y))
    ax.text(doy[-1] + 4, rel.values[-1], str(y), color=INK2, fontsize=9, va="center")
ax.axvspan(273, 365, color=P["Q4SPAN"], alpha=P["Q4ALPHA"], lw=0); ax.text(319, 178, "Q4", ha="center", color=INK2, fontsize=9)
ax.set_xlabel("Day of year"); ax.set_ylabel("Price, indexed to prior year-end = 100"); ax.set_ylim(0, 190)
ax.legend(loc="upper left", title="Two years after a halving")
ax.set_title("2026 against the three prior 'two years after halving' years: the same phase, a milder version")
save(fig, "09_2026_vs_bear_phase_analogs.png")
print("charts written:", sorted(p.name for p in C.glob("*.png")))
