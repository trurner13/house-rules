# Parallelise by default

**Principle:** Split work into independent pieces and run them at the same time —
separate sessions, each in its own worktree, and subagents fanned out inside a task.
Running things one after another is the exception, and it needs a reason.

**Why:** Agents are cheap and don't get tired; the scarce resource is calendar time.
Queuing independent work behind each other wastes it for nothing. The conference
evidence pulled both ways: Marsden runs many agents in parallel, while Batey and
Jourdan warned "one complex task at a time" because of the load on the humans. **Our
decision (2026-09-15): parallelise by default.** Their warning survives as the *limits*
below, not as the default.

**How to apply:**

- **Split at planning time.** Pieces are independent when they touch different files
  or modules and neither needs the other's output. Each piece gets its own issue, so
  each parallel line of work has a name, a branch and a `next:`.
- **Two kinds of parallel.**
  - *Across sessions* — several agents on one repo, each in its own worktree named
    after its issue. Reconcile what already exists first
    ([session-lifecycle](../../templates/agent-constraints/session-lifecycle.md)).
  - *Inside a task* — one agent fans out subagents for independent searches, reviews
    or checks. A subagent's file reads and tool output stay in its own context; only
    its conclusion comes back, which is also the main token-efficiency lever
    ([context-engineering-and-memory](../prompting/context-engineering-and-memory.md)).
- **Go serial when, and only when:**
  - the pieces edit the **same files** — parallel edits there produce merge conflicts
    at best and silent reverts at worst;
  - one piece **needs another's output**;
  - an **architectural decision** the others will build on isn't made yet. Make the
    decision first, then fan out.
- **Size the batch to the gates, not to the agent count.** Every parallel branch has
  to pass the same gates, and anything a human spot-checks lands in one person's
  queue. If branches are waiting on review or colliding at merge, the batch was too
  big. The limit is verification, not how many agents you can start.
- **Keep it legible.** Parallel work is only useful if you can still see what's
  going on:
  - worktrees live hidden inside the repo at `.claude/worktrees/<issue-id>`, **never**
    as folders beside the repo;
  - a worktree is removed once its branch merges;
  - the start-of-session digest lists whatever is still live.

  *Why not beside the repo:* one working machine had built up about 30 sibling
  worktree folders next to its repos, many of them finished work nobody removed, and
  telling live work from dead became genuinely confusing. Claude Code's own default is
  the hidden folder, so staying on it also keeps `--worktree <id>` reopening the right
  one.
- **Gotcha — make test runners and linters skip `.claude/worktrees/`.** A worktree
  nested inside the repo is a full second copy of the code. pytest skips dot-folders
  by default; Vitest and Jest don't, and will happily run every test twice or trip
  over duplicate package names. Add the folder to their excludes when you adopt this.

**Source:** conference conflict between Marsden and Batey/Jourdan (AI Native DevCon
London, June 2026); decided 2026-09-15 after the sibling-worktree sprawl above.
