# SessionStart hook -- prints the work-state digest into the agent's context.
#
# SessionStart cannot block anything. Its value is that stdout IS added to the
# model's context, so the session begins already holding the open issue list and
# any in-flight work -- without the agent having to decide to go looking.
#
# Output is STREAMED, section by section, most important first. The hook has a
# timeout (settings.json), and on timeout Claude Code discards everything the hook
# printed. Before 2026-10-12 this script buffered its output and printed it at the
# end, so one slow section (branches ahead of main, 224 s on a repo with 200 refs)
# lost the whole digest -- open issues included. Now a slow section can only lose
# itself and what follows it, and the slow section is last.
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

# Claude Code keeps the first 2,000 characters of hook output over 10,000 and spills the
# rest to a file. Stay under the limit so nothing important ends up in the spill.
$script:budget = 9500
$script:written = 0
$script:truncated = $false
function Emit {
  param([string[]]$lines)
  foreach ($l in $lines) {
    if ($script:truncated) { return }
    if ($script:written + $l.Length + 1 -gt $script:budget) {
      Write-Output '... (digest truncated to stay under the hook output limit)'
      $script:truncated = $true
      return
    }
    Write-Output $l
    $script:written += $l.Length + 1
  }
}

Write-Output '=== work state (session-start reconciliation) ==='
$today = (Get-Date).Date

# --- 1. trial reviews that are overdue (guardrails repo) ----------------------
# A trial has a review date, but nothing fires on a date by itself; a TODO item can wait
# months. So the digest says, at the top of every session, which reviews are past due,
# until someone decides adopt / extend / drop.
$todo = Join-Path $root 'TODO.md'
if (Test-Path $todo) {
  $text = Get-Content -Raw -Path $todo
  if ($text -match '(?s)## On trial.*?(?=\r?\n## )') {
    $section = $Matches[0]
    $overdue = @()
    foreach ($m in [regex]::Matches($section, '(?s)- \[.\] \*\*(?<name>[^*]+)\*\*.*?Review (?<date>\d{4}-\d{2}-\d{2})')) {
      $due = [datetime]$m.Groups['date'].Value
      if ($due -le $today) {
        $overdue += ("  {0}: review was due {1} ({2} day(s) ago)" -f $m.Groups['name'].Value.Trim(), $m.Groups['date'].Value, [int](($today - $due).TotalDays))
      }
    }
    if ($overdue.Count -gt 0) {
      Emit @('TRIAL REVIEW OVERDUE (TODO.md, "On trial"): the first decision of this session is adopt / extend / drop for')
      Emit $overdue
      Emit @('')
    }
  }
}

# --- 2. open issues ----------------------------------------------------------
# --untracked matters: a just-captured, unstaged issue is the one most at risk.
$issues = @(git -C "$root" grep --untracked -h -E '^# 20|^- (status|branch|next): ' -- ':(glob)issues/*.md' 2>$null)
if ($issues.Count -gt 0) {
  # A repo with forty issues and paragraph-long next: lines fills the whole output limit
  # by itself and nothing after it is seen. Each line is clipped and the section is capped;
  # the issue files hold the full text.
  Emit @('OPEN ISSUES (issues/ is the tracker; anything noticed gets a file there before the session moves on):')
  $sectionCap = 4500; $used = 0; $shown = 0
  foreach ($l in $issues) {
    $line = if ($l.Length -gt 180) { $l.Substring(0, 177) + '...' } else { $l }
    if ($used + $line.Length + 3 -gt $sectionCap) { break }
    Emit @('  ' + $line)
    $used += $line.Length + 3; $shown++
  }
  if ($shown -lt $issues.Count) {
    Emit @('  ... and ' + ($issues.Count - $shown) + ' more line(s); the rest are in issues/.')
  }
} else {
  Emit @('OPEN ISSUES: none recorded in issues/.')
}

# Catch issue files that exist but do not parse. Without this the digest reports
# "none recorded" for a malformed file, which reads as "nothing to do".
$issueDir = Join-Path $root 'issues'
if (Test-Path $issueDir) {
  $bad = @()
  foreach ($f in (Get-ChildItem -Path $issueDir -Filter '*.md' -File)) {
    $t = Get-Content -Raw -Path $f.FullName
    if (($t -notmatch '(?m)^#\s+\S') -or ($t -notmatch '(?m)^-\s+status:\s*\S')) { $bad += $f.Name }
  }
  if ($bad.Count -gt 0) {
    Emit @('', 'MALFORMED issue file(s), not counted above; each lacks the "# <id> - <title>"',
           '  heading or the "- status: <state>" line (agent-constraints/issue-tracker.md):')
    Emit @($bad | ForEach-Object { '  ' + $_ })
  }
}

# --- 3. in-flight work -------------------------------------------------------
$dirty = git -C "$root" status --porcelain=v1 -uall 2>$null
if ($dirty) {
  $n = @($dirty).Count
  Emit @('', "UNCOMMITTED: $n file(s) in this working tree. They are checkpointed onto the branch",
         '  before the turn ends; the exit does not save them.')
  Emit @(@($dirty | Select-Object -First 10) | ForEach-Object { '  ' + $_ })
  if ($n -gt 10) { Emit @('  ... and ' + ($n - 10) + ' more') }
}

$unpushed = git -C "$root" log --branches --not --remotes --oneline 2>$null
if ($unpushed) {
  Emit @('', 'UNPUSHED commits (they die with this machine):')
  Emit @(@($unpushed | Select-Object -First 10) | ForEach-Object { '  ' + $_ })
}

