---
name: ctmv3-workspace-activator
description: >
  CTMv3 workspace activation cognitive layer. Load when entering any unfamiliar codebase,
  when asked to encode or document a repo for agents, when doing cold or warm start work,
  when setting up .github/.claude/.codex/.sovereign directories, or when building
  ARCHITECTURE_MAP.md, AGENTS.md, TOPOLOGY.md, or PROVENANCE.md.
  Do NOT load for ordinary coding tasks in a repo that is already CTM-activated.
disable-model-invocation: false
---
# CTMv3 Workspace Activation — Cognitive Layer

Claude Code installation. This file is the semantic router. Full sub-documents are at:
- `../../templates/BOOT_PROTOCOL.md`
- `../../templates/DOT_TOPOLOGY.md`
- `../../templates/TOPOLOGY.md` (template)
- `../../templates/ARCHITECTURE_MAP_TEMPLATE.md`
- `../../templates/FAILURE_GRAMMAR.md` (template)
- `../../templates/PROVENANCE.md` (template)

At install time these paths resolve relative to this skill's directory. If the plugin is
installed via `claude plugin install`, the templates directory is at the plugin root.

---

**Paradigm**: CTM (Cognitive Topology Map), not SOP (Standard Operating Procedure)
**Version**: v3.0
**Operator**: Daeron
**Philosophy**: A skill is not a recipe. A codebase with a CTM skill package is executable
by any agent on cold entry — not explained to the agent, but alive in the agent's hands.

---

## IDENTITY BLOCK

**What CTMv3 knows that CTMv2 did not:**
- How to detect cold vs. warm entry state via .xyz directory discovery
- How to produce ARCHITECTURE_MAP.md traversal artifacts (question-oriented navigation maps)
- How to encode .github/, .claude/, .codex/, .sovereign/ as topology signals
- How to read config file spine (pyproject.toml, go.mod, manifest.json) as architectural
  evidence without executing them
- How to set up agent ecosystem hooks that enforce topology contracts at the OS level
- The session state machine: `if not run → full archaeology; if run → diff and continue`

**What this skill still knows (CTMv2 baseline):**
- Expert cognition vs. checklist simulation
- CTM package anatomy (topology, failure grammar, entry vectors, provenance)
- Daeron's recursive production system and encoding codebases within it
- Python, Go, Ada topology patterns
- Failure grammar for adversarial/OSINT domains
- Adversarially-aware skill construction

