import pytest

from harnex_memory.core.models import DocumentKind, MemoryCandidate
from harnex_memory.core.paths import PathSafetyError
from harnex_memory.core.preview import build_candidates_preview, make_diff, write_preview


def test_make_diff_contains_unified_headers(tmp_path):
    path = tmp_path / "rules.md"
    diff = make_diff(path, "old\n", "new\n")

    assert "--- a/rules.md" in diff
    assert "+++ b/rules.md" in diff
    assert "-old" in diff
    assert "+new" in diff


def test_build_candidates_preview_writes_preview_json(tmp_path):
    candidate = MemoryCandidate(
        target=DocumentKind.RULE,
        title="반복 프롬프트",
        content="## 반복 프롬프트\n\n- pytest 실행\n",
        reason="반복됨",
        evidence=["1", "2"],
    )

    preview = build_candidates_preview(tmp_path, [candidate], source="test")
    path = write_preview(tmp_path, preview)

    assert path.exists()
    assert path.parent == tmp_path / ".harnex/memory/previews"
    assert preview.file_changes[0].diff


def test_build_candidates_preview_merges_same_target_changes(tmp_path):
    candidates = [
        MemoryCandidate(
            target=DocumentKind.RULE,
            title="첫 번째",
            content="## 첫 번째\n\n- one\n",
            reason="반복됨",
            evidence=["1", "2"],
        ),
        MemoryCandidate(
            target=DocumentKind.RULE,
            title="두 번째",
            content="## 두 번째\n\n- two\n",
            reason="반복됨",
            evidence=["3", "4"],
        ),
    ]

    preview = build_candidates_preview(tmp_path, candidates, source="test")

    assert len(preview.file_changes) == 1
    assert "## 첫 번째" in preview.file_changes[0].after
    assert "## 두 번째" in preview.file_changes[0].after


def test_build_candidates_preview_uses_candidate_target_path(tmp_path):
    candidate = MemoryCandidate(
        target=DocumentKind.RULE,
        title="규칙",
        content="## Project Instructions\n\n- 항상 테스트를 실행한다.\n",
        reason="직접 제약",
        evidence=["constraint-preview"],
        target_kind="codex_agents",
        target_path="AGENTS.md",
    )

    preview = build_candidates_preview(tmp_path, [candidate], source="test")

    assert preview.file_changes[0].path == str(tmp_path / "AGENTS.md")
    assert "항상 테스트를 실행한다." in preview.file_changes[0].after
    assert not (tmp_path / "AGENTS.md").exists()


def test_build_candidates_preview_rejects_escaped_target_path(tmp_path):
    candidate = MemoryCandidate(
        target=DocumentKind.RULE,
        title="규칙",
        content="## Bad\n\n- nope\n",
        reason="직접 제약",
        evidence=["constraint-preview"],
        target_path="../AGENTS.md",
    )

    with pytest.raises(PathSafetyError):
        build_candidates_preview(tmp_path, [candidate], source="test")


def test_build_candidates_preview_skips_duplicate_content(tmp_path):
    candidate = MemoryCandidate(
        target=DocumentKind.RULE,
        title="규칙",
        content="## Project Instructions\n\n- 중복 금지\n",
        reason="직접 제약",
        evidence=["constraint-preview"],
        target_path="AGENTS.md",
    )

    preview = build_candidates_preview(tmp_path, [candidate, candidate], source="test")

    assert preview.file_changes[0].after.count("중복 금지") == 1
