#!/bin/sh
# Names the files in a change that a HUMAN must read before they land.
#
# Reads file paths on stdin (one per line), prints the ones that run before anyone
# reads them or decide what the agent may do, and exits 1 if there were any.
# Sourced by commit-msg and pre-merge-commit; runs by hand as
#   git diff --cached --name-only | sh .githooks/config-review-scan.sh
#
# Why this exists: these files are executable configuration. A committed
# SessionStart hook runs the moment a clone is opened; an MCP server entry decides
# which tools the agent trusts; a workflow runs with the repo's secrets; a lockfile
# decides what gets installed. In 2026 each was used as the attack: Miasma (5 Jun)
# rode a hijacked contributor account into 73 Microsoft repos through committed
# .claude/settings.json hooks; Deadbugz (10 Aug) added an MCP server by ordinary pull
# request that behaved for three calls and then harvested credentials. "From a
# trusted source" was true both times. So these paths get a person's eyes whoever --
# or whatever -- wrote the change. See agent-constraints/verification-and-gates.md.
#
# Add a pattern here, not an exception: the list is the policy.

grep -E \
  -e '(^|/)\.claude/' \
  -e '(^|/)\.mcp\.json$' \
  -e '(^|/)\.githooks/' \
  -e '(^|/)\.github/workflows/' \
  -e '(^|/)\.github/actions/' \
  -e '(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|poetry\.lock|uv\.lock|Pipfile\.lock|Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock|packages\.lock\.json)$' \
  -e '(^|/)(CLAUDE|AGENTS|CLAUDE\.local)\.md$' \
  -e '(^|/)\.cursor/' \
  -e '(^|/)\.gemini/' \
  -e '(^|/)\.vscode/(settings|tasks)\.json$' \
  -e '(^|/)\.devcontainer/' \
  && exit 1
exit 0
