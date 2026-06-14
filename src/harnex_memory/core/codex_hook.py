from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROMPT_KEYS = (
    "prompt",
    "user_prompt",
    "userPrompt",
    "message",
    "input",
    "text",
)
PROJECT_ROOT_KEYS = (
    "project_root",
    "projectRoot",
    "cwd",
    "working_directory",
    "workingDirectory",
)
METADATA_KEYS = (
    "hook_event_name",
    "event",
    "session_id",
    "sessionId",
    "thread_id",
    "threadId",
    "conversation_id",
    "conversationId",
)


def parse_hook_payload(raw_input: str) -> Any:
    text = raw_input.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"prompt": text}


def extract_prompt(payload: Any) -> str | None:
    found = _find_string_by_keys(payload, PROMPT_KEYS)
    if found:
        return found.strip()
    return None


def extract_project_root(payload: Any, fallback: Path) -> Path:
    found = _find_string_by_keys(payload, PROJECT_ROOT_KEYS)
    path = Path(found).expanduser() if found else fallback
    if path.exists() and path.is_file():
        path = path.parent
    return path.resolve()


def extract_metadata(
    payload: Any, source: str = "codex-user-prompt-submit"
) -> dict[str, str]:
    metadata = {"source": source}
    if isinstance(payload, dict):
        for key in METADATA_KEYS:
            value = payload.get(key)
            if value is not None and not isinstance(value, (dict, list)):
                metadata[key] = str(value)
    return metadata


def _find_string_by_keys(value: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        for candidate in value.values():
            found = _find_string_by_keys(candidate, keys)
            if found:
                return found
    elif isinstance(value, list):
        for candidate in value:
            found = _find_string_by_keys(candidate, keys)
            if found:
                return found
    return None
