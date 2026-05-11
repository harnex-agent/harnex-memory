from __future__ import annotations

from collections import defaultdict

from harnex_memory.core.models import ChangeRisk, DocumentKind, MemoryCandidate, PromptRecord
from harnex_memory.core.prompt_store import normalize_prompt


def suggest_candidates(records: list[PromptRecord], min_count: int = 2) -> list[MemoryCandidate]:
    grouped: dict[str, list[PromptRecord]] = defaultdict(list)
    for record in records:
        normalized = normalize_prompt(record.prompt)
        if normalized:
            grouped[normalized].append(record)

    candidates: list[MemoryCandidate] = []
    for _normalized, group in sorted(grouped.items(), key=lambda item: item[0]):
        if len(group) < min_count:
            continue
        first_prompt = group[0].prompt.strip()
        target = infer_target(first_prompt)
        title = f"반복 프롬프트: {summarize_prompt(first_prompt)}"
        content = render_candidate_content(first_prompt, group)
        candidates.append(
            MemoryCandidate(
                target=target,
                title=title,
                content=content,
                reason=f"같거나 매우 유사한 프롬프트가 {len(group)}회 기록되었습니다.",
                evidence=[record.id for record in group],
                risk=ChangeRisk.LOW,
            )
        )
    return candidates


def infer_target(prompt: str) -> DocumentKind:
    normalized = normalize_prompt(prompt)
    if any(keyword in normalized for keyword in ("hook", "pre-commit", "post-commit")):
        return DocumentKind.HOOK
    if any(keyword in normalized for keyword in ("skill", "스킬")):
        return DocumentKind.SKILL
    return DocumentKind.RULE


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
