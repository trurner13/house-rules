# Repo structure standard

How every AI-first repo should be laid out so Claude Code (and agents) reliably
find what they need. Verified against the Claude Code documentation current at
June 2026.

## Recommended layout

```
<repo>/
├── CLAUDE.md                      # lean entry point — repo nuance only
│                                  #   (copy templates/new-repo-CLAUDE.md; guardrails auto-load from .claude/rules/)
├── .claude/
│   ├── rules/                     # modular rules, one topic per file (all auto-loaded)
│   │   ├── 00-guardrails.md       #   VENDORED shared rules — synced from TRT-AI-guardrails (don't hand-edit)
│   │   ├── <topic>.md             #   always-on (no frontmatter)
│   │   └── <area>.md              #   path-scoped: YAML `paths:` globs → loads only when matching files are touched
│   ├── skills/
│   │   └── <skill-name>/
│   │       ├── SKILL.md           # UPPERCASE; frontmatter name+description; body <500 lines
│   │       ├── references/        #   detailed docs, loaded on demand
│   │       └── evals/             #   trigger/behaviour evals
│   ├── agents/
│   │   └── <name>.md              # custom subagents — a single .md file; identity from the `name:` frontmatter
│   ├── settings.json              # team settings: permissions, hooks, env  → COMMIT
│   ├── settings.local.json        # personal / machine overrides            → GITIGNORE
│   ├── hooks/                     # hook scripts referenced by settings.json → COMMIT
│   │   └── session-start.ps1      #   prints the work-state digest into context
│   └── worktrees/                 # per-session isolated checkouts           → GITIGNORE
├── .githooks/                     # VERSIONED git hooks                      → COMMIT
│   ├── commit-msg                 #   rejects a checkpoint with no Next-Step: trailer
│   └── pre-commit                 #   refuses to commit over an unresolved conflict
│                                  #   activate per clone: git config core.hooksPath .githooks
├── agent-constraints/             # phase conventions: triage / planning / adversarial / implementation,
│                                  #   plus session-lifecycle + issue-tracker (cross-cutting)
│                                  #   (start from templates/agent-constraints/)
├── issues/                        # THE issue tracker: one file per issue    → COMMIT
│   ├── <YYYY-MM-DD-xxxx>.md       #   open issues — status, next, log
│   └── archive/                   #   done / dropped, moved with `git mv`
├── .worktreeinclude               # gitignored files to copy into each worktree (.env etc.) → COMMIT
├── .mcp.json                      # project MCP servers                      → COMMIT
└── CLAUDE.local.md                # personal project notes                   → GITIGNORE
```

## Principles (each ties to an adopted rule)

- **Lean `CLAUDE.md`** — it loads every session, so keep it small (a map, not a
  dump); push detail into `.claude/rules/` or `.claude/skills/`. *(adopted: lean grounding map)*
- **Path-scoped rules** — a file in `.claude/rules/` with `paths:` frontmatter
  (globs) loads **only** when Claude touches matching files → saves context. Rules
  without `paths:` load every session.
- **Skills are code** — `.claude/skills/<name>/SKILL.md`, single responsibility,
  committed, lint + eval'd; extend third-party skills rather than editing them. *(adopted: skills are code)*
