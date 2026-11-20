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


KIT_TOOLS = {
    "scout": {"Read", "Grep", "Glob"},
    "reviewer": {"Read", "Grep", "Glob"},
    "light-editor": {"Read", "Grep", "Glob", "Edit", "Write"},
    "web-researcher": {"WebSearch", "WebFetch"},
}
CHEAP_WORD = re.compile(r"(haiku|sonnet)", re.I)  # a full id (claude-haiku-5-5) counts too

# This hook does not try to read YAML. YAML has many ways to write the same thing, and every way
# a parser misreads is a way round the check. Instead it finds every file that could define the
# helper and judges them conservatively: a mistake here can only refuse a call, never allow one.


def candidates(agent_type: str) -> list[tuple[pathlib.Path, str | None]]:
    """Every helper definition that could be agent_type, with its frontmatter (None if it has none).

    Searched: the project's and the user's .claude/agents/, at any depth. A file counts when its
    name is agent_type, or when agent_type appears as a word on any frontmatter line other than
    the description. Over-matching is safe: it can only lead to a refusal.
    """
    if not re.fullmatch(r"[A-Za-z0-9._-]+", agent_type):
        return []
    folders = []
    project = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project:
        folders.append(pathlib.Path(project, ".claude", "agents"))
    folders.append(pathlib.Path(os.environ.get("CLAUDE_AGENTS_HOME") or pathlib.Path.home() / ".claude" / "agents"))
    word = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(agent_type)}(?![A-Za-z0-9_-])")
    found: list[tuple[pathlib.Path, str | None]] = []
    for folder in folders:
        try:
            files = sorted(folder.rglob("*.md"))
        except OSError:
            continue
        for f in files:
            try:
                # Bytes decoded leniently, so a stray byte can't hide a file; a byte-order mark is dropped.
                text = f.read_bytes().decode("utf-8", errors="replace").lstrip("\ufeff").replace("\r\n", "\n")
            except OSError:
                text = None
            # The header ends at the FIRST "---" anywhere, as Claude Code reads it (its own pattern is
            # /^---\s*\n([\s\S]*?)---\s*\n?/), so a "---" inside a description cuts the header there too.
            # A header after leading blank lines is read as well, to be safe.
            head_match = re.match(r"\s*---\s*\n([\s\S]*?)---", text) if text is not None else None
            head = head_match.group(1) if head_match else None
            named = head is not None and any(
                word.search(line) for line in head.splitlines() if not line.lstrip().lower().startswith("description"))
            if f.stem == agent_type or named:
                found.append((f, head))
    return found


def plain_kit_form(head: str | None, agent_type: str) -> bool:
    """True only for the kit's own plain format: one-line `name:`, `description:`, `model:` and
    `tools:` (and, for light-editor, its `hooks:` block), each once, tools a comma list within the
    kit's set. Anything else (quotes, lists, comments, continued lines, other keys) is not plain."""
    if head is None:
        return False
    seen: set[str] = set()
    in_hooks = False
    for line in head.splitlines():
        if not line.strip():
            continue
        if line[0] in " \t":
            if in_hooks:
                continue
            return False
        in_hooks = False
        m = re.fullmatch(r"(name|description|model|tools|hooks):(?: (.*))?", line)
        if not m or m.group(1) in seen:
            return False
        key, value = m.group(1), (m.group(2) or "").strip()
        seen.add(key)
        if key == "name" and value != agent_type:
            return False
        if key == "model" and value not in ("haiku", "sonnet", "opus", "fable", "inherit"):
            return False
        if key == "tools":
            if not re.fullmatch(r"[A-Za-z]+(?:, [A-Za-z]+)*", value):
                return False
            if not set(value.split(", ")) <= KIT_TOOLS[agent_type]:
                return False
        if key == "description" and (not value or value[0] in "\"'|>[{&*!%@`" or " #" in value or "\\" in value):
            return False
        if key == "hooks":
            if value or agent_type != "light-editor":
                return False
            in_hooks = True
    return {"name", "tools"} <= seen


def cheap_hint(heads: list[tuple[pathlib.Path, str | None]]) -> str:
    """'haiku' or 'sonnet' if any candidate's frontmatter names one outside its description,
    however it is written; '' otherwise."""
    found = ""
    for _, head in heads:
        for line in (head or "").splitlines():
            if line.lstrip().lower().startswith("description"):
                continue
            m = CHEAP_WORD.search(line)
            if m:
                found = m.group(1).lower()
                if found == "haiku":
                    return found
    return found


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
            refuse(f"a whole session always has a shell, so sessions stay on Opus ({tool}, {model})")
        return
    if tool != "Agent":
        return

    # A fork always runs on the parent session's model whatever the call says, so it is never a cheap model.
    if agent_type == "fork":
        log_call(agent_type, family)
        return

    heads = candidates(agent_type) if agent_type else []
    if not family:
        # No model named in the call: a definition may still fix a cheap one, written any way at all.
        family = cheap_hint(heads)

    if not family and agent_type in BUILT_IN:
        refuse(f"a built-in helper needs a model named (agent type '{agent_type}')")
    if family in ALLOWED and agent_type not in ALLOWED[family]:
        names = " or ".join(sorted(ALLOWED[family]))
        refuse(f"{family} runs only on {names}, which have no shell, not on agent type '{agent_type}'")
    if family in ALLOWED and agent_type in KIT_TOOLS:
        if not heads:
            refuse(f"no definition of '{agent_type}' was found in .claude/agents/, so its tools cannot be checked "
                   f"and it does not run on {family}; copy the kit's agents/{agent_type}.md in first")
        for path, head in heads:
            if not plain_kit_form(head, agent_type):
                refuse(f"{path} could define '{agent_type}' and is not in the kit's plain format (one-line name, "
                       f"model and tools, tools within {', '.join(sorted(KIT_TOOLS[agent_type]))}), so '{agent_type}' "
                       f"does not run on {family}; rewrite it like the kit's agents/{agent_type}.md, or rename it")
    log_call(agent_type, family)


if __name__ == "__main__":
    main()
