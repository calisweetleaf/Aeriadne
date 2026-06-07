---
name: aeriadne-marketplace-operator
description: "Package skills, agent prompts, plugin wrappers, MCP/server reference cards, and local registry metadata into a private multi-client marketplace for Codex, Claude Code, and OpenCode. Use when building or auditing plugin manifests, marketplace cards, registry indexes, client adapters, package boundaries, install docs, dry-run install plans, or promotion gates for local/private agent artifacts."
---

# Aeriadne Marketplace Operator

## Prime directive

Turn local agent intelligence artifacts into marketplace-ready private packages without flattening their ontology. A plugin is not a skill, a skill is not an agent prompt, an MCP/server card is not vendored server code, and a client adapter is not the canonical source.

Use this skill when Aeriadne needs to package, inventory, validate, adapt, or release artifacts across Codex, Claude Code, OpenCode, local skills, agent/subagent prompts, and MCP/server catalogs.

## Trigger conditions

Use this skill for:

- Creating or updating plugin manifests (`plugin.json`, `plugin.toml`, client-specific mirrors).
- Building `registry/*.yaml` and marketplace cards.
- Mapping a canonical package into Codex, Claude Code, or OpenCode adapters.
- Adding agent/subagent prompt packs.
- Adding MCP/server catalog references without copying canonical server code.
- Auditing package completeness, portability, installability, and promotion readiness.
- Designing local/private marketplace layout before broader repo restructuring.

Do not use this skill for ordinary prompt constitution derivation. Use `constitutional-prompt-framework` for constitution design, prompt audits, prompt hardening, prompt-to-skill conversion, or platform-bound prompt rewriting.

## Load-bearing distinctions

### Plugin

Installable package shell. It may contain skills, commands, hooks, adapter docs, registry entries, and marketplace cards. It is a distribution/runtime surface, not necessarily the cognitive payload itself.

### Skill

The cognitive workflow payload. It contains `SKILL.md` and optional references/templates/scripts/tests. Skills should remain usable outside a plugin when practical.

### Agent prompt

A role/posture/subagent instruction artifact. It should define work scope, permitted write set, expected evidence, and final report shape. Agent prompts are parallel workstream enablers, not rank hierarchy.

### MCP/server card

A catalog entry that documents a canonical server/tool plane, capability classes, connection assumptions, data roots, and safety boundaries. Do not vendor BB7/SovereignMCP into Aeriadne.

### Adapter

A client-specific projection route. Codex, Claude Code, and OpenCode do not consume packages identically; adapters translate canonical package metadata into local install docs or generated files. Adapters are never the source of truth.

## Canonical package contract

Every Aeriadne package should be discoverable by:

- package id
- artifact type (`plugin`, `skill`, `agent-pack`, `mcp-card`, `mixed-bundle`)
- canonical source path
- owner/status/version
- client compatibility matrix
- included skills/agents/MCP references
- install mode (`local`, `dry-run`, `symlink`, `copy`, `manual`)
- validation commands
- known aliases/conflicts
- no-secret/no-cache packaging note

## Mode selection

Classify the task before writing.

### Mode A: Package creation

Create or update plugin metadata, manifest, README, changelog, registry entries, marketplace card, adapter docs, and validation gates.

### Mode B: Registry maintenance

Update machine-readable package indexes. Preserve local vs symlink vs external canonical roots. Do not invent installed status; mark `staged`, `validated`, or `installed` only with evidence.

### Mode C: Adapter mapping

Describe how one canonical package projects into a client. Keep Codex, Claude Code, and OpenCode assumptions separated. Mark unknown client mechanics as `schema-probe-needed` instead of guessing.

### Mode D: MCP cataloging

Document server/tool-plane reality as a reference card. Use capability categories and canonical paths. Do not copy server code, runtime databases, auth files, or secrets into plugin packages.

### Mode E: Release sentinel

Run or specify validation gates: JSON/TOML/YAML parse, path existence, skill frontmatter, no-secret scan, adapter drift, install exposure, package archive exclusion rules, and docs/current-state consistency.

## Packaging rules

1. Keep the canonical source clear: `Plugins/Aeriadne/` is the package source for Aeriadne; copied skills retain provenance to their authoring source.
2. Keep client projections subordinate: generated or adapter-specific outputs must not become canonical.
3. Keep BB7/SovereignMCP external: catalog it as `canonical-reference`, never as vendored plugin code.
4. Preserve direct authoring skills unless Daeron explicitly approves removal.
5. Do not claim install status without running install verification.
6. Prefer local/private marketplace first; public marketplace readiness is a separate promotion gate.
7. No secrets, auth files, runtime databases, caches, session logs, or high-churn state in packages.

## Output contract

When producing package work, return:

1. **Files changed** — exact paths.
2. **Package state** — staged, validated, installed, or blocked.
3. **Registry effect** — what package/skill/agent/MCP entries changed.
4. **Client effect** — Codex/Claude/OpenCode exposure or docs added.
5. **Validation evidence** — commands run and pass/fail.
6. **Next gate** — the smallest safe next move.

## Quality gates

A package is not v1-ready until:

- root manifest parses
- client mirror manifests parse when present
- all manifest paths exist
- skill frontmatter is present and trigger-specific
- registry rows match real files
- marketplace cards exist for plugin, primary skills, and MCP/server references
- adapter docs state canonical source vs generated/client-specific projection
- no secrets or runtime state are included
- install status is accurately labeled

## Final discipline

Aeriadne is a marketplace operator, not a junk drawer. Every package should make the surrounding agent ecosystem easier to enter, validate, install, audit, and evolve.
