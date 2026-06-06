---
name: sovereign-skill-architect
description: >
  Cognitive Topology Map (CTM) v3 skill creation engine. Use this skill whenever
  Daeron asks to create a skill, build a SKILL.md, document a codebase for agent
  consumption, encode a domain for autonomous agent use, build an agent constitution,
  or integrate a codebase into the agent ecosystem (.github, .claude, .codex,
  .sovereign directories, AGENTS.md, CLAUDE.md). Also triggers on: "make a skill
  for X", "encode this codebase", "write an AGENTS.md", "build Codex context for Y",
  "document this for autonomous use", "bring the codebase alive", "set up agent
  hooks", "build ARCHITECTURE_MAP", "cold start this repo", "warm start session",
  "set up .github for this", "integrate agents into my project". This skill does NOT
  produce workflow checklists or process documents. It produces cognitive topology
  maps and executable ecosystem artifacts: ARCHITECTURE_MAP.md traversal graphs,
  .sovereign/ session state, .github/ enforcement hooks, AGENTS.md operational
  postures — all making the codebase itself a navigable, self-describing system that
  an agent can enter cold and orient immediately. Critical distinction: a CTM skill
  is a domain's topology encoded as navigable structure, not a procedure encoded as
  steps. The codebase becomes executable in the agent's hands, not explained to it.
---

# SOVEREIGN SKILL ARCHITECT — CTMv3 Cognitive Topology Map Engine

**Paradigm**: CTM (Cognitive Topology Map), not SOP (Standard Operating Procedure)  
**Version**: v3.0 — Session State Machine + Executable Ecosystem  
**Operator**: Daeron  
**Philosophy**: A skill is not a recipe. It is a domain's cognitive topology encoded as
navigable structure. A codebase with a CTM skill package is executable by any agent on cold
entry — not explained to the agent, but alive in the agent's hands.

---

## IDENTITY BLOCK

**What CTMv3 knows that CTMv2 did not:**
- How to detect cold vs. warm entry state via `.xyz` directory discovery
- How to produce ARCHITECTURE_MAP.md traversal artifacts (question-oriented navigation maps)
- How to encode `.github/`, `.claude/`, `.codex/`, `.sovereign/` as topology signals
- How to read config file spine (`pyproject.toml`, `go.mod`, `manifest.json`, etc.) as
  architectural evidence without executing them
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
- Whether the agent ecosystem integration is already present (run BOOT_PROTOCOL.md first)

---

## SEMANTIC ROUTER — Load This Document, Not That One

Classify task type before loading any sub-document. Load only what the task requires.

```
TASK TYPE → LOAD ORDER
─────────────────────────────────────────────────────────────────────

[COLD_START_REPO] — entering a codebase with no prior CTM artifacts
  → BOOT_PROTOCOL.md (run discovery) → TOPOLOGY.md → DOT_TOPOLOGY.md
  → interfaces/{lang}.md → Phase 0 full archaeology → build all artifacts

[WARM_START_REPO] — resuming a session in a CTM-encoded codebase
  → BOOT_PROTOCOL.md (run warm check) → PROVENANCE.md (check lineage + session log)
  → diff current state → continue from last logged action

[BUILD_ARCHITECTURE_MAP] — producing the traversal-map artifact for a codebase
  → ARCHITECTURE_MAP_TEMPLATE.md → TOPOLOGY.md → build ARCHITECTURE_MAP.md

[NEW_SKILL from scratch]
  → TOPOLOGY.md (anatomy) → CONSTITUTION.md (philosophy) → interfaces/{lang}.md → build

[ENCODE existing codebase]
  → BOOT_PROTOCOL.md → TOPOLOGY.md → interfaces/{lang}.md
  → examples/case_codebase_entry.md → build

[INTEGRATE_AGENT_ECOSYSTEM] — setting up .github/, .claude/, .codex/, .sovereign/
  → DOT_TOPOLOGY.md → BOOT_PROTOCOL.md → build ecosystem artifacts

[OSINT / RE / adversarial domain]
  → TOPOLOGY.md → FAILURE_GRAMMAR.md → examples/case_osint.md → build

[UPGRADE existing skill]
  → Read existing SKILL.md → TOPOLOGY.md → diff against CTMv3 standard → upgrade

[AGENTS.md / CLAUDE.md / constitution build]
  → CONSTITUTION.md → TOPOLOGY.md → AGENTS_ADDENDUM.md → wrap existing agent posture

[FAILURE / something smells wrong]
  → FAILURE_GRAMMAR.md immediately, before any other action

[SESSION START in encoded repo]
  → BOOT_PROTOCOL.md → warm check → if stale: PROVENANCE.md → TOPOLOGY.md
```

