# Design for Agent Experience (AX), not just Developer Experience

**Principle:** When agents start driving your platform, every assumption that "a human is watching" becomes friction. Redesign your surfaces, signals, and feedback loops so an agent can operate them — and you make the product better for humans too.

**Why:** Tools built for humans assume someone reads the logs, eyeballs the preview, and answers the y/n prompt. Agents can't do any of that. The "AX paradox" is that fixing these things for agents doesn't trade off against human experience — it improves it for everyone, because code is no longer scarce; taste and judgment are. If your platform isn't legible and operable by an agent, agent-driven work stalls or fails silently.

**How to apply:**
- **Make three architectural shifts:**
  - *APIs → capabilities.* Expose high-level outcomes an agent can request ("deploy this"), not low-level request/response plumbing it has to orchestrate.
  - *Request/response → event-driven.* Let agents react to events rather than poll and block, so autonomous loops can run without a human pacing them.
  - *Make everything legible to agents.* Surfaces, errors, and state should be machine-readable, not just human-pretty.
- **Apply three trust principles** before letting agents act autonomously: run work in a **sandbox**, keep **human-in-the-loop by default**, and guarantee **audit + rollback** so any agent action can be traced and undone. (See `security`.)
- **Fix the concrete surfaces:** emit **structured, machine-readable error codes alongside the human text**; give **deploy previews explicit signals** an agent can parse; **redesign CLIs away from interactive y/n prompts** toward flags/output an agent can drive.
- **Package reusable knowledge as "blueprints":** skills, recipes, context, and architecture decision records (ADRs) the agent can pull from — your software "factory." (See `skills`.)

**Source:** Dana Lawson — "Built for Humans. Now Agents Are Here.", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-lawson-agent-experience/SKILL.md)
