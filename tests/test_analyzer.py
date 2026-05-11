from harnex_memory.core.analyzer import suggest_candidates
from harnex_memory.core.models import DocumentKind, PromptRecord


def test_suggest_candidates_detects_repeated_prompt():
    records = [
        PromptRecord(prompt="테스트 실행해줘", source="clarify", project_root="/tmp/project"),
        PromptRecord(prompt=" 테스트   실행해줘 ", source="verify", project_root="/tmp/project"),
    ]

    candidates = suggest_candidates(records)

    assert len(candidates) == 1
    assert candidates[0].target == DocumentKind.RULE
    assert candidates[0].evidence == [records[0].id, records[1].id]


def test_suggest_candidates_infers_hook_target():
    records = [
        PromptRecord(prompt="pre-commit hook 추가해줘", source="gui", project_root="/tmp/project"),
        PromptRecord(prompt="pre-commit hook 추가해줘", source="gui", project_root="/tmp/project"),
    ]

    candidates = suggest_candidates(records)

    assert candidates[0].target == DocumentKind.HOOK
