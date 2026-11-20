"""Tests for the two Claude Code hooks, session-start.py and session-end.py.

Builds throwaway git repos in the temp folder, copies the hooks into their
.claude/hooks/ (each hook resolves the repo from its own location), runs them with
this interpreter and checks the digest's headings, their order, the output budget and
the archive copy. Stdlib only; no network; never touches a real repo.

    python templates/hooks/test-session-hooks.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
results: list[tuple[bool, str, str]] = []


def expect(label: str, condition: bool, detail: str = "") -> None:
    results.append((condition, label, detail))
    print(("  PASS  " if condition else "  FAIL  ") + label + ("" if condition or not detail else f"\n        {detail}"))


def sh(cwd: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=False, env=env)


def git(cwd: Path, *args: str) -> None:
    res = sh(cwd, "git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
             "-c", "core.hooksPath=", "-c", "core.autocrlf=false", *args)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {res.stderr}")


def new_repo(tmp: Path, name: str) -> Path:
    root = tmp / name
    (root / ".claude" / "hooks").mkdir(parents=True)
    for hook in ("session-start.py", "session-end.py"):
        shutil.copyfile(HOOKS / hook, root / ".claude" / "hooks" / hook)
    git(root, "init", "-q", "-b", "main", ".")
    return root


def write(root: Path, rel: str, body: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8", newline="\n")


def digest(root: Path) -> tuple[int, str, str]:
    res = sh(root.parent, sys.executable, "-I", str(root / ".claude" / "hooks" / "session-start.py"))
    return res.returncode, res.stdout, res.stderr


def in_order(text: str, *needles: str) -> tuple[bool, str]:
    pos = -1
    for n in needles:
        i = text.find(n)
        if i < 0:
            return False, f"missing: {n!r}"
        if i < pos:
            return False, f"out of order: {n!r}"
        pos = i
    return True, ""


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="session-hooks-test-"))
    try:
        # --- 1. a quiet repo: the frame, "none recorded", and nothing else alarming ---
        quiet = new_repo(tmp, "quiet")
        write(quiet, "README.md", "x\n")
        git(quiet, "add", "-A")
        git(quiet, "commit", "-q", "-m", "init")
        code, out, err = digest(quiet)
        expect("quiet repo: exit 0", code == 0, err)
        ok, why = in_order(out, "=== work state (session-start reconciliation) ===",
                           "OPEN ISSUES: none recorded in issues/.",
                           "UNPUSHED commits (they die with this machine):",
                           "=== end work state ===")
        expect("quiet repo: frame, 'none recorded', unpushed (no remote), end marker, in order", ok, why or out)
        expect("quiet repo: no UNCOMMITTED section on a clean tree", "UNCOMMITTED:" not in out, out)
        expect("quiet repo: no issue section when issues/ is absent", "MALFORMED" not in out and "OPEN ISSUES (" not in out, out)
        # git older than 2.41 prints "BRANCHES AHEAD OF main: not computed": a notice, not a
        # section, so it is allowed here (the test must pass on any supported git).
        quiet_out = "\n".join(ln for ln in out.splitlines() if "not computed (git 2.41+" not in ln)
        expect("quiet repo: no trial, checkpoint or branch sections", not any(
            s in quiet_out for s in ("TRIAL REVIEW OVERDUE", "RULES ON TRIAL", "BRANCHES PARKED", "BRANCHES AHEAD OF", "STASHES")), out)

        # --- 2. a busy repo: every section fires, in the documented order ----------------
        busy = new_repo(tmp, "busy")
        write(busy, "README.md", "x\n")
        write(busy, "issues/2026-10-30-abcd.md",
              "# 2026-10-30-abcd - a test issue\n\n- status: open\n- next: do the thing\n\n## Log\n")
        write(busy, "issues/broken.md", "no heading and no status line\n")
        write(busy, "TODO.md",
              "# TODO\n\n## On trial in a repo\n\n"
              "- [~] **Some trial** - details here. Review 2020-01-01, then weekly.\n\n"
              "## Next\n\n- nothing\n")
        write(busy, ".claude/rules/trial.md", "# A rule (on trial from 2026-10-01)\n\n- do x\n")
        git(busy, "add", "-A")
        git(busy, "commit", "-q", "-m", "init")
        git(busy, "checkout", "-q", "-b", "feat/x")
        write(busy, "feature.txt", "y\n")
        git(busy, "add", "-A")
        git(busy, "commit", "-q", "-m", "wip(x): park it\n\nNext-Step: finish it\n")
        git(busy, "checkout", "-q", "main")
        write(busy, "dirty.txt", "z\n")
        code, out, err = digest(busy)
        expect("busy repo: exit 0", code == 0, err)
        ok, why = in_order(
            out,
            "=== work state (session-start reconciliation) ===",
            'TRIAL REVIEW OVERDUE (TODO.md, "On trial")',
            "Some trial: review was due 2020-01-01",
            "OPEN ISSUES (issues/ is the tracker;",
            "# 2026-10-30-abcd - a test issue",
            "- next: do the thing",
            "MALFORMED issue file(s), not counted above",
            "broken.md",
            "UNCOMMITTED: 1 file(s) in this working tree.",
            "?? dirty.txt",
            "UNPUSHED commits (they die with this machine):",
            "RULES ON TRIAL in this repo",
            "trial.md: on trial since 2026-10-01",
            "BRANCHES PARKED AT A CHECKPOINT (branch -> what to do next):",
            "feat/x -> finish it",
            "BRANCHES AHEAD OF main",
            "=== end work state ===",
        )
        expect("busy repo: every section, in order", ok, why or out)
        ahead_ok = ("feat/x: 1 ahead, 0 behind" in out) or ("not computed (git 2.41+" in out)
        expect("busy repo: branch distance row (or the git-too-old notice)", ahead_ok, out)
        expect("busy repo: no 'merge question' flag on a branch that left main today",
               "<-- the merge question is open" not in out, out)
        expect("busy repo: stderr is quiet", err.strip() == "", err)

        # --- 3. the output budget: many long issues are clipped and capped ---------------
        big = new_repo(tmp, "big")
        for i in range(80):
            write(big, f"issues/2026-10-30-{i:04d}.md",
                  f"# 2026-10-30-{i:04d} - issue {i}\n\n- status: open\n- next: " + ("word " * 60) + "\n")
        git(big, "add", "-A")
        git(big, "commit", "-q", "-m", "init")
        code, out, err = digest(big)
        expect("big repo: exit 0", code == 0, err)
        expect("big repo: stays under the 10,000-character hook limit", len(out) < 10000, str(len(out)))
        expect("big repo: says how many issue lines it left out", "more line(s); the rest are in issues/." in out, out[-300:])
        expect("big repo: long lines are clipped", "..." in out and max(len(ln) for ln in out.splitlines()) <= 183, "")
        expect("big repo: the end marker survives the cap", out.rstrip().endswith("=== end work state ==="), out[-200:])

        # --- 4. not a git repo: says so, exits 0 ----------------------------------------
        loose = tmp / "loose" / ".claude" / "hooks"
        loose.mkdir(parents=True)
        shutil.copyfile(HOOKS / "session-start.py", loose / "session-start.py")
        probe = sh(tmp / "loose", "git", "rev-parse", "--show-toplevel")
        if probe.returncode == 0:
            print("  SKIP  not-a-repo case: the temp folder is inside a git repository")
        else:
            res = sh(tmp, sys.executable, "-I", str(loose / "session-start.py"))
            expect("not a repo: exit 0 and says so", res.returncode == 0 and "is not inside a git repository" in res.stdout, res.stdout + res.stderr)

        # --- 4b. trial reviews: "On trial" as the LAST section, and an undated item ---
        trials = new_repo(tmp, "trials")
        write(trials, "TODO.md",
              "# TODO\n\n## On trial in a repo\n\n"
              "- [~] **Undated trial** - no review date yet.\n"
              "- [~] **Dated trial** - Review 2020-02-02.\n")
        git(trials, "add", "-A")
        git(trials, "commit", "-q", "-m", "init")
        code, out, err = digest(trials)
        expect("trials: a last 'On trial' section is still read", "Dated trial: review was due 2020-02-02" in out, out)
        expect("trials: an undated item never borrows the next item's date", "Undated trial:" not in out, out)

        # --- 5. session-end: the transcript is copied under <home>/.claude/session-archive/<repo>/ ---
        home = tmp / "home"
        home.mkdir()
        transcript = tmp / "transcript.jsonl"
        transcript.write_text('{"type":"x"}\n', encoding="utf-8")
        env = dict(os.environ)
        env["USERPROFILE"] = str(home)
        env["HOME"] = str(home)
        payload = json.dumps({"session_id": "abc123", "transcript_path": str(transcript)})
        res = subprocess.run([sys.executable, "-I", str(quiet / ".claude" / "hooks" / "session-end.py")],
                             input=payload, capture_output=True, text=True, encoding="utf-8", env=env, check=False)
        archived = home / ".claude" / "session-archive" / "quiet" / "abc123.jsonl"
        expect("session-end: exit 0", res.returncode == 0, res.stderr)
        expect("session-end: transcript copied to <home>/.claude/session-archive/<repo>/<session-id>.jsonl",
               archived.is_file() and archived.read_text(encoding="utf-8") == '{"type":"x"}\n', str(archived))
        res = subprocess.run([sys.executable, "-I", str(quiet / ".claude" / "hooks" / "session-end.py")],
                             input="", capture_output=True, text=True, encoding="utf-8", env=env, check=False)
        expect("session-end: empty stdin is a no-op, exit 0", res.returncode == 0, res.stderr)
        res = subprocess.run([sys.executable, "-I", str(quiet / ".claude" / "hooks" / "session-end.py")],
                             input=json.dumps({"session_id": "../../escape", "transcript_path": str(transcript)}),
                             capture_output=True, text=True, encoding="utf-8", env=env, check=False)
        expect("session-end: an unsafe session id never writes outside the archive",
               res.returncode == 0
               and not (home / ".claude" / "escape.jsonl").exists()
               and not (home / "escape.jsonl").exists()
               and (home / ".claude" / "session-archive" / "quiet" / "transcript.jsonl").is_file(), res.stderr)
        res = subprocess.run([sys.executable, "-I", str(quiet / ".claude" / "hooks" / "session-end.py")],
                             input=json.dumps({"session_id": "nope", "transcript_path": str(tmp / "missing.jsonl")}),
                             capture_output=True, text=True, encoding="utf-8", env=env, check=False)
        expect("session-end: a missing transcript is a no-op, exit 0",
               res.returncode == 0 and not (home / ".claude" / "session-archive" / "quiet" / "nope.jsonl").exists(), res.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
