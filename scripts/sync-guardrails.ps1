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
    -Init    : ALSO creates agent-constraints/ when the target has none. Use -Init the
               FIRST time you onboard a repo.

  So: `-Init` once to lay down the full kit; plain runs afterwards to re-sync the
  rules when rules/RULES.md changes (your adapted agent-constraints are left alone).
.EXAMPLE
  ./scripts/sync-guardrails.ps1 -Repo C:\Source\MyRepo -Init   # first-time: full kit
  ./scripts/sync-guardrails.ps1 -Repo C:\Source\MyRepo         # later: update rules only
#>
param(
  [Parameter(Mandatory = $true)] [string]$Repo,
  [switch]$Init
)
$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..'
$src  = Join-Path $root 'rules\RULES.md'
if (-not (Test-Path $src))  { throw "Source rules not found: $src" }
if (-not (Test-Path $Repo)) { throw "Target repo not found: $Repo" }

# --- rules (always) ------------------------------------------------------------
$destDir = Join-Path $Repo '.claude\rules'
$dest    = Join-Path $destDir '00-guardrails.md'
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$base   = 'https://github.com/trurner13/TRT-AI-guardrails/blob/main/'
$banner = @"
<!-- VENDORED from trurner13/TRT-AI-guardrails (rules/RULES.md). Claude Code auto-loads .claude/rules/*.md every session, so this applies on ANY machine with a plain git clone. DO NOT edit here: edit the source repo and re-run scripts/sync-guardrails.ps1. Deep-dive links are rewritten to absolute GitHub URLs (the source repo). The operational HOW lives in this repo's agent-constraints/ (run the script with -Init to lay it down). -->

"@
# -Encoding UTF8 is required: Windows PowerShell 5.1 reads as ANSI by default,
# which mangles every em-dash and smart quote in the rules.
$rules = Get-Content -Raw -Encoding UTF8 -Path $src
# relative deep-dive links (](../...) ) -> absolute source-repo URLs so they resolve anywhere
$rules = $rules -replace '\]\(\.\./', "]($base"
Set-Content -Path $dest -Value ($banner + $rules) -Encoding utf8
Write-Host "Synced rules -> $dest"

# --- agent-constraints -----------------------------------------------------------
# Every run FILLS GAPS: copies any constraint file the target doesn't have yet, and
# never overwrites one it does (those are adapted per repo). That way a repo onboarded
# months ago still picks up constraint files added since, without clobbering its edits.
# -Init additionally creates the folder on a first-time onboard.
$acSrc = Join-Path $root 'templates\agent-constraints'
$acDst = Join-Path $Repo 'agent-constraints'

if (-not (Test-Path $acDst)) {
  if ($Init) {
    New-Item -ItemType Directory -Force -Path $acDst | Out-Null
    Write-Host "Created agent-constraints/ -> $acDst"
  } else {
    Write-Host "No agent-constraints/ in target - re-run with -Init to lay down the operational starter."
  }
}

if (Test-Path $acDst) {
  $added = @()
  $kept  = @()
  foreach ($f in (Get-ChildItem -Path $acSrc -Filter '*.md')) {
    $target = Join-Path $acDst $f.Name
    if (Test-Path $target) {
      $kept += $f.Name
    } else {
      Copy-Item -Path $f.FullName -Destination $target
      $added += $f.Name
    }
  }
  if ($added.Count -gt 0) {
    Write-Host ("Added " + $added.Count + " new constraint file(s): " + ($added -join ', '))
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
      $a = Join-Path $acSrc $n
      $b = Join-Path $acDst $n
      if ((Get-FileHash $a).Hash -ne (Get-FileHash $b).Hash) { $stale += $n }
    }
    if ($stale.Count -gt 0) {
      Write-Host ("  ! " + $stale.Count + " of them DIFFER from the template: " + ($stale -join ', '))
      Write-Host "    If a file has no local edits (git log -- agent-constraints/<f>), it is merely"
      Write-Host "    stale: copy the template over it. If it is adapted, merge by hand."
    }
  }
}


# --- refresh generated machinery on EVERY run, not only under -Init ---------------
# The -Init block below already refreshes these, but ONLY under -Init. So a repo
# onboarded months ago never received a hook fix on an ordinary re-sync -- which
# contradicts the intent stated there, that hook scripts are REFRESHED rather than
# gap-filled precisely because "a stale hook does not fail loudly, it silently reports
# the wrong thing".
#
# Found 2026-08-24: a tracker gate was added to templates/hooks/pre-commit, an onboarded repo was
# re-synced, and the gate never arrived -- so a malformed issue file committed cleanly
# while a manual run of the same check reported the failure.
#
# This only touches files the target ALREADY has. -Init remains the thing that lays the
# kit down; this keeps an existing kit current.
$machineryRefresh = @(
  @{ src = 'session-start.ps1'; dst = '.claude\hooks\session-start.ps1' },
  @{ src = 'commit-msg';        dst = '.githooks\commit-msg' },
  @{ src = 'pre-commit';        dst = '.githooks\pre-commit' },
  @{ src = 'conflict-scan.sh';  dst = '.githooks\conflict-scan.sh' },
  @{ src = 'pre-merge-commit';  dst = '.githooks\pre-merge-commit' },
  @{ src = 'check-issues.py';   dst = 'scripts\check-issues.py' },
  @{ src = 'check-committed.py'; dst = 'scripts\check-committed.py' }
)
$refreshed = @()
foreach ($m in $machineryRefresh) {
  $target = Join-Path $Repo $m.dst
  $source = Join-Path (Join-Path $root 'templates\hooks') $m.src
  if (-not (Test-Path $target)) { continue }   # not onboarded for this file; -Init's job
  if (-not (Test-Path $source)) { continue }
  if ((Get-FileHash $source).Hash -ne (Get-FileHash $target).Hash) {
    Copy-Item -Path $source -Destination $target -Force
    $refreshed += $m.dst
  }
}
if ($refreshed.Count -gt 0) {
  Write-Host ("Refreshed stale machinery: " + ($refreshed -join ', '))
}

# --- the machinery (-Init only) ---------------------------------------------------
# Rules and constraint files are INSTRUCTIONS: the agent reads them and may or may not
# comply. The hooks below are the part that actually EXECUTES. Everything here is
# gap-fill: nothing is overwritten, so -Init is safe to re-run on an existing repo.
if ($Init) {
  $hookSrc = Join-Path $root 'templates\hooks'
  $didSomething = $false

  function Copy-IfMissing($src, $dst, $label) {
    if (Test-Path $dst) {
      Write-Host "  = $label already present - left as-is"
      return $false
    }
    $parent = Split-Path -Parent $dst
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Copy-Item -Path $src -Destination $dst
    Write-Host "  + $label"
    return $true
  }

  # Hook SCRIPTS are generated machinery, not content you adapt -- same class as
  # 00-guardrails.md. They are REFRESHED, not gap-filled: a stale hook does not fail
  # loudly, it silently reports the wrong thing (an early version resolved the repo from
  # the caller's working directory and happily described a different repository). If a
  # repo needs different behaviour, add its own hook alongside rather than editing this.
  function Copy-Always($src, $dst, $label) {
    $parent = Split-Path -Parent $dst
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $existed = Test-Path $dst
    $same = $false
    if ($existed) {
      $same = ((Get-FileHash $src).Hash -eq (Get-FileHash $dst).Hash)
    }
    Copy-Item -Path $src -Destination $dst -Force
    if (-not $existed)  { Write-Host "  + $label" }
    elseif ($same)      { Write-Host "  = $label already current" }
    else                { Write-Host "  ^ $label REFRESHED (was out of date)" }
  }

  Write-Host "Machinery (-Init):"

  # 1. SessionStart digest: prints open issues + in-flight work into the agent's context.
  Copy-Always (Join-Path $hookSrc 'session-start.ps1') (Join-Path $Repo '.claude\hooks\session-start.ps1') '.claude/hooks/session-start.ps1'

  # 2. Wire it. Only written when the repo has no settings.json - merging JSON blindly
  #    would clobber a repo's own permissions/env, so we print the snippet instead.
  $settingsDst = Join-Path $Repo '.claude\settings.json'
  if (Test-Path $settingsDst) {
    Write-Host "  ! .claude/settings.json exists - NOT modified. Add the SessionStart hook by hand:"
    Write-Host "      see templates/hooks/settings.json in the guardrails repo"
  } else {
    $null = Copy-IfMissing (Join-Path $hookSrc 'settings.json') $settingsDst '.claude/settings.json (SessionStart wiring)'
  }

  # 3. Git hooks, in a VERSIONED dir so they travel with the repo (.git/hooks does not).
  Copy-Always (Join-Path $hookSrc 'commit-msg') (Join-Path $Repo '.githooks\commit-msg') '.githooks/commit-msg'
  Copy-Always (Join-Path $hookSrc 'pre-commit') (Join-Path $Repo '.githooks\pre-commit') '.githooks/pre-commit'
  # conflict-scan.sh is SOURCED by both hooks; pre-merge-commit closes the auto-merge
  # gap (git runs it INSTEAD of pre-commit when it commits a merge itself).
  Copy-Always (Join-Path $hookSrc 'conflict-scan.sh') (Join-Path $Repo '.githooks\conflict-scan.sh') '.githooks/conflict-scan.sh'
  Copy-Always (Join-Path $hookSrc 'pre-merge-commit') (Join-Path $Repo '.githooks\pre-merge-commit') '.githooks/pre-merge-commit'

  # 3b. The tracker's well-formedness gate. Generated machinery, so refreshed like the
  #     hooks -- a stale check quietly stops catching the thing it was added for.
  Copy-Always (Join-Path $hookSrc 'check-issues.py') (Join-Path $Repo 'scripts\check-issues.py') 'scripts/check-issues.py'

  # 3c. The completeness gate: would a fresh clone of the target still work? This is
  #     the executable half of "a fresh clone is the deliverable" -- and the answer to
  #     the gitignore gate below being a one-shot check that only runs during a sync.
  Copy-Always (Join-Path $hookSrc 'check-committed.py') (Join-Path $Repo 'scripts\check-committed.py') 'scripts/check-committed.py'

  # 4. The issue tracker.
  $issuesDir = Join-Path $Repo 'issues'
  $keep      = Join-Path $issuesDir 'archive\.gitkeep'
  if (-not (Test-Path $keep)) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $keep) | Out-Null
    Set-Content -Path $keep -Value 'Terminal issues (done / dropped) are moved here with `git mv`.' -Encoding utf8
    Write-Host "  + issues/ and issues/archive/"
  } else {
    Write-Host "  = issues/ already present - left as-is"
  }

  # 5. Activate the git hooks. core.hooksPath is LOCAL config, never committed, so this
  #    has to be re-run in every clone - the procedure in ADOPTION.md says so.
  Push-Location $Repo
  try {
    $isRepo = (git rev-parse --is-inside-work-tree 2>$null)
    if ($isRepo -eq 'true') {
      $current = (git config core.hooksPath 2>$null)
      if ([string]::IsNullOrWhiteSpace($current)) {
        git config core.hooksPath .githooks
        Write-Host "  + git config core.hooksPath .githooks"
      } else {
        Write-Host "  = core.hooksPath already set to '$current' - left as-is"
      }

      # 6. Keep per-session worktrees out of the index.
      $gi = Join-Path $Repo '.gitignore'
      $line = '.claude/worktrees/'
      $has = $false
      if (Test-Path $gi) { $has = (Select-String -Path $gi -SimpleMatch $line -Quiet) }
      if (-not $has) {
        Add-Content -Path $gi -Value "`n# Claude Code per-session worktrees (isolated checkouts; never commit)`n$line"
        Write-Host "  + .gitignore: $line"
      } else {
        Write-Host "  = .gitignore already ignores $line"
      }

      # 7. Pin the git hooks to LF. Under core.autocrlf=true they check out as CRLF and a
      #    "#!/bin/sh\r" shebang fails with "bad interpreter" on Linux/macOS/WSL2. Git for
      #    Windows tolerates it, so this only breaks when the repo changes platform.
      $ga = Join-Path $Repo '.gitattributes'
      $gaLine = '.githooks/* text eol=lf'
      $gaHas = $false
      if (Test-Path $ga) { $gaHas = (Select-String -Path $ga -SimpleMatch '.githooks/*' -Quiet) }
      if (-not $gaHas) {
        Add-Content -Path $ga -Value "`n# Git hooks must keep LF: a CRLF shebang breaks them on Linux/macOS/WSL2`n$gaLine"
        Write-Host "  + .gitattributes: $gaLine"
      } else {
        Write-Host "  = .gitattributes already pins .githooks/*"
      }
    } else {
      Write-Host "  ! target is not a git repo - skipped core.hooksPath and .gitignore"
    }
  } finally {
    Pop-Location
  }

  Write-Host "Done. Commit the new files; the git hooks are active in THIS clone now,"
  Write-Host "and the SessionStart digest fires on the next Claude Code session there."
}

# --- did any of it actually reach version control? --------------------------------
# A blanket '.claude/' (or 'issues/', or '*.py') in the target's .gitignore turns this
# whole script into a no-op that reports success: every file exists on THIS machine and
# is absent from every clone, which is the precise failure the vendoring exists to
# prevent. Found in an onboarded ops repo on 2026-08-24, where the kit was written, reported "Done",
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
      if (-not (Test-Path (Join-Path $Repo $rel))) { continue }
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
