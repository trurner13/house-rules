# SessionStart hook -- prints the work-state digest into the agent's context.
#
# SessionStart cannot block anything. Its value is that stdout IS added to the
# model's context, so the session begins already holding the open issue list and
# any in-flight work -- without the agent having to decide to go looking.
#
# Wired in .claude/settings.json. See agent-constraints/session-lifecycle.md.

$ErrorActionPreference = 'SilentlyContinue'

# Resolve the repo from THIS SCRIPT'S location, never the caller's working directory.
# Using the cwd means the script silently prints nothing when run from anywhere else --
# and a hook that fails silently is worse than no hook, because it looks installed.
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$root = (git -C "$here" rev-parse --show-toplevel 2>$null)
if (-not $root) {
  Write-Output "session-start: '$here' is not inside a git repository - no work-state digest."
  exit 0
}

$out = New-Object System.Collections.Generic.List[string]

# --- open issues -------------------------------------------------------------
# --untracked matters: a just-captured, unstaged issue is the one most at risk.
$issues = git -C "$root" grep --untracked -h -E '^# 20|^- (status|branch|next): ' -- ':(glob)issues/*.md' 2>$null
if ($issues) {
  $out.Add('OPEN ISSUES (issues/ is the tracker; capture anything you notice before moving on):')
  foreach ($l in $issues) { $out.Add('  ' + $l) }
} else {
  $out.Add('OPEN ISSUES: none recorded in issues/.')
}

# Catch issue files that exist but do not parse. Without this the digest reports
# "none recorded" for a malformed file, which reads as "nothing to do".
$issueDir = Join-Path $root 'issues'
if (Test-Path $issueDir) {
  $bad = @()
  foreach ($f in (Get-ChildItem -Path $issueDir -Filter '*.md' -File)) {
    $text = Get-Content -Raw -Path $f.FullName
    if (($text -notmatch '(?m)^#\s+\S') -or ($text -notmatch '(?m)^-\s+status:\s*\S')) {
      $bad += $f.Name
    }
  }
  if ($bad.Count -gt 0) {
    $out.Add('')
    $out.Add('MALFORMED issue file(s) - not counted above. Each needs an "# <id> - <title>"')
    $out.Add('  heading and a "- status: <state>" line (see agent-constraints/issue-tracker.md):')
    foreach ($b in $bad) { $out.Add('  ' + $b) }
  }
}

# --- in-flight work ----------------------------------------------------------
$dirty = git -C "$root" status --porcelain=v1 -uall 2>$null
if ($dirty) {
  $n = @($dirty).Count
  $out.Add('')
  $out.Add("UNCOMMITTED: $n file(s) in this working tree. Checkpoint them onto the branch")
  $out.Add('  before the turn ends -- do not leave them for the exit.')
  foreach ($l in @($dirty | Select-Object -First 10)) { $out.Add('  ' + $l) }
  if ($n -gt 10) { $out.Add('  ... and ' + ($n - 10) + ' more') }
}

$unpushed = git -C "$root" log --branches --not --remotes --oneline 2>$null
if ($unpushed) {
  $out.Add('')
  $out.Add('UNPUSHED commits (they die with this machine):')
  foreach ($l in @($unpushed | Select-Object -First 10)) { $out.Add('  ' + $l) }
}

# --- other worktrees ---------------------------------------------------------
# Resume what exists rather than opening a rival.
$wt = git -C "$root" worktree list 2>$null
if (@($wt).Count -gt 1) {
  $out.Add('')
  $out.Add('WORKTREES -- reconcile before creating another; resume one of these instead:')
  foreach ($l in $wt) { $out.Add('  ' + $l) }
}

# --- parked checkpoints ------------------------------------------------------
# unfold,separator= is required or a multi-line trailer breaks the parse.
$cps = git -C "$root" for-each-ref --format='%(refname:short)%09%(trailers:key=Next-Step,valueonly,unfold,separator=%x20)' refs/heads 2>$null |
       Where-Object { $_ -match "`t." }
if ($cps) {
  $out.Add('')
  $out.Add('BRANCHES PARKED AT A CHECKPOINT (branch -> what to do next):')
  foreach ($l in $cps) { $out.Add('  ' + ($l -replace "`t", ' -> ')) }
}

$stash = git -C "$root" stash list 2>$null
if ($stash) {
  $out.Add('')
  $out.Add('STASHES exist (the stack is shared across every worktree of this repo):')
  foreach ($l in @($stash | Select-Object -First 5)) { $out.Add('  ' + $l) }
}

if ($out.Count -gt 0) {
  Write-Output '=== work state (session-start reconciliation) ==='
  $out | ForEach-Object { Write-Output $_ }
  Write-Output '=== end work state ==='
}

exit 0
