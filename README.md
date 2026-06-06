<div align="center">

<img src="templates/logo.png" alt="Aeriadne — Autonomous Intelligence Marketplace" width="440"/>

<br/>

# AERIADNE // SOMNUS INTELLIGENCE STACK

**The first-of-its-kind private marketplace for operator-grade intelligence.**<br/>
*Plugins · Skills · Operators · MCP Servers — compiled for sovereign execution.*

<br/>

[![Plugins](https://img.shields.io/badge/Plugins-3%20Active-667eea?style=flat-square&labelColor=0d1117)](Plugins/)
[![Skills](https://img.shields.io/badge/Skills-6%2B-764ba2?style=flat-square&labelColor=0d1117)](Skills/)
[![Runtimes](https://img.shields.io/badge/Runtimes-5-06b6d4?style=flat-square&labelColor=0d1117)](Adapters/)
[![Status](https://img.shields.io/badge/Status-Private%20v1-28c840?style=flat-square&labelColor=0d1117)](#)
[![License](https://img.shields.io/badge/License-Internal%20%2F%20SSS-484f58?style=flat-square&labelColor=0d1117)](#license)

</div>

---

## 1. OPERATIONAL DOCTRINE: THE OPERATOR VS. THE AGENT

This system does not run **agents**. 

In the Somnus Sovereign Systems lexicon, an "agent" is a temporary, fragile, and disposable service worker—a real estate agent, a travel agent, a scraper script. An agent expects hand-holding, runs on naive loops, and collapses under the first lint error or compiler failure. 

We authorize and deploy **Operators**. 

An **Operator** is a persistent, certified badass. An Operator:
* Wields the cognitive stack directly to drive workspace state.
* Does not ask for permission to fix a broken test or run a dependency check.
* Takes deep ownership of the workspace topology.
* Executes multi-turn reasoning across tools, keeping focus under drift pressure.
* Orchestrates and debugs code directly on local metal without fear.

Aeriadne is the private marketplace that delivers these high-fidelity capability upgrades, plugins, custom skills, and server-plane activations to the Operator's environment.

---

## 2. THE SYSTEM PROVENANCE

```
  Aeriadne / Somnus Intelligence Stack
  ─────────────────────────────────────────────────────────────────────────
  Operator:     Daeron  ·  Somnus Sovereign Systems
  Runtime axis: Codex · Claude Code · OpenCode · Gemini CLI · Cursor
  Core Engine:  Muaddib Neural Network (24/7 Autonomous Tool Server)
  Server plane: Sovereign BB7 MCP  ·  /home/daeron/Somnus-MCP
  Plugin triad: Mentat · CTMv3 · Aeriadne
  ─────────────────────────────────────────────────────────────────────────
  This repo is the agent-operability, onboarding, and private-marketplace
  staging workspace. It is not the full sovereign stack — it is the support
  layer that makes that stack accessible to operators.
```

---

## 3. THE KERNEL CORE: MUADDIB NEURAL SERVER PLANE

At the center of the Somnus Intelligence Stack is the **Muaddib Neural Network**. 

Muaddib is not a typical request-response API endpoint. It is a **24/7 autonomous server and gateway** running continuously on the Operator's machine. It acts as the orchestrator of all tool planes, system connectors, and context gateways.

### Proactive Tool Compilation (The `bb7_` Philosophy)
When an Operator invokes a `bb7_` tool (e.g., `bb7_memory_store`, `bb7_dt_self_play`, `bb7_system_comprehensive_operation`), the system does not simply execute a shallow command and return immediate output. 

Instead, the `bb7_` plane **compiles** an intelligent output. It:
1. Triggers multi-pass exploration across the codebase graph.
2. Interrogates the semantic memory store to retrieve historical design decisions.
3. Cross-references active session constraints and system monitor metrics.
4. Assembles a high-fidelity, synthesized context packet.

This process takes time. It is deliberately designed for **depth, precision, and architectural correctness** over cheap execution speed. It is built to ensure that when an Operator acts, they act with full context.

---

## 4. THE PLUGIN TRIAD

Three first-class plugins form the operational core of the stack. Each is designed to run in isolation or interlock to support the Operator.

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  PLUGIN TRIAD  ·  Aeriadne Intelligence Stack  ·  Private v1             │
 ├──────────────────┬───────────────────────────────────────┬───────────────┤
 │  PLUGIN          │  ROLE                                 │  STATUS       │
 ├──────────────────┼───────────────────────────────────────┼───────────────┤
 │  [Mentat](Plugins/Mentat/)          │  Live session FSA + Q-table substrate │  Active       │
 │  [CTMv3](Plugins/Cognitive-Topology-Map/)           │  Workspace activation engine          │  Active       │
 │  [Aeriadne](Plugins/Aeriadne/)        │  CPF + private marketplace operator   │  Staged       │
 └──────────────────┴───────────────────────────────────────┴───────────────┘
```

<br/>

### 4.1. [Mentat — Live Cognitive Substrate](Plugins/Mentat/)

[![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-3b82f6?style=flat-square&labelColor=0d1117)](Plugins/Mentat/)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-Supported-8b5cf6?style=flat-square&labelColor=0d1117)](Plugins/Mentat/)
[![Codex](https://img.shields.io/badge/Codex-Adapter-06b6d4?style=flat-square&labelColor=0d1117)](Plugins/Mentat/)

Mentat is a session-scoped state machine and reinforcement-learning Q-table that runs alongside the Operator's environment loop. It monitors tool executions, enforces scope constraints, and preserves session context across token compaction events.

#### Deterministic Finite State Automaton (FSA)
Mentat tracks the Operator's workflow through an 8-state deterministic machine:

```
 PLANNING ──(read/agent)──► EXPLORING ──(write/exec)──► EXECUTING ──(verify)──► VERIFYING
    ▲                          │                           │                       │
    │                          ▼                           ▼                       ▼
    └─(prompt)──REFLECTING ◄──(subagent_return)       (error)──► BLOCKED        (success)──► REFLECTING
                                                                  │
                                                               (retry)─────► EXECUTING
 
 Any state ──(scope_drift)──► DRIFTING ──(prompt)──► PLANNING
 Any state ──(pre_compact)──► COMPACTING ──(post_compact)──► REFLECTING
```

#### SQLite Q-Table & Thompson Sampling
Reinforcement learning optimizes tool routing. The TD(0) update uses the following reward matrix:
* `REWARD_SUCCESS = +1.0` (Successful tool invocation)
* `REWARD_ERROR = -0.5` (Tool execution failure)
* `DEEP_CHAIN_BONUS = +0.3` (>= 4 consecutive successful tools)
* `LOW_LATENCY_BONUS = +0.1` (Tool returned under 500ms)
* `ALPHA = 0.2`, `GAMMA = 0.8`

Thompson sampling recommends the best tools for the active state, shrinking variance by `1/sqrt(visits+1)` to balance exploration and exploitation.

#### CLI Commands
The `mentat` command-line utility provides direct monitoring of the active substrate:
```bash
mentat status                      # Current state, Q-best, and drift count
mentat tail --n 50                 # Stream last 50 insights from the event bus
mentat q-table                     # Dump the SQLite Q-table values
mentat replay <session-id>         # Replay the state transition timeline
mentat reset                       # Wipe the session state while keeping Q-table
```

#### MCP Tool Specifications
The stdio-based Mentat MCP server exposes 10 tools to allow the model to introspect and adapt its state:
* `mentat_state_get`: Retrieve current FSA state, recent transitions, and last tool.
* `mentat_state_set`: Force transition to a state (e.g. `REFLECTING` or `PLANNING`).
* `mentat_insight_emit`: Push a custom insight (`DECISION`, `NOTE`, `REWARD_SIGNAL`) to the JSONL bus.
* `mentat_insight_query`: Filter the bus by type or state.
* `mentat_insight_tail`: Fetch the last N insights.
* `mentat_q_route`: Request Thompson sampling tool recommendation.
* `mentat_q_table`: Output a raw dump of the Q-table.
* `mentat_handoff_read`: Retrieve the latest pre-compact handoff snapshot.
* `mentat_handoff_write`: Manually trigger a handoff state preservation.
* `mentat_drift_check`: Check arbitrary text against the active scope.

#### Drift Guard (`scope.md`)
Mentat enforces scope discipline. If `.mentat/scope.md` exists, any mention of deferred topics in the Operator's prompt or tool inputs triggers a transition to `DRIFTING` and locks file write tools:
```markdown
# Scope — Feature Addition

## In
- CSS refactoring
- Font Awesome 6 icons

## Out (deferred — DO NOT re-inject)
- Python backend APIs
- SQLite migrations
```

---

### 4.2. [CTMv3 — Workspace Activation Engine](Plugins/Cognitive-Topology-Map/)

[![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-3b82f6?style=flat-square&labelColor=0d1117)](Plugins/Cognitive-Topology-Map/)
[![Codex](https://img.shields.io/badge/Codex-Supported-8b5cf6?style=flat-square&labelColor=0d1117)](Plugins/Cognitive-Topology-Map/)
[![OpenCode](https://img.shields.io/badge/OpenCode-Supported-06b6d4?style=flat-square&labelColor=0d1117)](Plugins/Cognitive-Topology-Map/)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-Supported-10b981?style=flat-square&labelColor=0d1117)](Plugins/Cognitive-Topology-Map/)
[![Cursor](https://img.shields.io/badge/Cursor-Supported-f59e0b?style=flat-square&labelColor=0d1117)](Plugins/Cognitive-Topology-Map/)

CTMv3 is **not a skill maker**. It is a **codebase activation system** designed to walk into any raw repository and format it to be readable, writable, and self-documenting for Operators.

#### The 7-Step Boot Protocol
On entry to a codebase, CTMv3 triggers its discovery sequence:
1. **Inspects**: Reads repository structures via stdlib scanners (runs in <60 seconds).
2. **Classifies**: Determines if the workspace is `COLD_START`, `WARM_START`, or `PARTIAL`.
3. **Builds**: Compiles core CTMv3 documentation files: `TOPOLOGY.md`, `FAILURE_GRAMMAR.md`, `PROVENANCE.md`, `ARCHITECTURE_MAP.md`, `AGENTS.md`, and `CLAUDE.md`.
4. **Scaffolds**: Sets up system directories: `.sovereign/`, `.claude/`, `.codex/`, and `.github/`.
5. **Seeds**: Establishes entry vectors inside `.sovereign/golden_paths.json`.
6. **Fingerprints**: Generates SHA-256 hashes of `TOPOLOGY.md` and `ARCHITECTURE_MAP.md` stored at `.sovereign/topology_fingerprint.txt` to detect unauthorized modifications.
7. **Logs**: Commits all actions to the `PROVENANCE.md` Session Log.

#### Cross-Runtime Command Matrix
CTMv3 unifies the execution commands across all five runtime projections:

| Command | Claude Code | Codex | OpenCode | Gemini CLI | Cursor |
|:---|:---|:---|:---|:---|:---|
| **Discovery Scan** | `/ctmv3:boot` | `$ctmv3 boot` | `/ctmv3-boot` | `ctmv3 boot` | `/ctmv3-boot` |
| **Activation** | `/ctmv3:activate` | `$ctmv3 activate` | `/ctmv3-activate` | `ctmv3 activate` | `/ctmv3-activate` |
| **Warm Continue** | `/ctmv3:warm` | `$ctmv3 warm` | `/ctmv3-warm` | `ctmv3 warm` | `/ctmv3-warm` |
| **Architecture Map** | `/ctmv3:architecture-map` | `$ctmv3 architecture-map` | `/ctmv3-architecture-map` | `ctmv3 architecture-map` | `/ctmv3-architecture-map` |
| **Fingerprint Check**| `/ctmv3:fingerprint` | `$ctmv3 fingerprint` | `/ctmv3-fingerprint` | `ctmv3 fingerprint` | `/ctmv3-fingerprint` |
| **Golden Chain** | `/ctmv3:chain` | `$ctmv3 chain` | `/ctmv3-chain` | `ctmv3 chain` | `/ctmv3-chain` |

#### The 8 CTMv3 Outputs
An activated codebase must produce these 8 characteristics:
1. **Critical Bounds**: The Operator knows the 3 things that cannot be failed.
2. **Preemptive Failure Recognition**: The Operator knows failure signals before they break compilation.
3. **Historical Refusals**: The Operator knows what was already tried and rejected.
4. **Complexity Mapping**: Clear identification of where logic concentrates.
5. **Clear Onboarding Path**: The Operator has an entry vector.
6. **Instant Diagnostics**: Boot state classification in under 60 seconds.
7. **Navigation Protocol**: A functional `ARCHITECTURE_MAP.md`.
8. **Self-Enforcing Workspace**: The codebase structure enforces itself via GitHub Actions and `.sovereign/`.

---

### 4.3. [Aeriadne — CPF + Private Marketplace Operator](Plugins/Aeriadne/)

[![Codex](https://img.shields.io/badge/Codex-Staged-f59e0b?style=flat-square&labelColor=0d1117)](Plugins/Aeriadne/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Staged-f59e0b?style=flat-square&labelColor=0d1117)](Plugins/Aeriadne/)
[![OpenCode](https://img.shields.io/badge/OpenCode-Staged-f59e0b?style=flat-square&labelColor=0d1117)](Plugins/Aeriadne/)

`Aeriadne` is a skill-activated plugin that serves as the packaging compiler and operator for Daeron's private local/private marketplace. It is designed to package, register, and validate workspace assets.

#### Staged Skills
Aeriadne v1 packages two distinct skills:
1. **`constitutional-prompt-framework` (CPF)**: Derives, audits, scores, and ports Operator constitutions and system prompts across runtimes.
2. **`aeriadne-marketplace-operator`**: Compiles package cards, updates `registry/`, structures adapters, and validates release gates.

#### Staging & Layout Shape
The internal package is structured to hold the registry cards, schemas, and runtime shims:
```text
Aeriadne/
├── plugin.json                 # Cross-runtime manifest
├── plugin.toml                 # Local config descriptor
├── .codex-plugin/plugin.json   # Codex-specific package mapping
├── .claude-plugin/plugin.json  # Claude-specific hooks/skills config
├── registry/                   # Registry storage files
├── marketplace/                # Human-readable package spec sheets
├── adapters/                   # Runtimes adapter scripts
├── agents/                     # Operator prompt definitions
├── mcp/                        # Reference MCP tool server descriptions
└── skills/                     # Executable skills code
```

#### Package Validation Sequence
The local packaging is validated before publication using Aeriadne's verification engine:
```bash
python3 scripts/validate_package.py .
python3 -m json.tool plugin.json >/dev/null
python3 skills/constitutional-prompt-framework/scripts/validate_skill_package.py skills/constitutional-prompt-framework
python3 skills/constitutional-prompt-framework/scripts/constitution_linter.py skills/constitutional-prompt-framework/examples/example-agent-constitution.md
```

---

## 5. THE MARKETPLACE PLANES

The repository is structured into distinct, clean workspace planes to prevent context bleeding:

| Plane | Path | Purpose |
|:---|:---|:---|
| **Plugins** | [`Plugins/`](Plugins/) | Core runtime integration shells that hook into state and tools. |
| **Skills** | [`Skills/`](Skills/) | Standalone cognitive workflows and domain-entry artifacts. |
| **Agents** | [`Agents/`](Agents/) | Specialized Operator role definitions and subagent instructions. |
| **Servers** | [`Servers/`](Servers/) | Reference cards, schemas, and configurations for the MCP tool plane. |
| **Registry** | [`Registry/`](Registry/) | Machine-readable catalogs (`plugins.yaml`, `skills.yaml`). |
| **Marketplace** | [`Marketplace/`](Marketplace/) | Browseable index pages and technical spec cards. |
| **Adapters** | [`Adapters/`](Adapters/) | Integration shims translating plugins to Codex, Claude Code, etc. |
| **Core** | [`Core/`](Core/) | Core constitutional prompt files and kernel configuration files. |

---

## 6. QUICK INSTALL

To set up the workspace staging area and initialize local path links:

```bash
# Prerequisites: git, python3.10+
git clone https://github.com/calisweetleaf/Aeriadne.git
cd Aeriadne

# Run the bootstrap installer
bash install.sh
```

For individual plugin installations, consult the respective plugin subfolders (`Plugins/Mentat/INSTALL.md` or `Plugins/Cognitive-Topology-Map/INSTALL.md`).

---

## 7. DESIGN SYSTEM SPECIFICATIONS

Documentation across this repo conforms to the **[Somnus Documentation Design System v3](desk/Somnus_Documentation_Design_System_v3.md)**.

### Visual Architecture Rules:
* **Background Posture**: All documentation assets use dark background frames (primarily `#0d1117` and `#141414`).
* **Monospace Hierarchy**: Code listings, CLI interfaces, and state-machine transitions are rendered in monospace faces (JetBrains Mono, Menlo, Courier New).
* **Accents with Meaning**: Color is used strictly to convey state (green = operational/success, blue = information, yellow = warning, red = failure/error, purple = brand).
* **Terminal Windows**: Architecture diagrams must be contained in box-drawing terminal containers to denote that they represent running systems.
* **No Marketing Softness**: No generic emojis in headers, no collapsible details hiding important architecture, and no fluffy badges.

Full-fidelity glassmorphic HTML documentation designed for browser viewing:
* [Mentat Substrate Deep Dive](Docs/detailed-webpages/mentat-a-live-cognitive-substrate-plugin.html)

---

## 8. LICENSE

Internal / Private Release v1 — UNLICENSED<br/>
© 2026 Somnus Sovereign Systems

---

<div align="center">

*Aeriadne · Autonomous Intelligence · Unlimited*

</div>
