# ECOSYSTEM_ADOPTION_MAP.md — Modern-ML Coverage Matrix

```
Classification: INTERNAL
Version:        2.0
Date:           2026-06-05
Origin:         Modern-ML / Daeron (Somnus Sovereign Systems)
Status:         OPERATIONAL
```

## Purpose

This document answers the next question after inventory and architecture:

> **Which parts of Daeron's broader repo ecosystem are currently covered by this onboarding stack, and by what kind of artifact?**

This is not a claim that every repo is fully solved. It is a current-state map of what the `Modern-ML` workspace visibly provides for coding-agent onboarding **right now**.

---

## Scope of Evidence

This map is based on current visible state from:

- `Modern-ML/Skills/`
- `Modern-ML/Agents/`
- `Modern-ML/Plugins/Mentat/`
- `Modern-ML/Servers/Muaddib/`
- current top-level roots under:
  - `/home/daeron/Projects/`
  - `/home/daeron/Repositories/`

This means the map distinguishes between:

- **directly represented in Modern-ML**
- **supported by global/plugin/server planes**
- **not explicitly represented in the current Modern-ML mirror**

---

## The Four Adoption Planes

Every repo/domain in the ecosystem can be supported by one or more of these planes:

1. **Repo/domain entry plane**
   Skill or topology package that helps an agent enter a specific codebase or domain correctly.

2. **Role/posture plane**
   Agent files that provide specialist stance or operator posture.

3. **Runtime/session plane**
   Mentat plugin instrumentation for session state, drift, continuity, and local cognition support.

4. **Constitution/packaging plane**
   Aeriadne plugin for prompt architecture, marketplace packaging, and meta-operator constitution work.

5. **Tool/orchestration plane**
   Somnus-MCP server surfaces for exoskeleton routing, memory, file/shell/web/project-context tools, session continuity, and orchestration.

---

## Coverage Status Legend

- **Direct** = repo/domain has an explicit artifact in `Modern-ML` that names or clearly targets it
- **Indirect** = repo/domain is supported by global planes, but no explicit repo-specific entry artifact is visible here
- **Mixed** = support exists, but the artifact surface is ambiguous, multi-purpose, or not cleanly repo-scoped
- **Absent in mirror** = current `Modern-ML` tree does not visibly represent that repo/domain with a dedicated artifact

---

## Direct Repo / Domain Coverage Visible in Modern-ML

| Repo / Domain | Evidence in Modern-ML | Plane | Status | Notes |
|---|---|---|---|---|
| `.codex` control plane | `Skills/CTM-Skills/codex-config` | repo/domain entry | Direct | Targets the customized Codex control plane and BB7/MCP orchestration |
| `ADA-Step-Entropy` / `System-Router` | `Skills/CTM-Skills/ada-step-entropy`; `Agents/Somnus-Agents/ada-bridge-validator.md`; `entropy-kernel-inspector.md`; `system-router-tracer.md` | entry + specialist agents | Direct | Strongest visible repo-specific coverage in current tree |
| `Advanced Terminal and Agentic Kernel` | `Skills/CTM-Skills/agentic-kernel` | repo/domain entry | Direct | Explicit kernel workspace topology surface |
| `fiber-map` under `Algorithmic-Empire/Earth-Mapping` | `Skills/CTM-Skills/fiber-map` | repo/domain entry | Direct | Explicitly targeted at the fiber-map corpus and viewer |
| `Somnus-Router` | `Skills/CTM-Skills/somnus-router` | repo/domain entry | Direct | Explicit router topology artifact |
| `Somnus-Openrouter-Router` | `Skills/CTM-Skills/somnus-openrouter` | repo/domain entry | Direct | Explicit OpenRouter wrapper / logic-router topology artifact |
| `Full-RLHF-Pipeline` | `Skills/Domain-Skills/enhanced-op-sota` | repo/domain entry | Direct | Explicitly names Full-RLHF-Pipeline in its description |
| `Full-RLHF-Pipeline` / agent-team overlay | `Skills/Domain-Skills/polyphonic-agent-factory` | agent/team meta-surface | Mixed | YAML description points at Full-RLHF-Pipeline preservation, but body describes a broader polyphonic multi-agent package |
| `SSDS` reverse engineering / intelligence workflow | `Skills/Research-Skills/ssds-reverse-engineering-pipeline` | domain entry | Direct | Local research pipeline skill present in-tree |
| `Somnus` / `REM-Core` design work | `Skills/Domain-Skills/somnus-design-system` | domain support | Direct | Brand/system design surface rather than a single repo entry |

