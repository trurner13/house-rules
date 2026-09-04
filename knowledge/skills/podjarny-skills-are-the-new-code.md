# Treat Skills as Code — apply real engineering rigour to them

**Principle:** A "skill" (a reusable unit of capability you hand an AI agent) is now the primary thing you author in the agentic stack, so it deserves the same engineering discipline you'd apply to production code — not treated as a throwaway prompt.

**Why:** Skills are quietly becoming the new source of truth: they encode how work gets done, get reused across agents, and ship to users. If you author them casually — no testing, no security checks, no versioning — they rot, drift, leak, and fail silently, the same way unmanaged code does. The shift is that you increasingly maintain skills rather than hand-write the code; if you don't engineer the skills, you have no quality floor.

**How to apply:**

- **Adopt the five engineering disciplines for skills.** For every skill of consequence, ask whether you have the equivalent of each practice you'd expect for code:
  1. **Static analysis** — lint/check the skill's structure and instructions before it runs, not after it breaks.
  2. **Evals** — measure whether the skill actually produces the intended outcome; treat this as the regression test suite for the skill. See `evals`.
  3. **Security testing** — probe for prompt injection, data leakage, and unsafe actions the skill could be coaxed into.
  4. **Dependency management** — know what files, tools, and other skills it relies on, and version them; a skill with a missing bundled file should fail loudly.
  5. **Observability** — log and monitor skills in production so you can see how they actually behave and catch drift.
- **Frame work around the agentic development stack.** Recognise skills as a distinct layer above the model and harness, and manage them as a first-class asset (authored, reviewed, owned), not an inline afterthought.
- **Use the three challenge buckets** to triage where a skill is weak — sort issues into authoring quality, management/lifecycle, and quality scoring — then invest where the gap is biggest.
- **Score skill quality** explicitly so "good skill" isn't a vibe; make it a number you can track over time.

**Source:** Guy Podjarny — "Skills are the new Code", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-podjarny-skills-are-the-new-code/SKILL.md)
