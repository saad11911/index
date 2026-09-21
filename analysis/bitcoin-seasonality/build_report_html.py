#!/usr/bin/env python3
"""Assemble report.html (self-contained: charts embedded as data URIs) from the analysis outputs."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import os
THEME = os.environ.get("THEME", "dark")
C = ROOT / os.environ.get("CHART_DIR", "charts_dark" if THEME == "dark" else "charts")
OUT_FILE = ROOT / os.environ.get("REPORT_OUT", "report.html")

def img(name, alt, caption):
    b = base64.b64encode((C / name).read_bytes()).decode()
    return f'<figure><img src="data:image/png;base64,{b}" alt="{alt}" loading="lazy"><figcaption>{caption}</figcaption></figure>'

HEAD = """<title>Bitcoin's Fourth Quarter</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Hanken+Grotesk:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{color-scheme:dark;
  --ground:#0B1411;--panel:#12241D;--ink:#ECE8DE;--ink-2:#D5D1C6;--muted:#8C988E;--line:rgba(194,160,99,.26);--line-soft:rgba(236,232,222,.09);
  --accent:#C2A063;--accent-soft:rgba(194,160,99,.14);--neg:#E07070;--pos:#5FBF95;--plate:#0B1411;
  --serif:"Fraunces",Georgia,"Times New Roman",serif;--sans:"Hanken Grotesk",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:900px;margin:0 auto;padding-block:40px 64px;padding-inline:20px}
