# Session handover: work state must outlive the session

**Principle:** A session is not a unit of storage. Everything that matters — the diff,
the intent behind it, and the four things you noticed but didn't do — must be written
somewhere durable *before the turn ends*, because a session can stop at any moment
without warning and nothing left in its context survives.

**Why:** This is the same failure as
[findings-to-guardrails](findings-to-guardrails.md), one level up. That note is about a
*correction* living for one context window; this one is about the *work itself* doing
the same. The remedy is identical — build the memory outside the agent — but the two
things being remembered are different, and they need different homes.

Work state has exactly two halves, and losing either one breaks the handover:

- **Code state** — what has actually been changed. Its durable home is a commit on the
  feature branch, pushed.
- **Intent state** — what this work is, what comes next, and everything that was
  spotted along the way. Its durable home is
  [an issue file in the repo](../../templates/agent-constraints/issue-tracker.md).

A session that ends with either half only in the transcript has not handed over. It has
just stopped.

## How it actually fails

This is one causal chain, not a list of separate problems. Every link is a real,
observed behaviour rather than a hypothesis:

1. **Nothing forces a commit.** Mid-session the tree holds tracked edits, new untracked
   files, and gitignored local config. No control anywhere requires that to change.
2. **The session ends by a path that runs no cleanup** — a closed window, a crash, a
   context limit, `/clear`. Cleanup that only happens on the graceful exit doesn't
   happen when it matters.
3. **The automatic sweep is designed to abstain.** Claude Code's periodic worktree sweep
   explicitly *skips* any worktree that still holds changed files, untracked files or
   unpushed commits, and never touches one created with `--worktree`. Dirty worktrees
   therefore accumulate by design — the safety net declines in precisely the case you
   needed it. Headless `-p` runs have no exit prompt at all.
4. **The issue list evaporates.** In-session task lists live outside the repo in
   machine-local state that is swept on a retention timer and documented as safe to
   delete. The one place the four un-pursued issues were recorded is explicitly
   disposable.
5. **The next session cannot see any of it, and has no reason to look.** `git status`
   reports only the worktree it runs in; there is no repo-wide dirty check. Prose in
   `CLAUDE.md` telling the agent to check for prior work is advisory and fades mid-session.
6. **It tries the branch, is blocked, and routes around the block.** `git checkout`,
   `git switch` and `git worktree add` all fail identically on a branch checked out
   elsewhere. All three escapes are destructive: `--force` puts two worktrees on one
   branch, where the second's stale index turns a later commit into a **silent revert**
   of the first's work; `--detach` produces commits that become unreachable the instant
   the worktree is removed; and a new path makes `git worktree add` **invent** a branch name from the
   path — or silently reuse an existing branch with no warning. That last one is where
   `feature-import-2` comes from.
7. **Every naive "save my work" command loses something.** `git commit -am` does not
   stage untracked files. `git stash` is a single repo-global stack shared by every
   worktree, so another session can pop and drop yours onto the wrong branch — and it
   leaves untracked and ignored files in place, so the tree only *looks* saved.
   `git checkout <branch>` silently carries staged and untracked changes across.
8. **Cleanup destroys the remainder, asymmetrically.** `git worktree remove --force`
   deletes untracked *and* ignored files. Anything `git add`-ed survives as an anonymous
   dangling blob — no filename, no path, findable via `git fsck --lost-found`, and
   time-limited by garbage collection. Anything unstaged or untracked was never hashed
   and is simply gone. `git worktree prune` never deletes files but deletes the admin
   directory, permanently orphaning a temporarily-offline checkout — and
   `git worktree repair` **cannot** undo it, which is the trap, because repair is what
   you reach for.

**In one sentence:** there is no durable record of what state the work is in or what was
noticed, and every mechanism an agent improvises to create one has a silent-loss mode.

## The correction worth understanding

The obvious fix — "when the session ends, commit everything and close the worktree" —
is right about the goal and wrong about the mechanism, for one structural reason:

**A session-end hook cannot be a gate.** It cannot block, its output is discarded, it
has a 1.5-second default budget (raisable to 60 seconds per-hook), and there is no
documented guarantee it fires on a crash, a kill, or a closed window. A hook that may
not run, cannot block, and may be cut off mid-push is a backstop. Building the scheme on
it means the scheme fails in exactly the cases it exists for.

Two substitutions fix this without removing anything that was asked for:

- **Move the checkpoint from session-end to turn-end.** A `Stop` hook fires at the end
  of every assistant turn and *can* block. Checkpoint there and a crash costs one turn
  instead of a session. The session-end action still happens — it just stops being
  load-bearing.
