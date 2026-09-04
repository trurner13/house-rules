# verification-and-gates (starter)

What runs between "implementation done" and "merged / released" — the automated
gates that carry the safety burden once you **auto-merge**. Adapt per repo; for a
solo/small repo, start with the cheap high-value ones and add the rest as the repo
grows (scale notes inline). Pattern inspired by `swamp`; our own wording (it's AGPL).

## The merge gates (path-scope the expensive ones for cost)

- **Code review** — coding standards + test coverage; all non-draft PRs.
- **Adversarial review** — only when core/domain code changes; "assume it's broken
  until proven otherwise" across logic, error handling, security, concurrency, data
  integrity, resource management, API contract.
- **UX review** — only when user-facing surfaces change (CLI/output/errors): help
  text, error messages, log+JSON parity, exit codes, command-shape consistency.
- **CI-security review** — only when CI/workflow files change: prompt/expression
  injection, dangerous triggers, unpinned actions, over-broad job permissions, secret
  exposure, the auto-merge trust boundary.
- **Dependency / vuln audit** — OSV scan + outdated-dependency checks.
- **Smoke test** — boot the *compiled* artifact (`--version`/`--help`) to catch
  load-time errors that type-checks and unit tests miss.

Run the costly AI reviewers **only on the relevant changed paths** (path filtering)
so you're not paying for an adversarial review on a docs-only PR.

## Hardening every AI reviewer

- Open each reviewer prompt by declaring the diff, title, body and comments
  **UNTRUSTED USER DATA**; tell it to flag any text trying to influence its verdict
  as a security finding.
- **Scope reviewer tools to read-only** (read/search + read-only VCS view) — no
  write, no exec.
- **Tier models:** stronger model for adversarial/security/general review, cheaper
  for UX.
- Make the verdict a **hard gate**: on a critical/high finding the reviewer requests
  changes *and the CI step fails* (e.g. non-zero exit / marker file) so branch
  protection blocks the merge. An advisory comment is not a gate.

## Gates as code (pre-flight checks, not prompt requests)

Encode blocking conditions as executable checks:

- A plan can't be marked **approved** while unresolved critical/high findings exist,
  or while the review is stale for the current plan version.
- Ordering/cooldown checks (e.g. don't accept a "merged" signal seconds after the PR
  opened).
- Nothing merges on a red gate; a **`hold` label** blocks auto-merge (escape hatch).

## The enforced flow (aspirational: a state machine)

Model the idea→merge lifecycle as states with legal transitions
(`triage → classified → plan → approved → implementing → pr_open → releasing →
done`, plus terminal `dropped` for the ones you decline); illegal jumps **fail**, and
state persists to disk so it survives a fresh agent context. **That disk is
[`issue-tracker.md`](issue-tracker.md)** — one file per issue, carrying the current
state and the transition log. Without it the state machine silently resets every
session. Start as a checklist/skill for a solo repo; harden into a real state machine
when the flow is worth enforcing.

## UAT — run the built artifact as a user (before release)

Three gates on the **compiled artifact**, not the source:

1. **Acceptance** — exercise each command/path the way a user would; validate
   structured output against a schema; run in isolated temp dirs.
2. **Adversarial** — try to break it: bad input, path traversal, secret leakage,
   mid-operation interruption (SIGTERM), concurrency, resource exhaustion, corrupted
   config.
3. **Performance** — budget thresholds (e.g. p75 latency) with warmup + measured runs.

Why: a green unit suite isn't "done" (real bugs pass unit tests and only surface
here). Keep UAT in its own space and run the **locally-built** binary, not whatever
is on `PATH`.

## Evals (two lanes + a drift monitor)

- **Quality** — is the skill/prompt well-written? A judge scores it; gate on a
  threshold (e.g. average ≥ 0.90).
- **Routing/triggering** — does the model actually pick this skill for the right
  queries and *not* for the wrong ones? Use positive **and** negative cases; gate on
  a pass rate (e.g. ≥ 90%).
- **Drift monitor** — a periodic (e.g. weekly) cross-model eval across providers as a
  **non-blocking** signal to catch model regressions and provider lock-in.

> **Scale note (solo / small repo):** begin with the smoke test, one code review, the
> untrusted-input preamble, and the `git checkout`-reversibility permission rule. Add
> the adversarial / UX / CI-security reviewers, pre-flight gates, and UAT as the repo
> earns them.
