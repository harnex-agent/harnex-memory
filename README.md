# harnex-memory

`harnex-memory` is the lowest-level memory module for harnex. It manages project
skill/rule/hook documents and stores prompt memory events that can later be used
to suggest document updates.

## Commands

```text
harnex-memory docs list --project-root <path>
harnex-memory docs preview --project-root <path> --target <skill|rule|hook> --content <path>
harnex-memory docs apply --project-root <path> --preview <path>
harnex-memory prompt record --project-root <path> --source <source> --prompt <text>
harnex-memory prompt suggest --project-root <path>
```

All writes are constrained to the provided project root. Document changes are
created as preview JSON first and applied only through the apply command.

