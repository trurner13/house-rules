# The issue tracker (starter)

One place, in the repo, that holds **every** open issue with its status and history.

This is not new process. [`verification-and-gates.md`](verification-and-gates.md)
already says the idea→merge state machine must persist "to disk so it survives a fresh
agent context" — it just never said *where*. **This is that disk.** The tracker is the
missing persistence layer for a flow the repo already committed to.

The problem it solves is specific: during one session an agent notices five things,
pursues one in depth, and the other four exist nowhere but the prompt history. They are
gone at the end of the session and nobody ever revisits them. A correction lives for
one context window; so does an observation. The only durable memory an agent has is the
one you build outside it.

## The shape: one file per issue

`issues/<id>.md`, one issue per file, plain markdown in the working tree.

**Not** a single `ISSUES.md`. Two worktrees appending to one file conflict on *every*
concurrent append, and the conflict lands mid-merge where the cheapest resolution is to
drop one side. Setting `merge=union` to "fix" it is worse: it silently keeps both
`status: done` and `status: open` for the same issue, with no conflict marker.

The "read the whole list in one shot" requirement is real, and it is met by **deriving**
the list with one command rather than storing an index that can drift. If a browsable
index is wanted for the web UI, generate it in CI on push to the default branch only —
single writer, so nothing to conflict — and mark it `<!-- GENERATED - do not edit -->`.

**The test that matters is the storage shape, not the tool:** plain text in the working
tree that `grep` and `git diff` read with nothing installed. Anything meeting that test
qualifies. Anything that hides state in a binary database, or behind a server, does not
— an agent reads the working tree, not an object graph or an API.

## The id

`YYYY-MM-DD-xxxx` — four+ lowercase hex characters by default, or a deliberate
mnemonic (`shld`, `cfdt`): anything `[a-z0-9]{4,}`. The filename **is** the id; there is
no `id:` field. No central counter, so two agents can create issues in parallel:

```bash
printf '<title>|<branch>|<iso-timestamp>' | git hash-object -t blob --stdin | cut -c1-4
```

The date prefix sorts chronologically, namespaces the random suffix per day, and
removes the need for a `discovered:` field. This is **collision-evident, not
collision-proof** — and both collision paths fail loudly (an existing file locally,
`CONFLICT (add/add)` across branches). At 30 captures in one day the collision chance
is under 1%; widen to six hex characters if a repo routinely exceeds that.

## The states

Two families share one field. The **flow** states are the adopted idea→merge machine;
the **empirical** states were added on 2026-08-31 after the first repo to run a large
tracker (45 open issues) invented its own words because the machine had no room for
investigation-shaped work — the gate was failing 32 of 34 real issues:

```text
flow:      triage → classified → plan → approved → implementing → pr_open → releasing → done
                                                                                       → dropped
empirical: open      (acknowledged / being worked / awaiting a ruling)
           fixed     (remediation landed; verification — LOOK, drape-verify — pending)
           deferred  (deliberately parked; next: says what brings it back)
```

**Status is ONE token.** The nuance that used to live in parenthetical status text
(“fixed for X; open for Y”) goes in `- note:` — a recognised optional field — or in
`next:`. A gate that fights how the work actually is gets routed around; widening the
vocabulary to fit the work is what keeps the token machine-readable.

`dropped` is not an invention. [`triage-conventions.md`](triage-conventions.md) already
asks "worth doing now? or decline/defer (note why)?" and the machine had nowhere to put
that answer. Without it the list grows without bound and agents re-raise the same thing
every month.

**There is deliberately no `blocked` state.** Blocked is orthogonal to phase — an issue
blocked while `implementing` is still implementing, and collapsing the two destroys the
resumability that is the whole point. Record it as an optional `blocked-by:` line.

## The fields

Markdown bullets under the H1, not YAML frontmatter — frontmatter has to sit *above*
the H1, which reorders the derived digest so every record reads its status before its
own title. Bullets grep identically, render as a list, and match house precedent.

| Field | When required |
|---|---|
| `status:` | always |
| `next:` | while open — **the one field that carries the handover**. One line, overwritten each time |
| `severity:` | at flow states past `classified` only. It means "blocks the gate", not "how much I care" — empirical states (`open`/`fixed`/`deferred`) are exempt |
| `branch:` | at `implementing` and beyond. **Branch name only** — a worktree path is machine-specific and goes stale |
| `refs:` | optional; one line, space-separated |
| `note:` | optional; the nuance the one-token status can no longer carry ("fixed for X; the ten others still open") |

