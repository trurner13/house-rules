# agent-constraints (starter)

Phase-split constraint files for an AI-first repo's flow: **triage → plan →
(adversarial review) → implement → verify/gate → merge** — plus two **cross-cutting**
files that aren't phases at all: the session boundary and the issue tracker. Copy this
folder into a new repo (under `agent-constraints/` or fold into `.claude/rules/`) and
adapt per repo. The lean `CLAUDE.md` points the agent at these for the relevant phase.

Treat the flow as an **enforced state machine** where it's worth it: illegal phase
jumps fail and state persists across sessions (aspirational for a solo repo — start
as a checklist, harden later). See `verification-and-gates.md` for the gates that
must pass before merge.

Pattern **inspired by System Initiative's open-source `swamp`** (the AI-native CLI
from Paul Stack's talk — a real, working instance of these guardrails). `swamp` is
AGPL, so we wrote our own versions and borrow the *ideas*, not the files.

Files — the phases:

- `triage-conventions.md` — classify an incoming issue before planning.
- `planning-conventions.md` — write the plan/spec (spec-first) before implementing.
- `adversarial-dimensions.md` — the dimensions the adversarial reviewer challenges.
- `implementation-conventions.md` — general conventions for the implement phase.
- `verification-and-gates.md` — the merge gates, reviewer hardening, pre-flight
  checks, UAT on the built artifact, and evals that run before merge/release.

And the two cross-cutting ones — read these *first*, because they hold the state
everything else depends on:

- `issue-tracker.md` — the single list of every open issue, its status and its history.
  This is the on-disk state the flow above persists into; without it the state machine
  resets every session.
- `session-lifecycle.md` — what happens at the session boundary: reconcile before you
  create a workspace, checkpoint the branch every turn, close it cleanly at the end.
