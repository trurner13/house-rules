# Use AI to close the security gap, but pair it with deterministic tooling and humans

**Principle:** AI is leverage for the 1-security-specialist-per-100-developers gap, but it only helps if you treat it as a reasoning layer on top of deterministic detection, kept inside least-privilege boundaries, with a human in the loop — never as a replacement for security testing.

**Why:** There are roughly 100 developers for every application security specialist, so security cannot scale by hiring. AI can close that gap or widen it. AI alone hallucinates, is non-deterministic, and gives different answers on different runs, so leaning on it as your sole security tool produces false confidence and misses real vulnerabilities. Deterministic tooling plus good scaffolding plus tight permissions is what makes AI trustworthy enough to use.

**How to apply:**

- **Start left, not just shift left.** Don't merely move security checks earlier in an existing pipeline — design security into the work from the very first prompt and scaffold, so AI-assisted code is born safer.
- **Cover the five areas where AI helps security:** (1) writing safer code, (2) MCP servers + skills + agentic workflows, (3) supply-chain decisions, (4) remediating alerts faster in the PR, (5) developer security education. Audit your own setup area by area and mark each covered / partial / missing.
- **AI as the reasoning layer on deterministic detection.** Let scanners (SAST and similar) do the finding; let AI explain, prioritise, and fix. Treat it as a "fixing problem, not a detection problem."
- **Use dual-LLM / LLM-as-judge ("LLM jury")** to cross-check AI security output rather than trusting a single pass, given non-determinism.
- **Enforce least-privilege boundaries** on MCP servers, skills, and agents so an agent can't reach beyond its task.
- **Reuse free templates** instead of inventing: gh.io/sk (supply-chain instruction files), gh.io/scg (hands-on training playground), gh.io/taskflows (vulnerability-finding task flows).
- **Educate via security SLOs** — set measurable security objectives for dev teams rather than one-off training.
- Keep a human in the loop; AI changes the scene but does not replace security testing. Relates to `evals`.

**Source:** Joseph Katsioloudes — "Code Security Reinvented: Navigating the era of AI", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-katsioloudes-code-security-ai/SKILL.md)
