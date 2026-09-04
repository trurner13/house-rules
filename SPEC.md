# SPEC — TRT-AI-guardrails

The one-page charter for this repo. (Yes, the guardrails repo has a spec now — it
should practice the spec-first rule it preaches.) The detail lives in the files this
points to; this is the durable statement of *what this repo is and how it's run*.

## Purpose

The single source of truth for the owner's AI best practices — captured once here,
then **vendored into every other repo** so all of them are built the same way
(humans architect/spec/review; AI writes the code).

## What this repo is (and isn't)

- **Is:** a curated, plain-English **knowledge base** of adopted rules + the evidence
  and reasoning behind them, plus the templates/scripts that push them into other repos.
- **Isn't:** a code/product project. There is no application, runtime, or build
  artifact here — so the code-specific rules don't all apply (see
  [CLAUDE.md → Guardrail exceptions](CLAUDE.md)).

## Design (two layers + distribution)

- **Rules** — [`rules/RULES.md`](rules/RULES.md): short, universal, always-on
  directives. One line per rule, linking to the deeper note. Kept lean (enforced).
- **Knowledge** — [`knowledge/<topic>/`](knowledge/INDEX.md): the reasoning, examples,
  and nuance behind each rule. Read on demand.
- **Distribution** — the rules are **vendored** into each consuming repo as
  `.claude/rules/00-guardrails.md` (auto-loaded by Claude Code), and the operational
  "how" ships as [`templates/agent-constraints/`](templates/agent-constraints/README.md).
  Both are laid down by [`scripts/sync-guardrails.ps1 -Init`](scripts/sync-guardrails.ps1)
  and work on any machine from a plain clone. Full flow: [ADOPTION.md](ADOPTION.md).
- **Working notes** — the raw source material (conference transcripts, reading
  notes, the day-to-day tracker) stays in the private source repo. It is input,
  not the published surface.

## How a rule gets adopted

1. Capture the evidence — a talk, an article, a reference repo — and write it up
   in [`knowledge/`](knowledge/INDEX.md) with the source cited.
2. Decide one practice at a time, and record what was decided against and why.
3. If universal, add a lean line to `rules/RULES.md`; put the depth in `knowledge/`
   or `templates/agent-constraints/`.
4. Re-sync consuming repos (`sync-guardrails.ps1`) to pick up the change.

## How this repo is run (dogfooding)

- **Spec-first:** this file. Non-trivial changes start from intent, not code.
- **Automated gates** (the prose-appropriate "fundamentals first"), in
  [`.github/workflows/checks.yml`](.github/workflows/checks.yml) — nothing proceeds on red:
  - markdown lint of the published surface (entry docs + rules + templates),
  - internal links must resolve ([`scripts/check-links.mjs`](scripts/check-links.mjs)),
  - `RULES.md` stays lean ([`scripts/check-rules-lean.mjs`](scripts/check-rules-lean.mjs)).
- **Nothing carried silently:** anything found mid-session is written down before
  the session ends.
- **Deliberate exceptions** to the rules are recorded in [CLAUDE.md](CLAUDE.md).

## Out of scope

- Application/product code, runtime services, build/release pipelines.
- Tests/UAT, language-specific lint, and the full PR + adversarial-review + auto-merge
  flow — deferred (see exceptions). This repo is single-maintainer; the gates above
  are the right-sized substitute.

## Success

Adopting a new repo to the full kit takes minutes and "just works" on any machine;
every adopted rule is sourced, lean, and applied here too — not just preached.
