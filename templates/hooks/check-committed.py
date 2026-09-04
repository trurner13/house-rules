#!/usr/bin/env python3
"""Completeness gate: would a fresh clone of this repo actually work?

Deterministic, stdlib only, no network, no LLM -- so it can be a hard gate rather
than advice.

    python scripts/check-committed.py              # local: advisories are warnings
    python scripts/check-committed.py --ci         # CI: advisories fail too
    python scripts/check-committed.py --handover   # report everything git is hiding
    python scripts/check-committed.py --json       # machine-readable, for agents

Why it exists: the rule "a fresh clone is the deliverable" was prose, and prose has
already failed at this. In an onboarded repo (2026-08-24) a blanket '.claude/' meant the whole
guardrail kit installed, reported success, existed on exactly one machine, and would
have vanished on the next clone. Nothing noticed. This is the version that notices.

It asks git, never the text of .gitignore -- negations, nested ignore files,
.git/info/exclude and the machine-global core.excludesFile all decide the answer and
none of them are visible in the repo's own .gitignore. That last one is the handover
killer: a file ignored in ~/.gitignore_global never appears in the author's `git status`
and is absent from every clone.

Per-repo additions live in a `.must-commit` file at the repo root (optional):

    # one path or directory prefix per line; blank lines and # comments ignored
    config/settings.yml
    data/fixtures/
    -.vscode/launch.json    # leading '-' exempts a built-in check, deliberately

The exemption form matters: a gate that cannot be right about a legitimate exception
gets bypassed wholesale, which is worse than one that never runs.

See .claude/rules/00-guardrails.md -- "A fresh clone is the deliverable" and
"Ask git what's ignored".
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Files that must reach version control IF THEY EXIST ON DISK. Presence is the
# trigger: a repo with no lock file is not failed for lacking one, but a repo that
# has one and hides it is broken for everybody who clones it.
MUST_SHIP_FILES = [
    # the agent kit -- the single most common casualty (a blanket '.claude/')
    ".claude/settings.json",
    ".mcp.json",
    ".worktreeinclude",
    # exact dependency versions: without them the next machine installs different
    # code and "works on mine" stops being falsifiable
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
    "bun.lockb", "poetry.lock", "uv.lock", "Pipfile.lock", "requirements.lock",
    "Cargo.lock", "Gemfile.lock", "composer.lock", "go.sum", "packages.lock.json",
    "gradle.lockfile", "pubspec.lock", "mix.lock",
    # the key list -- eaten by a bare '.env*' pattern
    ".env.example", ".env.sample", ".env.template", ".env.dist", ".env.defaults",
    # which toolchain this project needs; looks like personal taste, is not
    ".nvmrc", ".tool-versions", ".python-version", ".ruby-version", ".node-version",
    ".editorconfig",
    # project-level editor config: the difference between a clone that debugs on
    # day one and one that has to be configured first
    ".vscode/settings.json", ".vscode/extensions.json", ".vscode/launch.json",
    ".vscode/tasks.json",
    # how it builds and ships
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yaml",
    "Makefile", "justfile", ".gitlab-ci.yml", "Jenkinsfile",
    # intent, not just code -- code without the why is a rewrite, not a handover
    "SPEC.md", "CLAUDE.md", "AGENTS.md",
]

# Directory prefixes: every file underneath must reach version control.
MUST_SHIP_DIRS = [
    ".claude/rules/", ".claude/skills/", ".claude/agents/", ".claude/hooks/",
    ".githooks/", ".github/workflows/",
    "agent-constraints/", "issues/", "docs/decisions/",
    "migrations/", "db/migrate/", "prisma/migrations/", "alembic/versions/",
    "supabase/migrations/",
]

# Directories that are legitimately ignored even though they sit under a
# must-ship prefix.
MUST_SHIP_DIR_EXCEPTIONS = [
    ".claude/worktrees/",
]

# If the left-hand file exists, at least one of the right-hand ones must too.
# A .env with no committed example leaves the next person guessing which settings
# the app even reads.
COUNTERPARTS = [
    (".env", (".env.example", ".env.sample", ".env.template", ".env.dist")),
]

# "What this clone can't give you" -- the README section that makes a loud ignore
# loud. Apostrophes vary; match on the distinctive tail.
HANDOVER_SECTION = re.compile(r"can.?.?t\s+give\s+you", re.IGNORECASE)

DEFAULT_MAX_MB = 10.0


def git(root: Path, *args: str) -> tuple[int, str]:
    """Run git and return (returncode, stdout). Never raises on a non-zero exit."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout


def zsplit(out: str) -> list[str]:
    return [p for p in out.split("\0") if p]


