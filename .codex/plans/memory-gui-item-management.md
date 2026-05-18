# harnex-memory GUI item management plan

## Clarify status

- Source: harnex-clarify MCP
- Status: ready
- Ambiguity score: 0.1105
- Goal clarity: 0.92
- Target/scope clarity: 0.88
- Context/constraint clarity: 0.83
- Success criteria clarity: 0.91

## Goal

Expose skill/rule/hook document contents as structured items so a GUI can show,
select, delete, disable, and re-enable them without asking users to manually edit
Markdown files.

The implementation should keep the current safety model: preview first, write
only through apply, and never write outside the selected project root.

## Codex scope notes

Official Codex docs define these relevant layers:

- `AGENTS.md`: Codex reads global guidance from `CODEX_HOME` (default
  `~/.codex`) and project guidance from the project root down to the current
  working directory. Within the same directory, `AGENTS.override.md` suppresses
  `AGENTS.md`; across directories, files closer to the current directory appear
  later and can override earlier guidance semantically.
- Project `.codex/config.toml`: Codex reads project-scoped config from
  `.codex/config.toml` files from project root to current working directory; if
  the same key appears more than once, the closest config wins. Project `.codex`
  layers load only when trusted.
- Team Config: repo `.codex/` can hold shared `config.toml`, `rules/`, and
  `skills/` for the team. This means `<repo>/.codex` should be modeled as a
  project/team layer, not as a private personal layer.
- Rules: rules live under `rules/` next to active config layers. Matching
  command rules combine conservatively; the most restrictive decision wins.
- Hooks: hooks are loaded from user and project config layers. Multiple matching
  hook sources all run; higher-precedence layers do not replace lower-precedence
  hooks.
- Skills: skills are directories with `SKILL.md`. Codex supports reusable skill
  sources, including user and shared/team locations, but the docs do not define
  a universal "closest skill overrides older skill" rule. Duplicate skill names
  should therefore be surfaced as conflicts instead of silently shadowed.

Sources:

- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/config-advanced
- https://developers.openai.com/codex/rules
- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/skills

## Scope model

Add explicit scope metadata instead of hard-coding "personal/team/global" labels
into behavior.

Suggested scope enum:

- `global_user`: user-level Codex home files such as `~/.codex/AGENTS.md`,
  `~/.codex/config.toml`, `~/.codex/rules/`, and user hooks.
- `project_root`: project-root files such as `AGENTS.md` and legacy
  `.harnex/memory/*.md`.
- `project_codex`: trusted project `.codex/` files such as
  `.codex/config.toml`, `.codex/rules/`, `.codex/hooks.json`, and
  `.codex/skills/*/SKILL.md`.
- `nested_project`: nested `AGENTS.md`, `AGENTS.override.md`, or nested
  `.codex/config.toml` closer to the current working directory.
- `managed`: admin/system/cloud-managed configuration that harnex-memory may
  list as read-only when visible, but should not edit in this project module.

Phase 1 should write only project-root-contained files. Global/user and managed
sources can be listed as read-only later through an explicit opt-in provider.

## Item model

Introduce a GUI-facing document item model:

- `id`: stable hash from scope, document path, item kind, normalized text, and
  source span.
- `document_kind`: `skill`, `rule`, or `hook`.
- `target_kind`: more specific source type such as `codex_agents`,
  `codex_skill`, `codex_rules`, `codex_hooks`, `legacy_skill`, `legacy_rule`,
  or `legacy_hook`.
- `scope`: one of the scope enum values.
- `path`: project-relative path when inside the project, otherwise display-only
  source path for read-only providers.
- `title`: heading text, bullet preview, rule pattern, hook matcher, or skill
  name.
- `body`: item body text or structured config payload.
- `format`: `markdown_section`, `markdown_bullet`, `starlark_rule`,
  `toml_config`, `json_hook`, or `skill_document`.
- `status`: `active`, `disabled`, `shadowed`, `conflict`, `read_only`, or
  `deleted`.
- `span`: start/end line numbers for Markdown-backed items.
- `source_hash`: content hash used to detect stale GUI actions.
- `reason`: explanation for disabled/shadowed/conflict/read-only state.

## Operation semantics

Selection is read-only and returns the full item plus neighboring context.

Delete creates a preview that removes the item from the active source document.
Apply records the deleted content in the normal apply result audit trail.

Disable is non-destructive:

