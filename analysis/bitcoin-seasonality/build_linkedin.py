#!/usr/bin/env python3
"""LinkedIn deliverables: cover images (1200x627 and 1080x1350) and a paginated PDF of the report.
Renders HTML with headless Chromium; fonts embedded from @fontsource (Fraunces, Hanken Grotesk)."""
import base64, re, subprocess, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "linkedin"; OUT.mkdir(exist_ok=True)
FONTS = Path("/tmp/claude-0/-home-user-index/1c591747-7c05-52c3-bbf1-bff5b78f2329/scratchpad/fonts")
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

def font_face(family, path, weight):
    b = base64.b64encode(path.read_bytes()).decode()
    return f'@font-face{{font-family:"{family}";font-weight:{weight};font-style:normal;font-display:block;src:url(data:font/woff2;base64,{b}) format("woff2");}}'

FONT_CSS = "".join([
    font_face("Fraunces", FONTS / "fraunces/files/fraunces-latin-400-normal.woff2", 400),
    font_face("Fraunces", FONTS / "fraunces/files/fraunces-latin-500-normal.woff2", 500),
    font_face("Fraunces", FONTS / "fraunces/files/fraunces-latin-600-normal.woff2", 600),
    font_face("Hanken Grotesk", FONTS / "hanken-grotesk/files/hanken-grotesk-latin-400-normal.woff2", 400),
    font_face("Hanken Grotesk", FONTS / "hanken-grotesk/files/hanken-grotesk-latin-500-normal.woff2", 500),
    font_face("Hanken Grotesk", FONTS / "hanken-grotesk/files/hanken-grotesk-latin-600-normal.woff2", 600),
])

# 2026 year-to-date price path as an SVG polyline (real data as the cover's background element)
px = pd.read_csv(ROOT / "data/btc_daily.csv", parse_dates=["date"]).set_index("date")["close"]
s = px["2025-10-01":]
W, H = 1000, 300
xs = (s.index - s.index[0]).days / (s.index[-1] - s.index[0]).days * W
lo, hi = s.min(), s.max()
ys = H - (s.values - lo) / (hi - lo) * (H * 0.86) - H * 0.07
pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
SPARK = (f'<svg class="spark" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">'
         f'<polyline points="{pts}" fill="none" stroke="#C2A063" stroke-width="2.2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')

MARK = '<div class="mark"><span class="glyph">19K</span><span class="lbl">Holdings</span></div>'
ODDS = [
    ("October closes above its 30 September close", "~60%"),
    ("October + November combined positive", "~50%"),
    ("Full quarter (1 Oct &ndash; 31 Dec) positive", "~45%"),
    ("A daily close below the June low ($58,654) during Q4", "~30%"),
    ("Year-end close above $87,517, so 2026 finishes up", "~25%"),
    ("New all-time high before year-end", "&lt;5%"),
]
LEDGER = "".join(f'<div class="row"><span>{a}</span><em>{b}</em></div>' for a, b in ODDS)

BASE_CSS = FONT_CSS + """
*{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#0B1411;--panel:#12241D;--paper:#ECE8DE;--brass:#C2A063;--brass-soft:#d8c195;--muted:#8C988E;--line:rgba(194,160,99,.28)}
body{background:var(--ink);color:var(--paper);font-family:"Hanken Grotesk",Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.cover{position:relative;overflow:hidden;background:var(--ink);background-image:radial-gradient(ellipse at 85% 15%, rgba(194,160,99,.16), transparent 55%)}
.spark{position:absolute;left:0;right:0;bottom:0;width:100%;opacity:.28;pointer-events:none}
.eyebrow{font-size:15px;letter-spacing:.18em;text-transform:uppercase;color:var(--brass);font-weight:600}
h1{font-family:"Fraunces",Georgia,serif;font-weight:500;line-height:.98;letter-spacing:-.012em;color:var(--paper)}
.sub{color:var(--muted);line-height:1.4}
.ledger{border-top:1px solid var(--line)}
.row{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:baseline;border-bottom:1px solid var(--line)}
.row span{color:var(--paper)}
.row em{font-family:"Fraunces",Georgia,serif;font-style:normal;font-weight:500;color:var(--brass);font-variant-numeric:tabular-nums;white-space:nowrap;line-height:1}
.foot{position:absolute;display:flex;justify-content:space-between;color:var(--muted);font-size:14px;letter-spacing:.02em}
.mark{position:absolute;display:flex;align-items:baseline;gap:11px}
.mark .glyph{font-family:"Fraunces",Georgia,serif;font-weight:600;letter-spacing:.02em;color:var(--brass)}
.mark .lbl{letter-spacing:.28em;text-transform:uppercase;color:var(--muted);font-weight:500}
"""

