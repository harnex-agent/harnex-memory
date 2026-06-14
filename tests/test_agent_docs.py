from pathlib import Path

from harnex_memory.core.agent_docs import (
    CLAUDE_SPEC,
    CODEX_SPEC,
    agent_spec,
    agents_path,
    choose_skill_path,
    default_skill_path,
    discover_skill_paths,
    extract_skill_path,
    iter_agent_specs,
    list_agent_document_statuses,
    list_all_document_statuses,
    template_for,
)
from harnex_memory.core.models import DocumentKind, TargetKind


def test_agent_spec_lookup_returns_registered_specs():
    assert agent_spec("codex") is CODEX_SPEC
    assert agent_spec("claude") is CLAUDE_SPEC


def test_iter_agent_specs_is_deterministic_codex_first():
    assert [spec.name for spec in iter_agent_specs()] == ["codex", "claude"]


def test_agents_path_uses_spec_filename(tmp_path):
    assert agents_path(CODEX_SPEC, tmp_path) == (tmp_path / "AGENTS.md").resolve()
    assert agents_path(CLAUDE_SPEC, tmp_path) == (tmp_path / "CLAUDE.md").resolve()


def test_default_skill_path_for_claude(tmp_path):
    assert default_skill_path(CLAUDE_SPEC, tmp_path) == (
        tmp_path / ".claude/skills/general/SKILL.md"
    ).resolve()


def test_discover_skill_paths_finds_claude_skills(tmp_path):
    skill_path = tmp_path / ".claude/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    found = discover_skill_paths(CLAUDE_SPEC, tmp_path)

    assert skill_path.resolve() in found
    assert discover_skill_paths(CODEX_SPEC, tmp_path) == []


def test_extract_skill_path_is_scoped_to_spec_directory():
    assert extract_skill_path(CLAUDE_SPEC, "update .claude/skills/foo/SKILL.md please") == Path(
        ".claude/skills/foo/SKILL.md"
    )
    assert extract_skill_path(CLAUDE_SPEC, "update .codex/skills/foo/SKILL.md please") is None
    assert extract_skill_path(CODEX_SPEC, "update .codex/skills/foo/SKILL.md please") == Path(
        ".codex/skills/foo/SKILL.md"
    )


def test_choose_skill_path_matches_named_claude_skill(tmp_path):
    skill_path = tmp_path / ".claude/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")

    chosen = choose_skill_path(CLAUDE_SPEC, tmp_path, "foo 스킬을 업데이트해줘")

    assert chosen == skill_path.resolve()


def test_choose_skill_path_falls_back_to_default(tmp_path):
    chosen = choose_skill_path(CLAUDE_SPEC, tmp_path, "스킬을 만들어줘")

    assert chosen == default_skill_path(CLAUDE_SPEC, tmp_path)


def test_template_for_resolves_across_registry():
    assert template_for(TargetKind.CODEX_AGENTS.value) == "# Project Instructions\n\n"
    assert template_for(TargetKind.CLAUDE_AGENTS.value) == "# Project Instructions\n\n"
    assert template_for(TargetKind.CLAUDE_SKILL.value) == "# Claude Skill\n\n"
    assert template_for("unknown_kind") == ""


def test_list_agent_document_statuses_for_claude(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project Instructions\n", encoding="utf-8")

    statuses = list_agent_document_statuses(CLAUDE_SPEC, tmp_path)

    agents = [s for s in statuses if s.target_kind == TargetKind.CLAUDE_AGENTS.value]
    assert len(agents) == 1
    assert agents[0].kind == DocumentKind.RULE
    assert agents[0].agent == "claude"
    assert agents[0].path.endswith("CLAUDE.md")
    assert agents[0].exists
    assert all(status.agent == "claude" for status in statuses)


def test_list_all_document_statuses_covers_both_agents(tmp_path):
    statuses = list_all_document_statuses(tmp_path)

    agents = {status.agent for status in statuses}
    assert agents == {"codex", "claude"}
