# Tauri + Svelte GUI implementation plan

## Goal

Create a desktop GUI for `harnex-memory` using Tauri v2 and Svelte. The GUI
should let users choose a project root, inspect skill/rule/hook items, preview
delete/disable/enable actions, review diffs, and apply approved previews without
manually editing Markdown files.

This is a replacement GUI effort. Any existing non-Tauri GUI should be treated
as legacy and removed or retired once the Tauri/Svelte first slice reaches
feature parity for item listing, preview, and apply. Do not keep two active GUI
implementations unless the old GUI is needed temporarily as a reference during
the migration.

This plan only covers the GUI layer and the process bridge. The existing Python
core/API/CLI remains the source of truth for item parsing, preview generation,
path safety, and apply behavior.

## Official Reference Notes

- Tauri v2 officially supports creating a project with framework templates,
  including Svelte, through `create-tauri-app`.
- Vite supports a `svelte-ts` template, which matches this project better than a
  JavaScript-only frontend.
- Tauri sidecars and the `@tauri-apps/plugin-shell` command APIs require explicit
  capability configuration. Do not expose arbitrary shell execution to the UI.
- Shell commands can be executed as configured programs or sidecars; production
  packaging should move from a dev-only Python command to a bundled sidecar.

Sources:

- https://v2.tauri.app/start/create-project/
- https://vite.dev/guide/
- https://v2.tauri.app/develop/sidecar/
- https://v2.tauri.app/reference/javascript/shell/

## Recommended App Location

Create the GUI as a sibling app under the current repo:

```text
harnex-memory/
  gui/
    package.json
    vite.config.ts
    src/
      app.css
      main.ts
      App.svelte
      lib/
        api/
        components/
        stores/
        types/
    src-tauri/
      Cargo.toml
      tauri.conf.json
      capabilities/
      src/
        main.rs
        commands.rs
        harnex_memory.rs
```

Use `gui/` rather than putting Tauri files at the Python package root. This keeps
Python packaging, Rust/Tauri packaging, and frontend dependencies separated.

If an existing GUI directory already uses another stack, migrate it in place only
if that avoids path churn. Otherwise create the new `gui/` Tauri app, port the
useful UX ideas/data contracts, and remove the old GUI files after the new app
can run the first slice. Keep unrelated Python package files untouched.

## Legacy GUI Retirement

Before scaffolding, identify any existing GUI files or dependencies:

- frontend directories such as `gui/`, `app/`, `web/`, `frontend/`, or
  `src-ui/`
- package files such as `package.json`, `vite.config.*`, `svelte.config.*`, or
  old web build config
- Python/CLI glue that exists only for the old GUI

Retirement rules:

- Preserve backend APIs, tests, and CLI commands that the new Tauri GUI can
  reuse.
- Remove old GUI-only dependencies, build scripts, generated assets, and stale
  docs once the Tauri/Svelte first slice replaces them.
- Do not delete user data, memory documents, previews, disabled item state, or
  apply results.
- If the old GUI contains behavior not covered by this plan, list it as a
  migration gap before deletion.

## Scaffold Command

Preferred scaffold command:

```bash
pnpm create tauri-app gui --template svelte-ts
```

Acceptable alternatives if `pnpm` is not available:

```bash
npm create tauri-app@latest gui -- --template svelte-ts
bun create tauri-app gui --template svelte-ts
```

After scaffolding, adjust generated paths so frontend dev runs from `gui/` while
the Python package root remains `..`.

## Bridge Strategy

Phase 1 should use a Tauri Rust command layer that wraps a narrow
`harnex-memory` JSON command adapter.

Do not call arbitrary shell commands directly from Svelte components. The
frontend should call `invoke(...)` commands exposed by Rust, and Rust should
execute only known harnex-memory operations.

Development bridge:

- Run the Python CLI through the current repository source tree.
- Command shape: `python -m harnex_memory.cli ...`
- Set `PYTHONPATH=<repo>/src` from the Rust command adapter in dev mode.
- Parse stdout as JSON and surface stderr/exit codes as structured errors.

Production bridge:

- Package a `harnex-memory` sidecar executable.
- Configure it in `tauri.conf.json > bundle > externalBin`.
- Allow only the sidecar command in Tauri capabilities.
- Keep the JSON contract identical to the dev bridge.

Avoid embedding Python business logic in Rust during the first GUI slice. The
Python CLI/API already enforces path safety and preview-before-apply.

## Rust Command Contract

Add these Tauri commands:

- `select_project_root() -> ProjectRootSelection`
- `list_items(project_root: string, cwd?: string, include_readonly?: boolean) -> ItemsPayload`
- `show_item(project_root: string, item_id: string) -> ItemPayload`
- `preview_item_action(project_root: string, item_id: string, action: ItemAction, expected_source_hash?: string) -> PreviewPayload`
- `apply_preview(project_root: string, preview_path: string) -> ApplyPayload`

