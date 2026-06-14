import json

from typer.testing import CliRunner

from harnex_memory.cli import app


def test_items_list_command_outputs_gui_items_json(tmp_path):
    rules_path = tmp_path / ".harnex/memory/rules.md"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# Rules\n\n- Run pytest\n", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(app, ["items", "list", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["items"][0]["title"] == "Run pytest"
    assert payload["items"][0]["source_hash"]


def test_items_preview_command_outputs_preview_json(tmp_path):
    rules_path = tmp_path / ".harnex/memory/rules.md"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# Rules\n\n- Run pytest\n", encoding="utf-8")
    runner = CliRunner()
    list_result = runner.invoke(app, ["items", "list", "--project-root", str(tmp_path)])
    item_id = json.loads(list_result.stdout)["items"][0]["id"]

    result = runner.invoke(
        app,
        [
            "items",
            "preview",
            "--project-root",
            str(tmp_path),
            "--item-id",
            item_id,
            "--action",
            "delete",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["preview"]["action"] == "delete"
    assert payload["preview"]["file_changes"]


def test_prompt_ingest_command_outputs_recommendations_json(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "prompt",
            "ingest",
            "--project-root",
            str(tmp_path),
            "--source",
            "adapter",
            "--prompt",
            "항상 한국어로 답변해줘",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["record"]["prompt"] == "항상 한국어로 답변해줘"
    assert payload["recommendations"][0]["target_path"] == "AGENTS.md"


def test_prompt_ingest_command_routes_to_claude_with_agent_option(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "prompt",
            "ingest",
            "--project-root",
            str(tmp_path),
            "--source",
            "adapter",
            "--prompt",
            "항상 한국어로 답변해줘",
            "--agent",
            "claude",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recommendations"][0]["target_path"] == "CLAUDE.md"


def test_constraint_preview_command_routes_to_claude_with_agent_option(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "constraint",
            "preview",
            "--project-root",
            str(tmp_path),
            "--constraint",
            "항상 한국어로 답변해줘",
            "--agent",
            "claude",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["preview"]["candidates"][0]["target_path"] == "CLAUDE.md"


def test_recommendations_list_command_outputs_pending_recommendations(tmp_path):
    runner = CliRunner()
    runner.invoke(
        app,
        [
            "prompt",
            "ingest",
            "--project-root",
            str(tmp_path),
            "--source",
            "adapter",
            "--prompt",
            "항상 한국어로 답변해줘",
        ],
    )

    result = runner.invoke(
        app,
        ["recommendations", "list", "--project-root", str(tmp_path), "--status", "pending"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload["recommendations"]) == 1
    assert payload["recommendations"][0]["status"] == "pending"
