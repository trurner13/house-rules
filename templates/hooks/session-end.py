#!/usr/bin/env python3
"""SessionEnd hook -- archives the session transcript so it outlives Claude Code's cleanup.

OPT-IN. The kit's settings.json does not wire this hook; a repo that wants the
archive adds the block below to .claude/settings.json (the sync lays the script
down either way). Before opting in, know what it keeps: every session transcript,
in full -- code, command output, file contents and everything the agent read --
written unencrypted to a folder in the user's home directory, kept with no purge.

  "SessionEnd": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv",
          "args": ["run", "--no-sync", "python",
                   "${CLAUDE_PROJECT_DIR}/.claude/hooks/session-end.py"],
          "timeout": 10
        }
      ]
    }
  ]

Why this exists: the rule "Retain all agent sessions end-to-end" was prose until
2026-10-12. Claude Code deletes local transcripts after `cleanupPeriodDays` (30 by
default), so every session older than a month was being lost. The kit's settings.json
sets a long retention period; this hook, in a repo that wires it, also copies each
transcript out of Claude Code's own store, which the retention sweep never touches.

Where: <home>/.claude/session-archive/<repo-name>/<session-id>.jsonl
  - per machine, never inside the repo: a transcript holds code, command output and
    everything the agent read, which is private data under the lethal-trifecta rule.
  - the raw JSONL format is internal to Claude Code and changes between versions; the
    archive is for a future consolidation pass to parse, not a stable contract.

SessionEnd cannot block and shares a 1.5 s budget unless the hook sets its own timeout
(the wiring block above gives this one 10 s). It may never fire (a killed process); the archive
is best-effort and the retention setting is the backstop.

Standard library only, Python 3.9+; runs on Windows, Linux and macOS alike (the
PowerShell original, session-end.ps1, was retired 2026-10-30). Opt-in: see the top of
this docstring. See agent-constraints/session-lifecycle.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def find_exe(name: str) -> str | None:
    """Find a program on PATH only, never in the current directory.

    On Windows, starting a bare "git" also searches the current directory first, and a
    hook's current directory is the repo: a cloned repo carrying its own git.exe would
    run at session start. So the path is resolved here, from absolute PATH entries only.
    """
    win = sys.platform == "win32"
    exts = [e for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e] if win else [""]
    for d in os.environ.get("PATH", "").split(os.pathsep):
        d = d.strip().strip('"')
        if not d or not os.path.isabs(d):
            continue
        for ext in exts:
            p = os.path.join(d, name + ext)
            if os.path.isfile(p) and (win or os.access(p, os.X_OK)):
                return p
    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        data = json.loads(raw)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    src_text = data.get("transcript_path")
    if not src_text:
        return 0
    src = Path(src_text)
    if not src.is_file():
        return 0

    # The repo is resolved from THIS SCRIPT'S location, never the caller's working directory.
    here = Path(__file__).resolve().parent
    repo = "unknown-repo"
    git_exe = find_exe("git")
    try:
        if git_exe:
            # --git-common-dir names the main checkout's .git, so a session in a worktree
            # (.claude/worktrees/<id>) still archives under the repo's own name. It is
            # relative to `here` on some git versions and absolute on others, so resolve it
            # against `here`. (--path-format=absolute is not used: git before 2.31 echoes an
            # unknown rev-parse option back with exit 0 instead of failing.)
            res = subprocess.run(
                [git_exe, "-C", str(here), "rev-parse", "--git-common-dir"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            )
            out = res.stdout.strip()
            if res.returncode == 0 and out and "\n" not in out:
                common = (here / out).resolve()
                name = common.parent.name if common.name == ".git" else common.name
                if name and re.fullmatch(r"[^\x00-\x1f/\\]+", name):
                    repo = name
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass

    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or str(Path.home())
    dst_dir = Path(home) / ".claude" / "session-archive" / repo
    dst_dir.mkdir(parents=True, exist_ok=True)

    # The id becomes a file name: only a plain name is accepted, so "../x" or "/x" can
    # never write outside the archive folder.
    safe = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
    session_id = data.get("session_id")
    if not (isinstance(session_id, str) and safe.fullmatch(session_id)):
        # Fall back to the transcript's own name, else a name derived from the id and
        # path, so two odd sessions never overwrite each other's archive.
        if safe.fullmatch(src.stem):
            session_id = src.stem
        else:
            seed = f"{data.get('session_id')!r}|{src}".encode("utf-8", "replace")
            session_id = "session-" + hashlib.sha256(seed).hexdigest()[:16]
    dst = dst_dir / f"{session_id}{src.suffix}"
    shutil.copyfile(src, dst)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - best effort: a failed archive must never fail the session
        sys.exit(0)
