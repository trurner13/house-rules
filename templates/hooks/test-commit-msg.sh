#!/bin/sh
# Tests for the commit-msg hook. Runs by hand and in CI:
#
#   sh templates/hooks/test-commit-msg.sh
#
# Each case writes a commit message to a temp file and runs the real hook on it.
# The hook must read the message the way git does (git interpret-trailers), so a
# Next-Step: line git files under the body is rejected. Exits 1 on any failure.

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

# No sign-off gate (removed 2026-11-07, owner's decision): a hook or lockfile change
# commits with no Config-Reviewed-By: trailer.
expect_staged pass   "a hook and lockfile change, no sign-off" '.githooks/pre-commit
uv.lock' 'hooks: tidy

Co-Authored-By: A <a@example.invalid>
'
expect_staged reject "a checkpoint touching a hook still needs Next-Step" '.githooks/pre-commit' 'wip(x): park it

Body.
'

if [ "$failures" -gt 0 ]; then
  echo "$failures of $n check(s) FAILED"
  exit 1
fi
echo "All $n checks passed."
