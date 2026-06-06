# Operator Control Plane

Use this when Daeron frames Codex as an autonomous operator rather than a temporary agent, or when comparing Codex to Hermes-style `AGENTS.md` / `MEMORY.md` / `CONTEXT.md` / `USER.md` / `SOUL.md` behavior.

## Semantics

Preferred framing for this workspace:

- Codex is the active operator state machine.
- BB7/Sovereign, Mentat, CodeGraph, hooks, skills, and plugins are support surfaces.
- Daeron is the human operator; Codex is not a generic real-estate-style "agent" persona.
- Preserve "operator" language in local docs when editing doctrine.

## What Codex can do today

Codex can be configured into a strong operator-control plane through:

1. `config.toml` for model, approval, sandbox/permissions, features, MCP, plugins, and hooks state.
2. `model_instructions_file` and AGENTS discovery for persistent instruction context.
3. Project docs (`AGENTS.override.md`, `AGENTS.md`, fallback filenames) for repository/task-specific rules.
4. Hooks for lifecycle side effects and concise `additionalContext` injection.
5. MCP for external tools/context such as BB7, CodeGraph, and Mentat.
6. Skills for reusable workflows and progressive disclosure.
7. Plugins for bundles of skills, hooks, apps, MCP, and assets.
8. Codex Memories and BB7 memory for continuity, with docs still owning binding rules.

## What Codex cannot do by config alone

- Remove or replace higher-priority upstream system/developer instructions.
- Treat every linked Markdown file as automatically loaded context.
- Load multiple instruction files from the same directory in project scope when `AGENTS.override.md` already wins.
- Make BB7 tools native OpenAI built-ins without MCP/source/runtime support.
- Guarantee every hook injects model-visible context unless the hook event schema supports it and the JSON is valid.
- Cross OAuth/provider/runtime boundaries safely without explicit operator authorization.

## Hermes-like doc stack mapping

| Desired symbolic layer | Codex-local equivalent | Caveat |
|---|---|---|
| `SOUL.md` | compact persona/symbolic doctrine | not auto-loaded unless configured/injected |
| `AGENTS.md` | large constitution / identity / working agreements | shadowed by global `AGENTS.override.md` at global scope |
| `AGENTS.override.md` | highest-priority local runtime override | good for compact law, not huge lore |
| `USER.md` | Daeron/operator facts | not official special file |
| `MEMORY.md` | durable decisions/gotchas | not official Codex Memories by itself |
| `CONTEXT.md` | current handoff/state | not auto-loaded unless discovered/read |
| `MCP_SPEC.md` | topology/reference | load only task-relevant sections |
| `workflows.md` | golden paths | use smallest useful subset |

## Practical startup strategies

### Strategy A — compact override plus explicit reads

Keep `AGENTS.override.md` compact and strict. It tells Codex to read `AGENTS.md`, `USER.md`, `MEMORY.md`, and `CONTEXT.md` before substantial work. This keeps startup prompt small but depends on the operator loop actually doing the reads.

### Strategy B — aggregator model instructions

Create a single aggregator file such as `OPERATOR_BOOT.md` and point `model_instructions_file` at it. The aggregator contains the minimal always-on essentials and explicitly names deeper docs. This is closest to a Hermes-like single boot constitution without relying on same-directory fallback behavior.

### Strategy C — hook-injected briefing

Use `SessionStart` / `UserPromptSubmit` hooks to inject a concise state summary from `CONTEXT.md`, `MEMORY.md`, BB7 recall, or generated summaries. Keep it small and schema-valid. Do not inject full giant docs every turn.

### Strategy D — nested scope docs

Use nested project directories with their own `AGENTS.md`/`AGENTS.override.md` when a repo or subproject needs specific rules. This uses Codex's root-to-current merge order instead of fighting same-directory one-file limits.

### Strategy E — skill/plugin packaging

Put repeatable workflows in skills and bundle larger systems as plugins. Skills are better than startup docs for detailed procedures because Codex loads them only when relevant.

## Observed local prompt-loading warning

A structural `codex debug prompt-input` audit on 2026-06-04 from `/home/daeron/.codex` found a project instruction segment titled `AGENTS.md instructions for /home/daeron/.codex`, but the segment content matched the compact runtime override rather than the full `CODEX CONSTITUTION` from `AGENTS.md`. Literal `USER.md` and `SOUL.md` content did not appear in that prompt-input audit.

Treat this as a verification target, not a failure panic: the current runtime still has instructions to read `CONTEXT.md`/`MEMORY.md` before substantial work, and BB7/skill/memory context surfaces are active. But do not claim the full Hermes-like doc stack autoloads at session start until `codex debug prompt-input` proves it.

## Candidate future patch, not automatic

If Daeron explicitly asks to make the Hermes-like stack more automatic, propose a reversible patch:

1. Create `OPERATOR_BOOT.md` or `SOUL.md` with compact essentials only.
2. Set `model_instructions_file = "OPERATOR_BOOT.md"` or keep current override and have it summarize the essentials.
3. Keep `AGENTS.md` as deeper constitution, but do not assume it is startup-loaded.
4. Add `USER.md` and optional `SOUL.md` to `project_doc_fallback_filenames` only if the same-directory selection behavior is understood; fallback is not a multi-file include list.
5. Add or adjust hook summaries only after schema smoke tests.
6. Verify with `codex debug prompt-input` and a JSON/Markdown audit manifest.
