from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from harnex_memory.core.analyzer import (
    candidate_from_constraint,
    is_direct_constraint_prompt,
    suggest_candidates,
)
from harnex_memory.core.apply import apply_preview_changes
from harnex_memory.core.documents import list_document_statuses
from harnex_memory.core.items import (
    build_memory_item_action_preview,
)
from harnex_memory.core.items import (
    get_memory_item as get_memory_item_core,
)
from harnex_memory.core.items import (
    list_memory_items as list_memory_items_core,
)
from harnex_memory.core.models import (
    DocumentKind,
    DocumentStatus,
    MemoryItem,
    Preview,
    PromptRecord,
    Recommendation,
    RecommendationKind,
    RecommendationStatus,
)
from harnex_memory.core.paths import ensure_inside_project, resolve_project_root
from harnex_memory.core.preview import (
    build_candidates_preview,
    build_document_preview,
    read_preview,
    write_preview,
)
from harnex_memory.core.prompt_store import append_prompt_record, read_prompt_records
from harnex_memory.core.recommendations import (
    append_recommendations,
    build_recommendation,
    get_recommendation,
    read_recommendations,
    recommendation_exists,
    update_recommendation_status,
)


def list_documents(project_root: str | Path) -> list[DocumentStatus]:
    root = resolve_project_root(project_root)
    return list_document_statuses(root)


def list_memory_items(
    project_root: str | Path,
    cwd: str | Path | None = None,
    include_readonly: bool = False,
) -> list[MemoryItem]:
    root = resolve_project_root(project_root)
    return list_memory_items_core(root, cwd=cwd, include_readonly=include_readonly)


def get_memory_item(project_root: str | Path, item_id: str) -> MemoryItem:
    root = resolve_project_root(project_root)
    return get_memory_item_core(root, item_id)


def preview_memory_item_action(
    project_root: str | Path,
    item_id: str,
    action: str,
    expected_source_hash: str | None = None,
    cwd: str | Path | None = None,
) -> tuple[Preview, Path]:
    root = resolve_project_root(project_root)
    preview = build_memory_item_action_preview(
        root,
        item_id=item_id,
        action=action,
        expected_source_hash=expected_source_hash,
        cwd=cwd,
    )
    path = write_preview(root, preview)
    return preview, path


def preview_document_update(
    project_root: str | Path,
    target: str | DocumentKind,
    content: str,
    source: str = "api",
) -> tuple[Preview, Path]:
    root = resolve_project_root(project_root)
    kind = DocumentKind(target)
    preview = build_document_preview(root, kind, content, source)
    path = write_preview(root, preview)
    return preview, path


def preview_constraint_update(
    project_root: str | Path,
    constraint: str,
    source: str = "constraint-preview",
    metadata: dict[str, Any] | None = None,
    agent: str | None = None,
) -> tuple[Preview, Path]:
    root = resolve_project_root(project_root)
    candidate = candidate_from_constraint(root, constraint, source=source, agent=agent)
    if metadata:
        candidate = replace(
            candidate,
            evidence=[
                *candidate.evidence,
                *[f"{key}={value}" for key, value in sorted(metadata.items())],
            ],
        )
    preview = build_candidates_preview(root, [candidate], source=source)
    path = write_preview(root, preview)
    return preview, path


def apply_preview(project_root: str | Path, preview_path: str | Path) -> Path:
    root = resolve_project_root(project_root)
    path = ensure_inside_project(root, preview_path)
    preview = read_preview(path)
    return apply_preview_changes(root, preview)


def record_prompt(
    project_root: str | Path,
    prompt: str,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> PromptRecord:
    root = resolve_project_root(project_root)
    return append_prompt_record(root, prompt, source, metadata)


def suggest_prompt_updates(
    project_root: str | Path,
    min_count: int = 2,
    source: str = "prompt-suggest",
) -> tuple[Preview | None, Path | None]:
    root = resolve_project_root(project_root)
    records = read_prompt_records(root)
    candidates = suggest_candidates(records, min_count=min_count, project_root=root)
    if not candidates:
        return None, None
    preview = build_candidates_preview(root, candidates, source=source)
    path = write_preview(root, preview)
    return preview, path


def ingest_prompt(
    project_root: str | Path,
    prompt: str,
    source: str,
    metadata: dict[str, Any] | None = None,
    min_count: int = 2,
    auto_suggest: bool = True,
    agent: str | None = None,
) -> tuple[PromptRecord, list[Recommendation]]:
    root = resolve_project_root(project_root)
    record = append_prompt_record(root, prompt, source, metadata)
    if not auto_suggest:
        return record, []

    candidate_entries = []
    if is_direct_constraint_prompt(prompt):
        candidate_entries.append(
            (
                RecommendationKind.DIRECT_CONSTRAINT,
                candidate_from_constraint(
                    root, prompt, source=f"prompt:{record.id}", agent=agent
                ),
            )
        )

    records = read_prompt_records(root)
    candidate_entries.extend(
        (RecommendationKind.REPEATED_PROMPT, candidate)
        for candidate in suggest_candidates(records, min_count=min_count, project_root=root)
    )

    recommendations: list[Recommendation] = []
    for kind, candidate in candidate_entries:
        if recommendation_exists(root, kind, candidate):
            continue
        preview = build_candidates_preview(root, [candidate], source=f"prompt-ingest:{kind.value}")
        if not any(change.diff for change in preview.file_changes):
            continue
        preview_path = write_preview(root, preview)
        recommendations.append(build_recommendation(root, kind, candidate, preview, preview_path))

    append_recommendations(root, recommendations)
    return record, recommendations


def list_recommendations(
    project_root: str | Path,
    status: str | RecommendationStatus | None = None,
) -> list[Recommendation]:
    root = resolve_project_root(project_root)
    recommendations = read_recommendations(root)
    if status is None:
        return recommendations
    status_value = RecommendationStatus(status).value
    return [item for item in recommendations if item.status == status_value]


def get_recommendation_detail(
    project_root: str | Path,
    recommendation_id: str,
) -> tuple[Recommendation, Preview]:
    root = resolve_project_root(project_root)
    recommendation = get_recommendation(root, recommendation_id)
    preview_path = ensure_inside_project(root, recommendation.preview_path)
    return recommendation, read_preview(preview_path)


def dismiss_recommendation(
    project_root: str | Path,
    recommendation_id: str,
    reason: str = "",
) -> Recommendation:
    root = resolve_project_root(project_root)
    return update_recommendation_status(
        root,
        recommendation_id,
        RecommendationStatus.DISMISSED,
        dismissed_reason=reason,
    )


def apply_recommendation(
    project_root: str | Path,
    recommendation_id: str,
) -> tuple[Path, Recommendation]:
    root = resolve_project_root(project_root)
    recommendation = get_recommendation(root, recommendation_id)
    if recommendation.status != RecommendationStatus.PENDING.value:
        raise ValueError(
            "Only pending recommendations can be applied; "
            f"current status is {recommendation.status}."
        )
    result_path = apply_preview(root, recommendation.preview_path)
    updated = update_recommendation_status(root, recommendation_id, RecommendationStatus.APPLIED)
    return result_path, updated
