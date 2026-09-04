#!/usr/bin/env python3
"""Well-formedness gate for the issues/ tracker.

Deterministic, stdlib only, no network, no LLM -- so it can be a hard gate rather
than advice. Run it in CI, and optionally from pre-commit.

    python scripts/check-issues.py            # local: caps are warnings
    python scripts/check-issues.py --ci       # CI: caps fail too
    python scripts/check-issues.py --todos    # also: every TODO cites a live issue

Why it exists: a malformed issue file is invisible to the session-start digest, so
the author believes the issue is captured while the digest reports nothing to do.
That is a worse failure than no tracker at all, and it is exactly what happened
the first time this tracker was used for real.

See agent-constraints/issue-tracker.md for the format this enforces.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Two families share one field. The FLOW states are the idea->merge machine
# (triage -> classified -> plan -> approved -> implementing -> pr_open -> releasing).
# The EMPIRICAL states came from real use on investigation-heavy repos, where the
# machine vocabulary had no room for "being worked" / "remediation landed, not yet
# verified" / "parked on purpose":
#   open     -- acknowledged and being worked (or awaiting a slot / a ruling)
#   fixed    -- remediation landed; verification (LOOK, drape-verify, ...) pending
#   deferred -- deliberately parked; next: says what brings it back
# Status is ONE token from this list. Nuance goes in `- note:` or `- next:`, never
# in the status line -- a gate that fights the work gets routed around.
STATES = [
    "triage", "classified", "open", "plan", "approved",
    "implementing", "pr_open", "releasing", "fixed", "deferred",
    "done", "dropped",
]
TERMINAL = {"done", "dropped"}
BRANCH_REQUIRED_FROM = {"implementing", "pr_open", "releasing"}
# severity means "blocks the review gate" -- a flow concept. Empirical states are
# exempt: demanding invented severities on investigation files teaches people to
# stop filing them.
SEVERITY_REQUIRED = {"classified", "plan", "approved", "implementing", "pr_open", "releasing"}

# Open-issue cap; past this, triage or drop something. Raised from 40 on
# 2026-08-31: the first real repo ran 45 healthy, dated, next:-carrying open
# issues in week three — 40 was calibrated on nothing.
MAX_OPEN = 60
MAX_LOG = 12    # transitions; more than this and it is a project, not an issue

# The id carries the date so it sorts and namespaces the random suffix per day.
ID_RE = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])-[a-z0-9]{4,}$")
# Accept an em dash or a plain hyphen between id and title.
H1_RE = re.compile(r"^#\s+(\S+)\s*[—-]\s*(\S.*)$")
FIELD_RE = re.compile(r"^-\s+([a-z-]+):\s*(.*)$")
LOG_RE = re.compile(r"^-\s+\S")
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
TODO_ID_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}-[0-9a-f]{4,})\b")


def parse(path: Path) -> tuple[dict, list[str], list[str]]:
    """Return (fields, log_lines, errors) for one issue file."""
    errors: list[str] = []
    fields: dict[str, str] = {}
    log: list[str] = []

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    heading_id = None
    in_log = False
    for line in lines:
        if heading_id is None and line.startswith("# "):
            m = H1_RE.match(line)
            if not m:
                errors.append('heading must read "# <id> - <title>"')
                heading_id = ""
            else:
                heading_id = m.group(1)
            continue
        if line.strip().lower().startswith("## log"):
            in_log = True
            continue
        if line.startswith("## "):
            in_log = False
            continue
        if in_log:
            if LOG_RE.match(line):
                log.append(line)
            continue
        m = FIELD_RE.match(line)
        if m and m.group(1) in (
            "status", "severity", "branch", "next", "refs", "blocked-by", "note",
        ):
            fields.setdefault(m.group(1), m.group(2).strip())

    if heading_id is None:
        errors.append("no '# <id> - <title>' heading -- the digest cannot see this file")
    elif heading_id and heading_id != path.stem:
        errors.append(f"heading id '{heading_id}' does not match filename '{path.stem}'")
    elif heading_id and not ID_RE.match(heading_id):
        errors.append(f"id '{heading_id}' is not YYYY-MM-DD-xxxx (xxxx = 4+ lowercase hex)")

    status = fields.get("status")
    if not status:
        errors.append("no '- status: <state>' line -- the digest cannot see this file")
    elif status not in STATES:
        errors.append(f"status '{status}' is not one of: {', '.join(STATES)}")
    else:
        if status in SEVERITY_REQUIRED and not fields.get("severity"):
            errors.append(f"severity is required at flow status '{status}'")
        if status in BRANCH_REQUIRED_FROM and not fields.get("branch"):
            errors.append(f"branch is required at status '{status}'")
        if status not in TERMINAL and not fields.get("next"):
            errors.append("next: is required while the issue is open -- it IS the handover")
        if fields.get("branch", "").startswith(("/", ".")) or "\\" in fields.get("branch", ""):
            errors.append("branch: must be a branch name, not a path (paths go stale)")

    if not log:
        errors.append("no '## Log' entries -- record at least the transition that created it")
    elif len(log) > MAX_LOG:
        errors.append(f"{len(log)} log lines (max {MAX_LOG}) -- this is a project, split it")

    return fields, log, errors


# --- decisions (docs/decisions/ADR-*.md) -------------------------------------
# The ADR gate. Same philosophy: structure only, never truth. Statuses here are
# a closed set because a reviewer cannot trust a graph whose nodes lie about
# being retired -- the calibration corpus had a file saying SUPERSEDED on line 3
# and ACCEPTED on line 5, two different decisions sharing one id, and fourteen
# "proposed" records with 3-17 implementing commits each.
ADR_STATES = {"proposed", "accepted", "refuted", "superseded"}
ADR_FILE_RE = re.compile(r"^ADR-(\d{4})-[a-z0-9-]+\.md$")
ADR_STATUS_RE = re.compile(r"^- status:\s*([a-z-]+)\b\s*(.*)$")
# Legacy forms that must not survive: "**Status:** x", "Status: x". Stage-log
# lines like "**Status 2026-08-29 04:00 --" carry no colon after the word and
# are the historical record -- they stay.
ADR_LEGACY_RE = re.compile(r"^\s*>?\s*\*{0,2}Status\*{0,2}\s*:", re.I)
ADR_CITE_RE = re.compile(r"ADR-\d{4}")
ISSUE_CITE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}-[a-z0-9]{4,}")


def check_decisions(root: Path, known_issue_ids: set) -> list:
    dec = root / "docs" / "decisions"
    if not dec.is_dir():
        return []
    problems = []
    ids = {}
    files = sorted(f for f in dec.glob("ADR-*.md") if f.is_file())
    for f in files:
        rel = f.relative_to(root).as_posix()
        m = ADR_FILE_RE.match(f.name)
        if not m:
            problems.append(f"{rel}: filename is not ADR-NNNN-slug.md")
            continue
        num = m.group(1)
        if num in ids:
            problems.append(f"{rel}: duplicate id ADR-{num} (also {ids[num]})")
        ids[num] = f.name

    known = {f"ADR-{n}" for n in ids}
    for f in files:
        rel = f.relative_to(root).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        fid = f.name[:8]

        h1 = next((ln for ln in lines if ln.startswith("# ")), "")
        if fid not in h1:
            problems.append(f"{rel}: H1 does not carry {fid}")

        status_lines = [(i + 1, ln) for i, ln in enumerate(lines) if ADR_STATUS_RE.match(ln)]
        if len(status_lines) == 0:
            problems.append(f"{rel}: no '- status: <token>' line")
        elif len(status_lines) > 1:
            where = ", L".join(str(i) for i, _ in status_lines)
            problems.append(
                f"{rel}: {len(status_lines)} '- status:' lines (L{where})"
                " -- exactly one; history goes in prose"
            )
        if status_lines:
            token, detail = ADR_STATUS_RE.match(status_lines[0][1]).groups()
            if token not in ADR_STATES:
                problems.append(f"{rel}: status '{token}' not in {sorted(ADR_STATES)}")
            elif token in ("refuted", "superseded") and len(detail.strip()) < 5:
                problems.append(
                    f"{rel}: status '{token}' needs a detail -- what refuted/superseded it"
                )

        for i, ln in enumerate(lines, 1):
            if ADR_LEGACY_RE.match(ln) and not ADR_STATUS_RE.match(ln):
                problems.append(
                    f"{rel}:{i}: legacy status form -- normalise to '- status: <token> -- detail'"
                )

        for cite in sorted(set(ADR_CITE_RE.findall(text))):
            if cite != fid and cite not in known:
                problems.append(f"{rel}: cites {cite}, which does not exist")

        for mm in ISSUE_CITE_RE.finditer(text):
            start = mm.start()
            before = text[max(0, start - 1):start]
            if before in (":", "-", "_"):
                continue  # cross-repo (repo:id), or part of a longer token
            if before == "/":
                seg = text[:start].rstrip("/").rsplit("/", 1)[-1]
                if seg not in ("issues", "archive"):
                    continue  # a branch or path like feat/2026-..., not an issue ref
            if mm.group(0) not in known_issue_ids:
                problems.append(
                    f"{rel}: cites issue {mm.group(0)}, which is not in issues/ or issues/archive/"
                )
    return problems


def tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [root / p for p in out.splitlines() if p]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ci", action="store_true", help="fail on the open-issue cap too")
    ap.add_argument(
        "--todos", action="store_true", help="every TODO/FIXME must cite a live issue id"
    )
    ap.add_argument("--decisions", action="store_true", help="also gate docs/decisions/ADR-*.md")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    issues_dir = root / "issues"
    if not issues_dir.is_dir():
        print(f"check-issues: no issues/ directory in {root} -- nothing to check.")
        return 0

    live = sorted(p for p in issues_dir.glob("*.md") if p.is_file())
    archive_dir = issues_dir / "archive"
    archived = sorted(archive_dir.glob("*.md")) if archive_dir.is_dir() else []

    problems: list[str] = []
    known_ids: set[str] = set()
    open_count = 0

    for path in live + archived:
        fields, _log, errors = parse(path)
        known_ids.add(path.stem)
        rel = path.relative_to(root).as_posix()
        status = fields.get("status", "")
        is_archived = path in archived

        if status in TERMINAL and not is_archived:
            errors.append(f"status '{status}' is terminal -- git mv it into issues/archive/")
        if status and status not in TERMINAL and is_archived:
            errors.append(f"status '{status}' is not terminal -- it should not be archived")
        if status and status not in TERMINAL and not is_archived:
            open_count += 1

        for e in errors:
            problems.append(f"{rel}: {e}")

    # The cap must never block a capture -- a gate that punishes writing things down
    # teaches the agent not to write things down. CI only.
    if open_count > MAX_OPEN:
        msg = f"{open_count} open issues (cap {MAX_OPEN}) -- triage or drop some"
        if args.ci:
            problems.append(msg)
        else:
            print(f"check-issues: WARNING {msg}")

    if args.decisions:
        problems.extend(check_decisions(root, known_ids))

    if args.todos:
        for f in tracked_files(root):
            if not f.is_file() or issues_dir in f.parents:
                continue
            if f.name == "check-issues.py":
                continue  # this file names TODO/FIXME in its own help and patterns
            if f.suffix.lower() == ".md":
                continue  # --todos gates CODE; prose legitimately discusses TODOs
            try:
                if b"\0" in f.read_bytes()[:8192]:
                    continue  # binary (a PNG's byte soup can spell TODO)
            except OSError:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if TODO_RE.search(line):
                    cited = TODO_ID_RE.search(line)
                    if not cited:
                        problems.append(
                            f"{f.relative_to(root).as_posix()}:{i}: TODO with no issue id -- "
                            "add (<id>) pointing at issues/"
                        )
                    elif cited.group(1) not in known_ids:
                        problems.append(
                            f"{f.relative_to(root).as_posix()}:{i}: cites '{cited.group(1)}', "
                            "which is not an issue file"
                        )

    ndec = len(list((root / "docs" / "decisions").glob("ADR-*.md"))) if args.decisions else None
    dtxt = f", {ndec} decision records" if ndec is not None else ""
    print(f"check-issues: {len(live)} open, {len(archived)} archived{dtxt}.")
    if problems:
        print("ISSUE CHECK FAILED:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1
    print("OK: every issue file is well-formed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
