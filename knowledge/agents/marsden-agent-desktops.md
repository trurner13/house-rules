# Give Every Agent Its Own Desktop

**Principle:** When you run coding agents on the server, give each *agent* (not each human) its own full computer with an IDE, scale agent work by task rather than by org chart, and drive everything through a plan-then-implement spec flow — then dogfood the platform on itself until "the snake eats its own tail."

**Why:** Parallel agents that share one workspace step on each other and corrupt state. Treating an agent like a junior teammate without its own machine, IDE, and review loop produces unreviewable, untrusted output. And a platform you don't run on its own development never gets battle-tested, so the rough edges never surface.

**How to apply:**
- **Walk the seven design-space dimensions** when building or auditing an agent platform, in this order:
  1. *Local vs centralized* — run agents on shared server infrastructure, not on each developer's laptop.
  2. *IDE or not* — keep a real IDE in the loop so humans can see and steer (Marsden forks the Zed IDE for remote control).
  3. *Task-scaling vs org-scaling* — spin up capacity per task (e.g. Kanban cards that each launch a desktop), not per role; or use a coarse-role + task-scaling hybrid.
  4. *Spec-driven development* — split every job into a **plan phase** then an **implement phase**, with human review of the spec in between.
  5. *Mobile / multiplayer* — support multiplayer human-in-the-loop spec review and in-browser QA, accessible anywhere.
  6. *Dev-environment bootstrap speed* — make per-agent environments near-instant (Marsden uses ZFS-cloned Docker-in-Docker envs so each desktop is a cheap clone).
  7. *Token-cost / model strategy* — mix local models (e.g. Llama 3.1) with frontier models (e.g. Claude Opus) to control cost.
- **Give each agent a real, GPU-accelerated streaming Linux desktop** so it has the same tools a human dev would, and humans can drop in to observe or take over.
- **Audit yourself dimension by dimension:** for each, mark covered / partial / missing and close the gaps.
- Caveat: this framework targets *coding* agents; it says little about non-coding agent work.

See also `spec-driven-development` and `parallel-agents`.

**Source:** Luke Marsden — "Giving Every Agent Its Own Desktop: Lessons from Dogfooding HelixML", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-marsden-agent-desktops/SKILL.md)
