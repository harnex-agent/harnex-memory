from __future__ import annotations

import difflib
import json
from pathlib import Path
from uuid import uuid4

from harnex_memory.core.documents import read_document, read_document_at_path
from harnex_memory.core.models import (
    DocumentKind,
    FileChange,
    InsertionStrategy,
    MemoryCandidate,
    Preview,
)
from harnex_memory.core.paths import (
    document_path,
    ensure_inside_project,
    previews_dir,
    project_relative_path,
)


def make_diff(path: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
        )
    )


def build_document_preview(
    project_root: Path,
    target: DocumentKind,
    content: str,
    source: str,
) -> Preview:
    before = read_document(project_root, target)
    after = content if content.endswith("\n") else f"{content}\n"
    path = document_path(project_root, target)
    change = FileChange(
        path=str(path),
        before=before,
        after=after,
        diff=make_diff(path, before, after),
    )
    candidate = MemoryCandidate(
        target=target,
        title=f"{target.value} 문서 변경",
        content=after,
        reason=f"{source}에서 요청한 문서 변경입니다.",
        evidence=[source],
        target_path=project_relative_path(project_root, path),
        insertion_strategy=InsertionStrategy.REPLACE_MANAGED_BLOCK.value,
    )
    return Preview(
        project_root=str(project_root),
        preview_id=uuid4().hex,
        source=source,
        candidates=[candidate],
        file_changes=[change],
    )


def build_candidates_preview(
    project_root: Path,
    candidates: list[MemoryCandidate],
    source: str,
) -> Preview:
    file_changes: list[FileChange] = []
    candidates_by_target: dict[Path, list[MemoryCandidate]] = {}
    for candidate in candidates:
        path = target_path_for_candidate(project_root, candidate)
        candidates_by_target.setdefault(path, []).append(candidate)

    for path, target_candidates in candidates_by_target.items():
        first_candidate = target_candidates[0]
        before = read_document_at_path(
            project_root,
            path,
            fallback_kind=first_candidate.target,
            target_kind=first_candidate.target_kind,
        )
        after = before
        for candidate in target_candidates:
            after = append_content(after, candidate.content)
        file_changes.append(
            FileChange(
                path=str(path),
                before=before,
                after=after,
                diff=make_diff(path, before, after),
            )
        )
    return Preview(
        project_root=str(project_root),
        preview_id=uuid4().hex,
        source=source,
        candidates=candidates,
        file_changes=file_changes,
    )


def append_content(current: str, addition: str) -> str:
    content = addition.strip()
    if not content or content in current:
        return current
    separator = "" if current.endswith("\n\n") else "\n\n" if current.endswith("\n") else "\n\n"
    return f"{current}{separator}{content}\n"


def target_path_for_candidate(project_root: Path, candidate: MemoryCandidate) -> Path:
    if candidate.target_path:
        return ensure_inside_project(project_root, candidate.target_path)
    return document_path(project_root, candidate.target)


def write_preview(project_root: Path, preview: Preview) -> Path:
    directory = previews_dir(project_root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{preview.preview_id}.json"
    path.write_text(json.dumps(preview.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_preview(path: Path) -> Preview:
    return Preview.from_dict(json.loads(path.read_text(encoding="utf-8")))
