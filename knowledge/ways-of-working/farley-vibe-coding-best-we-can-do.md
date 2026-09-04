# Treat the AI like a compiler, not a wish-granting genie

**Principle:** Natural-language "vibe coding" alone is too weak to build reliable software. Drive AI agents the way you'd drive a compiler — with precise, executable specifications and an automated way to verify the output — rather than vague chat prompts.

**Why:** Real programming languages have three properties that plain English lacks: a simple consistent grammar, unambiguous expression of intent, and repeatable deterministic execution. AI coding speeds up the *easy* part (writing code) while making the *hard* parts worse. It creates three new problems: it's hard to specify precisely what you want, hard to verify you got it, and it breaks your ability to work in small safe increments. Vague prompts produce plausible-looking code you can't trust.

**How to apply:**
- **Check your tool against the three properties.** When you describe what you want, is your intent unambiguous? Is there a consistent structure? Will the same request give a repeatable result? Plain prose fails all three — tighten it.
- **Watch for the three AI-introduced problems** and design around each: (1) *precise specification* — write down exactly what "done" means; (2) *verification* — have an automated check that proves it; (3) *incrementalism* — make one small, testable change at a time, not a giant generated lump.
- **Prompt with BDD-style executable specifications.** Work top-down: vision → user story → concrete worked examples → executable specs. Give the AI examples it can be measured against, not adjectives.
- **Use a problem-specific DSL.** A small, structured "language" for your domain removes ambiguity that free text leaves open.
- **Verify with a deployment pipeline.** Continuous-delivery practices — automated tests and a real build/deploy gate — are how you confirm AI output actually works.
- **Be skeptical of AI writing its own tests** to grade its own code; that's circular. Anchor tests in human-specified examples.

This is continuous delivery applied to AI-driven development: specify clearly, verify automatically, move in small steps. See also `evals`.

**Source:** Dave Farley — "Vibe Coding — Is this really the best we can do?", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-farley-vibe-coding-best-we-can-do/SKILL.md)
