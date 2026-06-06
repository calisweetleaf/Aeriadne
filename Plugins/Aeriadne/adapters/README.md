# Aeriadne Client Adapters

Adapters document how the canonical Aeriadne package projects into specific agent clients.

Canonical source remains `Plugins/Aeriadne/`. Client adapter outputs, generated files, or install notes are projections only.

## Clients

- `codex/` — Codex local plugin exposure and prompt-input verification.
- `claude-code/` — Claude Code plugin/skill/subagent packaging notes.
- `opencode/` — OpenCode skill/prompt projection notes.

## Rule

Do not mix client-specific assumptions into the canonical CPF skill or the root package manifest unless the field is explicitly cross-client.
