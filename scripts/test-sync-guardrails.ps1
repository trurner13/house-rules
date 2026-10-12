<#
.SYNOPSIS
  Tests for sync-guardrails.ps1. Runs by hand, no Pester needed:

    powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/test-sync-guardrails.ps1

  Builds a throwaway guardrails repo (with template history) and throwaway target
  repos in the temp folder, runs the real sync script against them, and checks:
    - an unchanged vendored file (an older template version) is refreshed;
    - an adapted file is left alone and warned about (plain run and -Init);
    - the rules file 00-guardrails.md is always written, even over hand edits;
    - -DryRun changes nothing and says what it would do;
    - with no template history to prove a file stale, nothing is overwritten;
    - a guardrails checkout behind origin/main is refused (also as a dry run) and
      writes nothing, unless -AllowStale; a branch ahead of main passes; offline, it
      compares with the last-fetched origin/main.
  Exits 1 on any failure. Never touches a real repo.
#>
$ErrorActionPreference = 'Stop'
$sync = Join-Path $PSScriptRoot 'sync-guardrails.ps1'
$exe  = (Get-Process -Id $PID).Path
$tmp  = Join-Path ([IO.Path]::GetTempPath()) ("sync-test-" + [Guid]::NewGuid().ToString('N').Substring(0, 8))
$failures = 0

function Check([bool]$ok, [string]$what) {
  if ($ok) { Write-Host "PASS  $what" }
  else     { Write-Host "FAIL  $what" -ForegroundColor Red; $script:failures++ }
}
function Put([string]$path, [string]$text) {
  $parent = Split-Path -Parent $path
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [IO.File]::WriteAllText($path, $text)   # UTF-8, no BOM, exactly these bytes
}
function Text([string]$path) { [IO.File]::ReadAllText($path) }
function TGit([string]$dir) {
  $a = @('-C', $dir, '-c', 'user.name=sync-test', '-c', 'user.email=sync-test@example.invalid',
         '-c', 'core.autocrlf=false', '-c', 'core.hooksPath=') + $args
  & git @a 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') failed in $dir" }
}
function Snapshot([string]$dir) {
  $h = @{}
  Get-ChildItem -Path $dir -Recurse -File -Force |
    Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' } |
    ForEach-Object { $h[$_.FullName] = (Get-FileHash $_.FullName).Hash }
  return $h
}
function Run-Sync([string]$guard, [string]$repo, [string[]]$extra) {
  # The script's stderr must reach the checks as text, not abort this test.
  $ErrorActionPreference = 'Continue'
  $out = & $exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $guard 'scripts/sync-guardrails.ps1') -Repo $repo @extra 2>&1 | Out-String
  return @{ code = $LASTEXITCODE; out = $out }
}

