# Aeriadne Marketplace Surface

This folder is the human-facing rendered side of the private/local marketplace scaffold.

Registry files under `../registry/` are the machine-readable source. Marketplace cards here are readable summaries generated or maintained from registry facts.

## Contents

- `cards/aeriadne.plugin.md`
- `cards/constitutional-prompt-framework.skill.md`
- `cards/aeriadne-marketplace-operator.skill.md`
- `cards/sovereign-bb7.mcp.md`
- `indexes/plugin-index.yaml`
- `indexes/skill-index.yaml`
- `indexes/agent-index.yaml`
- `indexes/mcp-index.yaml`

## Rule

Cards must not claim installed status without install evidence. Use `private-v1`, `staged`, `validated-local`, or `installed-local` precisely.
