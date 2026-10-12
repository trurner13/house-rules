#!/bin/sh
# Tests for the commit-msg hook. Runs by hand and in CI:
#
#   sh templates/hooks/test-commit-msg.sh
#
# Each case writes a commit message to a temp file and runs the real hook on it.
# The hook must read the message the way git does (git interpret-trailers), so a
# Next-Step: line git files under the body is rejected. The configuration gate is
# fed its staged-file list through COMMIT_MSG_STAGED_FILES so the tests never depend
# on what happens to be staged in the repo they run in. Exits 1 on any failure.

here=$(cd "$(dirname "$0")" && pwd)
hook="$here/commit-msg"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
failures=0
n=0

# expect <pass|reject> <description> <printf format of the message>
#   (nothing sensitive staged)
expect() {
  want="$1"; what="$2"; n=$((n + 1))
  printf "$3" > "$tmp/msg$n"
  if COMMIT_MSG_STAGED_FILES="src/app.py" sh "$hook" "$tmp/msg$n" 2>/dev/null; then got=pass; else got=reject; fi
  if [ "$got" = "$want" ]; then
    echo "PASS  $what ($want)"
  else
    echo "FAIL  $what: wanted $want, got $got"
    failures=$((failures + 1))
  fi
}

# expect_staged <pass|reject> <description> <staged files, newline-separated> <message>
expect_staged() {
  want="$1"; what="$2"; n=$((n + 1))
  printf "$4" > "$tmp/msg$n"
  if COMMIT_MSG_STAGED_FILES="$3" sh "$hook" "$tmp/msg$n" 2>/dev/null; then got=pass; else got=reject; fi
  if [ "$got" = "$want" ]; then
    echo "PASS  $what ($want)"
  else
    echo "FAIL  $what: wanted $want, got $got"
    failures=$((failures + 1))
  fi
}

# Good checkpoints.
expect pass   "trailer alone"                      'wip(x): park it\n\nNext-Step: re-run the suite\n'
expect pass   "trailer beside Co-Authored-By"       'wip(x): park it\n\nSome body.\n\nNext-Step: re-run the suite\nCo-Authored-By: A <a@example.invalid>\n'
expect pass   "Co-Authored-By first, then trailer"  'wip(x): park it\n\nCo-Authored-By: A <a@example.invalid>\nNext-Step: re-run the suite\n'
expect pass   "a --- line in the body"              'wip(x): park it\n\nNotes\n---\nmore notes\n\nNext-Step: re-run the suite\n'
expect pass   "comment lines after the trailer"     'wip(x): park it\n\nNext-Step: re-run the suite\n# Please enter the commit message for your changes.\n# Lines starting with # will be ignored.\n'
expect pass   "CRLF line endings"                   'wip(x): park it\r\n\r\nSome body.\r\n\r\nNext-Step: re-run the suite\r\nCo-Authored-By: A <a@example.invalid>\r\n'
expect pass   "key in another case"                 'wip(x): park it\n\nnext-step: re-run the suite\n'

# Malformed checkpoints.
expect reject "no Next-Step at all"                 'wip(x): park it\n\nSome body.\n\nCo-Authored-By: A <a@example.invalid>\n'
expect reject "Next-Step in the body, blank line before Co-Authored-By" 'wip(x): park it\n\nNext-Step: re-run the suite\n\nCo-Authored-By: A <a@example.invalid>\n'
expect reject "Next-Step mid-body"                  'wip(x): park it\n\nNext-Step: re-run the suite\n\nMore body after it.\n'
expect reject "Next-Step on the subject's paragraph" 'wip(x): park it\nNext-Step: re-run the suite\n'
expect reject "empty value"                         'wip(x): park it\n\nNext-Step:\n'
expect reject "blank value"                         'wip(x): park it\n\nNext-Step:   \n'
expect reject "empty value, CRLF"                   'wip(x): park it\r\n\r\nNext-Step: \r\nCo-Authored-By: A <a@example.invalid>\r\n'
expect reject "only in a comment line"              'wip(x): park it\n\nBody.\n# Next-Step: re-run the suite\n'
expect reject "editor message, leading blank line"  '\nwip(x): park it\n\nBody.\n'
expect reject "editor message, leading comment"     '# Please enter the commit message\nwip(x): park it\n\nBody.\n'
expect pass   "editor message, leading comment, good" '# Please enter the commit message\nwip(x): park it\n\nNext-Step: re-run the suite\n'

# Not governed by the checkpoint gate.
expect pass   "an ordinary commit"                  'docs: tidy\n\nNo trailer needed.\n'
expect pass   "a fixup! of a checkpoint"            'fixup! wip(x): park it\n'

# The executable-configuration gate: a person signs for hooks, agent settings, MCP
# lists, workflows and lockfiles, whatever the subject line says.
sig='Config-Reviewed-By: A Person <a@example.invalid>'
expect_staged reject "a hook change, unsigned"            '.githooks/pre-commit'                 'hooks: tighten\n\nBody.\n'
expect_staged pass   "a hook change, signed"              '.githooks/pre-commit'                 "hooks: tighten\n\n$sig\n"
expect_staged reject "agent settings, unsigned"           '.claude/settings.json'                'settings: add hook\n'
expect_staged reject "a nested .claude file, unsigned"    'apps/web/.claude/hooks/x.ps1'         'settings: add hook\n'
expect_staged reject "an MCP server list, unsigned"       '.mcp.json'                            'mcp: add server\n'
expect_staged reject "a workflow, unsigned"               '.github/workflows/ci.yml'             'ci: faster\n'
expect_staged reject "a lockfile, unsigned"               'package-lock.json'                    'deps: bump\n'
expect_staged reject "CLAUDE.md, unsigned"                'CLAUDE.md'                            'docs: instructions\n'
expect_staged reject "a fixup! that touches a hook, unsigned" '.githooks/commit-msg'             'fixup! hooks: tighten\n'
expect_staged reject "signature in the body, not a trailer" '.githooks/pre-commit'               "hooks: tighten\n\n$sig\n\nMore body after it.\n"
expect_staged reject "signature with no name"             '.githooks/pre-commit'                 'hooks: tighten\n\nConfig-Reviewed-By:\n'
expect_staged pass   "mixed change, signed"               '.claude/settings.json\nsrc/app.py'    "feat: x\n\n$sig\nCo-Authored-By: A <a@example.invalid>\n"
expect_staged pass   "a signed checkpoint touching a hook" '.githooks/pre-commit'                "wip(x): park it\n\nNext-Step: finish\n$sig\n"
expect_staged reject "a checkpoint touching a hook, signed but no Next-Step" '.githooks/pre-commit' "wip(x): park it\n\n$sig\n"
expect_staged pass   "ordinary source files, unsigned"    'src/app.py\ndocs/readme.md'           'feat: x\n'
expect_staged pass   "a path that merely contains the word claude" 'src/claude_client.py'       'feat: x\n'
expect_staged pass   "nothing staged"                     ''                                     'feat: x\n'

if [ "$failures" -gt 0 ]; then
  echo "$failures of $n check(s) FAILED"
  exit 1
fi
echo "All $n checks passed."