- **Commit vs gitignore** — commit `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`,
  `.claude/agents/`, `.claude/settings.json`, `.mcp.json`, `issues/`, `.worktreeinclude`;
  gitignore `.claude/settings.local.json`, `.claude/worktrees/` and `CLAUDE.local.md`.
  No local-only setup. The same test applies to the rest of the repo — see
  [What must be committed, what may be ignored](#what-must-be-committed-what-may-be-ignored).
  *(adopted: a fresh clone is the deliverable / skills are code)*
- **The issue tracker is in the repo** — `issues/<id>.md`, one file per issue, holding
  the status and transition log for *every* open issue, not just the one being worked.
  It is the on-disk state that lets the triage→merge flow survive a new session.
  *(adopted: one issue, one file — see [agent-constraints/issue-tracker.md](agent-constraints/issue-tracker.md))*
- **Worktrees are gitignored and short-named** — Claude Code creates them under
  `.claude/worktrees/<name>/`; name them after the issue id so `--worktree <id>` reopens
  the existing one instead of creating a rival. Gitignoring keeps them out of `git
  status`; it does **not** protect them from `git clean -ffdx`, so never run that.
  `.worktreeinclude` carries `.env`-style gitignored files into each new worktree.
  *(adopted: isolated environment per agent — see [agent-constraints/session-lifecycle.md](agent-constraints/session-lifecycle.md))*
- **Hooks for hard guarantees** — anything that MUST happen every time goes in a
  hook (in `settings.json`), not an advisory rule. *(adopted: deterministic guardrails)*
- **Git hooks are versioned, not hidden.** Put them in `.githooks/` and commit them;
  `.git/hooks/` is not version-controlled, so hooks living there exist on exactly one
  machine. The catch: `core.hooksPath` is *local* config, so **every clone must run
  `git config core.hooksPath .githooks` once** or they silently do nothing. Prefer a git
  hook over a harness hook where either would work — a git hook has no override, applies
  to human commits too, and doesn't depend on the agent's version.
- **One source of truth, vendored** — the source of truth stays `rules/RULES.md` in
  the guardrails repo, but each repo carries a **synced copy** at
  `.claude/rules/00-guardrails.md` (Claude Code auto-loads it). This is what makes the
  rules work on any machine with a plain clone — no `~` import, no global setup. Don't
  hand-edit the vendored copy; re-sync it (`scripts/sync-guardrails.ps1`) when rules
  change. *(adopted: lean grounding map / single source of truth)*
- **Phase-split constraints** — keep the agent flow (triage → plan → adversarial
  review → implement) as separate files in `agent-constraints/`, alongside the two
  cross-cutting ones (`session-lifecycle.md`, `issue-tracker.md`); the lean `CLAUDE.md`
  points to the right one per phase. *(inspired by `swamp`; start from
  [agent-constraints/](agent-constraints/README.md))*
- **Verification gate** — after work, run the repo's full check/lint/format/test/
  build chain; nothing proceeds on red.
- **Auto-merge with an escape hatch** — gates green → auto-merge; a `hold` label
  blocks it when a human wants to step in.
- **Dual output mode** — every command/endpoint supports a structured
  machine-readable (JSON) output mode alongside human output. *(adopted: logs are for the agent)*

## What must be committed, what may be ignored

The test is a **fresh clone on a machine that has never seen this project**. If a
competent person — or an agent — can't clone it, run the documented setup and get a
working project, the handover has failed; and the missing piece is nearly always a file
somebody ignored on purpose and never thought about again. `.gitignore` is not a tidiness
setting. It is a promise that everything listed in it is **regenerable, per-machine, or a
secret**. Anything else in there is a defect.

### Always committed

These are the ones that actually go missing:

- **The whole `.claude/` kit** bar the two per-machine files — rules, skills, agents,
  hook scripts, `settings.json`. A blanket `.claude/` is the single most common cause of
  a broken handover: every guardrail then exists on exactly one machine. (Found in
  an onboarded ops repo, 2026-08-24 — the kit installed, reported success, and would have vanished
  on the next clone. `sync-guardrails.ps1` has failed the run on this since.)
- **`.githooks/`** — plus the activation step in the README, because `core.hooksPath` is
  *local* config: a clone that never runs `git config core.hooksPath .githooks` silently
  has no hooks at all.
- **Lock files** — `package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`, `Cargo.lock`,
  `Gemfile.lock`. Without them the next machine resolves a different dependency set, and
  "works on mine" becomes unfalsifiable.
- **`.env.example`** carrying *every* key the app reads, each with a safe default or a
  comment saying where the real value comes from. A bare `.env*` pattern eats it — see
  the negation trap below.
- **Version pins and shared editor config** — `.nvmrc`, `.tool-versions`,
  `.python-version`, `.editorconfig`, and the project-level `.vscode/settings.json` /
  `extensions.json` / `launch.json`. Ignore `.vscode/*` and re-include those three;
  never blanket-ignore the folder.
- **CI, container and infrastructure config** — workflows, `Dockerfile`, compose files,
  IaC. If the pipeline can't be rebuilt from the clone, it isn't handed over.
- **Migrations and seed data.** A schema nobody can rebuild is not a deliverable.
- **Test fixtures, golden files and small runtime assets** — routinely killed by a
  blanket `data/`, `fixtures/`, `assets/`, `*.csv` or `*.json` ignore.
- **Generated code — unless the build regenerates it.** Checked-in API clients,
  protobuf stubs, generated types. "It's generated" earns an ignore only if you can
  point at the step *in this repo* that reproduces it on a fresh clone. If you can't, it
  stopped being generated output the day the tool was last run by hand: it is now a
  source file nobody wrote, and it ships.
- **Intent, not just code** — `SPEC.md`, ADRs, `issues/`, `agent-constraints/`. Code
  without the why is a rewrite, not a handover.
- **Empty-but-required directories.** Git tracks files, not directories: commit a
  `.gitkeep` or create the directory in the setup script.

### Ignored — and nothing else

- **Real secrets** — `.env`, `*.pem`, `*.key`, service-account JSON, `.npmrc` /
  `.pypirc` holding tokens. If one is committed by accident, **rotate it**: deleting the
  file does not unpublish it, and neither does ignoring it afterwards.
- **Per-machine state** — `.claude/settings.local.json`, `CLAUDE.local.md`,
  `.idea/workspace.xml`, `.DS_Store`, `Thumbs.db`.
- **Regenerable output and caches** — `node_modules/`, `dist/`, `build/`, `target/`,
  `__pycache__/`, `.venv/`, coverage and test caches.
- **Agent scratch** — `.claude/worktrees/`.
- **Large binaries and datasets — ignored *loudly*.** They stay out of the repo (every
  clone would carry them forever, in every version they ever had), but each one gets a
  committed line saying what it is, roughly how big, where it lives, and **who grants
  access**. An ignored 2 GB dataset with no note is indistinguishable from a lost one.
  When one turns up, ask rather than assume: *should this live in shared drive storage,
  with its link committed here?* Usually yes — a link in the repo is findable by anyone
  who clones it; a file on somebody's laptop is findable by nobody. (Git LFS is the
  alternative when the file must match a specific commit.) And a link is not access:
  name the owner, or the next person gets a URL and a permission error.