Each command should:

- Validate basic input shape before spawning the sidecar/dev command.
- Use fixed command names and fixed argument ordering.
- Reject missing project roots, missing item ids, and unknown actions before
  invoking Python.
- Return typed JSON errors with `kind`, `message`, and optional `stderr`.

## Frontend Data Types

Mirror the Python JSON fields in TypeScript:

- `MemoryItem`
- `TextSpan`
- `Preview`
- `FileChange`
- `ItemAction`
- `ItemStatus`
- `BlockedReason`
- `ApplyResult`

Keep these types in `gui/src/lib/types/harnex-memory.ts`. Avoid hand-parsing
Markdown in the frontend; the backend item model is authoritative.

## Main Screens

1. Project selector
   - Pick or type a project root.
   - Show the currently selected root.
   - Persist the last selected root in local app state.

2. Item browser
   - Table/list of items.
   - Columns: status, kind, scope, title, path, line span.
   - Filters: `skill`, `rule`, `hook`, `active`, `disabled`, `shadowed`,
     `conflict`.
   - Status affordances should be icon-first with labels available via tooltip.

3. Item detail
   - Show title, source path, status reason, source hash, and body preview.
   - Make read-only/shadowed/conflict states visually clear.
   - Do not allow destructive actions without preview.

4. Preview/diff panel
   - Show action, affected files, warnings, blocked reasons, and unified diff.
   - Disable Apply when `blocked_reasons` is non-empty.
   - Show before/after file paths and action metadata.

5. Apply result
   - Show written files and apply result path.
   - Refresh item list after apply.

## UI Design Direction

This is an operational desktop tool, not a marketing site.

- Use a dense but calm layout: sidebar filters, item list, detail/diff panel.
- Prefer compact controls and predictable keyboard/mouse behavior.
- Avoid decorative hero sections or card-heavy landing pages.
- Use icons for delete, disable, enable, refresh, open project, and apply.
- Keep cards only for repeated item rows or modal/dialog content.
- Ensure long file paths and item titles truncate cleanly and show full text on
  hover/focus.

## Safety Rules

- The GUI must never edit project files directly.
- All writes must go through `items preview` followed by `docs apply`.
- Always pass `expected_source_hash` when previewing an action from a listed item.
- Display `blocked_reasons` and prevent apply if any are present.
- Rust command layer must not expose arbitrary shell execution.
- Project root paths must be explicit user choices or previously stored choices.
- Sidecar command arguments should be fixed and validated, not freeform.

## Implementation Tasks

1. Scaffold `gui/` with Tauri v2 + Svelte + TypeScript.
2. Add frontend lint/test scripts and keep them isolated from Python package
   tooling.
3. Add Rust command adapter for dev-mode Python CLI execution.
4. Add TypeScript API client wrapping Tauri `invoke`.
5. Add TypeScript types matching `harnex-memory` JSON.
6. Build project selector and item list.
7. Build item detail and action buttons.
8. Build preview/diff panel and blocked-state handling.
9. Wire apply flow and refresh-after-apply behavior.
10. Add tests for command adapter argument construction and frontend state.
11. Add smoke/e2e flow for fixture project: list item, preview disable, block stale
    hash, apply valid preview.
12. Add production sidecar packaging plan once the dev GUI flow is stable.

## Suggested First Slice

Build the minimum useful GUI against the current CLI:

- Project root input.
- `items list` display.
- Item detail.
- `items preview --action delete|disable|enable`.
- Preview diff display.
- `docs apply` button.

Skip global read-only sources, advanced config visualization, and production
sidecar packaging until the first slice proves the JSON contract.

## Verification Checklist

- `harnex-memory items list --project-root <fixture>` returns item JSON.
- GUI loads that item JSON through the Tauri command adapter.
- Preview action returns a preview path and diff.
- Blocked previews are shown and cannot be applied.
- Valid previews can be applied through `docs apply`.
- Item list refreshes after apply.
- Frontend unit tests pass.
- Rust command adapter tests pass.
- `pnpm tauri dev` opens the desktop UI in development.
- No GUI action writes files without a preview/apply step.

## Open Decisions

- Package manager: prefer `pnpm`, but confirm whether this repo standardizes on
  `npm`, `pnpm`, or `bun`.
- Sidecar packaging: choose PyInstaller, `uv`-managed Python app packaging, or a
  small Rust native command wrapper after the dev bridge works.
- Diff renderer: start with plain unified diff text, then decide whether to add a
  richer diff component.
- Project selection: start with text input; add native folder picker once the
  Tauri dialog plugin is added.
