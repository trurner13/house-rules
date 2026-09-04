# Surviving the AI-Native Shift: Feedback Loops and Harness Engineering

**Principle:** Treat the AI shift as a whole-organisation change, not an engineering one, and survive it by investing in disciplined feedback loops, first-class harness engineering, and AI-adapted observability — before you let any agent run unsupervised.

**Why:** The move to AI-native is faster and more sweeping than cloud or DevOps because it forces *every* department to adapt, not just engineering. Teams that skip the discipline drown in low-signal noise, can't tell when an AI is drifting, and hand autonomy to systems they can't actually see into. The teams that improve over time are the ones who close the loop between production behaviour and how they build.

**How to apply:**

- **Make harness engineering a first-class discipline.** Don't treat prompts, guardrails, input/output validation, and feedback mechanisms as afterthoughts. Build them as deliberate, owned engineering work that makes AI behaviour testable and improvable. If you can't test and iterate on the harness, you don't have one.
- **Place yourself on the co-driving vs. self-driving spectrum, deliberately.** Co-driving means AI augments human decisions; self-driving means autonomous in production. Pick your point based on organisational maturity, not ambition. Even "low-risk" autonomous actions sit toward the self-driving end and demand governance.
- **Close the feedback loop before removing human sign-off.** This is the panel's core differentiator between teams that improve and teams that stagnate. Structurally capture production signals (user feedback, error rates, downstream outcomes) and route them back into evaluation or prompt refinement. See `evals`.
- **Define what a meaningful signal is** before wiring up alerts — undefined signals create alert fatigue and hide the real drift.
- **Use reflector agents** to watch their own outputs and production behaviour for anomalies/drift, closing the loop without constant human review.
- **Upgrade observability for AI.** Traditional APM isn't enough; add prompt/response logging, token-level tracing, and semantic drift detection.
- **Govern self-learning agents tightly.** Agents that self-modify from production feedback carry real risk; gate any autonomy on observability maturity.

**Source:** Stephane Jourdan (with Simon, Saxo Bank, and Samantha) — "From Pipelines to Prompts: Surviving the Shift to AI", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-jourdan-pipelines-to-prompts/SKILL.md)
