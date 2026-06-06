# PROVENANCE

## Snapshot lineage

This update is grounded in an uploaded doctrine bundle rather than a generic scaffold alone. It incorporates:

- `AGENTS.md`
- `AGENTS.override.md`
- `OPSEC.md`
- `STYLE.md`
- `MCP_SPEC.md`
- `default.rules`
- `tool_manifest.json`

## Rejected alternatives

### Rejected: keep the skill as a generic `.codex` mapper
Reason: the runtime doctrine is now explicit, and generic config reasoning would miss the real entry law.

### Rejected: treat `AGENTS.override.md` as the only authoritative file
Reason: the operator clarified that `AGENTS.md` remains the main identity and baseline posture.

### Rejected: phrase terminal posture as unrestricted by definition
Reason: the operator wants broad terminal authority, but the truthful model still depends on host and rule surfaces.

## Open questions

- the current real `.codex` tree and launch wrappers are still not bundled in this package
- `workflows.md` was referenced by the operator but is not in the uploaded bundle
- the exact injection mechanism for these doctrine files inside the live Codex install is still inferred rather than directly inspected

## Decision log

- added first-mission doctrine loading as a hard rule
- added exo-first sequencing as explicit runtime law
- added permission-surface reasoning through `default.rules` and `tool_manifest.json`
- widened host reasoning beyond Windows-only language because the uploaded doctrine bundle includes multi-host context
