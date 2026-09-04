# Product/design context is first-class agent context

Adopted as a rule. From Marc Sloan's AI Native DevCon London 2026 talk, "Harness
engineering beyond code" (auto-caption source — gist verified, product names treated
as uncertain).

## The thesis

Our context rules are code-centric, but much of what an agent needs to do the *right*
thing lives **outside the codebase**: design systems, accessibility rules, brand
guidelines, product intent, and "why we decided **not** to build this." It sits in
Figma, Linear, Notion, CRMs. Agents that can't see it pick the wrong component or
rebuild something that was deliberately rejected.

## What to do

- **Treat external context as part of the harness**, not an afterthought.
- **Connect design components to their code components** (e.g. Storybook docs, Figma
  Code Connect) so the agent uses the *right* existing component, not a generic one.
- **Distil it to skill-sized, signal-over-noise, then eval it** — the same
  context-engineering discipline we apply to code context. Don't dump a whole design
  system into context; shrink it and confirm with evals that it helps rather than
  overwhelms. (Extends the adopted "lean grounding map" + "skills ship with evals".)
- **Make it a maintained, owned connection** — code↔design/product sync needs a
  dedicated owner and will never be perfectly in sync; accept some drift deliberately.
- **Bidirectional, not just code-ward**: flow technical-effort / tech-debt context
  *back* to PMs and designers so they can decide when **not** to build something —
  "just as valuable to know when not to build."
- When wiring agents to external tools via **MCP**, mind the caveats: rate limits,
  cost, third-party availability, and the lack of a canonical source of truth.

## Source

- `transcripts/talks/sloan-harness-engineering-beyond-code.txt`
