"""Split the report body into ordered top-level content blocks per section (used to paginate the PDF)."""
from html.parser import HTMLParser
import re

VOID = {"img", "br", "meta", "link", "hr", "input"}

class Splitter(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=False)
        self.raw, self.depth, self.stack, self.blocks, self.section = raw, 0, [], [], None
        self.open_pos = None
    def _off(self):
        line, col = self.getpos(); return sum(len(l) + 1 for l in self.raw.split("\n")[:line - 1]) + col
    def handle_starttag(self, tag, attrs):
        if tag in VOID: return
        a = dict(attrs)
        if tag == "section": self.section = a.get("id"); self.depth = 1; return
        if tag == "footer" and self.depth == 0: self.section = "footer"; self.depth = 1; self.open_pos = self._off(); self.stack.append(tag); return
        if self.depth == 1 and self.section:
            self.open_pos = self._off()
        if self.depth >= 1: self.stack.append(tag); self.depth += 1
    def handle_endtag(self, tag):
        if tag in VOID: return
        if tag == "section": self.depth = 0; self.section = None; return
        if self.depth >= 2 and self.stack and self.stack[-1] == tag:
            self.stack.pop(); self.depth -= 1
            if self.depth == 1:
                end = self._off() + len(tag) + 3
                self.blocks.append((self.section, self.raw[self.open_pos:end]))
                if tag == "footer": self.depth = 0; self.section = None

def blocks_of(body_html):
    s = Splitter(body_html); s.feed(body_html)
    out = []
    for sec, html in s.blocks:
        if html.startswith('<div class="prose">'):
            inner = html[len('<div class="prose">'):-len('</div>')]
            for m in re.finditer(r"<p\b.*?</p>", inner, flags=re.S):
                out.append((sec, m.group(0)))
        else:
            out.append((sec, html))
    return out

if __name__ == "__main__":
    import sys
    raw = open(sys.argv[1], encoding="ascii").read().split("</style>", 1)[1]
    raw = re.sub(r"<header>.*?</header>", "", raw, count=1, flags=re.S)
    for i, (sec, h) in enumerate(blocks_of(raw)):
        tag = re.match(r"<(\w+)[^>]*>", h).group(0)[:40]
        txt = re.sub(r"<[^>]+>", " ", h); txt = re.sub(r"\s+", " ", txt).strip()[:70]
        print(f"{i:2d} {sec:9s} {len(h):7d} {tag:40s} {txt}")
