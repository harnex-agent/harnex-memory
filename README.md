# harnex-memory

`harnex-memory` is the lowest-level memory module for harnex. It manages project
skill/rule/hook documents and stores prompt memory events that can later be used
to suggest document updates.

## Commands

```text
harnex-memory docs list --project-root <path>
harnex-memory docs preview --project-root <path> --target <skill|rule|hook> --content <path>
harnex-memory docs apply --project-root <path> --preview <path>
harnex-memory constraint preview --project-root <path> --constraint <text>
harnex-memory items list --project-root <path>
harnex-memory items show --project-root <path> --item-id <id>
harnex-memory items preview --project-root <path> --item-id <id> --action <delete|disable|enable>
harnex-memory prompt record --project-root <path> --source <source> --prompt <text>
harnex-memory prompt suggest --project-root <path>
```

All writes are constrained to the provided project root. Document changes are
created as preview JSON first and applied only through the apply command.

`docs list` includes the legacy `.harnex/memory/{skills,rules,hooks}.md`
documents plus Codex-facing documents such as project-root `AGENTS.md` and
`.codex/skills/*/SKILL.md` or `.codex/skills/*.md`.

`constraint preview` classifies a direct user constraint without external LLM
calls. General project rules preview into `AGENTS.md`, skill-related constraints
preview into a Codex skill document, and hook-related constraints keep using the
hook-compatible memory document.

`items list` exposes GUI-friendly structured items from skill/rule/hook documents.
The first supported editable sources are legacy `.harnex/memory/*.md`,
project-root `AGENTS.md`, and project `.codex/skills` Markdown files. Each item
includes a stable `id`, `status`, `scope`, source `path`, line span, and
`source_hash`.

`items preview` creates a preview for item-level actions. `delete` removes the
selected item from its source document. `disable` removes it from the active
document and stores the full item in `.harnex/memory/disabled-items.json`.
`enable` restores a disabled item and removes it from the disabled store. These
commands still do not write target documents directly; use `docs apply` with the
returned preview path to apply approved changes.

Codex scope handling follows Codex's own layering rules where they are explicit:
global user guidance lives under `CODEX_HOME`/`~/.codex`, project guidance comes
from `AGENTS.md` files from the project root down to the current working
directory, and trusted project `.codex/` directories are project/team config
layers. `AGENTS.override.md` shadows `AGENTS.md` in the same directory. Duplicate
Codex skill names are surfaced as conflicts instead of being silently resolved.

## Desktop GUI

The `gui/` directory contains a Tauri v2 + Svelte desktop first slice for item
management. It lists memory items, shows item detail, previews
`delete`/`disable`/`enable` actions with `expected_source_hash`, displays blocked
previews, and applies approved preview files through `docs apply`.

```text
cd gui
npm install
npm run tauri dev
```

The development bridge runs `python3 -m harnex_memory.cli` with
`PYTHONPATH=<repo>/src`. Set `HARNEX_MEMORY_PYTHON` if a different Python
executable should be used.
