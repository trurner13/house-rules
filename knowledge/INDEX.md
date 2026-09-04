# Knowledge index

All distilled best-practice notes, by topic. The universal ones are lifted into
[rules/RULES.md](../rules/RULES.md) (always-on). Seeded from **AI Native DevCon
London, June 2026** (31 talks via the Tessl registry) plus ongoing notes.

## Prompting & context
- [context-engineering-and-memory](prompting/context-engineering-and-memory.md) — the CLAUDE.md → memory tools → Skills → filesystem → "dreaming" progression, and the four production principles (versioning, concurrency, permissioning, portability).
- [interaction-style](prompting/interaction-style.md) — standing preferences for how any AI works with us: no sycophancy, clarify vague prompts.
- [sloan-product-design-context](prompting/sloan-product-design-context.md) — the context agents need lives in Figma/Linear/Notion; distil it to skill-sized, eval it, flow effort back to PMs.

## Evals & testing
- [testing-ai-written-code](evals/testing-ai-written-code.md) — tests are the contract the agent can't renegotiate: spec-derived tests, the four ways an agent fakes green, the layered stack.

## Agents & tools
- [adversarial-review](agents/adversarial-review.md) — how to actually run the reviewer: independent context, base branch not diff, structured verdicts, refutation pass, hard gate.
- [agent-readable-logging](agents/agent-readable-logging.md) — logs and errors written for an agent to parse and act on first, not human prose.
- [lawson-agent-experience](agents/lawson-agent-experience.md) — design for Agent Experience (AX): surfaces, errors, and feedback loops agents can actually operate.
- [luebken-embedding-pi-coding-agent](agents/luebken-embedding-pi-coding-agent.md) — embed a coding agent into a product via four primitives (setup, tools, extensions, sessions).
- [maple-harness-engineering](agents/maple-harness-engineering.md) — harness engineering: make "good" legible to agents and surface guardrails just-in-time.
- [marsden-agent-desktops](agents/marsden-agent-desktops.md) — give every agent its own desktop; a seven-dimension design space for server-side agents.

## RAG & data
- [douglas-training-ai-on-your-own-code](rag/douglas-training-ai-on-your-own-code.md) — capture agent sessions via a telemetry proxy and fine-tune small local models (QLoRA, SFT vs DPO).

## Skills
- [moss-skills-team-workflow](skills/moss-skills-team-workflow.md) — manage team skills with software discipline (decompose, version, review, register, eval).
- [podjarny-skills-are-the-new-code](skills/podjarny-skills-are-the-new-code.md) — the five engineering disciplines for skills: static analysis, evals, security testing, dependency management, observability.

## MCP & protocols
- [firtman-web-mcp-agentic-web](mcp/firtman-web-mcp-agentic-web.md) — Web MCP: give agents typed, named frontend tools (a contract) instead of pixel-guessing.

## Security
- [agent-guardrail-failures-2026](security/agent-guardrail-failures-2026.md) — what GuardFall, IssueTrojanBench, Friendly Fire and the skills supply chain proved: inspection-based guardrails don't hold; only boundary controls do.
- [katsioloudes-code-security-ai](security/katsioloudes-code-security-ai.md) — AI as a reasoning layer on deterministic detection; least-privilege, dual-LLM checks, human-in-the-loop.
- [tal-skills-security](security/tal-skills-security.md) — treat skills as untrusted supply chain; review like NPM deps; watch the lethal trifecta.

## Stacks
- [cloudflare-supabase-posthog](stacks/cloudflare-supabase-posthog.md) — the trifecta assembles across these three services; per-vendor lockdown settings, RLS defaults, destructive-migration guards, deploy gates.

## Ways of working
- [batey-building-product-teams-age-of-ai](ways-of-working/batey-building-product-teams-age-of-ai.md) — AI-era product teams: ADR-first, tiny adoption-bound squads, one complex task at a time.
- [debois-agent-enablement](ways-of-working/debois-agent-enablement.md) — build a dedicated Agent Enablement function; fix the system, not the code.
- [dns-in-code-not-registrar](ways-of-working/dns-in-code-not-registrar.md) — the registrar only delegates nameservers; every record lives in a managed zone, changed reviewably.
- [farley-vibe-coding-best-we-can-do](ways-of-working/farley-vibe-coding-best-we-can-do.md) — treat the AI like a compiler: executable specs, verification, small increments.
- [findings-to-guardrails](ways-of-working/findings-to-guardrails.md) — the reinforcement loop: every finding becomes a permanent enforced check, so the same class of bug can't return.
- [jones-odevo-ai-native-transformation](ways-of-working/jones-odevo-ai-native-transformation.md) — earn the right to roll out agentic coding: fundamentals → discovery → pilot → train-the-trainer.
- [jourdan-pipelines-to-prompts](ways-of-working/jourdan-pipelines-to-prompts.md) — closed feedback loops and harness engineering before granting agent autonomy.
- [maleix-collective-intelligence](ways-of-working/maleix-collective-intelligence.md) — turn agents' attributed mistakes into reusable team knowledge (three-act workflow).
- [martinelli-spec-driven-development](ways-of-working/martinelli-spec-driven-development.md) — the AI Unified Process: keep use cases as the stable spec, regenerate code from them.
- [measuring-ai-adoption](ways-of-working/measuring-ai-adoption.md) — the adopted metric: merge rate and zero-follow-up share; which vanity metrics to demote (three talks).
- [session-handover-and-work-state](ways-of-working/session-handover-and-work-state.md) — a session is not a unit of storage: checkpoint the branch, capture the intent, and make the *next* session's start the gate.
- [stack-humans-architect-ai-writes-code](ways-of-working/stack-humans-architect-ai-writes-code.md) — humans own intent and constraints; agents write all code; five merge gates.
- [syme-continuous-ai](ways-of-working/syme-continuous-ai.md) — Continuous AI as a third pillar beside CI/CD: recurring, sandboxed agent jobs that emit to one narrow safe channel.
