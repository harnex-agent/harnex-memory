from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

from harnex_memory.core.codex_docs import discover_codex_skill_paths
from harnex_memory.core.models import (
    SCHEMA_VERSION,
    DocumentKind,
    FileChange,
    ItemAction,
    ItemFormat,
    ItemStatus,
    MemoryItem,
    MemoryScope,
    Preview,
    TargetKind,
    TextSpan,
    stable_item_source_hash,
)
from harnex_memory.core.paths import (
    DOCUMENT_PATHS,
    disabled_items_path,
    document_path,
    ensure_inside_project,
    project_relative_path,
)
from harnex_memory.core.preview import make_diff

DISABLED_STORE_VERSION = f"{SCHEMA_VERSION}/disabled-items"
_BULLET_PATTERN = re.compile(r"^(?P<indent>\s*)[-*]\s+(?P<title>.+?)\s*$")
_HEADING_PATTERN = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")


class ItemActionError(ValueError):
    """Raised when a GUI item action cannot be previewed."""


def list_memory_items(
    project_root: Path,
    cwd: str | Path | None = None,
    include_readonly: bool = False,
) -> list[MemoryItem]:
    root = project_root.resolve()
    items: list[MemoryItem] = []

    items.extend(_list_legacy_markdown_items(root))
    items.extend(_list_agents_items(root, cwd))
    items.extend(_list_codex_skill_items(root))
    items.extend(read_disabled_items(root))

    if not include_readonly:
        return [item for item in items if item.status != ItemStatus.READ_ONLY.value]
    return items


def get_memory_item(project_root: Path, item_id: str) -> MemoryItem:
    for item in list_memory_items(project_root, include_readonly=True):
        if item.id == item_id:
            return item
    raise ItemActionError(f"Memory item not found: {item_id}")


def build_memory_item_action_preview(
    project_root: Path,
    item_id: str,
    action: str | ItemAction,
    expected_source_hash: str | None = None,
    cwd: str | Path | None = None,
) -> Preview:
    root = project_root.resolve()
    action_value = ItemAction(action).value
    item = _find_item(root, item_id, cwd)

    if expected_source_hash and expected_source_hash != item.source_hash:
        return _blocked_preview(
            root,
            action_value,
            item,
            f"Stale source hash for item {item.id}.",
        )

    if action_value == ItemAction.ENABLE.value:
        return _build_enable_preview(root, item)

    if item.status != ItemStatus.ACTIVE.value:
        return _blocked_preview(
            root,
            action_value,
            item,
            f"Only active items can be {action_value}d; current status is {item.status}.",
        )

    if action_value == ItemAction.DELETE.value:
        return _build_delete_preview(root, item)
    if action_value == ItemAction.DISABLE.value:
        return _build_disable_preview(root, item)

    raise ItemActionError(f"Unsupported item action: {action_value}")


def read_disabled_items(project_root: Path) -> list[MemoryItem]:
    path = disabled_items_path(project_root)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        replace(MemoryItem.from_dict(item), status=ItemStatus.DISABLED.value)
        for item in data.get("items", [])
    ]


def render_disabled_items(items: list[MemoryItem]) -> str:
    data = {
        "schema_version": DISABLED_STORE_VERSION,
        "items": [
            replace(item, status=ItemStatus.DISABLED.value).to_dict()
            for item in sorted(items, key=lambda candidate: candidate.id)
        ],
    }
    return f"{json.dumps(data, ensure_ascii=False, indent=2)}\n"


def _list_legacy_markdown_items(project_root: Path) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    for kind in DOCUMENT_PATHS:
        path = document_path(project_root, kind)
        if not path.exists():
            continue
        items.extend(
            _parse_markdown_items(
                project_root=project_root,
                path=path,
                document_kind=kind,
                target_kind=_legacy_target_kind(kind),
                scope=MemoryScope.PROJECT_ROOT.value,
                status=ItemStatus.ACTIVE.value,
                reason="",
                item_format=None,
            )
        )
    return items


