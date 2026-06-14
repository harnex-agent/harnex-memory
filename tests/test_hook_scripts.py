"""End-to-end tests for the user-prompt-submit hook scripts.

These exercise the actual auto-trigger entrypoint (`main()`) the way Codex/Claude
invoke it: a JSON payload arrives on stdin and the script records the prompt and
generates recommendations without the user mentioning harnex-memory.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from harnex_memory import prompt_hook
from harnex_memory.api import list_recommendations
from harnex_memory.core.models import RecommendationKind

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_script(name: str) -> ModuleType:
    path = SCRIPTS_DIR / name
    spec = importlib.util.spec_from_file_location(f"hook_{name.replace('.', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _feed(monkeypatch: pytest.MonkeyPatch, payload: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))


def _payload(prompt: str, root: Path) -> str:
    return json.dumps(
        {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": str(root)}
    )


def test_codex_hook_script_records_prompt_and_recommends_on_repeat(tmp_path, monkeypatch):
    script = _load_script("codex_user_prompt_submit.py")
    payload = _payload("pytest 실행해줘", tmp_path)

    _feed(monkeypatch, payload)
    assert script.main() == 0
    records_file = tmp_path / ".harnex/memory/prompt-records.jsonl"
    assert records_file.exists()
    assert list_recommendations(tmp_path) == []

    _feed(monkeypatch, payload)
    assert script.main() == 0

    recommendations = list_recommendations(tmp_path)
    assert len(recommendations) == 1
    assert recommendations[0].kind == RecommendationKind.REPEATED_PROMPT.value
    assert recommendations[0].target_path == "AGENTS.md"
    assert "2회 기록되었습니다" in recommendations[0].reason


def test_claude_hook_script_routes_recommendation_to_claude(tmp_path, monkeypatch):
    script = _load_script("claude_user_prompt_submit.py")
    payload = _payload("pytest 실행해줘", tmp_path)

    _feed(monkeypatch, payload)
    assert script.main() == 0
    _feed(monkeypatch, payload)
    assert script.main() == 0

    recommendations = list_recommendations(tmp_path)
    assert len(recommendations) == 1
    assert recommendations[0].kind == RecommendationKind.REPEATED_PROMPT.value
    assert recommendations[0].target_path == "CLAUDE.md"


def test_codex_hook_script_without_prompt_is_noop(tmp_path, monkeypatch):
    script = _load_script("codex_user_prompt_submit.py")

    _feed(monkeypatch, json.dumps({"cwd": str(tmp_path)}))

    assert script.main() == 0
    assert not (tmp_path / ".harnex").exists()


def test_codex_hook_script_reports_ingest_failure_without_blocking(tmp_path, monkeypatch, capsys):
    script = _load_script("codex_user_prompt_submit.py")

    def _boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(prompt_hook, "ingest_prompt", _boom)
    _feed(monkeypatch, _payload("pytest 실행해줘", tmp_path))

    # A memory failure must surface on stderr but must not block the prompt (exit 0).
    assert script.main() == 0
    captured = capsys.readouterr()
    assert "ingest failed" in captured.err
    assert "disk full" in captured.err
