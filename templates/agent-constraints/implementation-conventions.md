# Implementation conventions

General conventions for the **implement** phase. Add repo/stack-specific rules in
the repo's own `.claude/rules/` (these are the language-agnostic baseline).

- **Check altitude, not just the diff.** Every turn, restate what the task is *for*
  and check the next action against the issue/spec. If it doesn't move that goal,
  stop and say so — don't polish, generalise or micro-optimise your way into a
  cul-de-sac. If the work shows the spec is wrong, change the spec; never drift
  from it silently.
- **Escapes collapse when you write a file through a shell heredoc.** A `\n` in the
  generating script becomes a real newline before your code ever sees it. This repo
  has shipped a literal backspace, a literal NUL and three broken `printf` lines that
  way. When generating source that must CONTAIN an escape sequence, compose it
  (`chr(92) + "n"`) or use a file-writing tool, then read back what actually landed.
- **Small blast radius.** Change only what the task needs; don't refactor adjacent
  code that isn't part of it.
- **Structured output.** Every command/endpoint supports a machine-readable output
  mode (e.g. JSON) alongside human output — logs and errors are written for the
  agent to parse and act on (see the agent-readable-logging rule).
- **No fire-and-forget async.** Await or explicitly handle every promise; pass a
  cancellation/timeout signal on outbound calls so the caller controls it.
- **Cross-platform paths.** Use the platform's path APIs; never hand-roll with
  string slicing (`split('/')`, `lastIndexOf`, etc.). Code must run on Linux/macOS/Windows.
- **Tests next to source**, named to describe behaviour. Refactors that touch shared
  constants/paths/contracts must add integration tests so components still work together.
- **License header** on every source file (if the repo requires one) — automate it.
- **Verification gate** — after the work, run the repo's full check/lint/format/test/
  build chain; nothing proceeds on red.
- **Checkpoint as you go.** Don't hold work in the working tree across a turn boundary:
  `git add -A` and commit a `wip(...)` checkpoint with a `Next-Step:` trailer on the
  feature branch, then push. Never `git commit -am` — it skips new files. **`add -A`
  stages whatever `.gitignore` missed and the push then publishes it**, so don't
  automate this until the repo's ignore rules are verified and a secret scan runs in
  `pre-commit`. A checkpoint is a parked state, not progress: it may be red, but it must
  never be *merged* red. See [session-lifecycle.md](session-lifecycle.md).
- **Keep the issue current.** When the state changes, update `status:` and `next:` in
  the issue file in the same commit as the code. They can't drift if they move together.
