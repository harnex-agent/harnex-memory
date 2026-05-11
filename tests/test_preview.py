from harnex_memory.core.models import DocumentKind, MemoryCandidate
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
