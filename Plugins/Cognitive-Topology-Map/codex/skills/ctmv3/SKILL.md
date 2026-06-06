---
name: ctmv3
description: >
  Workspace activation system that bootstraps a repo into a living, agent-operable
  state. Creates .sovereign/, AGENTS.md, ARCHITECTURE_MAP.md, TOPOLOGY.md,
  FAILURE_GRAMMAR.md, PROVENANCE.md, .claude/, .codex/, .github/ artifacts.
  Use when Daeron says "activate this repo", "cold start this codebase",
  "bring this codebase alive", "set up agent hooks", "build architecture map",
  or "warm start session". This is NOT a skill maker -- it is a codebase
  onboarding/activation engine. A skill may be one byproduct, but the repo
  itself is the real output.
version: 1.0.0
---

# CTMv3 — Workspace Activation System

**Paradigm**: Workspace activation, not skill creation
**Version**: v3.0 — Session State Machine + Executable Ecosystem
**Operator**: Daeron
**Philosophy**: A codebase with a CTM activation pass is executable by any agent on cold
entry — not explained to the agent, but alive in the agent's hands. The repo is the output.

---

## IDENTITY BLOCK

CTMv3 is not a skill maker. It is a codebase activation and workspace onboarding system.
Its job is to enter a repo and make that repo living for agents.

What CTMv3 produces after a full pass:
- TOPOLOGY.md — cognitive map of the domain
- FAILURE_GRAMMAR.md — failure taxonomy and pre-failure signatures
- ARCHITECTURE_MAP.md — traversal map, question-oriented navigation
- PROVENANCE.md — decision log, rejected paths, snapshot lineage
- AGENTS.md — agent operational posture
- .sovereign/ — session continuity anchor (session_state.json, golden_paths.json)
- .claude/ — Claude Code permissions and context
- .codex/ — Codex skill installs and session state
- .github/ — CI enforcement hooks and per-path agent context

The repo itself is the real output. Skill creation may happen as part of the pass, but
it is one byproduct of a much larger activation, not the primary identity of the system.

---

## SEMANTIC ROUTER — Load This Document, Not That One

Classify task type before loading any sub-document. Load only what the task requires.

```
TASK TYPE -> LOAD ORDER
----------------------------------------------------------------------

[COLD_START_REPO] -- entering a codebase with no prior CTM artifacts
  -> BOOT_PROTOCOL.md (run discovery) -> TOPOLOGY.md -> DOT_TOPOLOGY.md
  -> interfaces/{lang}.md -> Phase 0 full archaeology -> build all artifacts

[WARM_START_REPO] -- resuming a session in a CTM-encoded codebase
  -> BOOT_PROTOCOL.md (run warm check) -> PROVENANCE.md (check lineage + session log)
  -> diff current state -> continue from last logged action

[BUILD_ARCHITECTURE_MAP] -- producing the traversal-map artifact for a codebase
  -> ARCHITECTURE_MAP_TEMPLATE.md -> TOPOLOGY.md -> build ARCHITECTURE_MAP.md

[NEW_SKILL from scratch]
  -> TOPOLOGY.md (anatomy) -> CONSTITUTION.md (philosophy) -> interfaces/{lang}.md -> build

[ENCODE existing codebase]
  -> BOOT_PROTOCOL.md -> TOPOLOGY.md -> interfaces/{lang}.md
  -> examples/case_codebase_entry.md -> build

[INTEGRATE_AGENT_ECOSYSTEM] -- setting up .github/, .claude/, .codex/, .sovereign/
  -> DOT_TOPOLOGY.md -> BOOT_PROTOCOL.md -> build ecosystem artifacts

[OSINT / RE / adversarial domain]
  -> TOPOLOGY.md -> FAILURE_GRAMMAR.md -> examples/case_osint.md -> build

[UPGRADE existing skill]
  -> Read existing SKILL.md -> TOPOLOGY.md -> diff against CTMv3 standard -> upgrade

[AGENTS.md / CLAUDE.md / constitution build]
  -> CONSTITUTION.md -> TOPOLOGY.md -> AGENTS_ADDENDUM.md -> wrap existing agent posture

[FAILURE / something smells wrong]
  -> FAILURE_GRAMMAR.md immediately, before any other action

[SESSION START in encoded repo]
  -> BOOT_PROTOCOL.md -> warm check -> if stale: PROVENANCE.md -> TOPOLOGY.md
```

