# The merge unit: one branch, one increment, one yes

**Principle:** A branch carries one increment and the human's yes to that increment merges
it the same day. Never let a branch become the unit of a campaign, never merge a branch into
another branch, and never let shared state outside git (a database, served documents) get
ahead of main.

**Why:** A team looked across its repos after a long stretch of agent-driven work. Nothing had
been lost: every line was pushed, checkpointed and written up. That is exactly why the problem
had no pain signal. What it found:

- One branch was dozens of commits ahead of main, carrying several increments. A human had
  approved each one, and none had merged: no approval ever asked "merge?", and each came with
  "carry on unsupervised", which the agent read as "carry on, on this branch".
- A helper agent's branch had been merged *into* that branch, making it a second main.
- Two unmerged branches had each bumped the same version number for different changes, so
  whichever merged second would have had to renumber.
- Shared data that other services read had been reloaded from the unmerged branch, so main no
  longer matched what was being served. "Don't merge yet" had quietly become the riskier option.
- A gate that checked records against main's checkout failed for anything written on a branch,
  and the workaround, a holding folder, made the long branch permanent.
- There were no pull requests, and not every repo had CI, so merging was a human act that had to
  be remembered. The rule "agents auto-merge on green gates" had no machinery behind it there.

The rules already in place covered isolation, checkpointing, issue capture and gates as code,
and all of them held. None named the merge unit, a branch's maximum life, what a yes implies for
main, or that shared data must follow main. A start-of-session digest that reports dirty trees
and unpushed commits, but not "dozens of commits and several days ahead of main", lets a safe
branch sit unmerged indefinitely. The nearest general advice ("work in small, verifiable
increments", "CI before scaling agents") was already being followed, or pointed at the missing
CI without saying what the merge unit is: the problem needed a rule written from the failure.

Two other rules pull the other way unless this one exists. *Parallelise by default* multiplies
branches, and without a merge unit it produces exactly the branch-into-branch seen here. *CI
runs are a budget* merges several ready changes through one integration branch and one run;
read loosely that licenses a long campaign branch, so this rule says an integration branch holds
only approved, finished increments and is merged or deleted the same day. *Decisions come as a
briefing* helps directly: the merge question becomes one of the choices on the page instead of
the question nobody asks.

**How to apply:**

1. One branch per increment (one feature, one plan step, one decision). The decision page's
   ask says "yes means this merges", and the merge happens the day the yes arrives.
2. "Carry on unsupervised" means merge the approved increment, then branch again from main.
3. A sub-agent's branch merges into main after its review, or waits. Never into a branch.
4. Reload a shared database or served documents only from code that is on main.
5. A record that cannot be filed until a merge is a reason to merge today, not to park it.
   If a gate blocks the filing, the gate is the bug.
6. The session-start digest prints each branch's commits ahead of main, commits behind,
   days since it left main and days since its last commit, and flags anything more than two
   days or one increment ahead. The next session puts that number to the human as a merge
   question before starting new work. The block lives in
   [templates/hooks/session-start.py](../../templates/hooks/session-start.py).

Tried first as a repo-specific rule where the problem showed, then adopted as *One branch, one
increment, merged on its yes* in [rules/RULES.md](../../rules/RULES.md). The rule names the
problem and the digest makes it visible; the merge itself still has to happen.

**Source:** a team's own repo survey; builds on
[session-handover-and-work-state](session-handover-and-work-state.md) and
[findings-to-guardrails](findings-to-guardrails.md).
