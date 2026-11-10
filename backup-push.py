#!/usr/bin/env python3
"""Back up the modular wool-intel site to the GitHub `backup` branch.

Usage:
    python3 backup-push.py ["commit message"]

Pushes the current site files from ~/workspace/goals/pro/pages/ to
b1ncoder/hao-yang-mao on branch `backup` (never main, so GitHub Pages
is untouched) as one snapshot commit, via the GitHub connector's
`push-files` tool. Skips the push when nothing changed since the last
recorded backup. Records each confirmed push in the adjacent sync
record (see SNAPSHOT_PUSH.md notes in the GitHub connector docs).

The `backup` branch is write-only from this script: never edit it
directly on GitHub, or the next snapshot will overwrite those edits.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

OWNER = "b1ncoder"
REPO = "hao-yang-mao"
BRANCH = "backup"
SOURCE_DIR = "/home/hatch/workspace/goals/pro/pages"
RECORD = "/home/hatch/workspace/goals/pro/pages.muse-github-snapshot-sync.json"
MANIFEST = "/tmp/wool-backup-manifest"
GH = "/opt/hatch/bin/github"

FILES = [
    "index.html",          # 生成物（build-static.py 产出，不要手改）
    "index.template.html", # 首页模板（改结构改这里，再跑构建）
    "build-static.py",     # 构建脚本：繁简转换 + 静态预渲染 + 合并 bundle
    "convert-t2s.py",      # 繁简转换（构建脚本内部也会跑）
    "style.css",
    "app.js",              # 交互逻辑源码（bundle.js 由它 + 数据文件合成）
    "bundle.js",           # 生成物：数据 + app.js 合一，首页唯一加载的脚本
    "fleet.html",          # 生成物（build-fleet.py 产出，不要手改）
    "fleet.template.html", # 舰队页模板（改结构改这里，再跑 build-fleet.py）
    "build-fleet.py",      # 舰队页构建脚本：data/fleet.js + 模板 -> fleet.html
    "data/fleet.js",
    "data/news.js",
    "data/x.js",
    "data/sec-pro.js",
    "data/sec-domain.js",
    "data/sec-ai.js",
    "data/sec-cloud.js",
    "data/sec-esim.js",
    "data/sec-student.js",
    "data/sec-server.js",
    "data/sec-videos.js",
    "data/sec-archive.js",
    ".htaccess",
    "robots.txt",
    "sitemap.xml",
    "404.html",
    "feed.xml",
    "README.md",
    "OPTIMIZATION-NOTES.md",
    "split-page.py",
    "split-sections.py",
    "push-page.py",
    "backup-push.py",
]
# og.png 是二进制文件，github push-files 只接受 UTF-8 快照，无法推送，
# 故不列入备份清单（本地与 InfinityFree 上各有一份）。


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def load_record():
    if not os.path.exists(RECORD):
        return []
    with open(RECORD, encoding="utf-8") as f:
        return json.load(f)


def save_record(entries):
    tmp = "%s.tmp-%d" % (RECORD, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RECORD)


def main():
    message = sys.argv[1] if len(sys.argv) > 1 else (
        "Backup wool intel site " + time.strftime("%Y-%m-%d %H:%M SGT", time.localtime())
    )

    # Read and validate every file (UTF-8, size bound).
    contents = {}
    total = 0
    for rel in FILES:
        path = os.path.join(SOURCE_DIR, rel)
        if not os.path.exists(path):
            print("missing file:", rel, file=sys.stderr)
            return 1
        with open(path, "rb") as f:
            data = f.read()
        data.decode("utf-8")  # 清单内全是文本文件；二进制文件不进备份
        contents[rel] = data
        total += len(data)
    if total > 16 * 1024 * 1024:
        print("snapshot too large:", total, file=sys.stderr)
        return 1

    # Skip when nothing changed since the last recorded backup.
    digest = hashlib.sha256()
    for rel in sorted(contents):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(contents[rel])
        digest.update(b"\0")
    content_hash = digest.hexdigest()
    entries = load_record()
    if entries:
        last = entries[-1]
        if (
            last.get("owner") == OWNER
            and last.get("repo") == REPO
            and last.get("branch") == BRANCH
            and last.get("content_sha256") == content_hash
        ):
            print("no changes since", last.get("commit_sha"), "- skipped")
            return 0

    # NUL-delimited manifest, outside the source directory.
    with open(MANIFEST, "wb") as f:
        for rel in FILES:
            f.write(rel.encode("utf-8") + b"\0")

    r = subprocess.run(
        [GH, "push-files", "--owner", OWNER, "--repo", REPO,
         "--branch", BRANCH, "--message", message,
         "--source-dir", SOURCE_DIR, "--paths-file", MANIFEST],
        capture_output=True, text=True, timeout=300,
    )
    print((r.stdout or "")[:2000])
    if r.returncode != 0:
        print("push-files failed:", r.stderr[:2000], file=sys.stderr)
        return 1

    # Find the confirmed commit SHA in the provider result.
    out = r.stdout or ""
    sha = None
    try:
        parsed = json.loads(out)
        sha = parsed.get("commit_sha") or parsed.get("sha")
        if not sha:
            # dig one level: result.content[0].text may hold JSON
            result = parsed.get("result", {})
            content = result.get("content", [])
            if content:
                inner = json.loads(content[0].get("text", "{}"))
                sha = inner.get("sha") or inner.get("commit_sha")
    except Exception:
        pass
    if not sha:
        import re
        m = re.search(r"\b[0-9a-f]{40}\b", out)
        sha = m.group(0) if m else None
    if not sha:
        print("push output has no confirmed commit SHA; record unchanged",
              file=sys.stderr)
        return 1

    entries.append({
        "owner": OWNER, "repo": REPO, "branch": BRANCH,
        "source_dir": SOURCE_DIR, "commit_sha": sha,
        "paths": FILES, "content_sha256": content_hash,
    })
    try:
        save_record(entries)
    except Exception as e:
        print("remote write succeeded (%s) but record save failed: %s"
              % (sha, e), file=sys.stderr)
        return 1
    print("backed up as commit", sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
