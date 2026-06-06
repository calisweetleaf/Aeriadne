# PLAN — Modern-ML

## Current objective

The workspace has been consolidated into a clean **3-plugin core**:

| Plugin | Purpose | Status |
|--------|---------|--------|
| `Plugins/Aeriadne/` | CPF + marketplace operator (skill-activated) | Staged, not installed |
| `Plugins/Cognitive-Topology-Map/` | CTMv3 workspace activation / topology | Active |
| `Plugins/Mentat/` | Live session/runtime substrate | Active |

Archived to `Plugins/old/`: `Codex-Config-Topology`, `Parallax-Narthex`, `CPF-Plugin-Ariadne`.

## Completed

- [x] Copied `constitutional-prompt-framework` into `Plugins/Aeriadne/skills/constitutional-prompt-framework/`
- [x] Added `aeriadne-marketplace-operator` as the second Aeriadne skill
- [x] Added plugin manifests, registry, marketplace cards, adapters, subagent prompts, MCP/server card, tests, and validator
- [x] Validated package shape, JSON/TOML manifests, CPF package, linter, score, static evals, and render fixture
- [x] Updated `README.md`, `AGENTS.md`, `CONTEXT.md`, `MEMORY.md`, `ARCHITECTURE_MAP.md`, and `PLAN.md` to reflect the clean 3-plugin triad
- [x] Archived `Codex-Config-Topology` to `Plugins/old/`

## Next gates

- [ ] Decide whether to install `aeriadne@local` (use local marketplace/cache pattern from `codex-config-topology@local`)
- [ ] Create root-level `Registry/`, `Marketplace/`, `Adapters/`, `MCP/` surfaces for the broader private-marketplace expansion
- [ ] Add `Servers/Somnus-MCP` pointer to `/home/daeron/Somnus-MCP` for cold-entry agents
- [ ] Refresh inventory/filetree after broader restructure
- [ ] Do not install legacy `cpf-plugin-ariadne@local` alongside `aeriadne@local` unless duplicate CPF exposure is intentional
