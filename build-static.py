#!/usr/bin/env python3
"""薅羊毛公开页构建脚本：静态预渲染（SSR）+ 合并 bundle.js。

用法：python3 build-static.py
在 ~/workspace/goals/pro/pages/ 下运行。

做三件事（缺一不可，顺序固定）：
  1. 繁简转换：把 data/news.js、data/x.js 里的繁体中文转简体（OpenCC t2s；
     没装 opencc 时跳过并警告，不中断构建）。
  2. 静态预渲染：按 data/*.js 把新闻、X 两区、7 张栏目表、视频、归档、
     统计卡、“最后更新”直接写进 index.html（以 index.template.html 为模板）。
     index.html 是生成物，不要手改；改结构请改 index.template.html 再跑构建。
  3. 合并 bundle.js：data/*.js（按页面加载顺序）+ app.js 合成一个文件，
     首页只加载 bundle.js（1 个请求）+ style.css + index.html 本身。
     bundle 开头写入 window.SITE_BUILD（含 stamp：全部数据文件的 SHA1 前 10 位），
     首页 <body data-build="..."> 写同一 stamp；app.js 启动时比对，
     不一致就用 bundle 里的数据强制重渲染（自愈：防止只传了 bundle 没传首页）。

同时刷新 feed.xml（新闻 + Pro）与 sitemap.xml 的 lastmod。

每次改完任何 data/*.js 后都必须跑一遍本脚本，再上传 bundle.js + index.html
（只传数据文件不会更新页面内容——页面内容已经在 index.html 里了）。
构建完用 node --check bundle.js 检查语法；jsdom 抽查见 OPTIMIZATION-NOTES.md。
"""
import hashlib
import html as htmlmod
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_ORDER = ["news", "x", "sec-pro", "sec-domain", "sec-ai", "sec-cloud",
              "sec-esim", "sec-student", "sec-server", "sec-videos", "sec-archive"]
SECTIONS = ["pro", "domain", "ai", "cloud", "esim", "student", "server"]


def esc(s):
    return htmlmod.escape(str("" if s is None else s), quote=True)


def safe_url(u):
    v = str("" if u is None else u).strip()
    return v if re.match(r"^https?://", v, re.I) else "#"


def load_data(name):
    txt = (BASE / "data" / f"{name}.js").read_text(encoding="utf-8")
    m = re.match(r"window\.\w+\s*=\s*(\{[\s\S]*\});\s*$", txt)
    return json.loads(m.group(1))


def t2s_convert():
    try:
        import opencc
    except ImportError:
        print("警告：未装 opencc，跳过繁简转换（pip install --break-system-packages opencc-python-reimplemented）")
        return
    cc = opencc.OpenCC("t2s")
    for name in ("news", "x"):
        p = BASE / "data" / f"{name}.js"
        txt = p.read_text(encoding="utf-8")
        m = re.match(r"(window\.\w+\s*=\s*)(\{[\s\S]*\});\s*$", txt)
        data = json.loads(cc.convert(json.dumps(json.loads(m.group(2)), ensure_ascii=False)))
        p.write_text(f"{m.group(1)}{json.dumps(data, ensure_ascii=False, separators=(',', ':'))};\n",
                     encoding="utf-8")
    print("繁简转换完成：news.js、x.js 已转简体")


def render_news(data):
    out = []
    for it in data.get("items", []):
        if it.get("zh"):
            out.append(
                '<article class="news-item"><div class="news-bi">'
                f'<div class="news-en"><a href="{esc(safe_url(it.get("u")))}" target="_blank" rel="noopener">{esc(it.get("t"))}</a></div>'
                f'<div class="news-zh">{esc(it.get("zh"))}</div></div>'
                f'<div class="news-meta">{esc(it.get("s"))} · {esc(it.get("d"))}</div></article>')
        else:
            out.append(
                '<article class="news-item">'
                f'<div class="news-en"><a href="{esc(safe_url(it.get("u")))}" target="_blank" rel="noopener">{esc(it.get("t"))}</a></div>'
                f'<div class="news-meta">{esc(it.get("s"))} · {esc(it.get("d"))}</div></article>')
    return "".join(out)


