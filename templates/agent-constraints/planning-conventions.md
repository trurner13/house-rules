# Planning conventions

How an agent writes the plan/spec **before** implementing (spec-first).

- State the **goal** and concrete **"done" criteria** — with examples/tests where possible.
- **Requirements: who asked.** List each requirement with who asked for it: a named person, the spec, a test or a rule. Mark any requirement the agent added itself; it is cut unless the human keeps it.
- **What we cut.** List the parts, steps, options and dependencies the plan deliberately leaves out. Simplify only what survived, and automate last ([question-delete-simplify](../../knowledge/ways-of-working/question-delete-simplify.md)). A small single-requirement fix skips both lists.
- List the **files/interfaces involved** and what's **out of scope**. Keep the blast radius small.
- Include **non-functional needs** (performance, security) explicitly — the model can't infer how secure/fast this should be.
- Note any **design-doc or skill updates** the change requires (see the Documentation dimension).
- Run the plan through the **adversarial reviewer** ([adversarial-dimensions.md](adversarial-dimensions.md)), capped at ~5 rounds, then escalate to a human.
- A **human approves the plan** before implementation begins. (Control is upstream, at the plan — not at the merge.)
