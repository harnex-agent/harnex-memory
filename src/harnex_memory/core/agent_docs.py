"""Agent-aware document registry.

Holds per-agent knowledge (filenames, skill directories, templates, target kinds,
scopes) in a single data structure so routing and document logic stay generic.
Adding another agent (e.g. Cursor) is one ``AgentSpec`` plus enum values, with no
control-flow changes. ``codex_docs`` delegates to the helpers here as a backwards
compatible shim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harnex_memory.core.models import DocumentKind, DocumentStatus, MemoryScope, TargetKind
from harnex_memory.core.paths import ensure_inside_project


@dataclass(frozen=True)
class AgentSpec:
    name: str
    agents_filename: str
    skills_dir: Path
    agents_target_kind: str
    skill_target_kind: str
    scope: str
    default_skill_subpath: Path
    agents_template: str
    skill_template: str
    override_filename: str | None = None


CODEX_SPEC = AgentSpec(
    name="codex",
    agents_filename="AGENTS.md",
    skills_dir=Path(".codex/skills"),
    agents_target_kind=TargetKind.CODEX_AGENTS.value,
    skill_target_kind=TargetKind.CODEX_SKILL.value,
    scope=MemoryScope.PROJECT_CODEX.value,
    default_skill_subpath=Path("general/SKILL.md"),
    agents_template="# Project Instructions\n\n",
    skill_template="# Codex Skill\n\n",
    override_filename="AGENTS.override.md",
)

CLAUDE_SPEC = AgentSpec(
    name="claude",
    agents_filename="CLAUDE.md",
    skills_dir=Path(".claude/skills"),
    agents_target_kind=TargetKind.CLAUDE_AGENTS.value,
    skill_target_kind=TargetKind.CLAUDE_SKILL.value,
    scope=MemoryScope.PROJECT_CLAUDE.value,
    default_skill_subpath=Path("general/SKILL.md"),
    agents_template="# Project Instructions\n\n",
    skill_template="# Claude Skill\n\n",
    override_filename=None,
)

AGENT_SPECS: dict[str, AgentSpec] = {
    CODEX_SPEC.name: CODEX_SPEC,
    CLAUDE_SPEC.name: CLAUDE_SPEC,
}
DEFAULT_AGENT = "codex"
DEFAULT_AGENT_ORDER: tuple[str, ...] = ("codex", "claude")

DOCUMENT_TEMPLATES: dict[str, str] = {}
for _spec in AGENT_SPECS.values():
    DOCUMENT_TEMPLATES[_spec.agents_target_kind] = _spec.agents_template
    DOCUMENT_TEMPLATES[_spec.skill_target_kind] = _spec.skill_template


def agent_spec(name: str) -> AgentSpec:
    return AGENT_SPECS[name]


def iter_agent_specs() -> list[AgentSpec]:
    return [AGENT_SPECS[name] for name in DEFAULT_AGENT_ORDER]


def agents_path(spec: AgentSpec, project_root: Path) -> Path:
    return ensure_inside_project(project_root, Path(spec.agents_filename))


def skills_dir(spec: AgentSpec, project_root: Path) -> Path:
    return ensure_inside_project(project_root, spec.skills_dir)


def default_skill_path(spec: AgentSpec, project_root: Path) -> Path:
    return ensure_inside_project(project_root, spec.skills_dir / spec.default_skill_subpath)


def discover_skill_paths(spec: AgentSpec, project_root: Path) -> list[Path]:
    directory = skills_dir(spec, project_root)
    if not directory.exists():
        return []

    paths = [
        path
        for path in directory.glob("*/SKILL.md")
        if path.is_file() and ensure_inside_project(project_root, path) == path.resolve()
    ]
    paths.extend(
        path
        for path in directory.glob("*.md")
        if path.is_file() and ensure_inside_project(project_root, path) == path.resolve()
    )
    return sorted(set(paths), key=lambda path: path.relative_to(project_root.resolve()).as_posix())


def choose_skill_path(spec: AgentSpec, project_root: Path, text: str) -> Path:
    explicit = extract_skill_path(spec, text)
    if explicit:
        return ensure_inside_project(project_root, explicit)

    normalized = text.casefold()
    skill_paths = discover_skill_paths(spec, project_root)
    for path in skill_paths:
        names = {path.stem.casefold(), path.parent.name.casefold()}
        if any(name and re.search(rf"\b{re.escape(name)}\b", normalized) for name in names):
            return path

    if len(skill_paths) == 1:
        return skill_paths[0]

    return default_skill_path(spec, project_root)


def extract_skill_path(spec: AgentSpec, text: str) -> Path | None:
    prefix = re.escape(spec.skills_dir.as_posix())
    match = re.search(rf"(?P<path>{prefix}/[^\s`'\"]+?\.md)", text)
    if not match:
        return None
    return Path(match.group("path"))


def template_for(target_kind: str | None) -> str:
    return DOCUMENT_TEMPLATES.get(str(target_kind), "")


def list_agent_document_statuses(spec: AgentSpec, project_root: Path) -> list[DocumentStatus]:
    agents_file = agents_path(spec, project_root)
    statuses = [
        DocumentStatus(
            kind=DocumentKind.RULE,
            path=str(agents_file),
            exists=agents_file.exists(),
            target_kind=spec.agents_target_kind,
            agent=spec.name,
        )
    ]

    skill_paths = discover_skill_paths(spec, project_root)
    if not skill_paths:
        skill_paths = [default_skill_path(spec, project_root)]

    statuses.extend(
        DocumentStatus(
            kind=DocumentKind.SKILL,
            path=str(path),
            exists=path.exists(),
            target_kind=spec.skill_target_kind,
            agent=spec.name,
        )
        for path in skill_paths
    )
    return statuses


def list_all_document_statuses(project_root: Path) -> list[DocumentStatus]:
    statuses: list[DocumentStatus] = []
    for spec in iter_agent_specs():
        statuses.extend(list_agent_document_statuses(spec, project_root))
    return statuses
