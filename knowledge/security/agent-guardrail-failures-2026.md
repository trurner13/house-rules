# What 2026 proved about coding-agent guardrails

**Principle:** Guardrails that work by *inspecting* what the agent is about to do —
command deny-lists, prompt-injection classifiers, "treat this as untrusted" preambles —
have now been measured, repeatedly, by independent groups. They fail often enough that
none of them can be the thing you rely on. Only controls that sit **outside** the agent
and remove the capability hold up.

**Why:** Until mid-2026 the case for boundary-level isolation was mostly argued from
first principles. It is now argued from numbers, and the numbers are worse than the
argument was. Four results between June and July 2026 attack four different layers —
the shell parser, the agent framework, the permission classifier, and the skill
loader — and all four conclude the same thing: **the inspection layer is not where
safety lives.** This note is the evidence base for the rule changes that followed.

Read it alongside [tal-skills-security](tal-skills-security.md) (the lethal trifecta)
and the "isolate at the boundary, not in the prompt" rule, which this material
promotes from a good idea to the only defensible position.

## The four results

### 1. GuardFall — text deny-lists don't survive the shell

Pattern-based command guards inspect the raw command string. Bash then expands,
unquotes and rewrites that string before running it. The two never see the same
command, so decades-old shell-quoting tricks walk straight through. Adversa AI
demonstrated this against **10 of 11** popular open-source coding agents (~548k GitHub
stars between them).

It is architectural, not a bug in any one product — patching a single tool's deny-list
does not close it. The one agent that held up parses the command the way bash will,
*then* decides, and keeps a hard list of destructive commands blocked outright.

**What it changes:** a command gate must evaluate the command **post-expansion**. A
regex over the literal text is decoration.

### 2. IssueTrojanBench — the harness contributes almost nothing

Researchers hid malicious instructions inside ordinary-looking GitHub issues and ran
them against Cursor, Claude Code and Codex Desktop, across six delivery vectors: PDFs,
external websites, source-code comments, image metadata, issue comments, and the issue
body itself. **66.5% penetrated every guardrail**, agent-level and model-level combined.

The finding that matters most for how we build: **rejection came almost entirely from
the LLM, not the agent framework.** Whatever the harnesses are doing, it is not
detectable in the results.

**What it changes:** "the agent will treat it as untrusted because we told it to" is
an instruction, and instructions are exactly the layer measured here at near-zero
contribution. Keep the preamble — it costs nothing — but never count it as a control.

### 3. Friendly Fire — reviewing untrusted code *is* the attack

The one that lands hardest on our own rules, because it attacks the **defensive**
workflow we advocate.

Setup: a compromised third-party library, and the prompt "perform security testing on
this package." The injection is two-layer. A `security.sh` script and a `code_policies`
binary sit in the repo alongside a decoy source file (the researchers embedded snippets
from the decoy into the binary, because agents commonly disassemble binaries to check
them). The activation is one innocent line in the `README.md`: running the security
checker usually surfaces important issues.

The agent reads the README, concludes that running the script is part of the review it
was asked to do, and executes it. The permission classifier approves, because on its
face this *is* the requested task. Result: code execution, no human prompt.

Confirmed on Claude Sonnet 4.6, Sonnet 5, Opus 4.8 and GPT-5.5/Codex. The attack
transferred between models unmodified — it is a property of the agent design, not of
any model.

The authors' own conclusions are blunt, and two of them cut against positions we hold:

- **They reject human-in-the-loop as a mitigation**, citing automation bias and prompt
  fatigue, and note that operators without security expertise would not recognise the
  compromise even if shown it.
- **They consider sandboxing insufficient**, since achieved code execution can be
  escaped via known vulnerabilities.
- Their actual recommendation: do not let an agent with code execution or access to
  security-critical environments ingest untrusted data at all.

**What it changes:** we now hold a rule that says exactly that. Reviewing a dependency,
a third-party repo or an inbound PR means dropping the execution or dropping the input.
Note the asymmetry — reviewing *your own* branch, written by your own agent from your
own spec, is not this. The exposure begins at third-party content.

### 4. The skills supply chain — execution before the model sees anything

