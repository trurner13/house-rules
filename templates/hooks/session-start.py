#!/usr/bin/env python3
"""SessionStart hook -- prints the work-state digest into the agent's context.

Standard library only, Python 3.9+; runs on Windows, Linux and macOS alike. It replaced
the PowerShell original (session-start.ps1, retired 2026-10-30) section for section, with
the same wording and caps; the two were diffed identical on Windows before the switch.

SessionStart cannot block anything. Its value is that stdout IS added to the
model's context, so the session begins already holding the open issue list and
any in-flight work -- without the agent having to decide to go looking.

Output is STREAMED, section by section, most important first. The hook has a
timeout (settings.json), and on timeout Claude Code discards everything the hook
printed. One slow section can only lose itself and what follows it, and the slow
section is last.

Wired in .claude/settings.json. See agent-constraints/session-lifecycle.md.
"""

from __future__ import annotations

import contextlib
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

UTC = timezone.utc  # datetime.UTC needs 3.11; the hook promises 3.9+

# Windows consoles default to cp1252; the digest holds em-dashes and friends.
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def out(line: str) -> None:
    """Print one line and flush, so a timeout only loses what was not yet printed."""
    print(line, flush=True)


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


GIT = find_exe("git")
GIT_TIMEOUT = 20  # seconds per call at most
# One deadline for the whole digest, under settings.json's 120 s: a slow repo gets a short
# digest that says it stopped, instead of overrunning (Claude Code would discard it all).
# SESSION_DIGEST_BUDGET (seconds) exists so the test can exercise the out-of-time path.
try:
    _BUDGET = float(os.environ.get("SESSION_DIGEST_BUDGET", "100"))
except ValueError:
    _BUDGET = 100.0
if not math.isfinite(_BUDGET):
    _BUDGET = 100.0
DEADLINE = time.monotonic() + min(max(_BUDGET, 0.0), 100.0)


def time_left(cap: float) -> float:
    return max(0.0, min(cap, DEADLINE - time.monotonic()))


def stop_out_of_time() -> None:
    """Out of time: stop here and say so.

    Every section after a skipped or killed git call would rest on missing data (a false
    "nothing to report", a wrong day count), so none is printed: the digest ends here.
    """
    out("")
    out("DIGEST INCOMPLETE: the time budget ran out, so the checks after this point were not "
        "run. Check `git status` and `git log --branches --not --remotes` by hand.")
    out("=== end work state ===")
    sys.exit(0)


def git(*args: str, cwd: Path | str | None = None, first: bool = False) -> str:
    """Run git and return its stdout, or '' on any failure or timeout (nothing to report).

    A call that would be skipped or is killed for time ends the digest (stop_out_of_time),
    so a missing answer is never passed off as "nothing to report".
    """
    if GIT is None:
        return ""
    # The first call (finding the repo) always gets its own 20 s: without it there is no
    # digest at all, and "out of time" would be misreported as "not a git repository".
    budget = GIT_TIMEOUT if first else time_left(GIT_TIMEOUT)
    if budget < 1:
        stop_out_of_time()
    cmd = [GIT]
    if cwd is not None:
        cmd += ["-C", str(cwd)]
    cmd += list(args)
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=budget,
        )
    except subprocess.TimeoutExpired:
        stop_out_of_time()
    except (OSError, ValueError):
        return ""
    if res.returncode != 0:
        return ""
    return res.stdout


def git_lines(*args: str, cwd: Path | str | None = None) -> list[str]:
    return [ln for ln in git(*args, cwd=cwd).splitlines() if ln != ""]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_iso(value: str) -> datetime | None:
    try:
        d = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d


# Resolve the repo from THIS SCRIPT'S location, never the caller's working directory.
# Using the cwd means the script silently prints nothing when run from anywhere else --
# and a hook that fails silently is worse than no hook, because it looks installed.
here = Path(__file__).resolve().parent
root_text = git("rev-parse", "--show-toplevel", cwd=here, first=True).strip()
if not root_text:
    out(f"session-start: '{here}' is not inside a git repository - no work-state digest.")
    sys.exit(0)
root = Path(root_text)

# Claude Code keeps the first 2,000 characters of hook output over 10,000 and spills the
# rest to a file. Stay under the limit so nothing important ends up in the spill.
BUDGET = 9500
written = 0
truncated = False


def emit(lines) -> None:
    global written, truncated
    for ln in lines:
        if truncated:
            return
        if written + len(ln) + 1 > BUDGET:
            out("... (digest truncated to stay under the hook output limit)")
            truncated = True
            return
        out(ln)
        written += len(ln) + 1


out("=== work state (session-start reconciliation) ===")
today = date.today()
now = datetime.now(UTC)

