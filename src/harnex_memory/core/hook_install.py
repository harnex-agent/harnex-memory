"""Install/remove the agent UserPromptSubmit hook that auto-runs harnex-memory.

The hook is registered in the agent's user-level config so a submitted prompt is
recorded automatically:
  * Codex  — ``$CODEX_HOME/hooks.json`` (default ``~/.codex/hooks.json``)
  * Claude — ``$CLAUDE_CONFIG_DIR/settings.json`` (default ``~/.claude/settings.json``)

Both use the same JSON shape: ``hooks.UserPromptSubmit`` is a list of groups,
each with a ``hooks`` list of ``{type, command, ...}``. Merges are idempotent and
preserve unrelated hooks/keys; only harnex entries are added or removed.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

HOOK_EVENT = "UserPromptSubmit"
STATUS_MESSAGE = "Recording Harnex memory"
HOOK_TIMEOUT = 5

_HOOK_MODULES = {
    "codex": "harnex_memory.hooks.codex",
    "claude": "harnex_memory.hooks.claude",
}
# Substrings that identify a harnex-owned hook command (new module form + legacy
# script paths), so uninstall cleans up both and install stays idempotent.
_HARNEX_MARKERS = ("harnex_memory.hooks", "harnex-memory/scripts", "_user_prompt_submit")


def supported_agents() -> tuple[str, ...]:
    return tuple(_HOOK_MODULES)


def hook_config_path(agent: str) -> Path:
    if agent == "codex":
        home = os.environ.get("CODEX_HOME") or (Path.home() / ".codex")
        return Path(home) / "hooks.json"
    if agent == "claude":
        home = os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")
        return Path(home) / "settings.json"
    raise ValueError(f"Unknown agent: {agent!r} (expected one of {supported_agents()})")


def build_hook_command(agent: str, python: str | None = None) -> str:
    module = _HOOK_MODULES.get(agent)
    if module is None:
        raise ValueError(f"Unknown agent: {agent!r}")
    return f"{shlex.quote(python or sys.executable)} -m {module}"


def _is_harnex_command(command: str) -> bool:
    return any(marker in command for marker in _HARNEX_MARKERS)


def _read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _event_groups(data: dict[str, Any]) -> list[Any]:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return []
    groups = hooks.get(HOOK_EVENT)
    return groups if isinstance(groups, list) else []


def is_installed(agent: str, *, config_path: Path | None = None) -> bool:
    path = config_path or hook_config_path(agent)
    for group in _event_groups(_read_config(path)):
        inner = group.get("hooks") if isinstance(group, dict) else None
        for hook in inner or []:
            if isinstance(hook, dict) and _is_harnex_command(str(hook.get("command", ""))):
                return True
    return False


def hook_status(agent: str, *, config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or hook_config_path(agent)
    return {
        "agent": agent,
        "config_path": str(path),
        "installed": is_installed(agent, config_path=path),
        "command": build_hook_command(agent),
    }


def install_hook(
    agent: str, *, config_path: Path | None = None, python: str | None = None
) -> dict[str, Any]:
    path = config_path or hook_config_path(agent)
    if is_installed(agent, config_path=path):
        return {"agent": agent, "config_path": str(path), "installed": True, "changed": False}

    data = _read_config(path)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"Unexpected 'hooks' structure in {path}")
    event = hooks.setdefault(HOOK_EVENT, [])
    if not isinstance(event, list):
        raise ValueError(f"Unexpected '{HOOK_EVENT}' structure in {path}")
    event.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": build_hook_command(agent, python),
                    "timeout": HOOK_TIMEOUT,
                    "statusMessage": STATUS_MESSAGE,
                }
            ]
        }
    )
    _write_config(path, data)
    return {"agent": agent, "config_path": str(path), "installed": True, "changed": True}


def uninstall_hook(agent: str, *, config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or hook_config_path(agent)
    data = _read_config(path)
    hooks = data.get("hooks")
    changed = False
    if isinstance(hooks, dict) and isinstance(hooks.get(HOOK_EVENT), list):
        new_groups: list[Any] = []
        for group in hooks[HOOK_EVENT]:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                new_groups.append(group)
                continue
            kept = [
                hook
                for hook in group["hooks"]
                if not (isinstance(hook, dict) and _is_harnex_command(str(hook.get("command", ""))))
            ]
            if len(kept) == len(group["hooks"]):
                new_groups.append(group)
            else:
                changed = True
                if kept:
                    new_groups.append({**group, "hooks": kept})
                # A group that held only harnex hooks is dropped entirely.
        if changed:
            if new_groups:
                hooks[HOOK_EVENT] = new_groups
            else:
                hooks.pop(HOOK_EVENT, None)
            _write_config(path, data)
    return {
        "agent": agent,
        "config_path": str(path),
        "installed": is_installed(agent, config_path=path),
        "changed": changed,
    }
