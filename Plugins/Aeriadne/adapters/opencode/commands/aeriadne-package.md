---
description: Package an Aeriadne artifact (skill, agent prompt pack, MCP card) — run the marketplace operator to create or update manifests, registry rows, marketplace cards, and adapter docs.
agent: aeriadne-mop
subtask: true
---

Run the Aeriadne Marketplace Operator.

Input: $ARGUMENTS
Expected format: `<artifact-path> --mode <A|B|C|D|E>`
Modes: A=package-creation | B=registry | C=adapter | D=mcp-catalog | E=release-sentinel

If no mode is given, classify the task from context and proceed with the appropriate mode.

1. Read the artifact at the given path.
2. Determine the artifact type (plugin / skill / agent-pack / mcp-card / mixed-bundle).
3. Run the corresponding mode workflow.
4. For Mode A or E: run `python3 scripts/validate_package.py .` at the end.

Return the evidence contract: files changed, package state, registry effect,
client effect, validation evidence, next gate.
