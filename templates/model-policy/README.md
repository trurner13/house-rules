# Model triage: an optional kit

Opus stays in the main session and triages. Cheap helpers do the legwork, with the limits enforced by their tool lists and
two hooks rather than by asking nicely. **Optional:** nothing here loads in any repo until that repo copies it in, and the sync
script does not lay it down. It enforces the adopted rule *Triage the models and agents for each job*. The reasoning, the evidence and what to measure are in
[opus-drives-cheaper-helpers](../../knowledge/agents/opus-drives-cheaper-helpers.md).

## What is in the kit

| File | Goes to | What it does |
|---|---|---|
| [`model-policy.md`](model-policy.md) | `.claude/rules/` | The rule and its table of tiers. Set the date on its second line |
| [`agents/scout.md`](agents/scout.md) | `.claude/agents/` | Haiku. Reads and searches: no editing, no shell |
| [`agents/light-editor.md`](agents/light-editor.md) | `.claude/agents/` | Sonnet. Edits files off the protected list: no shell |
| [`agents/reviewer.md`](agents/reviewer.md) | `.claude/agents/` | Any model, named per call. Reviews read-only: no editing, no shell, no web, so the three-model review can run on Opus, Sonnet and Haiku |
| [`agents/web-researcher.md`](agents/web-researcher.md) | `.claude/agents/` | Sonnet. Web only: it cannot read the repo, so private data, untrusted content and a way out never meet in one agent |
| [`hooks/check-helper-model.py`](hooks/check-helper-model.py) | `.claude/hooks/` | Refuses a built-in helper with no model named, a cheap model on anything but its own helper, and a cheap model on a whole session |
| [`hooks/guard-light-editor.py`](hooks/guard-light-editor.py) | `.claude/hooks/` | Refuses `light-editor`'s edits to a protected path, at the moment of editing |
| [`protected-paths.txt`](protected-paths.txt) | `.claude/` | The list the guard reads. **Add your repo's own paths** |

[`test-model-policy-hooks.py`](test-model-policy-hooks.py) holds both hooks to their cases, and stays here.

## How to adopt it

1. Copy the files as the table says.
2. Add your repo's own paths to `.claude/protected-paths.txt`: money, sends, sign-in, secrets, data access, migrations,
   infrastructure, tests that guard those, and **every script and template**, in any folder (`*.js`, `*.ts` and the like). A
   `*` crosses folders. Check the list against real files: a list written from memory leaves the dangerous file open.
3. Add this to `hooks.PreToolUse` in `.claude/settings.json`, keeping everything already there:

   ```json
   {
     "matcher": "Agent|mcp__ccd_session__start_session|mcp__ccd_session_mgmt__set_session_model",
     "hooks": [
       {
         "type": "command",
         "command": "uv",
         "args": ["run", "--no-sync", "python", "${CLAUDE_PROJECT_DIR}/.claude/hooks/check-helper-model.py"],
         "timeout": 30
       }
     ]
   }
   ```

4. Add one line to `agent-constraints/triage-conventions.md`, before its last step: name the model for any helper, from
   `.claude/rules/model-policy.md`.
5. **Prove it with real calls**, in a session started after the files are committed. A helper with no model is refused. Haiku on
   `Explore` is refused. `scout` reports no shell. `light-editor` makes one allowed edit and has one refused. Delete the file
   the allowed edit made.

## What it cannot do

- **A session cannot change its own model.** Triage decides for the helpers it starts, not for itself. That is also why whole
  sessions and streams stay on the strong model: a session always has a shell.
- **The guard can refuse only when it runs.** If uv or the script is missing, or it times out, or the folder has not been
  trusted, the edit goes through. Keep reading every diff.
- **It saves room under a plan's limits, probably not cash,** and less than you might hope: building and test runs stay on Opus.
- **Not covered:** agents inside a Workflow script, a session started from a saved preset, a person's own model picker,
  and a plugin's helpers (`plugin:name`): the hook reads helper definitions only from the repo's and the user's
  `.claude/agents/`. A helper named like one of the kit's (`scout`, `reviewer`, `light-editor`, `web-researcher`) runs on a
  cheap model only if every file that could define it, in the repo's or the user's `.claude/agents/` at any depth, is in
  the kit's own plain format (one-line `name:`, `model:` and `tools:`, no more tools than the kit's). The hook does not
  parse YAML, so anything else is refused rather than guessed at: keep the kit's files as they are.
- **It catches mistakes, not a repo author dodging their own policy.** A helper file written to disguise its name
  (YAML escapes such as `"\x73cout"`, a name split across lines) can get past it. Whoever can write
  `.claude/agents/` can also switch the hook off, so the hook is a routing aid, not a security boundary.
- **Stopping it:** creating `~/.claude/model-policy-off` stops the routing hook in every repo at once. The guard stays on.
