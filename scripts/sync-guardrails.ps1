<#
.SYNOPSIS
  Vendor the adopted guardrails into a target repo so Claude Code applies them on
  ANY machine from a plain `git clone` — no global setup, no `~` import.

    Always   : writes the rules to <repo>/.claude/rules/00-guardrails.md (Claude Code
               auto-loads it), rewriting the deep-dive links to absolute GitHub URLs
               so they resolve from any repo/machine.
    Always   : ALSO fills gaps in the target's agent-constraints/ (the "how" — triage /
               planning / adversarial / implementation / verification-and-gates, plus the
               cross-cutting issue-tracker + session-lifecycle). Copies only files the
               target is MISSING; never overwrites one it already has, since those are
               adapted per repo. So a repo onboarded months ago picks up newly-added
               constraint files on an ordinary re-sync.
    Always   : refreshes the vendored machinery (hooks, check scripts) the target
               already has -- but ONLY a file that is still byte-for-byte (line endings
               aside) some earlier version of its template. A file the target has
               changed since it was vendored is ADAPTED: it is left alone and named in
               a warning, so a re-sync never undoes a repo's own fix. (A repo that
               rolls a file back to an exact older template version is indistinguishable
               from a stale one, and is refreshed.)
    -Init    : ALSO creates agent-constraints/ and lays down the machinery when the
               target has none. Use -Init the FIRST time you onboard a repo.
    -DryRun  : prints exactly what a run would change and changes nothing.
    Always   : first fetches this guardrails checkout and REFUSES (exit 1, nothing
               written) when the commit it would copy from lacks commits that
               origin/main has - an old copy would report "up to date" against old
               rules. Offline, it warns and compares with the last-fetched origin/main.
    -AllowStale : sync from a checkout that is behind origin/main anyway.

  So: `-Init` once to lay down the full kit; plain runs afterwards to re-sync the
  rules when rules/RULES.md changes. A plain run is safe to run blind.
.EXAMPLE
  ./scripts/sync-guardrails.ps1 -Repo C:\Source\MyRepo -Init     # first-time: full kit
  ./scripts/sync-guardrails.ps1 -Repo C:\Source\MyRepo -DryRun   # what would change?
  ./scripts/sync-guardrails.ps1 -Repo C:\Source\MyRepo           # later: re-sync
  ./scripts/sync-guardrails.ps1 -Repo C:\Source\MyRepo -AllowStale  # behind origin/main, knowingly
