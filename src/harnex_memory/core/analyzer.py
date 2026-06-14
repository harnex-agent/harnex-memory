from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from harnex_memory.core.classifier import (
    HOOK_KEYWORDS,
    SKILL_KEYWORDS,
    Classification,
    classify_text,
    detect_agent,
)
from harnex_memory.core.models import (
    ChangeRisk,
    DocumentKind,
    InsertionStrategy,
    MemoryCandidate,
    PromptRecord,
)
from harnex_memory.core.prompt_store import normalize_prompt
from harnex_memory.core.similarity import SimilarityMatcher, resolve_matcher

DIRECT_CONSTRAINT_KEYWORDS = (
    "always",
    "never",
    "must",
    "whenever",
    "prefer",
    "do not",
    "don't",
    "항상",
    "앞으로",
    "매번",
    "반드시",
    "기억해",
    "기억해줘",
    "규칙",
    "원칙",
)
DIRECT_CONSTRAINT_TARGET_KEYWORDS = (*HOOK_KEYWORDS, *SKILL_KEYWORDS)
DIRECT_CONSTRAINT_ACTION_KEYWORDS = (
    "add",
    "record",
    "remember",
    "update",
    "추가",
    "기록",
    "저장",
    "반영",
    "업데이트",
)
# Prompts that should NOT be hardened into a durable rule even when repeated.
# Mirrors hermes-agent's background-review "Do NOT capture" guidance: negative
# tool/environment claims and transient error reports. Kept high-precision and
# conservative — over-filtering would suppress legitimate memories. Matched
# against the casefolded prompt, so all patterns are lowercase.
LOW_VALUE_PATTERNS = (
    # Negative tool/environment claims — saving these makes the agent cite them
    # against itself for months.
    "안 돼",
    "안돼",
    "안 됨",
    "안됨",
    "작동 안",
    "동작 안",
    "먹통",
    "doesn't work",
    "does not work",
    "not working",
    "won't work",
    "is broken",
    # Transient errors that were likely already resolved.
    "에러 났",
    "에러났",
    "오류 났",
    "오류났",
    "traceback",
    "stack trace",
)


def suggest_candidates(
    records: list[PromptRecord],
    min_count: int = 2,
    project_root: Path | None = None,
    matcher: SimilarityMatcher | None = None,
) -> list[MemoryCandidate]:
    # Cluster repeated prompts per agent (so a prompt repeated under both Codex and
    # Claude produces a candidate for each agent's document). The matcher decides
    # what "repeated" means: identical-after-normalization by default, or semantic
    # similarity when an embedding matcher is configured.
    matcher = matcher or resolve_matcher()
    by_agent: dict[str, list[PromptRecord]] = defaultdict(list)
    for record in records:
        if not normalize_prompt(record.prompt):
            continue
        root = project_root or Path(record.project_root)
        agent = detect_agent(root, text=record.prompt, source=record.source)
        by_agent[agent].append(record)

    candidates: list[MemoryCandidate] = []
    seen: set[tuple[str, str]] = set()
    for agent in sorted(by_agent):
        agent_records = by_agent[agent]
        clusters = matcher.cluster([record.prompt for record in agent_records])
        groups = sorted(
            ([agent_records[index] for index in cluster] for cluster in clusters),
            key=lambda group: normalize_prompt(group[0].prompt),
        )
        for group in groups:
            if len(group) < min_count:
                continue
            first_prompt = group[0].prompt.strip()
            if is_low_value_prompt(first_prompt):
                continue
            root = project_root or Path(group[0].project_root)
            classification = classify_text(root, first_prompt, agent=agent)
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
                    id=stable_prompt_candidate_id(first_prompt, classification.target_path),
                )
            )
    return candidates


def infer_target(prompt: str) -> DocumentKind:
    return classify_text(Path("."), prompt).target


def candidate_from_constraint(
    project_root: Path,
    constraint: str,
    source: str = "constraint-preview",
    agent: str | None = None,
) -> MemoryCandidate:
    text = constraint.strip()
    classification = classify_text(project_root, text, source=source, agent=agent)
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


def is_direct_constraint_prompt(prompt: str) -> bool:
    normalized = normalize_prompt(prompt)
    if _contains_any(normalized, DIRECT_CONSTRAINT_KEYWORDS):
        return True
    return _contains_any(normalized, DIRECT_CONSTRAINT_TARGET_KEYWORDS) and _contains_any(
        normalized,
        DIRECT_CONSTRAINT_ACTION_KEYWORDS,
    )


def is_low_value_prompt(prompt: str) -> bool:
    """Return True for prompts not worth hardening into a durable memory rule.

    Conservative, high-precision filter mirroring hermes-agent's "Do NOT
    capture" guidance: negative tool/environment claims and transient error
    reports. Used to skip repeated-prompt suggestions; explicit user
    constraints (see is_direct_constraint_prompt) are intentionally not
    filtered here.
    """
    return _contains_any(normalize_prompt(prompt), LOW_VALUE_PATTERNS)


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


_METADATA_BULLET_KEYS = ("반복 횟수", "출처")


def document_already_contains(project_root: Path, candidate: MemoryCandidate) -> bool:
    """Return True if the candidate's substance already lives in its target doc.

    preview.append_content already skips an exact rendered-block duplicate; this
    matches the *salient* text (the prompt/constraint) instead, so a rule the
    user wrote by hand — or a near-duplicate whose only difference is bookkeeping
    metadata (반복 횟수 등) — is not re-recommended.
    """
    if not candidate.target_path:
        return False
    doc_path = project_root / candidate.target_path
    if not doc_path.is_file():
        return False
    haystack = normalize_prompt(doc_path.read_text(encoding="utf-8"))
    if not haystack:
        return False
    return any(phrase in haystack for phrase in _candidate_key_phrases(candidate))


def _candidate_key_phrases(candidate: MemoryCandidate) -> list[str]:
    """Extract the dedupe-worthy text from a candidate's rendered bullets."""
    phrases: list[str] = []
    for raw_line in candidate.content.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        body = line[2:].strip()
        key, separator, value = body.partition(":")
        if separator:
            key = key.strip()
            if key in _METADATA_BULLET_KEYS:
                continue
            if key == "원문":
                body = value.strip()
        normalized = normalize_prompt(body)
        if normalized:
            phrases.append(normalized)
    return phrases


def stable_prompt_candidate_id(prompt: str, target_path: str) -> str:
    digest = sha256()
    digest.update(normalize_prompt(prompt).encode("utf-8"))
    digest.update(b"\0")
    digest.update(target_path.encode("utf-8"))
    return digest.hexdigest()[:16]


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)
