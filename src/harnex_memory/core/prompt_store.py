from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from harnex_memory.core.models import PromptRecord
from harnex_memory.core.paths import prompt_records_path


def normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.strip().casefold())


def append_prompt_record(
    project_root: Path,
    prompt: str,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> PromptRecord:
    record = PromptRecord(
        prompt=prompt,
        source=source,
        project_root=str(project_root),
        metadata=metadata or {},
    )
    path = prompt_records_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True))
        file.write("\n")
    return record


def read_prompt_records(project_root: Path) -> list[PromptRecord]:
    path = prompt_records_path(project_root)
    if not path.exists():
        return []
    records: list[PromptRecord] = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            records.append(PromptRecord.from_dict(json.loads(line)))
    return records
