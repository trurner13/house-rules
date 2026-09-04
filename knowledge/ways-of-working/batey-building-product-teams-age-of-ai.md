# Running product teams when AI amplifies everything

**Principle:** AI is an amplifier, not a fix — it speeds up building but magnifies weak product decisions, shallow system understanding, and limited review capacity. Counter it with disciplined practice, small adoption-bound teams, and measuring real adoption rather than output volume.

**Why:** When you let a team generate code faster without changing how it decides, understands, and reviews, the bottleneck simply moves. Production rate goes up while human review capacity stays flat, so review becomes the constraint. Meanwhile vanity metrics (commits, PRs, tokens) make a team look productive while nothing valuable actually ships or gets used.

**How to apply:**
- **Organise around three pillars.** (1) A path to production that works at AI speed, (2) a way to train and evaluate AI-enabled engineers, and (3) a workflow designed for parallel change. Treat these as the standing agenda you revisit every quarter.
- **Write ADRs first.** Capture the architecture decision before the agent writes code. The decision record becomes the spec the agent works against and the artifact reviewers check against — design is the leverage point, not the typing.
- **Expect review to become the bottleneck** and invest there deliberately: smaller diffs, clearer decision records, and reviewer time treated as the scarce resource — not coding time.
- **Understand the "producer black box": harness + host + model.** When AI output is wrong, debug all three layers (the tooling/harness, the environment it runs in, the model itself) rather than blaming the model alone.
- **Keep teams tiny and mission-bound:** two-to-four-person sub-streams, each owning a slice end to end. The mantra is "you build it, you run it, you drive adoption" — ownership extends past shipping into making people actually use it.
- **Parallelise, but only one complex task at a time.** Run many simple tasks in parallel; serialise the genuinely hard one so a human can hold it in their head.
- **Measure adoption, not vanity metrics.** Commits, PRs, and token counts are noise; the real signal is whether the thing is used. See `evals`.

**Source:** Christopher Batey — "Building Product Teams in the Age of AI: What We Had to Relearn Every Quarter", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-batey-building-product-teams-age-of-ai/SKILL.md)
