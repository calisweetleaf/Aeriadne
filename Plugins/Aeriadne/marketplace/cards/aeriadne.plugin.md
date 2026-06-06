# Aeriadne

Type: Plugin  
Status: Private v1 / staged  
Version: 1.0.0  
Clients: Codex, Claude Code, OpenCode, Grok Build  
Canonical path: `/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne`

## What it does

Aeriadne packages the Constitutional Prompt Framework as a skill-activated plugin and adds the private marketplace scaffold for plugin manifests, skills, agent prompts, adapters, registry records, marketplace cards, and MCP/server cards.

## Includes

- `constitutional-prompt-framework` skill
- `aeriadne-marketplace-operator` skill
- Aeriadne subagent prompt pack
- `sovereign-bb7` MCP/server reference card
- Registry and marketplace card skeleton
- Codex, Claude Code, OpenCode, and Grok Build adapter docs

## Expected Codex exposure after install

```text
aeriadne:constitutional-prompt-framework
aeriadne:aeriadne-marketplace-operator
```

## Supersedes

- Legacy `cpf-plugin-ariadne` / `CPF-Plugin-Ariadne`
- Legacy `legacy CPF plugin shell`

## Boundary

Not installed in this staging pass. BB7/SovereignMCP is referenced as canonical server plane, not vendored. Legacy plugin descriptors were deleted and must not be restored as active installables.
