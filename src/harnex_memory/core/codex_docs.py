from __future__ import annotations

import re
from pathlib import Path

from harnex_memory.core.models import DocumentKind, DocumentStatus, TargetKind
from harnex_memory.core.paths import ensure_inside_project, project_relative_path

CODEX_AGENTS_PATH = Path("AGENTS.md")
CODEX_SKILLS_DIR = Path(".codex/skills")
DEFAULT_CODEX_SKILL_PATH = CODEX_SKILLS_DIR / "general" / "SKILL.md"

CODEX_DOCUMENT_TEMPLATES: dict[str, str] = {
    TargetKind.CODEX_AGENTS.value: "# Project Instructions\n\n",
    TargetKind.CODEX_SKILL.value: "# Codex Skill\n\n",
}


def list_codex_document_statuses(project_root: Path) -> list[DocumentStatus]:
    agents_path = codex_agents_path(project_root)
    statuses = [
        DocumentStatus(
            kind=DocumentKind.RULE,
            path=str(agents_path),
            exists=agents_path.exists(),
            target_kind=TargetKind.CODEX_AGENTS.value,
            agent="codex",
        )
    ]

    skill_paths = discover_codex_skill_paths(project_root)
    if not skill_paths:
        skill_paths = [default_codex_skill_path(project_root)]

    statuses.extend(
        DocumentStatus(
            kind=DocumentKind.SKILL,
            path=str(path),
            exists=path.exists(),
            target_kind=TargetKind.CODEX_SKILL.value,
            agent="codex",
        )
        for path in skill_paths
    )
    return statuses


def codex_agents_path(project_root: Path) -> Path:
    return ensure_inside_project(project_root, CODEX_AGENTS_PATH)


def codex_skills_dir(project_root: Path) -> Path:
    return ensure_inside_project(project_root, CODEX_SKILLS_DIR)


def default_codex_skill_path(project_root: Path) -> Path:
    return ensure_inside_project(project_root, DEFAULT_CODEX_SKILL_PATH)


def discover_codex_skill_paths(project_root: Path) -> list[Path]:
    skills_dir = codex_skills_dir(project_root)
    if not skills_dir.exists():
        return []

    paths = [
        path
        for path in skills_dir.glob("*/SKILL.md")
        if path.is_file() and ensure_inside_project(project_root, path) == path.resolve()
    ]
    paths.extend(
        path
        for path in skills_dir.glob("*.md")
        if path.is_file() and ensure_inside_project(project_root, path) == path.resolve()
    )
    return sorted(set(paths), key=lambda path: path.relative_to(project_root.resolve()).as_posix())


def choose_codex_skill_path(project_root: Path, text: str) -> Path:
    explicit = extract_codex_skill_path(text)
    if explicit:
        return ensure_inside_project(project_root, explicit)

    normalized = text.casefold()
    skill_paths = discover_codex_skill_paths(project_root)
    for path in skill_paths:
        names = {path.stem.casefold(), path.parent.name.casefold()}
        if any(name and re.search(rf"\b{re.escape(name)}\b", normalized) for name in names):
            return path

    if len(skill_paths) == 1:
        return skill_paths[0]

    return default_codex_skill_path(project_root)


def extract_codex_skill_path(text: str) -> Path | None:
    match = re.search(r"(?P<path>\.codex/skills/[^\s`'\"]+?\.md)", text)
    if not match:
        return None
    return Path(match.group("path"))


def codex_template_for(target_kind: str | None) -> str:
    return CODEX_DOCUMENT_TEMPLATES.get(str(target_kind), "")


def relative_codex_path(project_root: Path, path: str | Path) -> str:
    return project_relative_path(project_root, path)
