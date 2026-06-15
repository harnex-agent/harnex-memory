"""Codex UserPromptSubmit entry point (``python -m harnex_memory.hooks.codex``)."""

from __future__ import annotations

from harnex_memory.prompt_hook import run_prompt_submit_hook


def main() -> int:
    return run_prompt_submit_hook(source="codex-user-prompt-submit")


if __name__ == "__main__":
    raise SystemExit(main())
