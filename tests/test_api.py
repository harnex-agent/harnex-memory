from harnex_memory.api import (
    apply_preview,
    list_documents,
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
    assert (tmp_path / ".harnex/memory/rules.md").exists()


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
