from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harnex_memory.core.agent_docs import (
    AGENT_SPECS,
    DEFAULT_AGENT,
    DEFAULT_AGENT_ORDER,
    agent_spec,
    agents_path,
    choose_skill_path,
    discover_skill_paths,
    iter_agent_specs,
)
from harnex_memory.core.models import ChangeRisk, DocumentKind, InsertionStrategy, TargetKind
from harnex_memory.core.paths import DOCUMENT_PATHS, project_relative_path
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
    ".claude/skills",
    "skill.md",
    "skill",
    "skills",
    "codex skill",
    "claude skill",
    "스킬",
)

CLAUDE_TEXT_MARKERS = (".claude/skills", "claude.md", "claude")
CODEX_TEXT_MARKERS = (".codex/skills", "agents.md", "codex")


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


def detect_agent(
    project_root: Path,
    text: str | None = None,
    source: str | None = None,
    agent: str | None = None,
) -> str:
    """Resolve which agent a candidate targets, re-evaluated on every call.

    Priority: explicit ``agent`` > prompt text markers > prompt ``source`` >
    on-disk artifacts (only one agent present) > :data:`DEFAULT_AGENT`. With no
    signal the result is ``codex``, preserving the previous behaviour byte for byte.
    """

    if agent and agent in AGENT_SPECS:
        return agent
    if text:
        from_text = _agent_from_text(text)
        if from_text:
            return from_text
    if source:
        from_source = _agent_from_source(source)
        if from_source:
            return from_source
    from_artifacts = _agent_from_artifacts(project_root)
    if from_artifacts:
        return from_artifacts
    return DEFAULT_AGENT


def classify_text(
    project_root: Path,
    text: str,
    source: str | None = None,
    agent: str | None = None,
) -> Classification:
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

    spec = agent_spec(detect_agent(project_root, text=text, source=source, agent=agent))
    agent_label = spec.name.capitalize()

    if _contains_any(normalized, SKILL_KEYWORDS):
        path = choose_skill_path(spec, project_root, text)
        exists = path.exists()
        return Classification(
            target=DocumentKind.SKILL,
            target_kind=spec.skill_target_kind,
            target_path=project_relative_path(project_root, path),
            insertion_strategy=(
                InsertionStrategy.APPEND_SECTION.value
                if exists
                else InsertionStrategy.CREATE_FILE.value
            ),
            section=f"{agent_label} Skill Guidance",
            reason=(
                f"Skill-related wording routes this candidate to a {agent_label} skill document."
            ),
            confidence="high",
        )

    return Classification(
        target=DocumentKind.RULE,
        target_kind=spec.agents_target_kind,
        target_path=Path(spec.agents_filename).as_posix(),
        insertion_strategy=InsertionStrategy.APPEND_BULLET.value,
        section="Project Instructions",
        reason=(
            f"General project or process constraints route to the "
            f"{agent_label} {spec.agents_filename} document."
        ),
        confidence="high",
    )


def _agent_from_text(text: str) -> str | None:
    normalized = normalize_prompt(text)
    claude_hit = _contains_any(normalized, CLAUDE_TEXT_MARKERS)
    codex_hit = _contains_any(normalized, CODEX_TEXT_MARKERS)
    if claude_hit and not codex_hit:
        return "claude"
    if codex_hit and not claude_hit:
        return "codex"
    return None


def _agent_from_source(source: str) -> str | None:
    lowered = source.casefold()
    matches = [name for name in DEFAULT_AGENT_ORDER if name in lowered]
    if len(matches) == 1:
        return matches[0]
    return None


def _agent_from_artifacts(project_root: Path) -> str | None:
    present = [
        spec.name
        for spec in iter_agent_specs()
        if agents_path(spec, project_root).exists() or discover_skill_paths(spec, project_root)
    ]
    if len(present) == 1:
        return present[0]
    return None


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)
