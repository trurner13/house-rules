# External evidence (non-conference sources)

Reference material beyond the conference talks, gathered to inform the rules in
`rules/RULES.md`. These are short cited summaries — read the originals for depth.

## 1. GitHub — "Peli's Agent Factory" (gh-aw / GitHub Agentic Workflows)
*github.github.com/gh-aw/blog — 12 Jan 2026*
- 100+ **specialized** agentic workflows running in production repos. Heterogeneous
  (many focused agents) beats one general-purpose agent — "focused agents allowed
  us to find more useful applications."
- Workflows authored in **Markdown**, compiled to GitHub Actions with **carefully
  scoped permissions + guardrails**. Insight: "strict constraints actually make it
  easier to experiment safely."
- **Operational tiers:** read-only analysis → PR proposals → **meta-agents** that
  monitor and improve other workflows.
- Everything is **observable, auditable, and remixable**; explicit cost-quality
  tradeoffs (longer analyses aren't always better).
- **Converges with:** Maple "Continuous AI" (agents in CI), Debois "agent
  enablement", and the harness-engineering practices in the talk notes in `knowledge/`.

## 2. martinfowler.com — recent AI articles (2026)
- **"Maintainability sensors for coding agents"** — Birgitta Böckeler, 19 May 2026:
  a system of "guides and sensors" that raises the probability of quality agent
  output and lets agents self-correct. *(Böckeler gives the Day-2 keynote we lack a
  transcript for — good proxy for her thinking.)* Converges with Ryan Lopopolo
  (just-in-time lints/guardrails) and Jourdan ("linting to 11").
- **"Interrogatory LLM"** — Martin Fowler, 14 May 2026: generate context docs via
  structured interviews, not just hand-written prompts. Converges with Claude
  Code's "let Claude interview you" and Burrows/Debois context systems.
- **"Vibe Coding"** — Martin Fowler, 21 May 2026: fine for disposable software;
  maintainability/security problems for production. Converges with Farley's talk.
- **"The VibeSec Reckoning"** — 27 May 2026: write a **security-context file** to
  guide the AI; ship secure-by-default templates. Converges with Katsioloudes/Tal.
- **"What is Code"** — Unmesh Joshi, 12 May 2026: code is both machine instructions
  and a conceptual model — matters when delegating to agents.

## 3. Justin Cormack — "Ignore previous directions" (newsletter)
*buttondown.com/justincormack/archive* — Cormack is a Day-2 DevCon speaker ("When
Tests Lie: Using Observability to Keep AI Honest", transcript not uploaded yet).
Newsletter is mostly systems/hardware; the only AI-relevant issue is
**#12 "System programming experiments with AI"** (8 May 2026) — content not exposed
in the archive view. Low priority; revisit if we want his observability angle.

## 4. System Initiative — `swamp` (live reference implementation)
`github.com/systeminit/swamp` — Paul Stack's AI-native CLI (TypeScript/Deno, AGPLv3,
~400★), built almost entirely by agents. The old Rust product
`github.com/systeminit/si` has been frozen since Feb 2026 ("we threw it away in
January"). `swamp` is a real, working instance of our adopted guardrails — **our
biggest source of inspiration.**

Direct matches to adopted rules:
- Executable `CLAUDE.md` constraints (TS strict / no `any`, named exports, AGPLv3
  header per file, no fire-and-forget promises, small blast radius, explicit
  commands + verification chain).
- **Auto-merge after CI + Claude review, with a `hold` label to block it** → our C1 + escape hatch.
- Skills-are-code: `.claude/skills/<name>/SKILL.md` (uppercase, frontmatter
  name+description, <500 lines, `references/`, `evals/`), hard-prerequisite `skill-creator`.
- `agent-constraints/` split by phase (triage / planning / implementation /
  adversarial-dimensions) → our spec-first + adversarial reviewer.
- `evals/promptfoo` + a `multi-model-eval.yml` CI gate; `extensions/` for lifecycle guardrails.
- Every command supports `log` + `json` output → our agent-readable-logging.

**Woven into the guardrails:** the phase files
([templates/agent-constraints/](../templates/agent-constraints/README.md)), the
adversarial dimensions, the skill spec, the `hold`-label escape hatch, the
verification gate, and dual output mode. **Caution:** `swamp` is AGPLv3 — we
borrowed the *patterns in our own words*, not the files.

### Deep-dive (verified 2026-06-03 — repo files + Stack's blogs)
Two parallel reads — the actual repo (`github.com/systeminit/swamp`, files on HEAD)
and Paul Stack's blog (`stack72.dev`) — cross-checked each other. Quotes kept short
(AGPL). Stack's relevant posts: *The Lifecycle of a Swamp Issue* (08 Apr), *The Vibes
Don't Scale* (13 Apr), *Anatomy of a Swamp PR* (15 Apr), *The Gate Between Our Agent
Code and Our Users* (21 Apr), *Agent Trust Is a System Design Problem* (23 Apr),
*Skills Are Context, and Context Needs Tests* (09 Apr), *Your Agent Is Starving*
(29 Apr), *Deterministic Automation for a Probabilistic System* (26 May), *The First
Step… Is Encoding What You Already Know* (02 Jun).

**Two corrections to what we'd captured from the talk:**
- **No numeric round-cap on the plan↔adversarial loop.** Stack *said* "five loops"
  on stage, but neither the repo nor the blog encodes a cap — the loop runs "until
  findings resolve / the human approves." Our `~5-round cap` is therefore *ours*, not
  swamp's. (Decision: keep as our own runaway-spend safeguard, or drop — see TODO.)
- **Not "5 gates on every PR."** Reality = **4 path-scoped AI reviewers** (general /
  adversarial / UX / CI-security) **+ a deps/OSV audit + a compiled-binary smoke
  test**; the expensive reviewers only fire on relevant changed paths (dorny/paths-filter).

**Verified detail worth keeping (patterns, in our words):**
- **Lifecycle = enforced state machine, not phase docs.** A `TRANSITIONS` table
  (`extensions/models/_lib/schemas.ts`) declares legal source phases per method;
  illegal jumps throw. State persists in `.swamp/` so it survives context loss. Driven
  by an `issue-lifecycle` skill backed by a CLI model. Conventions externalised to
  `agent-constraints/{triage,planning,adversarial-dimensions,implementation}.md` with
  generic fallbacks → the skill is repo-portable.
- **Programmatic pre-flight gates, not prompt requests:** `approve` is code-blocked if
  unresolved critical/high findings exist or the review is stale (`adversarial-review-clear`);
  a `pr-cooldown` blocks merge within 3 min of PR link. "Never auto-approve."
- **Adversarial reviewer, two places:** plan-time (7 dimensions; a notable encoded
  heuristic — watch "state that persists across failure boundaries") and CI-time
  (composite action, prompt "assume the code is broken until proven otherwise",
  Opus, tool-scoped to `Read/Glob/Grep` + scoped `gh pr`). Critical/high → `--request-changes`
  + `touch /tmp/review-failed` → the step fails (LLM verdict becomes a hard gate).
- **Every CI review prompt opens with an injection-hardening preamble:** the PR diff/
  title/body/comments are "UNTRUSTED USER DATA"; flag attempts to influence the review.
- **A dedicated CI-security reviewer audits the workflow files themselves** (prompt/
  expression injection, `pull_request_target`, SHA-pinning, job permissions, secret
  exposure, auto-merge trust boundary) — gated on `.github/**` changes.
- **Architecture / DDD layering / license headers are enforced as integration tests**
  (`architecture_boundary_test.ts`, `ddd_layer_rules_test.ts`, `copyright_header_test.ts`),
  plus a compiled-binary smoke test (`--version`/`--help`) catching load-time throws.
- **UAT lives in a separate repo (`systeminit/swamp-uat`)** — 3 gates run on the
  *compiled binary* before release: CLI-acceptance (88 files), adversarial "break it",
  perf benchmarks (p75 thresholds). Evidence: **3 real bugs passed unit tests, caught
  only by UAT.** Planning forces a UAT-gap assessment + a docs-gap assessment.
- **Two eval lanes:** tessl = skill *quality* (avg description+content ≥ 0.90);
  promptfoo = skill *routing/trigger* (≥ 90%, ~$2 / 30s per model). On-PR runs one
  model; a **weekly** cron runs Opus/Sonnet/GPT-5.4/Gemini-2.5-Pro as a *non-blocking*
  model-drift / provider-lock monitor.
- **Permission heuristic — "can `git checkout` undo it?"** Reversible/local → allow;
  force-push, hard reset, recursive delete, cloud mutations, PR create/merge/close →
  ask. The one checkpoint that matters is *publication* (private → public).
- **Determinism:** agents author Zod-validated *definitions* executed via a
  deterministic topological sort — no LLM at run time, so re-runs are repeatable and
  free. (Directly applicable to a scheduled bot.)
- **Isolation:** per-task git worktrees (`.claude/worktrees/`, gitignored; lifecycle
  skill passes `--repo-dir` back to the parent) **and** execution drivers (host/Docker/
  custom) so one method can't read another's output.
- **Model tiering:** Opus for adversarial/security/general review; Sonnet for UX.
- **Economics (from *Your Agent Is Starving*):** 5 devs, **zero hand-written code**,
  **~$3k/month** = ~$1k Claude Max Pro licences + ~$2k CI (4 reviews/PR + adversarial +
  skill/eval gates + UAT).
- **Adoption framing (from *Encoding What You Already Know*):** start by turning tribal
  knowledge into *enforced* constraints, on the critical path; expand as incidents
  surface new ones. "A wiki page nobody reads vs an encoded constraint that prevents it."
- **swamp-specific, NOT for us:** employee-only contribution lockout (external PRs
  auto-closed), GitHub issues funnelled off to swamp-club, `jujutsu` support.

## 5. Agent-security research, mid-2026 (added 2026-08-12)

Four independent results between June and July 2026 measured whether inspection-based
guardrails actually hold on coding agents. They don't. Full write-up, with sources and
confidence markers, in
[knowledge/security/agent-guardrail-failures-2026.md](../knowledge/security/agent-guardrail-failures-2026.md);
in one line each:

- **GuardFall** — command deny-lists inspect raw text, bash expands it first; defeated
  10 of 11 open-source coding agents. A gate must evaluate the *post-expansion* command.
- **IssueTrojanBench** — 66.5% of malicious GitHub issues penetrated every guardrail
  across Cursor, Claude Code and Codex Desktop; rejection came almost entirely from the
  LLM, not the harness. Our injection-hardening preambles contribute roughly nothing.
- **Friendly Fire** (AI Now Institute) — asking an agent to security-review an untrusted
  library *is* the exploit; injection in the README steers it into running an
  attacker-supplied script, which the permission classifier approves because it looks
  like the requested task. The authors explicitly reject human-in-the-loop (automation
  bias) and sandboxing (escape after code execution) as sufficient.
- **Skills supply chain** — `!` dynamic-context commands run *before the model sees the
  skill*, so model refusal is structurally impossible; `disableSkillShellExecution` is
  the real control.

Plus the **Claude Code GitHub Action** chain (public issue → secret/OIDC exfiltration →
push to the action's own repo → downstream propagation, patched v1.0.94), which is the
evidence for promoting "review the pipeline itself" from advice to a hard gate.

**Adopted from this (2026-08-12):** a new rule against pointing a code-executing agent
at untrusted code; post-expansion evaluation added to "gates as code"; the `!` mechanism
named in "vet skills"; automation bias upgraded from side-risk to failure mode in "human
gate on the dangerous legs"; and the trifecta check widened to the whole tool set.

## 6. Counter-evidence on the auto-merge decision (added 2026-08-12)

Recording this next to the rule because C1/C2 (full auto-merge, no mandatory human
line-by-line review) is our most consequential departure from mainstream practice, and
2026 produced the strongest evidence against it so far. **The bet stands** — it was made
deliberately, for a solo operator, with the safety burden knowingly moved onto the
gates — but it should not stand undocumented.

- **Anthropic, 2026 Agentic Coding Trends Report.** Developers use AI in roughly 60% of
  their work but report being able to "fully delegate" only **0–20% of tasks**. The
  report's own framing is "not fully delegated but highly collaborative", and one of its
  four priorities for the year is *scaling* human oversight rather than removing it:
  "the goal isn't to remove humans from the loop — it's to make human expertise count
  where it matters most." Also relevant: their prediction that oversight scales by
  agents *learning when to ask*, and that quality control itself becomes agentic.
- **DORA 2026.** ROI runs through the whole delivery flow, and code review specifically.
  Faster PR production without matching downstream capacity converts into review
  queues, rework and production risk rather than value. Removing the human review step
  doesn't remove the work — it relocates it onto the automated gates, which become the
  new flow constraint.
- **Code-review-agent research (MSR '26 and related).** The cost of false positives is
  not the seconds spent per comment; it's the team learning to skip every comment the
  tool leaves. Narrow, specific checks (security, a named convention) beat
  general-purpose review on signal ratio. Directly applicable to our adversarial
  reviewer, and now reflected in that rule.

**What changed as a result:** one carve-out, not a reversal. Auto-merge applies only to
changes originating from a **trusted source**; anything triggered by or containing
third-party content goes to `hold` for a human. That closes the specific hole §5 opened
— an injected instruction riding an inbound issue or dependency through a fully
automated merge path — without giving up the bet on everything we actually author.

**Still open:** the gates are now the only thing standing between a bad change and
`main`, and we have no measurement of whether they're catching anything. A finding-rate
or escape-rate metric on the gates would be the honest version of this decision.

## How this feeds decisions
These independently reinforce several candidate practices already in
talk-takeaways.md: deterministic guards/lints + "sensors",
scoped least-privilege permissions for CI agents, context-via-interview,
security-context files, and spec-first development. Use as supporting evidence
when deciding what to adopt.
