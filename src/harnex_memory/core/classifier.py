from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harnex_memory.core.codex_docs import (
    CODEX_AGENTS_PATH,
    choose_codex_skill_path,
    relative_codex_path,
)
from harnex_memory.core.models import ChangeRisk, DocumentKind, InsertionStrategy, TargetKind
from harnex_memory.core.paths import DOCUMENT_PATHS
from harnex_memory.core.prompt_store import normalize_prompt

HOOK_KEYWORDS = (
    "hook",
    "hooks",
    "pre-commit",
    "post-commit",
    "pre-push",
    "commit-msg",
    "githook",
    "lefthook",
    "husky",
    "훅",
)
SKILL_KEYWORDS = (
    ".codex/skills",
    "skill.md",
    "skill",
    "skills",
    "codex skill",
    "스킬",
)


@dataclass(frozen=True)
class Classification:
    target: DocumentKind
    target_kind: str
    target_path: str
    insertion_strategy: str
    section: str | None
    reason: str
    risk: ChangeRisk = ChangeRisk.LOW
    confidence: str = "medium"


def classify_text(project_root: Path, text: str) -> Classification:
    normalized = normalize_prompt(text)
    if _contains_any(normalized, HOOK_KEYWORDS):
        return Classification(
            target=DocumentKind.HOOK,
            target_kind=TargetKind.HOOK.value,
            target_path=DOCUMENT_PATHS[DocumentKind.HOOK].as_posix(),
            insertion_strategy=InsertionStrategy.APPEND_SECTION.value,
            section="Hook Guidance",
            reason=(
                "Hook-related keywords route this candidate to the "
                "hook-compatible memory document."
            ),
            confidence="high",
        )

    if _contains_any(normalized, SKILL_KEYWORDS):
        path = choose_codex_skill_path(project_root, text)
        exists = path.exists()
        return Classification(
            target=DocumentKind.SKILL,
            target_kind=TargetKind.CODEX_SKILL.value,
            target_path=relative_codex_path(project_root, path),
            insertion_strategy=(
                InsertionStrategy.APPEND_SECTION.value
                if exists
                else InsertionStrategy.CREATE_FILE.value
            ),
            section="Codex Skill Guidance",
            reason="Skill-related wording routes this candidate to a Codex skill document.",
            confidence="high",
        )

    return Classification(
        target=DocumentKind.RULE,
        target_kind=TargetKind.CODEX_AGENTS.value,
        target_path=CODEX_AGENTS_PATH.as_posix(),
        insertion_strategy=InsertionStrategy.APPEND_BULLET.value,
        section="Project Instructions",
        reason="General project or process constraints route to the Codex AGENTS.md document.",
        confidence="high",
    )


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)
