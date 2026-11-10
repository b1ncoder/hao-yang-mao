#!/usr/bin/env python3
"""舰队展示页构建脚本：data/fleet.js + fleet.template.html -> fleet.html。

用法：python3 build-fleet.py（在 ~/workspace/goals/pro/pages/ 下运行）
fleet.html 是生成物，不要手改；改数据改 data/fleet.js，改结构改
fleet.template.html，再跑本脚本。发布时只传 fleet.html（首页 nav 已链
到它；首页本身由 build-static.py 生成，改 nav 后须另跑一次主构建）。
"""
import hashlib
import html as htmlmod
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def esc(s):
    return htmlmod.escape(str("" if s is None else s), quote=True)


def load_data(name):
    txt = (BASE / "data" / f"{name}.js").read_text(encoding="utf-8")
    m = re.match(r"window\.\w+\s*=\s*(\{[\s\S]*\});\s*$", txt)
    return json.loads(m.group(1))


def main():
    data = load_data("fleet")
    updated = str(data.get("updated", ""))
    updated_date = updated[:10]

    pipeline = "".join(
        f'<li><strong>{esc(p["step"])}：{esc(p["who"])}</strong><br>{esc(p["what"])}</li>'
        for p in data.get("pipeline", []))
    rows = "".join(
        "<tr>"
        f'<td><strong>{esc(h["name"])}</strong></td>'
        f'<td>{esc(h["role"])}</td>'
        f'<td>{esc(h["spec"])}</td>'
        f'<td><span class="tag {esc(h["statusCls"])}">{esc(h["status"])}</span></td>'
        f'<td>{esc(h["usage"])}</td>'
        f'<td>{esc(h["note"])}</td>'
        "</tr>"
        for h in data.get("hosts", []))

    template = (BASE / "fleet.template.html").read_text(encoding="utf-8")
    style_v = hashlib.sha1((BASE / "style.css").read_bytes()).hexdigest()[:10]
    html = (template
            .replace("{{STYLEV}}", style_v)
            .replace("{{UPDATED}}", esc(updated))
            .replace("{{UPDATED_DATE}}", esc(updated_date))
            .replace("{{PIPELINE}}", pipeline)
            .replace("{{ROWS}}", rows))
    assert "{{" not in html, "模板占位符未替换完"
    (BASE / "fleet.html").write_text(html, encoding="utf-8")
    print(f"舰队页构建完成 fleet.html {len(html)} 字节，更新时间 {updated}，成员 {len(data.get('hosts', []))} 台")


if __name__ == "__main__":
    sys.exit(main())
