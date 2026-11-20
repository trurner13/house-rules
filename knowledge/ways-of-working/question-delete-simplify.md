# Question, delete, simplify — then speed up, automate last

**Principle:** Before a plan is approved, work five steps in this order: question every
requirement and who asked for it; delete what can go; simplify what survives; speed it up;
automate last. Doing them out of order means polishing, speeding up or automating something
that should not exist at all.

**Why:** It's Musk's "algorithm" from SpaceX and Tesla, and the order is the point: he names
his own commonest mistake as optimising a part that should have been deleted. It matters more
with AI-written work than with people's, because **agents invent requirements**. They add
options, fallbacks, settings, abstractions and "while I'm here" extras nobody asked for, and
every one is code to test, review and maintain. Asking *who asked for this, by name* is the
cheapest filter there is: if the answer is "the agent", it goes unless a human wants it. It
also backs up *Check altitude every turn*. That rule asks whether the next step serves the
goal; this one asks whether each piece of the plan does.

**How to apply:**

1. **Question every requirement.** The plan lists each requirement with who asked for it: a
   person by name, the spec, a test, or a rule. Nothing comes from "the team" or "best
   practice". A requirement the agent added itself is marked as such and cut unless the
   human keeps it. Even a smart person's requirement gets questioned.
2. **Delete.** Remove every part, step, file, dependency, option and process that can go. The
   best part is no part. Expect to add back about 10% later; if nothing ever comes back, you
   didn't cut enough. The plan records *what we cut*, so the reviewer and the human can see it
   and argue to put something back.
3. **Simplify** only what survived the delete step. Don't simplify something you could have
   deleted.
4. **Speed up** the cycle: shorter loops, real tests sooner, smaller increments. Only now,
   and only for what is left.
5. **Automate last.** Don't build a script, job, hook or agent workflow for a process until
   the process has been questioned, cut and simplified, and has run by hand long enough to
   prove it is worth keeping. Musk said of Tesla's 2018 factory that too much automation was a
   mistake.

**Where it bites (adopted 2026-11-20):**

- **Every plan.** [planning-conventions](../../templates/agent-constraints/planning-conventions.md)
  asks for a *Requirements: who asked* list and a *What we cut* list.
- **The adversarial reviewers.** The *Scope* lens in
  [adversarial-dimensions](../../templates/agent-constraints/adversarial-dimensions.md)
  asks whether anything could be deleted, and flags any requirement with no one named who
  asked for it. That is advice, not a gate: an AI's judgement doesn't block anything (*Gates
  as code*).
- **Not every one-line fix.** A small fix with an obvious single requirement needs no
  ceremony. The plan rule already exempts it.

**Not a contradiction:** *Never give the same feedback twice* turns a repeated failure into an
automated check straight away. That is not "automating early". The failure has already
happened, more than once, so the requirement has been tested by reality. "Automate last"
is about building the product and the processes, not about delaying guardrails.

**Source:** Elon Musk to Tim Dodd (Everyday Astronaut), Starbase tour, 30 July 2021
([Everyday Astronaut](https://everydayastronaut.com/starbase-tour-and-interview-with-elon-musk/)). The "add back about 10%" rule of thumb is
reported in Walter Isaacson, *Elon Musk* (2023). The AI angle (agents invent requirements) is
ours. "The best part is no part" is widely attributed to him; no primary source was found.
