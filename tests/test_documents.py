from harnex_memory.core.documents import (
    build_document_content,
    list_document_statuses,
    read_document,
)
from harnex_memory.core.models import DocumentKind, TargetKind


def test_list_document_statuses_uses_default_legacy_paths(tmp_path):
    statuses = list_document_statuses(tmp_path)
    legacy_statuses = [status for status in statuses if status.agent is None]

    assert [status.kind for status in legacy_statuses] == [
        DocumentKind.SKILL,
        DocumentKind.RULE,
        DocumentKind.HOOK,
    ]
    assert legacy_statuses[0].path.endswith(".harnex/memory/skills.md")


def test_list_document_statuses_detects_codex_agents(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")

    statuses = list_document_statuses(tmp_path)

    agents = [
        status for status in statuses if status.target_kind == TargetKind.CODEX_AGENTS.value
    ]
    assert len(agents) == 1
    assert agents[0].kind == DocumentKind.RULE
    assert agents[0].path.endswith("AGENTS.md")
    assert agents[0].exists


def test_list_document_statuses_detects_codex_skill_directory_file(tmp_path):
    skill_path = tmp_path / ".codex/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    statuses = list_document_statuses(tmp_path)

    assert any(
        status.target_kind == TargetKind.CODEX_SKILL.value
        and status.path.endswith(".codex/skills/foo/SKILL.md")
        and status.exists
        for status in statuses
    )


def test_list_document_statuses_detects_codex_flat_skill_file(tmp_path):
    skill_path = tmp_path / ".codex/skills/foo.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    statuses = list_document_statuses(tmp_path)

    assert any(
        status.target_kind == TargetKind.CODEX_SKILL.value
        and status.path.endswith(".codex/skills/foo.md")
        and status.exists
        for status in statuses
    )


def test_list_document_statuses_detects_claude_agents(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project Instructions\n", encoding="utf-8")

    statuses = list_document_statuses(tmp_path)

    agents = [
        status for status in statuses if status.target_kind == TargetKind.CLAUDE_AGENTS.value
    ]
    assert len(agents) == 1
    assert agents[0].kind == DocumentKind.RULE
    assert agents[0].agent == "claude"
    assert agents[0].path.endswith("CLAUDE.md")
    assert agents[0].exists


def test_list_document_statuses_detects_claude_skill_directory_file(tmp_path):
    skill_path = tmp_path / ".claude/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    statuses = list_document_statuses(tmp_path)

    assert any(
        status.target_kind == TargetKind.CLAUDE_SKILL.value
        and status.path.endswith(".claude/skills/foo/SKILL.md")
        and status.exists
        and status.agent == "claude"
        for status in statuses
    )


def test_read_document_returns_template_when_missing(tmp_path):
    assert read_document(tmp_path, DocumentKind.RULE) == "# Rules\n\n"


def test_build_document_content_appends_once(tmp_path):
    addition = "## 새 규칙\n\n- 같은 내용은 한 번만 추가한다."

    first = build_document_content(tmp_path, DocumentKind.RULE, addition)
    (tmp_path / ".harnex/memory").mkdir(parents=True)
    (tmp_path / ".harnex/memory/rules.md").write_text(first, encoding="utf-8")
    second = build_document_content(tmp_path, DocumentKind.RULE, addition)

    assert second.count("## 새 규칙") == 1