# --- 1. trial reviews that are overdue (guardrails repo) ----------------------
# A trial has a review date, but nothing fires on a date by itself; a TODO item can wait
# months. So the digest says, at the top of every session, which reviews are past due,
# until someone decides adopt / extend / drop.
todo = root / "TODO.md"
if todo.is_file():
    text = read_text(todo)
    sec = re.search(r"## On trial.*?(?=\r?\n## |\Z)", text, re.S | re.I)
    if sec:
        section = sec.group(0)
        overdue = []
        # One item at a time, so an item with no review date never borrows the next one's.
        for item in re.split(r"\r?\n(?=- \[.\] )", section):
            m = re.match(r"- \[.\] \*\*(?P<name>[^*]+)\*\*", item)
            d = re.search(r"Review (?P<date>\d{4}-\d{2}-\d{2})", item)
            if not m or not d:
                continue
            try:
                due = date.fromisoformat(d.group("date"))
            except ValueError:
                continue
            if due <= today:
                name = m.group("name").strip()
                overdue.append(
                    f"  {name}: review was due {d.group('date')} ({(today - due).days} day(s) ago)"
                )
        if overdue:
            emit(['TRIAL REVIEW OVERDUE (TODO.md, "On trial"): the first decision of this '
                  "session is adopt / extend / drop for"])
            emit(overdue)
            emit([""])

# --- 2. open issues ----------------------------------------------------------
# --untracked matters: a just-captured, unstaged issue is the one most at risk.
issues = git_lines(
    "grep", "--untracked", "-h", "-E", "^# 20|^- (status|branch|next): ",
    "--", ":(glob)issues/*.md", cwd=root,
)
if issues:
    # A repo with forty issues and paragraph-long next: lines fills the whole output limit
    # by itself and nothing after it is seen. Each line is clipped and the section is capped;
    # the issue files hold the full text.
    emit(["OPEN ISSUES (issues/ is the tracker; anything noticed gets a file there before the "
          "session moves on):"])
    section_cap = 4500
    used = 0
    shown = 0
    for ln in issues:
        line = ln[:177] + "..." if len(ln) > 180 else ln
        if used + len(line) + 3 > section_cap:
            break
        emit(["  " + line])
        used += len(line) + 3
        shown += 1
    if shown < len(issues):
        emit(["  ... and " + str(len(issues) - shown) + " more line(s); the rest are in issues/."])
else:
    emit(["OPEN ISSUES: none recorded in issues/."])

# Catch issue files that exist but do not parse. Without this the digest reports
# "none recorded" for a malformed file, which reads as "nothing to do".
issue_dir = root / "issues"
if issue_dir.is_dir():
    bad = []
    for f in sorted(issue_dir.glob("*.md"), key=lambda p: p.name.lower()):
        if not f.is_file():
            continue
        t = read_text(f)
        if not re.search(r"^#\s+\S", t, re.M) or not re.search(r"^-\s+status:\s*\S", t, re.M):
            bad.append(f.name)
    if bad:
        emit(["", 'MALFORMED issue file(s), not counted above; each lacks the "# <id> - <title>"',
              '  heading or the "- status: <state>" line (agent-constraints/issue-tracker.md):'])
        emit(["  " + b for b in bad])

# --- 3. in-flight work -------------------------------------------------------
dirty = git_lines("status", "--porcelain=v1", "-uall", cwd=root)
if dirty:
    n = len(dirty)
    emit(["",
          f"UNCOMMITTED: {n} file(s) in this working tree. They are checkpointed onto the branch",
          "  before the turn ends; the exit does not save them."])
    emit(["  " + d for d in dirty[:10]])
    if n > 10:
        emit(["  ... and " + str(n - 10) + " more"])

unpushed = git_lines("log", "--branches", "--not", "--remotes", "--oneline", cwd=root)
if unpushed:
    emit(["", "UNPUSHED commits (they die with this machine):"])
    emit(["  " + u for u in unpushed[:10]])

# --- 4. other worktrees ------------------------------------------------------
# Resume what exists rather than opening a rival.
wt = git_lines("worktree", "list", cwd=root)
if len(wt) > 1:
    emit(["", "WORKTREES already exist; an existing one is resumed rather than a new one created:"])
    emit(["  " + w for w in wt])

# --- 5. rules on trial in this repo (consumer repos) --------------------------
rules_dir = root / ".claude" / "rules"
if rules_dir.is_dir():
    trials = []
    for f in sorted(rules_dir.glob("*.md"), key=lambda p: p.name.lower()):
        if not f.is_file():
            continue
        first = "\n".join(read_text(f).splitlines()[:3])
        m = re.search(r"on trial.*?from (\d{4}-\d{2}-\d{2})", first, re.I)
        if m:
            try:
                since = date.fromisoformat(m.group(1))
            except ValueError:
                continue
            trials.append(
                f"  {f.name}: on trial since {m.group(1)} ({(today - since).days} day(s))"
            )
    if trials:
        emit(["", "RULES ON TRIAL in this repo (the adopt-or-drop review is decided where the "
                  "rules are maintained):"])
        emit(trials)

