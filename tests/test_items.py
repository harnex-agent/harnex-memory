import json

from harnex_memory.api import (
    apply_preview,
    list_memory_items,
    preview_memory_item_action,
)
from harnex_memory.core.models import ItemStatus, TargetKind
from harnex_memory.core.paths import disabled_items_path


def test_list_memory_items_returns_legacy_markdown_bullets(tmp_path):
    rules_path = tmp_path / ".harnex/memory/rules.md"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# Rules\n\n- Run pytest\n- Answer in Korean\n", encoding="utf-8")

    items = list_memory_items(tmp_path)

    titles = {item.title for item in items}
    assert "Run pytest" in titles
    assert "Answer in Korean" in titles
    assert all(item.status == ItemStatus.ACTIVE.value for item in items)
    assert any(item.target_kind == TargetKind.LEGACY_RULE.value for item in items)


def test_delete_item_preview_removes_only_selected_item_after_apply(tmp_path):
    rules_path = tmp_path / ".harnex/memory/rules.md"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# Rules\n\n- Run pytest\n- Answer in Korean\n", encoding="utf-8")
    item = next(item for item in list_memory_items(tmp_path) if item.title == "Run pytest")

    preview, preview_path = preview_memory_item_action(tmp_path, item.id, "delete")

    assert not preview.blocked_reasons
    assert "Run pytest" not in preview.file_changes[0].after
    assert "Answer in Korean" in preview.file_changes[0].after
    assert "Run pytest" in rules_path.read_text(encoding="utf-8")

    apply_preview(tmp_path, preview_path)

    assert "Run pytest" not in rules_path.read_text(encoding="utf-8")
    assert "Answer in Korean" in rules_path.read_text(encoding="utf-8")


def test_disable_and_enable_item_round_trip_through_disabled_store(tmp_path):
    rules_path = tmp_path / ".harnex/memory/rules.md"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# Rules\n\n- Run pytest\n", encoding="utf-8")
    item = list_memory_items(tmp_path)[0]

    disable_preview, disable_path = preview_memory_item_action(tmp_path, item.id, "disable")
    apply_preview(tmp_path, disable_path)

    assert not disable_preview.blocked_reasons
    assert "Run pytest" not in rules_path.read_text(encoding="utf-8")
    store_data = json.loads(disabled_items_path(tmp_path).read_text(encoding="utf-8"))
    assert store_data["items"][0]["id"] == item.id

    disabled_item = next(
        candidate for candidate in list_memory_items(tmp_path) if candidate.id == item.id
    )
    assert disabled_item.status == ItemStatus.DISABLED.value

    enable_preview, enable_path = preview_memory_item_action(tmp_path, disabled_item.id, "enable")
    apply_preview(tmp_path, enable_path)

    assert not enable_preview.blocked_reasons
    assert "Run pytest" in rules_path.read_text(encoding="utf-8")
    store_data = json.loads(disabled_items_path(tmp_path).read_text(encoding="utf-8"))
    assert store_data["items"] == []


def test_stale_source_hash_blocks_item_action(tmp_path):
    rules_path = tmp_path / ".harnex/memory/rules.md"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# Rules\n\n- Run pytest\n", encoding="utf-8")
    item = list_memory_items(tmp_path)[0]
    rules_path.write_text("# Rules\n\n- Run pytest carefully\n", encoding="utf-8")

    preview, _preview_path = preview_memory_item_action(
        tmp_path,
        item.id,
        "delete",
        expected_source_hash=item.source_hash,
    )

    assert preview.file_changes == []
    assert preview.blocked_reasons


def test_agents_override_shadows_same_directory_agents_items(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Rules\n\n- Base guidance\n", encoding="utf-8")
    (tmp_path / "AGENTS.override.md").write_text(
        "# Rules\n\n- Override guidance\n", encoding="utf-8"
    )

    items = list_memory_items(tmp_path)

    base = next(item for item in items if item.title == "Base guidance")
    override = next(item for item in items if item.title == "Override guidance")
    assert base.status == ItemStatus.SHADOWED.value
    assert override.status == ItemStatus.ACTIVE.value


def test_duplicate_codex_skill_names_are_marked_conflict(tmp_path):
    nested_skill = tmp_path / ".codex/skills/foo/SKILL.md"
    flat_skill = tmp_path / ".codex/skills/foo.md"
    nested_skill.parent.mkdir(parents=True)
    nested_skill.write_text("# Foo\n\nInstructions\n", encoding="utf-8")
    flat_skill.write_text("# Foo\n\nOther instructions\n", encoding="utf-8")

    items = [
        item
        for item in list_memory_items(tmp_path)
        if item.target_kind == TargetKind.CODEX_SKILL.value
    ]

    assert len(items) == 2
    assert {item.status for item in items} == {ItemStatus.CONFLICT.value}


def test_list_memory_items_marks_claude_agent_items(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Rules\n\n- Answer in Korean\n", encoding="utf-8")

    items = list_memory_items(tmp_path)

    claude_item = next(item for item in items if item.title == "Answer in Korean")
    assert claude_item.target_kind == TargetKind.CLAUDE_AGENTS.value
    assert claude_item.agent == "claude"
    assert claude_item.status == ItemStatus.ACTIVE.value


def test_claude_agents_has_no_override_shadowing(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Rules\n\n- Base guidance\n", encoding="utf-8")
    (tmp_path / "CLAUDE.override.md").write_text(
        "# Rules\n\n- Override guidance\n", encoding="utf-8"
    )

    items = list_memory_items(tmp_path)

    base = next(item for item in items if item.title == "Base guidance")
    # Claude has no override-file concept: base stays active and the override file is ignored.
    assert base.status == ItemStatus.ACTIVE.value
    assert all(item.title != "Override guidance" for item in items)


def test_codex_and_claude_same_skill_name_do_not_conflict(tmp_path):
    codex_skill = tmp_path / ".codex/skills/foo/SKILL.md"
    claude_skill = tmp_path / ".claude/skills/foo/SKILL.md"
    codex_skill.parent.mkdir(parents=True)
    claude_skill.parent.mkdir(parents=True)
    codex_skill.write_text("# Foo\n\nCodex instructions\n", encoding="utf-8")
    claude_skill.write_text("# Foo\n\nClaude instructions\n", encoding="utf-8")

    items = [
        item
        for item in list_memory_items(tmp_path)
        if item.target_kind in {TargetKind.CODEX_SKILL.value, TargetKind.CLAUDE_SKILL.value}
    ]

    assert len(items) == 2
    assert {item.status for item in items} == {ItemStatus.ACTIVE.value}
    assert {item.agent for item in items} == {"codex", "claude"}
