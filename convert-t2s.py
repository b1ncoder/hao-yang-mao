#!/usr/bin/env python3
"""把 data/news.js 与 data/x.js 里的繁体中文转简体（OpenCC t2s）。

用法：python3 convert-t2s.py [data/news.js data/x.js ...]
默认处理 news.js 与 x.js。需要 pip install opencc-python-reimplemented。
新闻 / X 每小时 cron 写完数据文件后跑一遍，再同步上传。
只转中文字符串内容；英文标题、链接、时间戳不受影响。
"""
import json
import re
import sys
from pathlib import Path

FILES = sys.argv[1:] or ["data/news.js", "data/x.js"]

try:
    import opencc
except ImportError:
    print("缺少 opencc：pip install --break-system-packages opencc-python-reimplemented")
    sys.exit(1)

cc = opencc.OpenCC("t2s")
for f in FILES:
    p = Path(f)
    txt = p.read_text(encoding="utf-8")
    m = re.match(r"(window\.\w+\s*=\s*)(\{[\s\S]*\});\s*$", txt)
    if not m:
        print(f"跳过（格式不符）: {f}")
        continue
    data = json.loads(m.group(2))
    converted = json.loads(cc.convert(json.dumps(data, ensure_ascii=False)))
    p.write_text(f"{m.group(1)}{json.dumps(converted, ensure_ascii=False, separators=(',', ':'))};\n", encoding="utf-8")
    print(f"已转简体: {f}")
