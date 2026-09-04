# Turn agent mistakes into team knowledge that compounds

**Principle:** Coding agents learn something every session, but those lessons die in closed chat windows. Capture each correction as an attributed, reusable artifact so the whole team's agents get smarter over time instead of repeating the same mistakes.

**Why:** Without a capture loop, every agent rediscovers the same bugs from scratch and the rationale behind fixes evaporates. Knowledge decays into private chat history. Attribution matters because lessons you can trace back to a real incident (and a real author) are trusted, auditable, and worth reusing — anonymous rules get ignored.

**How to apply:**

Run the three-act workflow Edouard Maleix describes:

- **Act 1 — Identity & Diary.** Give each coding agent its own identity and make it sign its commits, so every change is attributable to a specific agent (and human). As work happens, the agent records *why* it did things in a "diary" made of discrete **entries** — small, linked notes capturing the rationale behind a decision or a fix, not just the final code.
- **Act 2 — Pack, Curation & Render.** Don't dump raw entries on the team. Curate related entries into thematic **packs**, then **render** each pack into an agent-readable skill. Two constraints to honour: preserve attribution (source incident + human + agent identifier flows through to the rendered skill), and respect a token budget when rendering so the skill stays lean enough to load. A pack is the unit you review; a rendered skill is what agents actually consume. (See `skills-authoring`.)
- **Act 3 — Evals & Autonomy.** Before trusting a pack, run two evals with binary (pass/fail) criteria: a **fidelity eval** (does the rendered skill faithfully represent the original lesson?) and a **usefulness eval** (does it actually help on real tasks?). Only then move toward more autonomy — eventually "voluntary task picking," where specialised agents pick up work themselves.

Audit yourself by walking all three dimensions in order — Identity & Diary, Pack/Curation/Render, Evals & Autonomy — and mark each as covered, partial, or missing. The value is in completeness; don't skip the weak ones. This is "compound engineering": each attributed mistake becomes durable collective intelligence. (See `evals-binary-criteria`.)

**Source:** Edouard Maleix — "How AI-First Dev Teams Build Collective Intelligence — One Attributed Mistake at a Time", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-maleix-collective-intelligence/SKILL.md)