.prose{max-width:68ch}
.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 14px}
h1{font-family:var(--serif);font-weight:500;font-size:clamp(38px,6vw,60px);line-height:1.04;letter-spacing:-.01em;margin:0 0 18px;text-wrap:balance;font-variation-settings:"opsz" 144}
h2{font-family:var(--serif);font-weight:500;font-size:clamp(26px,3.6vw,34px);line-height:1.15;margin:0 0 14px;text-wrap:balance}
h3{font-family:var(--sans);font-weight:600;font-size:17px;margin:28px 0 8px}
p{margin:0 0 16px}
.stand{font-size:20px;line-height:1.5;color:var(--ink-2);max-width:62ch}
.asof{color:var(--muted);font-size:14px;margin-top:22px;padding-top:14px;border-top:1px solid var(--line)}
section{margin-top:64px;padding-top:28px;border-top:1px solid var(--line)}
.findings{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:18px}
.findings li{padding-left:22px;position:relative}
.findings li::before{content:"";position:absolute;left:0;top:.62em;width:9px;height:9px;border-radius:50%;background:var(--accent)}
.findings b{font-weight:600;color:var(--ink)}
.ledger{margin:30px 0 6px;border-top:1px solid var(--line)}
.ledger .row{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:baseline;padding:12px 0;border-bottom:1px solid var(--line-soft)}
.ledger .row span{color:var(--ink-2)}
.ledger .row em{font-family:var(--serif);font-style:normal;font-weight:500;font-size:28px;color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap}
.note{font-size:14px;color:var(--muted)}
figure{margin:28px 0}
figure img{display:block;width:100%;max-width:100%;height:auto;background:var(--plate);border:1px solid var(--line);border-radius:4px}
.mark{display:flex;align-items:baseline;gap:11px;color:var(--ink);text-decoration:none}
.mark .glyph{font-family:var(--serif);font-weight:600;font-size:23px;letter-spacing:.02em;color:var(--accent)}
.mark .lbl{font-size:12px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted);font-weight:500}
.topbar{display:flex;justify-content:space-between;align-items:baseline;gap:16px;padding-bottom:22px;margin-bottom:34px;border-bottom:1px solid var(--line)}
.topbar .site{font-size:13px;color:var(--muted);letter-spacing:.04em}
figcaption{font-size:14px;color:var(--muted);margin-top:8px;max-width:75ch}
.tbl{overflow-x:auto;margin:18px 0 22px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:14.5px;font-variant-numeric:tabular-nums;min-width:520px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line-soft);text-align:right;vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:12.5px;letter-spacing:.04em;text-transform:uppercase;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
td.hl,tr.hl td{background:var(--accent-soft);font-weight:600}
.neg{color:var(--neg)}.pos{color:var(--pos)}
.scen{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:26px}
.scen>div{border-top:2px solid var(--accent);padding-top:14px}
.scen h3{margin:0 0 4px;font-family:var(--serif);font-weight:500;font-size:22px}
.scen .p{font-family:var(--serif);font-size:40px;font-weight:500;line-height:1;margin:6px 0 12px;color:var(--ink)}
.scen p{font-size:15px;color:var(--ink-2);margin-bottom:10px}
.levels{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;margin:16px 0;font-size:15.5px}
.levels em{font-style:normal;font-family:var(--serif);font-size:20px;font-weight:500;font-variant-numeric:tabular-nums;white-space:nowrap}
.caveats{padding-left:20px}.caveats li{margin-bottom:10px}
footer{margin-top:64px;padding-top:24px;border-top:1px solid var(--line);font-size:14px;color:var(--muted)}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;background:var(--accent-soft);padding:1px 5px;border-radius:3px}
a{color:var(--accent)}
@media (max-width:720px){.scen{grid-template-columns:1fr}.ledger .row em{font-size:24px}body{font-size:16px}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
</style>
"""

BODY = f"""
<div class="wrap">
<div class="topbar"><a class="mark" href="https://19kholdings.com"><span class="glyph">19K</span><span class="lbl">Holdings</span></a><span class="site">19kholdings.com</span></div>
<header>
<p class="eyebrow">Research note · 21 September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="stand">"Uptober" is real but small, November is mostly a legend, the Fed is not the driver, and the pattern people are trading is a four‑year halving cycle wearing a calendar costume. Here is what fifteen years of daily prices actually say, and what they imply for October–December 2026.</p>
<p class="asof">Daily prices 18 July 2010 – 15 September 2026 (last close $75,686; spot about $78,000 on 18 September). Fed funds target 3.75–4.00% after the 16 September hike. All statistics reproducible from the accompanying code and data. This is a data study, not investment advice.</p>
</header>

<section id="verdict">
<p class="eyebrow">The verdict</p>
<h2>Six things the record shows</h2>
<ul class="findings prose">
<li><b>October's edge is real but modest; November's is mostly one year.</b> Since 2013 October closed higher in 10 of 13 years, median +14.8% (bootstrap 95% interval +5% to +33%). November was positive in only 8 of 13; its famous +41% average is November 2013 (+451%). Without that year November's median is about +8% with a 7‑of‑12 hit rate. December's median is negative (−3.4%).</li>
<li><b>The pattern is a halving‑cycle effect.</b> Three of four cycle peaks landed in Q4 of the year after a halving (Dec 2013, Dec 2017, Nov 2021) and the fourth on 6 October 2025. Remove those years and October's mean falls from +20% to +6% (median +10%); November's from +41% to +5%.</li>
<li><b>The timeline that matters is four years.</b> Grouping annual returns by position in a 4‑year cycle explains 56% of their variance (adjusted R² 0.42, permutation p = 0.03). Two‑, three‑, five‑ and six‑year groupings explain nothing (p = 0.13, 0.71, 0.96, 0.71). A periodogram of the detrended price peaks at 44 months.</li>
<li><b>The Fed is not the driver.</b> Bitcoin's 12‑month return has a −0.05 correlation with the 12‑month change in the policy rate. In the 21 days after a rate cut the median Bitcoin return was −5.7% (11 cuts); after a hike, −2.6% (20 hikes). Big Q4s happened under zero rates (2013, 2020), under hiking (2017) and under cutting (2024). Q4 2019 and Q4 2025 fell while the Fed was cutting.</li>
<li><b>2026 is in the phase that has been Bitcoin's worst.</b> 2026 is "two years after a halving", like 2014, 2018 and 2022. In those years Q4 returned −18%, −44% and −15%; November was negative in two of three and December in all three. Prior cycle lows came 364–406 days after the peak; from the 6 October 2025 peak that window is 5 October – 16 November 2026.</li>
<li><b>But this cycle is milder, and price enters Q4 in better shape than any prior year‑two.</b> The drawdown so far is −53% (June low $58,654) against −77%, −84% and −85% before. Price sits 7.7% above its 200‑day average after a +25% August, something no earlier year‑two had on 30 September. The realistic expectation is a near coin‑flip quarter with two‑sided November risk, and a cycle low that is either already in or gets retested in the October–November window.</li>
</ul>

<h3>Odds for Q4 2026</h3>
<p class="note prose">Judgment informed by the base rates below, not a model output. Reference prices: June low $58,654; 2025 close $87,517; cycle peak $124,824 (daily closes).</p>
<div class="ledger">
<div class="row"><span>October closes above its 30 September close</span><em>~60%</em></div>
<div class="row"><span>October + November combined positive</span><em>~50%</em></div>
<div class="row"><span>Full quarter (1 Oct – 31 Dec) positive</span><em>~45%</em></div>
<div class="row"><span>A daily close below the June low at some point in Q4</span><em>~30%</em></div>
<div class="row"><span>Year‑end close above $87,517 (2026 finishes up)</span><em>~25%</em></div>
<div class="row"><span>New all‑time high before year‑end</span><em>&lt;5%</em></div>
</div>
<p class="prose" style="margin-top:18px">The most useful single sentence in the record: in every prior cycle the strong, low‑risk part of the pattern began in the <b>third</b> year after the halving (2015 +34%, 2019 +94%, 2023 +156%), after a Q4‑or‑January low in year two. If the template holds even in dampened form, the interesting window is weakness between mid‑October 2026 and January 2027, not "buy on 1 October".</p>
</section>

<section id="seasonal">
<p class="eyebrow">Part 1</p>
<h2>Is the seasonal pattern real?</h2>
{img("01_monthly_returns_heatmap.png", "Heatmap of Bitcoin monthly returns by year and month, 2011 to September 2026", "Monthly returns, 2011 – Sep 2026. Blue positive, red negative, color clipped at ±50%. September 2026 is month‑to‑date.")}
{img("02_month_medians_ci.png", "Bar chart of median return by calendar month with bootstrap confidence intervals and hit rates", "Median return by calendar month, 2013 – 2025, with bootstrap 95% intervals. Labels give the share of years the month was positive. October is the only month whose interval excludes zero.")}
<div class="tbl"><table>
<thead><tr><th>Month</th><th>n</th><th>Mean</th><th>Median</th><th>Positive</th><th>t‑test p</th><th>Wilcoxon p</th><th>Median 95% CI</th></tr></thead>
<tbody>
<tr><td>Jan</td><td>14</td><td>+3.4%</td><td>+0.4%</td><td>50%</td><td>0.91</td><td>0.81</td><td>−14% … +14%</td></tr>
<tr><td>Feb</td><td>14</td><td>+11.2%</td><td>+11.7%</td><td>71%</td><td>0.22</td><td>0.14</td><td>−7% … +23%</td></tr>
<tr><td>Mar</td><td>14</td><td>+12.2%</td><td>−0.1%</td><td>50%</td><td>0.58</td><td>0.86</td><td>−9% … +16%</td></tr>
<tr><td>Apr</td><td>14</td><td>+12.2%</td><td>+10.0%</td><td>64%</td><td>0.05</td><td>0.08</td><td>−2% … +29%</td></tr>
<tr><td>May</td><td>14</td><td>+9.0%</td><td>+3.1%</td><td>50%</td><td>0.46</td><td>0.43</td><td>−8% … +18%</td></tr>
<tr><td>Jun</td><td>14</td><td>−2.1%</td><td>−0.7%</td><td>50%</td><td>0.48</td><td>0.76</td><td>−14% … +12%</td></tr>
<tr><td>Jul</td><td>14</td><td>+7.9%</td><td>+8.0%</td><td>71%</td><td>0.03</td><td>0.03</td><td>−2% … +19%</td></tr>
<tr><td>Aug</td><td>14</td><td>+2.7%</td><td>−7.4%</td><td>36%</td><td>0.92</td><td>0.81</td><td>−11% … +13%</td></tr>
<tr><td>Sep</td><td>13</td><td>−3.2%</td><td>−2.9%</td><td>38%</td><td>0.16</td><td>0.22</td><td>−8% … +4%</td></tr>
<tr class="hl"><td>Oct</td><td>13</td><td>+20.0%</td><td>+14.8%</td><td>77%</td><td>0.007</td><td>0.008</td><td>+5% … +33%</td></tr>
<tr><td>Nov</td><td>13</td><td>+41.4%</td><td>+8.9%</td><td>62%</td><td>0.28</td><td>0.27</td><td>−16% … +37%</td></tr>
<tr><td>Dec</td><td>13</td><td>+4.0%</td><td>−3.4%</td><td>38%</td><td>0.82</td><td>0.89</td><td>−7% … +14%</td></tr>
</tbody></table></div>
<div class="prose">
<p><b>What survives scrutiny.</b> October's single‑test p‑value is 0.007, but "is October special?" involves twelve looks at the data; a max‑|t| permutation test that accounts for that gives a family‑wise p of 0.11. Suggestive, not proof. Start the sample in 2011 rather than 2013 (adding October 2011 at −37% and October 2012 at −10%) and October's median drops to +11% with a 67% hit rate. The effect is real‑looking and fragile to two data points.</p>
<p><b>November is not distinguishable from zero on any test</b>, and it is the second most volatile month of the year (annualized realized volatility 86%, against 56% in October). November is where the big moves happen in both directions: +451%, +56%, +42%, +37% but also −37%, −18%, −16%, −17%.</p>
<p><b>October is the calmest month.</b> Realized volatility bottoms in September–October and jumps in November–December. "Uptober" has historically been a low‑volatility drift, not a blow‑off. July (71% positive, p = 0.03) is the second‑best month and gets none of the attention; April is third.</p>
<p><b>Cross‑checks.</b> Ether (2016–2025) shows almost no October effect (median +1.3%, 60% positive; November median −4.2%), so this is not a generic crypto calendar. The S&amp;P 500's October mean since 1950 is −0.06%; the equity seasonal is November–January and April, so Bitcoin's October is not inherited from stocks.</p>
</div>
{img("08_realized_vol_by_month.png", "Bar chart of annualized realized volatility by calendar month", "Annualized realized volatility of daily returns by calendar month, 2013 – 2026.")}
</section>

<section id="timeline">
<p class="eyebrow">Part 2</p>
<h2>Two, three, four or five years?</h2>
<p class="prose">Annual returns were grouped by their position in a 2‑, 3‑, 4‑, 5‑ and 6‑year cycle and the share of variance each grouping explains was tested against 10,000 random relabelings (2012–2025, the years with a clean halving phase).</p>
<div class="tbl"><table>
<thead><tr><th>Grouping</th><th>R²</th><th>Adjusted R²</th><th>Permutation p</th></tr></thead>
<tbody>
<tr><td>2‑year</td><td>0.18</td><td>0.11</td><td>0.13</td></tr>
<tr><td>3‑year</td><td>0.06</td><td>−0.11</td><td>0.71</td></tr>
<tr class="hl"><td>4‑year (halving cycle)</td><td>0.56</td><td>0.42</td><td>0.032</td></tr>
<tr><td>5‑year</td><td>0.07</td><td>−0.35</td><td>0.96</td></tr>
<tr><td>6‑year</td><td>0.28</td><td>−0.17</td><td>0.71</td></tr>
</tbody></table></div>
<p class="prose">Geometric‑average annual return by phase: halving year +176%, year after +483%, <b>two years after −65%</b>, three years after +88%. The weak 2‑year signal is an alias of the 4‑year one (odd vs even years). A Lomb–Scargle periodogram of the detrended log price peaks at 44 months, with all five top periods between 42 and 46 months.</p>
</section>

<section id="cycle">
<p class="eyebrow">Part 3</p>
<h2>The halving cycle explains the calendar</h2>
<div class="tbl"><table>
<thead><tr><th>Halving</th><th>Price</th><th>Cycle peak</th><th>Days to peak</th><th>Gain</th><th>Cycle low</th><th>Days peak→low</th><th>Drawdown</th></tr></thead>
<tbody>
<tr><td>28 Nov 2012</td><td>$12.3</td><td>4 Dec 2013 · $1,135</td><td>371</td><td>91×</td><td>14 Jan 2015 · $176</td><td>406</td><td class="neg">−85%</td></tr>
<tr><td>9 Jul 2016</td><td>$652</td><td>16 Dec 2017 · $19,640</td><td>525</td><td>29×</td><td>15 Dec 2018 · $3,185</td><td>364</td><td class="neg">−84%</td></tr>
<tr><td>11 May 2020</td><td>$8,592</td><td>8 Nov 2021 · $67,542</td><td>546</td><td>6.9×</td><td>9 Nov 2022 · $15,758</td><td>366</td><td class="neg">−77%</td></tr>
<tr><td>20 Apr 2024</td><td>$64,908</td><td>6 Oct 2025 · $124,824</td><td>534</td><td>1.9×</td><td>30 Jun 2026 · $58,654 <span class="note">so far</span></td><td>267 <span class="note">so far</span></td><td class="neg">−53% <span class="note">so far</span></td></tr>
</tbody></table></div>
<p class="prose">Peaks arrive at a stable lag (525–546 days in the last three cycles) with collapsing amplitude (91× → 29× → 6.9× → 1.9×) and shallower busts. The cycle is dampening as the asset matures, which matters for the forecast.</p>
{img("05_halving_aligned_paths.png", "Four cycles aligned on their halving date, price relative to halving-day price on a log scale", "Each cycle aligned on its halving. The 2024 cycle is on day 878.")}
{img("03_q4_months_by_cycle_year.png", "Grouped bars of October, November and December median returns by halving-cycle phase, with individual years as dots", "October, November and December by cycle phase. Bars are medians; dots are individual years. The 'two years after' phase, where 2026 sits, has been negative in all three months.")}
<div class="tbl"><table>
<thead><tr><th>Phase</th><th>Oct median</th><th>Oct up</th><th>Nov median</th><th>Nov up</th><th>Dec median</th><th>Dec up</th><th>Q4 median</th><th>Q4 up</th></tr></thead>
<tbody>
<tr><td>Halving year (2012, 16, 20, 24)</td><td>+13.0%</td><td>3/4</td><td>+25.0%</td><td>4/4</td><td>+19.1%</td><td>3/4</td><td>+53%</td><td>4/4</td></tr>
<tr><td>Year after (2013, 17, 21, 25)</td><td>+44.3%</td><td>3/4</td><td>+24.2%</td><td>2/4</td><td>−11.1%</td><td>1/4</td><td>+114%</td><td>3/4</td></tr>
<tr class="hl"><td>Two years after (2014, 18, 22)</td><td>−4.5%</td><td>1/3</td><td>−16.2%</td><td>1/3</td><td>−7.2%</td><td>0/3</td><td>−18%</td><td>0/3</td></tr>
<tr><td>Three years after (2015, 19, 23)</td><td>+28.4%</td><td>3/3</td><td>+8.9%</td><td>2/3</td><td>+11.9%</td><td>2/3</td><td>+57%</td><td>2/3</td></tr>
</tbody></table></div>
{img("04_q4_return_by_year.png", "Bar chart of fourth-quarter return by year colored by halving-cycle phase", "Q4 return by year. The three 'two years after' quarters (2014, 2018, 2022) are the only phase with no positive outcome.")}
<div class="prose">
<p><b>Decomposing Uptober.</b> All years 2013–2025: October mean +20.0%, median +14.8%, 77% positive. Excluding the year after each halving: mean +6.1%, median +10.5%, 64% positive. Two years after a halving only: mean −4.2%, median −4.5%, 1 of 3 positive. Outside the blow‑off years October is an ordinary good month, on par with February, April and July; in 2026's phase it has leaned negative.</p>
<p><b>Why a calendar effect at all, once the cycle is removed?</b> Three candidates fit the data. Volatility seasonality: Q3 is the quietest quarter and when volatility re‑expands in Q4 it does so in the direction of the prevailing trend, which is why October was positive in 8 of 9 years that entered it up on the year but only 2 of 4 that entered it down. Reflexivity: "Uptober" became a meme around 2020–21 and a widely believed seasonal in a momentum market mildly self‑fulfils, consistent with a persistent ~+10% low‑volatility drift. Year‑end positioning in bear years: tax‑loss selling and redemptions make November–December the worst months of year‑two and give December a negative median overall. What does not fit: institutional year‑end allocations (December would be positive) and equity seasonality.</p>
</div>
</section>

<section id="fed">
<p class="eyebrow">Part 4</p>
<h2>The Fed, tested three ways</h2>
{img("07_btc_vs_fed_regimes.png", "Bitcoin log price with Fed policy regimes shaded, and the Fed funds target upper bound below", "Bitcoin against the Fed's policy regime since 2013. Green shading is zero rates or QE, red is a hiking cycle, blue is a cutting phase; dashed lines mark halvings.")}
<div class="tbl"><table>
<thead><tr><th>Regime</th><th>Months</th><th>Mean</th><th>Median</th><th>Positive</th><th>Ann. vol</th></tr></thead>
<tbody>
<tr><td>Zero rates / QE (2011–15, 2020–22)</td><td>83</td><td>+21.4%</td><td>+7.6%</td><td>58%</td><td>244%</td></tr>
<tr><td>Hiking cycle (2016–18, 2022–23, Sep 2026–)</td><td>52</td><td>+6.5%</td><td>+4.2%</td><td>56%</td><td>83%</td></tr>
<tr><td>Hold at peak rate (2019 H1, Aug 2023 – Sep 2024)</td><td>21</td><td>+9.8%</td><td>+8.0%</td><td>67%</td><td>68%</td></tr>
<tr><td>Cutting (2019, late 2024, late 2025)</td><td>9</td><td>+1.6%</td><td>−3.9%</td><td>44%</td><td>57%</td></tr>
<tr><td>Hold after cuts (2020 Q1, 2025, 2026 to Sep)</td><td>23</td><td>+0.9%</td><td>−2.1%</td><td>48%</td><td>46%</td></tr>
</tbody></table></div>
<p class="prose">The zero‑rate era looks spectacular only because it contains 2011–2013. Within the modern sample the best regime was "Fed on hold at a high rate" (the 2019 H1 rally, the 2023–24 ETF rally) and the worst was "Fed cutting".</p>
<div class="tbl"><table>
<thead><tr><th>FOMC decision</th><th>n</th><th>2‑day mean</th><th>2‑day median</th><th>21‑day mean</th><th>21‑day median</th><th>21‑day positive</th></tr></thead>
<tbody>
<tr><td>Cut</td><td>11</td><td>−0.4%</td><td>−0.2%</td><td>−1.7%</td><td class="neg">−5.7%</td><td>45%</td></tr>
<tr><td>Hike</td><td>20</td><td>−0.1%</td><td>−0.2%</td><td>−1.5%</td><td>−2.6%</td><td>45%</td></tr>
<tr><td>Hold</td><td>79</td><td>+0.4%</td><td>+0.0%</td><td>+10.6%</td><td>+3.6%</td><td>58%</td></tr>
<tr><td>Any 22‑day window</td><td></td><td></td><td></td><td>+3.9%</td><td></td><td></td></tr>
</tbody></table></div>
<div class="prose">
<p>Rate cuts have been "sell the news" for Bitcoin more often than not. The three Q4 cutting episodes: 2019 (Bitcoin −14% in Q4), 2024 (+48%, driven by the election and ETF flows), 2025 (−23%). Correlation of Bitcoin's 12‑month return with the 12‑month change in the policy rate, 2013–2026: −0.05.</p>
<p>Two caveats. This tests the policy rate, not liquidity; the popular "global M2 leads Bitcoin by 10–12 weeks" relationship was not tested here and is a better‑motivated channel than the funds rate, though notoriously sensitive to the chosen lag. And the September 2026 hike is the first since 2023, with guidance for possibly one more this year. Hiking regimes historically had positive median months (+4.2%), but the two prior Q4s that fell inside a hiking cycle <i>and</i> a year‑two phase (2018, 2022) were the worst in the sample. The Fed did not cause those; the cycle phase did, and the Fed did not rescue them.</p>
</div>
</section>

<section id="now">
<p class="eyebrow">Part 5</p>
<h2>Where 2026 sits</h2>
<div class="tbl"><table>
<thead><tr><th>Indicator, 15 Sep 2026</th><th>Value</th><th>Comparable years on 30 Sep</th></tr></thead>
<tbody>
<tr><td>Price</td><td>$75,686</td><td></td></tr>
<tr><td>Cycle phase</td><td>two years after the 2024 halving</td><td>2014, 2018, 2022</td></tr>
<tr><td>Days since cycle peak (6 Oct 2025)</td><td>344 · price is 61% of peak</td><td>prior cycles at day 344: 37%, 20%, 29% of peak</td></tr>
<tr><td>Drawdown from all‑time high</td><td class="neg">−39%</td><td>10 of 13 years were worse than −30%</td></tr>
<tr><td>Year‑to‑date</td><td class="neg">−13.5%</td><td>2014 (−47%), 2015 (−26%), 2018 (−53%), 2022 (−58%)</td></tr>
<tr><td>Trailing 12 months</td><td class="neg">−34%</td><td>only 2015 (−39%) and 2022 (−56%)</td></tr>
<tr><td>vs 200‑day average (~$70,300)</td><td class="pos">+7.7% above</td><td>above in 2013, 16, 17, 20, 25; below in every prior year‑two</td></tr>
<tr><td>2026 by month</td><td colspan="2">Jan −10%, Feb −15%, Mar +2%, Apr +12%, May −3%, Jun −20%, Jul +7%, Aug +25%, Sep −4% to the 15th (Q1 −22%, Q2 −14%, Q3 +29% so far)</td></tr>
<tr><td>Macro</td><td colspan="2">Fed hiked 25bp on 16 Sep to 3.75–4.00% (12–0); dots imply one more in 2026; next FOMC 27–28 Oct and 8–9 Dec. Spot ETFs net negative for the year after a record outflow streak in late May and June; Strategy's first BTC sale since 2022.</td></tr>
</tbody></table></div>
<h3>Conditional base rates for Q4, given the state on 30 September (2013–2025)</h3>
<div class="tbl"><table>
<thead><tr><th>Condition</th><th>Years</th><th>Oct up</th><th>Nov up</th><th>Q4 up</th><th>Q4 median</th></tr></thead>
<tbody>
<tr><td>Year‑to‑date negative</td><td>2014, 15, 18, 22</td><td>2/4</td><td>2/4</td><td class="neg">1/4</td><td class="neg">−16%</td></tr>
<tr><td>Year‑to‑date positive</td><td>9 years</td><td>8/9</td><td>6/9</td><td>7/9</td><td>+56%</td></tr>
<tr><td>Above 200‑day average</td><td>2013, 16, 17, 20, 25</td><td>4/5</td><td>4/5</td><td>4/5</td><td>+169%</td></tr>
<tr><td>Below 200‑day average</td><td>8 years</td><td>6/8</td><td>4/8</td><td>4/8</td><td>−4%</td></tr>
<tr><td>Trailing 12‑month return negative</td><td>2015, 22</td><td>2/2</td><td>1/2</td><td>1/2</td><td>+81% / −15%</td></tr>
<tr><td>Two years after a halving</td><td>2014, 18, 22</td><td>1/3</td><td>1/3</td><td>0/3</td><td>−18%</td></tr>
</tbody></table></div>
<p class="prose">2026 sits on both sides of these tables: it looks like a year‑two bear on the calendar, on year‑to‑date return and on the cycle clock, but it enters Q4 with momentum no prior year‑two had. The prior "trailing‑12‑month‑negative" Octobers (2015 +33%, 2022 +5%) were both positive, the best argument for a decent October; the prior year‑two Novembers (2018 −37%, 2022 −16%) are the best argument for caution in November.</p>
{img("06_peak_aligned_drawdowns.png", "Price as a percentage of cycle peak versus days since the peak, four cycles, with the window of prior cycle lows shaded", "Bear phases aligned on the cycle peak. Prior lows came on day 364, 366 and 406; from the 6 October 2025 peak those are 5 October, 7 October and 16 November 2026. From the equivalent of today (day 344) the next 107 days in prior cycles saw drawdowns of −19%, −19% and −58% before the low.")}
{img("09_2026_vs_bear_phase_analogs.png", "2026 price path indexed to prior year-end against 2014, 2018 and 2022", "2026 against the three prior 'two years after halving' years, indexed to the prior year‑end. The same phase, a milder version, and the only one above the 200‑day average entering Q4.")}
</section>

<section id="scenarios">
<p class="eyebrow">Part 6</p>
<h2>What to expect in Q4 2026</h2>
<div class="scen">
<div><h3>Range and grind</h3><div class="p">40%</div><p>October drifts toward $80–90k on low volatility, as most Octobers do; November is two‑way; the year closes between $70k and $90k. The modal outcome because the two strongest forces, year‑two phase pulling down and momentum plus a shallow drawdown holding up, roughly offset.</p><p class="note">Signposts: ETF flows flat‑to‑positive; the Fed holds on 28 October or a hike is fully priced; the 200‑day average (~$70k) holds on any dip.</p></div>
<div><h3>Cycle‑template washout</h3><div class="p">35%</div><p>A November‑led decline retests or undercuts the June low ($55–62k) between mid‑October and January, marking the cycle low, followed by the year‑three recovery pattern (2015 +34%, 2019 +94%, 2023 +156%). Undercuts of the mid‑year low are the norm in year two: by 10% in 2022, by 47% in 2018, by half in 2014–15.</p><p class="note">Signposts: weekly close below the 200‑day average and $70k; ETF outflows resuming for two‑plus weeks; a second hike in October or December with hawkish guidance; rising real yields and dollar.</p></div>
<div><h3>Uptober breakout</h3><div class="p">25%</div><p>Price reclaims the 2025 close ($87.5k, erasing the year's loss) in October and trades to $95–105k by year‑end. This is what the raw calendar statistics would predict; it is discounted because the calendar's power comes from a phase the market is not in.</p><p class="note">Signposts: three‑plus consecutive weeks of net ETF inflows; the Fed signals the September hike was one‑and‑done; a weekly close above the early‑September high (~$81k) then an October close above $87.5k.</p></div>
</div>
<h3>Levels that matter, in order</h3>
<div class="levels">
<em>$87,517</em><span>2025 close. Above it the year is positive and the breakout scenario is live.</span>
<em>~$81,000</em><span>Early‑September high.</span>
<em>~$70,300</em><span>200‑day average. A weekly close below it makes the washout scenario live.</span>
<em>$58,654</em><span>June closing low.</span>
<em>~$55,000</em><span>A 10% undercut of the June low, the 2022‑style outcome.</span>
</div>
<p class="prose">What would change the odds: sustained ETF inflows or a Fed pivot back to cuts without a recession raise the breakout case; a loss of the 200‑day average in October raises the washout case sharply; an October close above $90k would mean the cycle template failed in a way it never has, and the reading would move from "dampened cycle" to "cycle broken".</p>
</section>

<section id="caveats">
<p class="eyebrow">Read this too</p>
<h2>Caveats, stated plainly</h2>
<ul class="caveats prose">
<li><b>Sample size.</b> Thirteen Octobers, three year‑two years, nine months of Fed cuts. Every conditional table has a handful of observations. Treat the numbers as base rates that organize thinking, not as probabilities with decimals.</li>
<li><b>Multiple comparisons.</b> October's headline p‑value (0.007) becomes 0.11 once you account for having looked at twelve months. November has no detectable effect at all.</li>
<li><b>The cycle is changing.</b> Peak gains have fallen from 91× to 1.9× and drawdowns from −85% to −53%. Spot ETFs, corporate treasuries and a far larger holder base make 2014, 2018 and 2022 templates for timing and direction, not magnitude. The 2025 peak (+92% from the halving, no Q4 blow‑off, negative October and November in a post‑halving year) is itself evidence the old template is weakening.</li>
<li><b>Data.</b> Coin Metrics daily reference prices to 23 May 2026, spliced with a secondary daily source that tracks Coin Metrics to within 0.24% on average; month‑end closes verified against independent quotes. FOMC dates compiled from the published calendars and verified for 2025–2026.</li>
<li><b>Not investment advice.</b> This is a description of what the record shows and a probabilistic reading of where the record says we are.</li>
</ul>
</section>

<footer>
<div class="topbar" style="margin-bottom:18px"><span class="mark"><span class="glyph">19K</span><span class="lbl">Holdings</span></span><span class="site">Cross-border principal investment &amp; operating platform · 19kholdings.com</span></div>
<p>Method: monthly returns from month‑end closes; per‑month mean, median, hit rate, t‑test on log returns, Wilcoxon signed‑rank test, 20,000‑sample bootstrap intervals; max‑|t| permutation test for the twelve‑month family; cycle phase by calendar year relative to the latest halving; Fed regimes from the target‑rate path; FOMC event study from the close before each decision. Code, data and result tables: <code>analysis/bitcoin-seasonality</code> in the repository (build_dataset.py, analyze.py, charts.py).</p>
<p>Sources: Coin Metrics community data (CC BY‑NC 4.0); Habrador/Bitcoin‑price‑visualization; Federal Reserve press releases and FOMC calendars; Shiller S&amp;P 500 monthly data; press quotes for 2026 month‑end verification.</p>
</footer>
</div>
"""

html = (HEAD + BODY).encode("ascii", "xmlcharrefreplace").decode("ascii")  # pure ASCII: renders correctly with or without a charset header
OUT_FILE.write_text(html, encoding="ascii")
print(OUT_FILE.name, round(OUT_FILE.stat().st_size / 1e6, 2), "MB")