Whatever a clone genuinely cannot contain — secrets, licensed data, large files — gets a
**"What this clone can't give you"** section in the README. One line each: what it is,
where it lives, who grants access. That section *is* the handover for everything the repo
can't hold, and it takes a minute to write:

```
## What this clone can't give you

- Production secrets — 1Password vault "acme-prod". Ask Dana.
- Training data (~2 GB) — Drive: <link>. Request access from Dana.
- Staging DB dump (~400 MB, refreshed weekly) — Drive: <link>. Self-serve.
```

Silence is the bug: "we're missing the training data, ask Dana" is a five-minute problem;
"something's missing and nobody knows what" is a fortnight.

### Never blanket-ignore a directory that also holds committed files

Git **cannot re-include a file whose parent directory is excluded**, so this does
nothing at all — the rules stay ignored and nothing warns you:

```
.claude/            # WRONG: excludes the directory itself
!.claude/rules/     # never reached
```

Exclude the *contents* instead, then re-include:

```
.claude/*
!.claude/rules/
!.claude/skills/
!.claude/agents/
!.claude/hooks/
!.claude/settings.json
```

The same shape applies to `.vscode/*` + `!.vscode/settings.json`, and to `.env*` +
`!.env.example`.

### Three more that fail silently

- **Machine-global ignores are invisible in the repo.** `core.excludesFile`
  (`~/.gitignore_global`) and `.git/info/exclude` are not committed and not shared. A
  file ignored there never shows up in *your* `git status` and is absent from every
  clone — precisely the "the file I expected isn't there" failure, and reading the
  repo's `.gitignore` will never explain it.
