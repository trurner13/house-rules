# Cloudflare + Supabase + PostHog, with agents

**Principle:** These three connected to one agent assemble the lethal trifecta **across
services** — PostHog ingests untrusted content, Supabase holds the private data,
Cloudflare is the outbound channel. No single MCP server looks dangerous on its own,
which is exactly why this arrangement is harder to spot than the single-tool version.
Scope each connection down in its config, and keep production writes behind a gate.

**Why:** All three vendors ship an MCP server, all three default to more access than
the work needs, and there are two documented real-world incidents on almost exactly
this setup. The good news is that all three also ship real lockdown controls — they
just aren't the defaults.

## Supabase — the highest-risk of the three

The MCP server connects with credentials that **bypass Row Level Security by design**.
The documented breach on this pattern: an attacker filed a support ticket containing
hidden instructions; the agent read the ticket as part of its context, ran
`SELECT * FROM integration_tokens`, and wrote the results back into the ticket thread
where the attacker could read them. Private data, untrusted content and an outbound
channel, all three legs inside one tool. A textbook confused deputy — root access, no
sense of data versus commands.

**Lock the connection down.** Supabase's own documented options:

| Option | Effect |
|---|---|
| `read_only=true` | Runs queries as a restricted Postgres user |
| `project_ref=<id>` | Scopes to one project instead of the whole organisation |
| `features=database,docs` | Disables tool groups you don't need |

Plus: connect to a **development project, not production**, and use branching for
anything that needs to look like real data.

**What agents specifically get wrong on Supabase**, per Supabase's own writeup:

- **RLS is off by default** for tables created via SQL, migrations or AI tools. The
  Table Editor enables it; the path an agent takes doesn't. This is where the real
  leaks come from — an agent scaffolds five tables and never runs
  `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.
- Views without `security_invoker = true` silently bypass RLS.
- Agents authorise on `user_metadata`, which **users can edit**. Authorisation belongs
  in `app_metadata`.
- Deleting a user doesn't invalidate their JWT — revoke sessions first.
- Storage upserts fail silently without INSERT + SELECT + UPDATE permissions.
- Agents hallucinate CLI commands that don't exist (`supabase db execute`) and work
  from training data months out of date rather than reading the docs.

Supabase publishes official skills for all of this:
`claude plugin marketplace add supabase/agent-skills`. Install on day one.

**The destructive-migration guard.** There is a July 2026 incident in which an agent
pointed at a live Supabase instance ran a Prisma migration with `--shadow-database-url`
aimed at production; Prisma resets the shadow database by design, and every table came
back empty. *(Second-hand account — treat the specifics as indicative.)* The guard is
worth having regardless: block `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`,
`prisma migrate reset`, `prisma db push --force-reset`, and any command carrying a
shadow-database URL. Keep production credentials out of every file the agent can read —
dev URL in agent-visible config, production in the hosting platform's environment.

## Cloudflare — blast radius, not exfiltration

Cloudflare publishes official Claude Code setup: `claude plugin marketplace add
cloudflare/skills`, then `/plugin install cloudflare@cloudflare`. Two things from it
matter — run Claude from the project root where `wrangler.jsonc` lives, because that's
how it reads your bindings, and **enable their documentation MCP server** so the agent
stops working from stale training data.

The risk here is different: `wrangler deploy` goes **straight to production**. There is
no staging step by default. By our own reversibility test that's an irreversible
outbound action and needs a gate.

**Tokens.** Never the Global API Key — it can't be scoped and can't be cleanly revoked
without rotating it everywhere. Use a custom token with just "Edit Cloudflare Workers",
scoped to the one account. Keep the CI token separate from your personal one, so a
leaked pipeline secret means redeploy access rather than the whole account. OIDC /
trusted publishing for Wrangler is under discussion upstream but not shipped.

**Correctness gotchas agents reliably hit on Workers**, from Cloudflare's own
best-practices skill:

- Floating promises silently drop work — every promise awaited, returned, voided, or
  handed to `ctx.waitUntil()`.
- Buffering with `await response.text()` instead of streaming blows the 128 MB limit.
- Module-level mutable globals leak state across requests.
- Secrets hardcoded in `wrangler.jsonc` instead of `wrangler secret put`.
- Hand-written `Env` interfaces drift from actual bindings — run `wrangler types`.
- `Math.random()` used for security-critical values instead of `crypto.randomUUID()`.
- Stale `compatibility_date`; REST API calls where a native binding exists.

## PostHog — lowest risk, best-designed for agents

Genuinely good lockdown controls, all documented:

- `mode=read-only` (or the `x-posthog-mcp-mode` header) excludes every create, update
  and delete tool.
- `x-posthog-organization-id` / `x-posthog-project-id` pin the session — and pinning
  **automatically removes** the switch-organization and switch-project tools.
- `feature_categories` / `tool_names` filter down to just the tools you need.
- Personal API keys are scopable, with an MCP Server preset that scopes to one project.

**The one thing to gate: feature flags are a production write.** An agent that can flip
a flag changes production behaviour with no deploy, no diff and no review. That must
not sit inside whatever exceptions you carve out of read-only mode.

PostHog's [golden rules of agent-first product engineering](https://posthog.com/newsletter/agent-first-product-engineering)
is also a good design note for the product itself — particularly "meet agents at their
level of abstraction" (expose a semantic layer, not UI-shaped endpoints) and
"front-load universal context".

## Where the three combine

- **Pooling.** Reaching Supabase from Workers via Hyperdrive: use Supabase's **Direct
  connection string**, not the Supavisor pooled one. Hyperdrive does its own pooling and
  double-pooling breaks it.
- **Context cost.** Three MCP servers is three tool sets loaded every session. PostHog's
  own guidance: most startups land on 3–9 servers; start with two or three and add on
  evidence, not on availability.
- **The trifecta across services.** Worth restating because it's the whole reason this
  note exists. Run the lethal-trifecta check over the agent's *entire* connected tool
  set. Untrusted content arrives through analytics — support tickets, error messages,
  event properties, session recordings — not just through the code you're reviewing.

**Related:** [agent-guardrail-failures-2026](../security/agent-guardrail-failures-2026.md)
(the same failure modes, generally), [tal-skills-security](../security/tal-skills-security.md)
(the trifecta), and the drop-in rules file at
[templates/stack-cloudflare-supabase-posthog.md](../../templates/stack-cloudflare-supabase-posthog.md).

**Source:** Researched August 2026. Primary: Supabase MCP docs and the Supabase
"agent skills" blog post, Cloudflare's `agent-setup/claude-code` docs and Hyperdrive →
Supabase guide, PostHog's MCP FAQ and API-key docs. Secondary, verify before relying on
specifics: the Supabase MCP support-ticket breach (originally General Analysis; read via
[Pomerium's writeup](https://www.pomerium.com/blog/when-ai-has-root-lessons-from-the-supabase-mcp-data-leak))
and the July 2026 Prisma shadow-database wipe.
