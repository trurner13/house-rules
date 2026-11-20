# The merge unit: one branch, one increment, one yes

**Principle:** A branch carries one increment and the human's yes to that increment merges
it the same day. Never let a branch become the unit of a campaign, never merge a branch into
another branch, and never let shared state outside git (a database, served documents) get
ahead of main.

**Why:** On 2026-10-07 three sibling repos (a solver, an API and a studio app) were surveyed after a
long run of feature work. Nothing had been lost - every line was pushed, checkpointed and written
up in a handoff - and that is exactly why the problem had no pain signal. What the survey found:

- The solver had one branch 46 commits ahead of main carrying five features. The owner had said
  yes to each feature's decision page. None had merged, because no page ever asked "merge?"
  and each yes came with "carry on unsupervised", which the agent read as "on this branch".
- A sub-agent's branch had been merged *into* that branch, making it a second main.
- Two unmerged branches had both raised the engine hash to the same version for different
  changes; whichever merged second would have had to renumber.
- The API's database had been reloaded with configuration documents from the unmerged solver
  branch. Those documents declared a key that the solver on main silently ignores, so main no
  longer produced what the API served. "Don't merge yet" had become the riskier option while
  still being recorded as "the owner's call".
- The cross-repo gate that keeps decision records byte-identical across the three repos
  reads only the solver's main checkout, so a record written on a branch fails it. The
  workaround, a pending folder, institutionalised the long branch.
- The same pattern had already run once: a branch lived from 11 September to 5 October and
  landed only on "merge everything open into main".
- No pull request has ever existed in any of the three repos and the solver has no CI. The
  adopted rule "human control is upstream, agents auto-merge on green gates" has no
  machinery behind it there, so merging is a human act that has to be remembered.

The adopted guardrails covered isolation, checkpointing, issue capture and gates as code, and
all of them held. None named the merge unit, a branch's maximum life, what a yes on a page
implies for main, or that shared data must follow main. A session-start digest that reports
dirty trees and unpushed commits, but not "47 commits and 4 days ahead of main", lets a safe
branch sit unmerged indefinitely.

Would the parked candidate rules have prevented it? No. The nearest ones ("work in small,
independently verifiable increments", "scale safety in step with shipping speed",
"fundamentals first: CI before scaling agents") are either already implied by adopted rules
that were being followed, or point at the missing CI without saying what the merge unit is.
None names a branch's life, what a yes implies, or data following main. The problem needed a
rule written from the failure, not one picked from a list.

**Against the rules adopted between 15 September and 5 October 2026**: none of them names the merge unit either, and two pull the other way.
*Parallelise by default* multiplies branches and says itself that the limit is what the gates
can absorb - without a merge unit it produces exactly the sub-branch-into-branch seen here.
*CI runs are a budget* tells agents to merge several ready changes through one integration
branch and one run; read loosely, that is a licence for the campaign branch, so the rule
says an integration branch holds only approved, green increments and lives hours. *Isolated
environment* now removes a worktree once its branch merges, which is downstream of the problem:
it cleans up after a merge that this failure never reached (and the solver's worktree sits
beside the repo, not under `.claude/worktrees/`, against that rule). *Never hard-code a branch*
came from the previous long branch's merge. *Decisions as multiple choice* helps directly: the
merge question becomes one of the choices on the page instead of the question nobody asks.

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

Tried in those three repos from 2026-10-07 as a repo-specific rule, then adopted on
2026-11-20 as *One branch, one increment, merged on its yes* in
[rules/RULES.md](../../rules/RULES.md). Two of the repos' branches had again outlived their
yes when it was adopted: the rule names the problem, the digest makes it visible, and the
merge still has to happen.

**Source:** a survey of three sibling repos with their owner, 2026-10-07; builds on [session-handover-and-work-state](session-handover-and-work-state.md) and
[findings-to-guardrails](findings-to-guardrails.md).