def cover_html(width, height, layout):
    if layout == "landscape":
        css = BASE_CSS + f"""
.cover{{width:{width}px;height:{height}px;padding:56px 64px 52px}}
.grid{{display:grid;grid-template-columns:1.05fr 1fr;gap:56px;height:100%;align-items:start;padding-top:50px}}
h1{{font-size:78px;margin:18px 0 22px}}
.sub{{font-size:21px;max-width:30ch}}
.ledger{{margin-top:6px}}
.row{{padding:12px 0}} .row span{{font-size:18px;line-height:1.25}} .row em{{font-size:40px}}
.foot{{left:64px;right:64px;bottom:22px}}
.spark{{height:34%;opacity:.24}}
.mark{{top:44px;right:64px}} .mark .glyph{{font-size:30px}} .mark .lbl{{font-size:14px}}
"""
        body = f"""<div class="cover">{MARK}<div class="grid"><div>
<p class="eyebrow">Research note &middot; September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="sub">Six odds for October&ndash;December 2026, from fifteen years of daily prices, four halving cycles and 110 Fed meetings.</p>
</div><div class="ledger">{LEDGER}</div></div>
<div class="foot"><span>Full report in the PDF &middot; not investment advice</span><span>19kholdings.com &middot; daily prices to 15 Sep 2026</span></div>
{SPARK}</div>"""
    else:
        css = BASE_CSS + f"""
.cover{{width:{width}px;height:{height}px;padding:84px 76px 72px}}
h1{{font-size:96px;margin:20px 0 24px}}
.sub{{font-size:25px;max-width:34ch}}
.ledger{{margin-top:44px}}
.row{{padding:18px 0}} .row span{{font-size:24px;line-height:1.25;max-width:30ch}} .row em{{font-size:56px}}
.foot{{left:76px;right:76px;bottom:34px;font-size:17px}}
.spark{{height:26%;opacity:.22}}
.mark{{top:78px;right:76px}} .mark .glyph{{font-size:34px}} .mark .lbl{{font-size:16px}}
"""
        body = f"""<div class="cover">{MARK}
<p class="eyebrow">Research note &middot; September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="sub">Six odds for October&ndash;December 2026, from fifteen years of daily prices, four halving cycles and 110 Fed meetings.</p>
<div class="ledger">{LEDGER}</div>
<div class="foot"><span>Full report in the PDF &middot; not investment advice</span><span>19kholdings.com &middot; daily prices to 15 Sep 2026</span></div>
{SPARK}</div>"""
    return f"<!doctype html><html><head><meta charset='utf-8'><title>cover</title><style>{css}</style></head><body>{body}</body></html>"

def run(args):
    r = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=8000"] + args,
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(r.stderr[-800:]); sys.exit(1)

for name, w, h, layout in [("cover_linkedin_1200x627", 1200, 627, "landscape"), ("cover_linkedin_1080x1350", 1080, 1350, "portrait")]:
    p = OUT / f"{name}.html"; p.write_text(cover_html(w, h, layout), encoding="utf-8")
    run([f"--window-size={w},{h}", "--force-device-scale-factor=2", f"--screenshot={OUT / (name + '.png')}", f"file://{p}"])
    p.unlink()
    print("wrote", name + ".png")

# ------------------------------------------------------------------ PDF: explicit 8x10in pages, dark, same treatment as the cover
import os
from split_blocks import blocks_of
dark_src = OUT / "_report_dark.html"
subprocess.run([sys.executable, str(ROOT / "build_report_html.py")], check=True,
               env={**os.environ, "CHART_DIR": "charts_dark", "REPORT_OUT": "linkedin/_report_dark.html"}, capture_output=True)
