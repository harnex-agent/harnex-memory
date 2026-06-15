import json
import sys

from typer.testing import CliRunner

from harnex_memory.cli import app
from harnex_memory.core.hook_install import (
    build_hook_command,
    install_hook,
    is_installed,
    uninstall_hook,
)

runner = CliRunner()


def _commands(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        hook["command"]
        for group in data["hooks"]["UserPromptSubmit"]
        for hook in group["hooks"]
    ]


def test_install_creates_hook_in_fresh_config(tmp_path):
    path = tmp_path / "hooks.json"

    result = install_hook("codex", config_path=path)

    assert result["changed"] is True
    assert result["installed"] is True
    assert any("harnex_memory.hooks.codex" in command for command in _commands(path))


def test_install_is_idempotent(tmp_path):
    path = tmp_path / "hooks.json"
    install_hook("codex", config_path=path)

    second = install_hook("codex", config_path=path)

    assert second["changed"] is False
    harnex = [c for c in _commands(path) if "harnex_memory.hooks" in c]
    assert len(harnex) == 1


def test_install_preserves_existing_hooks_and_keys(tmp_path):
    path = tmp_path / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "otherKey": {"keep": True},
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "echo existing"}]}
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    install_hook("codex", config_path=path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["otherKey"] == {"keep": True}
    commands = _commands(path)
    assert "echo existing" in commands
    assert any("harnex_memory.hooks.codex" in command for command in commands)


def test_uninstall_removes_only_harnex_hook(tmp_path):
    path = tmp_path / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "echo existing"}]}
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    install_hook("codex", config_path=path)

    result = uninstall_hook("codex", config_path=path)

    assert result["changed"] is True
    assert result["installed"] is False
    commands = _commands(path)
    assert "echo existing" in commands
    assert not any("harnex_memory" in command for command in commands)


def test_uninstall_detects_and_removes_legacy_entry(tmp_path):
    path = tmp_path / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/x/.venv/bin/python "
                                    "/x/harnex-memory/scripts/codex_user_prompt_submit.py",
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    assert is_installed("codex", config_path=path) is True

    result = uninstall_hook("codex", config_path=path)

    assert result["changed"] is True
    assert is_installed("codex", config_path=path) is False


def test_uninstall_is_idempotent_when_absent(tmp_path):
    path = tmp_path / "hooks.json"

    result = uninstall_hook("codex", config_path=path)

    assert result["changed"] is False
    assert result["installed"] is False


def test_build_hook_command_uses_current_interpreter():
    command = build_hook_command("codex")

    assert sys.executable in command
    assert "harnex_memory.hooks.codex" in command


def test_cli_hook_install_prompts_then_yes_skips_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))

    declined = runner.invoke(app, ["hook", "install", "--agent", "codex"], input="n\n")
    assert declined.exit_code == 0
    assert is_installed("codex", config_path=tmp_path / "hooks.json") is False

    accepted = runner.invoke(app, ["hook", "install", "--agent", "codex", "--yes"])
    assert accepted.exit_code == 0
    assert is_installed("codex", config_path=tmp_path / "hooks.json") is True


def test_cli_hook_status_and_uninstall(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    runner.invoke(app, ["hook", "install", "--agent", "codex", "--yes"])

    status = json.loads(runner.invoke(app, ["hook", "status", "--agent", "codex"]).stdout)
    assert status["agent"] == "codex"
    assert status["installed"] is True

    runner.invoke(app, ["hook", "uninstall", "--agent", "codex", "--yes"])
    after = json.loads(runner.invoke(app, ["hook", "status", "--agent", "codex"]).stdout)
    assert after["installed"] is False
