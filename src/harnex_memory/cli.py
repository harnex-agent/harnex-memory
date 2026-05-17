from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from harnex_memory.api import (
    apply_preview,
    list_documents,
    preview_constraint_update,
    preview_document_update,
    record_prompt,
    suggest_prompt_updates,
)
from harnex_memory.core.models import DocumentKind
from harnex_memory.core.paths import ensure_inside_project, resolve_project_root

app = typer.Typer(help="Manage harnex memory documents and prompt records.")
docs_app = typer.Typer(help="Manage skill/rule/hook documents.")
prompt_app = typer.Typer(help="Record and analyze prompt memory.")
constraint_app = typer.Typer(help="Preview direct user constraints.")
app.add_typer(docs_app, name="docs")
app.add_typer(prompt_app, name="prompt")
app.add_typer(constraint_app, name="constraint")


ProjectRootOption = Annotated[
    Path,
    typer.Option("--project-root", exists=True, file_okay=False, dir_okay=True, readable=True),
]


def _print_json(data: object) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@docs_app.command("list")
def docs_list(project_root: ProjectRootOption) -> None:
    statuses = list_documents(project_root)
    _print_json({"documents": [status.to_dict() for status in statuses]})


@docs_app.command("preview")
def docs_preview(
    project_root: ProjectRootOption,
    target: Annotated[DocumentKind, typer.Option("--target", case_sensitive=False)],
    content: Annotated[
        Path,
        typer.Option("--content", exists=True, file_okay=True, dir_okay=False, readable=True),
    ],
    source: Annotated[str, typer.Option("--source")] = "docs-preview",
) -> None:
    root = resolve_project_root(project_root)
    content_path = ensure_inside_project(root, content)
    preview, path = preview_document_update(
        root,
        target=target,
        content=content_path.read_text(encoding="utf-8"),
        source=source,
    )
    _print_json({"preview_path": str(path), "preview": preview.to_dict()})


@docs_app.command("apply")
def docs_apply(
    project_root: ProjectRootOption,
    preview: Annotated[Path, typer.Option("--preview", exists=True, readable=True)],
) -> None:
    result_path = apply_preview(project_root, preview)
    _print_json({"apply_result_path": str(result_path)})


@constraint_app.command("preview")
def constraint_preview(
    project_root: ProjectRootOption,
    constraint: Annotated[str, typer.Option("--constraint")],
    source: Annotated[str, typer.Option("--source")] = "constraint-preview",
    metadata: Annotated[list[str] | None, typer.Option("--metadata")] = None,
) -> None:
    preview, path = preview_constraint_update(
        project_root,
        constraint=constraint,
        source=source,
        metadata=_parse_metadata(metadata or []),
    )
    _print_json({"preview_path": str(path), "preview": preview.to_dict()})


@prompt_app.command("record")
def prompt_record(
    project_root: ProjectRootOption,
    source: Annotated[str, typer.Option("--source")],
    prompt: Annotated[str, typer.Option("--prompt")],
    metadata: Annotated[list[str] | None, typer.Option("--metadata")] = None,
) -> None:
    record = record_prompt(
        project_root,
        prompt=prompt,
        source=source,
        metadata=_parse_metadata(metadata or []),
    )
    _print_json({"record": record.to_dict()})


@prompt_app.command("suggest")
def prompt_suggest(
    project_root: ProjectRootOption,
    min_count: Annotated[int, typer.Option("--min-count", min=2)] = 2,
) -> None:
    preview, path = suggest_prompt_updates(project_root, min_count=min_count)
    if preview is None:
        _print_json({"preview_path": None, "preview": None, "candidates": []})
        return
    _print_json({"preview_path": str(path), "preview": preview.to_dict()})


def _parse_metadata(entries: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise typer.BadParameter("metadata must use key=value format")
        key, value = entry.split("=", 1)
        parsed[key] = value
    return parsed


def main() -> None:
    app()


if __name__ == "__main__":
    main()