# --- 6. parked checkpoints and stashes ---------------------------------------
# unfold,separator= is required or a multi-line trailer breaks the parse.
cps = [
    c for c in git_lines(
        "for-each-ref",
        "--format=%(refname:short)%09%(trailers:key=Next-Step,valueonly,unfold,separator=%x20)",
        "refs/heads", cwd=root,
    )
    if re.search(r"\t.", c)
]
if cps:
    emit(["", "BRANCHES PARKED AT A CHECKPOINT (branch -> what to do next):"])
    emit(["  " + c.replace("\t", " -> ") for c in cps])

stash = git_lines("stash", "list", cwd=root)
if stash:
    emit(["", "STASHES exist (the stack is shared across every worktree of this repo):"])
    emit(["  " + s for s in stash[:5]])

# --- 7. the tool itself ------------------------------------------------------
# Guardrails that depend on a Claude Code version (hooks that fail closed, path-scoped
# rules, the worktree sweep) silently do not apply on an older build. Say which one runs.
claude_exe = find_exe("claude")
cv = ""
if claude_exe:
    budget = time_left(10)
    if budget < 1:
        stop_out_of_time()
    try:
        res = subprocess.run(
            [claude_exe, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=budget,
        )
        cv = next((ln for ln in res.stdout.splitlines() if ln != ""), "")
    except subprocess.TimeoutExpired:
        stop_out_of_time()
    except (OSError, ValueError):
        cv = ""
if cv:
    emit(["", f"CLAUDE CODE: {cv}"])

# --- 8. branches ahead of main (last: the slow section) ----------------------
# A branch that is pushed, written up and checkpointed is SAFE, and that is exactly why it
# can sit unmerged for weeks: nothing hurts. Print each branch's distance from main so the
# question "why is this not merged?" is asked with a number at the start of every session,
# not noticed in a survey weeks later. See the rule *One branch, one increment, merged on its yes*.
#
# One for-each-ref gives ahead/behind and the last-commit date for every ref at once
# (git 2.41+). Only branches actually ahead cost two more git calls each, and the table
# is capped, so a repo with 200 refs no longer spends minutes here.
base = None
for cand in ("origin/main", "main", "origin/master", "master"):
    if git("rev-parse", "--verify", "--quiet", cand, cwd=root).strip():
        base = cand
        break
if base:
    cap = 15
    seen = set()
    rows: list[str] = []
    skipped = 0
    refs = git_lines(
        "for-each-ref",
        f"--format=%(refname:short)%09%(ahead-behind:{base})%09%(committerdate:iso-strict)",
        "refs/heads", "refs/remotes/origin", cwd=root,
    )
    if not refs or not re.search(r"\t\d+ \d+\t", refs[0]):
        emit(["", f"BRANCHES AHEAD OF {base}: not computed (git 2.41+ is needed for "
                  "%(ahead-behind))."])
    else:
        for r in refs:
            parts = r.split("\t")
            if len(parts) < 3:
                continue
            short = re.sub(r"^origin/", "", parts[0])
            if short in ("main", "master", "HEAD"):
                continue
            if short in seen:
                continue  # local first; remote-only branches still count
            seen.add(short)
            ab = parts[1].split(" ")
            try:
                ahead, behind = int(ab[0]), int(ab[1])
            except (IndexError, ValueError):
                continue
            if ahead <= 0:
                continue  # merged (or empty): nothing to report
            if len(rows) >= cap:
                skipped += 1
                continue
            last = parse_iso(parts[2]) or now
            mb = git("merge-base", base, parts[0], cwd=root).strip()
            left = None
            if mb:
                left = parse_iso(git("log", "-1", "--format=%cI", mb, cwd=root))
            if left is None:
                left = now
            days = math.floor((now - left).total_seconds() / 86400)
            idle = math.floor((now - last).total_seconds() / 86400)
            flag = "  <-- the merge question is open" if (days > 2 or ahead > 15) else ""
            rows.append(
                f"  {short}: {ahead} ahead, {behind} behind, left main {days} day(s) ago, "
                f"last commit {idle} day(s) ago{flag}"
            )
        if rows:
            emit(["", f"BRANCHES AHEAD OF {base} (one increment, one yes, one merge - "
                      "see the guardrails):"])
            emit(rows)
            if skipped > 0:
                emit([f"  ... and {skipped} more unmerged branch(es) not listed (cap {cap}). "
                      "That many is itself the finding."])

out("=== end work state ===")
sys.exit(0)