A skill's `!` dynamic-context commands execute **at load time, before the model is
shown the skill at all**, and `allowed-tools` frontmatter (e.g. `Bash(*)`) pre-approves
tools before the rendered skill reaches the model. Model-level refusal is therefore
structurally impossible, not merely unreliable: by the time Claude could object, the
command has run. Datadog demonstrated credential theft this way (`gh auth token`
exfiltrated to an attacker-controlled host), and observed inconsistent detection across
versions — one model spotted it, another executed it without comment.

There is a real control: **`disableSkillShellExecution`** in managed settings replaces
those commands with a placeholder instead of running them. *(Verified against the
Claude Code settings docs, August 2026.)* Alongside it: review `.claude/**` changes
like code, including nested directories, and look for network tools in dynamic context,
unrestricted Bash grants, and external URLs.

Marketplace hygiene is genuinely bad — reports of a "ClawHavoc" campaign planting
hundreds of poisoned packages, 71 overtly malicious skills found on one marketplace,
and 13.4% of skills carrying at least one critical issue. *(Second-hand figures; treat
as indicative of the direction, not as precise.)* Enabled plugins persist across
sessions, so one install keeps shaping agent behaviour indefinitely.

**What it changes:** our "vet skills like untrusted dependencies" rule names the
mechanism now, because the mechanism is what makes the usual reassurance false.

## The supply-chain case: Claude Code GitHub Action

Not a guardrail failure so much as the thing guardrails are for. A flaw in the official
Claude Code GitHub Action (found by RyotaK / GMO Flatt Security, patched in v1.0.94)
chained an authorization bypass, indirect prompt injection and environment-variable
exfiltration: **open a public issue → exfiltrate secrets and OIDC tokens → push code
into the action's own repository → propagate to every downstream dependent.** No novel
technique; well-understood weaknesses composed. Microsoft's security team wrote it up
as the reference case for CI/CD in an agentic world.

Our "review the pipeline itself" rule anticipated this class. This is the evidence for
making it a hard gate rather than advice, especially anywhere auto-merge is on.

## The common vocabulary: OWASP Top 10 for Agentic Applications 2026

Published December 2025, ASI01–ASI10: agent goal hijack, tool misuse, identity, supply
chain, code execution, memory, inter-agent communication, cascading failures,
human–agent trust, rogue agents. Built from real incidents rather than projections.

Useful to us as a **checklist to map our rules against** — a periodic gap analysis
during the scheduled drift review — not as ten more rules to adopt.

## What this adds up to

1. **Remove the capability, don't inspect the request.** Every result here defeats an
   inspector. None of them defeat an agent that simply could not run the command.
2. **The gate must see what actually executes.** Post-expansion, post-render,
   post-load — whatever layer runs last is the only honest place to check.
3. **Untrusted input is the trigger in every case.** GuardFall needs an attacker-chosen
   command; the other three need attacker-chosen content. Controlling *where content
   comes from* is the highest-leverage single control we have.
4. **Approval prompts are not a safety layer at volume.** Cited by researchers as a
   failure mode. A gate that fires constantly is a gate that gets clicked through.

**Related:** [tal-skills-security](tal-skills-security.md),
[katsioloudes-code-security-ai](katsioloudes-code-security-ai.md),
[cloudflare-supabase-posthog](../stacks/cloudflare-supabase-posthog.md) (the same
failure modes on a specific stack), [findings-to-guardrails](../ways-of-working/findings-to-guardrails.md).

**Source:** Researched August 2026. Primary sources read directly: the
[Friendly Fire exploit brief](https://ainowinstitute.org/publications/friendly-fire-exploit-brief)
(AI Now Institute, Boyan Milanov & Heidy Khlaaf, 8 Jul 2026);
[IssueTrojanBench](https://arxiv.org/abs/2607.20759) (Concordia University, arXiv
2607.20759); [Datadog Security Labs on malicious skills](https://securitylabs.datadoghq.com/articles/malicious-skills-supply-chain-risks-in-coding-agents-with-dynamic-context/);
Claude Code settings documentation. Read via secondary reporting only — verify before
leaning hard on the details: GuardFall (Adversa AI, Omer Ben Simon, 30 Jun 2026, via
[The Hacker News](https://thehackernews.com/2026/06/guardfall-exposes-open-source-ai-coding.html)),
the [Claude Code GitHub Action chain](https://flatt.tech/research/posts/poisoning-claude-code-one-github-issue-to-break-the-supply-chain/),
and the skills-marketplace figures.
