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
