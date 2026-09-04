# Make the spec, not the code, the durable artifact

**Principle:** Treat a precise specification as the stable source of truth and let AI agents generate (and regenerate) code from it. For business applications, the most durable spec is a *system use case*, not a user story or PRD.

**Why:** AI can rewrite code cheaply, so code becomes disposable while requirements endure. If your real intent lives only in code or scattered stories, you get drift between what the system does and what anyone documented, and the AI has nothing solid to regenerate against. A good spec also constrains the agent enough to produce architecture you actually want.

**How to apply:**
- **Adopt the AI Unified Process:** a process-centric, spec-driven loop where system use cases are the central, stable artifact and code is generated from them by AI agents fitted with skills, MCP servers, and architectural guardrails.
- **Write system use cases, not user stories.** Structure each as: Actor, Preconditions, Main success scenario, Alternative flows, Postconditions (acceptance criteria), plus an API section when relevant. A single user story is usually just one flow inside a use case, so use cases keep the whole behavior together.
- **Keep a domain/entity model alongside the use cases** so the agent understands the data, not just the steps.
- **Pick an AI-friendly architecture.** Martinelli favors *self-contained systems* over microservices or a modular monolith, because the architecture style directly shapes how well coding agents perform.
- **Equip the agent:** Skills matched to your tech stack; MCP servers to serve large in-house framework documentation; guardrails (architecture docs, coding guidelines) kept deliberately small.
- **Tie review intensity to module risk** — review the dangerous parts hard, the trivial parts lightly.
- **Restructure the team:** smaller teams, continuous flow, drop the two-week sprint cadence.
- **Manage drift** by regenerating from the spec rather than patching code and letting docs rot.

Scope note: Martinelli scopes this to business applications, not products/tools. See also `evals` and skills/MCP setup.

**Source:** Simon Martinelli — "Lessons from Spec-driven Development", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-martinelli-spec-driven-development/SKILL.md)
