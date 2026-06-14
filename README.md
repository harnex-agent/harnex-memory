# harnex-memory

`harnex-memory` is the lowest-level memory module for harnex. It manages project
skill/rule/hook documents and stores prompt memory events that can later be used
to suggest document updates.

## Commands

```text
harnex-memory docs list --project-root <path>
harnex-memory docs preview --project-root <path> --target <skill|rule|hook> --content <path>
harnex-memory docs apply --project-root <path> --preview <path>
harnex-memory constraint preview --project-root <path> --constraint <text> [--agent <codex|claude>]
harnex-memory items list --project-root <path>
harnex-memory items show --project-root <path> --item-id <id>
harnex-memory items preview --project-root <path> --item-id <id> --action <delete|disable|enable>
harnex-memory prompt record --project-root <path> --source <source> --prompt <text>
harnex-memory prompt ingest --project-root <path> --source <source> --prompt <text> [--agent <codex|claude>]
harnex-memory prompt suggest --project-root <path>
harnex-memory recommendations list --project-root <path>
harnex-memory recommendations show --project-root <path> --recommendation-id <id>
harnex-memory recommendations apply --project-root <path> --recommendation-id <id>
harnex-memory recommendations dismiss --project-root <path> --recommendation-id <id>
```

All writes are constrained to the provided project root. Document changes are
created as preview JSON first and applied only through the apply command.

`docs list` includes the legacy `.harnex/memory/{skills,rules,hooks}.md`
documents plus per-agent documents: Codex `AGENTS.md` and `.codex/skills/*/SKILL.md`
(or `.codex/skills/*.md`), and Claude `CLAUDE.md` and `.claude/skills/*/SKILL.md`
(or `.claude/skills/*.md`). Each agent-facing document is tagged with its `agent`
(`codex` or `claude`); legacy documents carry no agent tag.

`constraint preview` classifies a direct user constraint without external LLM
calls. General project rules preview into the agent's instructions file
(`AGENTS.md` for Codex, `CLAUDE.md` for Claude), skill-related constraints preview
into that agent's skill document, and hook-related constraints keep using the
hook-compatible memory document. The target agent is detected on every call (see
[Agent routing](#agent-routing)); pass `--agent codex|claude` to force it.

`items list` exposes GUI-friendly structured items from skill/rule/hook documents.
The supported editable sources are legacy `.harnex/memory/*.md`, Codex `AGENTS.md`
and `.codex/skills` Markdown files, and Claude `CLAUDE.md` and `.claude/skills`
Markdown files. Each item includes a stable `id`, `status`, `scope`, `agent`,
source `path`, line span, and `source_hash`.

`items preview` creates a preview for item-level actions. `delete` removes the
selected item from its source document. `disable` removes it from the active
document and stores the full item in `.harnex/memory/disabled-items.json`.
`enable` restores a disabled item and removes it from the disabled store. These
commands still do not write target documents directly; use `docs apply` with the
returned preview path to apply approved changes.

`prompt ingest` is the adapter-facing entrypoint for automatic prompt capture. A
host integration should call it from the user-input path without requiring users
to mention harnex-memory in their prompt. It records the prompt, detects direct
constraints, runs repeated-prompt suggestions, writes preview JSON for new
recommendations, and indexes them in `.harnex/memory/recommendations.jsonl`.
Recommendations are append-only status records with `pending`, `applied`,
`dismissed`, or `stale` states. Applying a recommendation applies its preview and
marks the recommendation as applied; dismissing it prevents the same suggestion
from being recreated.

Each recommendation carries an `origin` (`heuristic` by default) and is
priority-ranked when listed (explicit user constraints first, then reviewer
suggestions, then repeated-prompt inferences). Suggestions whose substance
already lives in the target document — or that read as transient/negative noise
("X doesn't work", "에러 났어") — are skipped. Applying re-validates the stored
preview against the current document and marks the recommendation `stale` if the
document drifted since it was generated. An optional, dependency-free review pass
can propose extra candidates: point `HARNEX_MEMORY_REVIEWER` at a `module:factory`
callable returning a reviewer; its candidates are staged with origin `llm_review`
and, like every recommendation, are never auto-applied.

Repeated-prompt detection groups prompts by similarity. The default groups
prompts that are identical after normalization (zero dependencies). For semantic
grouping that catches paraphrases across wording and language ("테스트 실행해줘"
≈ "test 돌려줘"), install the optional `embeddings` extra and set
`HARNEX_MEMORY_SIMILARITY=embedding`: it clusters prompts with a **local**
sentence-embedding model (one-time model download, then offline — no external API
call). Tune with `HARNEX_MEMORY_EMBED_MODEL` and `HARNEX_MEMORY_EMBED_THRESHOLD`.

For Codex app usage, wire `scripts/codex_user_prompt_submit.py` to Codex's
`UserPromptSubmit` hook. The hook records prompts automatically at submit time,
so users can keep working in the Codex app without typing an explicit
`harnex-memory` request.

For Claude Code usage, wire `scripts/claude_user_prompt_submit.py` to Claude's
`UserPromptSubmit` hook the same way. It records prompts with source
`claude-user-prompt-submit` and routes captured constraints to Claude documents.
Both hooks can be wired at once; each prompt is routed to the agent that produced
it.

### Agent routing

harnex-memory treats both Codex and Claude as first-class agents and resolves a
target agent on every call, so users who mix both keep their memories in the right
documents. Resolution order:

1. an explicit `--agent` (or the adapter-provided agent);
2. prompt-text markers (`CLAUDE.md` / `.claude/skills` / "claude" vs. `AGENTS.md`
   / `.codex/skills` / "codex");
3. the prompt `source` (`claude-user-prompt-submit` vs.
   `codex-user-prompt-submit`);
4. the only agent with on-disk artifacts, when exactly one is present;
5. Codex as the default when no signal is available.

A prompt repeated under both agents produces a recommendation for each agent's
document.

Codex scope handling follows Codex's own layering rules where they are explicit:
global user guidance lives under `CODEX_HOME`/`~/.codex`, project guidance comes
from `AGENTS.md` files from the project root down to the current working
directory, and trusted project `.codex/` directories are project/team config
layers. `AGENTS.override.md` shadows `AGENTS.md` in the same directory; Claude's
`CLAUDE.md` has no override-file concept. Duplicate skill names are surfaced as
conflicts per agent, so a Codex skill and a Claude skill that share a name do not
conflict with each other.

## Desktop GUI

The `gui/` directory contains a Tauri v2 + Svelte desktop first slice for item
management. It lists memory items with per-agent labels and an agent filter, shows
item detail, previews `delete`/`disable`/`enable` actions with
`expected_source_hash`, displays blocked previews, and applies approved preview
files through `docs apply`. The
Recommendations tab lists generated prompt-ingest recommendations, shows their
diff previews, and lets the user apply or dismiss them. The tab carries a
pending-count badge and can apply or dismiss all pending recommendations at once,
reporting any per-item failures.

```text
cd gui
npm install
npm run tauri dev
```

The development bridge runs `python3 -m harnex_memory.cli` with
`PYTHONPATH=<repo>/src`. Set `HARNEX_MEMORY_PYTHON` if a different Python
executable should be used.
