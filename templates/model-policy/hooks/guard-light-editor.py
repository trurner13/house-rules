#!/usr/bin/env python3
"""PreToolUse hook on Edit and Write, run only while the light-editor helper runs (templates/model-policy/).

Refuses an edit to a path on the protected list of the repo the file really lives in: the nearest folder above it holding
.git, so a session cannot use one repo's list on another repo's file, and a worktree's files are matched from the worktree.
Exit 2 blocks the call. Refuses on anything it cannot read. It can refuse only when it runs: a missing script or interpreter
lets the edit through, so the lead still reads every diff.

Standard library only, Python 3.9+. Held to its cases by templates/model-policy/test-model-policy-hooks.py.
"""

from __future__ import annotations

import datetime
import fnmatch
import json
import os
import pathlib
import re
import sys
import uuid


def log_decision(repo: str, decision: str, path: str) -> None:
    try:
        folder = pathlib.Path(os.environ.get("MODEL_TRIAL_DIR") or pathlib.Path.home() / ".claude" / "model-trial")
        folder.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now()
        name = f"guard-{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex}.txt"
        (folder / name).write_text(f"guard|{now:%Y-%m-%d}|{repo}|{decision}|{path}\n", encoding="utf-8")
    except OSError:
        pass


def block(why: str, repo: str = "", path: str = "") -> None:
    log_decision(repo, "refused", path)
    print(f"REFUSED by .claude/hooks/guard-light-editor.py: {why}.", file=sys.stderr)
    print("Stop and report this to the lead. Do not look for another way to make the change.", file=sys.stderr)
    sys.exit(2)


def find_root(full: str) -> str | None:
    folder = os.path.dirname(full)
    while True:
        if os.path.exists(os.path.join(folder, ".git")):
            return folder
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent


def matches(relative: str, entry: str) -> bool:
    if entry.endswith("/"):
        return relative.startswith(entry)
    return relative == entry or fnmatch.fnmatchcase(relative, entry)


def main() -> None:
    try:
        path = str(json.load(sys.stdin)["tool_input"]["file_path"])
    except (OSError, ValueError, KeyError, TypeError):
        block("could not read the hook input")
    if not path.strip():
        block("the edit names no file")

    # realpath follows symlinks and junctions, so a link inside an allowed folder that points at a
    # protected file is judged by where it really leads.
    full = os.path.realpath(os.path.abspath(path))
    root = find_root(full)
    if root is None:
        block("the file is in no repository", "", full)
    repo = os.path.basename(root.rstrip("\\/")) or root
    relative = os.path.relpath(full, root).replace("\\", "/").lower()

    for segment in relative.split("/"):
        if ":" in segment or re.search(r"[. ]$", segment) or re.search(r"~\d", segment):
            block("the path has a form that could hide its real name", repo, relative)
        if segment in (".git", ".claude"):
            block(f"{relative} is inside a {segment} folder", repo, relative)

    listing = os.path.join(root, ".claude", "protected-paths.txt")
    try:
        with open(listing, encoding="utf-8") as lines:
            entries = [line.strip().lower().replace("\\", "/") for line in lines]
    except OSError:
        block("this repository has no protected list", repo, relative)

    for entry in entries:
        if entry and not entry.startswith("#") and matches(relative, entry):
            block(f"{relative} is on the protected list", repo, relative)

    log_decision(repo, "allowed", relative)


if __name__ == "__main__":
    main()
