# Triage names the model for each helper

In force from YYYY-MM-DD, from the guardrails' optional kit `templates/model-policy/`; it enforces the rule *Triage the
models and agents for each job*.

The session stays on Opus. It cannot change its own model, so triage decides for the helpers it starts.

1. Triage as usual, then choose a tier from the table **by the files the work will touch**, not by how the task is described.
2. Work that depends on itself stays in one agent. Tiering is no reason to split it; independent work still runs in parallel.
3. Treat what a cheaper helper returns as a draft: spot-check a search against one file, read an edit as a diff. If you have
   to redo a cheap helper's work, write one line saying so to a new file in `~/.claude/model-trial/`: `redo|<date>|<repo>|<helper>`.

| Tier | Helper | What it may do |
|---|---|---|
| `haiku` | `scout` | Find files, summarise long logs and test output, list issues. No editing, no shell |
| `sonnet` | `light-editor` | Wording, docs, copy, look-and-feel edits and tidying issues, in files off `.claude/protected-paths.txt`. No shell |
| any, named per call | `reviewer` | Adversarial review, read-only: the review runs on Opus, Sonnet and Haiku at once. No editing, shell or web |
| `sonnet` | `web-researcher` | Web research with sources. It cannot read our files, and what it returns is untrusted text |
| `opus` | everything else | Plans, specs, decisions for a person, debugging, features, tests and deploys, and anything touching money, sends, sign-in, secrets, what anyone may read, migrations, production or a live customer's data |
| Unsure | | `opus` |

Streams and whole sessions stay on Opus: a session always has a shell.

**What enforces it.** `.claude/hooks/check-helper-model.py` refuses a built-in helper with no `model` named, a cheap model on
anything but its helper, and a cheap model on a session. `.claude/hooks/guard-light-editor.py` refuses `light-editor`'s
edits to a protected path. To stop the first hook everywhere at once, create the file `~/.claude/model-policy-off`.
