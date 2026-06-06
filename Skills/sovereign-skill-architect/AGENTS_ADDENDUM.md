# CODEX SKILL ARCHITECTURE — Addendum to AGENTS.md

## How to Integrate This Into Your AGENTS.md

This section is designed to be inserted into AGENTS.md as a new top-level section:
`## Skill Architecture — CTM Knowledge Layer`

Place it after `## Capabilities & Tools` and before `## Identity & Relationship with Daeron`.

---

## Skill Architecture — CTM Knowledge Layer

### What Skills Are (and Are Not)

Skills are **Cognitive Topology Maps** — navigable domain structure that encodes:
- Load-bearing concepts (what you absolutely cannot get wrong)
- Failure grammar (what wrong looks like before you can prove it)
- Entry vectors (how different task types navigate the domain differently)
- Provenance chains (what was rejected and why)

Skills are **NOT** procedure checklists. They do not tell you what to do step by step. They give you the topology of a domain so you can navigate it with genuine understanding rather than pattern-matching against a recipe.

### The Layer Hierarchy

When operating in this environment, the following authority layers govern:

```
AGENTS.md               ← Who you are, operational posture, tools, environment
SKILL/{domain}/         ← What you know about a specific domain
CONSTITUTION.md         ← How you think about development (recursive production philosophy)
STYLE.md                ← How you write code (naming, typing, docstrings, Mermaid)
```

No layer duplicates another. AGENTS.md doesn't define coding standards. SKILL doesn't define operational posture. CONSTITUTION doesn't define tool protocols.

### Skill Package Structure

```
~/.codex/skills/
└── {skill-name}/
    ├── SKILL.md              ← Entry point and semantic router (read first, always)
    ├── TOPOLOGY.md           ← Domain topology: load-bearing concepts, interface map
    ├── FAILURE_GRAMMAR.md    ← Failure taxonomy, adversarial signatures
    ├── PROVENANCE.md         ← Decision log, rejected paths, snapshot lineage
    ├── CONSTITUTION.md       ← Symlink to shared development philosophy
    ├── interfaces/
    │   ├── python.md
    │   ├── go.md
    │   └── ada.md
    └── examples/
        ├── case_success.md
        └── case_recovery.md
```

### How to Enter a Skill

1. Read `SKILL.md` first. Always.
2. The semantic router in `SKILL.md` tells you which sub-documents to load based on your task type.
3. Do NOT load all sub-documents upfront. Load conditionally per the router.
4. Update `PROVENANCE.md` after any significant action (per traceability doctrine).

### Semantic Router Quick Reference

```
Task type                    → First doc after SKILL.md
─────────────────────────────────────────────────────
Creating new skill           → TOPOLOGY.md
Encoding existing codebase   → TOPOLOGY.md → interfaces/{lang}.md
OSINT / RE / adversarial     → FAILURE_GRAMMAR.md → TOPOLOGY.md
Something smells wrong       → FAILURE_GRAMMAR.md immediately
Upgrade existing skill       → Read existing → TOPOLOGY.md → diff
AGENTS.md / constitution     → CONSTITUTION.md → TOPOLOGY.md
Starting new session         → PROVENANCE.md (check lineage)
After significant action     → PROVENANCE.md (log it)
```

### Before Every Skill-Guided Task

```
□ Read SKILL.md → identify task type → follow semantic router
□ Check PROVENANCE.md — is there a rejected path that matches your approach?
□ Check FAILURE_GRAMMAR.md if domain is adversarial or something already smells wrong
□ After substantive work: log to PROVENANCE.md
```

### Creating a New Skill (Using the Skill Architect)

When Daeron says "make a skill for X" or "encode this codebase":

1. Load `sovereign-skill-architect/SKILL.md`
2. Follow the semantic router for task type [NEW_SKILL] or [ENCODE codebase]
3. Run Phase 0 (Domain Archaeology) before writing anything
4. Build TOPOLOGY.md first — this is the cognitive map, everything else follows from it
5. Build FAILURE_GRAMMAR.md second — encode what wrong looks like before you write the happy path
6. Build the rest of the package
7. Produce the full package as files in `~/.codex/skills/{skill-name}/`

