from harnex_memory.api import (
    apply_preview,
    list_documents,
    preview_constraint_update,
    preview_document_update,
    record_prompt,
    suggest_prompt_updates,
)


def test_public_api_flow(tmp_path):
    statuses = list_documents(tmp_path)
    assert {status.kind.value for status in statuses} == {"skill", "rule", "hook"}
    assert all(not status.exists for status in statuses)

    record_prompt(tmp_path, prompt="pytest로 테스트를 실행해줘", source="test")
    record_prompt(tmp_path, prompt="pytest로 테스트를 실행해줘", source="test")

    preview, preview_path = suggest_prompt_updates(tmp_path)
    assert preview is not None
    assert preview_path is not None
    assert preview_path.exists()
    assert preview.file_changes

    result_path = apply_preview(tmp_path, preview_path)
    assert result_path.exists()
    assert (tmp_path / "AGENTS.md").exists()


def test_preview_document_update_applies_target_document(tmp_path):
    preview, preview_path = preview_document_update(
        tmp_path,
        target="skill",
        content="# Skills\n\n- 테스트 스킬\n",
        source="test",
    )

    assert preview_path.exists()
    assert preview.file_changes[0].diff

    apply_preview(tmp_path, preview_path)
    assert (tmp_path / ".harnex/memory/skills.md").read_text(encoding="utf-8") == (
        "# Skills\n\n- 테스트 스킬\n"
    )


def test_preview_constraint_update_routes_general_rule_to_agents(tmp_path):
    preview, preview_path = preview_constraint_update(
        tmp_path,
        constraint="항상 한국어로 답변해줘",
        source="test",
    )

    assert preview_path.exists()
    assert preview.candidates[0].target_path == "AGENTS.md"
    assert preview.file_changes[0].path == str(tmp_path / "AGENTS.md")
    assert "항상 한국어로 답변해줘" in preview.file_changes[0].after
    assert not (tmp_path / "AGENTS.md").exists()


def test_preview_constraint_update_routes_skill_rule_to_codex_skill(tmp_path):
    skill_path = tmp_path / ".codex/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    preview, _preview_path = preview_constraint_update(
        tmp_path,
        constraint="foo skill에는 입력 검증 규칙을 추가해줘",
        source="test",
    )

    assert preview.candidates[0].target_path == ".codex/skills/foo/SKILL.md"
    assert preview.file_changes[0].path == str(skill_path)