**What this skill explicitly does NOT know:**
- Your specific codebase (read it, don't assume it)
- Which modules are currently production-stable (check manifest.json or ask)
- Current snapshot state (check SNAPSHOT.md or manifest.json if present)
- What Daeron has already decided is wrong (check PROVENANCE.md — if absent, that's data)
- Whether the agent ecosystem integration is already present (run boot check first)

---

## SEMANTIC ROUTER — Load This Document, Not That One

Classify task type before loading any sub-document. Load only what the task requires.

```
TASK TYPE → LOAD ORDER
─────────────────────────────────────────────────────────────────────

[COLD_START_REPO] — entering a codebase with no prior CTM artifacts
  → BOOT_PROTOCOL.md (run discovery) → TOPOLOGY.md → DOT_TOPOLOGY.md
  → Phase 0 full archaeology → build all artifacts
  → In Claude Code: invoke /ctmv3:activate

[WARM_START_REPO] — resuming a session in a CTM-encoded codebase
  → BOOT_PROTOCOL.md (run warm check) → PROVENANCE.md (check lineage + session log)
  → diff current state → continue from last logged action
  → In Claude Code: invoke /ctmv3:warm

[BUILD_ARCHITECTURE_MAP] — producing the traversal-map artifact for a codebase
  → ARCHITECTURE_MAP_TEMPLATE.md → TOPOLOGY.md → build ARCHITECTURE_MAP.md
  → In Claude Code: invoke /ctmv3:architecture-map

[NEW_SKILL from scratch]
  → TOPOLOGY.md (anatomy) → build

[ENCODE existing codebase]
  → BOOT_PROTOCOL.md → TOPOLOGY.md
  → In Claude Code: invoke /ctmv3:activate

[INTEGRATE_AGENT_ECOSYSTEM] — setting up .github/, .claude/, .codex/, .sovereign/
  → DOT_TOPOLOGY.md → BOOT_PROTOCOL.md → build ecosystem artifacts
  → In Claude Code: invoke /ctmv3:dot-init

[OSINT / RE / adversarial domain]
  → TOPOLOGY.md → FAILURE_GRAMMAR.md → build

[UPGRADE existing skill]
  → Read existing SKILL.md → TOPOLOGY.md → diff against CTMv3 standard → upgrade

[AGENTS.md / CLAUDE.md / constitution build]
  → TOPOLOGY.md → AGENTS_ADDENDUM.md → wrap existing agent posture

[FAILURE / something smells wrong]
  → FAILURE_GRAMMAR.md immediately, before any other action

[SESSION START in encoded repo]
  → BOOT_PROTOCOL.md → warm check → if stale: PROVENANCE.md → TOPOLOGY.md
  → In Claude Code: invoke /ctmv3:boot
```

**Hard rule**: Never load all sub-documents upfront. Load conditionally.
BOOT_PROTOCOL.md is mandatory for any repo entry task. It determines the branch.
FAILURE_GRAMMAR.md loads when something smells wrong — not as a precaution but as a response.

---

## PHASE PROTOCOLS

### PRE-PHASE: Boot State Check (ALWAYS before any other phase for repo tasks)

Load BOOT_PROTOCOL.md and run the discovery sequence before Phase 0.

In Claude Code: run `python3 -m ctmv3 boot --json` or invoke /ctmv3:boot.

The boot check answers: is this a cold entry or a warm entry?
- Cold entry → full Phase 0-5 archaeology + artifact construction
- Warm entry → PROVENANCE.md diff + continuation from last session

---

### PHASE 0: Domain Archaeology (Always First for Cold Entry)

Before writing a single line of skill, excavate the domain.

**Questions that are NOT optional:**

1. **Load-bearing concepts** — What are the 3-7 concepts everything else depends on?
2. **Interface boundaries** — Where does this domain end?
3. **Complexity topology** — Where does hard complexity actually concentrate?
4. **Baked-in decisions** — What architectural choices were made upstream?
5. **Snapshot lineage** — What snapshot is this domain at?
6. **Hardware reality check** — Daeron's primary: Ryzen 5 2400G / 12GB RAM, no GPU.
7. **Config file spine** — What does the .xyz directory landscape look like?

---

### PHASE 1: Topology Construction

Build TOPOLOGY.md. Mandatory sections:
- Load-Bearing Concepts
- Interface Map
- Complexity Distribution (Mermaid mandatory for 4+ nodes)
- Dependency Graph (Mermaid mandatory)
- Baked-In Decisions
- Anti-Concepts
- Config File Spine

---

### PHASE 2: Failure Grammar Construction

Build FAILURE_GRAMMAR.md. Taxonomy of what wrong looks like before you can prove it.
Mandatory: pre-failure signatures, false success patterns.
Adversarial domains: adversarial inputs also mandatory.

---

### PHASE 3: Entry Vector Analysis

Encode the semantic router in the new skill. Table of task type → entry point → first doc.

---

### PHASE 4: Provenance Chain

Build PROVENANCE.md:
- Snapshot Lineage
- Architectural Decisions (Chronological)
- Rejected Alternatives (Graveyard)
- Open Questions
- Integration History
- Session Log

---

### PHASE 5: Ecosystem Artifact Construction

Build in order (order is load-bearing — do not invert):

1. ARCHITECTURE_MAP.md
2. .sovereign/ (after topology artifacts exist)
3. AGENTS.md
4. CLAUDE.md + .claude/settings.json
5. .github/copilot-instructions.md
6. .github/instructions/ per-path files (DENSE nodes only)
7. .github/workflows/ enforcement gates
8. PROVENANCE.md Session Log update

---

## OUTPUT CONTRACT

Eight outputs. All required. Package is incomplete if any are missing.

1. Agent can answer without asking: What are the 3 things I cannot get wrong?
2. Agent can recognize failure before it's provable: What does wrong smell like?
3. Agent knows what was already rejected: What won't I waste time re-discovering?
4. Agent knows where complexity concentrates: Where do I slow down?
5. Agent knows its entry vector: Based on my task type, where do I enter?
6. Agent knows the boot state: Cold entry or warm entry? Determined in < 60 seconds.
7. Agent has a traversal map: ARCHITECTURE_MAP.md answers "where is X" without a guide.
8. Codebase enforces itself: .github/, .sovereign/, AGENTS.md create structural enforcement.

---

## ANTI-PATTERNS

- Step-by-step workflows (AGENTS.md quick reference handles that)
- Generic best practices (encode Daeron's actual decisions)
- Flat single-file skills for complex domains
- Skills that assume happy path (failure grammar mandatory)
- Ecosystem setup that requires operator intervention to activate
- ARCHITECTURE_MAP that summarizes instead of navigates
- .sovereign/ initialized before topology artifacts exist

---

## REFERENCE FILES

| File | Load When |
|------|-----------|
| BOOT_PROTOCOL.md | Any repo entry task — always |
| DOT_TOPOLOGY.md | Building ecosystem artifacts, .xyz directory work |
| ARCHITECTURE_MAP_TEMPLATE.md | Building traversal maps |
| TOPOLOGY.md (template) | Building or entering any domain |
| FAILURE_GRAMMAR.md (template) | Something smells wrong, or adversarial domain |
| PROVENANCE.md (template) | Session start, lineage checks, snapshot work |
