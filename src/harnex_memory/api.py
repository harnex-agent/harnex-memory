from __future__ import annotations

from pathlib import Path
from typing import Any

from harnex_memory.core.analyzer import suggest_candidates
from harnex_memory.core.apply import apply_preview_changes
from harnex_memory.core.documents import list_document_statuses
from harnex_memory.core.models import DocumentKind, DocumentStatus, Preview, PromptRecord
from harnex_memory.core.paths import ensure_inside_project, resolve_project_root
from harnex_memory.core.preview import (
    build_candidates_preview,
    build_document_preview,
    read_preview,
    write_preview,
)
from harnex_memory.core.prompt_store import append_prompt_record, read_prompt_records


def list_documents(project_root: str | Path) -> list[DocumentStatus]:
    root = resolve_project_root(project_root)
    return list_document_statuses(root)


def preview_document_update(
    project_root: str | Path,
    target: str | DocumentKind,
    content: str,
    source: str = "api",
) -> tuple[Preview, Path]:
    root = resolve_project_root(project_root)
    kind = DocumentKind(target)
    preview = build_document_preview(root, kind, content, source)
    path = write_preview(root, preview)
    return preview, path


def apply_preview(project_root: str | Path, preview_path: str | Path) -> Path:
    root = resolve_project_root(project_root)
    path = ensure_inside_project(root, preview_path)
    preview = read_preview(path)
    return apply_preview_changes(root, preview)


def record_prompt(
    project_root: str | Path,
    prompt: str,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> PromptRecord:
    root = resolve_project_root(project_root)
    return append_prompt_record(root, prompt, source, metadata)


def suggest_prompt_updates(
    project_root: str | Path,
    min_count: int = 2,
    source: str = "prompt-suggest",
) -> tuple[Preview | None, Path | None]:
    root = resolve_project_root(project_root)
    records = read_prompt_records(root)
    candidates = suggest_candidates(records, min_count=min_count)
    if not candidates:
        return None, None
    preview = build_candidates_preview(root, candidates, source=source)
    path = write_preview(root, preview)
    return preview, path
