# Aeriadne Marketplace Schema Notes

## Artifact types

- `plugin`: installable package shell.
- `skill`: cognitive workflow payload with `SKILL.md`.
- `agent-pack`: role/subagent prompt set.
- `mcp-card`: canonical server/tool-plane reference card.
- `mixed-bundle`: package containing more than one artifact class.

## Required fields

Every registry entry should include:

- `id`
- `name`
- `type`
- `status`
- `version`
- `canonical_path`
- `owner`
- `clients`
- `includes`
- `validation`
- `notes`

## Status values

- `private-draft`
- `private-v1`
- `staged`
- `validated-local`
- `installed-local`
- `adapter-ready`
- `public-candidate`
- `deprecated`

## Dependency modes

- `vendored`
- `canonical-reference`
- `optional`
- `required`
- `schema-probe-needed`

BB7/SovereignMCP should be represented as `canonical-reference`, not `vendored`.
