# Continuous AI — a third pillar beside CI/CD

Adopted as a rule. From Don Syme's AI Native DevCon London 2026 talk, "The Agentic
Repository Automation Revolution" (auto-caption source — verified the gist, names
treated as uncertain).

## The idea

Beyond CI (build/test) and CD (ship), add **Continuous AI (CAI)**: recurring agentic
jobs that run on a schedule or event, automating work that used to wait for a human or
a rare sprint. "It's CI, CD, and continuous AI."

Examples: issue **triage**, repo **maintenance**, **fault analysis**, **accessibility**
and **performance** walkthroughs of the running app, docs upkeep, dependency hygiene.

## Run them safely (non-negotiable — "always have a security architecture")

- **Read-only, no secret access, sandboxed**: run in a container, firewalled network,
  no shared caches.
- **Plan / apply split with threat detection between**: the agent step produces output
  to a *narrow channel*; a separate, non-agentic stage applies it, with threat
  detection in between.
- **Narrow safe-output channels**: constrain output to a single declared artifact —
  one issue, or one PR. The PR is the guaranteed human checkpoint; **these agents never
  merge**. (Note the tension with our adopted auto-merge rule — CAI maintenance agents
  are a different risk class from the in-repo build loop; keep them gated.)
- **Safety enables speed, not the opposite**: "the better the quality of the rails, the
  faster your train can go." Rails are the enabler of throughput, not the brake.

## The framing: repo as an automated factory

Model the repo as a production line and yourself as a **flow designer** — spot
factories that are blocked, flowing, or idle. When a flow jams, **don't hand-fix the
individual outputs — step back and add a quality gate** so the whole factory flows
again. (A concrete instance of the adopted "fix the system, not the code" rule.)

A repo-maintenance agent can run on a cadence: read its own memory file, pick from a
maintainer-controlled task menu, triage the backlog, and propose PRs.

## Source

- `transcripts/talks/syme-agentic-repository-automation.txt`
- Related external evidence: GitHub's "Continuous AI" / gh-aw — see
  [external-evidence.md](../external-evidence.md) §1.
