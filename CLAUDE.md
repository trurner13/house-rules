# Working in this repo

This is a **knowledge base of AI engineering practice**, plus the hooks, gates and
templates that enforce it. It is the published cut of a working repo: the rules and
machinery ship here, the day-to-day tracker and raw source material stay private.
Treat the contents as the authoritative source for how AI work should be done
across my other repos.

**All of my repos — including this one — are AI-first:** humans own
architecture, intent, and review; AI writes the code. No human-written production
code. (See the rule in `rules/RULES.md`.)

When helping in this repo:

- **Write down anything you spot before the session moves on.** Work in this repo
  is tracked in the private source repo; a finding that only exists in a session
  transcript is a finding that is already lost.
- **Capturing a new practice:** put the full note in `knowledge/<topic>/` (one
  idea per file, use the template in `CONTRIBUTING.md`). If it's universal,
  also add a one-line entry to `rules/RULES.md`.
- **Keep `rules/RULES.md` lean.** It is vendored into every repo as
  `.claude/rules/00-guardrails.md` (which Claude Code auto-loads), so it loads in
  *every* session of *every* repo. Each rule should be one or two lines and link
  to the deeper `knowledge/` file for detail.
- **Write in plain English.** No code unless the practice itself is a snippet
  worth reusing.
- **Don't proliferate files.** Before creating any new file or folder, check
  whether the content belongs in an existing one and add it there. Reuse existing
  structure; only create something new when nothing suitable exists. Prefer
  extending over duplicating, and consolidate overlap when you find it.

## Guardrail exceptions (how this repo follows its own rules)

This repo dogfoods `rules/RULES.md`, but it's a prose knowledge base, not a code
project — so some rules are adapted or N/A. The charter is [`SPEC.md`](SPEC.md);
the gates run in [`.github/workflows/checks.yml`](.github/workflows/checks.yml).
Deliberate departures, with reasons:

- **Code-specific rules — N/A here:** tests-as-source-of-truth, three-gate UAT,
  fundamentals (build/CI for *code*), language lint / no-`any`, dual log+JSON output,
  license headers, deterministic-artifact execution. *Reason: no application,
  runtime, or build artifact exists — there's nothing to test/compile/run.* The
  *spirit* (deterministic quality gates) is met by markdown-lint + link-check +
  RULES-lean check.
- **Adversarial reviewer — adapted, not full:** no adversarial *code* reviewer. The
  equivalent here is human review plus the automated doc gates. *Reason: single
  maintainer, prose changes.*
- **Full PR + auto-merge flow — deferred (scope choice):** we run the gates on push
  to `main` rather than gating every change behind a PR + adversarial-content review +
  auto-merge/`hold`. *Reason: chose the "minimal" dogfood for a solo prose repo; the
  full flow is available to adopt later (it's documented in
  [`templates/agent-constraints/verification-and-gates.md`](templates/agent-constraints/verification-and-gates.md)).*
- **Isolated env per agent (worktrees) — half N/A, half not optional.** Work happens in
  the main working copy and `git worktree list` shows one entry. *Reason: one agent at a
  time, so the **isolation** half buys nothing here; adopt worktrees if this becomes
  multi-agent.* But the **session-boundary** half of that rule — reconcile before you
  start, checkpoint before the turn ends, leave nothing uncommitted — applies at one
  agent exactly as much as at ten, and is **not** excepted. A session here ends with the
  tree clean and the work checkpointed, or it hasn't ended properly. See
  [session-lifecycle](templates/agent-constraints/session-lifecycle.md).
- **Central issue tracker — adapted, and kept out of the published cut.** The adopted
  rule is one file per issue under `issues/`; the source repo runs a single dated
  tracker file instead. *Reason: one-file-per-issue exists to stop two worktrees
  conflicting on every append — a concurrency failure a solo prose repo with one agent
  and no feature branches never has.* The **discipline** is not excepted: anything
  spotted mid-session gets written down before the session moves on. Revisit if this
  repo ever runs parallel agents.
- **Isolate at the boundary (sandboxing) — known gap on Windows:** Claude Code's
  OS-level Bash sandbox (`/sandbox`) runs on macOS, Linux and WSL2 — **not native
  Windows**, which is where this repo is worked on. So the "isolate at the boundary"
  rule is currently aspirational here, and the boundary is really the machine.
  *Reason: prose repo, no code execution or untrusted input, so low exposure — but this
  stops being acceptable the moment an agent on this machine touches production
  credentials or third-party code.* Closing it means running Claude Code inside WSL2.
  Recorded 2026-08-12.
- **Standard `.claude/` structure — N/A as the source:** this repo *is* the source of
  the rules, so it doesn't vendor a copy of itself; it has this `CLAUDE.md` + `SPEC.md`
  instead of the consumer layout.
