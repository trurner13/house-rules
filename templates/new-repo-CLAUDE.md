<!-- STARTER CLAUDE.md for a new AI-first repo. Copy to <your-repo>/CLAUDE.md and
     fill the <placeholders>. Keep it lean (<~150 lines): this loads every session.
     Put detailed/path-specific rules in .claude/rules/, procedures in .claude/skills/.
     Full repo layout standard: templates/repo-structure.md.
     Phase conventions (triage/plan/adversarial/implement) + the two cross-cutting files
     (issue-tracker, session-lifecycle): templates/agent-constraints/. -->

# <Repo name>

<!-- The shared, adopted guardrails are VENDORED into this repo at
     .claude/rules/00-guardrails.md and load automatically every session (Claude
     Code auto-loads .claude/rules/*.md). The operational HOW lives in agent-constraints/.
     Both are laid down by `scripts/sync-guardrails.ps1 -Repo <repo> -Init` and work on
     any machine with a plain `git clone` — no import line, no global setup. Re-sync the
     rules with the same script (no -Init) when they change — see ADOPTION.md §2. -->

## This repo (AI-first)

Humans architect, design, and review; AI writes the code. No hand-written production code.

- **Purpose:** <one line — what this repo does and for whom>
- **Stack:** <languages / frameworks / key libs, with versions where they matter>
- **Commands:** build `<...>` · test `<...>` · lint `<...>`
- **Layout:** <key directories and what lives where>
- **How we work here:** follow the phase flow in [`agent-constraints/`](agent-constraints/README.md) — triage → plan → adversarial review → implement → verify/gate → merge. **First moves on a new repo:** make sure the fundamentals exist (CI + a way to ship + tests + lint), then work **spec-first** (write/approve a `SPEC.md` before building).
- **Every session:** start by reconciling in-flight work and reading [`issues/`](agent-constraints/issue-tracker.md) — resume what exists rather than opening a rival branch or worktree; capture anything you notice as its own issue before moving on; checkpoint the branch every turn and leave nothing uncommitted at the end ([`session-lifecycle`](agent-constraints/session-lifecycle.md)).
- **Conventions:** <non-default rules — e.g. naming, error format, no `any`>
- **Protected / careful:** <e.g. `.env`, migrations, anything irreversible>

## Repo-specific nuance & overrides
<!-- The shared rules in .claude/rules/00-guardrails.md are the baseline; anything
     here is repo-specific and takes precedence for THIS repo. Add repo-specific rules, and note any
     deliberate departure from a shared rule WITH THE REASON, e.g.:
       - Override: throwaway prototype — spec-first relaxed for the spike phase.
       - Override: no production services here, so the production-context rule N/A.
     If a departure turns out to be general/permanent, propose it back to the
     guardrails repo instead of keeping it local. -->
- <repo-specific rule or override, with reason — or "none yet">

<!-- Self-improvement: when you hit a non-obvious gotcha that would trip a future
     session, record it here (or in .claude/rules/) and propose a CLAUDE.md update. -->
