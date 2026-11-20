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


# The kit's own helpers and the tools each may hold. A definition under one of these names that
# lists any other tool (or no tools line, which means every tool) is not the kit's helper, so a
# cheap model on it is refused: the name alone is never trusted.
KIT_TOOLS = {
    "scout": {"Read", "Grep", "Glob"},
    "reviewer": {"Read", "Grep", "Glob"},
    "light-editor": {"Read", "Grep", "Glob", "Edit", "Write"},
    "web-researcher": {"WebSearch", "WebFetch"},
}


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def parse_front(head: str) -> dict[str, str]:
    """Top-level `key: value` pairs of a helper's frontmatter, as Claude Code reads them: quotes
    stripped, and a list (`[A, B]`, or `- A` lines under the key) joined into one comma list."""
    fields: dict[str, str] = {}
    key = ""
    for line in head.splitlines():
        top = re.match(r"^([A-Za-z_-]+):[ \t]*(.*?)[ \t]*$", line)
        if top:
            key, value = top.group(1), _unquote(top.group(2))
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            fields[key] = value
            continue
        item = re.match(r"^[ \t]+-[ \t]*(.*?)[ \t]*$", line)
        if item and key:
            fields[key] = f"{fields[key]},{_unquote(item.group(1))}" if fields[key] else _unquote(item.group(1))
    return fields


def find_definition(agent_type: str) -> tuple[str, set[str] | None] | None:
    """The `model:` and `tools:` of the helper named agent_type, from the repo's or the user's
    .claude/agents/ (matched on the `name:` line, else the file name). None when none is found;
    tools is None when the definition has no tools line (it then gets every tool)."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", agent_type):
        return None
    folders = []
    project = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project:
        folders.append(pathlib.Path(project, ".claude", "agents"))
    folders.append(pathlib.Path(os.environ.get("CLAUDE_AGENTS_HOME") or pathlib.Path.home() / ".claude" / "agents"))
    for folder in folders:
        try:
            files = sorted(folder.glob("*.md"))
        except OSError:
            continue
        for f in files:
            try:
                text = f.read_text(encoding="utf-8-sig")  # -sig: a byte-order mark must not hide the header
            except (OSError, ValueError):
                continue
            head = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---", text, re.S)
            if not head:
                continue
            fields = parse_front(head.group(1))
            if fields.get("name", f.stem) != agent_type:
                continue
            tools = fields.get("tools")
            names = {_unquote(t) for t in tools.split(",") if _unquote(t)} if tools else None
            return fields.get("model", "").lower(), names
    return None


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
    definition = find_definition(agent_type) if tool == "Agent" and agent_type not in ("", "fork") else None
    if not family and definition:
        # No model named in the call: the helper's own definition may still fix one.
        family = next((f for f in ("haiku", "sonnet", "opus", "fable") if f in definition[0]), "")

    if re.search(r"(start_session|set_session_model)$", tool):
        if family in ALLOWED:
            refuse(f"a whole session always has a shell, so sessions stay on Opus ({tool}, {model})")
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
        if family in ALLOWED and agent_type in KIT_TOOLS and definition is None:
            refuse(f"no definition of '{agent_type}' was found in .claude/agents/, so its tools cannot be checked "
                   f"and it does not run on {family}; copy the kit's agents/{agent_type}.md in first")
        if family in ALLOWED and definition and agent_type in KIT_TOOLS:
            tools = definition[1]
            if tools is None or not tools <= KIT_TOOLS[agent_type]:
                held = "every tool" if tools is None else ", ".join(sorted(tools))
                refuse(f"'{agent_type}' here holds {held}, more than the kit's helper of that name "
                       f"({', '.join(sorted(KIT_TOOLS[agent_type]))}), so it does not run on {family}")
    log_call(agent_type, family)


if __name__ == "__main__":
    main()
