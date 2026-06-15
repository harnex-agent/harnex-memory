"""Claude UserPromptSubmit entry point (``python -m harnex_memory.hooks.claude``)."""

from __future__ import annotations

from harnex_memory.prompt_hook import run_prompt_submit_hook


def main() -> int:
    return run_prompt_submit_hook(source="claude-user-prompt-submit", agent="claude")


if __name__ == "__main__":
    raise SystemExit(main())
