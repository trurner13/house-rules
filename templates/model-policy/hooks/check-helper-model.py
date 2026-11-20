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

BUILT_IN = {"", "general-purpose", "Plan", "Explore"}
ALLOWED = {"haiku": {"scout", "claude-code-guide"}, "sonnet": {"light-editor", "web-researcher", "claude-code-guide"}}
TIERS = ("Tiers (.claude/rules/model-policy.md): scout (haiku) reads; light-editor (sonnet) edits unprotected files; "
         "web-researcher (sonnet) searches the web; anything else names model: opus. Unsure means opus.")


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

    if re.search(r"(start_session|set_session_model)$", tool):
        if family in ALLOWED:
            refuse(f"a whole session always has a shell, so sessions stay on Opus in this trial ({tool}, {model})")
        return
    if tool != "Agent":
        return

    if agent_type != "fork":
        if not family and agent_type in BUILT_IN:
            refuse(f"a built-in helper needs a model named (agent type '{agent_type}')")
        if family in ALLOWED and agent_type not in ALLOWED[family]:
            names = " or ".join(sorted(ALLOWED[family]))
            refuse(f"{family} runs only on {names}, which have no shell, not on agent type '{agent_type}'")
    log_call(agent_type, family)


if __name__ == "__main__":
    main()