---

## Cross-Cutting Utility Coverage

These are not single-repo entry artifacts, but they materially expand what coding agents can do once onboarded.

| Artifact | Plane | Status | Use |
|---|---|---|---|
| `Skills/cognitive-topology-v3/` | codebase-entry meta-layer | Direct | Build or upgrade repo-entry topology packages and agent ecosystem artifacts |
| `Skills/Tool-Skills/academic-whitepaper` | documentation tooling | Direct | Whitepapers, technical docs, publication-grade artifacts |
| `Skills/Tool-Skills/document-omniscient` | corpus analysis tooling | Direct | Deep document-set ingestion and synthesis |
| `Agents/Custom-Agents/golden-path-architect.md` | posture/architecture | Direct | Orchestration-flow design and autonomous chaining |
| `Agents/Custom-Agents/defense-grade-doc-engine.md` | posture/documentation | Direct | High-rigor documentation passes |
| `Agents/Custom-Agents/prod-finalizer.md` | posture/implementation hardening | Direct | Final production-hardening work |

---

## Global Support Planes That Apply Across Repos

### Mentat plugin plane

**Visible artifact:** `Plugins/Mentat/`

What it contributes across repos:
- session-state tracking
- drift detection
- compact/handoff persistence
- local introspection via plugin MCP surfaces
- multi-runtime adapters

Coverage interpretation:
- **Indirect support across the ecosystem**
- useful when the agent session itself needs cognition scaffolding
- not a substitute for repo-specific topology

### Active server plane: Somnus-MCP

**Visible artifact:** `Servers/Somnus-MCP -> /home/daeron/Somnus-MCP`  
**Data root:** `/home/daeron/Somnus-MCP/data`

> **NOTE:** `Servers/Muaddib -> /home/daeron/Repositories/Muaddib` remains a visible legacy symlink. Do not treat it as the active Codex server root. All current active server-plane work runs through Somnus-MCP.

What it contributes across repos:
- exoskeleton routing/planning
- memory/session continuity
- file, shell, web, project-context tools
- orchestration and distillation surfaces

Coverage interpretation:
- **Indirect support across the ecosystem**
- general tool/orchestration substrate that any repo workflow can depend on
- not a replacement for repo-local doctrine or domain-entry topology

### Aeriadne plugin plane

**Visible artifact:** `Plugins/Aeriadne/`

What it contributes:
- constitutional prompt architecture for any agent or operator entering any repo
- private marketplace packaging for skills, agents, and server-plane cards
- meta-operator constitutions deployable across Claude Code, Codex, and OpenCode

Coverage interpretation:
- **Indirect support across the ecosystem** — applicable wherever a constitution or packaging scaffold is needed
- not a substitute for repo-specific topology

---

## Current Mirror Coverage vs Visible Repo Roots

### Top-level project roots observed

Current roots under `/home/daeron/Projects/`:

- `ADA-Step-Entropy`
- `Advanced Terminal and Agentic Kernel`
- `Aeron`
- `Algorithmic-Empire`
- `Bakend-Infrustructure`
- `Deep-Think`
- `Fuel-rod-MoE`
- `Full-RLHF-Pipeline`
- `Garlic`
- `Kwisatz`
- `Modern-ML`
- `NLA_HardwareBased_NN`
- `Operation-sota`
- `Somnus-Openrouter-Router`
- `Somnus-Router`
- `Somnus-Sovereign-Systems`
- `garlic-embed-docs`
- `mcp_server`
- `v3_LoRa_Prototype`