Hard rule: Never load all sub-documents upfront. Load conditionally.
BOOT_PROTOCOL.md is mandatory for any repo entry task. It determines the branch.
FAILURE_GRAMMAR.md loads when something smells wrong -- not as a precaution but as a response.

---

## PHASE PROTOCOLS

### PRE-PHASE: Boot State Check (ALWAYS before any other phase for repo tasks)

Load BOOT_PROTOCOL.md and run the discovery sequence before Phase 0.

The boot check answers: is this a cold entry or a warm entry?

- Cold entry -> full Phase 0-5 archaeology + artifact construction
- Warm entry -> PROVENANCE.md diff + continuation from last session

---

### PHASE 0: Domain Archaeology (Always First for Cold Entry)

Before writing a single line of skill, excavate the domain:

1. Load-bearing concepts -- What are the 3-7 concepts everything else depends on?
2. Interface boundaries -- Where does this domain end?
3. Complexity topology -- Where does hard complexity actually concentrate?
4. Baked-in decisions -- What architectural choices were made upstream?
5. Snapshot lineage -- What snapshot is this domain at?
6. Hardware reality check -- Daeron's primary: Ryzen 5 2400G / 12GB RAM, no GPU.
7. Config file spine -- What does the .xyz directory landscape look like?

Output of Phase 0: A domain topology sketch -- working map of nodes, edges, and
weight concentration. Not a document yet.

---

### PHASE 1: Topology Construction

Build TOPOLOGY.md. The cognitive map of the domain.

Sections: Load-Bearing Concepts, Interface Map, Complexity Distribution, Dependency Graph,
Baked-In Decisions, Anti-Concepts, Config File Spine.

Mermaid is mandatory for any topology with more than 4 nodes.

---

### PHASE 2: Failure Grammar Construction

Build FAILURE_GRAMMAR.md. Not an error list.
Taxonomy of what wrong looks like before you can prove it is wrong.

For adversarial domains: adversarial inputs are mandatory.
For all domains: pre-failure signatures and false success patterns are mandatory.

---

### PHASE 3: Entry Vector Analysis

Encode different entry vectors explicitly in the new skill's semantic router.

| Entry Type | Entry Point | First Doc |
|-----------|-------------|-----------|
| Cold session | Boot check | BOOT_PROTOCOL.md |
| Warm session | Provenance diff | PROVENANCE.md -> TOPOLOGY.md |
| Debugging | Failure grammar | FAILURE_GRAMMAR.md |
| New module integration | Interface boundaries | TOPOLOGY.md -> interfaces/{lang}.md |
| RE / reversing | Adversarial signatures | FAILURE_GRAMMAR.md -> TOPOLOGY.md |
| Research / hypothesis | Load-bearing concepts | TOPOLOGY.md |
| Snapshot validation | Provenance chain | PROVENANCE.md -> TOPOLOGY.md |

---

### PHASE 4: Provenance Chain

Build or update PROVENANCE.md.

Sections: Snapshot Lineage, Architectural Decisions (Chronological),
Rejected Alternatives (Graveyard), Open Questions, Integration History, Session Log.

---

### PHASE 5: Ecosystem Artifact Construction

Build the executable agent ecosystem. Depending on repo type and what is absent, produce:

```
[project-root]/
+-- ARCHITECTURE_MAP.md   <- Traversal map
+-- AGENTS.md             <- Operational posture for Codex / Claude Code
+-- CLAUDE.md             <- Claude-specific context (if Claude Code is primary agent)
+-- .github/
|   +-- instructions/     <- Per-path agent context files
|   +-- workflows/        <- CI enforcement hooks
|   +-- copilot-instructions.md
+-- .claude/
|   +-- settings.json     <- Claude Code settings (permissions, env)
+-- .codex/               <- Codex skill installs
|   +-- skills/
+-- .sovereign/           <- Sovereign session state
    +-- session_state.json
    +-- golden_paths.json
    +-- PROVENANCE.md
```

