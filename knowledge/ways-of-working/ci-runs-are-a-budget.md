# CI runs are a budget, not free

**Principle:** Every paid CI run (GitHub Actions minutes on private repos) spends from one
shared allowance. When it runs out, every repo stops merging at once. Spend runs like money:
test locally first, run CI once per change on its finished code, and never let a workflow
spend on nothing.

**Why:** Agents treat a CI run as free and instant. They push every fix, re-run to "see if it
goes green", and fan out streams that each test on their own, so a single feature can be planned
at a dozen runs. On private repos that spends paid minutes nobody agreed to, and an exhausted
allowance stops every repo merging at once: the cost is the smaller problem, the bottleneck is
the bigger one. Moving the tests to a cloud build service only moves the bill.

**How to apply:**

- **Local first.** Before any push, run lint, the build and the tests the change touches. CI
  confirms work; it is not a place to find out whether code compiles.
- **One run per change.** Push a finished head and open the pull request only when it is ready.
  Review rounds and fixes happen before that run, not after it. A change that needs a second run
  says why.
- **Batch merges.** Several ready changes go through one integration branch with one run on that
  exact tree, not one run each after every merge.
- **No speculative runs.** No re-run to see if a flaky test passes (fix or delete the test).
  No "proof" runs (mutation, revert) without a yes. No pushing to watch CI do your checking.
- **Plans count runs.** A plan or a fan-out states its expected runs and their cost before it
  starts. The target is one run per repo per change. More needs a reason the human accepts.
- **Workflows spend nothing on nothing.** Skip the full suite on documentation-only changes
  (`paths-ignore`). Do not re-run the suite when a label changes. Cancel a run its own next push
  supersedes (`concurrency: cancel-in-progress`). Cache slow installs. Do not test the same tree
  twice (the PR run, then again on `main` after a fast-forward merge).
- **When the allowance is gone, work waits.** Never fall back to another paid runner that has not
  been agreed in advance.

**Clarified 2026-10-12 (research pass):**

- **This is a house rule, for cost.** The wider field does not recommend it; the 2026-10-12
  research pass found nothing against it on those terms either. GitHub's withdrawn plan to
  charge for self-hosted runners (announced 2025-12-16, postponed within two days, never
  applied) was not the reason for this rule and its withdrawal changes nothing.
- **The laptop runner is for private repos only.** GitHub's own hardening guide says
  self-hosted runners should almost never be used for public repositories, because anyone who
  opens a pull request can run code on the machine. If a repository goes public, its CI moves
  off the laptop first. Public repositories get GitHub-hosted minutes free, so they use those
  (this one does): the rule is about paid compute, not about hosted runners as such.
- **An idle runner drops off.** A self-hosted runner that is offline for more than 14 days is
  removed from GitHub by itself and has to be registered again.
- **Anthropic's cloud features are paid compute too.** Managed Code Review, routines (full cloud sessions, every connector writable by default) and
  `/code-review ultra` all run on Anthropic's cloud for money. An agent never starts one on its
  own: each needs a yes from a human, per run. This closes the gap the research pass found,
  where the kit offered these features and the rule did not say whether they counted.