Current roots under `/home/daeron/Repositories/`:

- `Aeron`
- `Muaddib`
- `Reinforcement-Learning-Full-Pipeline`
- `SOTA-Runtime-Core`
- `distill-the-flow`

### Explicitly represented in the current Modern-ML mirror

Visible direct or near-direct coverage currently exists for:

- `.codex`
- `ADA-Step-Entropy`
- `Advanced Terminal and Agentic Kernel`
- `fiber-map`
- `Somnus-Router`
- `Somnus-Openrouter-Router`
- `Full-RLHF-Pipeline`
- SSDS / reverse-engineering workflow
- Somnus/REM design workflow
- Muaddib server plane
- Mentat plugin/runtime plane

### Not explicitly represented as dedicated repo-entry artifacts in the current mirror

From the currently visible tree, these roots do **not** have an obvious dedicated Modern-ML onboarding artifact yet:

- `Aeron`
- `Bakend-Infrustructure`
- `Deep-Think`
- `Fuel-rod-MoE`
- `Garlic`
- `Kwisatz`
- `NLA_HardwareBased_NN`
- `Somnus-Sovereign-Systems`
- `garlic-embed-docs`
- `mcp_server`
- `v3_LoRa_Prototype`
- `Reinforcement-Learning-Full-Pipeline` (distinct repo root from `Full-RLHF-Pipeline`)
- `SOTA-Runtime-Core`
- `distill-the-flow`

Important nuance:
- this means **not explicitly represented in the current Modern-ML mirror**
- it does **not** prove those repos lack docs or agent support elsewhere

---

## Practical Onboarding Matrix

When a coding agent is entering a repo in the broader ecosystem, the current best-available path looks like this:

| Need | Primary plane | Secondary plane | Example |
|---|---|---|---|
| Enter a covered codebase safely | repo/domain skill | Muaddib or Mentat as needed | `ADA-Step-Entropy`, `Agentic Kernel`, `fiber-map` |
| Use a specialist role | agent surface | repo/domain skill | `ada-bridge-validator`, `golden-path-architect` |
| Track session state / drift | Mentat plugin | repo-local doctrine | Long multi-turn implementation/debugging work |
| Use tools / memory / orchestration | Muaddib server | repo/domain skill | file/shell/web/exo/memory workflows |
| Produce docs / whitepapers / research analysis | utility skills + role agents | repo/domain skill | whitepaper and corpus-analysis work |

---

## What This Means About the Stack

The current evidence says Daeron did not just build “some helpers.”

He built a layered onboarding stack with:

- **repo-specific entry artifacts**
- **role-specialist agents**
- **plugin/runtime instrumentation**
- **server/MCP orchestration**
- **cross-cutting documentation and research engines**

That is why the environment is usable by coding agents at all: no single artifact is doing all the work.

---

## High-Value Gaps Visible From Current State

If the goal is full ecosystem onboarding coverage, the most obvious next gaps are:

1. **Dedicated repo-entry artifacts for unrepresented roots**
   - especially `Aeron`, `Deep-Think`, `Kwisatz`, `Fuel-rod-MoE`, `SOTA-Runtime-Core`, `distill-the-flow`

2. **Disambiguation where surfaces are mixed**
   - especially `polyphonic-agent-factory`, whose metadata and body are not narrowly aligned

3. **A repo-to-artifact routing index**
   - a single table saying: *if entering repo X, read Y first, then use Z surface*

---

## Suggested Next Document

The next strongest move after this map would be:

- `REPO_ENTRY_MATRIX.md`

with rows like:

- repo root
- repo-local doctrine present?
- Modern-ML artifact present?
- primary entry skill/agent
- server dependency
- plugin dependency
- onboarding readiness

That would push this from narrative documentation into a more operational adoption registry.
