from __future__ import annotations

from pathlib import Path

from harnex_memory.core.models import DocumentKind


class PathSafetyError(ValueError):
    """Raised when a path resolves outside the selected project root."""


DOCUMENT_PATHS: dict[DocumentKind, Path] = {
    DocumentKind.SKILL: Path(".harnex/memory/skills.md"),
    DocumentKind.RULE: Path(".harnex/memory/rules.md"),
    DocumentKind.HOOK: Path(".harnex/memory/hooks.md"),
}


def resolve_project_root(project_root: str | Path) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")
    return root


def ensure_inside_project(project_root: Path, path: str | Path) -> Path:
    root = project_root.resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.expanduser().resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PathSafetyError(f"Path escapes project root: {resolved}") from exc
    return resolved


def project_relative_path(project_root: Path, path: str | Path) -> str:
    resolved = ensure_inside_project(project_root, path)
    return resolved.relative_to(project_root.resolve()).as_posix()


def memory_dir(project_root: Path) -> Path:
    return ensure_inside_project(project_root, ".harnex/memory")


def previews_dir(project_root: Path) -> Path:
    return ensure_inside_project(project_root, ".harnex/memory/previews")


def apply_results_dir(project_root: Path) -> Path:
    return ensure_inside_project(project_root, ".harnex/memory/apply-results")


def prompt_records_path(project_root: Path) -> Path:
    return ensure_inside_project(project_root, ".harnex/memory/prompt-records.jsonl")


def document_path(project_root: Path, kind: DocumentKind) -> Path:
    return ensure_inside_project(project_root, DOCUMENT_PATHS[kind])
