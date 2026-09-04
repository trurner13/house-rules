# Logging is for the agent, not the human

**Principle:** In our APIs and front-ends (existing and future), logs and errors
are written to be read and acted on by an **AI agent first**, not a human.
Structured and machine-parseable, not human prose.

**Why:** Our repos are AI-first — agents diagnose and fix. An agent can't reliably
act on free-text logs ("something went wrong in checkout"); it can act on
structured records with explicit error codes, identifiers, and remediation
pointers. Designing logs for the agent is what lets it parse a failure, find the
cause, and fix it autonomously. (Echoes Dana Lawson's machine-readable error codes
that also helped humans, and Ryan Lopopolo's errors that name the failure and link
a runbook.)

**How to apply:**
- Emit **structured logs** (e.g. JSON), not free text — stable, queryable fields.
- Give every error a **machine-readable code/type**, not just a message.
- Include the **context an agent needs** to act: the operation, key inputs/IDs,
  expected vs actual, and a pointer to remediation (a runbook, the relevant
  guardrail, or the fix).
- Treat the **agent as the consumer** ("your customer is the agent") — optimise
  field names and structure for an LLM to parse, not for log-line readability.
- Human-readable text can ride alongside, but it's secondary; never *only* prose.

**Source:** our standing standard (2026-06-02), informed by Dana Lawson
(Netlify) and Ryan Lopopolo (OpenAI) at AI Native DevCon London 2026.
