"""Shared runner for the user-prompt-submit hook scripts (Codex and Claude).

Both ``scripts/codex_user_prompt_submit.py`` and
``scripts/claude_user_prompt_submit.py`` are thin wrappers around
``run_prompt_submit_hook``; they differ only by the prompt ``source`` and the
target ``agent``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from harnex_memory.api import ingest_prompt
from harnex_memory.core.codex_hook import (
    extract_metadata,
    extract_project_root,
    extract_prompt,
    parse_hook_payload,
)


def run_prompt_submit_hook(source: str, *, agent: str | None = None) -> int:
    """Record a hook-submitted prompt and trigger the ingest pipeline.

    Reads the hook payload from stdin and records the prompt under ``source``
    (routed to ``agent`` when given). A memory failure is reported to stderr but
    never blocks the user's prompt, so this always returns ``0``.
    """
    payload = parse_hook_payload(sys.stdin.read())
    prompt = extract_prompt(payload)
    if not prompt:
        return 0

    project_root = extract_project_root(payload, fallback=Path.cwd())
    metadata = extract_metadata(payload, source=source)
    try:
        ingest_prompt(
            project_root,
            prompt=prompt,
            source=source,
            metadata=metadata,
            agent=agent,
        )
    except Exception as exc:  # never block the user's prompt on a memory failure
        print(f"harnex-memory hook: ingest failed: {exc}", file=sys.stderr)
    return 0
