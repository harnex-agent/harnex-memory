from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "harnex-memory/v1"


class DocumentKind(StrEnum):
    SKILL = "skill"
    RULE = "rule"
    HOOK = "hook"


class ChangeRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class DocumentStatus:
    kind: DocumentKind
    path: str
    exists: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        data["file_changes"] = [change.to_dict() for change in self.file_changes]
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
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
        )


def path_to_str(path: Path) -> str:
    return str(path)
