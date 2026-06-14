from __future__ import annotations

from pathlib import Path

from harnex_memory.core.agent_docs import list_all_document_statuses, template_for
from harnex_memory.core.models import DocumentKind, DocumentStatus
from harnex_memory.core.paths import DOCUMENT_PATHS, document_path, ensure_inside_project

DOCUMENT_TEMPLATES: dict[DocumentKind, str] = {
    DocumentKind.SKILL: "# Skills\n\n",
    DocumentKind.RULE: "# Rules\n\n",
    DocumentKind.HOOK: "# Hooks\n\n",
}


def list_document_statuses(project_root: Path) -> list[DocumentStatus]:
    legacy_statuses = [
        DocumentStatus(kind=kind, path=str(document_path(project_root, kind)), exists=path.exists())
        for kind, path in ((kind, document_path(project_root, kind)) for kind in DOCUMENT_PATHS)
    ]
    return [*legacy_statuses, *list_all_document_statuses(project_root)]


def read_document(project_root: Path, kind: DocumentKind) -> str:
    path = document_path(project_root, kind)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DOCUMENT_TEMPLATES[kind]


def read_document_at_path(
    project_root: Path,
    path: str | Path,
    fallback_kind: DocumentKind,
    target_kind: str | None = None,
) -> str:
    resolved = ensure_inside_project(project_root, path)
    if resolved.exists():
        return resolved.read_text(encoding="utf-8")
    return template_for(target_kind) or DOCUMENT_TEMPLATES[fallback_kind]


def build_document_content(project_root: Path, kind: DocumentKind, addition: str) -> str:
    current = read_document(project_root, kind)
    content = addition.strip()
    if not content:
        return current
    if content in current:
        return current
    separator = "" if current.endswith("\n\n") else "\n\n" if current.endswith("\n") else "\n\n"
    return f"{current}{separator}{content}\n"
