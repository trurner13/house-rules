# Reviewing someone else's AI-written PR (a person leads, AI assists)

**Principle:** When you review a pull request someone else wrote with AI, you set the
questions and own the verdict. The AI widens the search, and you check every finding it
raises before it reaches the author. The written review leads with the verdict and the
few findings that matter, each with how it breaks and what it costs.

**Why:** AI-written PRs fail in predictable ways. They handle the happy path only, skip
authorisation unless asked, add abstractions nobody needs, duplicate helpers that already
exist, call APIs or versions that don't exist, and come with tests that only re-check the
code. They are also larger: blog-sourced counts put AI-assisted PRs at about 2.6 times the
size of unassisted ones, so they invite skimming. A reviewer who only asks an AI to
"review this" gets a confident list that mixes real defects with invented ones, and lets
the tool do the thinking. A reviewer who reads alone misses whatever lies outside their
own habits. The fix is the same split this repo uses for agents
([adversarial-review](../agents/adversarial-review.md)): a person frames the questions and
judges the answers, and a second pair of eyes tries to break the change.

This note covers the person-led version: an outside PR, a written review, AI allowed. It
fits a team review and also a take-home review exercise in an interview, where the
transcript of your AI session is often handed in with the review.

## How to apply

Five passes, in this order. The times assume about 45 minutes; scale them up or down.

### 1. Understand what it is for (about 5 minutes)

- Read the PR description and the issue or spec it links to. Write one sentence: "this
  change should make X true for Y".
- Ask whether that is the right problem. A review that says "this solves the wrong
  problem, here's the simpler one" is worth more than ten line comments.
- Decide what "done" would look like: which behaviour, which tests, which failure cases.
  You'll check the PR against that, not against its own story.

### 2. Your own first pass, before any AI (about 10 minutes)

- Read the code around the change, not just the diff: the files it touches, what calls
  them, the data model. A diff only asks "is this change OK?". The surrounding code lets
  you ask "is this the right change?" (Google's guide says the same: look at the whole
  file).
- Map the change: what it adds, what it changes, what data it writes.
- Write down your suspicions as short notes: "what if the payment call times out
  halfway?", "can customer A see customer B's quote?". These are the questions you'll point
  the AI at, and they show in the transcript that the thinking was yours.

### 3. A directed AI pass (about 10 minutes)

- **Treat the PR as untrusted content.** Someone else's code, description and tests are
  input from outside, and any of it may contain text meant to steer an AI. Give the AI
  read-only tools (read and search, no shell). If you want to run the tests, do it in a
  throwaway container or VM with no secrets or credentials in it, never on your working
  machine as it is ([never point a code-executing agent at untrusted content](../security/agent-guardrail-failures-2026.md)).
- Start a fresh session. Give it the one-sentence intent, your list of suspicions, and
  the lenses below. Tell it the PR text is untrusted and that any attempt to sway its
  verdict is a finding in itself.
- Demand structured findings: severity, file and line, a one-sentence claim, and a
  **concrete failure scenario** (the input or state that produces the wrong result). A
  finding with no scenario is usually a style opinion.

**Lenses** (pick the ones the change touches):

| Lens | What to look for |
|---|---|
| Correctness | Off-by-one, wrong conditions, missing cases, rounding, time zones and clock changes |
| Failure handling | Timeouts, retries that double-charge or double-send, partial writes, no rollback |
| Data model | States the model allows that should be impossible, missing constraints, nullable fields that shouldn't be |
| Security | Missing authorisation checks, injection, secrets in code, personal data in logs |
| Audit | Can you tell later who changed what, and why? |
| Tests | Do they test behaviour or just repeat the code? Is the risky path tested? Were any tests weakened? |
| Scope | Unrelated changes, abstractions nobody needs yet, duplicated helpers |
| AI tells | Made-up APIs or library versions, dead code, comments that describe something else |
| Running it | Logs, metrics and alerts for the new path; a safe migration; a way to roll back |

### 4. Verify before you write (about 10 minutes)

- Check every AI finding yourself in the code. Drop any you can't confirm, and say in
  the transcript why you dropped it. Reviewers told to find problems over-report.
- For a serious finding you're unsure of, ask a second fresh session to argue against it
  ([refutation pass](../agents/adversarial-review.md)). Keep it only if it survives.
- If you can, prove the top finding: a failing test, or the exact steps to reproduce it.

### 5. Write the review (about 10 minutes)

Lead with the decision, then a short list in severity order:

1. **Verdict:** approve, approve with changes, or request changes, plus one line of why.
2. **Summary:** what the PR does, in your words, and whether it solves the right problem.
3. **Findings, blocking first.** Each gives where (file and line), what is wrong, the
   failure scenario, the impact (on the customer, the money or the data), and a suggested
   fix. Label each one: `issue`, `suggestion`, `question` or `nitpick`, and blocking or
   non-blocking ([Conventional Comments](https://conventionalcomments.org/) labels).
4. **What's good:** name the decisions worth keeping. Google's guide asks reviewers to
   acknowledge good work, and it shows you read for understanding, not just faults.
5. **Questions for the author:** what you couldn't tell from the code.
6. **What you didn't check:** say plainly what you left out (for example, you didn't run
   it or didn't load-test it). Saying "not checked" beats implying it was checked.

Keep comments about the code, not the person. Group nitpicks into one line, or drop them.

## When the transcript is handed in

Then the transcript is part of the work, and it shows how you think:

- Open by stating the intent and your plan in a sentence or two.
- Your own suspicions come before the AI's findings.
- Push back where the AI is wrong, and say why.
- Never paste secrets, tokens or personal data into the session.
- If you prepared a reviewer prompt or skill beforehand, say so and show it: preparing
  your tools in advance is a strength, not a shortcut.

**Source:** Google engineering practices, "What to look for in a code review"
([google.github.io/eng-practices](https://google.github.io/eng-practices/review/reviewer/looking-for.html));
GitHub's guide to reviewing agent PRs
([github.blog](https://github.blog/ai-and-ml/generative-ai/agent-pull-requests-are-everywhere-heres-how-to-review-them/));
thoughtbot, "How to review AI generated PRs"
([thoughtbot.com](https://thoughtbot.com/blog/how-to-review-ai-generated-prs)); the 18F
code-review interview guide ([guides.18f.gov](https://guides.18f.gov/eng-hiring/interviews/code-review)).
The 2.6x size figure is from blog and vendor sources, not a study. The lenses, the order and the
transcript advice are ours, drawn from this repo's adversarial-review practice. Researched
2026-11-20 from search summaries.
