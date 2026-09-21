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
"""

def cover_html(width, height, layout):
    if layout == "landscape":
        css = BASE_CSS + f"""
.cover{{width:{width}px;height:{height}px;padding:56px 64px 52px}}
.grid{{display:grid;grid-template-columns:1.05fr 1fr;gap:56px;height:100%;align-items:start}}
h1{{font-size:78px;margin:18px 0 22px}}
.sub{{font-size:21px;max-width:30ch}}
.ledger{{margin-top:6px}}
.row{{padding:12px 0}} .row span{{font-size:18px;line-height:1.25}} .row em{{font-size:40px}}
.foot{{left:64px;right:64px;bottom:22px}}
.spark{{height:34%;opacity:.24}}
"""
        body = f"""<div class="cover"><div class="grid"><div>
<p class="eyebrow">Research note &middot; September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="sub">Six odds for October&ndash;December 2026, from fifteen years of daily prices, four halving cycles and 110 Fed meetings.</p>
</div><div class="ledger">{LEDGER}</div></div>
<div class="foot"><span>Full report in the PDF &middot; not investment advice</span><span>Daily prices to 15 Sep 2026</span></div>
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
"""
        body = f"""<div class="cover">
<p class="eyebrow">Research note &middot; September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="sub">Six odds for October&ndash;December 2026, from fifteen years of daily prices, four halving cycles and 110 Fed meetings.</p>
<div class="ledger">{LEDGER}</div>
<div class="foot"><span>Full report in the PDF &middot; not investment advice</span><span>Daily prices to 15 Sep 2026</span></div>
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

