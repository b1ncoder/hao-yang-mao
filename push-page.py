#!/usr/bin/env python3
"""Push the local wool-intel page to GitHub Pages.

Usage:
    python3 push-page.py ["commit message"]

Reads ~/workspace/goals/pro/pages/index.html (the desensitized public
version), fetches the current blob SHA from b1ncoder/hao-yang-mao, and
updates index.html on the main branch via the GitHub connector.

The local file is the source of truth: edit it first (keeping the
public-page desensitization rule — no email, phone, account names,
order numbers, or personal claim/holding status), then run this script.
GitHub Pages redeploys automatically, usually within a minute.
"""
import json
import subprocess
import sys

OWNER = "b1ncoder"
REPO = "hao-yang-mao"
PATH = "index.html"
BRANCH = "main"
LOCAL = "/home/hatch/workspace/goals/pro/pages/index.html"
GH = "/opt/hatch/bin/github"


def gh(*args):
    r = subprocess.run([GH, *args], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print("github CLI failed:", r.stdout, r.stderr, file=sys.stderr)
        sys.exit(1)
    return json.loads(r.stdout)


def main():
    message = sys.argv[1] if len(sys.argv) > 1 else "Update wool intel page"
    with open(LOCAL, encoding="utf-8") as f:
        content = f.read()

    got = gh(
        "call-read-tool",
        "--name", "get_file_contents",
        "--arguments-json",
        json.dumps({"owner": OWNER, "repo": REPO, "path": PATH, "ref": BRANCH}),
    )
    text = got["result"]["content"][0]["text"]
    # e.g. "successfully downloaded text file (SHA: <sha>)"
    sha = text.rsplit("SHA: ", 1)[1].rstrip(")")
    print("current SHA:", sha)

    out = gh(
        "call-tool",
        "--name", "create_or_update_file",
        "--arguments-json",
        json.dumps({
            "owner": OWNER, "repo": REPO, "path": PATH,
            "content": content, "message": message,
            "branch": BRANCH, "sha": sha,
        }),
    )
    print(json.dumps(out, ensure_ascii=False)[:500])


if __name__ == "__main__":
    main()
