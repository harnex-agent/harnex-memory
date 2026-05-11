from __future__ import annotations

from pathlib import Path

from harnex_memory.core.models import DocumentKind, DocumentStatus
from harnex_memory.core.paths import DOCUMENT_PATHS, document_path

DOCUMENT_TEMPLATES: dict[DocumentKind, str] = {
    DocumentKind.SKILL: "# Skills\n\n",
    DocumentKind.RULE: "# Rules\n\n",
    DocumentKind.HOOK: "# Hooks\n\n",
}


def list_document_statuses(project_root: Path) -> list[DocumentStatus]:
    return [
        DocumentStatus(kind=kind, path=str(document_path(project_root, kind)), exists=path.exists())
        for kind, path in ((kind, document_path(project_root, kind)) for kind in DOCUMENT_PATHS)
    ]


def read_document(project_root: Path, kind: DocumentKind) -> str:
    path = document_path(project_root, kind)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DOCUMENT_TEMPLATES[kind]


def build_document_content(project_root: Path, kind: DocumentKind, addition: str) -> str:
    current = read_document(project_root, kind)
    content = addition.strip()
    if not content:
        return current
    if content in current:
        return current
    separator = "" if current.endswith("\n\n") else "\n\n" if current.endswith("\n") else "\n\n"
    return f"{current}{separator}{content}\n"
