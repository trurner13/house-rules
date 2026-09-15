# Context engineering & agent memory (the CLAUDE.md → dreaming progression)

**Principle:** Treat what the model sees as a deliberately engineered, layered
system — not one big prompt. Memory should live as versioned markdown files the
agent reads on demand, and be curated over time rather than dumped in wholesale.

**Why:** Stuffing everything into context is expensive and degrades quality.
Anthropic's year of evolution went through distinct stages, each solving a limit
of the last:

1. **`CLAUDE.md` files** — static, always-loaded project instructions.
2. **Memory tools** — let the agent read/write memory during a task (in-band).
3. **Skills** — packaged, on-demand capabilities loaded only when relevant
   (the "bookshelf" analogy: you don't read every book, you pull the one you need).
4. **Filesystem-as-memory** — a directory of markdown files the agent navigates,
   so context stays lean and only relevant slices load.
5. **"Dreaming"** — an *out-of-band, asynchronous* process that reviews past
   agent transcripts, spots cross-session patterns, and proposes changes to the
   memory store (the "school/teacher" analogy: learning happens after the day,
   not mid-task).

**How to apply:**
- Use **progressive disclosure**: keep always-on context tiny; push detail into
  on-demand files/skills the agent loads only when the topic is live. *(This is
  exactly the two-layer design of this repo — see `../../rules/RULES.md` vs
  `knowledge/`.)*
- Distinguish **in-band** memory (written during a task) from **out-of-band**
  curation (reviewing transcripts later to improve the store). Don't rely on the
  agent to perfectly curate its own memory mid-task.
- When you build a memory/agent system to scale beyond one agent and session,
  enforce the **four production principles**:
  - **Versioning** — memory changes are tracked, reviewable, revertible.
  - **Concurrency** — handle simultaneous writes safely (e.g. hashing) so two
    agents don't clobber each other.
  - **Permissioning** — control who/what can read or modify which memory.
  - **Portability** — memory isn't locked to one tool/agent; it can move.
- Audit an existing memory/agent setup by walking **all** four principles plus
  the five stages in order — the value is in completeness, not cherry-picking.

## Adopted here: token efficiency (2026-09-15)

Two halves, because tokens are spent in two places.

**What loads every session** — the lean map above. `CLAUDE.md` points; it doesn't
contain. Always-on rules are one or two lines each, with the detail in files loaded
only when the topic is live. Rules files scoped to paths load only when matching files
are touched.

**How the agent works** — the habits that burn most tokens in practice:

- **Don't re-read what's already in context.** A file read earlier in the session is
  still there; re-reading it pays for it twice.
- **Read the part you need.** Jump to the section or line range rather than pulling in
  a whole large file to find one function.
- **Send broad work to a subagent.** A sweep across many files, a long test run or a
  log trawl happens in the subagent's own context; only its conclusion comes back. The
  Claude Code docs describe exactly this as the purpose of subagents.
- **Batch independent steps.** Several reads or checks that don't depend on each other
  go in one round trip, not one after another.
- **Don't write down what the model already knows.** Rules and skills carry what is
  local to your business: your conventions, your incidents, your decisions. General
  programming knowledge in a rules file is paid for in every session and adds nothing.
  (Obstbaum.)

## Adopted here: private memory holds nothing durable (2026-09-15)

**Rule:** rules, conventions, decisions, preferences and gotchas live in the repo, as
versioned markdown. They never live in the agent's per-machine memory.

**Why:** the per-machine memory (Claude Code's auto-memory under
`~/.claude/projects/<folder>/memory/`, and `CLAUDE.local.md`) fails all four production
principles above. It isn't versioned, nobody reviews it, a second machine or a second
agent can't see it, and a human never sees it at all. It is also keyed on the folder
path, so renaming or moving the repo quietly orphans it. The evidence came from a real
auto-memory, audited on 2026-09-15:

- seven notes, six of which duplicated rules already in the repo;
- one badly stale, describing the project as it had been months earlier;
- one working preference ("ask me as multiple choice, with a recommendation") written
  nowhere else. It had been working on one machine only and would have been lost with
  it. (Now in [interaction-style](interaction-style.md) §2.)

**How to apply:**

- **Switch auto-memory off in committed settings**, so it holds for everyone who
  clones: `"autoMemoryEnabled": false` in `.claude/settings.json`. On one machine only,
  the environment variable `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` does the same.
- **When the agent learns something worth keeping, it proposes a repo edit** in the
  right place, never a memory note:

  | What was learned | Where it goes |
  |---|---|
  | How the owner wants the agent to behave | [interaction-style](interaction-style.md), and `rules/RULES.md` if universal |
  | A fact about this project | `CLAUDE.md` or `SPEC.md` |
  | A non-obvious gotcha | `CLAUDE.md`'s self-improvement section or `.claude/rules/` |
  | Work not yet done | `issues/` |

- **`CLAUDE.local.md` holds only what is true of one machine**, such as a local path.
  Never a rule.
- **The user-level `~/.claude/CLAUDE.md` is a pointer to the repo, nothing more.**

**Source:** Lamis (Anthropic, Applied AI team) — "Context Engineering, Memory
Systems, and Dreaming", AI Native DevCon London, June 2026.
[Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-lamis-context-engineering-dreaming/SKILL.md)
