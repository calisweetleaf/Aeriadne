# Aeriadne — CPF + Private Marketplace Plugin

`Aeriadne` is a **skill-activated plugin** for Daeron's local/private agent marketplace stack.

It packages the existing `constitutional-prompt-framework` skill, adds a second `aeriadne-marketplace-operator` skill, and provides the first concrete scaffold for a private marketplace spanning Codex, Claude Code, OpenCode, Grok Build, plugin packages, skills, agent/subagent prompts, and MCP/server-plane reference cards.

## Current status

- Status: `private-v1` / staged, not installed
- Date staged: `2026-06-05`
- Source CPF skill copied from: `/home/daeron/.codex/skills/custom/constitutional-prompt-framework`
- Canonical package path: `/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne`
- Primary plugin id: `aeriadne`
- Display name: `Aeriadne`
- Legacy/search aliases: `Ariadne`, `cpf-plugin-ariadne`, `CPF-Plugin-Ariadne`
- Deprecated CPF plugin package: deleted from staging tree
- Legacy runtime marker descriptors: deleted from staging tree
- Install action: not performed in this pass
- Git action: none; do not push during the Somnus-Intellligence-Stack restructure pass

## What it contains

Aeriadne v1 contains **two first-class skills**:

1. `constitutional-prompt-framework`
   - copied from the direct Codex custom skill source
   - derives, hardens, audits, ports, scores, and packages constitutions/prompts/skill instructions
2. `aeriadne-marketplace-operator`
   - new plugin-local skill
   - packages plugins, skills, agent prompts, MCP/server cards, registries, adapters, marketplace cards, and release gates

Aeriadne also includes:

- plugin manifests (`plugin.json`, `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`)
- canonical local/private manifest (`plugin.toml`)
- registry files (`registry/*.yaml`, `registry/aeriadne.plugin.json`)
- marketplace cards and indexes (`marketplace/`)
- Codex, Claude Code, OpenCode, and Grok Build adapter docs (`adapters/`)
- subagent prompt pack (`agents/subagents/`)
- MCP/server catalog corner (`mcp/`), with BB7/SovereignMCP as canonical reference
- validation script and smoke case docs (`scripts/`, `tests/`)

## Layer classification

Aeriadne does **not** replace BB7, Mentat, Codex Config Topology, or CTMv3.

```text
Codex Config Topology     # Codex control-plane topology and plugin/config/hook doctrine; archived as plugin, useful as skill
Aeriadne / CPF            # constitution, prompt, plugin-packaging, registry, marketplace compiler
CTMv3 / Cognitive Map     # workspace activation and codebase topology
Mentat                    # live session/runtime substrate
Somnus-MCP / BB7          # canonical MCP/tool/server plane and data root
```

Codex remains the active state machine. Plugins are support surfaces that improve state transitions, packaging, context routing, and operator ergonomics.

## Directory shape

```text
Aeriadne/
├── plugin.json
├── plugin.toml
├── .codex-plugin/plugin.json
├── .claude-plugin/plugin.json
├── README.md
├── MANIFEST.md
├── MARKETPLACE_ROADMAP.md
├── CHANGELOG.md
├── LICENSE.md
├── registry/
├── marketplace/
├── adapters/
├── agents/
├── mcp/
├── scripts/
├── tests/
└── skills/
    ├── constitutional-prompt-framework/
    └── aeriadne-marketplace-operator/
```

## Expected Codex exposure after install

If installed as `aeriadne@local`, the expected plugin skill entries are:

```text
aeriadne:constitutional-prompt-framework
aeriadne:aeriadne-marketplace-operator
```

Do not install both `aeriadne@local` and the legacy `cpf-plugin-ariadne@local` unless duplicate CPF exposure is intentional.

Do not delete `/home/daeron/.codex/skills/custom/constitutional-prompt-framework` just because this package exists. Direct authoring and plugin distribution can coexist.

## Legacy package boundary

The legacy plugin archive was removed from the staging tree. The active CPF/private-marketplace package is `plugins/Aeriadne/`; do not restore legacy CPF plugin descriptors unless intentionally rebuilding a separate package.

## Validation

From this plugin root:

```bash
python3 scripts/validate_package.py .
python3 -m json.tool plugin.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool registry/aeriadne.plugin.json >/dev/null
python3 -c "import pathlib,tomllib; tomllib.loads(pathlib.Path('plugin.toml').read_text())"
python3 skills/constitutional-prompt-framework/scripts/validate_skill_package.py skills/constitutional-prompt-framework
python3 skills/constitutional-prompt-framework/scripts/constitution_linter.py skills/constitutional-prompt-framework/examples/example-agent-constitution.md
python3 skills/constitutional-prompt-framework/scripts/score_constitution.py skills/constitutional-prompt-framework/examples/example-agent-constitution.md
python3 skills/constitutional-prompt-framework/scripts/run_static_evals.py skills/constitutional-prompt-framework/tests/eval_cases.yaml
python3 skills/constitutional-prompt-framework/scripts/render_constitution_from_spec.py skills/constitutional-prompt-framework/tests/fixtures/minimal_constitution_spec.json -o /tmp/aeriadne-cpf-rendered-check.md
```

Install verification is intentionally omitted until Daeron approves a separate local marketplace install pass.

## Marketplace role

Aeriadne is the current proof pattern for a private marketplace structure:

- `plugins/` for installable package shells.
- `skills/` for reusable cognitive payloads.
- `agents/` for role/subagent prompt packs.
- `MCP/` or `Servers/` for canonical server/tool-plane cards.
- `Registry/` for machine-readable inventory.
- `Marketplace/` for human-facing package cards and indexes.
- `Adapters/` for Codex, Claude Code, OpenCode, and Grok Build projections.

The full staged plan is in `MARKETPLACE_ROADMAP.md`.
