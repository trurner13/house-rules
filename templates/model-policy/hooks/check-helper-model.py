#!/usr/bin/env python3
"""PreToolUse hook on Agent, start_session and set_session_model (templates/model-policy/).

Refuses a built-in helper with no model named, a cheap model on anything but its own helper, and a cheap model on a whole
session. Exit 2 blocks the call, and the message says what to do. It routes work and guards no data, so it lets through
anything it cannot read, and the file ~/.claude/model-policy-off stops it everywhere at once. Each call it lets through
is logged as one new file in ~/.claude/model-trial/ (one file each, so parallel helpers cannot collide), unless the repo
holds .claude/no-model-trial-log.

Standard library only, Python 3.9+. Held to its cases by templates/model-policy/test-model-policy-hooks.py.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import sys
import uuid

BUILT_IN = {"", "general-purpose", "Plan", "Explore", "claude-code-guide", "statusline-setup", "web-fetch"}
# reviewer is read-only (no shell, no web), so the adversarial review can run on Opus, Sonnet and Haiku at once.
ALLOWED = {"haiku": {"scout", "reviewer"}, "sonnet": {"light-editor", "web-researcher", "reviewer"}}
TIERS = ("Tiers (.claude/rules/model-policy.md): scout (haiku) reads; light-editor (sonnet) edits unprotected files; "
         "web-researcher (sonnet) searches the web; reviewer (any model) reviews read-only; anything else names "
         "model: opus. Unsure means opus.")


def refuse(why: str) -> None:
    print(f"REFUSED by .claude/hooks/check-helper-model.py: {why}.", file=sys.stderr)
    print(TIERS, file=sys.stderr)
    sys.exit(2)


def log_call(agent_type: str, family: str) -> None:
    try:
        project = os.environ.get("CLAUDE_PROJECT_DIR", "")
        if project and pathlib.Path(project, ".claude", "no-model-trial-log").exists():
            return
        folder = pathlib.Path(os.environ.get("MODEL_TRIAL_DIR") or pathlib.Path.home() / ".claude" / "model-trial")
        folder.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now()
        repo = pathlib.Path(project).name if project else "unknown"
        name = f"call-{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex}.txt"
        (folder / name).write_text(f"call|{now:%Y-%m-%d}|{repo}|{agent_type}|{family}\n", encoding="utf-8")
    except OSError:
        pass


def defined_model(agent_type: str) -> str:
    """The `model:` a repo's own helper definition fixes, if any (.claude/agents/<name>.md)."""
    project = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project or not re.fullmatch(r"[A-Za-z0-9._-]+", agent_type):
        return ""
    try:
        text = pathlib.Path(project, ".claude", "agents", f"{agent_type}.md").read_text(encoding="utf-8")
    except (OSError, ValueError):
        return ""
    head = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    m = re.search(r"^model:\s*(\S+)", head.group(1), re.M) if head else None
    return m.group(1).lower() if m else ""


def main() -> None:
    try:
        off = os.environ.get("MODEL_POLICY_OFF") or pathlib.Path.home() / ".claude" / "model-policy-off"
        if pathlib.Path(off).exists():
            return
        payload = json.load(sys.stdin)
        tool = str(payload.get("tool_name") or "")
        tool_input = payload.get("tool_input") or {}
        model = str(tool_input.get("model") or "").lower()
        agent_type = str(tool_input.get("subagent_type") or "")
    except (OSError, ValueError, AttributeError):
        return

    family = next((f for f in ("haiku", "sonnet", "opus", "fable") if f in model), "")
    if not family and tool == "Agent" and agent_type not in ("", "fork"):
        # No model named in the call: a repo's own helper may still fix one in its definition.
        fixed = defined_model(agent_type)
        family = next((f for f in ("haiku", "sonnet", "opus", "fable") if f in fixed), "")

    if re.search(r"(start_session|set_session_model)$", tool):
        if family in ALLOWED:
            refuse(f"a whole session always has a shell, so sessions stay on Opus in this trial ({tool}, {model})")
        return
    if tool != "Agent":
        return

    # A fork always runs on the parent session's model whatever the call says, so it is never a cheap model.
    if agent_type != "fork":
        if not family and agent_type in BUILT_IN:
            refuse(f"a built-in helper needs a model named (agent type '{agent_type}')")
        if family in ALLOWED and agent_type not in ALLOWED[family]:
            names = " or ".join(sorted(ALLOWED[family]))
            refuse(f"{family} runs only on {names}, which have no shell, not on agent type '{agent_type}'")
    log_call(agent_type, family)


if __name__ == "__main__":
    main()