# ------------------------------------------------------------------ PDF (Letter, paginated)
html = (ROOT / "report.html").read_text(encoding="ascii")
body = html.split("</style>", 1)[1]
body = re.sub(r"<header>.*?</header>", "", body, count=1, flags=re.S)   # cover page replaces the web header
body = body.replace('<h3>Odds for Q4 2026</h3>', '<div class="keep"><h3>Odds for Q4 2026</h3>', 1)
body = body.replace('</div>\n<p class="prose" style="margin-top:18px">', '</div></div>\n<p class="prose" style="margin-top:18px">', 1)
assert body.count('<div class="keep">') == 1 and '</div></div>\n<p class="prose" style="margin-top:18px">' in body
PRINT_CSS = FONT_CSS + """
@page{size:Letter;margin:0.75in 0.7in 0.8in 0.7in;@bottom-left{content:"Bitcoin's Fourth Quarter  \\00b7  Research note, 21 September 2026";font-family:"Hanken Grotesk",Helvetica,Arial,sans-serif;font-size:8.5pt;color:#6b746e}@bottom-right{content:counter(page);font-family:"Hanken Grotesk",Helvetica,Arial,sans-serif;font-size:8.5pt;color:#6b746e}}
@page cover{margin:0;@bottom-left{content:none}@bottom-right{content:none}}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#fff;color:#10201A;font-family:"Hanken Grotesk",Helvetica,Arial,sans-serif;font-size:10.5pt;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.coverpage{page:cover;width:8.5in;height:11in;background:#0B1411;color:#ECE8DE;position:relative;overflow:hidden;padding:0.95in 0.85in 0.8in;background-image:radial-gradient(ellipse at 85% 12%, rgba(194,160,99,.16), transparent 55%);break-after:page}
.coverpage .eyebrow{font-size:10.5pt;letter-spacing:.18em;text-transform:uppercase;color:#C2A063;font-weight:600;margin:0}
.coverpage h1{font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:58pt;line-height:.98;letter-spacing:-.012em;margin:14pt 0 16pt;color:#ECE8DE}
.coverpage .sub{color:#8C988E;font-size:15.5pt;line-height:1.4;max-width:34ch;margin:0}
.coverpage .ledger{margin-top:40pt;border-top:1px solid rgba(194,160,99,.28)}
.coverpage .row{display:grid;grid-template-columns:1fr auto;gap:14pt;align-items:baseline;padding:12pt 0;border-bottom:1px solid rgba(194,160,99,.28)}
.coverpage .row span{font-size:13.5pt;color:#ECE8DE;max-width:26ch;line-height:1.25}
.coverpage .row em{font-family:"Fraunces",Georgia,serif;font-style:normal;font-weight:500;font-size:34pt;color:#C2A063;font-variant-numeric:tabular-nums;line-height:1}
.coverpage .foot{position:absolute;left:0.85in;right:0.85in;bottom:0.55in;display:flex;justify-content:space-between;color:#8C988E;font-size:9.5pt}
.coverpage .spark{position:absolute;left:0;right:0;bottom:0;width:100%;opacity:.22}
.wrap{max-width:none;padding:0}
.eyebrow{font-size:8.5pt;letter-spacing:.14em;text-transform:uppercase;color:#8C6D35;font-weight:600;margin:0 0 6pt}
h2{font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:22pt;line-height:1.12;margin:0 0 10pt}
h3{font-size:11.5pt;font-weight:600;margin:16pt 0 6pt}
p{margin:0 0 9pt}
.prose{max-width:none}
section{break-before:auto;margin-top:22pt;padding-top:16pt;border-top:1px solid rgba(16,32,26,.2)}
section#verdict{margin-top:0;padding-top:0;border-top:none}
.eyebrow,h2,h3,.note{break-after:avoid}
.keep{break-inside:avoid}
.scen{break-inside:avoid}
.findings{list-style:none;padding:0;margin:6pt 0 0;display:grid;gap:8pt}
.findings li{padding-left:14pt;position:relative;break-inside:avoid}
.findings li::before{content:"";position:absolute;left:0;top:.55em;width:6pt;height:6pt;border-radius:50%;background:#8C6D35}
.ledger{margin:14pt 0 4pt;border-top:1px solid rgba(16,32,26,.2);break-inside:avoid}
.ledger .row{display:grid;grid-template-columns:1fr auto;gap:12pt;align-items:baseline;padding:6pt 0;border-bottom:1px solid rgba(16,32,26,.1)}
.ledger .row em{font-family:"Fraunces",Georgia,serif;font-style:normal;font-weight:500;font-size:17pt;font-variant-numeric:tabular-nums}
.note{font-size:9pt;color:#5F6B64}
figure{margin:12pt 0;break-inside:avoid}
figure img{display:block;width:100%;height:auto;border:1px solid rgba(16,32,26,.12);border-radius:2pt}
figcaption{font-size:8.8pt;color:#5F6B64;margin-top:4pt}
.tbl{overflow:visible;margin:10pt 0 12pt;break-inside:avoid}
table{border-collapse:collapse;width:100%;font-size:8.8pt;font-variant-numeric:tabular-nums;min-width:0}
th,td{padding:4pt 5pt;border-bottom:1px solid rgba(16,32,26,.1);text-align:right;vertical-align:top}
th{font-weight:600;color:#5F6B64;font-size:7.8pt;letter-spacing:.04em;text-transform:uppercase;border-bottom:1px solid rgba(16,32,26,.25)}
th:first-child,td:first-child{text-align:left}
td.hl,tr.hl td{background:rgba(140,109,53,.12);font-weight:600}
.neg{color:#B23A3A}.pos{color:#1F6E52}
.scen{display:grid;grid-template-columns:repeat(3,1fr);gap:14pt;margin-top:12pt}
.scen>div{border-top:2px solid #8C6D35;padding-top:8pt;break-inside:avoid}
.scen h3{margin:0 0 2pt;font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:14pt}
.scen .p{font-family:"Fraunces",Georgia,serif;font-size:26pt;font-weight:500;line-height:1;margin:4pt 0 8pt}
.scen p{font-size:9pt;margin-bottom:6pt}
.levels{display:grid;grid-template-columns:auto 1fr;gap:5pt 12pt;margin:10pt 0;font-size:10pt}
.levels em{font-style:normal;font-family:"Fraunces",Georgia,serif;font-size:13pt;font-weight:500;font-variant-numeric:tabular-nums;white-space:nowrap}
.caveats{padding-left:14pt}.caveats li{margin-bottom:6pt}
footer{margin-top:18pt;padding-top:10pt;border-top:1px solid rgba(16,32,26,.2);font-size:9pt;color:#5F6B64}
code{font-family:Menlo,Consolas,monospace;font-size:.9em}
a{color:#8C6D35}
"""
COVER_PAGE = f"""<div class="coverpage">
<p class="eyebrow">Research note &middot; 21 September 2026</p>
<h1>Bitcoin's Fourth Quarter</h1>
<p class="sub">What fifteen years of daily prices, four halving cycles and 110 Fed meetings say about October&ndash;December 2026.</p>
<div class="ledger">{LEDGER}</div>
<div class="foot"><span>Not investment advice</span><span>Daily prices 2010 &ndash; 15 Sep 2026</span></div>
{SPARK}</div>"""
pdf_html = f"<!doctype html><html><head><meta charset='utf-8'><title>Bitcoin's Fourth Quarter</title><style>{PRINT_CSS}</style></head><body>{COVER_PAGE}{body}</body></html>"
p = OUT / "report_print.html"; p.write_text(pdf_html, encoding="utf-8")
pdf = OUT / "Bitcoins_Fourth_Quarter_Q4_2026_outlook.pdf"
run([f"--print-to-pdf={pdf}", "--no-pdf-header-footer", f"file://{p}"])
p.unlink()
print("pdf size MB", round(pdf.stat().st_size / 1e6, 2))