def norm_rel(p: str) -> str:
    """Normalise a manifest path. NOT str.lstrip("./") -- that strips a CHARACTER SET,
    so it eats the leading dot of every dotfile and quietly turns '.vscode/launch.json'
    into 'vscode/launch.json', which matches nothing. Most of the must-ship list is
    dotfiles, so that bug would have disabled the escape hatch exactly where it matters."""
    p = p.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def load_manifest(root: Path) -> tuple[list[str], set[str]]:
    """Read .must-commit -> (extra paths/prefixes, exempted built-ins)."""
    extra: list[str] = []
    exempt: set[str] = set()
    path = root / ".must-commit"
    if not path.is_file():
        return extra, exempt
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            exempt.add(norm_rel(line[1:]))
        else:
            extra.append(norm_rel(line))
    return extra, exempt


def ignore_rules(root: Path, paths: list[str]) -> dict[str, tuple[str, str]]:
    """path -> (source_file, pattern) for whatever rule hides it. Batched: one
    subprocess for every path, because a pre-commit hook that is slow gets removed."""
    if not paths:
        return {}
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-v", "-z", "--stdin"],
            input="\0".join(paths) + "\0",
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        return {}
    fields = proc.stdout.split("\0")
    out: dict[str, tuple[str, str]] = {}
    # -v -z emits: source NUL linenum NUL pattern NUL pathname NUL
    for i in range(0, max(0, len(fields) - 3), 4):
        source, _lineno, pattern, pathname = fields[i:i + 4]
        if pathname:
            out[pathname] = (source, pattern)
    return out


def is_machine_local(source: str) -> bool:
    """True if this ignore rule lives outside the repo, so no clone reproduces it."""
    if not source:
        return False
    norm = source.replace("\\", "/")
    if norm.endswith(".git/info/exclude") or norm.endswith("info/exclude"):
        return True
    # Anything not resolving to a .gitignore inside the working tree: the global
    # excludesfile, typically ~/.gitignore_global or an XDG path.
    return not norm.endswith(".gitignore")


def under_dir(path: str, prefix: str) -> bool:
    return path == prefix.rstrip("/") or path.startswith(prefix)


def exempted(rel: str, exempt: set[str]) -> bool:
    """A '-' line in .must-commit wins over everything, built-in or manifest-added.
    An escape hatch that only works on some paths is not an escape hatch: the repo
    that hits the gap reaches for --no-verify instead, and loses the whole gate."""
    norm = rel.replace("\\", "/").rstrip("/")
    for e in exempt:
        e = e.replace("\\", "/").rstrip("/")
        if not e:
            continue
        if norm == e or norm.startswith(e + "/"):
            return True
    return False


def size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0.0