- For active items in editable project files, create a preview that removes the
  item from the active document and stores the full item in
  `.harnex/memory/disabled-items.json`.
- For already disabled items, return a no-op preview or validation error.
- For read-only/global/managed items, return a structured unsupported action
  unless the caller explicitly enables a future writable provider.

Enable creates a preview that restores a disabled item from
`.harnex/memory/disabled-items.json` back into the original document location or
a safe fallback section, then removes it from the disabled store on apply.

Shadowed items are not directly changed by "enable". The GUI should explain
which closer or override source is shadowing the item and offer actions on that
closer source instead.

## Effective resolver

Add a resolver that calculates GUI status without inventing Codex behavior:

- `AGENTS.override.md` shadows `AGENTS.md` at the same directory level.
- `AGENTS.md` files are ordered global first, then project root to current
  directory. Later/closer entries can be marked as higher precedence, but broad
  Markdown content is not automatically deleted.
- `.codex/config.toml` keys use closest-wins behavior for duplicate keys.
- Rules use most-restrictive-wins for matching command prefixes.
- Hooks are additive; matching hooks from multiple files all remain active.
- Duplicate skill names from multiple sources should be marked `conflict`
  unless Codex docs or local runtime inspection gives a clear precedence rule.

## Public API contract

Add API functions that GUI can call directly:

- `list_memory_items(project_root, cwd=None, include_readonly=False) -> list[MemoryItem]`
- `get_memory_item(project_root, item_id) -> MemoryItem`
- `preview_memory_item_action(project_root, item_id, action, expected_source_hash=None) -> Preview`
- `apply_preview(project_root, preview_path) -> Path` remains the only write path.

The preview JSON should include:

- `schema_version`
- `project_root`
- `preview_id`
- `source`
- `action`
- `items`
- `file_changes`
- `warnings`
- `blocked_reasons`

## CLI contract

Keep Typer handlers thin and mirror the API:

```text
harnex-memory items list --project-root <path> [--cwd <path>] [--include-readonly]
harnex-memory items show --project-root <path> --item-id <id>
harnex-memory items preview --project-root <path> --item-id <id> --action <delete|disable|enable>
```

The CLI should print JSON that the GUI can consume without post-processing.

## Implementation tasks

1. Add tests for item parsing from legacy `.harnex/memory/*.md`, `AGENTS.md`,
   and `.codex/skills/*/SKILL.md`.
2. Implement `MemoryItem`, `ItemStatus`, `ItemAction`, and serialization tests.
3. Add Markdown item parser support for headings, bullets, and managed blocks.
4. Add a disabled item store at `.harnex/memory/disabled-items.json`.
5. Implement delete/disable/enable preview builders with source hash checks.
6. Implement Codex effective resolver for AGENTS, config, rules, hooks, and
   duplicate skill conflict marking.
7. Add public API functions and JSON CLI commands.
8. Update README with GUI-facing examples and safety constraints.
9. Run full verification and tighten schemas based on test output.

## Acceptance tests

- `list_memory_items` returns items from legacy skill/rule/hook Markdown files.
- `list_memory_items` returns items from project `AGENTS.md`.
- `list_memory_items` returns skill items from `.codex/skills/foo/SKILL.md`.
- Each item includes `id`, `scope`, `path`, `document_kind`, `target_kind`,
  `status`, and `source_hash`.
- Delete preview removes only the selected item and does not modify files before
  apply.
- Disable preview removes the selected item from the active document and writes
  disabled state only through apply.
- Enable preview restores a disabled item and removes it from the disabled store
  only through apply.
- Stale `source_hash` blocks delete/disable/enable previews.
- `AGENTS.override.md` shadows same-directory `AGENTS.md` items.
- Nested/project config duplicate keys mark the closest key as active and the
  broader key as shadowed.
- Hook items from multiple layers remain active/additive.
- Duplicate skill names are marked `conflict` instead of silently shadowed.
- Read-only/global/managed items cannot be mutated by project-root apply.
- Paths outside project root are rejected.
- `python -m pytest` passes.
- `python -m ruff check .` passes.

## Suggested first implementation slice

Start with project-root-contained Markdown items only:

- legacy `.harnex/memory/{skills,rules,hooks}.md`
- project-root `AGENTS.md`
- project `.codex/skills/*/SKILL.md`
- project `.codex/skills/*.md`

This slice gives the GUI item list, selection, delete, disable, enable, preview,
and apply flow without needing writable global Codex providers.
