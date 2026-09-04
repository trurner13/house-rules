# Brownfield adoption — bringing an existing repo to agent-only, gradually

For repos that already have a pile of human-written code (your 2 inherited ones, and
the 12 you built before this). The goal is **not** a big-bang rewrite — it's a slow,
safe slide toward agent-only, one small area at a time.

Built from Katie Roberts' "Stop Maintaining, Start Evolving" (AI Native DevCon London
2026) + Paul Stack's "start tiny." Mindset throughout: **don't trust AI blindly about
old code, work in small versioned scopes, keep a human checkpoint, and do one area at a
time.** Her headline takeaways: *start with a map, not a migration; let your spec be the
contract; think slices, not rewrites; complexity is the opportunity.*

## Phase 0 — Make the repo guardrail-aware (5 min, zero risk)

Add a lean `CLAUDE.md` (from [new-repo-CLAUDE.md](new-repo-CLAUDE.md)) and lay down the
full kit — `scripts/sync-guardrails.ps1 -Repo <repo> -Init` (vendors the rules into
`.claude/rules/00-guardrails.md` **and** copies the `agent-constraints/` how-to), then
commit. Nothing else changes yet. In the "Repo-specific overrides" section, note it's
brownfield: `Override: brownfield repo — new code follows the rules; legacy is migrated
gradually (see below).`

## Phase 1 — Map before you change: people first, then AI (read-only)

**Start with people, not code — developers are the eyewitnesses.** (Roberts frames it as
forensics, citing *Your Code as a Crime Scene* — code analysis is just one piece of
evidence.)

1. **Interview the developers** and run a **value-vs-complexity workshop** (she used a
   Miro board, fully remote) so the team plots which areas are high-value AND
   high-complexity — that's where modernization pays off ("complexity is the
   opportunity").
2. **Then point AI at the *specific* problem areas the humans flagged** — not the whole
   repo. Run targeted investigations: dead-code paths, duplication, pattern
   inconsistencies, complexity hot spots, a light OWASP-style smell scan (*not* a
   replacement for real security scanning), dependency graphs, and **a map of what the
   code does *now*** — not what the (rotted) docs claim.
3. Produce a **prioritized findings backlog** and **human-readable docs reviewed by the
   whole team**. Don't let AI change code in this phase.

A surprising benefit: because the findings are AI-authored objective data — "not written
by the cleverest person on the team" — more people contribute, and it **breaks the
bike-shedding bottleneck** (objective metrics replace "the principal engineer says X").
*You* still hold context the AI can't infer — you're not a tourist in your own repo.

## Phase 2 — Stand the guardrails up GREEN before any implementation

Get tests, logs, and static analysis **working and trusted first** — Roberts' team spent
real time making sure SonarQube (or equivalent) was "up, running, working, and reporting"
and that they had confidence in the test suites *before* touching anything. Encode the
anti-patterns you found as **"more like this / less like that" skills kept alongside the
code**, so agents don't repeat the bad patterns. (This is the "never give the same
feedback twice" rule applied to a legacy codebase.)

## Phase 3 — Pick a migration pattern per area (don't force one)

- **Pseudo-greenfield** — build the new feature as if greenfield, branched out. Fast
  early. Risks: devs become "tourists" who never learn the codebase; you re-solve shared
  concerns (auth, logging, error handling); long-running branches diverge and become
  expensive to reintegrate or a permanent fork; integration bugs surface only at merge.
- **Strangler fig** (Fowler; used by Uber/Netflix/BBC) — replace a system alongside the
  original with no downtime; put a **facade/boundary** so legacy stays frozen. The
  **routing layer is the natural home for feature flags, A/B, canary, and rollback**, and
  progress is visible. Cost: two systems + two infra to run; finding abstraction points
  takes time; **requires commitment to completion** — a half-finished strangler is double
  maintenance.
- **Branch by abstraction** — work *inside* the codebase: put an interface in, branch to a
  new implementation behind a feature flag, run both at once to compare behaviour in
  production. Naturally **surfaces hidden dependencies/coupling**. Cost: the abstraction is
  extra code to write, maintain, and eventually delete; an abandoned abstraction adds
  cognitive load.
- **Default for everyday work:** new code is agent-only and follows the rules; old code
  gets migrated only when you're already touching that area.

## Phase 4 — Run the loop on one slice, then widen

On the chosen slice, run the full agent-only loop. Roberts' concrete pipeline:

- A **plan skill** captures the technical + product considerations → work is broken down
  (e.g. by a Jira-component skill) → handed to a **developer skill** that is a multi-agent
  flow: an **orchestrator** dispatches agents for (1) a dedupe check, (2) test scaffolding,
  (3) implementation, (4) static analysis + quality gates, (5) a **pre-review agent that
  reviews its own work** → **human review + sign-off** → main pipeline → an agent
  **updates the master plan**.
- **Flywheel:** the first couple of runs are slow while you get the skill right; then
  velocity compounds and devs run them "almost in the background," accumulating a
  **library of reusable skills** ("this is what good looks like").
- **Slice at the epic level** to small (1–2 person) feature teams + agents, and watch for
  **skill divergence** across teams — share skills so you don't build silos.

Keep the **blast radius small** and **version everything** so it's reviewable and
reversible. When it works, take the next slice.

## Brownfield-specific: planning expands, it doesn't shrink

Greenfield culture expects discovery/planning; brownfield culture is "let's all just dive
in" — so the plan phase gets skipped exactly where it's needed most. Going AI-native here
means **more** planning, not less — "proper archaeology on the codebase" before the build.

## Don't

- Don't point an agent at the whole legacy repo and hope.
- Don't rewrite everything at once.
- Don't skip the map — context first, change second.
- Don't start migrating before the guardrails (tests/static analysis) are green and trusted.

---

*Source: Katie Roberts, "Stop Maintaining, Start Evolving: Applying AI-Native Practices to
Brownfield Codebases" (AI Native DevCon London 2026) —
[transcript](https://www.youtube.com/watch?v=5SKh-FmjX7U) (auto-captions;
proper nouns may be misheard). Plus Paul Stack's "start tiny." Encode anti-patterns you
hit as new constraints so the agent stops repeating old mistakes.*
