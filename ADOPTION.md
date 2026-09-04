# Adopting these guardrails in other repos

How to make your other repos aware of — and compliant with — the practices in
this repo. Three parts:

1. [What every repo gets](#1-what-every-repo-gets) — the vendored kit
2. [New repos](#2-new-repo-creation-flow) — start compliant from day one
3. [Existing repos](#3-existing-repo-adaptation-plan) — bring them up to standard

---

> [!NOTE]
> This has been run for real, and the rules below carry the scars. The tracker
> gate found 32 of 34 malformed issues the first time it ran against a live
> tracker; the completeness gate was calibrated against a real 42-record set
> holding a six-week-old duplicate id, a record claiming two contradictory
> states five lines apart, and 16 records with no status at all; and the
> stale-constraint warning exists because a vendored file silently drifted in
> one repo and nobody noticed.

---

## 1. What every repo gets

Each adopting repo carries a **vendored copy** of the adopted rules at
`.claude/rules/00-guardrails.md`. Claude Code **auto-loads every `.claude/rules/*.md`**
at the start of each session, so the rules apply on **any machine with a plain
`git clone`** — no `~` import, no global setup, no extra step for a teammate or a
cloud/CI runner. The repo's root `CLAUDE.md` then only declares AI-first + repo nuance:

```markdown
# <Repo name>

<!-- Shared AI guardrails are vendored at .claude/rules/00-guardrails.md and load
     automatically every session. Re-sync from TRT-AI-guardrails when rules change. -->

## This repo (AI-first)
Humans architect, design, and review; AI writes the code. No hand-written production code.
- (repo purpose / stack / commands / conventions — see templates/new-repo-CLAUDE.md)
```

Why vendored (not a live `~` import):

- **Works on any machine** — the rules are *in* the repo, so a plain clone has them.
  Nothing depends on a home-directory clone existing or on `~` expanding.
- **Still single-source-of-truth** — the source is `rules/RULES.md` here; the copy is
  a generated artifact you don't hand-edit. Re-sync to pick up changes (§2).
- **Private-safe** — these are your private repos; the vendored file is just markdown.

> Trade-off vs a live import: updates aren't automatic — when `RULES.md` changes here,
> re-run the sync in each repo (one command, §2) to pull the new version.

---

## 2. New-repo creation flow

Goal: every repo you create is guardrail-aware **and actually enforces the guardrails**
from the first commit.

### The procedure

Substitute your own name and path for `<project>` and `C:\<project>`. Steps 1–6 are local
and reversible (delete the folder); step 7 is the only one that creates anything outside
your machine.

> **Shell:** run these in **PowerShell**. Only step 2 is shell-specific — a `.ps1` has no
> shebang, so Git Bash tries to execute it as a shell script and fails with
> `syntax error near unexpected token`. From Git Bash, use the explicit form given at
> step 2 instead. Every other step is plain `git`/`cp` and works in both.

**Step 1 — create the repo.**

```powershell
git init -b main C:/<project>
```

`-b main` matters: git still defaults to `master`, and the rest of your repos are on
`main`. The setup in step 2 needs the git repo to exist, because it sets git config and
appends to `.gitignore` — but it does *not* need a commit yet.

**Step 2 — install the guardrails and the machinery**, from a clone of this repo:

```powershell
./scripts/sync-guardrails.ps1 -Repo "C:\<project>" -Init
```

From Git Bash, that same step is:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/sync-guardrails.ps1 -Repo "C:\<project>" -Init
```

Reading the output: the first two lines are `Synced rules -> …` and
`Added N new constraint file(s): …`. Everything after the `Machinery (-Init):` header is
prefixed — `+` installed, `=` already present and left alone, `^` refreshed because it was
out of date, `!` needs a hand.

**Safe to re-run.** Two categories behave differently, and the distinction matters:

- **Generated machinery is refreshed every run** — `.claude/rules/00-guardrails.md` and
  the three hook scripts. Never hand-edit these; your changes are overwritten by design.
  They must track the source, because *a stale hook does not fail loudly* — an early
  version of the digest resolved the repo from the caller's working directory and
  cheerfully reported a **different repository's** state. If a repo needs different
  behaviour, add a second hook alongside rather than editing the shipped one.
- **Everything you adapt is gap-filled and never overwritten** — `agent-constraints/*.md`,
  `issues/`, `settings.json`, `.gitignore`, `.gitattributes`, `core.hooksPath`.

It installs:

| What | Where | Purpose |
|---|---|---|
| The adopted rules | `.claude/rules/00-guardrails.md` | Auto-loaded by Claude Code every session |
| Phase + cross-cutting conventions | `agent-constraints/*.md` | The operational "how", for the repo to adapt |
| Session-start digest | `.claude/hooks/session-start.ps1` | Prints open issues and in-flight work into the agent's context |
| Hook wiring | `.claude/settings.json` | Fires the digest on `SessionStart` |
| Checkpoint format gate | `.githooks/commit-msg` | Rejects a `wip(...)` commit with no `Next-Step:` trailer |
| Conflict gate | `.githooks/pre-commit` | Refuses to commit over an unresolved conflict or staged conflict markers |
| Completeness gate | `scripts/check-committed.py` | Fails if a fresh clone would be missing files someone ignored |
| The issue tracker | `issues/` + `issues/archive/` | One file per issue — status, next step, history |
| Hook activation | `git config core.hooksPath .githooks` | Makes the git hooks live in this clone |
| Worktree ignore | `.gitignore` | Keeps `.claude/worktrees/` out of the index |
| LF pin | `.gitattributes` | Stops the git hooks being checked out with CRLF |

**Step 3 — add the project's `CLAUDE.md`.**

```powershell
cp "<path-to-guardrails-repo>/templates/new-repo-CLAUDE.md" "C:/<project>/CLAUDE.md"
```

Then **open it and fill it in** — the only genuinely manual part of this procedure.
**Eight** placeholder slots: repo name, purpose, stack, commands (build/test/lint),
layout, non-default conventions, anything protected or irreversible, and the
repo-specific overrides line at the bottom (write "none yet" rather than leaving it).
**Also delete the template's opening HTML comment** — it is addressed to whoever is doing
the copy and points at `templates/…` paths that don't exist in your new repo.

Keep it under ~150 lines; it loads on every session and a bloated one makes Claude
*ignore* instructions. Leave a field out rather than padding it.

⚠️ **`cp` overwrites — run this step once.** Re-running it after you've filled the file
in silently replaces your work with the blank template. Unlike step 2, this step is not
gap-fill.

**Step 4 — write the first real issue**, at `C:\<project>\issues\<YYYY-MM-DD-xxxx>.md`.

The `xxxx` is four lowercase **hex** characters, not a counter — so two agents can create
issues in parallel without colliding. Generate one:

```bash
printf 'define what the project is for|main|2026-08-14' | git hash-object -t blob --stdin | cut -c1-4
```

Then write the file — e.g. `issues/2026-08-14-9d4c.md`:

```markdown
# 2026-08-14-9d4c — Define what <project> is for

- status: triage
- next: write SPEC.md — purpose, what's in scope, what isn't

## Log

- 2026-08-14 triage — created with the repo
```

Don't skip this. An empty `issues/` folder teaches the agent that the tracker is
decorative; one real entry sets the pattern it will follow.

**The shape is not decoration** — the session digest finds issues by grepping for a
`# <id> — <title>` heading and `- status:` / `- next:` lines. A file of plain prose is
invisible to it; the digest flags such files as malformed rather than silently reporting
"none recorded", but it's easier to write it right. The heading id must start `20`, or
the grep won't see it. Keeping the filename identical to the heading id is convention
rather than enforcement — nothing checks it — but `git log --follow` and archiving both
key off the filename, so a mismatch will bite you later.

**Step 5 — commit.**

```powershell
git -C C:/<project> add -A
```

```powershell
git -C C:/<project> commit -m "chore: initialise <project> with guardrails and session machinery"
```

Nothing takes effect until it's committed — Claude Code reads all of this from the
working tree.

This commit runs the hooks but **does not prove they work**: a `chore:` subject isn't a
`wip(` checkpoint, and a clean tree has no conflict for `pre-commit` to catch, so every
enforcement branch is skipped. To actually prove it, try a bad checkpoint — it must be
rejected:

```bash
git -C C:/<project> commit --allow-empty -m "wip(x): checkpoint with no trailer"
```

Expect `commit-msg REJECTED: a wip(...) checkpoint needs a 'Next-Step:' trailer.` and no
new commit. If that commit *succeeds*, `core.hooksPath` isn't set — go back to step 2.

**Step 6 — verify, three checks.**

```powershell
git -C C:/<project> config core.hooksPath
```

Must print `.githooks`. If it prints nothing the git hooks are inert and step 2 didn't
finish.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:/<project>/.claude/hooks/session-start.ps1"
```

Must print a `=== work state (session-start reconciliation) ===` block listing the issue
from step 4. It works from any directory — it locates the repo from its own path, not
your shell's. If it prints **nothing at all**, the script is an older copy that resolved
the repo from the working directory; re-run step 2 to replace it.

Then open Claude Code in the repo and run `/memory` — `00-guardrails.md` should be
loaded, and the session should *open* with the work-state digest already in context.
That digest is the whole point: the agent starts knowing what is outstanding without
being asked.

**Step 7 — create the remote and push.** The only outward-facing step:

```powershell
gh repo create <your-org>/<project> --private --source C:/<project> --remote origin --push
```

**New repos are owned by your `gh` account's org** — that's where
the current repos live. Note that some older repos, *including this guardrails repo
itself*, are still under `trurner13`; that's why the vendored deep-dive links point
there. Don't "correct" those to the org unless the repo is actually transferred —
they would all 404 the moment you did.

### What now runs by itself, and what doesn't

**Runs automatically:** the session-start digest (every new session), and both git hooks
(every commit).

**Does not run automatically:** the checkpoint commit itself. The agent is *told* what's
outstanding and is *prevented* from committing it wrongly, but it still decides when to
commit.

**That is the intended stopping point, not a gap.** Automating the commit is possible (a
`Stop` hook) and was **deliberately rejected** as disproportionate: the startup digest
already catches uncommitted work at the next session, so the hook only changes *when* it
is caught — while committing and pushing unattended every turn needs a secret scan first,
because `git add -A` stages whatever `.gitignore` missed. The reasoning is recorded in
[`agent-constraints/session-lifecycle.md`](templates/agent-constraints/session-lifecycle.md).

> **Once per clone, forever:** `core.hooksPath` is *local* git config — it is not
> committed and does not travel. Every new clone of the repo, on every machine, needs
> `git config core.hooksPath .githooks` once, or the git hooks silently do nothing.
> Re-running `sync-guardrails.ps1 -Init` also sets it.

> **Platform note:** the session-start digest is a PowerShell script (this is a Windows
> setup). On macOS or Linux it needs a POSIX equivalent. The two *git* hooks are
> `#!/bin/sh` and work everywhere, including Windows, because git ships its own shell.

### If the repo already has a `.claude/settings.json`

The script will not touch it — merging JSON blindly would clobber your permissions and
env settings. It prints a `!` notice instead; copy the `SessionStart` block from
`templates/hooks/settings.json` into your existing file by hand.

**Expect that same `!` on every re-run**, including on a repo the script set up itself.
It only checks whether the file exists, not whether the hook is already wired. If your
`settings.json` already has a `SessionStart` block, the notice is noise — ignore it.

### If the new project starts from an existing repo's code

Don't use step 1. Either `gh repo fork`, or clone and re-point the remote, *then* run
step 2 onward against the result. Also delete or triage the inherited `issues/` — an
imported backlog that nobody has read is worse than an empty one, because the digest
will show it every session until someone does.

Repo-specific overrides go in the `CLAUDE.md` below the repo nuance — later content
takes precedence, so a repo can override a shared rule with a stated reason.

### Updating a repo you onboarded earlier

Re-run the same command. Both forms leave your adapted files alone; the only file
rewritten every time is the generated `.claude/rules/00-guardrails.md`:

- **`-Init`** — brings an older repo fully up to date: refreshed rules, any missing
  `agent-constraints/` file, **and** the hooks/tracker machinery it never had.
- **without `-Init`** — the light touch: rules plus missing constraint files only. No
  hooks, no `issues/`, no git config changes.

Either way, files the repo already has are left alone, so local adaptations survive.
The script prints what it added and what it skipped.

### Hand this to Claude instead

In a fresh repo, paste this prompt and let the AI do the above:

```
This repo should follow my standing AI best practices, which live in the private
repo trurner13/TRT-AI-guardrails. Clone it (gh repo clone) if you don't have it, then
run its scripts/sync-guardrails.ps1 -Repo <this repo> -Init. That vendors the rules to
.claude/rules/00-guardrails.md, copies the agent-constraints/ operational starter, and
installs the machinery: the SessionStart digest hook, the commit-msg and pre-commit git
hooks, the issues/ tracker, core.hooksPath, and the .gitignore entry for worktrees.
Make sure this repo has a lean root CLAUDE.md declaring it AI-first and pointing at
agent-constraints/ (create from templates/new-repo-CLAUDE.md if missing), then commit.
Confirm with /memory that 00-guardrails.md loads and that `git config core.hooksPath`
prints .githooks.
```

### The automated option (recommended once rules stabilize)

Turn a starter repo into a **GitHub template repo** that already contains a
`CLAUDE.md` with the snippet. Then "Use this template" → every new repo starts
compliant with zero steps. (Ask Claude to set this up when you're ready.)

---

## 3. Existing-repo adaptation plan

> **Brownfield playbook:** the concrete, gradual steps live in
> [`templates/brownfield-adoption.md`](templates/brownfield-adoption.md) (Katie
> Roberts + Stack: map → one constraint → pick a pattern → one slice at a time).
> The phases below are the lighter-weight version of the same idea.

Goal: bring a repo you already have into line with the guardrails — without a
big-bang rewrite. Do it per repo, in phases. Each phase has a prompt you can
paste into Claude while working *in that repo*.

> Prerequisite: `RULES.md` has real content (see the gate at the top).

### Phase 0 — Make it aware (5 min, non-invasive)

Vendor the rules into the repo (`.claude/rules/00-guardrails.md`) and add a lean
`CLAUDE.md` if it lacks one. Nothing else changes yet. Use the new-repo prompt above,
or run `sync-guardrails.ps1 -Repo <repo>` and commit.

### Phase 1 — Audit against the rules (read-only, no changes)

Have the AI compare the repo to the guardrails and produce a gap list. Paste:

```
Read rules/RULES.md from the trurner13/TRT-AI-guardrails repo (clone it with
gh if needed). Then audit THIS repo against those rules. Produce a table:
rule | does this repo follow it? (yes/partial/no) | evidence | what to change.
Do not change any files yet — just give me the gap list, ordered by impact.
```

### Phase 2 — Prioritize

From the gap list, pick the changes worth making. Not every rule applies to
every repo — record the deliberate exceptions (see below) rather than forcing a
fit.

### Phase 3 — Remediate, one gap at a time

For each chosen gap, paste:

```
Implement the fix for gap #<n> from the audit. Make the change, explain what you
did in plain English, and stop so I can review before moving to the next gap.
```

Small, reviewable steps beat one sweeping change — especially since you're
reviewing in plain English rather than reading code.

### Phase 4 — Record exceptions and re-check

- Where a repo intentionally departs from a rule, note it in that repo's
  `CLAUDE.md` under a short "Guardrail exceptions" heading, with the reason.
  That keeps future audits honest.
- Re-run the Phase 1 audit periodically (e.g. when `RULES.md` gains major new
  rules) to catch drift.

### Suggested rollout order across repos

1. The repo you touch most often (fastest payoff).
2. Then the rest, one at a time — don't batch ten repos at once.
