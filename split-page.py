#!/usr/bin/env python3
"""Split ~/workspace/goals/pro/pages/index.html into modules:
  index.html (shell + static sections)
  style.css
  app.js (written separately by hand)
  data/news.js  (window.SITE_NEWS)
  data/x.js     (window.SITE_X)
Reads the current single-file page, extracts CSS + news items + X snapshots,
and rewrites index.html to load them. Keeps a .bak of the original.
"""
import html as htmlmod
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "index.html"

html_text = SRC.read_text(encoding="utf-8")

# ---------- backup ----------
BAK = BASE / "index.html.2026-11-09.bak"
if not BAK.exists():
    BAK.write_text(html_text, encoding="utf-8")
    print("backup:", BAK)

# ---------- style.css ----------
m = re.search(r"<style>(.*?)</style>", html_text, re.S)
assert m, "no <style> block"
(BASE / "style.css").write_text(m.group(1).strip() + "\n", encoding="utf-8")
print("style.css written")

# ---------- news data ----------
m = re.search(r"<!-- NEWS-START -->(.*?)<!-- NEWS-END -->", html_text, re.S)
assert m, "no NEWS region"
news_region = m.group(1)
m2 = re.search(r'<p class="news-updated">最后刷新：(.*?)</p>', html_text)
updated = m2.group(1).strip() if m2 else ""
items = []
for art in re.finditer(r'<article class="news-item">(.*?)</article>', news_region, re.S):
    a = art.group(1)
    link = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', a, re.S)
    assert link, "news item without link"
    url = htmlmod.unescape(link.group(1).strip())
    title = htmlmod.unescape(re.sub(r"<[^>]+>", "", link.group(2))).strip()
    zh_m = re.search(r'<div class="news-zh">(.*?)</div>', a, re.S)
    zh = htmlmod.unescape(re.sub(r"<[^>]+>", "", zh_m.group(1))).strip() if zh_m else ""
    meta = re.search(r'<div class="news-meta">(.*?)</div>', a, re.S)
    src, dt = "", ""
    if meta:
        parts = htmlmod.unescape(meta.group(1)).split("·")
        src = parts[0].strip()
        dt = parts[1].strip() if len(parts) > 1 else ""
    item = {"t": title, "u": url, "s": src, "d": dt}
    if zh:
        item["zh"] = zh
    items.append(item)
news_data = {"updated": updated, "items": items}
(BASE / "data").mkdir(exist_ok=True)
(BASE / "data" / "news.js").write_text(
    "window.SITE_NEWS = " + json.dumps(news_data, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"data/news.js written: {len(items)} items, updated {updated}")

# ---------- X data ----------
def strip_tags(s):
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def parse_x_section(sec_id):
    sec = re.search(r'<section id="%s".*?</section>' % sec_id, html_text, re.S)
    assert sec, f"no section {sec_id}"
    body = sec.group(0)
    snaps = []
    for sm in re.finditer(
        r'<div class="x-snap" data-hour="([^"]+)"[^>]*>(.*?)</table></div>\s*</div>',
        body, re.S,
    ):
        hour = sm.group(1)
        inner = sm.group(2)
        rows = []
        for tr in re.finditer(r"<tr>(.*?)</tr>", inner, re.S):
            if "<th>" in tr.group(1):
                continue
            cells = re.findall(r"<td[^>]*>(.*?)</td>", tr.group(1), re.S)
            if not cells:
                continue
            if len(cells) == 1 and "x-empty" in tr.group(0):
                continue  # empty snapshot -> rows stays []
            if sec_id == "xnews":
                topic, desc, tme, linkcell = (cells + ["", "", "", ""])[:4]
                lm = re.search(r'<a href="([^"]+)"[^>]*>([^<]*)</a>', linkcell)
                rows.append({
                    "topic": strip_tags(topic),
                    "desc": strip_tags(desc),
                    "time": strip_tags(tme),
                    "url": htmlmod.unescape(lm.group(1)) if lm else "",
                    "label": strip_tags(lm.group(2)) if lm else "",
                })
            else:
                post, content, author, statuscell, linkcell = (cells + ["", "", "", "", ""])[:5]
                sc = re.search(r'<span class="tag ([^"]+)">([^<]*)</span>', statuscell)
                lm = re.search(r'<a href="([^"]+)"[^>]*>([^<]*)</a>', linkcell)
                rows.append({
                    "post": strip_tags(post),
                    "content": strip_tags(content),
                    "author": strip_tags(author),
                    "status": strip_tags(sc.group(2)) if sc else strip_tags(statuscell),
                    "statusClass": sc.group(1) if sc else "wait",
                    "url": htmlmod.unescape(lm.group(1)) if lm else "",
                    "label": strip_tags(lm.group(2)) if lm else "",
                })
        snaps.append({"hour": hour, "rows": rows})
    return snaps

x_data = {"news": parse_x_section("xnews"), "wool": parse_x_section("xwool")}
(BASE / "data" / "x.js").write_text(
    "window.SITE_X = " + json.dumps(x_data, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"data/x.js written: news snaps {[ (s['hour'], len(s['rows'])) for s in x_data['news'] ]}, "
      f"wool snaps {[ (s['hour'], len(s['rows'])) for s in x_data['wool'] ]}")

# ---------- new index.html ----------
out = html_text
out = re.sub(r"<style>.*?</style>", '<link rel="stylesheet" href="style.css">', out, count=1, flags=re.S)
out = re.sub(r'<p class="news-updated">最后刷新：.*?</p>',
             '<p class="news-updated" id="news-updated"></p>', out, count=1)
out = re.sub(r"<!-- NEWS-START -->.*?<!-- NEWS-END -->",
             '<div id="news-list"></div>', out, count=1, flags=re.S)
for sec_id in ("xnews", "xwool"):
    sec = re.search(r'(<section id="%s".*?<h2>.*?</h2>\n)(.*?)(\n<p class="note">)' % sec_id, out, re.S)
    assert sec, f"cannot locate body of {sec_id}"
    replacement = ('<div class="x-tags" id="tags-%s"></div>\n'
                   '<div id="snaps-%s"></div>' % (sec_id, sec_id))
    out = out[:sec.start(2)] + replacement + out[sec.start(3):]
out = re.sub(r"<script>.*?</script>",
             '<script src="data/news.js"></script>\n<script src="data/x.js"></script>\n<script src="app.js"></script>',
             out, count=1, flags=re.S)
assert "<!-- NEWS-START -->" not in out, "NEWS markers left"
assert "x-snap" not in out or "snaps-xnews" in out, "old snaps left"
assert "<style>" not in out, "inline style left"
assert "Anthropic 34" not in out, "old X content left in shell"
assert "OpenAI 完成 110" not in out, "old news content left in shell"
SRC.write_text(out, encoding="utf-8")
print("index.html rewritten as shell")
print("sizes:", {p.name: p.stat().st_size for p in [SRC, BASE / "style.css", BASE / "data" / "news.js", BASE / "data" / "x.js"]})
