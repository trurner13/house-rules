# Humans Architect, AI Writes the Code

**Principle:** Move humans out of writing code and into expressing intent precisely. The quality of AI output mirrors how sharply you can state what you want, so the real engineering job becomes building the machine that writes the code — clear constraints, a review loop, and gated merges — not typing the code yourself.

**Why:** "Vibes don't scale." Loose prompting produces inconsistent, untrustworthy output that doesn't survive a real codebase. And in open source, human-authored pull requests are a supply-chain risk you can't fully vet. If intent is vague, the AI fills the gaps badly; if intent is captured as executable rules, the AI produces consistent, reviewable work at scale.

**How to apply:**
- **Intent is the new architecture.** Humans own architecture, constraints, and intent. Agents write every line of code. Spend your effort describing *what* and *why* with precision, not implementing the *how*.
- **CLAUDE.md as executable constraints.** Don't write prose guidelines — write rules the agent must obey on every change. Real examples from the talk: TypeScript strict, no `any`, named exports only, required license header, no fire-and-forget promises, imports from a known module, never leak implementation details. End it with: "if you hit a non-obvious problem, record it and propose an update" — so the constraint file learns.
- **No human PRs.** Internal or external pull requests written by humans are deleted on sight. Contributions come in as *issues* (intent); the agent writes the code. This keeps the supply chain trustworthy.
- **Planner + adversarial-reviewer loop.** One agent plans, a second adversarially reviews, iterate — with a hard cap (5 iterations) so it can't spin forever.
- **Five merge gates.** Nothing merges without passing: code check, adversarial review, UX check, CI security, and a skill check.
- **UAT as source of truth.** Keep user-acceptance tests in a separate repo; the tests, not the code, define correct behaviour.
- **Self-debugging agent.** When it hits an error, it opens an issue rather than silently failing.
- **Start small:** one constraint, one loop. Grow the machine from there.

See also `evals` and `skills`.

**Source:** Paul Stack — "The Humans Architect the System, the AI Writes the Code", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-stack-humans-architect-ai-writes-code/SKILL.md)
