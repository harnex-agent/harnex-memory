"""Optional LLM-style review pass — a dependency-free seam.

harnex-memory classifies prompts heuristically with NO external LLM calls. This
module adds an *optional* extension point: a Reviewer inspects a prompt (and the
prior records) and proposes extra MemoryCandidates that an agent "decided" are
worth saving. Reviewer output is routed through the normal recommendation flow
(deduped, previewed, staged as ``pending`` with origin ``llm_review``) and is
NEVER auto-applied — the user still approves/dismisses in the GUI.

The default is no reviewer (pure heuristics). To enable one WITHOUT harnex taking
on an LLM dependency, point the ``HARNEX_MEMORY_REVIEWER`` env var at a factory::

    HARNEX_MEMORY_REVIEWER="my_pkg.my_reviewer:build"

where ``build`` is a zero-arg callable (or a Reviewer attribute) returning a
Reviewer instance.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from harnex_memory.core.models import MemoryCandidate, PromptRecord

REVIEWER_ENV_VAR = "HARNEX_MEMORY_REVIEWER"


@runtime_checkable
class Reviewer(Protocol):
    """Proposes memory candidates from a prompt and its history."""

    def review(
        self,
        project_root: Path,
        prompt: str,
        records: list[PromptRecord],
    ) -> list[MemoryCandidate]:
        ...


class NullReviewer:
    """Default reviewer: proposes nothing (keeps the pure-heuristic behavior)."""

    def review(
        self,
        project_root: Path,
        prompt: str,
        records: list[PromptRecord],
    ) -> list[MemoryCandidate]:
        return []


def resolve_reviewer(spec: str | None = None) -> Reviewer | None:
    """Resolve a Reviewer from a ``module:attr`` spec or the env var.

    Returns ``None`` when unset (the default — no LLM pass). ``attr`` may be a
    Reviewer instance or a zero-arg callable returning one.
    """
    if spec is None:
        spec = os.environ.get(REVIEWER_ENV_VAR, "")
    spec = spec.strip()
    if not spec:
        return None
    module_name, separator, attr = spec.partition(":")
    if not separator or not module_name.strip() or not attr.strip():
        raise ValueError(f"Invalid reviewer spec (expected 'module:attr'): {spec!r}")
    target = getattr(importlib.import_module(module_name.strip()), attr.strip())
    return target() if callable(target) else target