- **Ignoring never untracks; untracking is invisible.** `.gitignore` only affects files
  git isn't already tracking. `git rm --cached <file>` drops it from the repo but leaves
  it on your disk, so the author keeps working against a file that stopped existing for
  everyone else — indefinitely, with a clean `git status`.
- **A `.gitignore` copied from a template is someone else's promise.** Generic templates
  ignore `config/`, `*.local`, `data/`, `build/` — reasonable defaults that quietly eat
  a real config file, a fixture set or a checked-in build the moment your project's
  layout differs.

### Verify with git, not by reading

The `.gitignore` text is not the answer: negations, nested ignore files, precedence and
global excludes decide it. Ask git — the same reason a command gate must evaluate the
expanded command rather than the raw string.

Is a file that must ship actually reachable? (Prints the exact rule doing the ignoring;
no output means "not ignored", which is what you want.)

```bash
git check-ignore -v -- .claude/rules/00-guardrails.md .env.example package-lock.json
```

What is git hiding on this machine? Read it once before any handover — the surprises are
the point.

```bash
git ls-files --others --ignored --exclude-standard
```

Where do this machine's private ignore rules live?

```bash
git config --get core.excludesFile && cat .git/info/exclude
```

And the only honest test, which the three above merely approximate — clone into a
directory the project has never run in, then run the documented setup and the build:

```bash
git clone <repo> ../handover-check
```

Anything that fails names a file that should have been committed.

### The executable version

Three commands is three chances to forget one, and prose has already failed at this
once. `check-committed.py` runs all of it and fails loudly. It ships with
`sync-guardrails.ps1 -Init`, `pre-commit` calls it whenever the ignore surface changes,
and CI runs it on every push:

```bash
python scripts/check-committed.py             # would a fresh clone work?
python scripts/check-committed.py --ci        # CI: advisories fail too
python scripts/check-committed.py --handover  # everything git is hiding, before handover
python scripts/check-committed.py --json      # same answer, typed, for an agent
```

It asks git for every verdict and never reads `.gitignore` as text. What it emits:

| Code | Means |
|---|---|
| `IGNORED_MUST_SHIP` | A file that must ship is ignored. Names the exact rule and its source |
| `IGNORED_MUST_SHIP_DIR` | The directory is ignored, so files already in it stay but every **new** one vanishes silently |
| `MACHINE_LOCAL_IGNORE` | Hidden by `.git/info/exclude` or the machine-global excludes file — invisible in your `git status`, absent from every clone |
| `UNTRACKED_MUST_SHIP` | Exists on disk, never committed |
| `BROKEN_NEGATION` | A `!` line that cannot work because a parent directory is excluded |
| `MISSING_COUNTERPART` | A `.env` with no committed example |
| `LARGE_TRACKED_FILE` | A big file **is** committed — permanent, every clone pays forever |
| `UNDOCUMENTED_LARGE_IGNORED` | Big ignored files and no "What this clone can't give you" section |

Per-repo additions and deliberate exemptions go in a `.must-commit` file at the root —
one path or directory per line, a leading `-` to exempt. The exemption form is
load-bearing: a gate that cannot be right about a legitimate exception gets bypassed
wholesale, which is worse than one that never runs.

## To start a repo

1. Copy [`new-repo-CLAUDE.md`](new-repo-CLAUDE.md) → `<repo>/CLAUDE.md`, fill the placeholders.
2. Vendor the rules: `scripts/sync-guardrails.ps1 -Repo <path-to-repo>` (creates `.claude/rules/00-guardrails.md`). Commit it.
3. Add more `.claude/rules/` and `.claude/skills/` as the repo grows (path-scope where you can).
4. Commit `.claude/settings.json`; gitignore `.claude/settings.local.json` + `CLAUDE.local.md`.
5. Verify with `/memory` (`00-guardrails.md` loaded) and `/doctor`.
