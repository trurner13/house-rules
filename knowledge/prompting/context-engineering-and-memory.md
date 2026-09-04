# Context engineering & agent memory (the CLAUDE.md → dreaming progression)

**Principle:** Treat what the model sees as a deliberately engineered, layered
system — not one big prompt. Memory should live as versioned markdown files the
agent reads on demand, and be curated over time rather than dumped in wholesale.

**Why:** Stuffing everything into context is expensive and degrades quality.
Anthropic's year of evolution went through distinct stages, each solving a limit
of the last:

1. **`CLAUDE.md` files** — static, always-loaded project instructions.
2. **Memory tools** — let the agent read/write memory during a task (in-band).
3. **Skills** — packaged, on-demand capabilities loaded only when relevant
   (the "bookshelf" analogy: you don't read every book, you pull the one you need).
4. **Filesystem-as-memory** — a directory of markdown files the agent navigates,
   so context stays lean and only relevant slices load.
5. **"Dreaming"** — an *out-of-band, asynchronous* process that reviews past
   agent transcripts, spots cross-session patterns, and proposes changes to the
   memory store (the "school/teacher" analogy: learning happens after the day,
   not mid-task).

**How to apply:**
- Use **progressive disclosure**: keep always-on context tiny; push detail into
  on-demand files/skills the agent loads only when the topic is live. *(This is
  exactly the two-layer design of this repo — see `../../rules/RULES.md` vs
  `knowledge/`.)*
- Distinguish **in-band** memory (written during a task) from **out-of-band**
  curation (reviewing transcripts later to improve the store). Don't rely on the
  agent to perfectly curate its own memory mid-task.
- When you build a memory/agent system to scale beyond one agent and session,
  enforce the **four production principles**:
  - **Versioning** — memory changes are tracked, reviewable, revertible.
  - **Concurrency** — handle simultaneous writes safely (e.g. hashing) so two
    agents don't clobber each other.
  - **Permissioning** — control who/what can read or modify which memory.
  - **Portability** — memory isn't locked to one tool/agent; it can move.
- Audit an existing memory/agent setup by walking **all** four principles plus
  the five stages in order — the value is in completeness, not cherry-picking.

**Source:** Lamis (Anthropic, Applied AI team) — "Context Engineering, Memory
Systems, and Dreaming", AI Native DevCon London, June 2026.
[Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-lamis-context-engineering-dreaming/SKILL.md)
