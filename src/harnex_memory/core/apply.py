from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from harnex_memory.core.models import Preview
from harnex_memory.core.paths import apply_results_dir, ensure_inside_project


def apply_preview_changes(project_root: Path, preview: Preview) -> Path:
    written_files: list[str] = []
    for change in preview.file_changes:
        path = ensure_inside_project(project_root, change.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(change.after, encoding="utf-8")
        written_files.append(str(path))

    result_id = uuid4().hex
    result = {
        "schema_version": preview.schema_version,
        "apply_id": result_id,
        "preview_id": preview.preview_id,
        "project_root": str(project_root),
        "written_files": written_files,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    directory = apply_results_dir(project_root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{result_id}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
