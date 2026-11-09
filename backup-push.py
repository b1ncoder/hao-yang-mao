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
    "index.html",
    "style.css",
    "app.js",
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
    "README.md",
    "split-page.py",
    "split-sections.py",
    "push-page.py",
    "backup-push.py",
]


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
        data.decode("utf-8")  # raises on non-UTF-8
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