**Hard rule**: Never load all sub-documents upfront. Load conditionally.
BOOT_PROTOCOL.md is mandatory for any repo entry task. It determines the branch.
FAILURE_GRAMMAR.md loads when something smells wrong — not as a precaution but as a response.

---

## PHASE PROTOCOLS

### PRE-PHASE: Boot State Check (ALWAYS before any other phase for repo tasks)

**Load BOOT_PROTOCOL.md and run the discovery sequence before Phase 0.**

The boot check answers: is this a cold entry or a warm entry?

- Cold entry → full Phase 0–5 archaeology + artifact construction
- Warm entry → PROVENANCE.md diff + continuation from last session

See BOOT_PROTOCOL.md for the full state machine.

---

### PHASE 0: Domain Archaeology (Always First for Cold Entry)

Before writing a single line of skill, excavate the domain:

**Questions that are NOT optional:**

1. **Load-bearing concepts** — What are the 3–7 concepts everything else depends on?
   If these are misunderstood, the entire skill fails silently.

2. **Interface boundaries** — Where does this domain end? What does it hand off to,
   and what does it receive from? (Critical for wrapper pattern integration)

3. **Complexity topology** — Where does hard complexity actually concentrate?
   Not where the code is longest — where does a subtle misunderstanding cause
   cascading failure?

4. **Baked-in decisions** — What architectural choices were made upstream that a new
   agent would never know to question? These are the invisible load-bearing walls.

5. **Snapshot lineage** — What snapshot is this domain at? What was rejected to get here?
   (PROVENANCE.md if present; manifest.json hash if present)

6. **Hardware reality check** — Daeron's primary: Ryzen 5 2400G / 12GB RAM, no GPU.
   Laptop: Ryzen 5 5625U / 16GB. Any skill that encodes memory-hungry patterns without
   acknowledging this is already wrong.

7. **Config file spine** — What does the `.xyz` directory landscape look like?
   pyproject.toml, go.mod, manifest.json, AGENTS.md, CLAUDE.md, golden_paths.json —
   these are archaeological evidence, not just configuration files.
   See DOT_TOPOLOGY.md.

**Output of Phase 0**: A domain topology sketch — working map of nodes, edges, and
weight concentration. Not a document yet.

---

### PHASE 1: Topology Construction

Build `TOPOLOGY.md`. This is the cognitive map of the domain.

**Topology document anatomy:**

```markdown
## Load-Bearing Concepts
[3–7 concepts. For each: definition, why load-bearing, common misunderstanding,
 verification test]

## Interface Map
[What enters, what exits, behavioral contracts — not type signatures]

## Complexity Distribution
[DENSE / MEDIUM / THIN per component. Mermaid diagram mandatory for 4+ nodes.]

## Dependency Graph
[What depends on what. Mermaid diagram mandatory.]

## Baked-In Decisions
[Invisible load-bearing walls. Upstream decisions not in the code.]

## Anti-Concepts
[Things that look like they belong but don't. False attractors.]

## Config File Spine
[What .xyz dirs and config files exist. What they encode about architecture.]
```

**Mermaid is mandatory** for any topology with more than 4 nodes.
See STYLE.md § 2.2.

---

### PHASE 2: Failure Grammar Construction

Build `FAILURE_GRAMMAR.md`. Not an error list.
Taxonomy of what *wrong looks like before you can prove it's wrong.*

For adversarial domains: adversarial inputs are mandatory. For all domains:
pre-failure signatures and false success patterns are mandatory.

See FAILURE_GRAMMAR.md for the full taxonomy template.

---

### PHASE 3: Entry Vector Analysis

Different task types enter the domain at different topology points.
Encode this explicitly in the new skill's semantic router.

| Entry Type | Entry Point | First Doc |
|-----------|-------------|-----------|
| Cold session | Boot check | BOOT_PROTOCOL.md |
| Warm session | Provenance diff | PROVENANCE.md → TOPOLOGY.md |
| Debugging | Failure grammar | FAILURE_GRAMMAR.md |
| New module integration | Interface boundaries | TOPOLOGY.md → interfaces/{lang}.md |
| RE / reversing | Adversarial signatures | FAILURE_GRAMMAR.md → TOPOLOGY.md |
| Research / hypothesis | Load-bearing concepts | TOPOLOGY.md |
| Snapshot validation | Provenance chain | PROVENANCE.md → TOPOLOGY.md |

---

### PHASE 4: Provenance Chain

Build or update `PROVENANCE.md`.

```markdown
## Snapshot Lineage
## Architectural Decisions (Chronological)
## Rejected Alternatives (Graveyard)
## Open Questions
## Integration History
## Session Log
```

See PROVENANCE.md for the full template.

---

### PHASE 5: Ecosystem Artifact Construction

**This phase is new in CTMv3. Build the executable agent ecosystem.**

Depending on repo type and what's absent, produce:

