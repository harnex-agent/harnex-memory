"""Backwards compatible Codex facade over the generic agent registry.

Public names and signatures are preserved so existing importers keep working; the
real logic lives in ``agent_docs`` keyed on :data:`CODEX_SPEC`.
"""

from __future__ import annotations

from pathlib import Path

from harnex_memory.core.agent_docs import (
    CODEX_SPEC,
    agents_path,
    choose_skill_path,
    default_skill_path,
    discover_skill_paths,
    extract_skill_path,
    list_agent_document_statuses,
    skills_dir,
    template_for,
)
from harnex_memory.core.models import DocumentStatus
from harnex_memory.core.paths import project_relative_path

CODEX_AGENTS_PATH = Path(CODEX_SPEC.agents_filename)
CODEX_SKILLS_DIR = CODEX_SPEC.skills_dir
DEFAULT_CODEX_SKILL_PATH = CODEX_SPEC.skills_dir / CODEX_SPEC.default_skill_subpath

CODEX_DOCUMENT_TEMPLATES: dict[str, str] = {
    CODEX_SPEC.agents_target_kind: CODEX_SPEC.agents_template,
    CODEX_SPEC.skill_target_kind: CODEX_SPEC.skill_template,
}


def list_codex_document_statuses(project_root: Path) -> list[DocumentStatus]:
    return list_agent_document_statuses(CODEX_SPEC, project_root)


def codex_agents_path(project_root: Path) -> Path:
    return agents_path(CODEX_SPEC, project_root)


def codex_skills_dir(project_root: Path) -> Path:
    return skills_dir(CODEX_SPEC, project_root)


def default_codex_skill_path(project_root: Path) -> Path:
    return default_skill_path(CODEX_SPEC, project_root)


def discover_codex_skill_paths(project_root: Path) -> list[Path]:
    return discover_skill_paths(CODEX_SPEC, project_root)


def choose_codex_skill_path(project_root: Path, text: str) -> Path:
    return choose_skill_path(CODEX_SPEC, project_root, text)


def extract_codex_skill_path(text: str) -> Path | None:
    return extract_skill_path(CODEX_SPEC, text)


def codex_template_for(target_kind: str | None) -> str:
    return template_for(target_kind)


def relative_codex_path(project_root: Path, path: str | Path) -> str:
    return project_relative_path(project_root, path)
