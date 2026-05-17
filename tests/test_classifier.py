from harnex_memory.core.classifier import classify_text
from harnex_memory.core.models import DocumentKind, TargetKind


def test_classify_general_constraint_targets_codex_agents(tmp_path):
    result = classify_text(tmp_path, "항상 한국어로 답변해줘")

    assert result.target == DocumentKind.RULE
    assert result.target_kind == TargetKind.CODEX_AGENTS.value
    assert result.target_path == "AGENTS.md"


def test_classify_skill_constraint_targets_existing_skill(tmp_path):
    skill_path = tmp_path / ".codex/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    result = classify_text(tmp_path, "foo skill을 업데이트해줘")

    assert result.target == DocumentKind.SKILL
    assert result.target_kind == TargetKind.CODEX_SKILL.value
    assert result.target_path == ".codex/skills/foo/SKILL.md"


def test_classify_hook_constraint_targets_legacy_hook_document(tmp_path):
    result = classify_text(tmp_path, "pre-commit hook에는 ruff를 실행해줘")

    assert result.target == DocumentKind.HOOK
    assert result.target_kind == TargetKind.HOOK.value
    assert result.target_path == ".harnex/memory/hooks.md"