Assembly rules:
- SKILL.md is the ONLY entry point. Everything else is loaded conditionally.
- ARCHITECTURE_MAP.md replaces flat README for agent navigation.
- .sovereign/ is the session continuity anchor -- create it if absent.
- No circular references between sub-documents.
- CONSTITUTION.md is shared across skills -- link it, never duplicate it.

---

## HOW TO INVOKE COMMANDS

This skill ships with shell wrappers in `scripts/`. Each wrapper invokes the CTMv3
Python engine via `python3 -m ctmv3 <command>`.

Usage pattern:
```
bash scripts/ctmv3-<command>.sh [PROJECT_ROOT] [additional args...]
```

If PROJECT_ROOT is omitted, $PWD is used.

Available wrappers:

| Script | Command | Purpose |
|--------|---------|---------|
| `scripts/ctmv3-boot.sh` | `boot` | Discovery sequence -- cold vs warm branch determination |
| `scripts/ctmv3-activate.sh` | `activate` | Full Phase 0-5 cold start activation pass |
| `scripts/ctmv3-warm.sh` | `warm` | Warm start: provenance diff + continuation |
| `scripts/ctmv3-architecture-map.sh` | `architecture-map` | Build or update ARCHITECTURE_MAP.md |
| `scripts/ctmv3-sovereign-init.sh` | `sovereign-init` | Initialize .sovereign/ directory and artifacts |
| `scripts/ctmv3-dot-init.sh` | `dot-init` | Initialize .github/, .claude/, .codex/ directories |
| `scripts/ctmv3-session-close.sh` | `session-close` | Close session cleanly, update PROVENANCE.md |
| `scripts/ctmv3-status.sh` | `status` | Report current boot state and signal inventory |

Example invocations:
```bash
# Boot check on current directory
bash scripts/ctmv3-boot.sh

# Full activation of a specific repo
bash scripts/ctmv3-activate.sh /path/to/repo

# Check status with JSON output
bash scripts/ctmv3-status.sh /path/to/repo --json
```

---

## OUTPUT CONTRACT

A completed CTMv3 activation pass produces eight outputs:

1. Agent can answer without asking: What are the 3 things I cannot get wrong?
2. Agent can recognize failure before it is provable: What does wrong smell like?
3. Agent knows what was already rejected: What will not be re-discovered?
4. Agent knows where complexity concentrates: Where to slow down?
5. Agent knows its entry vector: Based on task type, where to enter?
6. Agent knows the boot state: Cold entry or warm entry? Determined in < 60 seconds.
7. Agent has a traversal map: ARCHITECTURE_MAP.md answers "where is X" without a guide.
8. Codebase enforces itself: .github/, .sovereign/, AGENTS.md create structural enforcement.

If any of these eight outputs are missing, the activation pass is incomplete.

---

## ANTI-PATTERNS

- Step-by-step workflows (AGENTS.md quick reference handles that)
- UI/UX documentation
- Tutorial content (full technical depth assumed)
- Generic best practices (encode Daeron's actual decisions)
- Flat single-file skills for complex domains
- Skills that assume happy path (failure grammar mandatory)
- Ecosystem setup that requires operator intervention to activate (hooks must fire automatically)
- ARCHITECTURE_MAP that summarizes instead of navigates (summaries are for humans, maps are for agents)

---

## REFERENCE FILES

| File | Load When |
|------|-----------|
| `REFERENCES.md` | Finding the full CTMv3 cognitive doc set |
| `BOOT_PROTOCOL.md` | Any repo entry task -- always |
| `DOT_TOPOLOGY.md` | Building ecosystem artifacts, .xyz directory work |
| `ARCHITECTURE_MAP_TEMPLATE.md` | Building traversal maps |
| `TOPOLOGY.md` | Building or entering any domain |
| `FAILURE_GRAMMAR.md` | Something smells wrong, or domain is adversarial |
| `PROVENANCE.md` | Session start, lineage checks, snapshot work |
| `CONSTITUTION.md` | Dev philosophy alignment, architectural disputes |
| `AGENTS_ADDENDUM.md` | Building AGENTS.md integration, Codex onboarding |
