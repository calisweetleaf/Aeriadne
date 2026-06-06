# Manifest — Aeriadne

Package: `aeriadne`  
Version: `1.0.0`  
Date: `2026-06-05`  
Status: `private-v1` / staged, not installed  
Purpose: Skill-activated plugin wrapper for CPF plus local/private marketplace scaffold.

## Canonical path

```text
/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne
```

## Root contents

- `plugin.json` — root plugin metadata.
- `.codex-plugin/plugin.json` — Codex plugin metadata mirror.
- `.claude-plugin/plugin.json` — Claude/local plugin metadata mirror.
- `plugin.toml` — canonical local/private marketplace manifest.
- `README.md` — package ontology, provenance, validation, install/exposure notes.
- `MANIFEST.md` — this file.
- `MARKETPLACE_ROADMAP.md` — staged Codex/Claude Code/OpenCode/Grok Build/private marketplace plan.
- `CHANGELOG.md` — package change log.
- `LICENSE.md` — private/internal notice.
- `registry/` — machine-readable marketplace inventory.
- `marketplace/` — human-facing cards and indexes.
- `adapters/` — Codex, Claude Code, OpenCode, and Grok Build projection docs.
- `agents/` — subagent prompt pack and client projection placeholders.
- `mcp/` — MCP/server catalog corner.
- `scripts/validate_package.py` — stdlib package validator.
- `tests/` — package smoke/compatibility cases.
- `skills/` — bundled cognitive payloads.

## Bundled skills

### `constitutional-prompt-framework`

Copied from `/home/daeron/.codex/skills/custom/constitutional-prompt-framework`.

Contains:

- `SKILL.md`
- `README.md`
- `MANIFEST.md`
- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `package-manifest.json`
- `agents/openai.yaml`
- `assets/`
- `examples/`
- `references/`
- `schemas/`
- `scripts/`
- `tests/`

### `aeriadne-marketplace-operator`

New plugin-local skill for registry, packaging, adapters, marketplace cards, agent prompt packs, MCP/server cards, and release validation.

Contains:

- `SKILL.md`
- `references/marketplace-schema.md`
- `templates/plugin-card.md`
- `templates/registry-entry.yaml`
- `tests/smoke_cases.yaml`

## Agent prompt pack

- `agents/subagents/prompt-architect.md`
- `agents/subagents/package-cartographer.md`
- `agents/subagents/compatibility-auditor.md`
- `agents/subagents/registry-scribe.md`
- `agents/subagents/release-sentinel.md`

These are parallel workstream prompts, not rank hierarchy.

## MCP/server card

- `mcp/servers/sovereign-bb7.md`

BB7/SovereignMCP is represented as `canonical-reference`, not vendored code.

## Expected Codex exposure after install

```text
aeriadne:constitutional-prompt-framework
aeriadne:aeriadne-marketplace-operator
```

## Provenance

CPF copied from `/home/daeron/.codex/skills/custom/constitutional-prompt-framework` into `/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne/skills/constitutional-prompt-framework` on `2026-06-05`.

The source path remains intact for direct authoring. The plugin path is the distribution and marketplace staging surface.

Legacy CPF plugin package content was deleted from the staging tree. Aeriadne keeps only alias/conflict metadata for the old names; do not restore legacy descriptors as active installables.

## Boundary

Aeriadne does not replace:

- `Codex-Config-Topology` for Codex control-plane/config/plugin/hook topology.
- `Cognitive-Topology-Map` / CTMv3 for workspace activation.
- `Mentat` for live runtime state-machine instrumentation.
- `Somnus-MCP` / BB7 for the canonical MCP/tool/server plane.

## Validation status

Validation commands are listed in `README.md`. Installation has not been performed.
