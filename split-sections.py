#!/usr/bin/env python3
"""Split the static sections of ~/workspace/goals/pro/pages/index.html into
per-section data files (data/sec-*.js) rendered by app.js:
  sec-pro, sec-domain, sec-ai, sec-cloud, sec-esim, sec-student, sec-server
  sec-videos, sec-archive
The section shells (h2, table headers, notes) stay in index.html; only the
table bodies / cards / list items move into data files.
"""
import html as htmlmod
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "index.html"

html_text = SRC.read_text(encoding="utf-8")

TABLE_SECTIONS = ["pro", "domain", "ai", "cloud", "esim", "student", "server"]


def strip_tags(s):
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_cell(cell_html):
    """Return a plain string or a dict {t, u?, tag?, bad?}."""
    tag_m = re.search(r'<span class="tag ([^"]+)">([^<]*)</span>', cell_html)
    bad_m = re.search(r'<span class="bad">(.*?)</span>', cell_html, re.S)
    link_m = re.search(r'<a href="([^"]+)"[^>]*>([^<]*)</a>', cell_html)
    if link_m:
        cell = {"t": strip_tags(link_m.group(2)), "u": htmlmod.unescape(link_m.group(1))}
    elif bad_m:
        cell = {"t": strip_tags(bad_m.group(1)), "bad": True}
    else:
        text = strip_tags(cell_html)
        cell = text
    if tag_m:
        if isinstance(cell, str):
            cell = {"t": cell}
        cell["tag"] = {"text": strip_tags(tag_m.group(2)), "cls": tag_m.group(1)}
    return cell


def section_block(sec_id):
    m = re.search(r'(<section id="%s".*?</section>)' % sec_id, html_text, re.S)
    assert m, f"no section {sec_id}"
    return m.group(1)


# ---------- table sections ----------
for sec_id in TABLE_SECTIONS:
    block = section_block(sec_id)
    tbl = re.search(r'<div class="tw"><table>(.*?)</table></div>', block, re.S)
    assert tbl, f"no table in {sec_id}"
    inner = tbl.group(1)
    rows = []
    header_html = ""
    for tr in re.finditer(r"<tr>(.*?)</tr>", inner, re.S):
        if "<th>" in tr.group(1):
            header_html = tr.group(1)
            continue
        cells = [parse_cell(c) for c in re.findall(r"<td>(.*?)</td>", tr.group(1), re.S)]
        rows.append(cells)
    data = {"rows": rows}
    (BASE / "data" / f"sec-{sec_id}.js").write_text(
        f"window.SEC_{sec_id.upper()} = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"data/sec-{sec_id}.js: {len(rows)} rows")
    # rewrite table: keep header in <thead>, empty <tbody id="body-...">
    new_table = ('<div class="tw"><table><thead><tr>' + header_html +
                 '</tr></thead><tbody id="body-' + sec_id + '"></tbody></table></div>')
    new_block = block.replace(tbl.group(0), new_table)
    html_text = html_text.replace(block, new_block)

# ---------- videos ----------
block = section_block("videos")
cards = []
for cm in re.finditer(r'<div class="video-card">(.*?)</div>\s*</div>', block, re.S):
    c = cm.group(1)
    link = re.search(r'<a href="([^"]+)"', c)
    title = re.search(r'<strong><a href="[^"]+"[^>]*>([^<]*)</a></strong>(.*)', c, re.S)
    vid = re.search(r"[?&]v=([A-Za-z0-9_-]+)", link.group(1)) if link else None
    assert link and title and vid, "bad video card"
    cards.append({
        "id": vid.group(1),
        "t": strip_tags(title.group(1)),
        "u": htmlmod.unescape(link.group(1)),
        "d": strip_tags(title.group(2)),
    })
(BASE / "data" / "sec-videos.js").write_text(
    "window.SEC_VIDEOS = " + json.dumps({"items": cards}, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"data/sec-videos.js: {len(cards)} cards")
new_block = re.sub(r'<div class="videos">.*?</div>\s*(?=<p class="note">)',
                   '<div class="videos" id="videos-grid"></div>', block, count=1, flags=re.S)
assert 'id="videos-grid"' in new_block, "videos grid replace failed"
html_text = html_text.replace(block, new_block)

# ---------- archive ----------
block = section_block("archive")
items = []
for li in re.finditer(r"<li>(.*?)</li>", block, re.S):
    c = li.group(1)
    m = re.search(r'<strong>([^<]*)</strong><span class="tag ([^"]+)">([^<]*)</span><br>(.*)',
                  c, re.S)
    assert m, f"bad archive item: {c[:60]}"
    items.append({
        "t": strip_tags(m.group(1)),
        "tag": {"text": strip_tags(m.group(3)), "cls": m.group(2)},
        "d": strip_tags(m.group(4)),
    })
(BASE / "data" / "sec-archive.js").write_text(
    "window.SEC_ARCHIVE = " + json.dumps({"items": items}, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"data/sec-archive.js: {len(items)} items")
new_block = re.sub(r"<ul>.*?</ul>", '<ul id="archive-list"></ul>', block, count=1, flags=re.S)
assert 'id="archive-list"' in new_block, "archive list replace failed"
html_text = html_text.replace(block, new_block)

# ---------- script tags: add section data files before app.js ----------
old_scripts = ('<script src="data/news.js"></script>\n'
               '<script src="data/x.js"></script>\n'
               '<script src="app.js"></script>')
new_scripts = ('<script src="data/news.js"></script>\n'
               '<script src="data/x.js"></script>\n' +
               ''.join(f'<script src="data/sec-{s}.js"></script>\n'
                       for s in TABLE_SECTIONS + ["videos", "archive"]) +
               '<script src="app.js"></script>')
assert old_scripts in html_text, "script block not found"
html_text = html_text.replace(old_scripts, new_scripts)

SRC.write_text(html_text, encoding="utf-8")
print("index.html rewritten; new size:", SRC.stat().st_size)