def render_x_section(sec_id, snaps):
    is_news = sec_id == "xnews"
    tag_html = ['<span class="x-tags-note">时段：</span>']
    snap_html = []
    for i, snap in enumerate(snaps or []):
        h = snap["hour"]
        hh = h[11:]
        on = ' class="on" aria-pressed="true"' if i == 0 else ' aria-pressed="false"'
        tag_html.append(f'<button data-hour="{esc(h)}"{on} title="{esc(h)}">{esc(hh)}</button>')
        hidden = "" if i == 0 else " hidden"
        cap = "X 新闻热门 " if is_news else "X 羊毛热门 "
        s = f'<div class="x-snap" data-hour="{esc(h)}"{hidden}><div class="tw"><table>'
        if is_news:
            s += (f'<caption class="visually-hidden">{esc(cap + h)}</caption><thead><tr>'
                  '<th scope="col">话题</th><th scope="col">一句话</th><th scope="col">时间</th><th scope="col">链接</th>'
                  '</tr></thead><tbody>')
            for r in snap["rows"]:
                s += (f'<tr><td>{esc(r["topic"])}</td><td>{esc(r["desc"])}</td><td>{esc(r["time"])}</td>'
                      f'<td><a href="{esc(safe_url(r["url"]))}" target="_blank" rel="noopener">{esc(r["label"])}</a></td></tr>')
        else:
            s += (f'<caption class="visually-hidden">{esc(cap + h)}</caption><thead><tr>'
                  '<th scope="col">帖子</th><th scope="col">内容</th><th scope="col">作者</th><th scope="col">状态</th><th scope="col">链接</th>'
                  '</tr></thead><tbody>')
            if not snap["rows"]:
                s += '<tr class="x-empty"><td colspan="5">本小时暂无新热门羊毛帖。</td></tr>'
            else:
                for r in snap["rows"]:
                    note = f'<br><span class="bad">{esc(r["note"])}</span>' if r.get("note") else ""
                    rel = "noopener" if r.get("statusClass") == "ok" else "noopener nofollow"
                    s += (f'<tr><td>{esc(r["post"])}</td><td>{esc(r["content"])}{note}</td><td>{esc(r["author"])}</td>'
                          f'<td><span class="tag {esc(r["statusClass"])}">{esc(r["status"])}</span></td>'
                          f'<td><a href="{esc(safe_url(r["url"]))}" target="_blank" rel="{rel}">{esc(r["label"])}</a></td></tr>')
        s += "</tbody></table></div></div>"
        snap_html.append(s)
    return "".join(tag_html), "".join(snap_html)


def cell_html(cell, first):
    if isinstance(cell, str):
        return f"<strong>{esc(cell)}</strong>" if first else esc(cell)
    main = (f'<a href="{esc(safe_url(cell.get("u")))}" target="_blank" rel="noopener">{esc(cell.get("t"))}</a>'
            if cell.get("u") else esc(cell.get("t")))
    if cell.get("bad"):
        main = f'<span class="bad">{main}</span>'
    tag = cell.get("tag")
    tag_html = f' <span class="tag {esc(tag["cls"])}">{esc(tag["text"])}</span>' if tag else ""
    return (f"<strong>{main}</strong>{tag_html}" if first else f"{main}{tag_html}")


def render_table(data):
    out = []
    for row in data.get("rows", []):
        out.append("<tr>" + "".join(f"<td>{cell_html(c, i == 0)}</td>" for i, c in enumerate(row)) + "</tr>")
    return "".join(out)


def render_videos(data):
    out = []
    for v in data.get("items", []):
        out.append(
            '<div class="video-card">'
            f'<a href="{esc(safe_url(v["u"]))}" target="_blank" rel="noopener">'
            f'<img src="https://i.ytimg.com/vi/{esc(v["id"])}/maxresdefault.jpg" '
            f'srcset="https://i.ytimg.com/vi/{esc(v["id"])}/mqdefault.jpg 320w, '
            f'https://i.ytimg.com/vi/{esc(v["id"])}/maxresdefault.jpg 1280w" '
            'sizes="(max-width: 600px) 100vw, 50vw" width="1280" height="720" '
            f'onerror="this.onerror=null;this.src=&#39;https://i.ytimg.com/vi/{esc(v["id"])}/hqdefault.jpg&#39;" '
            f'alt="{esc(v["t"])}" loading="lazy"></a>'
            f'<div><strong><a href="{esc(safe_url(v["u"]))}" target="_blank" rel="noopener">{esc(v["t"])}</a></strong>'
            f'{esc(v["d"])}</div></div>')
    return "".join(out)


def render_archive(data):
    out = []
    for it in data.get("items", []):
        tag = it.get("tag")
        tag_html = f'<span class="tag {esc(tag["cls"])}">{esc(tag["text"])}</span>' if tag else ""
        out.append(f'<li><strong>{esc(it["t"])}</strong>{tag_html}<br>{esc(it["d"])}</li>')
    return "".join(out)