def check(root: Path, max_mb: float) -> tuple[list[dict], list[dict], dict]:
    """Return (problems, advisories, facts). Each entry is a typed dict so an agent
    can act on it without parsing prose."""
    problems: list[dict] = []
    advisories: list[dict] = []

    rc, _ = git(root, "rev-parse", "--is-inside-work-tree")
    if rc != 0:
        return ([{"code": "NOT_A_REPO", "path": str(root),
                  "detail": "not a git work tree -- nothing to check"}], [], {})

    tracked = set(zsplit(git(root, "ls-files", "-z")[1]))
    ignored = set(zsplit(git(root, "ls-files", "--others", "--ignored",
                             "--exclude-standard", "-z")[1]))
    untracked = set(zsplit(git(root, "ls-files", "--others", "--exclude-standard",
                               "-z")[1]))

    extra, exempt = load_manifest(root)
    files = list(MUST_SHIP_FILES)
    dirs = list(MUST_SHIP_DIRS)
    for item in extra:
        (dirs if item.endswith("/") else files).append(item)

    missing: list[str] = []

    # 1. Named files that exist on disk but will not reach a clone.
    for rel in files:
        if rel in tracked:
            continue
        if not (root / rel).is_file():
            continue
        missing.append(rel)

    # 2. Anything under a must-ship directory that git is hiding or has never seen.
    for prefix in dirs:
        if any(under_dir(prefix, exc) for exc in MUST_SHIP_DIR_EXCEPTIONS):
            continue
        for path in sorted(ignored | untracked):
            if not under_dir(path, prefix):
                continue
            if any(under_dir(path, exc) for exc in MUST_SHIP_DIR_EXCEPTIONS):
                continue
            missing.append(path)

    missing = [m for m in sorted(set(missing)) if not exempted(m, exempt)]
    rules = ignore_rules(root, missing)
    for rel in missing:
        source, pattern = rules.get(rel, ("", ""))
        if source and is_machine_local(source):
            problems.append({
                "code": "MACHINE_LOCAL_IGNORE", "path": rel,
                "source": source, "pattern": pattern,
                "detail": (f"hidden by '{pattern}' in {source}, which is NOT in the repo -- "
                           "invisible in your git status and absent from every clone"),
                "fix": "remove the pattern from that file, then `git add` the path",
            })
        elif source:
            problems.append({
                "code": "IGNORED_MUST_SHIP", "path": rel,
                "source": source, "pattern": pattern,
                "detail": f"ignored by '{pattern}' ({source}) -- no clone will have it",
                "fix": ("stop ignoring it (exclude the directory's CONTENTS, 'dir/*', "
                        "not 'dir/'), then `git add` the path"),
            })
        else:
            problems.append({
                "code": "UNTRACKED_MUST_SHIP", "path": rel,
                "detail": "exists on disk, never committed -- no clone will have it",
                "fix": f"git add {rel}",
            })

    # 3. A must-ship DIRECTORY covered by an ignore rule. Files already committed
    #    there stay tracked, so nothing looks broken today -- but every file added to
    #    it from now on is silently dropped. That is that same failure with a fuse
    #    on it: the next `sync-guardrails` writes a new rules file, git ignores it, the
    #    run reports success, and the clone is missing something nobody named.
    probes = {}
    for prefix in dirs:
        if any(under_dir(prefix, exc) for exc in MUST_SHIP_DIR_EXCEPTIONS):
            continue
        if not (root / prefix.rstrip("/")).is_dir():
            continue
        if exempted(prefix, exempt):
            continue
        probes[prefix.rstrip("/") + "/__probe__"] = prefix
    for probe, (source, pattern) in sorted(ignore_rules(root, sorted(probes)).items()):
        prefix = probes[probe]
        problems.append({
            "code": "IGNORED_MUST_SHIP_DIR", "path": prefix,
            "source": source, "pattern": pattern,
            "detail": (f"'{pattern}' ({source}) covers this directory, so any NEW file "
                       "added here is ignored silently -- files already committed stay, "
                       "which is why nothing looks wrong yet"),
            "fix": (f"exclude the contents, not the directory: '{pattern.rstrip('/')}/*' "
                    f"plus '!{prefix}'"),
        })

    # 3. A '!' negation that cannot work. Git will not re-include a file whose PARENT
    #    DIRECTORY is excluded, so '.claude/' + '!.claude/rules/' silently does nothing.
    #    Resolved against real files via check-ignore, not guessed from the text.
    negated: list[str] = []
    for gi in sorted(tracked):
        if Path(gi).name != ".gitignore":
            continue
        base = str(Path(gi).parent).replace("\\", "/")
        base = "" if base == "." else base + "/"
        try:
            text = (root / gi).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith("!") or "*" in line or "?" in line:
                continue
            negated.append(base + line[1:].strip().lstrip("/").rstrip("/"))

    still_ignored = ignore_rules(root, [n for n in negated if (root / n).exists()])
    for rel, (source, pattern) in sorted(still_ignored.items()):
        if pattern.startswith("!"):
            continue  # the negation is the winning rule: it works
        problems.append({
            "code": "BROKEN_NEGATION", "path": rel,
            "source": source, "pattern": pattern,
            "detail": (f"'!{rel}' cannot re-include it: '{pattern}' ({source}) excludes a "
                       "parent directory, and git will not descend into an excluded directory"),
            "fix": f"exclude the contents instead -- write '{pattern.rstrip('/')}/*', not "
                   f"'{pattern}'",
        })

    # 4. A .env with no committed example leaves the next person guessing which
    #    settings the app reads at all.
    for trigger, wanted in COUNTERPARTS:
        if not (root / trigger).exists():
            continue
        if any(w in tracked for w in wanted):
            continue
        advisories.append({
            "code": "MISSING_COUNTERPART", "path": trigger,
            "detail": f"{trigger} exists but none of {', '.join(wanted)} is committed",
            "fix": f"commit {wanted[0]} listing every key, with safe defaults or a "
                   "comment saying where the real value comes from",
        })

    # 5. Big files, both directions. Committed: permanent, every clone pays forever.
    big_tracked = [(p, size_mb(root / p)) for p in tracked if size_mb(root / p) > max_mb]
    for rel, mb in sorted(big_tracked, key=lambda x: -x[1])[:20]:
        advisories.append({
            "code": "LARGE_TRACKED_FILE", "path": rel, "mb": round(mb, 1),
            "detail": f"{mb:.1f} MB committed -- every clone carries this, in every "
                      "version it ever had, permanently",
            "fix": "move it to shared storage or LFS; removing it later does not "
                   "shrink the history",
        })

    # Ignored: fine, but it must be LOUD -- an ignored 2 GB dataset with no note is
    # indistinguishable from a lost one.
    big_ignored = sorted(
        ((p, size_mb(root / p)) for p in ignored
         if size_mb(root / p) > max_mb and not exempted(p, exempt)),
        key=lambda x: -x[1],
    )
    documented = False
    for name in ("README.md", "README", "HANDOVER.md", "docs/README.md"):
        p = root / name
        if p.is_file() and HANDOVER_SECTION.search(
            p.read_text(encoding="utf-8", errors="replace")
        ):
            documented = True
            break
    if big_ignored and not documented:
        advisories.append({
            "code": "UNDOCUMENTED_LARGE_IGNORED",
            "path": big_ignored[0][0],
            "count": len(big_ignored),
            "detail": (f"{len(big_ignored)} ignored file(s) over {max_mb:.0f} MB and no "
                       '"What this clone can\'t give you" section in the README'),
            "fix": ('add that section: one line per item -- what it is, where it lives '
                    "(link it), who grants access"),
        })

    facts = {
        "tracked": len(tracked),
        "ignored": len(ignored),
        "must_ship_checked": len(files) + len(dirs),
        "large_ignored": len(big_ignored),
        "handover_section": documented,
    }
    return problems, advisories, facts