def _list_agents_items(project_root: Path, cwd: str | Path | None) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    for directory in _project_directories(project_root, cwd):
        agents_path = directory / "AGENTS.md"
        override_path = directory / "AGENTS.override.md"
        scope = (
            MemoryScope.PROJECT_ROOT.value
            if directory == project_root
            else MemoryScope.NESTED_PROJECT.value
        )
        if agents_path.exists():
            status = (
                ItemStatus.SHADOWED.value
                if override_path.exists()
                else ItemStatus.ACTIVE.value
            )
            reason = (
                "AGENTS.override.md in the same directory shadows AGENTS.md."
                if status == ItemStatus.SHADOWED.value
                else ""
            )
            items.extend(
                _parse_markdown_items(
                    project_root=project_root,
                    path=agents_path,
                    document_kind=DocumentKind.RULE,
                    target_kind=TargetKind.CODEX_AGENTS.value,
                    scope=scope,
                    status=status,
                    reason=reason,
                    item_format=None,
                )
            )
        if override_path.exists():
            items.extend(
                _parse_markdown_items(
                    project_root=project_root,
                    path=override_path,
                    document_kind=DocumentKind.RULE,
                    target_kind=TargetKind.CODEX_AGENTS.value,
                    scope=scope,
                    status=ItemStatus.ACTIVE.value,
                    reason="",
                    item_format=None,
                )
            )
    return items


def _list_codex_skill_items(project_root: Path) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    for path in discover_codex_skill_paths(project_root):
        items.extend(
            _parse_markdown_items(
                project_root=project_root,
                path=path,
                document_kind=DocumentKind.SKILL,
                target_kind=TargetKind.CODEX_SKILL.value,
                scope=MemoryScope.PROJECT_CODEX.value,
                status=ItemStatus.ACTIVE.value,
                reason="",
                item_format=ItemFormat.SKILL_DOCUMENT.value,
            )
        )

    title_counts: dict[str, int] = {}
    for item in items:
        key = item.title.casefold()
        title_counts[key] = title_counts.get(key, 0) + 1

    return [
        replace(
            item,
            status=ItemStatus.CONFLICT.value,
            reason="Another Codex skill with the same name was discovered.",
        )
        if title_counts[item.title.casefold()] > 1
        else item
        for item in items
    ]


def _parse_markdown_items(
    project_root: Path,
    path: Path,
    document_kind: DocumentKind,
    target_kind: str,
    scope: str,
    status: str,
    reason: str,
    item_format: str | None,
) -> list[MemoryItem]:
    text = path.read_text(encoding="utf-8")
    relative_path = project_relative_path(project_root, path)
    lines = text.splitlines(keepends=True)

    if item_format == ItemFormat.SKILL_DOCUMENT.value:
        return [
            MemoryItem(
                document_kind=document_kind,
                target_kind=target_kind,
                scope=scope,
                path=relative_path,
                title=_title_from_markdown_file(path, text),
                body=text,
                format=ItemFormat.SKILL_DOCUMENT.value,
                status=status,
                span=TextSpan(start_line=1, end_line=max(1, len(lines))),
                reason=reason,
            )
        ]

    items = _parse_bullet_items(
        document_kind=document_kind,
        target_kind=target_kind,
        scope=scope,
        path=relative_path,
        status=status,
        reason=reason,
        lines=lines,
    )
    items.extend(
        _parse_section_items(
            document_kind=document_kind,
            target_kind=target_kind,
            scope=scope,
            path=relative_path,
            status=status,
            reason=reason,
            lines=lines,
        )
    )
    if not items and text.strip():
        items.append(
            MemoryItem(
                document_kind=document_kind,
                target_kind=target_kind,
                scope=scope,
                path=relative_path,
                title=_first_non_empty_line(text),
                body=text,
                format=ItemFormat.MARKDOWN_SECTION.value,
                status=status,
                span=TextSpan(start_line=1, end_line=max(1, len(lines))),
                reason=reason,
            )
        )
    return items


