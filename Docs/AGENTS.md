# AGENTS.md — Modern-ML

## Purpose

`Modern-ML` is not a generic code repo and not the full sovereign ML empire itself. It is the **agent-operability, onboarding, and private-marketplace staging workspace**: the place where plugins, skills, agent definitions, topology packages, MCP/server visibility cards, and registry scaffolds are organized so coding agents can enter Daeron's broader ecosystem without guessing blind.

This repo exists because the surrounding system is already large and specialized. The point here is to expose the support stack cleanly enough that future coding agents can adopt into the environment rather than flattening it into stock “vibe coding” assumptions.

## Precedence

Apply doctrine in this order:

1. Global `.codex` control-plane/runtime law
2. This repo-local `AGENTS.md`
3. This repo-local `CONTEXT.md`
4. This repo-local `MEMORY.md`
5. `README.md` and inventory docs

Global safety/runtime posture still comes from `.codex`, but this file controls how to interpret **Modern-ML specifically**.

## What This Repo Actually Is

This workspace is an aggregation surface across five distinct layers:

1. **Agents** — operator-facing role files and subagent prompt surfaces
2. **Plugins** — installable runtime/cognitive packages, including Mentat, CTMv3, Codex Config Topology, and Aeriadne
3. **Skills / topology packages** — reusable domain-entry, prompt-architecture, marketplace-operator, and codebase-entry artifacts
4. **MCP/server references** — cards/visibility around canonical server/tool planes such as Somnus-MCP / BB7
5. **Marketplace registry/docs** — private/local package inventory and future install surface

This repo is therefore both:

- a documentation workspace,
- a package staging workspace,
- and a topology mirror/index over canonical sources that sometimes live elsewhere.

## Critical Ontology

These distinctions are load-bearing. Do not blur them.

- **Aeriadne is the current CPF/private-marketplace plugin package**
  - canonical local surface here: `plugins/Aeriadne/`
  - contains two skills: `constitutional-prompt-framework` and `aeriadne-marketplace-operator`
  - expected future Codex exposure: `aeriadne:constitutional-prompt-framework` and `aeriadne:aeriadne-marketplace-operator`
  - not installed in Codex yet unless later evidence says otherwise

- **Codex Config Topology is no longer a staged plugin**
  - the old plugin package was deleted from the staging tree for public-clean consolidation
  - the standalone `codex-config-topology` skill remains useful
  - it was previously installed as `codex-config-topology@local`; do not treat it as part of the active plugin triad unless current runtime evidence says so

- **Mentat is the plugin/runtime substrate**
  - canonical local surface here: `plugins/Mentat/`
  - it includes hooks, adapters, evals, monitors, state-machine logic, commands, and plugin packaging

- **Somnus-MCP is the active server/MCP plane**
  - active root: `/home/daeron/Somnus-MCP`
  - active data root: `/home/daeron/Somnus-MCP/data`
  - `Servers/Muaddib -> /home/daeron/Repositories/Muaddib` may still appear as a legacy visible mirror/symlink artifact
  - do not call server-plane surfaces “the plugin”

- **`cognitive-topology-v3` / CTMv3 is not just a skill maker**
  - treat it as a **portable codebase-entry / workspace-topology package**
  - it is meant to be instantiated upon entry to a codebase and then maintained as part of that workspace’s durable agent context

- **Modern-ML is an onboarding/private-marketplace layer**
  - it is the stack built to make agents usable
  - it is not merely a collection of prompts

## Local vs Linked Reality

Do not assume everything here is local.

### Local payloads commonly include

- `plugins/Aeriadne/`
- `plugins/Cognitive-Topology-Map/`
- `plugins/Mentat/`
- `skills/cognitive-topology-v3/`
- `skills/Research-Skills/ssds-reverse-engineering-pipeline/`
- local inventory and orientation docs

### Linked/mirrored surfaces commonly include

- agent files under `Agents/` from `/home/daeron/.claude/agents/`
- many skill directories under `Skills/` from `/home/daeron/.opencode/skills/custom/`
- server mirrors under `Servers/` pointing at legacy/canonical repos, while active Codex server-plane work uses `/home/daeron/Somnus-MCP`

When documenting this repo, always distinguish:

- **local file content**
- **symlinked mirrors**
- **external canonical repos**

## Documentation Rules

When updating this repo:

1. Preserve the ontology above.
2. Prefer **evidence-first filesystem descriptions** over vague architectural prose.
3. Include sizes, symlink targets, validation status, or explicit path provenance when that helps future agents orient.
4. Keep `5-22-2026-modernMlTools-filetree.md` or its successor truthful to current state when inventory work is in scope.
5. Update `CONTEXT.md` and `MEMORY.md` after meaningful structural changes.
6. Expand `README.md` when the workspace topology changes enough that a new agent would misread the repo.
7. Do not claim a plugin is installed/enabled without command evidence.

## What Not To Say

Avoid these failure modes:

- do not describe `cognitive-topology-v3` as “the skill maker”
- do not collapse Mentat and the active server/MCP plane into one thing
- do not claim everything under `Skills/` is local
- do not describe this workspace as the total ML stack; it is the **support/onboarding/private-marketplace layer** around that stack
- do not treat Aeriadne as BB7, Mentat, or CTMv3
- do not install both `aeriadne@local` and legacy `cpf-plugin-ariadne@local` unless duplicate CPF exposure is intentional

## Current High-Value Artifacts

- `AGENTS.md` — primary entry; ontology, precedence, and workspace role
- `TECHNICAL_REFERENCE.md` — master technical spec with architecture, plane specs, flows, installation, glossary
- `CONTEXT.md` — current runtime state
- `MEMORY.md` — durable decisions, plugin ontology, gotchas
- `ARCHITECTURE_MAP.md` — interaction map across all planes
- `ECOSYSTEM_ADOPTION_MAP.md` — repo coverage matrix
- `REPO_ENTRY_MATRIX.md` — per-repo onboarding readiness registry
- `plugins/Aeriadne/` — unified marketplace operator and constitutional prompt compiler
- `plugins/Cognitive-Topology-Map/` — CTMv3 workspace activation package
- `plugins/Mentat/` — live session runtime substrate

## Recommended Structural Direction

The clean long-term shape for this repo is evolving toward:

```text
Modern-ML/
├── plugins/
├── skills/
├── agents/
├── MCP/ or Servers/
├── Registry/
├── Marketplace/
├── Adapters/
└── docs / inventories
```

That keeps plugin, skill, agent, MCP/server, registry, and rendered marketplace planes separated while still allowing package-specific scaffolds such as `Plugins/Aeriadne/registry/` during v1 staging.
