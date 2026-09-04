# Expose web app capabilities to agents with Web MCP

**Principle:** Instead of letting AI agents guess their way around your web app by reading pixels or scraping HTML, give them an explicit contract: named, typed tools your frontend declares so the agent calls a function instead of inferring what to click.

**Why:** Today's ways of letting agents use the web (HTTP fetch, browser-use plugins, computer use, screenshot inference) are slow, burn tokens, and break easily because the agent is guessing from images or raw markup. Firtman's framing: Web MCP moves you "from inference to a contract that we as web developers define." A typed tool that already lives in the browser has the full client context (DOM, forms, sensors, session, client-side APIs) the agent otherwise has to reconstruct unreliably.

**How to apply:**
- **Adoption recipe (start small):** pick ONE high-value page state, expose a single read-only diagnostic tool for it, evaluate how the agent calls it (the calls and arguments it sends), then automate testing today via Chrome DevTools MCP or Puppeteer as a bridge. Don't try to wrap the whole app at once.
- **Tool anatomy (imperative API):** each tool is an object with `name`, `description` (write it FOR the agent consumer, not a human dev), `inputSchema` (a JSON schema), and an `execute` async function.
- **Declarative (form-based) API:** for forms, annotate with a `tool` name, `tool description`, optional `tool auto submit`, and a per-field `tool param description` where the visible label isn't enough on its own.
- **Tool design rules:** one purpose per tool; register tools based on the current page state (only offer what's actually available now); use plain language; return meaningful errors; keep outputs small to protect the agent's context budget.
- **Status / timeline:** Web MCP is a proposed W3C standard entering a Chrome 149 origin trial. Treat it as emerging — prototype now with the bridge tools, design tools so they're ready when native support lands.
- Mental model Firtman uses: "Web MCP is to MCP as JavaScript is to Java" — related in name, different in scope. Web MCP exposes frontend capability; it is not the same as standing up an MCP server.

Keeping tool outputs small ties directly to `context-engineering`; evaluating the agent's actual calls/arguments is a small `evals` loop.

**Source:** Maximiliano Firtman — "Web MCP and the Agentic Web", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-firtman-web-mcp-agentic-web/SKILL.md)
