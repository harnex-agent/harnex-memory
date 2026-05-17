from harnex_memory.core.analyzer import suggest_candidates
from harnex_memory.core.models import DocumentKind, PromptRecord, TargetKind


def test_suggest_candidates_detects_repeated_prompt():
    records = [
        PromptRecord(prompt="테스트 실행해줘", source="clarify", project_root="/tmp/project"),
        PromptRecord(prompt=" 테스트   실행해줘 ", source="verify", project_root="/tmp/project"),
    ]

    candidates = suggest_candidates(records)

    assert len(candidates) == 1
    assert candidates[0].target == DocumentKind.RULE
    assert candidates[0].target_kind == TargetKind.CODEX_AGENTS.value
    assert candidates[0].target_path == "AGENTS.md"
    assert candidates[0].insertion_strategy
    assert candidates[0].evidence == [records[0].id, records[1].id]


def test_suggest_candidates_infers_hook_target():
    records = [
        PromptRecord(prompt="pre-commit hook 추가해줘", source="gui", project_root="/tmp/project"),
        PromptRecord(prompt="pre-commit hook 추가해줘", source="gui", project_root="/tmp/project"),
    ]

    candidates = suggest_candidates(records)

    assert candidates[0].target == DocumentKind.HOOK
    assert candidates[0].target_kind == TargetKind.HOOK.value
    assert candidates[0].target_path == ".harnex/memory/hooks.md"


def test_suggest_candidates_infers_codex_skill_target(tmp_path):
    skill_path = tmp_path / ".codex/skills/foo/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# Foo\n", encoding="utf-8")
    records = [
        PromptRecord(prompt="foo skill 업데이트해줘", source="gui", project_root=str(tmp_path)),
        PromptRecord(prompt="foo skill 업데이트해줘", source="gui", project_root=str(tmp_path)),
    ]

    candidates = suggest_candidates(records, project_root=tmp_path)

    assert candidates[0].target == DocumentKind.SKILL
    assert candidates[0].target_kind == TargetKind.CODEX_SKILL.value
    assert candidates[0].target_path == ".codex/skills/foo/SKILL.md"
