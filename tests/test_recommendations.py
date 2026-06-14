import pytest

from harnex_memory.api import (
    apply_recommendation,
    dismiss_recommendation,
    ingest_prompt,
    list_recommendations,
)
from harnex_memory.core.models import (
    Recommendation,
    RecommendationKind,
    RecommendationStatus,
)
from harnex_memory.core.recommendations import RecommendationError


def test_ingest_prompt_creates_direct_constraint_recommendation(tmp_path):
    record, recommendations = ingest_prompt(
        tmp_path,
        prompt="항상 한국어로 답변해줘",
        source="adapter",
    )

    assert record.prompt == "항상 한국어로 답변해줘"
    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.kind == RecommendationKind.DIRECT_CONSTRAINT.value
    assert recommendation.status == RecommendationStatus.PENDING.value
    assert recommendation.target_path == "AGENTS.md"
    assert (tmp_path / recommendation.preview_path).exists()

    stored = list_recommendations(tmp_path)
    assert [item.id for item in stored] == [recommendation.id]


def test_ingest_prompt_creates_repeated_prompt_recommendation_once(tmp_path):
    first_record, first_recommendations = ingest_prompt(
        tmp_path,
        prompt="pytest 실행해줘",
        source="adapter",
    )
    second_record, second_recommendations = ingest_prompt(
        tmp_path,
        prompt=" pytest   실행해줘 ",
        source="adapter",
    )
    _third_record, third_recommendations = ingest_prompt(
        tmp_path,
        prompt="pytest 실행해줘",
        source="adapter",
    )

    assert first_record.id != second_record.id
    assert first_recommendations == []
    assert len(second_recommendations) == 1
    assert third_recommendations == []
    assert second_recommendations[0].kind == RecommendationKind.REPEATED_PROMPT.value
    assert "2회 기록되었습니다" in second_recommendations[0].reason
    assert len(list_recommendations(tmp_path)) == 1


def test_recommendation_origin_defaults_to_heuristic_and_round_trips(tmp_path):
    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="항상 한국어로 답변해줘",
        source="adapter",
    )

    assert recommendations[0].origin == "heuristic"
    # Backward/forward compatible serialization round-trip.
    assert Recommendation.from_dict(recommendations[0].to_dict()).origin == "heuristic"
    # Missing origin (legacy record) falls back to heuristic.
    legacy = recommendations[0].to_dict()
    del legacy["origin"]
    assert Recommendation.from_dict(legacy).origin == "heuristic"


def test_ingest_skips_repeated_prompt_already_covered_by_document(tmp_path):
    # The user already recorded this prompt's intent by hand, in a different format
    # than the rendered candidate block — so the exact-block dedup would miss it.
    (tmp_path / "AGENTS.md").write_text("# 규칙\n\n- pytest 실행해줘\n", encoding="utf-8")

    ingest_prompt(tmp_path, prompt="pytest 실행해줘", source="adapter")
    _record, recommendations = ingest_prompt(tmp_path, prompt="pytest 실행해줘", source="adapter")

    assert recommendations == []


def test_dismiss_recommendation_updates_status_without_removing_history(tmp_path):
    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="항상 테스트를 실행해줘",
        source="adapter",
    )

    dismissed = dismiss_recommendation(tmp_path, recommendations[0].id, reason="too noisy")

    assert dismissed.status == RecommendationStatus.DISMISSED.value
    assert dismissed.dismissed_reason == "too noisy"
    assert list_recommendations(tmp_path, status=RecommendationStatus.PENDING) == []
    dismissed_recommendations = list_recommendations(
        tmp_path,
        status=RecommendationStatus.DISMISSED,
    )
    assert dismissed_recommendations[0].id == dismissed.id


def test_apply_recommendation_applies_preview_and_marks_applied(tmp_path):
    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="항상 한국어로 답변해줘",
        source="adapter",
    )

    result_path, recommendation = apply_recommendation(tmp_path, recommendations[0].id)

    assert result_path.exists()
    assert recommendation.status == RecommendationStatus.APPLIED.value
    assert "항상 한국어로 답변해줘" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_list_recommendations_ranks_direct_constraint_above_repeated(tmp_path):
    # Repeated prompt is created first (lower priority)...
    ingest_prompt(tmp_path, prompt="pytest 실행해줘", source="adapter")
    ingest_prompt(tmp_path, prompt="pytest 실행해줘", source="adapter")
    # ...the explicit user constraint is created later (higher priority).
    ingest_prompt(tmp_path, prompt="항상 한국어로 답변해줘", source="adapter")

    kinds = [r.kind for r in list_recommendations(tmp_path)]

    assert kinds.index(RecommendationKind.DIRECT_CONSTRAINT.value) < kinds.index(
        RecommendationKind.REPEATED_PROMPT.value
    )


def test_apply_recommendation_marks_stale_when_document_drifted(tmp_path):
    _record, recommendations = ingest_prompt(
        tmp_path,
        prompt="항상 한국어로 답변해줘",
        source="adapter",
    )
    recommendation_id = recommendations[0].id

    # The target document changes after the recommendation was generated.
    (tmp_path / "AGENTS.md").write_text("# 완전히 다른 내용\n", encoding="utf-8")

    with pytest.raises(RecommendationError):
        apply_recommendation(tmp_path, recommendation_id)

    refreshed = next(r for r in list_recommendations(tmp_path) if r.id == recommendation_id)
    assert refreshed.status == RecommendationStatus.STALE.value
