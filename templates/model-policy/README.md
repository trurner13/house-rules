# Model triage: an optional kit

Opus stays in the main session and triages. Cheap helpers do the legwork, with the limits enforced by their tool lists and
two hooks rather than by asking nicely. **Optional, and on trial:** nothing here loads in any repo until that repo copies it
in, and the sync script does not lay it down. The reasoning, the evidence and what a trial measures are in
[opus-drives-cheaper-helpers](../../knowledge/agents/opus-drives-cheaper-helpers.md).

## What is in the kit

| File | Goes to | What it does |
|---|---|---|
| [`model-policy.md`](model-policy.md) | `.claude/rules/` | The rule and its table of tiers. Set the date on its second line |
| [`agents/scout.md`](agents/scout.md) | `.claude/agents/` | Haiku. Reads and searches: no editing, no shell |
| [`agents/light-editor.md`](agents/light-editor.md) | `.claude/agents/` | Sonnet. Edits files off the protected list: no shell |
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

No sign-off trailer is needed on `.claude/` changes (owner's decision, 2026-11-07).

## What it cannot do

- **A session cannot change its own model.** Triage decides for the helpers it starts, not for itself. That is also why whole
  sessions and streams stay on the strong model: a session always has a shell.
- **The guard can refuse only when it runs.** If uv or the script is missing, or it times out, or the folder has not been
  trusted, the edit goes through. Keep reading every diff.
- **It saves room under a plan's limits, probably not cash,** and less than you might hope: building and test runs stay on Opus.
- **Not covered:** agents inside a Workflow script, a session started from a saved preset, and a person's own model picker.
- **Stopping it:** creating `~/.claude/model-policy-off` stops the routing hook in every repo at once. The guard stays on.
