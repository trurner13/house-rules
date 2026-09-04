#!/bin/sh
# The SUBSTANTIVE conflict checks, shared by pre-commit and pre-merge-commit.
#
# These are what actually protect the branch: unresolved content must never
# reach a commit. Being mid-operation is not itself the hazard -- finishing a
# RESOLVED merge is a legitimate commit, and blocking it only teaches people to
# reach for --no-verify, which also disables commit-msg.
#
# Exits 1 with an explanation, 0 if the staged content is clean.

fail=0

# Unmerged paths still staged.
if git diff --cached --name-only --diff-filter=U | grep -q .; then
  echo "REJECTED: unresolved conflicts are staged:" >&2
  git diff --cached --name-only --diff-filter=U | sed 's/^/    /' >&2
  fail=1
fi

# Conflict markers in staged content. Deliberately does NOT check '=======',
# which is a legitimate line in reStructuredText and Markdown headings.
markers=$(git diff --cached -U0 --no-color | grep -nE '^\+(<<<<<<<|>>>>>>>)([[:space:]]|$)' || true)
if [ -n "$markers" ]; then
  echo "REJECTED: conflict markers in staged content:" >&2
  printf '%s\n' "$markers" | head -n 10 | sed 's/^/    /' >&2
  fail=1
fi

exit "$fail"
