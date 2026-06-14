#!/usr/bin/env python3
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


def main() -> int:
    payload = parse_hook_payload(sys.stdin.read())
    prompt = extract_prompt(payload)
    if not prompt:
        return 0

    project_root = extract_project_root(payload, fallback=Path.cwd())
    metadata = extract_metadata(payload)
    try:
        ingest_prompt(
            project_root,
            prompt=prompt,
            source="codex-user-prompt-submit",
            metadata=metadata,
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