body = dark_src.read_text(encoding="ascii").split("</style>", 1)[1]
body = re.sub(r"<header>.*?</header>", "", body, count=1, flags=re.S)
B = [h for _, h in blocks_of(body) if not h.startswith('<div class="topbar"')]   # the web footer's wordmark is not report content
assert len(B) == 59, len(B)
NARROW = {46, 47}
PLAN = [  # block indices per page (after the cover)
    ("verdict", [0, 1, 2]),
    ("odds", [3, 4, 5, 6]),
    ("", [7, 8, 9, 12, 13]),
    ("", [10, 11]),
    ("", [14, 15, 16]),
    ("tight", [17, 18, 19, 20, 21, 22, 23, 24, 25]),
    ("", [26, 27]),
    ("", [28, 29, 30]),
    ("", [31, 32, 33, 34]),
    ("", [35, 36, 37, 38, 39]),
    ("", [40, 41, 42, 43, 44]),
    ("", [45, 46, 47]),
    ("", [48, 49, 50, 51, 52, 53]),
    ("", [54, 55, 56, 57, 58]),
]
assert sorted(sum((ix for _, ix in PLAN), [])) == list(range(59))
FONT_STACK = '"Hanken Grotesk",Helvetica,Arial,sans-serif'
PRINT_CSS = FONT_CSS + """
@page{size:8in 10in;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#0B1411}
body{color:#E6E2D8;font-family:FONTSTACK;font-size:10.5pt;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:8in;height:10in;padding:0.6in 0.6in 0.8in;position:relative;overflow:hidden;background:#0B1411;break-after:page}
.page:last-child{break-after:auto}
.pfoot{position:absolute;left:0.6in;right:0.6in;bottom:0.4in;display:flex;justify-content:space-between;font-size:8pt;color:#8C988E;letter-spacing:.02em}
.coverpage{padding:0.9in 0.8in 0.75in;color:#ECE8DE;background-image:radial-gradient(ellipse at 85% 12%, rgba(194,160,99,.16), transparent 55%)}
.coverpage p.eyebrow{font-size:10pt;letter-spacing:.18em;text-transform:uppercase;color:#C2A063;font-weight:600;margin:0;padding:0;border:0}
.coverpage h1{font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:54pt;line-height:.98;letter-spacing:-.012em;margin:12pt 0 14pt;color:#ECE8DE}
.coverpage .sub{color:#8C988E;font-size:14.5pt;line-height:1.4;max-width:34ch;margin:0}
.coverpage .ledger{margin-top:34pt;border-top:1px solid rgba(194,160,99,.28)}
.coverpage .row{display:grid;grid-template-columns:1fr auto;gap:14pt;align-items:baseline;padding:11pt 0;border-bottom:1px solid rgba(194,160,99,.28)}
.coverpage .row span{font-size:13pt;color:#ECE8DE;max-width:30ch;line-height:1.25}
.coverpage .row em{font-family:"Fraunces",Georgia,serif;font-style:normal;font-weight:500;font-size:32pt;color:#C2A063;font-variant-numeric:tabular-nums;line-height:1}
.coverpage .foot{position:absolute;left:0.8in;right:0.8in;bottom:0.5in;display:flex;justify-content:space-between;color:#8C988E;font-size:9pt}
.coverpage .spark{position:absolute;left:0;right:0;bottom:0;width:100%;height:24%;opacity:.22}
.coverpage .cmark{position:absolute;top:0.86in;right:0.8in;display:flex;align-items:baseline;gap:8pt}
.coverpage .cmark .glyph{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:22pt;letter-spacing:.02em;color:#C2A063}
.coverpage .cmark .lbl{font-size:10pt;letter-spacing:.28em;text-transform:uppercase;color:#8C988E;font-weight:500}
.pfoot .fl{display:flex;align-items:baseline;gap:10pt}
.pfoot .fmark{display:flex;align-items:baseline;gap:5pt}
.pfoot .fmark .glyph{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:10pt;letter-spacing:.02em;color:#C2A063}
.pfoot .fmark .lbl{font-size:6.5pt;letter-spacing:.28em;text-transform:uppercase;color:#8C988E;font-weight:500}
.eyebrow{font-size:8.5pt;letter-spacing:.14em;text-transform:uppercase;color:#C2A063;font-weight:600;margin:0 0 6pt}
h2{font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:22pt;line-height:1.12;margin:0 0 10pt;color:#ECE8DE}
h3{font-size:11.5pt;font-weight:600;margin:14pt 0 6pt;color:#ECE8DE}
p{margin:0 0 9pt}
.prose{max-width:none}
.eyebrow + h2{margin-top:0}
p.eyebrow:not(:first-child){margin-top:14pt;padding-top:12pt;border-top:1px solid rgba(194,160,99,.28)}
.findings{list-style:none;padding:0;margin:6pt 0 0;display:grid;gap:9pt}
.findings li{padding-left:14pt;position:relative}
.findings li::before{content:"";position:absolute;left:0;top:.55em;width:6pt;height:6pt;border-radius:50%;background:#C2A063}
.findings b{color:#ECE8DE}
.ledger{margin:14pt 0 4pt;border-top:1px solid rgba(194,160,99,.28)}
.ledger .row{display:grid;grid-template-columns:1fr auto;gap:12pt;align-items:baseline;padding:7pt 0;border-bottom:1px solid rgba(194,160,99,.16)}
.ledger .row span{color:#ECE8DE}
.ledger .row em{font-family:"Fraunces",Georgia,serif;font-style:normal;font-weight:500;font-size:18pt;color:#C2A063;font-variant-numeric:tabular-nums}
.odds h3{font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:22pt;margin:0 0 8pt}
.odds .ledger{margin-top:18pt}
.odds .ledger .row{padding:13pt 0}
.odds .ledger .row span{font-size:12.5pt}
.odds .ledger .row em{font-size:28pt}
.odds p.prose{margin-top:22pt !important}
.note{font-size:9pt;color:#8C988E}
.tight th,.tight td{padding:3pt 5pt}
.tight p{margin-bottom:7pt}
.tight h2{margin-bottom:7pt}
.tight .tbl{margin:6pt 0 9pt}
figure{margin:10pt 0 12pt}
figure img{display:block;width:100%;height:auto;border:1px solid rgba(194,160,99,.22);border-radius:2pt;background:#0F1C17}
figcaption{font-size:8.6pt;color:#8C988E;margin-top:4pt;line-height:1.4}
.narrow figure img{width:90%;margin:0 auto}
.narrow figcaption{width:90%;margin-left:auto;margin-right:auto}
.tbl{margin:8pt 0 12pt}
table{border-collapse:collapse;width:100%;font-size:8.8pt;font-variant-numeric:tabular-nums}
th,td{padding:4pt 5pt;border-bottom:1px solid rgba(236,232,222,.09);text-align:right;vertical-align:top}
th{font-weight:600;color:#8C988E;font-size:7.8pt;letter-spacing:.04em;text-transform:uppercase;border-bottom:1px solid rgba(194,160,99,.4)}
th:first-child,td:first-child{text-align:left}
td.hl,tr.hl td{background:rgba(194,160,99,.16);font-weight:600;color:#ECE8DE}
.neg{color:#E07070}.pos{color:#5FBF95}
.scen{display:grid;grid-template-columns:repeat(3,1fr);gap:14pt;margin-top:12pt}
.scen>div{border-top:2px solid #C2A063;padding-top:8pt}
.scen h3{margin:0 0 2pt;font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:14pt}
.scen .p{font-family:"Fraunces",Georgia,serif;font-size:26pt;font-weight:500;line-height:1;margin:4pt 0 8pt;color:#C2A063}
.scen p{font-size:9pt;margin-bottom:6pt;color:#D5D1C6}
.levels{display:grid;grid-template-columns:auto 1fr;gap:5pt 12pt;margin:10pt 0;font-size:10pt}
.levels em{font-style:normal;font-family:"Fraunces",Georgia,serif;font-size:13pt;font-weight:500;font-variant-numeric:tabular-nums;white-space:nowrap;color:#C2A063}
.caveats{padding-left:14pt;margin:0 0 12pt}.caveats li{margin-bottom:6pt}
.sources{margin-top:14pt;padding-top:10pt;border-top:1px solid rgba(194,160,99,.28);font-size:9pt;color:#8C988E}
.sources p{margin-bottom:6pt}
code{font-family:Menlo,Consolas,monospace;font-size:.9em;color:#D8C195}
a{color:#C2A063}
""".replace("FONTSTACK", FONT_STACK)
FOOT = "Bitcoin's Fourth Quarter &middot; Research note, 21 September 2026"
pages = [f"""<div class="page coverpage"><div class="cmark"><span class="glyph">19K</span><span class="lbl">Holdings</span></div>
<p class="eyebrow">Research note &middot; 21 September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="sub">What fifteen years of daily prices, four halving cycles and 110 Fed meetings say about October&ndash;December 2026.</p>
<div class="ledger">{LEDGER}</div>
<div class="foot"><span>Not investment advice</span><span>19kholdings.com &middot; daily prices 2010 &ndash; 15 Sep 2026</span></div>
{SPARK}</div>"""]
for n, (cls, ix) in enumerate(PLAN, start=2):
    parts = []
    for k in ix:
        h = B[k]
        if k in NARROW: h = f'<div class="narrow">{h}</div>'
        if k in (57, 58): h = h  # sources paragraphs, wrapped below
        parts.append(h)
    if 57 in ix:
        j = ix.index(57); parts = parts[:j] + [f'<div class="sources">{"".join(parts[j:])}</div>']
    pages.append(f'<div class="page {cls}">{"".join(parts)}<div class="pfoot"><span class="fl"><span class="fmark"><span class="glyph">19K</span><span class="lbl">Holdings</span></span><span>{FOOT}</span></span><span>{n}</span></div></div>')
pdf_html = f"<!doctype html><html><head><meta charset='utf-8'><title>Bitcoin's Fourth Quarter</title><style>{PRINT_CSS}</style></head><body>{''.join(pages)}</body></html>"
p = OUT / "report_print.html"; p.write_text(pdf_html, encoding="utf-8")
pdf = OUT / "Bitcoins_Fourth_Quarter_Q4_2026_outlook.pdf"
run([f"--print-to-pdf={pdf}", "--no-pdf-header-footer", f"file://{p}"])
p.unlink(); dark_src.unlink()
print("pdf size MB", round(pdf.stat().st_size / 1e6, 2), "pages planned", len(pages))