#>
param(
  [Parameter(Mandatory = $true)] [string]$Repo,
  [switch]$Init,
  [switch]$DryRun,
  [switch]$AllowStale
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$src  = Join-Path $root 'rules/RULES.md'
if (-not (Test-Path $src))  { throw "Source rules not found: $src" }
if (-not (Test-Path $Repo)) { throw "Target repo not found: $Repo" }
$Repo = (Resolve-Path $Repo).Path
$hookSrc = Join-Path $root 'templates/hooks'

if ($DryRun) {
  Write-Host "DRY RUN - nothing will be written. Lines below say what a real run would do."
}

# --- helpers: "is this file still an unmodified copy of some template version?" ------
# Found 2026-10-05: the refresh used to overwrite ANY file that differed from the
# current template. It lowered one repo's open-issue cap, undid a merge-hook lint fix
# in three repos, and replaced another repo's pre-commit and session-start hook,
# dropping a gate. "Differs from the template" cannot tell STALE
# from ADAPTED. The template's git history can: a file whose content equals some
# version the template once had is stale and safe to refresh; anything else was edited
# in the target and is left alone.

# Compare content, not bytes on disk: a Windows checkout turns LF into CRLF and
# Set-Content may add a UTF-8 BOM. Latin-1 maps every byte to one char, so this is
# lossless apart from the two normalisations.
$latin1 = [Text.Encoding]::GetEncoding(28591)
function Get-ContentKey([byte[]]$bytes) {
  $s = $latin1.GetString($bytes)
  if ($s.StartsWith([string][char]0xEF + [char]0xBB + [char]0xBF)) { $s = $s.Substring(3) }
  $s = $s.Replace("`r`n", "`n")
  $sha = [Security.Cryptography.SHA256]::Create()
  try { return [BitConverter]::ToString($sha.ComputeHash($latin1.GetBytes($s))) }
  finally { $sha.Dispose() }
}
function Get-FileKey([string]$path) { Get-ContentKey ([IO.File]::ReadAllBytes($path)) }

# Run git and return stdout as raw bytes (PowerShell's pipeline would re-encode it).
function Get-GitBytes([string]$dir, [string]$arguments) {
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = 'git'
  $psi.Arguments = $arguments
  $psi.WorkingDirectory = $dir
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $p = [Diagnostics.Process]::Start($psi)
  $errTask = $p.StandardError.ReadToEndAsync()
  $ms = New-Object IO.MemoryStream
  $p.StandardOutput.BaseStream.CopyTo($ms)
  $p.WaitForExit()
  $null = $errTask.Result
  if ($p.ExitCode -ne 0) { return $null }
  return ,$ms.ToArray()
}

# Is the guardrails source a git checkout we can read history from? If not, only the
# CURRENT template counts as known, so every differing file is treated as adapted:
# when we cannot prove a file is stale, we do not touch it.
$haveHistory = $false
try {
  $inside = Get-GitBytes $root 'rev-parse --is-inside-work-tree'
  $haveHistory = ($null -ne $inside) -and ($latin1.GetString($inside).Trim() -eq 'true')
} catch { $haveHistory = $false }
if (-not $haveHistory) {
  Write-Host "  ! The guardrails source is not a readable git checkout - template history is"
  Write-Host "    unavailable, so any vendored file that differs from the current template is"
  Write-Host "    treated as ADAPTED and left alone."
}

# --- is this copy of the guardrails behind GitHub? -----------------------------------
# Found 2026-10-04: a local copy was two commits behind origin, so every repo it
# synced was reported "up to date" with rules that were already old. Fetch, then refuse
# when the commit we copy FROM (this checkout's HEAD - a worktree on a feature branch
# counts as its branch) lacks commits origin/main has. A branch AHEAD of main passes.
# Offline: warn and compare with the last-fetched origin/main. No origin, or no
# origin/main: say so and carry on (nothing to compare with). Not a git checkout: the
# handling above applies and this check is skipped. Runs before anything is written,
# so a refusal leaves the target untouched (a dry run is refused too: its report would
# be against old templates).
if ($haveHistory) {
  $originUrl = Get-GitBytes $root 'remote get-url origin'
  if ($null -eq $originUrl) {
    Write-Host "  ! The guardrails checkout has no 'origin' remote - cannot tell whether it is behind."
  } else {
    $oldPrompt = $env:GIT_TERMINAL_PROMPT
    $env:GIT_TERMINAL_PROMPT = '0'   # never hang on a credential prompt
    try { $fetched = Get-GitBytes $root 'fetch --quiet origin' }
    finally { $env:GIT_TERMINAL_PROMPT = $oldPrompt }
    if ($null -eq $fetched) {
      Write-Host "  ! Could not fetch origin (offline?) - comparing with the last-fetched origin/main." -ForegroundColor Yellow
    }
    $hasMain = Get-GitBytes $root 'rev-parse --verify --quiet refs/remotes/origin/main'
    if ($null -eq $hasMain) {
      Write-Host "  ! No origin/main in the guardrails checkout - cannot tell whether it is behind."
    } else {
      # If the comparison itself fails (no commits yet, a broken or shallow clone), we
      # cannot show the copy is current, so it counts as behind: fail closed.
      $behindBytes = Get-GitBytes $root 'rev-list --count HEAD..refs/remotes/origin/main'
      $behind = 0
      $howFar = $null
      if ($null -eq $behindBytes) { $howFar = 'possibly behind (git could not compare it with)' }
      else {
        $behind = [int]($latin1.GetString($behindBytes).Trim())
        if ($behind -gt 0) { $howFar = "$behind commit(s) behind" }
      }
      if ($null -ne $howFar) {
        if ($AllowStale) {
          Write-Host "  ! The guardrails checkout is $howFar origin/main - syncing anyway (-AllowStale)." -ForegroundColor Yellow
        } else {
          Write-Host ""
          Write-Host "REFUSED - this copy of the guardrails is $howFar origin/main." -ForegroundColor Red
          Write-Host "  Syncing from it would vendor old rules and report them as current." -ForegroundColor Red
          Write-Host "  Bring it up to date first:   git -C `"$root`" pull --ff-only"
          Write-Host "  Or, knowingly, re-run with:  -AllowStale"
          Write-Host "  Nothing was written."
          exit 1
        }
      }
    }
  }
}

# Every content key the template at templates/hooks/<name> has ever had, plus the
# current working copy. Follows renames. A version that only ever existed inside a
# merge commit is missed, which errs safe (the file is then treated as adapted).
$knownCache = @{}
function Get-KnownKeys([string]$name) {
  if ($knownCache.ContainsKey($name)) { return $knownCache[$name] }
  $keys = @{}
  $cur = Join-Path $hookSrc $name
  if (Test-Path $cur) { $keys[(Get-FileKey $cur)] = $true }
  if ($haveHistory) {
    $log = Get-GitBytes $root "log --format= --raw --no-abbrev --follow -- templates/hooks/$name"
    if ($null -ne $log) {
      foreach ($line in ($latin1.GetString($log) -split "`n")) {
        # :<oldmode> <newmode> <oldblob> <newblob> <status>\t<path>
        if ($line -notmatch '^:\d+ \d+ [0-9a-f]+ ([0-9a-f]+) ') { continue }
        $blob = $Matches[1]
        if ($blob -match '^0+$') { continue }   # a deletion
        $bytes = Get-GitBytes $root "cat-file blob $blob"
        if ($null -ne $bytes) { $keys[(Get-ContentKey $bytes)] = $true }
      }
    }
  }
  $knownCache[$name] = $keys
  return $keys
}

$adaptedKept = @()
# One vendored machinery file. Missing: laid down only when -Init asks. Present:
# 'current' (nothing to do), 'stale' (an old template version - refreshed) or
# 'adapted' (changed in the target - left alone, warned about).
function Sync-Machinery([string]$name, [string]$rel, [bool]$createIfMissing) {
  $source = Join-Path $hookSrc $name
  $target = Join-Path $Repo $rel
  if (-not (Test-Path $source)) { return }
  if (-not (Test-Path $target)) {
    if (-not $createIfMissing) { return }   # not onboarded for this file; -Init's job
    if ($DryRun) { Write-Host "  would add $rel"; return }
    $parent = Split-Path -Parent $target
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Copy-Item -Path $source -Destination $target
    Write-Host "  + $rel"
    return
  }
  $have = Get-FileKey $target
  if ($have -eq (Get-FileKey $source)) {
    Write-Host "  = $rel already current"
    return
  }
  if ((Get-KnownKeys $name).ContainsKey($have)) {
    if ($DryRun) { Write-Host "  would refresh $rel (an unmodified older template version)"; return }
    Copy-Item -Path $source -Destination $target -Force
    Write-Host "  ^ $rel REFRESHED (was an unmodified older template version)"
    return
  }
  $script:adaptedKept += $rel
  Write-Host "  ! $rel is ADAPTED (changed in this repo since it was vendored) - left alone" -ForegroundColor Yellow
}

# --- rules (always) ------------------------------------------------------------
$destDir = Join-Path $Repo '.claude/rules'
$dest    = Join-Path $destDir '00-guardrails.md'
$base   = 'https://github.com/trurner13/house-rules/blob/main/'
$banner = @"
<!-- VENDORED from house-rules (rules/RULES.md). Claude Code auto-loads .claude/rules/*.md every session, so this applies on ANY machine with a plain git clone. DO NOT edit here: edit the source repo and re-run scripts/sync-guardrails.ps1. Deep-dive links are rewritten to absolute GitHub URLs (the source repo). The operational HOW lives in this repo's agent-constraints/ (run the script with -Init to lay it down). -->

"@
# -Encoding UTF8 is required: Windows PowerShell 5.1 reads as ANSI by default,
# which mangles every em-dash and smart quote in the rules.
$rules = Get-Content -Raw -Encoding UTF8 -Path $src
# relative deep-dive links (](../...) ) -> absolute source-repo URLs so they resolve anywhere
$rules = $rules -replace '\]\(\.\./', "]($base"
$rulesText = $banner + $rules
# Set-Content appends one newline; what lands on disk is this.
$rulesOnDisk = $rulesText + [Environment]::NewLine
if ($DryRun) {
  $same = (Test-Path $dest) -and ((Get-Content -Raw -Encoding UTF8 -Path $dest) -ceq $rulesOnDisk)
  if ($same) { Write-Host "Rules already current -> $dest" }
  else       { Write-Host "would write rules -> $dest" }
} else {
  # The rules file is ALWAYS written: it is generated, never adapted. Read it back so a
  # write that silently did not land fails the run instead of reporting success.
  New-Item -ItemType Directory -Force -Path $destDir | Out-Null
  Set-Content -Path $dest -Value $rulesText -Encoding utf8
  if ((Get-Content -Raw -Encoding UTF8 -Path $dest) -cne $rulesOnDisk) {
    throw "Rules file did not update: $dest"
  }
  Write-Host "Synced rules -> $dest"
}

# --- agent-constraints -----------------------------------------------------------
# Every run FILLS GAPS: copies any constraint file the target doesn't have yet, and
# never overwrites one it does (those are adapted per repo). That way a repo onboarded
# months ago still picks up constraint files added since, without clobbering its edits.
# -Init additionally creates the folder on a first-time onboard.
$acSrc = Join-Path $root 'templates/agent-constraints'
$acDst = Join-Path $Repo 'agent-constraints'

$acExists = Test-Path $acDst
if (-not $acExists) {
  if ($Init) {
    if ($DryRun) {
      Write-Host "would create agent-constraints/ -> $acDst"
    } else {
      New-Item -ItemType Directory -Force -Path $acDst | Out-Null
      Write-Host "Created agent-constraints/ -> $acDst"
      $acExists = $true
    }
  } else {
    Write-Host "No agent-constraints/ in target - re-run with -Init to lay down the operational starter."
  }
}

if ($acExists -or ($Init -and $DryRun)) {
  $added = @()
  $kept  = @()
  foreach ($f in (Get-ChildItem -Path $acSrc -Filter '*.md')) {
    $target = Join-Path $acDst $f.Name
    if (Test-Path $target) {
      $kept += $f.Name
    } else {
      if (-not $DryRun) { Copy-Item -Path $f.FullName -Destination $target }
      $added += $f.Name
    }
  }
  if ($added.Count -gt 0) {
    $verb = 'Added'; if ($DryRun) { $verb = 'would add' }
    Write-Host ("$verb " + $added.Count + " new constraint file(s): " + ($added -join ', '))
  }
  if ($kept.Count -gt 0) {
    Write-Host ("Left " + $kept.Count + " existing file(s) untouched - adapt those in the target repo.")
    # ...but SAY which of them are out of date. Silence here reads as "up to date",
    # and it isn't: gap-fill never overwrites, so a constraint file rewritten
    # upstream never reaches a repo that already has the old copy. Found 2026-09-01
    # on one onboarded repo -- 7 of 8 files stale, none of them locally adapted, and nothing
    # had ever said so.
    $stale = @()
    foreach ($n in $kept) {
      if ((Get-FileKey (Join-Path $acSrc $n)) -ne (Get-FileKey (Join-Path $acDst $n))) { $stale += $n }
    }
    if ($stale.Count -gt 0) {
      Write-Host ("  ! " + $stale.Count + " of them DIFFER from the template: " + ($stale -join ', '))
      Write-Host "    If a file has no local edits (git log -- agent-constraints/<f>), it is merely"
      Write-Host "    stale: copy the template over it. If it is adapted, merge by hand."
    }
  }
}

# --- the vendored machinery: refreshed on EVERY run, created only under -Init -------
# Hook scripts and check scripts are generated machinery. A stale hook does not fail
# loudly, it silently reports the wrong thing (found 2026-08-24: a tracker gate added
# upstream never reached one onboarded repo, because only -Init refreshed). So every run refreshes
# them -- but only a file the target has NOT changed (Sync-Machinery, above). Some
# repos do adapt a hook (one repo raised its issue cap; three repos fixed a merge-hook
# lint error; another added a gate), and a re-sync must never undo that.
$machinery = @(
  @{ src = 'session-start.ps1';  dst = '.claude/hooks/session-start.ps1' },
  @{ src = 'session-end.ps1';    dst = '.claude/hooks/session-end.ps1' },
  # config-review-scan.sh names the executable-configuration paths; commit-msg and
  # pre-merge-commit both call it.
  @{ src = 'config-review-scan.sh'; dst = '.githooks/config-review-scan.sh' },
  @{ src = 'commit-msg';         dst = '.githooks/commit-msg' },
  @{ src = 'pre-commit';         dst = '.githooks/pre-commit' },
  # conflict-scan.sh is SOURCED by both hooks; pre-merge-commit closes the auto-merge
  # gap (git runs it INSTEAD of pre-commit when it commits a merge itself).
  @{ src = 'conflict-scan.sh';   dst = '.githooks/conflict-scan.sh' },
  @{ src = 'pre-merge-commit';   dst = '.githooks/pre-merge-commit' },
  # The tracker's well-formedness gate, and the completeness gate (would a fresh clone
  # of the target still work?).
  @{ src = 'check-issues.py';    dst = 'scripts/check-issues.py' },
  @{ src = 'check-committed.py'; dst = 'scripts/check-committed.py' }
)
Write-Host "Machinery:"
foreach ($m in $machinery) { Sync-Machinery $m.src $m.dst ([bool]$Init) }

# --- the rest of the kit (-Init only) ---------------------------------------------
# Rules and constraint files are INSTRUCTIONS: the agent reads them and may or may not
# comply. The hooks are the part that actually EXECUTES. Everything here is gap-fill:
# nothing is overwritten, so -Init is safe to re-run on an existing repo.
if ($Init) {
  Write-Host "Kit (-Init):"

  # Wire the SessionStart digest. Only written when the repo has no settings.json -
  # merging JSON blindly would clobber a repo's own permissions/env, so we print the
  # snippet instead.
  $settingsDst = Join-Path $Repo '.claude/settings.json'
  if (Test-Path $settingsDst) {
    Write-Host "  ! .claude/settings.json exists - NOT modified. Add the SessionStart hook by hand:"
    Write-Host "      see templates/hooks/settings.json in the guardrails repo"
  } elseif ($DryRun) {
    Write-Host "  would add .claude/settings.json (SessionStart wiring)"
  } else {
    Copy-Item -Path (Join-Path $hookSrc 'settings.json') -Destination $settingsDst
    Write-Host "  + .claude/settings.json (SessionStart wiring)"
  }

  # The issue tracker.
  $issuesDir = Join-Path $Repo 'issues'
  $keep      = Join-Path $issuesDir 'archive/.gitkeep'
  if (Test-Path $keep) {
    Write-Host "  = issues/ already present - left as-is"
  } elseif ($DryRun) {
    Write-Host "  would add issues/ and issues/archive/"
  } else {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $keep) | Out-Null
    Set-Content -Path $keep -Value 'Terminal issues (done / dropped) are moved here with `git mv`.' -Encoding utf8
    Write-Host "  + issues/ and issues/archive/"
  }

  # Activate the git hooks. core.hooksPath is LOCAL config, never committed, so this
  # has to be re-run in every clone - the procedure in ADOPTION.md says so.
  Push-Location $Repo
  try {
    $isRepo = (git rev-parse --is-inside-work-tree 2>$null)
    if ($isRepo -eq 'true') {
      $current = (git config core.hooksPath 2>$null)
      if (-not [string]::IsNullOrWhiteSpace($current)) {
        Write-Host "  = core.hooksPath already set to '$current' - left as-is"
      } elseif ($DryRun) {
        Write-Host "  would run git config core.hooksPath .githooks"
      } else {
        git config core.hooksPath .githooks
        Write-Host "  + git config core.hooksPath .githooks"
      }

      # Keep per-session worktrees out of the index.
      $gi = Join-Path $Repo '.gitignore'
      $line = '.claude/worktrees/'
      $has = $false
      if (Test-Path $gi) { $has = (Select-String -Path $gi -SimpleMatch $line -Quiet) }
      if ($has) {
        Write-Host "  = .gitignore already ignores $line"
      } elseif ($DryRun) {
        Write-Host "  would add to .gitignore: $line"
      } else {
        Add-Content -Path $gi -Value "`n# Claude Code per-session worktrees (isolated checkouts; never commit)`n$line"
        Write-Host "  + .gitignore: $line"
      }

      # Pin the git hooks to LF. Under core.autocrlf=true they check out as CRLF and a
      # "#!/bin/sh\r" shebang fails with "bad interpreter" on Linux/macOS/WSL2. Git for
      # Windows tolerates it, so this only breaks when the repo changes platform.
      $ga = Join-Path $Repo '.gitattributes'
      $gaLine = '.githooks/* text eol=lf'
      $gaHas = $false
      if (Test-Path $ga) { $gaHas = (Select-String -Path $ga -SimpleMatch '.githooks/*' -Quiet) }
      if ($gaHas) {
        Write-Host "  = .gitattributes already pins .githooks/*"
      } elseif ($DryRun) {
        Write-Host "  would add to .gitattributes: $gaLine"
      } else {
        Add-Content -Path $ga -Value "`n# Git hooks must keep LF: a CRLF shebang breaks them on Linux/macOS/WSL2`n$gaLine"
        Write-Host "  + .gitattributes: $gaLine"
      }
    } else {
      Write-Host "  ! target is not a git repo - skipped core.hooksPath and .gitignore"
    }
  } finally {
    Pop-Location
  }

  if (-not $DryRun) {
    Write-Host "Done. Commit the new files; the git hooks are active in THIS clone now,"
    Write-Host "and the SessionStart digest fires on the next Claude Code session there."
  }
}

if ($adaptedKept.Count -gt 0) {
  Write-Host ""
  Write-Host ("WARNING: " + $adaptedKept.Count + " adapted file(s) were LEFT ALONE: " + ($adaptedKept -join ', ')) -ForegroundColor Yellow
  Write-Host "  Each differs from every version its template has ever had, so the repo changed it."
  Write-Host "  To take an upstream fix, merge it by hand: compare with templates/hooks/ here."
}

# --- did any of it actually reach version control? --------------------------------
# A blanket '.claude/' (or 'issues/', or '*.py') in the target's .gitignore turns this
# whole script into a no-op that reports success: every file exists on THIS machine and
# is absent from every clone, which is the precise failure the vendoring exists to
# prevent. Found in one onboarded repo on 2026-08-24, where the kit was written, reported "Done",
# and would have vanished on the next clone.
#
# Ask git, do not pattern-match .gitignore. Negations, precedence and nested ignore
# files make the text unreliable; `git check-ignore` is the only answer that matches
# what git will actually do - the same reason a command gate must evaluate the expanded
# command rather than the raw string.
Push-Location $Repo
try {
  $isRepo = (git rev-parse --is-inside-work-tree 2>$null)
  if ($isRepo -eq 'true') {

    $mustReachGit = @('.claude/rules/00-guardrails.md')
    if ($Init) {
      $mustReachGit += @(
        '.claude/settings.json',
        '.claude/hooks/session-start.ps1',
        '.githooks/commit-msg',
        '.githooks/pre-commit',
        'scripts/check-issues.py',
        'scripts/check-committed.py',
        'agent-constraints/README.md',
        'issues/archive/.gitkeep'
      )
    }

    $ignored = @()
    foreach ($rel in $mustReachGit) {
      # In a dry run the file may not exist yet; check-ignore answers for the path anyway.
      if (-not $DryRun -and -not (Test-Path (Join-Path $Repo $rel))) { continue }
      git check-ignore -q -- $rel 2>$null
      if ($LASTEXITCODE -eq 0) { $ignored += $rel }   # 0 = git WILL ignore this path
    }

    if ($ignored.Count -gt 0) {
      Write-Host ""
      Write-Host "GITIGNORE GATE FAILED - the kit was written but git will ignore it." -ForegroundColor Red
      Write-Host ""
      Write-Host "  These files exist on this machine and would never be committed," -ForegroundColor Red
      Write-Host "  so a fresh clone gets none of the guardrails:" -ForegroundColor Red
      Write-Host ""
      foreach ($f in $ignored) {
        $rule = (git check-ignore -v -- $f 2>$null)
        if ($rule) { Write-Host "    $f" -ForegroundColor Red
                     Write-Host "        ignored by: $rule" -ForegroundColor DarkGray }
        else       { Write-Host "    $f" -ForegroundColor Red }
      }
      Write-Host ""
      Write-Host "  Fix the target's .gitignore, then re-run. COMMIT .claude/rules,"
      Write-Host "  skills, agents, hooks and settings.json; ignore only the two things"
      Write-Host "  that are genuinely per-machine:"
      Write-Host ""
      Write-Host "      .claude/settings.local.json"
      Write-Host "      .claude/worktrees/"
      Write-Host "      CLAUDE.local.md"
      Write-Host ""
      Write-Host "  A blanket '.claude/' is the usual culprit. Leave a comment saying"
      Write-Host "  why it must not come back."
      Write-Host ""
      exit 1
    }

    Write-Host "Gitignore gate: OK - every vendored file can reach version control."
  }
} finally {
  Pop-Location
}

# The loop above leaves $LASTEXITCODE from the final `git check-ignore` (1 = not
# ignored, the good case), and PowerShell would propagate that as the script's own
# exit code. Say success explicitly. The gate's own failure path exits 1 above.
exit 0