Deliberately absent, each with its replacement: `id` (the filename), `title` (the H1),
`owner`/`agent`/`session` (git records the committer, and agents already commit under
distinct signed identities — an in-file owner is a second, unsigned, always-stale copy),
`priority` (nothing decides on it that status and severity don't), `updated`
(`git log -1 --format=%cs -- issues/<id>.md`; a hand-maintained date lies exactly when
you need it), `discovered` (the date is in the id; the provenance is the first log line).

## `## Log` — why it is not redundant with git

Git already records every change to the file, so an in-file history looks like
duplication. Keep it anyway, for three concrete reasons:

- **Squash-merge destroys the git equivalent.** Four status transitions collapse into
  one commit, unrecoverable once the branch is deleted.
- **CI cannot see it.** `actions/checkout` defaults to `fetch-depth: 1`.
- **Git records what the file said, not why it changed.**

Format: append-only, transitions and decisions **only**, never progress prose.

```text
- YYYY-MM-DD <state> — <one clause of why>
```

Cap it at twelve lines and fail above it. An issue needing thirteen transitions is a
project, and should be split.

## Examples

An issue in flight — `issues/2026-08-14-9d4c.md`:

```markdown
# 2026-08-14-9d4c — Session handover leaves uncommitted work behind

- status: implementing
- severity: high
- branch: feat/2026-08-14-9d4c-handover
- next: add the Stop hook that blocks turn-end on unmerged paths
- refs: plan:docs/plans/handover.md pr:#128

A session ends with modified files never committed, so the next session opens a tree
that disagrees with the branch and silently re-does or loses the work.

## Log

- 2026-08-14 triage — spotted while auditing three stale worktrees
- 2026-08-14 classified — harness bug, not product code
- 2026-08-14 approved — plan reviewed; blast radius is .claude/settings.json only
- 2026-08-14 implementing — feat/2026-08-14-9d4c-handover
```

The **capture form** — what gets written the moment something is noticed, before
moving on. Seven lines, no thinking required. This is the whole design: if capture
costs more than this, it will not happen.

```markdown
# 2026-08-14-c07a — Nothing enforces one branch per issue

- status: triage
- next: decide whether a WorktreeCreate hook can see the target issue id

Two worktrees were opened for the same work last week; neither knew about the other.

## Log

- 2026-08-14 triage — noticed while working 2026-08-14-9d4c
```

## The commands

```bash
# The session-start digest — the whole open list, ~175 bytes per issue
git grep --untracked -h -E '^# 20|^- (status|branch|next): ' -- ':(glob)issues/*.md'

# What is already in flight (run this BEFORE creating a worktree or a branch)
git grep --untracked -l -E '^- status: (approved|implementing|pr_open)' -- ':(glob)issues/*.md'

# One issue's full history. Give the path as it exists NOW — for an archived issue
# that is the archive/ path, or --follow silently truncates at the move.
git log -p --follow -- issues/<id>.md            # still open
git log -p --follow -- issues/archive/<id>.md    # archived
```

Three traps, all of which fail silently rather than loudly:

- **`git grep` skips untracked files by default.** A just-captured, unstaged issue is
  invisible without `--untracked` — which is exactly the issue most at risk.
- **Git pathspec globs do not stop at a directory boundary.** `issues/*.md` also matches
  `issues/archive/...`. Use `:(glob)` or add `':!issues/archive'`.
- **Never `git log -S<id>`** to find an issue's history — it finds the commit that
  created the line, not the status transitions. `-G` is the flag you want.
- **`--follow` traverses renames backwards from the path you give it**, so it must be
  the path as it exists at `HEAD`. Ask for an archived issue by its old path and you get
  a plausible-looking history that silently stops at the archive move — missing the
  `done` transition, which is usually the one you wanted.

## Keeping it small

The tracker is read at the start of every session, so it must not become a context dump.

- **Archive terminal issues immediately.** `git mv` to `issues/archive/`;
  `git log --follow` traverses the rename **when given the new path**, so archiving
  costs nothing in traceability.
- **Cap the open list** — 40 is a reasonable start. Same shape as a rules-file leanness
  gate: hitting the cap forces triage or `dropped` instead of letting the list rot.
  **The cap must never block a capture.** Enforce it in CI, so an over-cap list fails the
  *merge* and forces triage; if it also fired in `pre-commit`, capturing the 41st issue
  would fail and you would lose exactly the issue the tracker exists to catch. A gate
  that punishes writing things down teaches the agent not to write things down.
- **The agent never reads the directory.** `SessionStart` injects the derived digest,
  so the list arrives without the agent having *chosen* to look. Full files are opened
  only for the issue being worked.

## What to enforce

`scripts/check-issues.py` is installed with the rest of the kit and does all of this.
Python 3, stdlib only, no network, no LLM — so it can be a hard gate rather than advice:

```bash
python scripts/check-issues.py              # local: the open-issue cap is a warning
python scripts/check-issues.py --ci         # CI: the cap fails too
python scripts/check-issues.py --todos      # also: every TODO must cite a live issue
python scripts/check-issues.py --decisions  # also: gate docs/decisions/ADR-*.md
```

`--decisions` is the ADR gate, added 2026-08-31 after auditing a real 42-record set:
closed status set {proposed, accepted, refuted, superseded}; exactly one `- status:`
line per file (a record was found claiming SUPERSEDED on line 3 and ACCEPTED on line
5); no legacy `**Status:**` forms; unique ids (two records shared one number for six
weeks); every cited ADR id and issue id must resolve; cross-repo refs are `repo:id`.
Structure only, never truth — liveness of a status is a human call.

Add the `--ci` form to your pipeline. Adding the plain form to `pre-commit` is optional
and safe — it never blocks a capture, only a malformed one.

What it checks:

- the filename matches the H1 id, and the state is one of the **twelve** — the flow
  chain plus `dropped`, `open`, `fixed`, `deferred`. (Enumerate all twelve in the script:
  a check written against the flow chain alone rejects every real investigation issue as
  malformed, which is exactly what happened before the 2026-08-31 widening.)
- `severity:` present at flow states past `classified`; **empirical states are exempt** — demanding invented severities on investigation files teaches agents to stop filing them; `branch:` present at `implementing` and beyond
- `next:` present while open — a script can require the line, though nothing can
  require it be *true*
- terminal issues live in `archive/`; `## Log` is 1–12 lines
- open issues ≤ 60 — **CI only**, never in `pre-commit` (see the cap note above)
- **every added `TODO`/`FIXME`/`HACK`/`XXX` in tracked source carries a `(<id>)` that
  resolves to a real issue file.** This is the deterministic proxy for "spotted, then
  forgotten" — it cannot detect an unrecorded thought, but it catches every downstream
  trace of one
- a branch whose commits touch source must also touch `issues/` — which makes branch
  state and tracker state structurally unable to disagree. **CI only.** In `pre-commit`
  this deadlocks the every-turn checkpoint: on a turn where the code moved but `status:`
  and `next:` genuinely didn't, there is no `issues/` diff to make, so the commit is
  refused and the turn's work stays stranded in the working tree — the exact loss this
  whole design exists to prevent

Write the check so it fails first: run it against the repo as it is and confirm it goes
red before you trust it.

**Honest limit:** nothing can enforce that an issue was recorded at all. What this
design does instead is make every downstream trace fail, and make capture cheaper than
not capturing. That is the ceiling, and it is worth saying out loud rather than
pretending the gate is total.

## Other trackers

- **GitHub Issues** — a human-facing **mirror** or inbox, never the agent's working
  tracker. If a repo accepts inbound reports, a human or a read-only triage agent
  transcribes them into `issues/<id>.md` with `refs: gh:#123`, treated as quoted
  untrusted content: 66.5% of malicious GitHub issues penetrated every guardrail across
  three major coding agents in 2026 testing, and third-party content already routes to
  `hold` under the adopted rules. For a solo agent-only repo, **turn the Issues feature
  off** — removing the capability beats adding a prompt.
- **Off-the-shelf markdown trackers** (one file per task, no database, no daemon) meet
  the storage-shape test and are a reasonable choice if a repo wants a CLI or UI. Check
  two things before adopting one: that its ids are safe to allocate from parallel clones,
  and that it reconciles state across active branches.
- **Anything database-backed** fails the test, however good the ergonomics — if the
  canonical state is a binary file, or a gitignored directory, or a server, then it is
  not diffable in review and not readable by an agent without the tool installed. Check
  what a tool's *current* source of truth is; several popular ones changed theirs and the
  blog posts recommending them describe a design that no longer exists.
- **Do not add a `HANDOFF.md` alongside this.** A handoff doc plus a continuously-updated
  tracker gives you two sources that disagree, and the no-duplication rule that would
  prevent it is unenforceable. `next:` plus the `## Log` **is** the handover.
