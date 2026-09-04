# Treat AI skills as software, not solo hacks

**Principle:** A skill that works for one person becomes "skills sprawl" across a team. Manage skills with the same discipline software earned over 20 years: decompose, version-control, review, register, and measure them.

**Why:** Solo skills are quick wins, but at team scale they overlap, drift apart, fail to trigger, go stale, and bloat. Without discipline you re-learn the painful lessons of software engineering — except now for the context layer instead of the code layer.

**How to apply:**

- **Watch for the five failure modes of skills sprawl.** Audit your setup against each:
  - *Overlap* — two skills do nearly the same thing, so the agent picks inconsistently.
  - *Drift* — copies of a skill diverge across people/machines ("works on my machine").
  - *Activation* — the skill exists but never triggers when it should.
  - *Rot* — the skill silently goes stale as the codebase or tools move on.
  - *Overloading* — one skill tries to do too much and loses focus.
- **Remember the agentic equation: model + harness + context.** A skill is part of the context input. You can't control the model, so quality comes from engineering the harness and context deliberately.
- **Adopt the skills-as-software checklist:**
  - *Decompose* big skills into small ones with a single responsibility.
  - *Version-control skills inside the repo* — never install them globally (e.g. avoid dumping into `~/.claude/`), which is the root of drift.
  - *Extend, don't edit* third-party/vendored skills, so you can take upstream updates.
  - *Automate skill review* — linting plus LLM-as-judge — like CI for code.
  - *Publish to a registry* for governance, security scans, a minimum release age, and discoverability.
  - *Keep skills agent-agnostic* — don't lock to one tool.
  - *Measure with evals* and treat context as a shared team asset, not personal config.
- **Frame the whole effort as the Context Development Life Cycle (CDLC)** — the SDLC's lessons applied to context. Don't repeat history.

See also `evals` for measuring skill quality.

**Source:** James Moss — "Using skills to pay the bills: graduating from solo hacks to a team workflow", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-moss-skills-team-workflow/SKILL.md)