def handover_report(root: Path, max_mb: float) -> None:
    """Everything git is hiding on THIS machine. Read it once before a handover;
    the surprises are the point."""
    ignored = zsplit(git(root, "ls-files", "--others", "--ignored",
                         "--exclude-standard", "-z")[1])
    print(f"\ncheck-committed: {len(ignored)} path(s) git is hiding on this machine")
    big = [(p, size_mb(root / p)) for p in ignored]
    for rel, mb in sorted(big, key=lambda x: -x[1])[:40]:
        flag = "  <-- over the size threshold" if mb > max_mb else ""
        print(f"    {mb:8.1f} MB  {rel}{flag}")
    if len(ignored) > 40:
        print(f"    ... and {len(ignored) - 40} more (not listed)")

    print("\nWhere this machine's private ignore rules live "
          "(not in the repo, not in any clone):")
    rc, out = git(root, "config", "--get", "core.excludesFile")
    print(f"    core.excludesFile : {out.strip() if rc == 0 and out.strip() else '(none set)'}")
    rc, top = git(root, "rev-parse", "--absolute-git-dir")
    exclude = Path(top.strip()) / "info" / "exclude" if rc == 0 and top.strip() else None
    if exclude and exclude.is_file():
        body = [ln for ln in exclude.read_text(encoding="utf-8", errors="replace").splitlines()
                if ln.strip() and not ln.strip().startswith("#")]
        print(f"    .git/info/exclude : {len(body)} active rule(s)")
        for ln in body[:10]:
            print(f"        {ln}")
    else:
        print("    .git/info/exclude : (none)")
    print("\nThe only honest test is still a clean clone: clone into a directory this")
    print("project has never run in, run the documented setup, and run the build.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--ci", action="store_true", help="advisories fail too")
    ap.add_argument("--handover", action="store_true",
                    help="also print everything git is hiding on this machine")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="machine-readable output, for agents")
    ap.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB,
                    help=f"large-file threshold in MB (default: {DEFAULT_MAX_MB:g})")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    problems, advisories, facts = check(root, args.max_mb)

    if args.ci:
        problems = problems + advisories
        advisories = []

    if args.as_json:
        print(json.dumps({
            "ok": not problems,
            "facts": facts,
            "problems": problems,
            "advisories": advisories,
        }, indent=2))
        return 1 if problems else 0

    print(f"check-committed: {facts.get('tracked', 0)} tracked, "
          f"{facts.get('ignored', 0)} ignored, "
          f"{facts.get('must_ship_checked', 0)} must-ship rules applied.")

    for a in advisories:
        print(f"check-committed: WARNING [{a['code']}] {a['path']}: {a['detail']}")
        print(f"    fix: {a['fix']}")

    if args.handover:
        handover_report(root, args.max_mb)

    if problems:
        print("COMMIT CHECK FAILED -- a fresh clone would not have these:", file=sys.stderr)
        for p in problems:
            print(f"  [{p['code']}] {p['path']}", file=sys.stderr)
            print(f"      {p['detail']}", file=sys.stderr)
            if p.get("fix"):
                print(f"      fix: {p['fix']}", file=sys.stderr)
        print("", file=sys.stderr)
        print("  See .claude/rules/00-guardrails.md -- \"A fresh clone is the "
              "deliverable\".", file=sys.stderr)
        return 1

    print("OK: everything that must reach a clone, does.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