- **Make the next session's *start* the blocking gate.** This is the move that actually
  closes the loop, and it inverts the problem: **you cannot guarantee a clean shutdown,
  so guarantee mandatory recovery instead.** A gate that refuses to create a new
  workspace while any worktree is dirty, any branch carries an un-resumed checkpoint, or
  any commit is unpushed converts every failure above from *silent loss* into *the next
  session is forced to deal with it*. A shutdown gate protects one session. A startup
  gate protects all of them — including the ones that already crashed.

Two clauses of the naive version also need correcting. **Never close a worktree with
`--force`**: a refusal to remove a dirty worktree is a correctness signal that the
checkpoint missed something, and forcing past it deletes untracked and ignored files.
And **the interim commit must be pushed** — an unpushed checkpoint is recoverable only
by an expert on the same machine, and invisible to anyone looking at the remote.

**How to apply:** the mechanics, commands and hook wiring are in
[session-lifecycle](../../templates/agent-constraints/session-lifecycle.md) and
[issue-tracker](../../templates/agent-constraints/issue-tracker.md). The judgement calls
behind them:

- **Name the workspace after the issue.** `claude --worktree <name>` reopens an existing
  worktree of that name rather than creating a new one, so an id-based naming convention
  fixes most of the duplicate-worktree problem for the price of a convention rather than
  a hook. Do the cheap structural fix before the expensive enforced one.
- **Capture before you pursue.** The moment a second issue is noticed, it gets a file —
  *then* you go back to the first. This is the entire fix for "the other four were lost".
  It only works if capture is trivially cheap, which is why the capture form is seven
  lines with two required fields.
- **Put the ban list where it will be read.** `-am`, `--no-verify`, `--force`,
  `--detach`, bare `prune`, `stash`-as-handover: these are not obscure. They are the
  commands an agent reaches for *first* when trying to be helpful about saving work.
- **Place each half of the guardrail honestly on the
  [advisory→binding ladder](findings-to-guardrails.md).** Some of this genuinely can be
  enforced: a `commit-msg` hook rejecting a malformed checkpoint is pure git, has no
  override, and works for human commits too. Some of it cannot: no check can detect an
  issue that was thought about and never written down. Say which is which. A guardrail
  that reads as stronger than it is will be trusted more than it deserves.
- **Duplicate every hook check in CI.** A `Stop` hook is overridden after repeated
  consecutive blocks *(our note records a ceiling of 8; the current docs don't state a
  number — [unverified])*. CI has no override, and that is what makes the ceiling
  survivable.
- **Prefer the harness's own mechanisms** where they exist — `.worktreeinclude` carries
  gitignored files like `.env` into every new worktree, which is a real fix for the one
  thing no git mechanism captures.

## Salvage, when it has already gone wrong

- **Staged content after a forced removal:** `git fsck --lost-found` lists dangling
  blobs. They have no filenames and the window is time-limited by `gc` — recover early,
  and don't count on it.
- **A pruned worktree's admin directory:** `git worktree repair` will not fix it. The
  files are still on disk; treat it as an untracked directory and re-import by hand.
- **A detached-HEAD worktree's commits:** recoverable from the reflog while the worktree
  exists. Once it is removed they become unreachable and the per-worktree reflog goes
  with them — but the objects survive, so `git fsck --lost-found` still returns the
  commit with its full tree and filenames until `gc` prunes it.
- Treat any of these as a **data-loss incident to inspect**, not an error to retry. The
  retry is usually what destroys the evidence.

## The honest limit

A tracker does not create discipline, and neither does a rule. The agent will not reach
for either unprompted, and instructions in an always-loaded file fade under pressure
mid-session. That is not an argument against writing them down — it is the argument for
**reading the tracker at `SessionStart`** (where stdout is injected into context, so the
agent starts holding the list without having chosen to look) and **writing at `Stop`**
(where a hook can act every turn). Any version of this guardrail that is prose only has
already failed; treat it as a staging post on the way to the hooks, not the destination.

**Related:** [findings-to-guardrails](findings-to-guardrails.md) (the same loop, applied
to defects), [context-engineering-and-memory](../prompting/context-engineering-and-memory.md)
(memory as versioned files — that note covers curating a memory *store*; this one covers
handing over unfinished *work*), [marsden-agent-desktops](../agents/marsden-agent-desktops.md)
(isolated workspace per agent — the rule this extends with a lifecycle).

**Source:** Our own experience — reported repeatedly on a complex multi-session project,
where sessions left branches with uncommitted changes, new sessions opened rival
worktrees, and identified issues were lost in the prompt history whenever one of them
was pursued in depth. Diagnosed 2026-08-14 against git 2.52.0 and Claude Code v2.1.220
(hook blocking behaviour, worktree cleanup rules and `.worktreeinclude` verified against
the live docs that day). The git failure modes were reproduced directly rather than
inferred.