def _parse_bullet_items(
    document_kind: DocumentKind,
    target_kind: str,
    scope: str,
    path: str,
    status: str,
    reason: str,
    lines: list[str],
) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    index = 0
    while index < len(lines):
        match = _BULLET_PATTERN.match(lines[index])
        if not match:
            index += 1
            continue
        end = _bullet_end(lines, index, len(match.group("indent")))
        body = "".join(lines[index:end])
        items.append(
            MemoryItem(
                document_kind=document_kind,
                target_kind=target_kind,
                scope=scope,
                path=path,
                title=match.group("title").strip(),
                body=body,
                format=ItemFormat.MARKDOWN_BULLET.value,
                status=status,
                span=TextSpan(start_line=index + 1, end_line=end),
                reason=reason,
            )
        )
        index = end
    return items


def _parse_section_items(
    document_kind: DocumentKind,
    target_kind: str,
    scope: str,
    path: str,
    status: str,
    reason: str,
    lines: list[str],
) -> list[MemoryItem]:
    heading_indexes = [
        index for index, line in enumerate(lines) if _HEADING_PATTERN.match(line)
    ]
    items: list[MemoryItem] = []
    for position, start in enumerate(heading_indexes):
        end = heading_indexes[position + 1] if position + 1 < len(heading_indexes) else len(lines)
        block = "".join(lines[start:end])
        if any(_BULLET_PATTERN.match(line) for line in lines[start:end]):
            continue
        if not block.strip():
            continue
        title_match = _HEADING_PATTERN.match(lines[start])
        title = title_match.group("title").strip() if title_match else lines[start].strip()
        items.append(
            MemoryItem(
                document_kind=document_kind,
                target_kind=target_kind,
                scope=scope,
                path=path,
                title=title,
                body=block,
                format=ItemFormat.MARKDOWN_SECTION.value,
                status=status,
                span=TextSpan(start_line=start + 1, end_line=end),
                reason=reason,
            )
        )
    return items


def _bullet_end(lines: list[str], start: int, indent: int) -> int:
    end = start + 1
    while end < len(lines):
        if _HEADING_PATTERN.match(lines[end]):
            break
        next_bullet = _BULLET_PATTERN.match(lines[end])
        if next_bullet and len(next_bullet.group("indent")) <= indent:
            break
        end += 1
    return end


def _build_delete_preview(project_root: Path, item: MemoryItem) -> Preview:
    change = _removal_change(project_root, item)
    if isinstance(change, str):
        return _blocked_preview(project_root, ItemAction.DELETE.value, item, change)
    return Preview(
        project_root=str(project_root),
        preview_id=_preview_id(),
        source="item-action",
        candidates=[],
        file_changes=[change],
        action=ItemAction.DELETE.value,
        items=[replace(item, status=ItemStatus.DELETED.value)],
    )


def _build_disable_preview(project_root: Path, item: MemoryItem) -> Preview:
    removal_change = _removal_change(project_root, item)
    if isinstance(removal_change, str):
        return _blocked_preview(project_root, ItemAction.DISABLE.value, item, removal_change)

    disabled_items = [
        candidate for candidate in read_disabled_items(project_root) if candidate.id != item.id
    ]
    disabled_item = replace(
        item,
        status=ItemStatus.DISABLED.value,
        reason="Disabled through harnex-memory item action.",
    )
    disabled_items.append(disabled_item)
    store_change = _disabled_store_change(project_root, disabled_items)
    return Preview(
        project_root=str(project_root),
        preview_id=_preview_id(),
        source="item-action",
        candidates=[],
        file_changes=[removal_change, store_change],
        action=ItemAction.DISABLE.value,
        items=[disabled_item],
    )


