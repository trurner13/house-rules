# Opus drives; cheaper helpers do the legwork

> **Adopted 2026-11-20 as the rule *Triage the models and agents for each job***, which
> replaced *Don't let weak models drive the top-level agent* and *Default to one agent*. It was
> on trial in two repos and was adopted before those trials reported. A ready-to-copy,
> enforced version is [templates/model-policy/](../../templates/model-policy/README.md)
> (added 2026-10-30).

**Principle:** The strongest model (Opus) stays the main session: it plans, decides and
checks. It hands self-contained, low-stakes jobs to helper agents on a cheaper model
(Sonnet or Haiku) and treats what comes back as a draft until it has checked it.

**Why:** Most of the tokens in a long session go on legwork: sweeping files, reading logs,
mechanical edits. A cheaper model does that well enough, at a fraction of the price, and its
output never reaches the main context, only its conclusion. The judgment work stays on the
strong model. This is the arrangement Anthropic's own cost guidance measures as working (a
frontier orchestrator over cheaper workers), and it is the positive half of the older rule
*Don't let weak models drive the top-level agent*, which the triage rule replaced. The reverse fails: a cheap model in charge
never consulted the stronger one it was given as an adviser.

Its limits:

- **Dependent steps stay with one agent.** Splitting work that depends on itself costs up to 10x for worse
  results. The saving exists only for genuinely independent jobs. For one long chain of
  reasoning, one frontier model at lower effort beats an orchestrator.
- **The choice of model for each job is Opus's judgment, and nothing measures it.** So the
  policy is written down, and each helper's result is checked before it is used.
- **Prove correct before going cheaper** (added 2026-11-10). A job moves to a
  cheaper model, or has its context trimmed, only once there is a check that says what a
  correct result for that kind of job looks like. Without one, a saving and a silent drop in
  quality look the same. Tessl cut its cost per PR from about $75 to $13 this way, by its own
  account, and only after the checks existed
  ([podjarny](https://www.youtube.com/watch?v=kPB9y6ZWXxk&t=3956s),
  01:05:56); Steve Yegge uses one check per job type to decide whether a cheaper model
  qualifies ([yegge](https://www.youtube.com/watch?v=kPB9y6ZWXxk&t=30798s), 08:33:18).

## How to apply

**Three ways to set a helper's model in Claude Code:**

1. **Opus picks per job.** When the main session starts a helper, it can name `haiku`,
   `sonnet` or `opus` for that one job. Flexible, but it relies on the written policy below.
2. **Fixed per helper type (most predictable).** A helper defined in the repo's
   `.claude/agents/<name>.md` carries a `model: haiku` or `model: sonnet` line and always runs
   on that model. No definition may carry a `memory:` field.
3. **One setting for every helper:** `CLAUDE_CODE_SUBAGENT_MODEL`. Simple, but blunt: it
   cannot tell a file search from a security review.

**A starting policy** to write into the repo's `.claude/rules/`:

| Job | Model |
|---|---|
| Searching and reading widely, summarising long logs or test output | Haiku |
| Mechanical edits that follow a pattern already set, routine docs | Sonnet |
| Plans, architecture, anything touching money, sign-in, secrets or irreversible writes; the adversarial review | Opus; the adversarial review is three reviewers (Opus, Sonnet, Haiku), plus Fable for full-review changes |
| Unsure | Opus |

**Opus checks before it relies on the result:** a helper's search is spot-checked against
one file; a helper's edit is read as a diff and run through the gates like any other change.

**Check the build first.** The machine this was written on ran Claude Code 2.1.86;
per-helper model choice works there, but check newer controls on a current build before
relying on them.

## The enforced form: triage names the model

The policy above relies on Opus remembering it. One team's repos went further on 2026-10-30: triage names a tier for
every helper, and the limits are enforced. The kit is [templates/model-policy/](../../templates/model-policy/README.md).

- **Three helpers with fixed tools.** Haiku and Sonnet run only as `scout` (reads), `light-editor` (edits) and
  `web-researcher` (web only). None has a shell, so a cheap helper cannot deploy, merge or reach a secret through a script,
  whatever it is told. That is stronger than a rule about what it may do, and it is why the built-in `Explore` is not used
  for Haiku: it has a shell.
- **The tier follows the files touched, not the task's description.** The worst failure is a "tidy-up" on a cheap model
  quietly reaching money or sign-in code, so the guard refuses protected paths at the moment of editing. A check at merge
  was tried on paper first and dropped: it trusted a label anyone could write or leave off.
- **Streams and whole sessions stay on Opus.** A session always has a shell, and it cannot change its own model.
- **The cost:** test runs, branch updates and builds stay on Opus too, so this saves less than the looser policy.

Review found the same mistake twice in protected lists written from memory: a live script that customers' pages load was
left open. Protect every script and template in any folder, then check the list against real files.

## What to measure

- **Cost:** tokens or spend per finished task, against the same kind of task with Opus alone.
- **Rework:** helper results Opus had to redo or correct, and fixes within a week to work a
  cheap helper did. A saving that comes back as rework is not a saving.
- **Escapes:** any helper on Haiku or Sonnet that touched a job the policy reserves for Opus
  (target zero).

Keep the cheaper tier if cost falls with no rise in rework or escapes; otherwise go back to Opus.

**Source:** written 2026-10-22; Anthropic,
[optimising for cost and intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence);
the October research pass, rules 35 and 36 in
[research-rules-still-current-2026-10](../research-rules-still-current-2026-10.md).
