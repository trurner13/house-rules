# house-rules

Standing rules for working with coding agents, plus the hooks and CI gates that
enforce them. Written once here, then vendored into the repos I work in,
32 of them today, so the same standards load in every session on any machine
from a plain clone.

The premise is that a rule an agent is merely *asked* to follow is advice, not a
control. Advice is fine for style. It is not fine for "don't drop the database"
or "don't mark a plan approved while critical findings are open". Anything that
must hold gets an executable check behind it.

## Start here

| | |
|---|---|
| [`rules/RULES.md`](rules/RULES.md) | The 58 rules themselves. One or two lines each, every one linking to the note behind it. This is the file that gets vendored. |
| [`templates/hooks/`](templates/hooks/) | The enforcement. Dependency-free Python, shell and PowerShell: a completeness gate that asks whether a fresh clone would actually work, a tracker well-formedness gate, commit-message, pre-commit and pre-merge hooks, and a config-review gate that needs a human's name on any change to hooks, agent settings, MCP lists, workflows or lockfiles. The kit can also archive session transcripts to a folder in the user's home directory; that hook is off by default, and what it stores is the whole transcript (code, command output, everything the agent read), unencrypted, with no purge. |
| [`knowledge/`](knowledge/INDEX.md) | The reasoning behind the rules, one idea per file. Read on demand, deliberately kept out of the always-on rules file so it does not cost context in every session. |
| [`templates/agent-constraints/`](templates/agent-constraints/README.md) | The operational conventions: planning, triage, verification and gates, issue tracking, session lifecycle, adversarial review dimensions. |
| [`ADOPTION.md`](ADOPTION.md) | How the kit lands in a new or existing repo. |

## The parts worth reading first

**[`templates/hooks/check-committed.py`](templates/hooks/check-committed.py)** asks
the question most repos answer wrongly: would a fresh clone of this actually build
and run? It emits machine-readable codes rather than prose, has `--json`, `--ci`
and `--handover` modes, and ships with
[25 tests](templates/hooks/test-check-committed.py) that assert on the codes, so
every check has been watched failing before it was trusted. The commit-message hook
ships with [37 cases](templates/hooks/test-commit-msg.sh) of its own, and the sync
script with [its tests](scripts/test-sync-guardrails.ps1).

**[`.github/workflows/checks.yml`](.github/workflows/checks.yml)** runs the gate's
own tests *before* the gate. A completeness gate nobody has watched fail is a
claim, not a check.

**[`knowledge/ways-of-working/session-handover-and-work-state.md`](knowledge/ways-of-working/session-handover-and-work-state.md)**
is the one I would point a sceptic at. It starts from a wrong answer, finds that
session-end hooks cannot block and may never fire, and moves the design to
checkpointing at the end of each turn with the *next* session's start as the real
gate. The rules here are mostly like that: something broke, and this is what
replaced it.

## The operating model

I own the specs, the architecture and the gates. Coding agents write the
implementation inside them, under adversarial review, and nothing merges on a red
gate. The roughly 2,700 lines of Python, PowerShell, shell and Node in this repo were
specified, reviewed and hardened that way.

The division that makes it work is that **deterministic checks block and model
judgment only advises**. An LLM reviewer that can veto a merge is a flaky
pipeline waiting to happen. It runs alongside the gates, argues its case, and
escalates to a human instead of looping.

## What is not here

This is the published cut of a working repo. The raw source material behind the
notes, the day-to-day tracker, and client-specific detail stay private. Talk
citations point at the public recordings rather than at transcripts, which are
not mine to republish. Where a rule came from a real failure, the failure is
described and the repo it happened in is not.

One rule in `RULES.md` is marked *(aspirational)*: intended, not yet enforced.
It is labelled rather than quietly listed with the other 57, because a rules file
that blurs the two is not trustworthy about any of them.

## Licence

Two licences, split by what the file is:

- **The writing** — the rules, the plain-English companion, the notes in
  `knowledge/`, the conventions in `templates/agent-constraints/` and every other
  document — is under [Creative Commons Attribution 4.0 International](LICENSE)
  (CC BY 4.0). Reuse it, adapt it, vendor it into your own repos; keep the
  attribution.
- **The code** — everything in `templates/hooks/` and `scripts/`, and any `.ps1`,
  `.py`, `.sh` or `.mjs` file wherever it sits — is under the [MIT licence](LICENSE-CODE),
  so it can go into a codebase under any licence without CC terms attaching to
  the code around it.

A lawyer has been asked to confirm this choice; until that comes back, treat
the split as the intent rather than settled.
