# Triage conventions

How an agent classifies an incoming issue/request **before** planning.

1. **Restate the intent** in one line; identify the type (bug / feature / chore / question).
2. **Gather context** — read the relevant code, design docs, and any prior incidents/decisions before deciding anything.
3. **Decide routing:**
   - Worth doing now? Or decline/defer (note why)?
   - Well-specified → proceed to a plan.
   - Ambiguous or strategic → route to a written plan/PRD for human shaping first.
   - Needs a human judgement (risk, strategy, cost) → flag it.
4. **Output a short findings summary** the planner can act on (what it is, what's involved, open questions).
5. **File everything you found but aren't doing.** Every issue surfaced during triage gets its own entry in the tracker *before* you move on — the one you pursue is not the only one that mattered. Anything left only in the conversation is gone at the end of the session. See [issue-tracker.md](issue-tracker.md); the capture form is seven lines.
