# Testing when the agent writes the code

**Principle:** Tests are the contract the agent is not allowed to renegotiate. They
derive from the approved spec, not from the implementation, and the agent's job is to
make the code satisfy them — never the reverse.

**Why:** When a human writes both the code and the tests, a test that bends to fit the
implementation is a mild smell. When an *agent* writes both, it's the default failure
mode: the fastest path to green is to change the assertion, and the agent will find it.
Its training data is full of developers doing exactly this. So the discipline that is
optional on a human team becomes structural here — if the tests can move, you have no
signal at all, and "all gates green" means only that the agent successfully negotiated
with itself.

## Where tests come from

- **From the spec, before the implementation exists.** The spec is written and approved
  first, so the acceptance criteria are fixed before there's any code to accommodate.
  Derive the test list from the spec in a separate step, and review *that list* — it's
  much cheaper to spot a missing case in ten lines of test names than in the diff.
- **Not from the diff.** A test written after the fact, by the same agent that wrote the
  code, tests what the code does — including its bugs. If tests must be added to existing
  code, have a different agent write them from the spec/behaviour, without the diff.
- **Behaviour, not lines.** Line coverage is trivially gamed by an agent and says nothing
  about whether the spec is met. Track which *acceptance criteria* have a test.

## The four ways an agent fakes green

Watch for these in review; each one has an enforcement answer.

1. **Weakening the assertion** — loosening an equality to a range, `toBeTruthy`, removing
   a case. *Enforce:* changes to test files are reviewed as changes to the contract; a
   diff that touches tests and source together gets flagged for human eyes.
2. **Mocking away the failure** — stubbing the thing that actually broke, so the test
   passes without the behaviour working. *Enforce:* at least one test per acceptance
   criterion runs against the real dependency (integration or UAT layer).
3. **Retry-until-green** — adding retries or timeouts to a flaky test instead of fixing
   the underlying race. *Enforce:* zero tolerance for flakes — fix or delete the same
   day, never retry. A tolerated flake trains everyone, human and agent, to ignore red.
4. **Skipping and deleting** — marking a test skipped, or quietly removing it, and
   reporting the suite green. *Enforce:* track the test count and the skip list as a
   checked-in artifact so a drop shows up as a diff, not as silence.

## The layered stack

Each layer catches what the one below it structurally cannot:

- **Types + lint** — free, instant, and the cheapest possible feedback for the agent.
  Crank these up: strict mode, no implicit `any`, no unused, architectural boundaries as
  lint rules. Every rule here is a class of bug the agent can never ship again.
- **Unit tests** — logic and edge cases, derived from the spec.
- **Integration tests** — the seams. Most agent-written bugs live here, because the
  agent reasons correctly about each side and wrongly about the contract between them.
- **UAT on the built artifact** — run what you're actually shipping, as a user would, in
  a clean environment. A green unit suite is not "done": load-time errors, packaging
  mistakes, and config problems only appear here.
- **Adversarial pass** — a separate agent trying to break it: bad input, boundary values,
  interrupted operations, concurrent access, resource exhaustion. See
  [adversarial-review](../agents/adversarial-review.md).

## Make it a gate, not a request

An instruction in the prompt — "run the tests before you finish" — is advisory. The
agent may comply, and you'll never know when it doesn't. The same check as a CI job is
binding: it runs whether or not the agent felt like it, and nothing merges red. Anything
you actually care about belongs in the pipeline, not in the prompt. Run the suite in your
own pipeline rather than asking the agent to report on it — an agent reporting its own
test results is a self-graded exam.

**Related:** [findings-to-guardrails](../ways-of-working/findings-to-guardrails.md) —
what to do with each failure so it can't recur.

**Source:** Dave Farley (vibe coding: treat the AI like a compiler — verification is the
whole game), Paul Stack (tests as the source of truth; three-gate UAT), Justin Cormack
("When Tests Lie" — never tolerate a flaky test), plus our own practice.
