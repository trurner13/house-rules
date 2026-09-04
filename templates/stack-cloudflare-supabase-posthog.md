<!-- Drop-in path-scoped rules for a Cloudflare Workers + Supabase + PostHog project.
     Copy to <your-repo>/.claude/rules/10-stack.md — Claude Code auto-loads
     .claude/rules/*.md every session, alongside the vendored 00-guardrails.md.
     Evidence and reasoning: knowledge/stacks/cloudflare-supabase-posthog.md.
     Delete the sections for services this repo doesn't actually use. -->

# Stack guardrails — Cloudflare, Supabase, PostHog

These are hard rules for this stack. They sit on top of the shared guardrails in
`00-guardrails.md`, and they win where they're more specific.

## The whole-stack rule

- **Run the lethal-trifecta check over every connected tool at once.** PostHog ingests
  untrusted content (support tickets, error messages, event properties, session
  recordings), Supabase holds the private data, Cloudflare is the outbound channel. No
  single server looks dangerous alone; together they are the trifecta. If all three are
  connected in one session, one leg must be read-only.
- **Never connect an agent to production data and a production deploy path in the same
  session.** Split the work, or split the credentials.

## Supabase

- **Never use the service-role key in anything the agent can read.** It bypasses Row
  Level Security by design. Agent-visible config carries the development database URL
  only; staging and production credentials live in the hosting platform's environment.
- **Scope the MCP connection.** `read_only=true`, `project_ref=<one project>`,
  `features=<only what's needed>`. Development project, not production. Use branching
  for realistic data.
- **Enable RLS explicitly on every new table.** It is *off* by default for tables
  created via SQL, migrations or an agent — only the Table Editor turns it on. Every
  migration that creates a table also runs `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.
- **No permissive placeholder policies.** `USING (true)` satisfies the linter and
  protects nothing. Write the real policy or leave the table unexposed.
- **Views need `security_invoker = true`**, or they silently bypass RLS.
- **Authorise on `app_metadata`, never `user_metadata`** — users can edit the latter.
- **Revoke sessions before deleting a user.** Deleting the user does not invalidate
  their JWT.
- **Run the Supabase Security Advisor as a gate**, not as a thing to look at sometimes.
- **Destructive SQL and migrations are blocked, not prompted.** `DROP TABLE`,
  `DROP DATABASE`, `TRUNCATE`, `prisma migrate reset`, `prisma db push --force-reset`,
  and any command carrying a `--shadow-database-url`. A shadow-database URL pointing at
  production has already wiped one real database.
- **Install the official skills:** `claude plugin marketplace add supabase/agent-skills`.

## Cloudflare

- **`wrangler deploy` is a production write.** It is irreversible and it needs a human
  gate every time. There is no staging step by default — if this repo needs one, build
  it before the first deploy.
- **Never the Global API Key.** Custom token, "Edit Cloudflare Workers" only, scoped to
  one account. The CI token is separate from any personal token.
- **Secrets go in `wrangler secret put`**, never in `wrangler.jsonc` or source.
- **Every promise is awaited, returned, voided, or passed to `ctx.waitUntil()`.** Bare
  `fetch()` silently drops work and swallows errors.
- **Stream large or unknown payloads.** `await response.text()` on an unbounded body
  hits the 128 MB memory limit.
- **No module-level mutable state.** Globals leak across requests.
- **Run `wrangler types`** — hand-written `Env` interfaces drift from real bindings.
- **Use native bindings (KV, R2, D1, Queues), not the Cloudflare REST API**, from inside
  a Worker.
- **`crypto.randomUUID()` for anything security-relevant**, never `Math.random()`.
- **Keep `compatibility_date` current** on new projects and review it periodically.
- **Enable Cloudflare's documentation MCP server** so the agent stops answering from
  stale training data. Run Claude from the directory holding `wrangler.jsonc`.

## PostHog

- **Connect read-only and pinned by default:** `mode=read-only`, plus
  `x-posthog-organization-id` and `x-posthog-project-id`. Pinning also removes the
  organisation- and project-switching tools.
- **Filter the tool set** with `feature_categories` / `tool_names` — load what this repo
  actually uses, not the catalogue.
- **Feature flags are a production write.** Flipping a flag changes production behaviour
  with no deploy, no diff and no review. Never inside an agent's autonomous scope.
- **Personal API keys are scoped keys.** Use the MCP Server preset, scoped to one
  project. Never in frontend code.

## Integration notes

- **Hyperdrive → Supabase: use the Direct connection string**, not the Supavisor pooled
  one. Hyperdrive pools already; double-pooling breaks connections.
- **Keep the MCP server count down.** Three servers is three tool sets in context every
  session. Add a fourth only against a concrete use case.
