# Embedding a coding agent into your product with four primitives

**Principle:** The "magic" of a Codex-style coding agent isn't unique to coding — you can reproduce it inside ordinary business software by composing four primitives (agent setup, tools, extensions, sessions) into the right interaction pattern.

**Why:** Teams often assume an embedded agent has to be either a rigid scripted workflow or a wide-open chatbot. Treating the agent as a set of reusable building blocks lets you dial in exactly the openness and the guardrails your product needs, instead of bolting an LLM onto a feature and hoping for the best.

**How to apply:**

- **Start from the four primitives.** Every embedded agent is built from: (1) *agent setup* — the base instructions/prompts that define who the agent is; (2) *tools* — the actions it can take (e.g. read CRM, draft an email); (3) *extensions* — lifecycle hooks that fire around the agent's behaviour; (4) *sessions* — the running record of what happened.
- **Pick one of three patterns** for how the user meets the agent: *workflow* (streamlined, the agent runs a mostly fixed path), *chat* (an embedded power-user conversation), or *malleable software* (the user can reshape the tool itself — the Ink & Switch idea).
- **Design tools so the agent never has to guess.** Make tool definitions *intent-revealing* and *scoped to the specific task*. Deliberately limit capability: in the after-sales demo the "draft email" tool literally cannot send — drafting and sending are separate.
- **Use extensions (lifecycle hooks) as guardrails, not as cages.** Hook the *tool-call* / *tool-result* boundary to enforce rules (e.g. replies must stay in the customer's own domain) without scripting the agent's open-ended reasoning. Extensions are just TypeScript plus a short markdown summary — cheap to add. This is the "radical extensibility" idea.
- **Treat the session as an event-log tree** — an auditable record you can inspect, branch, and replay.
- **Isolate state per entity:** the demo runs one agent per customer, grounded in real CRM/ERP tool calls rather than guesswork.

See also `agent-tool-design`, `guardrails-for-llm-output`.

**Source:** Matthias Lübken — "A Piece of PI – Embedding The OpenClaw Coding Agent In Your Product", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-luebken-embedding-pi-coding-agent/SKILL.md)
