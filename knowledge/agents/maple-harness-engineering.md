# Harness Engineering: surface the right context to coding agents just-in-time

**Principle:** The bottleneck in software is no longer writing code — it's human time, attention, and the model's context window. So make your team's "definition of a good job" legible to agents, encode it as static guardrails, and surface that context just-in-time across the agent's run rather than dumping it up front.

**Why:** Agents can produce code endlessly, but a human still has to review and own it. If your non-functional requirements (style, patterns, quality bars) live only in people's heads, every PR drifts and every review burns scarce human attention. Writing it down once, and intervening automatically at the right moment, is how you scale oversight instead of becoming the bottleneck.

**How to apply:**

- **Respect the three foundational constraints.** Optimise everything for human *time*, human *attention*, and the *context window*. If a practice doesn't reduce load on one of these, question it.
- **Write it down.** Make the definition of "good" explicit — don't rely on tribal knowledge the agent can't see.
- **Use an `agents.md` as a map, not a dumping ground.** Give it numbered grounding steps that point out to curated files, rather than jamming every rule inline (which floods the context window).
- **Curate review personas** as bolded guardrail lists in separate files (e.g. a security reviewer, a performance reviewer) the agent loads when relevant.
- **Think in three phases of context delivery:** grounding (start) → the messy middle (mid-trajectory) → review & merge. Deliver each guardrail in the phase where it bites.
- **Shift interventions RIGHT, not left.** Instead of more synchronous human pre-work, lean on just-in-time signals: descriptive lint/test failures whose error messages point to runbooks, snapshot tests with high branch coverage, banning loose types like `any`/`unknown`.
- **Put LLM-as-judge reviewer agents in CI** to catch issues before a human looks.
- **Capture and distil human feedback** systematically so corrections become future guardrails.
- **Unify the codebase** on consistent patterns to lower attention cost. Treat the agent as a teammate you onboard.

See also `evals` and `skills`.

**Source:** Simon Maple — "Welcome to AI Native DevCon" (Harness Engineering), AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-maple-harness-engineering/SKILL.md)
