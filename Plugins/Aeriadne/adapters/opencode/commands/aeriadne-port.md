---
description: Port an existing agent constitution or system prompt to a target platform — Codex, Claude Code, OpenCode, Gemini-CLI, Cursor, or platform-agnostic.
agent: aeriadne-cpf
subtask: true
---

Run the Constitutional Prompt Framework in Mode E (Platform Portability Binding).

Input: $ARGUMENTS
Expected format: `<source-file-or-content> --target <platform>`
Platforms: codex | claude-code | opencode | gemini-cli | cursor | platform-agnostic

1. Identify source (file path or inline content) and target platform.
2. Load `references/10-platform-binding-matrix.md` for the target platform's
   capability model, unavailable features, and graceful degradation patterns.
3. Load `references/21-interoperability-notes.md` for portability rules.
4. Produce a platform-bound version of the constitution:
   - Replace unavailable features with conditional protocols.
   - Keep platform-agnostic sections intact.
   - Add a platform binding note to the Living Status footer.

Return the full ported constitution and a diff summary of what changed.
