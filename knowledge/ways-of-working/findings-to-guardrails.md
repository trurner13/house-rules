# Turning findings into guardrails (the reinforcement loop)

**Principle:** Every finding — a failed test, an adversarial review hit, a production
error, a correction you had to give twice — is two pieces of work: **fix the instance,
and encode a check so the class can't return**. The second half is the one that
compounds. Skip it and you buy the same bug repeatedly, forever.

**Why:** Agents don't learn from being told. A correction lives for one context window
and vanishes on `/clear`; the next session repeats the mistake with total confidence.
That makes the usual human remedy — remember, mentor, be more careful next time — worth
nothing here. The only durable memory an agent has is the one you build outside it: a
lint rule, a test, a gate, a line in the rules file it loads every session. So the
question after every defect isn't "how do I fix this?" but **"where does this go so it
can't happen again?"**

This is also why the loop gets *faster* over time rather than slower. Each encoded check
is a class of failure permanently removed from review, so review attention moves to
things no check can catch yet. The system is designed to make itself stricter.

## Triage: instance or class?

Ask two questions about every finding:

1. **Could this recur?** A one-off typo, no. Anything arising from a pattern — a
   convention the agent doesn't know, a seam it reasons wrongly about, a repo-specific
   constraint that isn't written down — yes.
2. **Would a machine have caught it?** If yes, it becomes a check. If no — it needed
   human judgment about intent — it becomes a written constraint, and that's still
   durable.

If you have given the same feedback twice, the triage is already decided. Twice is the
signal that it was never an instance.

## Where each kind of finding goes

Prefer the most enforceable home the finding can reach:

| Finding | Encode as |
|---|---|
| Wrong behaviour, edge case missed | A **test**, derived from the spec |
| Wrong pattern, banned construct, boundary crossed | A **lint rule** (incl. architectural boundaries as failing tests) |
| Unsafe or irreversible action | A **hook / permission gate** at the tool-call boundary |
| Missing step in the process | A **pre-flight check** — a state that can't be reached |
| Repo-specific knowledge the agent can't infer | A line in the repo's **`CLAUDE.md`** constraints |
| Universal across every project | A line in the **rules file** vendored to every repo |
| A recurring multi-step task done inconsistently | A **skill**, versioned with the repo |

## The ladder — advisory to binding

Not everything can be a hard gate on day one, but everything should be climbing:

1. **Told once** — worthless, gone at the end of the session.
2. **Written down** in the always-loaded rules — survives, but the agent can still
   overlook it under pressure.
3. **Checked automatically**, advisory — visible, ignorable, useful for judgment calls
   where an LLM's opinion is a signal rather than a verdict.
4. **Enforced** — an executable check that fails the build. This is the only rung that
   actually holds.

Keep semantic/LLM judgment on rungs 2–3 and off the binary pass/fail. Deterministic
checks block; inferential ones advise. An LLM judge on the critical path makes the gate
non-reproducible, and a flaky gate gets disabled within a fortnight.

## Write the check so it fails first

The discipline that makes this real: **write the new check, run it against the code as it
was, and confirm it goes red.** A check that was never seen failing is a check you're
guessing about. This is the difference between "I added a test" and "I proved this class
of bug is now impossible" — and it's the thing that stops the encoded rule from being
subtly wrong in a way nobody discovers for months.

## Keep it honest

- **Prune.** Checks that have never fired, and rules nobody has needed, cost context and
  runtime on every change. Review them periodically and delete the dead ones. Guardrails
  are not free, and a bloated always-on rules file degrades every session.
- **Never weaken a check to make a change pass.** The moment a red gate becomes
  negotiable, the entire scheme is decorative. If the check is genuinely wrong, change it
  deliberately, in its own commit, with the reason recorded.
- **Track the repeat rate.** The metric that matters is how often the same class of
  finding comes back. Trending to zero means the loop is working; flat means you're
  fixing instances and calling it a system.

**Related:** [testing-ai-written-code](../evals/testing-ai-written-code.md),
[adversarial-review](../agents/adversarial-review.md),
[debois-agent-enablement](debois-agent-enablement.md) (fix the system, not the code).

**Source:** Ryan Lopopolo (never give the same feedback twice; harness engineering),
Patrick Debois (fix the system, not the code), Stephane Jourdan et al. (crank the
deterministic gates up), Edouard Maleix (turn attributed mistakes into reusable team
knowledge), plus our own practice.