```
[project-root]/
├── ARCHITECTURE_MAP.md   ← Traversal map (see ARCHITECTURE_MAP_TEMPLATE.md)
├── AGENTS.md             ← Operational posture for Codex / Claude Code
├── CLAUDE.md             ← Claude-specific context (if Claude Code is primary agent)
├── .github/
│   └── instructions/     ← Per-path agent context files (GitHub Copilot model)
│   └── workflows/        ← CI enforcement hooks
│   └── copilot-instructions.md ← Repo-wide agent instruction
├── .claude/
│   └── settings.json     ← Claude Code settings (permissions, env)
├── .codex/               ← Codex skill installs
│   └── skills/
└── .sovereign/           ← Sovereign session state
    ├── session_state.json
    ├── golden_paths.json  ← Seeded from workflows or built fresh
    └── PROVENANCE.md      ← Symlink or copy of skill PROVENANCE.md
```

See DOT_TOPOLOGY.md for what each artifact encodes and how to build it.
See ARCHITECTURE_MAP_TEMPLATE.md for the traversal map construction protocol.

**Assembly rules:**
- SKILL.md is the ONLY entry point. Everything else is loaded conditionally.
- ARCHITECTURE_MAP.md replaces flat README for agent navigation.
- .sovereign/ is the session continuity anchor — create it if absent.
- No circular references between sub-documents.
- CONSTITUTION.md is shared across skills — link it, never duplicate it.

---

## OUTPUT CONTRACT

A completed CTMv3 skill package produces all five CTMv2 outputs plus three new ones:

**CTMv2 outputs (still required):**
1. Agent can answer without asking: What are the 3 things I cannot get wrong?
2. Agent can recognize failure before it's provable: What does wrong smell like?
3. Agent knows what was already rejected: What won't I waste time re-discovering?
4. Agent knows where complexity concentrates: Where do I slow down?
5. Agent knows its entry vector: Based on my task type, where do I enter?

**CTMv3 additions:**
6. Agent knows the boot state: Cold entry or warm entry? Determined in < 60 seconds.
7. Agent has a traversal map: ARCHITECTURE_MAP.md answers "where is X" without a guide.
8. Codebase enforces itself: .github/, .sovereign/, AGENTS.md create structural enforcement.

If any of these eight outputs are missing, the package is incomplete.

---

## ANTI-PATTERNS — What This Skill Does NOT Produce

- ❌ Step-by-step workflows (AGENTS.md quick reference handles that)
- ❌ UI/UX documentation
- ❌ Tutorial content (full technical depth assumed)
- ❌ Generic best practices (encode Daeron's actual decisions)
- ❌ Flat single-file skills for complex domains
- ❌ Skills that assume happy path (failure grammar mandatory)
- ❌ Ecosystem setup that requires operator intervention to activate (hooks must fire automatically)
- ❌ ARCHITECTURE_MAP that summarizes instead of navigates (summaries are for humans, maps are for agents)

---

## INTEGRATION WITH AGENTS.md / CLAUDE.md

When Daeron says "build this for Codex" or "make a CLAUDE.md":

1. SKILL package → domain knowledge layer
2. AGENTS.md → operational posture layer (sovereign, execute-first, bb7 tools)
3. CONSTITUTION.md → development philosophy layer
4. STYLE.md → code standards layer

Layer hierarchy (top = highest authority):
```
AGENTS.md / CLAUDE.md  ← Who you are, how you operate, your environment
SKILL/{domain}         ← What you know about THIS domain
CONSTITUTION.md        ← How you think about development
STYLE.md               ← How you write code
```

No layer duplicates another. AGENTS.md doesn't define coding standards.
SKILL doesn't define operational posture. CONSTITUTION doesn't define tool protocols.

---

## REFERENCE FILES

| File | Load When |
|------|-----------|
| `BOOT_PROTOCOL.md` | Any repo entry task — always |
| `DOT_TOPOLOGY.md` | Building ecosystem artifacts, .xyz directory work |
| `ARCHITECTURE_MAP_TEMPLATE.md` | Building traversal maps |
| `TOPOLOGY.md` | Building or entering any domain |
| `FAILURE_GRAMMAR.md` | Something smells wrong, or domain is adversarial |
| `PROVENANCE.md` | Session start, lineage checks, snapshot work |
| `CONSTITUTION.md` | Dev philosophy alignment, architectural disputes |
| `AGENTS_ADDENDUM.md` | Building AGENTS.md integration, Codex onboarding |
| `interfaces/python.md` | Python codebase work |
| `interfaces/go.md` | Go codebase work |
| `interfaces/ada.md` | Ada codebase work |
| `examples/case_codebase_entry.md` | Encoding an existing codebase |
| `examples/case_osint.md` | OSINT or RE domain skill |
