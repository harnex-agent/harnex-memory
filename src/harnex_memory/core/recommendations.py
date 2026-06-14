from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from harnex_memory.core.models import (
    MemoryCandidate,
    Preview,
    Recommendation,
    RecommendationKind,
    RecommendationOrigin,
    RecommendationStatus,
    stable_recommendation_id,
)
from harnex_memory.core.paths import project_relative_path, recommendations_path


class RecommendationError(ValueError):
    """Raised when a recommendation cannot be found or updated."""


def read_recommendations(project_root: Path) -> list[Recommendation]:
    path = recommendations_path(project_root)
    if not path.exists():
        return []

    latest: dict[str, Recommendation] = {}
    first_seen: dict[str, int] = {}
    with path.open(encoding="utf-8") as file:
        for index, line in enumerate(file):
            if not line.strip():
                continue
            recommendation = Recommendation.from_dict(json.loads(line))
            latest[recommendation.id] = recommendation
            first_seen.setdefault(recommendation.id, index)

    return sorted(latest.values(), key=lambda item: (item.created_at, first_seen[item.id]))


def append_recommendations(project_root: Path, recommendations: list[Recommendation]) -> None:
    if not recommendations:
        return
    path = recommendations_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        for recommendation in recommendations:
            file.write(json.dumps(recommendation.to_dict(), ensure_ascii=False, sort_keys=True))
            file.write("\n")


def build_recommendation(
    project_root: Path,
    kind: RecommendationKind,
    candidate: MemoryCandidate,
    preview: Preview,
    preview_path: Path,
    origin: str = RecommendationOrigin.HEURISTIC.value,
) -> Recommendation:
    target_path = candidate.target_path or project_relative_path(
        project_root,
        preview.file_changes[0].path,
    )
    return Recommendation(
        kind=kind.value,
        title=candidate.title,
        reason=candidate.reason,
        preview_id=preview.preview_id,
        preview_path=project_relative_path(project_root, preview_path),
        target_path=target_path,
        target_kind=str(candidate.target_kind or ""),
        risk=str(candidate.risk),
        evidence=list(candidate.evidence),
        candidate_id=candidate.id,
        origin=origin,
        id=stable_recommendation_id(kind.value, candidate.id),
    )


def recommendation_exists(
    project_root: Path,
    kind: RecommendationKind,
    candidate: MemoryCandidate,
) -> bool:
    recommendation_id = stable_recommendation_id(kind.value, candidate.id)
    return any(item.id == recommendation_id for item in read_recommendations(project_root))


def get_recommendation(project_root: Path, recommendation_id: str) -> Recommendation:
    for recommendation in read_recommendations(project_root):
        if recommendation.id == recommendation_id:
            return recommendation
    raise RecommendationError(f"Recommendation not found: {recommendation_id}")


def update_recommendation_status(
    project_root: Path,
    recommendation_id: str,
    status: str | RecommendationStatus,
    dismissed_reason: str = "",
) -> Recommendation:
    current = get_recommendation(project_root, recommendation_id)
    status_value = RecommendationStatus(status).value
    updated = replace(
        current,
        status=status_value,
        dismissed_reason=(
            dismissed_reason if status_value == RecommendationStatus.DISMISSED.value else ""
        ),
        updated_at=datetime.now(UTC).isoformat(),
    )
    append_recommendations(project_root, [updated])
    return updated
