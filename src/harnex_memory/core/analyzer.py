from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from harnex_memory.core.classifier import Classification, classify_text
from harnex_memory.core.models import (
    ChangeRisk,
    DocumentKind,
    InsertionStrategy,
    MemoryCandidate,
    PromptRecord,
)
from harnex_memory.core.prompt_store import normalize_prompt


def suggest_candidates(
    records: list[PromptRecord],
    min_count: int = 2,
    project_root: Path | None = None,
) -> list[MemoryCandidate]:
    grouped: dict[str, list[PromptRecord]] = defaultdict(list)
    for record in records:
        normalized = normalize_prompt(record.prompt)
        if normalized:
            grouped[normalized].append(record)

    candidates: list[MemoryCandidate] = []
    seen: set[tuple[str, str]] = set()
    for _normalized, group in sorted(grouped.items(), key=lambda item: item[0]):
        if len(group) < min_count:
            continue
        first_prompt = group[0].prompt.strip()
        root = project_root or Path(group[0].project_root)
        classification = classify_text(root, first_prompt)
        dedupe_key = (normalize_prompt(first_prompt), classification.target_path)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        title = f"반복 프롬프트: {summarize_prompt(first_prompt)}"
        content = render_candidate_content(first_prompt, group)
        candidates.append(
            MemoryCandidate(
                target=classification.target,
                title=title,
                content=content,
                reason=(
                    f"같거나 매우 유사한 프롬프트가 {len(group)}회 기록되었습니다. "
                    f"{classification.reason}"
                ),
                evidence=[record.id for record in group],
                risk=ChangeRisk.LOW,
                target_kind=classification.target_kind,
                target_path=classification.target_path,
                insertion_strategy=classification.insertion_strategy,
                section=classification.section,
            )
        )
    return candidates


def infer_target(prompt: str) -> DocumentKind:
    return classify_text(Path("."), prompt).target


def candidate_from_constraint(
    project_root: Path,
    constraint: str,
    source: str = "constraint-preview",
) -> MemoryCandidate:
    text = constraint.strip()
    classification = classify_text(project_root, text)
    return MemoryCandidate(
        target=classification.target,
        title=f"사용자 제약: {summarize_prompt(text)}",
        content=render_constraint_content(text, classification),
        reason=classification.reason,
        evidence=[source],
        risk=classification.risk,
        target_kind=classification.target_kind,
        target_path=classification.target_path,
        insertion_strategy=classification.insertion_strategy,
        section=classification.section,
    )


def summarize_prompt(prompt: str, limit: int = 48) -> str:
    one_line = " ".join(prompt.split())
    if len(one_line) <= limit:
        return one_line
    return f"{one_line[: limit - 3]}..."


def render_candidate_content(prompt: str, records: list[PromptRecord]) -> str:
    sources = ", ".join(sorted({record.source for record in records}))
    return (
        f"## 반복 프롬프트: {summarize_prompt(prompt)}\n\n"
        f"- 반복 횟수: {len(records)}\n"
        f"- 출처: {sources}\n"
        f"- 원문: {prompt.strip()}\n"
    )


def render_constraint_content(constraint: str, classification: Classification) -> str:
    if classification.insertion_strategy == InsertionStrategy.APPEND_BULLET.value:
        return f"- {constraint.strip()}\n"
    heading = classification.section or "Memory Candidate"
    return f"## {heading}\n\n- {constraint.strip()}\n"