def main():
    t2s_convert()
    data = {name: load_data(name) for name in DATA_ORDER}

    # stamp：全部数据文件原文的 SHA1 前 10 位
    h = hashlib.sha1()
    for name in DATA_ORDER:
        h.update((BASE / "data" / f"{name}.js").read_bytes())
    stamp = h.hexdigest()[:10]

    news = data["news"]
    x = data["x"]
    updated_date = str(news.get("updated", ""))[:10]
    x_latest = (x.get("news") or [{}])[0].get("hour", "")

    template = (BASE / "index.template.html").read_text(encoding="utf-8")
    html = template
    html = html.replace("<body>", f'<body data-build="{stamp}" data-news="{esc(news.get("updated", ""))}" data-x="{esc(x_latest)}">')
    html = html.replace("bundle.js?v=BUILD", f"bundle.js?v={stamp}")
    # style.css 也按内容哈希加版本：改了样式就换 URL，旧缓存不会继续用老样式
    style_v = hashlib.sha1((BASE / "style.css").read_bytes()).hexdigest()[:10]
    html = html.replace("style.css?v=STYLEV", f"style.css?v={style_v}")
    html = html.replace('"dateModified":"2026-11-09"', f'"dateModified":"{updated_date}"')
    html = html.replace('<span id="last-updated">2026-11-09</span>', f'<span id="last-updated">{updated_date}</span>')
    html = html.replace('<span class="last-updated">2026-11-09</span>', f'<span class="last-updated">{updated_date}</span>')
    html = html.replace('<p class="news-updated" id="news-updated"></p>',
                        f'<p class="news-updated" id="news-updated">最后刷新：{esc(news.get("updated", ""))}</p>')
    html = html.replace('<div id="news-list"></div>', f'<div id="news-list">{render_news(news)}</div>')
    for sec_id, key in (("xnews", "news"), ("xwool", "wool")):
        tags, snaps = render_x_section(sec_id, x.get(key, []))
        html = html.replace(f'<div class="x-tags" id="tags-{sec_id}"></div>', f'<div class="x-tags" id="tags-{sec_id}">{tags}</div>')
        html = html.replace(f'<div id="snaps-{sec_id}"></div>', f'<div id="snaps-{sec_id}">{snaps}</div>')
    total = 0
    stats = {}
    for sec in SECTIONS:
        rows_html = render_table(data[f"sec-{sec}"])
        html = html.replace(f'<tbody id="body-{sec}"></tbody>', f'<tbody id="body-{sec}">{rows_html}</tbody>')
        n = len(data[f"sec-{sec}"].get("rows", []))
        stats[sec] = n
        total += n
    stats["total"] = total
    for key in ("xnews", "xwool"):
        snaps = x.get("news" if key == "xnews" else "wool", [])
        n = 0
        if snaps:
            n = len([r for r in snaps[0].get("rows", [])])
        stats[key] = n
    for key, n in stats.items():
        html = re.sub(rf'(<b id="stat-{key}">)\d+(</b>)', rf'\g<1>{n}\g<2>', html)
    html = html.replace('<div class="videos" id="videos-grid"></div>',
                        f'<div class="videos" id="videos-grid">{render_videos(data["sec-videos"])}</div>')
    html = html.replace('<ul id="archive-list"></ul>',
                        f'<ul id="archive-list">{render_archive(data["sec-archive"])}</ul>')
    (BASE / "index.html").write_text(html, encoding="utf-8")

    # bundle.js：数据（原样拼接）+ app.js
    parts = [f'window.SITE_BUILD = {json.dumps({"stamp": stamp, "news": news.get("updated", ""), "x": x_latest}, ensure_ascii=False)};']
    for name in DATA_ORDER:
        parts.append((BASE / "data" / f"{name}.js").read_text(encoding="utf-8"))
    parts.append((BASE / "app.js").read_text(encoding="utf-8"))
    bundle = "\n".join(parts)
    (BASE / "bundle.js").write_text(bundle, encoding="utf-8")

    # feed.xml 与 sitemap.xml 刷新
    items = []
    for it in news.get("items", []):
        title = it.get("zh") or it["t"]
        items.append(f'<item><title>{esc(title)}</title><link>{esc(it["u"])}</link>'
                     f'<guid>{esc(it["u"])}</guid><description>{esc(it["t"])}（{esc(it["s"])}）</description>'
                     f'<pubDate>{esc(it["d"])}</pubDate></item>')
    for row in data["sec-pro"].get("rows", []):
        c0 = row[0]
        t = c0["t"] if isinstance(c0, dict) else c0
        u = c0.get("u", "https://freenofree.ct.ws/") if isinstance(c0, dict) else "https://freenofree.ct.ws/"
        items.append(f'<item><title>{esc("Pro：" + t)}</title><link>{esc(u)}</link>'
                     f'<guid>{esc(u + "#" + t)}</guid><description>{esc(row[1])}；{esc(row[2])}</description></item>')
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            '<title>薅羊毛情报站 — 最新科技新闻</title><link>https://freenofree.ct.ws/</link>'
            '<description>只收录官方可验证的免费羊毛：免费 Pro、免费域名、AI 免费额度、大云试用金、免费 eSIM、学生福利、免费服务器，每天核验更新。</description>'
            f'<language>zh-CN</language><lastBuildDate>{esc(news.get("updated", ""))}</lastBuildDate>\n'
            + "\n".join(items) + "\n</channel></rss>\n")
    (BASE / "feed.xml").write_text(feed, encoding="utf-8")
    (BASE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>https://freenofree.ct.ws/</loc><lastmod>{updated_date}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
        f'  <url><loc>https://freenofree.ct.ws/fleet.html</loc><lastmod>{updated_date}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>\n'
        f'  <url><loc>https://freenofree.ct.ws/feed.xml</loc><lastmod>{updated_date}</lastmod><changefreq>daily</changefreq><priority>0.5</priority></url>\n'
        '</urlset>\n', encoding="utf-8")

    print(f"构建完成 stamp={stamp} news={news.get('updated')} x最新={x_latest}")
    print(f"index.html {len(html)} 字节，bundle.js {len(bundle)} 字节，统计 {stats}")


if __name__ == "__main__":
    sys.exit(main())
