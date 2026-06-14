from harnex_memory.core.classifier import classify_text, detect_agent
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


def test_detect_agent_defaults_to_codex_without_signal(tmp_path):
    assert detect_agent(tmp_path) == "codex"


def test_detect_agent_explicit_argument_wins(tmp_path):
    assert detect_agent(tmp_path, text="just text", agent="claude") == "claude"
    # 잘못된 이름은 무시하고 다음 신호로 폴백
    assert detect_agent(tmp_path, agent="bogus") == "codex"


def test_detect_agent_from_text_marker(tmp_path):
    assert detect_agent(tmp_path, text="CLAUDE.md에 규칙 추가") == "claude"
    assert detect_agent(tmp_path, text="AGENTS.md에 규칙 추가") == "codex"
    # 양쪽 단서가 함께 있으면 모호 → 다음 신호로
    assert detect_agent(tmp_path, text="CLAUDE.md와 AGENTS.md 둘 다") == "codex"


def test_detect_agent_from_source(tmp_path):
    assert detect_agent(tmp_path, source="claude-user-prompt-submit") == "claude"
    assert detect_agent(tmp_path, source="codex-user-prompt-submit") == "codex"


def test_detect_agent_text_beats_source(tmp_path):
    assert (
        detect_agent(tmp_path, text="CLAUDE.md에 추가", source="codex-user-prompt-submit")
        == "claude"
    )


def test_detect_agent_from_single_artifact(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
    assert detect_agent(tmp_path) == "claude"


def test_detect_agent_coexisting_artifacts_fall_back_to_codex(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# y\n", encoding="utf-8")
    assert detect_agent(tmp_path) == "codex"


def test_classify_claude_constraint_via_explicit_agent(tmp_path):
    result = classify_text(tmp_path, "항상 한국어로 답변해줘", agent="claude")

    assert result.target == DocumentKind.RULE
    assert result.target_kind == TargetKind.CLAUDE_AGENTS.value
    assert result.target_path == "CLAUDE.md"


def test_classify_claude_constraint_via_source(tmp_path):
    result = classify_text(tmp_path, "항상 한국어로 답변해줘", source="claude-user-prompt-submit")

    assert result.target_kind == TargetKind.CLAUDE_AGENTS.value
    assert result.target_path == "CLAUDE.md"


def test_classify_claude_skill_targets_existing_claude_skill(tmp_path):
    skill_path = tmp_path / ".claude/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    result = classify_text(tmp_path, "foo skill을 업데이트해줘", agent="claude")

    assert result.target == DocumentKind.SKILL
    assert result.target_kind == TargetKind.CLAUDE_SKILL.value
    assert result.target_path == ".claude/skills/foo/SKILL.md"


def test_classify_coexisting_docs_default_to_codex(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# y\n", encoding="utf-8")

    result = classify_text(tmp_path, "항상 한국어로 답변해줘")

    assert result.target_kind == TargetKind.CODEX_AGENTS.value
    assert result.target_path == "AGENTS.md"
