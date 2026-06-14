import pytest

from harnex_memory.api import ingest_prompt
from harnex_memory.core.models import (
    ChangeRisk,
    DocumentKind,
    MemoryCandidate,
    RecommendationKind,
    RecommendationOrigin,
)
from harnex_memory.core.reviewer import NullReviewer, resolve_reviewer


class _FakeReviewer:
    def __init__(self, candidates):
        self._candidates = candidates

    def review(self, project_root, prompt, records):
        return list(self._candidates)


def _candidate() -> MemoryCandidate:
    return MemoryCandidate(
        target=DocumentKind.RULE,
        title="리뷰 제안",
        content="- 항상 타입 힌트를 추가",
        reason="리뷰어가 저장 가치가 있다고 판단했습니다.",
        evidence=["llm"],
        risk=ChangeRisk.LOW,
        target_kind="codex_agents",
        target_path="AGENTS.md",
        insertion_strategy="append_bullet",
    )


def test_reviewer_candidates_become_llm_review_recommendations(tmp_path):
    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="그냥 평범한 프롬프트",
        source="adapter",
        reviewer=_FakeReviewer([_candidate()]),
    )

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert rec.kind == RecommendationKind.LLM_REVIEW.value
    assert rec.origin == RecommendationOrigin.LLM_REVIEW.value
    assert rec.target_path == "AGENTS.md"


def test_reviewer_candidate_skipped_when_document_already_covers_it(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# 규칙\n\n- 항상 타입 힌트를 추가\n", encoding="utf-8")

    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="그냥 평범한 프롬프트",
        source="adapter",
        reviewer=_FakeReviewer([_candidate()]),
    )

    assert recommendations == []


def test_no_reviewer_keeps_pure_heuristic_behavior(tmp_path):
    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="그냥 평범한 프롬프트",
        source="adapter",
    )

    assert recommendations == []


def test_resolve_reviewer_defaults_to_none_and_loads_from_spec(monkeypatch):
    monkeypatch.delenv("HARNEX_MEMORY_REVIEWER", raising=False)

    assert resolve_reviewer("") is None
    assert resolve_reviewer(None) is None
    assert isinstance(resolve_reviewer("harnex_memory.core.reviewer:NullReviewer"), NullReviewer)


def test_resolve_reviewer_rejects_bad_spec():
    with pytest.raises(ValueError):
        resolve_reviewer("no-colon-here")