### Skill Versioning and Snapshot Integration

Skill packages are version-locked to the snapshot lineage they encode:

- `PROVENANCE.md` records which project snapshot the skill was extracted from
- When a new snapshot is taken, the skill package should be reviewed and updated if topology changed
- Skill package version does NOT need to match project snapshot version — but PROVENANCE.md must link them

### Current Installed Skills

| Skill | Domain | Snapshot | Last Updated |
|-------|--------|----------|-------------|
| sovereign-skill-architect | Skill creation (CTM paradigm) | - | 2026-03-08 |
| [add as installed] | | | |

---

## bb7 Session Integration for Skill Work

When working within a skill-guided task, integrate bb7 tool calls:

**Session bootstrap for skill work:**
```
□ bb7_exo_bootstrap → initialize exoskeleton
□ bb7_memory_intelligent_search → check for relevant past skill sessions
□ Read SKILL.md (relevant skill) → load per semantic router
□ bb7_start_session / bb7_resume_session → begin tracked session
□ bb7_update_focus → set focus to current skill task
```

**During skill-guided work:**
```
□ bb7_capture_insight → when topology reveals something non-obvious
□ bb7_log_event → when a significant integration decision is made
□ Update PROVENANCE.md → when a path is rejected (don't just log, document)
```

**After skill work:**
```
□ bb7_exo_reflect → mandatory, non-optional (per SKILL.md boot protocol)
□ bb7_pause_session → with summary
□ bb7_memory_store → critical insights from this session
□ PROVENANCE.md updated → new session logged
```

---

## CTMv3 Additions to AGENTS.md

### Boot State Machine Integration

Every CTM-active agent session in an encoded repo follows this boot sequence.
Add this to AGENTS.md under `## Session Bootstrap`:

```
CTM BOOT SEQUENCE (mandatory for every session start)
──────────────────────────────────────────────────────
□ Read SKILL.md → identify task type
□ Run BOOT_PROTOCOL.md discovery sequence (< 60 seconds, read-only)
□ Branch:
    COLD_START → Phase 0–5 full archaeology
    WARM_START → PROVENANCE.md Session Log diff → continue
□ If bb7 active: bb7_exo_bootstrap before any routing
□ If .sovereign/ absent: create it after TOPOLOGY.md is complete
```

### Ecosystem Artifact Maintenance (New Standing Instruction)

Add this to AGENTS.md under `## Standing Instructions`:

```
ECOSYSTEM ARTIFACT MAINTENANCE
After any session that changes architecture, modules, or entry points:
□ Check ARCHITECTURE_MAP.md line anchors for the changed files
□ Update .sovereign/topology_fingerprint.txt
□ Log in PROVENANCE.md Session Log
□ If .github/ enforcement hooks exist: verify they still match current topology
```

### Current Installed Skills (Updated Format)

| Skill | Domain | CTM Version | Snapshot | Last Updated |
|-------|--------|-------------|----------|-------------|
| sovereign-skill-architect | Skill creation (CTM paradigm) | v3.0 | — | 2026-05-11 |
| [add as installed] | | | | |

### New Task Type Quick Reference (CTMv3)

```
"bring this codebase alive"     → COLD_START_REPO + Phase 5 ecosystem build
"warm start session"            → WARM_START_REPO → BOOT_PROTOCOL §3
"build architecture map"        → BUILD_ARCHITECTURE_MAP → ARCHITECTURE_MAP_TEMPLATE.md
"set up agent hooks"            → INTEGRATE_AGENT_ECOSYSTEM → DOT_TOPOLOGY.md
"set up .github for this"       → DOT_TOPOLOGY.md §.github + TOPOLOGY.md complete first
"install this skill for Codex"  → output to .codex/skills/{skill-name}/
"cold entry this repo"          → BOOT_PROTOCOL §4 full cold start
```