try {
  # --- a fake guardrails repo whose templates have two versions in history ---------
  $guard = Join-Path $tmp 'guard'
  Put (Join-Path $guard 'rules/RULES.md') "# Rules v1`n- a rule [x](../knowledge/x.md)`n"
  Put (Join-Path $guard 'templates/agent-constraints/README.md') "constraints`n"
  Put (Join-Path $guard 'templates/hooks/pre-commit') "#!/bin/sh`necho pre-commit v1`n"
  Put (Join-Path $guard 'templates/hooks/check-issues.py') "CAP = 60  # v1`n"
  Put (Join-Path $guard 'templates/hooks/session-start.ps1') "'session v1'`n"
  Put (Join-Path $guard 'templates/hooks/commit-msg') "#!/bin/sh`necho msg v1`n"
  Put (Join-Path $guard 'templates/hooks/settings.json') "{}`n"
  New-Item -ItemType Directory -Force -Path (Join-Path $guard 'scripts') | Out-Null
  Copy-Item $sync (Join-Path $guard 'scripts/sync-guardrails.ps1')
  TGit $guard init -q
  TGit $guard add -A
  TGit $guard commit -q -m v1
  Put (Join-Path $guard 'templates/hooks/pre-commit') "#!/bin/sh`necho pre-commit v2`n"
  Put (Join-Path $guard 'templates/hooks/check-issues.py') "CAP = 60  # v2`n"
  Put (Join-Path $guard 'templates/hooks/session-start.ps1') "'session v2'`n"
  TGit $guard add -A
  TGit $guard commit -q -m v2
  # A third version that only exists in the working copy (uncommitted) is the current one.
  Put (Join-Path $guard 'templates/hooks/commit-msg') "#!/bin/sh`necho msg v2`n"

  # --- a target repo vendored at v1, partly adapted since -------------------------
  $t = Join-Path $tmp 'target'
  Put (Join-Path $t '.githooks/pre-commit') "#!/bin/sh`r`necho pre-commit v1`r`n"      # v1, CRLF checkout: unchanged
  Put (Join-Path $t 'scripts/check-issues.py') "CAP = 210  # v1, raised here`n"        # adapted
  Put (Join-Path $t '.claude/hooks/session-start.ps1') "'session v1'`n'our extra gate'`n" # adapted
  Put (Join-Path $t '.githooks/commit-msg') ([char]0xFEFF + "#!/bin/sh`necho msg v1`n")  # v1 with a BOM: unchanged
  Put (Join-Path $t '.claude/rules/00-guardrails.md') "hand edited - must be replaced`n"
  Put (Join-Path $t 'agent-constraints/README.md') "our own constraints`n"
  TGit $t init -q
  TGit $t add -A
  TGit $t commit -q -m vendored

  # 1. Dry run: nothing changes, and it says what would.
  $before = Snapshot $t
  $r = Run-Sync $guard $t @('-DryRun')
  $after = Snapshot $t
  $same = ($before.Count -eq $after.Count) -and -not ($before.Keys | Where-Object { $before[$_] -ne $after[$_] })
  Check ($r.code -eq 0) "dry run exits 0"
  Check $same "dry run changes no file"
  Check ($r.out -match 'would refresh \.githooks/pre-commit') "dry run names the stale file it would refresh"
  Check ($r.out -match 'would write rules') "dry run says it would write the rules"
  Check ($r.out -match 'scripts/check-issues\.py is ADAPTED') "dry run warns about the adapted file"

  # 2. Plain run.
  $r = Run-Sync $guard $t @()
  Check ($r.code -eq 0) "plain run exits 0"
  Check ((Text (Join-Path $t '.githooks/pre-commit')) -ceq "#!/bin/sh`necho pre-commit v2`n") "unchanged vendored file (CRLF) is refreshed"
  Check ((Text (Join-Path $t '.githooks/commit-msg')) -ceq "#!/bin/sh`necho msg v2`n") "unchanged vendored file (BOM) is refreshed to an uncommitted current template"
  Check ((Text (Join-Path $t 'scripts/check-issues.py')) -ceq "CAP = 210  # v1, raised here`n") "adapted check script is left alone"
  Check ((Text (Join-Path $t '.claude/hooks/session-start.ps1')) -ceq "'session v1'`n'our extra gate'`n") "adapted session hook is left alone"
  Check ($r.out -match 'WARNING: 2 adapted file\(s\) were LEFT ALONE') "plain run warns about both adapted files"
  $rules = [IO.File]::ReadAllText((Join-Path $t '.claude/rules/00-guardrails.md'))
  Check ($rules -match '# Rules v1' -and $rules -match 'VENDORED') "rules file is written over a hand edit"
  Check ($rules -match '\]\(https://github\.com/trurner13/house-rules/blob/main/knowledge/x\.md\)') "rules links are made absolute"
  Check ((Text (Join-Path $t 'agent-constraints/README.md')) -ceq "our own constraints`n") "existing constraint file is left alone"

  # 3. Rules change upstream: the next plain run writes them again.
  Put (Join-Path $guard 'rules/RULES.md') "# Rules v2`n"
  $r = Run-Sync $guard $t @()
  Check ($r.code -eq 0 -and (Text (Join-Path $t '.claude/rules/00-guardrails.md')) -match '# Rules v2') "rules file is rewritten when the rules change"

  # 4. -Init on the same repo: adapted files still survive; missing ones are laid down.
  $r = Run-Sync $guard $t @('-Init')
  Check ($r.code -eq 0) "-Init exits 0"
  Check ((Text (Join-Path $t 'scripts/check-issues.py')) -ceq "CAP = 210  # v1, raised here`n") "-Init leaves the adapted check script alone"
  Check ((Text (Join-Path $t '.claude/hooks/session-start.ps1')) -ceq "'session v1'`n'our extra gate'`n") "-Init leaves the adapted session hook alone"
  Check ($r.out -match 'WARNING: 2 adapted file\(s\) were LEFT ALONE') "-Init warns about both adapted files"
  Check (Test-Path (Join-Path $t 'issues/archive/.gitkeep')) "-Init lays down the tracker"

  # 5. -Init -DryRun on an empty repo changes nothing.
  $e = Join-Path $tmp 'empty'
  New-Item -ItemType Directory -Force -Path $e | Out-Null
  TGit $e init -q
  $r = Run-Sync $guard $e @('-Init', '-DryRun')
  $files = @(Get-ChildItem -Path $e -Recurse -File -Force | Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' })
  Check ($files.Count -eq 0) "-Init -DryRun on an empty repo writes nothing"
  Check ($r.out -match 'would add \.githooks/pre-commit') "-Init -DryRun says what it would add"

  # 6. No template history (the guardrails copy is not a git checkout): an old version
  #    cannot be proved stale, so it is kept, and the rules are still written.
  $bare = Join-Path $tmp 'guard-nogit'
  Copy-Item -Recurse $guard $bare
  Remove-Item -Recurse -Force (Join-Path $bare '.git')
  $n = Join-Path $tmp 'target-nohistory'
  Put (Join-Path $n '.githooks/pre-commit') "#!/bin/sh`necho pre-commit v1`n"
  TGit $n init -q
  $r = Run-Sync $bare $n @()
  Check ((Text (Join-Path $n '.githooks/pre-commit')) -ceq "#!/bin/sh`necho pre-commit v1`n") "without history, a differing file is not overwritten"
  Check ($r.code -eq 0 -and $r.out -match '\.githooks/pre-commit is ADAPTED') "without history, it exits 0 and warns"
  Check (Test-Path (Join-Path $n '.claude/rules/00-guardrails.md')) "without history, the rules are still written"

  # 7. Fetch first. A guardrails checkout cloned from an "upstream" that then moves on.
  $up = Join-Path $tmp 'upstream'
  Put (Join-Path $up 'rules/RULES.md') "# Rules v1`n"
  Put (Join-Path $up 'templates/agent-constraints/README.md') "constraints`n"
  Put (Join-Path $up 'templates/hooks/pre-commit') "#!/bin/sh`necho pre-commit v1`n"
  New-Item -ItemType Directory -Force -Path (Join-Path $up 'scripts') | Out-Null
  Copy-Item $sync (Join-Path $up 'scripts/sync-guardrails.ps1')
  TGit $up init -q -b main
  TGit $up add -A
  TGit $up commit -q -m v1
  $g = Join-Path $tmp 'guard-clone'
  TGit $tmp clone -q $up $g
  $s = Join-Path $tmp 'target-stale'
  New-Item -ItemType Directory -Force -Path $s | Out-Null
  TGit $s init -q

  $r = Run-Sync $g $s @()
  Check ($r.code -eq 0 -and $r.out -notmatch 'REFUSED') "a checkout level with origin/main syncs"

  Put (Join-Path $up 'rules/RULES.md') "# Rules v2 upstream`n"
  TGit $up add -A
  TGit $up commit -q -m v2
  $before = Snapshot $s
  $r = Run-Sync $g $s @()
  $after = Snapshot $s
  $same = ($before.Count -eq $after.Count) -and -not ($before.Keys | Where-Object { $before[$_] -ne $after[$_] })
  Check ($r.code -eq 1 -and $r.out -match 'REFUSED - this copy of the guardrails is 1 commit\(s\) behind') "a checkout behind origin/main is refused, exit 1"
  Check $same "a refused run writes nothing"
  $r = Run-Sync $g $s @('-DryRun')
  Check ($r.code -eq 1 -and $r.out -match 'REFUSED') "a dry run from a stale checkout is refused too"
  $r = Run-Sync $g $s @('-AllowStale')
  Check ($r.code -eq 0 -and $r.out -match 'syncing anyway \(-AllowStale\)') "-AllowStale syncs a stale checkout and says so"
  Check ((Text (Join-Path $s '.claude/rules/00-guardrails.md')) -match '# Rules v1') "-AllowStale used the local (old) rules"

  # A feature branch that has main's commits plus its own passes; one that lacks them does not.
  TGit $g checkout -q -b feature
  TGit $g merge -q --ff-only origin/main
  Put (Join-Path $g 'rules/RULES.md') "# Rules v3 on a branch`n"
  TGit $g commit -q -am v3
  $r = Run-Sync $g $s @()
  Check ($r.code -eq 0 -and $r.out -notmatch 'REFUSED') "a branch ahead of origin/main syncs"
  Check ((Text (Join-Path $s '.claude/rules/00-guardrails.md')) -match '# Rules v3') "it syncs from the checked-out branch"

  # Offline: the fetch fails, so it compares with the last-fetched origin/main.
  Put (Join-Path $up 'rules/RULES.md') "# Rules v4 upstream`n"
  TGit $up add -A
  TGit $up commit -q -m v4
  TGit $g remote set-url origin (Join-Path $tmp 'no-such-remote')
  $r = Run-Sync $g $s @()
  Check ($r.code -eq 0 -and $r.out -match 'Could not fetch origin') "offline, it warns and uses the last-fetched origin/main (not behind it)"
  $first = (& git -C $g rev-list --max-parents=0 HEAD | Out-String).Trim()   # v1, behind the fetched v2
  TGit $g checkout -q -b old $first
  $r = Run-Sync $g $s @()
  Check ($r.code -eq 1 -and $r.out -match 'Could not fetch origin' -and $r.out -match 'REFUSED') "offline and behind the last-fetched origin/main, it refuses"

  # A comparison git cannot make (a branch with no commits yet) fails closed.
  TGit $g checkout -q --orphan unborn
  $r = Run-Sync $g $s @()
  Check ($r.code -eq 1 -and $r.out -match 'REFUSED - this copy of the guardrails is possibly behind') "when git cannot compare, it refuses"
} finally {
  if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
}

if ($failures -gt 0) { Write-Host "$failures check(s) FAILED" -ForegroundColor Red; exit 1 }
Write-Host "All checks passed."
exit 0
