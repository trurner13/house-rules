# SessionEnd hook -- archives the session transcript so it outlives Claude Code's cleanup.
#
# OPT-IN. The kit's settings.json does not wire this hook; a repo that wants the
# archive adds the block below to .claude/settings.json (the sync lays the script
# down either way). Before opting in, know what it keeps: every session transcript,
# in full -- code, command output, file contents and everything the agent read --
# written unencrypted to a folder in the user's home directory, kept with no purge.
#
#   "SessionEnd": [
#     {
#       "hooks": [
#         {
#           "type": "command",
#           "command": "powershell",
#           "args": [
#             "-NoProfile",
#             "-ExecutionPolicy",
#             "Bypass",
#             "-File",
#             "${CLAUDE_PROJECT_DIR}/.claude/hooks/session-end.ps1"
#           ],
#           "timeout": 10
#         }
#       ]
#     }
#   ]
#
# Why this exists: the rule "Retain all agent sessions end-to-end" was prose until
# 2026-10-12. Claude Code deletes local transcripts after `cleanupPeriodDays` (30 by
# default), so every session older than a month was being lost. settings.json now sets
# a long retention period AND this hook copies each transcript out of Claude Code's own
# store, which the retention sweep never touches.
#
# Where: <user profile>\.claude\session-archive\<repo-name>\<session-id>.jsonl
#   - per machine, never inside the repo: a transcript holds code, command output and
#     everything the agent read, which is private data under the lethal-trifecta rule.
#   - the raw JSONL format is internal to Claude Code and changes between versions; the
#     archive is for a future consolidation pass to parse, not a stable contract.
#
# SessionEnd cannot block and shares a 1.5 s budget unless the hook sets its own timeout
# (the block above gives this one 10 s). It may never fire (a killed process); the archive
# is best-effort and the retention setting is the backstop.
#
# Wired, when opted in, in .claude/settings.json. See agent-constraints/session-lifecycle.md.

$ErrorActionPreference = 'SilentlyContinue'

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }
$in = $raw | ConvertFrom-Json
$src = $in.transcript_path
if (-not $src -or -not (Test-Path $src)) { exit 0 }

$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$root = (git -C "$here" rev-parse --show-toplevel 2>$null)
$repo = if ($root) { Split-Path -Leaf $root } else { 'unknown-repo' }

# ($HOME is a read-only automatic variable in PowerShell; do not assign to it.)
$userHome = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
$dir = Join-Path (Join-Path (Join-Path $userHome '.claude') 'session-archive') $repo
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$id = if ($in.session_id) { $in.session_id } else { [IO.Path]::GetFileNameWithoutExtension($src) }
$dst = Join-Path $dir ("{0}{1}" -f $id, [IO.Path]::GetExtension($src))
Copy-Item -Path $src -Destination $dst -Force
exit 0
