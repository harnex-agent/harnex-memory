from harnex_memory.api import (
    apply_recommendation,
    dismiss_recommendation,
    ingest_prompt,
    list_recommendations,
)
from harnex_memory.core.models import RecommendationKind, RecommendationStatus


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
