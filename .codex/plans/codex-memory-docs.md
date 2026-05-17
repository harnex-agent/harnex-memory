# Codex Memory Document Management Plan

## Clarify Status

- Source: harnex-clarify MCP
- Status: ready
- Ambiguity score: 0.105
- Goal clarity: 0.90
- Target/scope clarity: 0.86
- Context/constraint clarity: 0.90
- Success criteria clarity: 0.92

## Goal

harnex-memory should turn repeated prompts and user-provided constraints into safe Codex document update candidates.

The first supported agent target is Codex. The system should discover Codex-facing documents, classify prompt/constraint content into the right document target, generate preview JSON with diffs, and only write files through the existing approved apply flow.

## In Scope

- Discover Codex document locations under a selected project root.
- Treat project-root `AGENTS.md` as the primary Codex rule document.
- Treat `.codex/skills/*/SKILL.md` and `.codex/skills/*.md` as Codex skill documents.
- Keep existing `.harnex/memory/skills.md`, `.harnex/memory/rules.md`, and `.harnex/memory/hooks.md` compatibility.
- Add deterministic rule-based classification for repeated prompts and direct constraints.
- Include concrete target metadata in memory candidates and preview JSON.
- Add public API and CLI entrypoints for previewing user constraints.
- Preserve preview-before-apply behavior.

## Out of Scope

- External LLM calls for classification.
- Claude or other agent-specific document conventions beyond extension points.
- Automatic file writes without preview/apply approval.
- Broad refactors unrelated to document discovery, classification, preview, and apply.

## Data Model Changes

Extend `MemoryCandidate` with fields similar to:

- `id`: stable generated candidate id.
- `target`: existing broad document kind for compatibility.
- `target_kind`: more specific target such as `codex_agents`, `codex_skill`, `rule`, or `hook`.
- `target_path`: project-root-relative or absolute safe path selected for the candidate.
- `insertion_strategy`: append section, append bullet, create file, or replace managed block.
- `section`: optional heading or managed section label.

Keep `target`, `title`, `content`, `reason`, `evidence`, and `risk` backward compatible.

## Core Modules

### `core/codex_docs.py`

- Discover `AGENTS.md`.
- Discover `.codex/skills/*/SKILL.md`.
- Discover `.codex/skills/*.md`.
- Return structured document statuses with kind, path, exists, and agent target metadata.
- Provide default paths/templates when a target document does not exist.

### `core/classifier.py`

- Classify prompt or constraint text without LLM calls.
- Route general project/process constraints to `AGENTS.md`.
- Route skill creation/update instructions to a Codex skill document.
- Route hook/pre-commit/post-commit automation instructions to hook-compatible targets.
- Return reason, confidence-like label if useful, risk, target_kind, and insertion_strategy.

### `core/analyzer.py`

- Keep repeated prompt grouping behavior.
- Replace only the target inference part with classifier-backed target selection.
- Populate target path and insertion strategy on candidates.
- Avoid duplicate candidates for identical normalized content and target path.

### `core/preview.py`

- Build previews from candidates using `target_path` when present.
- Continue to support legacy `DocumentKind` path mapping.
- Ensure preview JSON includes candidate metadata and unified diff.
- Do not change files while previewing.

### `core/documents.py` and `core/paths.py`

- Add Codex document listing alongside existing harnex memory documents.
- Keep path resolution constrained to project root.
- Add helpers for safe project-relative Codex paths.

### `api.py`

- Keep existing functions compatible.
- Add a function such as `preview_constraint_update(project_root, constraint, source="constraint-preview", metadata=None)`.
- Add a function for listing Codex document statuses if it should be separate from existing `list_documents`.

### `cli.py`

- Keep Typer handlers thin.
- Extend `docs list` output to include Codex documents or add `docs list --agent codex`.
- Add a preview command for direct constraints, for example:

```text
harnex-memory constraint preview --project-root <path> --constraint <text>
```

or:

```text
harnex-memory docs classify --project-root <path> --text <text> --source <source>
```

Pick one command shape during implementation and document it in README.

## Preview JSON Requirements

Each preview should expose:

- `schema_version`
- `project_root`
- `preview_id`
- `source`
- `candidates`
- `file_changes`
- `warnings`

Each candidate should expose:

- `id`
- `target`
- `target_kind`
- `target_path`
- `title`
- `content`
- `reason`
- `evidence`
- `risk`
- `insertion_strategy`
- optional `section`

Each file change should expose:

- `path`
- `before`
- `after`
- `diff`

## Acceptance Tests

- `docs list` or the corresponding API detects project-root `AGENTS.md`.
- Codex skill discovery detects `.codex/skills/foo/SKILL.md`.
- Codex skill discovery detects `.codex/skills/foo.md`.
- Repeated prompts produce candidates with `target_kind`, `target_path`, and `insertion_strategy`.
- Direct user constraints preview into `AGENTS.md` when they are general process rules.
- Skill-related constraints preview into an appropriate skill document.
- Hook-related prompts still route to hook-compatible targets.
- Preview does not write target files.
- Apply writes only files listed in an approved preview.
- Duplicate content is not appended twice.
- Paths outside the project root are rejected.
- `python -m pytest` passes.
- `python -m ruff check .` passes.

## Suggested Implementation Order

1. Add failing tests for Codex document discovery.
2. Implement `codex_docs.py` and safe path helpers.
3. Add tests for classifier decisions.
4. Implement deterministic classifier.
5. Extend `MemoryCandidate` serialization/deserialization while preserving existing fields.
6. Update analyzer to use classifier output.
7. Update preview generation to honor candidate target paths.
8. Add public API for direct constraint preview.
9. Add CLI command and README examples.
10. Run pytest and Ruff, then tighten any ambiguous output names.
