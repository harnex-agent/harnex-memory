from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "harnex-memory/v1"


class DocumentKind(StrEnum):
    SKILL = "skill"
    RULE = "rule"
    HOOK = "hook"


class TargetKind(StrEnum):
    CODEX_AGENTS = "codex_agents"
    CODEX_SKILL = "codex_skill"
    CODEX_CONFIG = "codex_config"
    CODEX_RULES = "codex_rules"
    CODEX_HOOKS = "codex_hooks"
    CLAUDE_AGENTS = "claude_agents"
    CLAUDE_SKILL = "claude_skill"
    LEGACY_SKILL = "legacy_skill"
    LEGACY_RULE = "legacy_rule"
    LEGACY_HOOK = "legacy_hook"
    SKILL = "skill"
    RULE = "rule"
    HOOK = "hook"


class InsertionStrategy(StrEnum):
    APPEND_SECTION = "append_section"
    APPEND_BULLET = "append_bullet"
    CREATE_FILE = "create_file"
    REPLACE_MANAGED_BLOCK = "replace_managed_block"


class ChangeRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MemoryScope(StrEnum):
    GLOBAL_USER = "global_user"
    PROJECT_ROOT = "project_root"
    PROJECT_CODEX = "project_codex"
    PROJECT_CLAUDE = "project_claude"
    NESTED_PROJECT = "nested_project"
    MANAGED = "managed"


class ItemFormat(StrEnum):
    MARKDOWN_SECTION = "markdown_section"
    MARKDOWN_BULLET = "markdown_bullet"
    STARLARK_RULE = "starlark_rule"
    TOML_CONFIG = "toml_config"
    JSON_HOOK = "json_hook"
    SKILL_DOCUMENT = "skill_document"


class ItemStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SHADOWED = "shadowed"
    CONFLICT = "conflict"
    READ_ONLY = "read_only"
    DELETED = "deleted"


class ItemAction(StrEnum):
    DELETE = "delete"
    DISABLE = "disable"
    ENABLE = "enable"


class RecommendationKind(StrEnum):
    DIRECT_CONSTRAINT = "direct_constraint"
    REPEATED_PROMPT = "repeated_prompt"
    LLM_REVIEW = "llm_review"


class RecommendationStatus(StrEnum):
    PENDING = "pending"
    APPLIED = "applied"
    DISMISSED = "dismissed"
    STALE = "stale"


class RecommendationOrigin(StrEnum):
    HEURISTIC = "heuristic"
    LLM_REVIEW = "llm_review"


@dataclass(frozen=True)
class DocumentStatus:
    kind: DocumentKind
    path: str
    exists: bool
    target_kind: str | None = None
    agent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TextSpan:
    start_line: int
    end_line: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TextSpan:
        return cls(start_line=int(data["start_line"]), end_line=int(data["end_line"]))


