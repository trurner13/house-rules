# Measuring AI adoption — merge rate, not vanity metrics

Adopted as a rule. How to tell whether "AI-native" is actually working, rather than
just busy. Drawn from three AI Native DevCon London 2026 talks that independently
converged on the same point (auto-caption sources — names verified, figures treated
as indicative).

## The core metric: merge rate

- Measure the **merge rate** of PRs authored by agents / non-technical contributors,
  and especially the **share merged with no human follow-up commits** — that's the
  signal the output was actually usable, not just produced.
  - Tammuz Dubnov (Autonomy AI): reported ~74% merge rate, ~84% of those merged with
    no dev follow-up. The number matters less than *tracking it at all*.

## Vanity metrics to demote

- Ian Thomas (Meta): weekly-active users, diffs generated, lines written, and token
  usage are **vanity metrics** — "not actually proving any value." Don't report them
  as success.
- Birgitta Böckeler (Thoughtworks) reinforced the skeptic's view: throughput up ≠
  delivery up. Faster code can just move the bottleneck to review/integration (her
  "flow crisis"). So pair any speed metric with a flow/quality metric.

## External confirmation — DORA 2026 (added 2026-08-12)

DORA's 2026 report extends its 2025 finding (AI is an *amplifier* — it magnifies both
the strengths of high performers and the dysfunctions of struggling teams) by following
the whole delivery flow rather than stopping at individual productivity. Its conclusion
lands squarely on the metric above: **writing more code and opening PRs faster does not
by itself mean more value is delivered.** Where the rest of the process can't keep up,
the gains reappear as costs — changes queued for review, rework, broken tests, and more
risk reaching production. The report identifies code review specifically as the place
ROI is won or lost.

Two consequences for us:

- It is direct external support for demoting PR count and diff volume, and for pairing
  any speed metric with a flow metric — exactly Böckeler's point, now with a dataset.
- It is a caution about the auto-merge bet: removing the review *step* doesn't remove
  the review *work*, it relocates it to the automated gates. Those gates are now the
  flow constraint, and they need measuring like one. See
  [external-evidence](../external-evidence.md) §6.

*(Read via secondary reporting on the 2026 report, not the primary PDF — treat the
framing as sound and specific figures as unverified.)*

## Supporting practices (honourable mentions — parked as candidates)

- **Risk-tag every diff/PR** (Dubnov + Thomas's "DRS" independently): auto-label each
  PR with a risk level + size so review effort routes to the risky changes and
  low-risk ones fast-track. Strong, but lives in `agent-constraints/` not as a lean
  rule.
- **Maturity self-assessment on a cadence** (Thomas, DORA-derived): give teams a
  multi-dimension AI-adoption maturity model and a workshop they re-run every few
  weeks to find their own gaps.
- **Start adoption on low-risk work** (Thomas): begin on tests, internal tooling, and
  codemods — high control, low blast radius — before novel feature work. (Sharpens the
  adopted "Start tiny" rule.)

## Sources

- `transcripts/talks/dubnov-pm-writing-code-merge-rate.txt`
- `transcripts/talks/thomas-ai-native-engineering.txt`
- `transcripts/talks/bockeler-state-of-play-coding-assistants.txt`
