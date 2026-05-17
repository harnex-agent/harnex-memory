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