def _build_enable_preview(project_root: Path, item: MemoryItem) -> Preview:
    if item.status != ItemStatus.DISABLED.value:
        return _blocked_preview(
            project_root,
            ItemAction.ENABLE.value,
            item,
            f"Only disabled items can be enabled; current status is {item.status}.",
        )

    path = ensure_inside_project(project_root, item.path)
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    after = _append_restored_content(before, item.body)
    target_change = FileChange(
        path=str(path),
        before=before,
        after=after,
        diff=make_diff(path, before, after),
    )
    remaining_disabled_items = [
        candidate for candidate in read_disabled_items(project_root) if candidate.id != item.id
    ]
    store_change = _disabled_store_change(project_root, remaining_disabled_items)
    enabled_item = replace(item, status=ItemStatus.ACTIVE.value, reason="")
    return Preview(
        project_root=str(project_root),
        preview_id=_preview_id(),
        source="item-action",
        candidates=[],
        file_changes=[target_change, store_change],
        action=ItemAction.ENABLE.value,
        items=[enabled_item],
    )


def _removal_change(project_root: Path, item: MemoryItem) -> FileChange | str:
    if item.span is None:
        return f"Item {item.id} has no source span and cannot be changed safely."
    path = ensure_inside_project(project_root, item.path)
    if not path.exists():
        return f"Source file does not exist: {item.path}"
    before = path.read_text(encoding="utf-8")
    lines = before.splitlines(keepends=True)
    start = item.span.start_line - 1
    end = item.span.end_line
    if start < 0 or end > len(lines) or start >= end:
        return f"Item {item.id} source span is no longer valid."
    current_body = "".join(lines[start:end])
    if stable_item_source_hash(current_body) != item.source_hash:
        return f"Item {item.id} source content changed since it was listed."
    after = "".join([*lines[:start], *lines[end:]])
    return FileChange(
        path=str(path),
        before=before,
        after=after,
        diff=make_diff(path, before, after),
    )


def _disabled_store_change(project_root: Path, items: list[MemoryItem]) -> FileChange:
    path = disabled_items_path(project_root)
    before = path.read_text(encoding="utf-8") if path.exists() else render_disabled_items([])
    after = render_disabled_items(items)
    return FileChange(
        path=str(path),
        before=before,
        after=after,
        diff=make_diff(path, before, after),
    )


def _blocked_preview(project_root: Path, action: str, item: MemoryItem, reason: str) -> Preview:
    return Preview(
        project_root=str(project_root),
        preview_id=_preview_id(),
        source="item-action",
        candidates=[],
        file_changes=[],
        warnings=[reason],
        action=action,
        items=[item],
        blocked_reasons=[reason],
    )


def _find_item(project_root: Path, item_id: str, cwd: str | Path | None) -> MemoryItem:
    for item in list_memory_items(project_root, cwd=cwd, include_readonly=True):
        if item.id == item_id:
            return item
    raise ItemActionError(f"Memory item not found: {item_id}")


def _project_directories(project_root: Path, cwd: str | Path | None) -> list[Path]:
    if cwd is None:
        current = project_root
    else:
        current = ensure_inside_project(project_root, cwd)
        if current.exists() and current.is_file():
            current = current.parent
    current = current.resolve()
    root = project_root.resolve()
    relative_parts = current.relative_to(root).parts
    directories = [root]
    cursor = root
    for part in relative_parts:
        cursor = cursor / part
        directories.append(cursor)
    return directories


def _legacy_target_kind(kind: DocumentKind) -> str:
    if kind == DocumentKind.SKILL:
        return TargetKind.LEGACY_SKILL.value
    if kind == DocumentKind.HOOK:
        return TargetKind.LEGACY_HOOK.value
    return TargetKind.LEGACY_RULE.value


def _title_from_markdown_file(path: Path, text: str) -> str:
    for line in text.splitlines():
        match = _HEADING_PATTERN.match(line)
        if match:
            return match.group("title").strip()
    if path.name == "SKILL.md":
        return path.parent.name
    return path.stem


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped
    return "Untitled"


def _append_restored_content(current: str, body: str) -> str:
    content = body if body.endswith("\n") else f"{body}\n"
    if content.strip() and content.strip() in current:
        return current
    if not current:
        return content
    separator = "" if current.endswith("\n\n") else "\n" if current.endswith("\n") else "\n\n"
    return f"{current}{separator}{content}"


def _preview_id() -> str:
    from uuid import uuid4

    return uuid4().hex
