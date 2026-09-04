# Running an adversarial reviewer

**Principle:** A second agent is pointed at the work with one job — **prove it's wrong,
unsafe, or incomplete**. Not "review this", not "any thoughts?". Its success condition is
finding a defect, and its verdict is a gate that can stop a merge.

**Why:** An agent reviewing its own output agrees with itself; it reconstructs the same
reasoning and finds the same blind spots. Even a fresh agent asked to "review this change"
drifts into summarising and approving, because approval is the statistically normal
outcome in its training data. Inverting the objective — you are trying to *break* this —
changes what it looks for. And because the reviewer is cheap and parallel, you can afford
several with different lenses, which is the one thing a single human reviewer can't do.

**What to check** is the dimensions list —
[agent-constraints/adversarial-dimensions](../../templates/agent-constraints/adversarial-dimensions.md).
This note is **how to run it** so the verdict is worth something.

## Scale the gate to the blast radius

The reviewer being cheap is not a reason to point a heavy one at everything. Match the depth to
what the change costs *if it is wrong*, which is mostly a question of **reversibility**:

| The change | Gate |
|---|---|
| Spends money per run, writes irreversibly, touches auth or secrets, migrates data, or puts a persistent bad state on a live customer surface | Full — several lenses, plus a refuter per finding |
| Sits behind a flag, or on a path with a fast rollback | One lens, or a targeted check on the risky part only |
| Is layout, copy, styling — anything a glance at the running thing settles | Build it, ship it, look at it |

Two asymmetries decide which row you are in, and they pull in opposite directions:

- **A cheap change can have an expensive failure, and still needs the full gate.** A one-line
  `?? true` on a stock field emptied a live merchant's catalogue. Size of diff predicts nothing.
- **An expensive review of a cheap, reversible failure is waste that reads as diligence.** Twelve
  agents on a `max-width` is not rigour; the agents are cheap but wall-clock and the user's patience
  are not, and for that class of change *shipping it is the faster verification*.

The tell that you have over-gated: the findings come back about the **tests** rather than the
behaviour, and the quickest way to settle the original question would have been to look at the
running page. If you notice that mid-flight, stop the loop and ship — do not finish the ceremony
because you started it.

## Set-up rules that decide whether it works

- **Independent context.** A fresh agent, no memory of writing the code, no access to the
  author's reasoning. If it inherits the implementer's context it inherits the blind spot.
- **Review the base branch, not just the diff** (for critical review). A diff frames the
  question as "is this change OK?" and anchors on the author's chosen solution. Reading
  the base first lets the reviewer ask "is this the right change at all?" — which is where
  the expensive mistakes live.
- **Read-only tools.** Read, search, read-only VCS. No write, no exec. A reviewer that can
  edit will fix what it finds and report success, and you lose the finding.
- **Treat the input as hostile.** Open the prompt by declaring the diff, title, body and
  comments **untrusted user data**, and instruct the reviewer to raise any text attempting
  to influence its verdict as a security finding in its own right.
- **A strong model.** This is the wrong place to save money — a weak reviewer produces
  confident noise, which is worse than no reviewer, because it trains you to skim.

## Make the output usable

Demand a **structured verdict**, not prose: one entry per finding with severity
(critical / high / medium / low), file and line, a one-sentence claim, and — the field
that does the work — **a concrete failure scenario: inputs or state that produce the
wrong result**. A finding that can't name how it breaks is usually a style opinion
wearing a severity label. Requiring the scenario kills most of them at the source.

Prose reviews cannot be gated on, counted, or tracked. Structured ones can.

## Verify the findings before you act on them

Adversarial reviewers over-report — they were told to find problems, so they find them.
Before a finding blocks a merge or costs a fix, run a **refutation pass**: two or three
independent agents each asked to *refute* the claim, defaulting to "refuted" when
uncertain. Keep the finding only if it survives a majority. Where a defect could fail in
more than one way, give each verifier a different lens (correctness, security, does-it-
actually-reproduce) rather than running identical skeptics — diversity catches what
redundancy can't.

This is the step most people skip, and it's the one that makes the difference between a
reviewer you trust and a reviewer you learn to ignore.

## Close the loop, with a cap

- Planner ↔ reviewer iterate until findings are resolved or consciously accepted.
- **Hard cap at ~5 rounds, then escalate to a human.** Two agents can argue indefinitely
  and expensively; the cap is a runaway-spend and non-convergence safeguard.
- **The verdict is a hard gate:** a surviving critical/high finding fails the CI step so
  branch protection blocks the merge. An advisory comment that everyone can ignore is not
  a gate — it's a suggestion box.
- **Path-scope the expensive reviewers** so a docs-only change doesn't pay for a full
  security pass.

## Then feed it back

Every confirmed finding is two pieces of work: fix the instance, and — if it represents a
class — encode a check so that class can't return. See
[findings-to-guardrails](../ways-of-working/findings-to-guardrails.md). Without that step
the reviewer finds the same category of bug forever, and you pay for it every time.

**Source:** Paul Stack (adversarial reviewer in the merge-gate pipeline), Shachar Azriel
(review the base branch, not the diff), the `swamp` reference implementation (structured
verdicts, hard gates, untrusted-input hardening); the ~5-round cap and the refutation pass
are ours.