# --- 4. other worktrees ------------------------------------------------------
# Resume what exists rather than opening a rival.
$wt = git -C "$root" worktree list 2>$null
if (@($wt).Count -gt 1) {
  Emit @('', 'WORKTREES already exist; an existing one is resumed rather than a new one created:')
  Emit @($wt | ForEach-Object { '  ' + $_ })
}

# --- 5. rules on trial in this repo (consumer repos) --------------------------
$rulesDir = Join-Path $root '.claude\rules'
if (Test-Path $rulesDir) {
  $trials = @()
  foreach ($f in (Get-ChildItem -Path $rulesDir -Filter '*.md' -File)) {
    $first = Get-Content -Path $f.FullName -TotalCount 3 | Out-String
    if ($first -match '(?i)on trial.*?from (\d{4}-\d{2}-\d{2})') {
      $since = [datetime]$Matches[1]
      $trials += ("  {0}: on trial since {1} ({2} day(s))" -f $f.Name, $Matches[1], [int](($today - $since).TotalDays))
    }
  }
  if ($trials.Count -gt 0) {
    Emit @('', 'RULES ON TRIAL in this repo (the review is decided in the guardrails repo's tracker):')
    Emit $trials
  }
}

# --- 6. parked checkpoints and stashes ---------------------------------------
# unfold,separator= is required or a multi-line trailer breaks the parse.
$cps = git -C "$root" for-each-ref --format='%(refname:short)%09%(trailers:key=Next-Step,valueonly,unfold,separator=%x20)' refs/heads 2>$null |
       Where-Object { $_ -match "`t." }
if ($cps) {
  Emit @('', 'BRANCHES PARKED AT A CHECKPOINT (branch -> what to do next):')
  Emit @($cps | ForEach-Object { '  ' + ($_ -replace "`t", ' -> ') })
}

$stash = git -C "$root" stash list 2>$null
if ($stash) {
  Emit @('', 'STASHES exist (the stack is shared across every worktree of this repo):')
  Emit @(@($stash | Select-Object -First 5) | ForEach-Object { '  ' + $_ })
}

# --- 7. the tool itself ------------------------------------------------------
# Guardrails that depend on a Claude Code version (hooks that fail closed, path-scoped
# rules, the worktree sweep) silently do not apply on an older build. Say which one runs.
$cv = (claude --version 2>$null | Select-Object -First 1)
if ($cv) { Emit @('', "CLAUDE CODE: $cv") }

# --- 8. branches ahead of main (last: the slow section) ----------------------
# A branch that is pushed, written up and checkpointed is SAFE, and that is exactly why it
# can sit unmerged for weeks: nothing hurts. Print each branch's distance from main so the
# question "why is this not merged?" is asked with a number at the start of every session,
# not noticed in a survey weeks later.
#
# One for-each-ref gives ahead/behind and the last-commit date for every ref at once
# (git 2.41+). Only branches actually ahead cost two more git calls each, and the table
# is capped, so a repo with 200 refs no longer spends minutes here.
$base = $null
foreach ($cand in @('origin/main', 'main', 'origin/master', 'master')) {
  if (git -C "$root" rev-parse --verify --quiet "$cand" 2>$null) { $base = $cand; break }
}
if ($base) {
  $cap = 15
  $seen = @{}
  $rows = New-Object System.Collections.Generic.List[string]
  $skipped = 0
  $refs = @(git -C "$root" for-each-ref --format="%(refname:short)%09%(ahead-behind:$base)%09%(committerdate:iso-strict)" refs/heads refs/remotes/origin 2>$null)
  if ($refs.Count -eq 0 -or ($refs[0] -notmatch "`t\d+ \d+`t")) {
    Emit @('', "BRANCHES AHEAD OF ${base}: not computed (git 2.41+ is needed for %(ahead-behind)).")
  } else {
    foreach ($r in $refs) {
      $parts = $r -split "`t"
      if ($parts.Count -lt 3) { continue }
      $short = $parts[0] -replace '^origin/', ''
      if ($short -in @('main', 'master', 'HEAD')) { continue }
      if ($seen.ContainsKey($short)) { continue }   # local first; remote-only branches still count
      $seen[$short] = $true
      $ab = $parts[1] -split ' '
      $ahead = [int]$ab[0]; $behind = [int]$ab[1]
      if ($ahead -le 0) { continue }                 # merged (or empty): nothing to report
      if ($rows.Count -ge $cap) { $skipped++; continue }
      $last = [datetime]$parts[2]
      $mb = git -C "$root" merge-base "$base" "$($parts[0])" 2>$null
      $left = if ($mb) { [datetime](git -C "$root" log -1 --format=%cI "$mb" 2>$null) } else { Get-Date }
      $days = [int][math]::Floor(((Get-Date) - $left).TotalDays)
      $idle = [int][math]::Floor(((Get-Date) - $last).TotalDays)
      $flag = if ($days -gt 2 -or $ahead -gt 15) { '  <-- the merge question is open' } else { '' }
      $rows.Add(("  {0}: {1} ahead, {2} behind, left main {3} day(s) ago, last commit {4} day(s) ago{5}" -f $short, $ahead, $behind, $days, $idle, $flag))
    }
    if ($rows.Count -gt 0) {
      Emit @('', "BRANCHES AHEAD OF $base (one increment, one yes, one merge):")
      Emit $rows
      if ($skipped -gt 0) { Emit @("  ... and $skipped more unmerged branch(es) not listed (cap $cap). That many is itself the finding.") }
    }
  }
}

Write-Output '=== end work state ==='
exit 0
