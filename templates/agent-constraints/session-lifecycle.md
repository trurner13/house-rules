# Session lifecycle (starter)

What happens at the **boundaries** of an agent session — before the first change,
at every turn, and at the exit. This is the file that stops work being lost between
sessions. Adapt per repo; the depth and reasoning are in
[session-handover-and-work-state](https://github.com/trurner13/TRT-AI-guardrails/blob/main/knowledge/ways-of-working/session-handover-and-work-state.md).

The rule underneath all of it: **a session is not a unit of storage.** Anything that
matters must be on a branch, on the remote, or in the issue tracker before the turn
ends — because the session can stop at any moment without warning, and everything
still only in its context dies with it.

Work has exactly three durable homes:

| What | Where it survives | Lost if you skip it |
|---|---|---|
| Code state | a commit on the feature branch, **pushed** | the diff |
| Intent state — what this is, what's next | [`issues/<id>.md`](issue-tracker.md) | *why* the diff exists, and everything you noticed but didn't do |
| Environment state — gitignored files | `.worktreeinclude`, or a `Not-Captured:` list | `.env` and friends, silently |

## Start — reconcile before you create

The failure this prevents: a new session opens a second worktree, or a rival branch,
for work that is already half-done somewhere else. **Never create a workspace before
looking for one.**

Run this as one read-only pass. It takes under a second:

```bash
# 1. Where am I? (unequal = already inside a linked worktree)
#    --path-format=absolute on BOTH is required. --absolute-git-dir alone is
#    absolutised but --git-common-dir is not: from the main checkout it prints the
#    literal ".git", so comparing the two is unequal 100% of the time and the test
#    always answers "linked worktree".
git rev-parse --path-format=absolute --git-dir --git-common-dir

# 2. Every workspace, with its branch, lock and prunable state
git worktree list --porcelain

# 3. Is any of them dirty? -uall is REQUIRED: the default collapses an untracked
#    directory to a single "?? dir/" line, so a line count under-reports.
git -C "<each worktree path>" status --porcelain=v1 -uall

# 4. Branches parked at a checkpoint, with the next step already written down
git for-each-ref --format='%(refname:short) %(trailers:key=Next-Step,valueonly,unfold,separator=%x20)' refs/heads

# 5. Commits that exist only on this machine
git log --branches --not --remotes --oneline --decorate

# 6. The stash stack is REPO-GLOBAL and shared by every worktree — it may hold
#    another session's work, on another branch
git stash list

# 7. What is already in flight, from the tracker
git grep --untracked -l -E '^- status: (approved|implementing|pr_open)' -- ':(glob)issues/*.md'
```

Then, in order of preference: **resume** the existing workspace, **finish or drop** it,
or — only if it is genuinely unrelated work — create a new one.

Two traps in step 4/5 worth knowing: `unfold,separator=` is required, or a multi-line
trailer emits a newline and breaks the parse; and `%(upstream:track)` cannot replace
step 5, because empty means both "in sync" and "no upstream configured".

Also probe each worktree for an interrupted operation — `rebase-merge`, `rebase-apply`,
`MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `BISECT_LOG` under its own git dir. An
interrupted rebase leaves a **detached HEAD**, which every branch-based query above
misses entirely.

### Name the workspace after the issue

`claude --worktree <name>` **reopens** an existing worktree of that name instead of
creating a new one. So name it after the issue id and the collision problem largely
solves itself:

```bash
claude --worktree 2026-08-14-9d4c
```

One live branch per issue; the issue records the branch in its `branch:` field. This is
the cheapest fix available for "the new session made its own worktree" — it costs a
naming convention, not a hook.

## During — checkpoint at every turn, not at the end

**Do not rely on the exit.** A session-end hook cannot block, gets a 1.5-second budget
by default, and there is no documented guarantee it fires on a crash, a killed
terminal, or a closed window. Checkpoint at the end of every turn instead and a crash
costs you one turn rather than a session.

Whenever the tree is dirty:

1. **Refuse first.** If `git status --porcelain=v2` shows an unmerged entry (a line
   whose first field is `u`), or any
   in-progress-operation file exists, **stop and surface it**. This is the one case
   worth blocking on. `git add -A` during an unresolved conflict *clears* the unmerged
   state, after which `git commit` cheerfully succeeds and commits `<<<<<<<` markers
   onto the branch. Without the `add -A`, git would have refused.
2. `git add -A` — **never `git commit -am`**, which silently skips every new file the
   session created. This one flag is the single most common cause of "the work was
   there and now it isn't".

   ⚠️ **`add -A` stages whatever `.gitignore` failed to exclude, and step 4 then pushes
   it.** Automating this turns a gitignore gap into a published secret. Before turning
   the checkpoint on in a repo: confirm `.gitignore` actually covers env files,
   credentials, build output and dependency directories, and put a **secret scan in
   `pre-commit`** so the checkpoint refuses rather than publishes. This is the one place
   the automation can do more damage than the problem it solves — do not skip it.
3. Commit with the trailer block below.
4. `git push -u origin HEAD`, throttled — say, skip if the last push is under ten
   minutes old. Commits are cheap; pushes are not. **An unpushed checkpoint is not
   durable**: it dies with the disk, and a human looking at the remote cannot see it.
5. No-op if the tree was clean. This must be safe to run every turn.

### The checkpoint commit

```text
wip(<scope>): checkpoint - <one line>

<what state this is actually in>

Checkpoint: true
Next-Step: <what the next session does first>
Gate-Status: red|green <detail>
Not-Captured: .env, config/local.json
```

`Checkpoint: true` is the machine-readable hook — `git log --grep='^Checkpoint: true'`
and `%(trailers:key=Checkpoint,valueonly)` both find it. `Next-Step:` is the field that
actually carries the handover. `Not-Captured:` exists because **no git mechanism
captures ignored files**; if the next session needs them recreated, they have to be
named here.

This does not weaken "nothing proceeds on a red gate". A red checkpoint is not
progress — it is a parked state whose trailer records that it is red. What must never
happen is a red checkpoint being *merged*.

### Continuing a checkpoint later

Add another `wip(...)` commit, or `git commit --fixup=<sha>` and autosquash while it is
still local. **Never `--amend` a checkpoint**: `--amend -m` silently drops the
trailers, turning a discoverable checkpoint into an invisible one, and amending is
unsafe once pushed. Squash-on-merge collapses the whole chain at PR time, which is what
makes committing WIP to a feature branch harmless.

## End — best-effort, and label it that way

At exit: run the same checkpoint, push, `git worktree unlock`, then `git worktree
remove` **without `--force`**.

A refusal (`contains modified or untracked files`) is **a correctness signal that the
checkpoint missed something**, not an obstacle to force past. Investigate it; never
add `--force`. On Windows a single open file handle makes `worktree remove --force`
exit **255 after** deleting the `.git` pointer, the admin directory and every unlocked
file — so a non-zero exit there does **not** mean nothing happened.

## Never

| Command | What it actually does |
|---|---|
| `git commit -am` | skips untracked files — the new files are not in the commit |
| `git commit --no-verify` | disables `commit-msg` too, so it kills the very hook that makes a checkpoint discoverable. Use a named escape hatch (`CHECKPOINT=1`) instead |
| `git worktree add --force` | two worktrees on one branch; the second one's stale index turns a later commit into a **silent revert** of the first one's work |
| `git worktree add --detach` | commits become unreachable the instant the worktree is removed, taking its reflog with them. Recoverable as a dangling commit via `git fsck --lost-found` — complete with tree and filenames — but only until `gc` prunes it |
| `git worktree remove --force` | deletes untracked *and* ignored files. Staged content survives as an anonymous dangling blob (`git fsck --lost-found`, time-limited); unstaged and untracked content is simply gone |
| bare `git worktree prune` | deletes the admin dir of a temporarily-unreachable worktree, and **`git worktree repair` cannot undo it**. Run `-n -v` first, never while a path is offline |
| `git clean -ffdx` | deletes a nested worktree outright. Gitignoring it silences `git status` and provides **no** protection |
| `git stash` as a handover | one global stack shared across every worktree; another session can pop and drop yours onto the wrong branch. It also leaves untracked and ignored files in place, so the tree only *looks* saved |

## Wiring it up — honestly

Hook facts verified against the Claude Code docs and a local **v2.1.220** install,
2026-08-14.

| Boundary | Hook | Blocks? |
|---|---|---|
| Inject the tracker digest + reconciliation summary | `SessionStart` | **No** — but its stdout *is* added to context, which is the point: it removes the *decision* to look |
| Checkpoint the tree | `Stop` | **Yes.** Have it *act* every turn and block only on the refuse conditions |
| Refuse a malformed checkpoint | `commit-msg` (plain git) | **Yes**, absolutely — and it has no override, works for human commits, and needs no Claude Code version |
| Allow a red gate for a checkpoint only | `pre-commit` reading `CHECKPOINT=1` | **Yes.** Strictly better than `--no-verify` |
| Reconcile before a workspace is created | `WorktreeCreate` | **Yes** — "any non-zero exit code causes worktree creation to fail". Only fires for Claude Code's own worktree feature, so pair it with a `PreToolUse` matcher for raw `git worktree add` on **every** command-running tool — `Bash`, `PowerShell` and `Monitor`. A matcher covering one shell is a hole, not a gate |
| Close the workspace | `SessionEnd`, `WorktreeRemove` | **No.** Output discarded, 1.5s default budget (raisable to 60s per-hook). Backstop only |

Two honest limits, both of which must be stated wherever this is adopted:

- **A `Stop` hook is overridden after repeated consecutive blocks** — our note records
  a ceiling of 8; the current docs don't state a number *[unverified]*. It is a gate
  with teeth, not an absolute gate. **Duplicate every `Stop` check in CI**, which has
  no override. That is what makes the ceiling survivable.
- **A `PreToolUse` command matcher must evaluate the command as the shell will run it**
  — post-expansion, never raw text. Raw-text deny-lists are a documented failure mode.

### Windows

- **Windows PowerShell 5.1 has no `&&` or `||`.** `git add -A && git commit -m ...` is a
  parser error (`The token '&&' is not a valid statement separator in this version`), not
  a failed command — so a chained checkpoint doesn't half-run, it doesn't run at all. Use
  separate statements, or `A; if ($?) { B }`. The same applies to `?:`, `??` and `?.`.
  PowerShell 7+ and Git Bash are fine; don't assume which shell you're in.
- Claude Code puts worktrees in `.claude/worktrees/<name>/`. **Gitignore that path** —
  and note that gitignoring protects it from `git status` noise, not from `git clean`.
- `core.longpaths` is commonly unset and the 260-character `MAX_PATH` ceiling is real.
  Keep worktree names short, or set `core.longpaths` and the OS `LongPathsEnabled`.
- Close editors, dev servers and file watchers before removing a worktree — an open
  handle is what produces the partial-destruction exit 255 above.
- In any script an agent runs, prefer `git -C <absolute-path>` over `cd`. If the
  directory has vanished, `-C` fails loudly instead of silently retargeting whatever
  the shell fell back to — which is how a stray branch ends up in the wrong repository.

### Carrying gitignored files into a new workspace

A worktree is a fresh checkout, so `.env` is not in it. Add a `.worktreeinclude` at the
project root (gitignore syntax; only files that match *and* are gitignored are copied):

```text
.env
.env.local
config/secrets.json
```

This is the native fix for the `Not-Captured:` problem — prefer it to a hand-written
list wherever the repo supports it.

⚠️ **`.worktreeinclude` and a `WorktreeCreate` hook are mutually exclusive.** The hook
replaces the default git logic entirely, and the docs are explicit: `.worktreeinclude`
"is not processed when you use `--worktree`" once a hook is configured. Nothing errors —
`.env` just silently stops being copied, which is precisely the failure the durable-homes
table exists to prevent. If you adopt the create-time gate as a `WorktreeCreate` hook,
**move the file-copying into the hook script**. Prefer implementing that gate as a
`PreToolUse` matcher instead, and leave `WorktreeCreate` alone.

## Adopt it in this order

Do not ship all of this at once — it is the "start tiny" rule applied to itself. Each
step is useful alone and earns the next:

1. The issue tracker and the capture habit, by hand. **This alone fixes "issues get
   lost in the prompt history."**
2. The tracker's well-formedness check, in CI.
3. The `SessionStart` digest — pure upside, it cannot block anything. **With 1–3 you have
   the whole benefit at almost none of the cost. Most repos should stop here.**
4. `commit-msg` + `pre-commit` — pure git, so it works regardless of harness version.

### What we deliberately did NOT adopt, and why

**The `Stop` auto-checkpoint** — a hook that runs `git add -A`, commits and pushes at the
end of every turn. It is the only way to make checkpointing truly automatic, and we
**rejected it as disproportionate**. The reasoning is worth keeping, because it will be
proposed again:

- The startup digest already solves the actual problem. Uncommitted work is *found and
  surfaced* at the next session rather than silently lost. That is the whole benefit; the
  Stop hook only changes *when* it gets caught.
- It commits and pushes without anyone looking, every turn. `git add -A` stages whatever
  `.gitignore` missed, so it needs a secret scan in `pre-commit` before it is safe at all
  — real cost, on repos that genuinely hold service-account JSON and API keys.
- The remaining exposure is one session's work, recoverable from the working tree, which
  is not worth an always-on automation that can publish a credential.

Adopt it only where losing a session's work is genuinely expensive *and* the secret scan
is already in place. Otherwise the startup check is the right depth.

**The create-time reconciliation gate** (a `PreToolUse` matcher, or `WorktreeCreate`) is
likewise optional. Naming worktrees after the issue id already makes `--worktree` reopen
the existing one, which fixes most of the problem for the price of a convention.
