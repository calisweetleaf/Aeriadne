# REPO_ENTRY_MATRIX.md — Modern-ML Operational Readiness Registry

```
Classification: INTERNAL
Version:        2.0
Date:           2026-06-05
Origin:         Modern-ML / Daeron (Somnus Sovereign Systems)
Status:         OPERATIONAL
```

## Purpose

This file is the operational companion to `ECOSYSTEM_ADOPTION_MAP.md`. Its job is to answer the practical question:

> **If a coding agent is about to enter repo X, what entry surfaces already exist, what doctrine is present locally, and how ready is that repo from the perspective of the current onboarding stack?**

It is a current-state registry based on live filesystem evidence plus the visible Modern-ML mirror.

## Column Definitions

- **Doctrine** = whether `AGENTS.md`, `CONTEXT.md`, and `MEMORY.md` are present locally in that repo root (`Full`, `Partial`, `None`).

- **Extra docs** = additional high-value orientation docs visible at root (`README.md`, `ARCHITECTURE_MAP.md`, `MCP_SPEC.md`).

- **Mirror status** = whether Modern-ML currently exposes an explicit onboarding artifact for that repo/domain.

- **Primary entry** = the best visible first artifact/surface from Modern-ML for entering that repo.

- **Mentat plane** = session/runtime instrumentation availability via `Plugins/Mentat/`.

- **Somnus-MCP plane** = tool/orchestration availability via active server `/home/daeron/Somnus-MCP`.

- **Readiness** = practical operator-facing summary, not a guarantee that the repo is fully production-ready.

## Readiness Heuristic

- **Mapped+Documented** = explicit Modern-ML coverage plus full local doctrine.

- **Partially Mapped** = some explicit coverage exists, but it is nested, mixed, or incomplete.

- **Doctrine Present / Mirror Gap** = repo-local docs exist, but Modern-ML does not yet expose a dedicated entry artifact.

- **Partial Doctrine / Mirror Gap** = some local docs exist, but not enough to count as full doctrine and no dedicated Modern-ML artifact is visible.

- **Needs Entry Artifact** = no meaningful visible Modern-ML entry artifact and weak/no local doctrine at root.

## Repo Entry Matrix

| Group | Repo | Doctrine | Extra docs | Mirror status | Modern-ML artifact | Primary entry | Mentat plane | Somnus-MCP plane | Readiness |
|---|---|---|---|---|---|---|---|---|---|
| Projects | ADA-Step-Entropy | Full | README.md, ARCHITECTURE_MAP.md | Direct | Skills/CTM-Skills/ada-step-entropy; Agents/Somnus-Agents/{ada-bridge-validator, entropy-kernel-inspector, system-router-tracer} | ada-step-entropy-system-router + specialist agents | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Mapped+Documented |
| Projects | Advanced Terminal and Agentic Kernel | Full | README.md | Direct | Skills/CTM-Skills/agentic-kernel | agentic-kernel-topology | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Mapped+Documented |
| Projects | Aeron | Full | README.md, ARCHITECTURE_MAP.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Doctrine Present / Mirror Gap |
| Projects | Algorithmic-Empire | Full | README.md | Partial | Skills/CTM-Skills/fiber-map (nested subdomain only) | fiber-map-ctm | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Partially Mapped |
| Projects | Bakend-Infrustructure | Full | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Doctrine Present / Mirror Gap |
| Projects | Deep-Think | None | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Projects | Fuel-rod-MoE | None | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Projects | Full-RLHF-Pipeline | Full | README.md | Direct/Mixed | Skills/Domain-Skills/enhanced-op-sota; Skills/Domain-Skills/polyphonic-agent-factory | enhanced-op-sota (primary) | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Mapped+Documented |
| Projects | Garlic | Full | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Doctrine Present / Mirror Gap |
| Projects | garlic-embed-docs | Partial | README.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Partial Doctrine / Mirror Gap |
| Projects | Kwisatz | Full | README.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Doctrine Present / Mirror Gap |
| Projects | mcp_server | Partial | MCP_SPEC.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Partial Doctrine / Mirror Gap |
| Projects | Modern-ML | Full | README.md, ARCHITECTURE_MAP.md | Direct | Local repo docs + inventory + maps | AGENTS.md -> README.md -> inventory/maps | Available; useful while evolving onboarding docs | Mirrored here as server plane | Mapped+Documented |
| Projects | NLA_HardwareBased_NN | None | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Projects | Operation-sota | None | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Projects | Somnus-Openrouter-Router | Full | README.md | Direct | Skills/CTM-Skills/somnus-openrouter | somnus-openrouter-router | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Mapped+Documented |
| Projects | Somnus-Router | Full | README.md | Direct | Skills/CTM-Skills/somnus-router | somnus-router | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Mapped+Documented |
| Projects | Somnus-Sovereign-Systems | Full | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Doctrine Present / Mirror Gap |
| Projects | v3_LoRa_Prototype | None | README.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Repositories | Aeron | None | README.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Repositories | distill-the-flow | None | — | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Repositories | Muaddib | Full | README.md, ARCHITECTURE_MAP.md, MCP_SPEC.md | Legacy mirror | Servers/Muaddib (legacy) | Servers/Somnus-MCP (active) | Optional | Active server plane via Somnus-MCP | Doctrine Present / Legacy Mirror |
| Repositories | Reinforcement-Learning-Full-Pipeline | None | README.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |
| Repositories | SOTA-Runtime-Core | None | README.md | Absent in mirror | — | — | Available; likely for long multi-turn session work | Available; likely for tool/orchestration-heavy work | Needs Entry Artifact |

## Immediate Priorities

### Highest-confidence ready entry lanes

- `ADA-Step-Entropy`
- `Advanced Terminal and Agentic Kernel`
- `Full-RLHF-Pipeline`
- `Somnus-Router`
- `Somnus-Openrouter-Router`
- `Muaddib`
- `Modern-ML` itself

### Strong doctrine exists but Modern-ML mirror still lags

- `Aeron` (project copy)
- `Bakend-Infrustructure`
- `Garlic`
- `Kwisatz`
- `Somnus-Sovereign-Systems`

### Most obvious next entry-artifact gaps

- `Deep-Think`
- `Fuel-rod-MoE`
- `NLA_HardwareBased_NN`
- `SOTA-Runtime-Core`
- `distill-the-flow`
- `Reinforcement-Learning-Full-Pipeline`

## Notes and Caveats

- `Algorithmic-Empire` is marked **Partially Mapped** because the current explicit coverage is for the nested `fiber-map` domain, not the whole umbrella repo.

- `Full-RLHF-Pipeline` is marked `Direct/Mixed` because `enhanced-op-sota` is explicit, but `polyphonic-agent-factory` is broader and not as cleanly repo-scoped.

- `Mentat` and `Somnus-MCP` are treated as **global support planes** available across repos, but availability does not mean every repo already has an ideal repo-specific entry artifact.

- `Aeron` appears both under `Projects/` and `Repositories/`; the project copy currently has much stronger local doctrine evidence.

## Suggested Next Move

The next highest-value documentation move after this registry is to create targeted CTM or doctrine-entry artifacts for the repos currently marked **Needs Entry Artifact** or **Doctrine Present / Mirror Gap**. That would convert this matrix from a visibility registry into a real onboarding rollout plan.
