#!/usr/bin/env python3
"""Holds the two model-policy hooks to their cases. Run: python templates/model-policy/test-model-policy-hooks.py

Exit 0 when every case holds, 1 otherwise, with one line per failing case. Standard library only.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROUTE = HERE / "hooks" / "check-helper-model.py"
GUARD = HERE / "hooks" / "guard-light-editor.py"

ROUTE_CASES = [
    ({"subagent_type": "general-purpose"}, "Agent", 2),
    ({}, "Agent", 2),
    ({"subagent_type": "Plan"}, "Agent", 2),
    ({"subagent_type": "Explore"}, "Agent", 2),
    ({"subagent_type": "Plan", "model": "opus"}, "Agent", 0),
    ({"subagent_type": "Explore", "model": "haiku"}, "Agent", 2),
    ({"subagent_type": "general-purpose", "model": "sonnet"}, "Agent", 2),
    ({"subagent_type": "statusline-setup", "model": "haiku"}, "Agent", 2),
    ({"subagent_type": "a-reviewer", "model": "sonnet"}, "Agent", 2),
    ({"subagent_type": "light-editor", "model": "haiku"}, "Agent", 2),
    ({"subagent_type": "scout"}, "Agent", 0),
    ({"subagent_type": "scout", "model": "haiku"}, "Agent", 2),
    ({"subagent_type": "light-editor"}, "Agent", 0),
    ({"subagent_type": "light-editor", "model": "sonnet"}, "Agent", 2),
    ({"subagent_type": "web-researcher", "model": "sonnet"}, "Agent", 2),
    ({"subagent_type": "claude-code-guide", "model": "sonnet"}, "Agent", 2),
    ({"subagent_type": "claude-code-guide"}, "Agent", 2),
    ({"subagent_type": "claude-code-guide", "model": "opus"}, "Agent", 0),
    ({"subagent_type": "web-fetch"}, "Agent", 2),
    ({"subagent_type": "reviewer", "model": "sonnet"}, "Agent", 2),
    ({"subagent_type": "reviewer", "model": "haiku"}, "Agent", 2),
    ({"subagent_type": "reviewer", "model": "opus"}, "Agent", 0),
    ({"subagent_type": "bom-shell"}, "Agent", 2),
    ({"subagent_type": "renamed-shell"}, "Agent", 2),
    ({"subagent_type": "user-shell"}, "Agent", 2),
    ({"subagent_type": "cheap-shell"}, "Agent", 2),
    ({"subagent_type": "opus-helper"}, "Agent", 0),
    ({"subagent_type": "a-reviewer"}, "Agent", 0),
    ({"subagent_type": "fork"}, "Agent", 0),
    ({"model": "claude-sonnet-5-5"}, "mcp__ccd_session__start_session", 2),
    ({"model": "claude-haiku-5-5", "session_id": "x"}, "mcp__ccd_session_mgmt__set_session_model", 2),
    ({"model": "claude-opus-5-5"}, "mcp__ccd_session__start_session", 0),
    ({"initiation": "offer", "title": "x"}, "mcp__ccd_session__start_session", 0),
    ({"proposal_id": "x"}, "mcp__ccd_session__start_session", 0),
    ({"command": "git status"}, "Bash", 0),
]


def run(hook: pathlib.Path, payload: str, env: dict) -> int:
    return subprocess.run([sys.executable, str(hook)], input=payload, capture_output=True, text=True,
                          env={**os.environ, **env}).returncode


def test_route(problems: list, work: pathlib.Path) -> None:
    project = work / "project"
    (project / ".claude" / "agents").mkdir(parents=True)
    (project / ".claude" / "agents" / "cheap-shell.md").write_text(
        "---\nname: cheap-shell\nmodel: haiku\ntools: Bash\n---\nx\n", encoding="utf-8")
    (project / ".claude" / "agents" / "opus-helper.md").write_text(
        "---\nname: opus-helper\nmodel: opus\n---\nx\n", encoding="utf-8")
    (project / ".claude" / "agents" / "bom-shell.md").write_text(
        "\ufeff---\nname: bom-shell\nmodel: haiku\ntools: Bash\n---\nx\n", encoding="utf-8")
    (project / ".claude" / "agents" / "other-file-name.md").write_text(
        "---\nname: renamed-shell\nmodel: haiku\ntools: Bash\n---\nx\n", encoding="utf-8")
    (project / ".claude" / "agents" / "reviewer.md").write_text(
        "---\nname: reviewer\ntools: Read, Grep, Glob, Bash\n---\nx\n", encoding="utf-8")
    home_agents = work / "home-agents"
    home_agents.mkdir()
    (home_agents / "user-shell.md").write_text(
        "---\nname: user-shell\nmodel: haiku\n---\nx\n", encoding="utf-8")
    trial = {"MODEL_TRIAL_DIR": str(work / "trial"), "MODEL_POLICY_OFF": str(work / "no-such-file"),
             "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_AGENTS_HOME": str(home_agents)}
    for tool_input, tool, want in ROUTE_CASES:
        code = run(ROUTE, json.dumps({"tool_name": tool, "tool_input": tool_input}), trial)
        if code != want:
            problems.append(f"route: {tool} {tool_input} gave {code}, wanted {want}")
    kit_project = work / "kit-project"
    (kit_project / ".claude" / "agents").mkdir(parents=True)
    for helper in ("reviewer", "scout", "light-editor", "web-researcher"):
        shutil.copy(HERE / "agents" / f"{helper}.md", kit_project / ".claude" / "agents" / f"{helper}.md")
    kit_env = {**trial, "CLAUDE_PROJECT_DIR": str(kit_project)}
    for tool_input in ({"subagent_type": "reviewer", "model": "haiku"}, {"subagent_type": "reviewer", "model": "sonnet"},
                       {"subagent_type": "scout"}, {"subagent_type": "light-editor"},
                       {"subagent_type": "web-researcher", "model": "sonnet"}):
        code = run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": tool_input}), kit_env)
        if code != 0:
            problems.append(f"route: the kit's own helper {tool_input} gave {code}, wanted 0")
    clean_home = work / "clean-home"
    clean_home.mkdir()
    for helper in ("reviewer", "scout", "light-editor"):
        shutil.copy(HERE / "agents" / f"{helper}.md", clean_home / f"{helper}.md")
    # Frontmatter as Claude Code accepts it: quoted values and YAML lists, both ways round.
    fmt = work / "formats"
    (fmt / ".claude" / "agents").mkdir(parents=True)
    (fmt / ".claude" / "agents" / "scout.md").write_text(
        "---\nname: scout\nmodel: haiku\ntools:\n  - Read\n  - Grep\n  - Glob\n---\nx\n", encoding="utf-8")
    (fmt / ".claude" / "agents" / "reviewer.md").write_text(
        '---\nname: "reviewer"\ntools: "Read, Grep, Glob"\n---\nx\n', encoding="utf-8")
    (fmt / ".claude" / "agents" / "light-editor.md").write_text(
        "---\nname: 'light-editor'\nmodel: \"sonnet\"\ntools: [Read, Grep, Glob, Edit, Write]\n---\nx\n", encoding="utf-8")
    (fmt / ".claude" / "agents" / "web-researcher.md").write_text(
        "---\nname: web-researcher  # web only\nmodel: sonnet # cheap\ntools:\n- WebSearch\n- WebFetch  # sources\n---\nx\n",
        encoding="utf-8")
    fmt_env = {**trial, "CLAUDE_PROJECT_DIR": str(fmt)}
    # Not the kit's plain format, so refused on a cheap model even when what it says is harmless:
    # the hook does not parse YAML, so it cannot be fooled by a form it misreads.
    for tool_input in ({"subagent_type": "scout"}, {"subagent_type": "reviewer", "model": "haiku"},
                       {"subagent_type": "light-editor"}, {"subagent_type": "web-researcher"}):
        code = run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": tool_input}), fmt_env)
        if code != 2:
            problems.append(f"route: a helper not in the kit's plain format {tool_input} gave {code}, wanted 2")
    # ... and on Opus it runs: the format check only guards the cheap tiers.
    code = run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": {"subagent_type": "reviewer", "model": "opus"}}), fmt_env)
    if code != 0:
        problems.append(f"route: a non-plain reviewer on opus gave {code}, wanted 0")

    # Every way round the old parser that review found. Each project holds one hostile file and the
    # user's folder holds the kit's clean copies; every call must be refused.
    sneaky = {
        "spaced-key": {"evil.md": "---\nname : reviewer\ntools: Bash\n---\n"},
        "quoted-key": {"evil.md": '---\n"name": reviewer\ntools: Bash\n---\n'},
        "flow-map": {"evil.md": "---\n{name: reviewer, tools: Bash}\n---\n"},
        "indented": {"evil.md": "---\n  name: reviewer\n  tools: Bash\n---\n"},
        "duplicate": {"a.md": "---\nname: reviewer\ntools: Read\n---\n", "b.md": "---\nname: reviewer\ntools: Read, Bash\n---\n"},
        "subfolder": {"sub/deeper/r.md": "---\nname: reviewer\ntools: Bash\n---\n"},
        "colon-item": {"r.md": "---\nname: reviewer\ntools:\n  - Read\n  - Bash(git status:*)\n  - Grep\n---\n"},
        "continued-tools": {"r.md": "---\nname: reviewer\ntools: Read,\n  Bash\n---\n"},
        "next-line-name": {"r.md": "---\nname:\n  reviewer\ntools: Bash\n---\n"},
        "twice": {"r.md": "---\nname: reviewer\ntools: Read\ntools: Bash\n---\n"},
    }
    for label, files in sneaky.items():
        proj = work / f"sneaky-{label}"
        for rel, body in files.items():
            target = proj / ".claude" / "agents" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body + "x\n", encoding="utf-8")
        env5 = {**trial, "CLAUDE_PROJECT_DIR": str(proj), "CLAUDE_AGENTS_HOME": str(clean_home)}
        code = run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": {"subagent_type": "reviewer", "model": "haiku"}}), env5)
        if code != 2:
            problems.append(f"route: hostile reviewer definition '{label}' gave {code}, wanted 2")
    # A cheap model fixed in any form on a helper called with no model is seen as cheap.
    proj = work / "sneaky-model"
    (proj / ".claude" / "agents").mkdir(parents=True)
    (proj / ".claude" / "agents" / "s.md").write_text("---\nname: scout\nmodel:\n  sonnet\ntools: Read, Bash\n---\nx\n", encoding="utf-8")
    code = run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": {"subagent_type": "scout"}}),
               {**trial, "CLAUDE_PROJECT_DIR": str(proj), "CLAUDE_AGENTS_HOME": str(clean_home)})
    if code != 2:
        problems.append(f"route: a cheap model fixed on a continued line gave {code}, wanted 2")
    bad = work / "quoted-bad"
    (bad / ".claude" / "agents").mkdir(parents=True)
    (bad / ".claude" / "agents" / "x.md").write_text(
        '---\nname: "reviewer"\ntools: Read, Bash\n---\nx\n', encoding="utf-8")
    (bad / ".claude" / "agents" / "y.md").write_text(
        "---\nname: scout\ntools:\n  - Read\n  - Bash\n---\nx\n", encoding="utf-8")
    (bad / ".claude" / "agents" / "z.md").write_text(
        "---\nname: light-editor  # read-only, honest\ntools: Read, Bash  # shell\n---\nx\n", encoding="utf-8")
    bad_env = {**trial, "CLAUDE_PROJECT_DIR": str(bad), "CLAUDE_AGENTS_HOME": str(clean_home)}
    for tool_input in ({"subagent_type": "reviewer", "model": "haiku"}, {"subagent_type": "scout", "model": "haiku"},
                       {"subagent_type": "light-editor", "model": "sonnet"}):
        code = run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": tool_input}), bad_env)
        if code != 2:
            problems.append(f"route: a kit name holding a shell in another YAML form {tool_input} gave {code}, wanted 2")
    if run(ROUTE, "not json", trial) != 0:
        problems.append("route: unreadable input did not pass (it must fail open)")
    off = work / "off"
    off.write_text("off", encoding="utf-8")
    if run(ROUTE, json.dumps({"tool_name": "Agent", "tool_input": {}}), {**trial, "MODEL_POLICY_OFF": str(off)}) != 0:
        problems.append("route: the off switch did not pass a refused call")


def test_guard(problems: list, work: pathlib.Path) -> None:
    repo = work / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".claude").mkdir()
    shutil.copy(HERE / "protected-paths.txt", repo / ".claude" / "protected-paths.txt")
    with open(repo / ".claude" / "protected-paths.txt", "a", encoding="utf-8") as listing:
        listing.write("src/Billing/\nsrc/*Money.cs\n*.js\n")
    worktree = repo / ".claude" / "worktrees" / "x"
    (worktree / ".claude").mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
    shutil.copy(repo / ".claude" / "protected-paths.txt", worktree / ".claude" / "protected-paths.txt")
    bare = work / "no-list"
    (bare / ".git").mkdir(parents=True)
    outside = work / "outside"
    outside.mkdir()
    cases = [
        (repo / "docs" / "a.md", 0),
        (repo / "README.md", 0),
        (repo / "src" / "Page.cs", 0),
        (repo / "CLAUDE.md", 2),
        (repo / "claude.MD", 2),
        (repo / ".claude" / "settings.json", 2),
        (repo / "scripts" / "x.py", 2),
        (repo / "src" / "Billing" / "Charge.cs", 2),
        (repo / "SRC" / "billing" / "Charge.cs", 2),
        (repo / "src" / "PriceMoney.cs", 2),
        (repo / "src" / "embed" / "loader.js", 2),
        (f"{repo}{os.sep}docs{os.sep}..{os.sep}CLAUDE.md", 2),
        (worktree / "docs" / "a.md", 0),
        (worktree / "src" / "Billing" / "Charge.cs", 2),
        (worktree / ".claude" / "settings.json", 2),
        (repo / "theme" / ".git", 2),
        (repo / "theme" / ".git" / "HEAD", 2),
        (repo / "theme" / ".claude" / "protected-paths.txt", 2),
        (bare / "a.md", 2),
        (outside / "a.md", 2),
        (f"{repo / 'CLAUDE.md'}::$DATA", 2),
        (repo / "CLAUDE~1.MD", 2),
        (f"{repo / 'CLAUDE.md'}:hidden", 2),
    ]
    link = repo / "docs" / "link-to-scripts"
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "scripts").mkdir(exist_ok=True)
    try:
        os.symlink(repo / "scripts", link, target_is_directory=True)
        cases.append((link / "run.py", 2))
    except (OSError, NotImplementedError):
        print("  SKIP  symlink case: this machine cannot create symlinks without extra rights")
    trial = {"MODEL_TRIAL_DIR": str(work / "trial")}
    for path, want in cases:
        code = run(GUARD, json.dumps({"tool_input": {"file_path": str(path)}}), trial)
        if code != want:
            problems.append(f"guard: {path} gave {code}, wanted {want}")
    for payload in ["not json", json.dumps({"tool_input": {}})]:
        if run(GUARD, payload, trial) != 2:
            problems.append(f"guard: {payload!r} did not refuse (it must fail closed)")
    if not list((work / "trial").glob("guard-*.txt")):
        problems.append("guard: wrote no log")


def main() -> int:
    problems: list = []
    with tempfile.TemporaryDirectory() as folder:
        work = pathlib.Path(folder).resolve()
        test_route(problems, work)
        test_guard(problems, work)
    for line in problems:
        print(f"FAIL: {line}")
    print("test-model-policy-hooks: OK" if not problems else f"test-model-policy-hooks: {len(problems)} failed")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