@dataclass(frozen=True)
class MemoryItem:
    document_kind: DocumentKind
    target_kind: str
    scope: str
    path: str
    title: str
    body: str
    format: str
    status: str = ItemStatus.ACTIVE.value
    span: TextSpan | None = None
    source_hash: str = ""
    reason: str = ""
    agent: str = ""
    id: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        source_hash = self.source_hash or stable_item_source_hash(self.body)
        object.__setattr__(self, "source_hash", source_hash)
        if not self.id:
            object.__setattr__(
                self,
                "id",
                stable_item_id(
                    scope=self.scope,
                    path=self.path,
                    document_kind=self.document_kind,
                    target_kind=self.target_kind,
                    item_format=self.format,
                    span=self.span,
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["document_kind"] = self.document_kind.value
        data["span"] = self.span.to_dict() if self.span else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryItem:
        span_data = data.get("span")
        return cls(
            document_kind=DocumentKind(data["document_kind"]),
            target_kind=str(data["target_kind"]),
            scope=str(data["scope"]),
            path=str(data["path"]),
            title=str(data["title"]),
            body=str(data["body"]),
            format=str(data["format"]),
            status=str(data.get("status") or ItemStatus.ACTIVE.value),
            span=TextSpan.from_dict(span_data) if span_data else None,
            source_hash=str(data.get("source_hash") or ""),
            reason=str(data.get("reason") or ""),
            agent=str(data.get("agent") or ""),
            id=str(data.get("id") or ""),
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class PromptRecord:
    prompt: str
    source: str
    project_root: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    id: str = field(default_factory=lambda: uuid4().hex)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptRecord:
        return cls(
            prompt=str(data["prompt"]),
            source=str(data["source"]),
            project_root=str(data["project_root"]),
            metadata=dict(data.get("metadata", {})),
            timestamp=str(data.get("timestamp") or datetime.now(UTC).isoformat()),
            id=str(data.get("id") or uuid4().hex),
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class MemoryCandidate:
    target: DocumentKind
    title: str
    content: str
    reason: str
    evidence: list[str]
    risk: ChangeRisk = ChangeRisk.LOW
    target_kind: str | None = None
    target_path: str | None = None
    insertion_strategy: str | None = None
    section: str | None = None
    id: str = ""

    def __post_init__(self) -> None:
        target_kind = self.target_kind or default_target_kind(self.target)
        insertion_strategy = self.insertion_strategy or InsertionStrategy.APPEND_SECTION.value
        object.__setattr__(self, "target_kind", str(target_kind))
        object.__setattr__(self, "insertion_strategy", str(insertion_strategy))
        if not self.id:
            object.__setattr__(
                self,
                "id",
                stable_candidate_id(
                    target=self.target,
                    target_kind=str(target_kind),
                    target_path=self.target_path,
                    title=self.title,
                    content=self.content,
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FileChange:
    path: str
    before: str
    after: str
    diff: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Preview:
    project_root: str
    preview_id: str
    source: str
    candidates: list[MemoryCandidate]
    file_changes: list[FileChange]
    warnings: list[str] = field(default_factory=list)
    action: str | None = None
    items: list[MemoryItem] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        data["file_changes"] = [change.to_dict() for change in self.file_changes]
        data["items"] = [item.to_dict() for item in self.items]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Preview:
        return cls(
            project_root=str(data["project_root"]),
            preview_id=str(data["preview_id"]),
            source=str(data["source"]),
            candidates=[
                MemoryCandidate(
                    target=DocumentKind(candidate["target"]),
                    title=str(candidate["title"]),
                    content=str(candidate["content"]),
                    reason=str(candidate["reason"]),
                    evidence=[str(item) for item in candidate.get("evidence", [])],
                    risk=ChangeRisk(candidate.get("risk", ChangeRisk.LOW)),
                    target_kind=(
                        str(candidate["target_kind"]) if candidate.get("target_kind") else None
                    ),
                    target_path=str(candidate["target_path"])
                    if candidate.get("target_path")
                    else None,
                    insertion_strategy=str(candidate["insertion_strategy"])
                    if candidate.get("insertion_strategy")
                    else None,
                    section=str(candidate["section"]) if candidate.get("section") else None,
                    id=str(candidate["id"]) if candidate.get("id") else "",
                )
                for candidate in data.get("candidates", [])
            ],
            file_changes=[
                FileChange(
                    path=str(change["path"]),
                    before=str(change.get("before", "")),
                    after=str(change.get("after", "")),
                    diff=str(change.get("diff", "")),
                )
                for change in data.get("file_changes", [])
            ],
            warnings=[str(item) for item in data.get("warnings", [])],
            action=str(data["action"]) if data.get("action") else None,
            items=[MemoryItem.from_dict(item) for item in data.get("items", [])],
            blocked_reasons=[str(item) for item in data.get("blocked_reasons", [])],
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class Recommendation:
    kind: str
    title: str
    reason: str
    preview_id: str
    preview_path: str
    target_path: str
    target_kind: str
    risk: str
    evidence: list[str]
    candidate_id: str
    status: str = RecommendationStatus.PENDING.value
    dismissed_reason: str = ""
    origin: str = RecommendationOrigin.HEURISTIC.value
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    id: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(
                self,
                "id",
                stable_recommendation_id(kind=self.kind, candidate_id=self.candidate_id),
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Recommendation:
        return cls(
            kind=str(data["kind"]),
            title=str(data["title"]),
            reason=str(data["reason"]),
            preview_id=str(data["preview_id"]),
            preview_path=str(data["preview_path"]),
            target_path=str(data.get("target_path") or ""),
            target_kind=str(data.get("target_kind") or ""),
            risk=str(data.get("risk") or ChangeRisk.LOW.value),
            evidence=[str(item) for item in data.get("evidence", [])],
            candidate_id=str(data["candidate_id"]),
            status=str(data.get("status") or RecommendationStatus.PENDING.value),
            dismissed_reason=str(data.get("dismissed_reason") or ""),
            origin=str(data.get("origin") or RecommendationOrigin.HEURISTIC.value),
            created_at=str(data.get("created_at") or datetime.now(UTC).isoformat()),
            updated_at=str(data.get("updated_at") or datetime.now(UTC).isoformat()),
            id=str(data.get("id") or ""),
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
        )


def path_to_str(path: Path) -> str:
    return str(path)


def default_target_kind(target: DocumentKind) -> str:
    if target == DocumentKind.SKILL:
        return TargetKind.SKILL.value
    if target == DocumentKind.HOOK:
        return TargetKind.HOOK.value
    return TargetKind.RULE.value


def stable_candidate_id(
    target: DocumentKind,
    target_kind: str,
    target_path: str | None,
    title: str,
    content: str,
) -> str:
    digest = sha256()
    digest.update(str(target).encode("utf-8"))
    digest.update(b"\0")
    digest.update(target_kind.encode("utf-8"))
    digest.update(b"\0")
    digest.update((target_path or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update(title.strip().encode("utf-8"))
    digest.update(b"\0")
    digest.update(content.strip().encode("utf-8"))
    return digest.hexdigest()[:16]


def stable_item_source_hash(body: str) -> str:
    digest = sha256()
    digest.update(body.encode("utf-8"))
    return digest.hexdigest()[:16]


def stable_item_id(
    scope: str,
    path: str,
    document_kind: DocumentKind,
    target_kind: str,
    item_format: str,
    span: TextSpan | None,
) -> str:
    digest = sha256()
    digest.update(scope.encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.encode("utf-8"))
    digest.update(b"\0")
    digest.update(document_kind.value.encode("utf-8"))
    digest.update(b"\0")
    digest.update(target_kind.encode("utf-8"))
    digest.update(b"\0")
    digest.update(item_format.encode("utf-8"))
    digest.update(b"\0")
    if span:
        digest.update(str(span.start_line).encode("utf-8"))
        digest.update(b":")
        digest.update(str(span.end_line).encode("utf-8"))
    else:
        digest.update(b"no-span")
    return digest.hexdigest()[:16]


def stable_recommendation_id(kind: str, candidate_id: str) -> str:
    digest = sha256()
    digest.update(kind.encode("utf-8"))
    digest.update(b"\0")
    digest.update(candidate_id.encode("utf-8"))
    return digest.hexdigest()[:16]
