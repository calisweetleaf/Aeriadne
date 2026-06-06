# PROVENANCE.md — Decision Log, Snapshot Lineage, Rejected Paths

**Loaded by**: SKILL.md at session start, snapshot work, lineage checks  
**Purpose**: Records the history of decisions so future agents don't re-discover
rejected paths. Also serves as the template for all CTM skill package PROVENANCE.md files.

---

## Skill Package Lineage

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-08 | Initial CTM paradigm: TOPOLOGY, FAILURE_GRAMMAR, PROVENANCE, CONSTITUTION, python.md, case_codebase_entry.md, AGENTS_ADDENDUM |
| v2.0 | 2026-03-08 | Packaged as sovereign-skill-operator.zip. First full multi-doc package. |
| v3.0 | 2026-05-11 | CTMv3: BOOT_PROTOCOL.md, DOT_TOPOLOGY.md, ARCHITECTURE_MAP_TEMPLATE.md added. TOPOLOGY.md Node 8 (config spine). FAILURE_GRAMMAR.md Category 5 (ecosystem failures). SKILL.md semantic router expanded with COLD_START_REPO, WARM_START_REPO, BUILD_ARCHITECTURE_MAP, INTEGRATE_AGENT_ECOSYSTEM task types. |

**Current version**: v3.0 (2026-05-11)

---

## Architectural Decisions (Chronological)

### Decision 1: CTM over SOP
**Date**: 2026-03-08  
**Context**: Initial design choice for skill paradigm  
**Options considered**:
1. Standard Operating Procedure (checklist) — rejected: doesn't survive refactors, produces
   agents that pattern-match steps instead of understanding domain
2. **CTM (Cognitive Topology Map) — chosen**: encodes topology invariants, survives
   implementation changes, produces agents that navigate with genuine understanding
**Implications**: All skills must encode load-bearing concepts, not steps.
**Revisit condition**: If evidence shows CTM skills are consistently too complex to load
within context window constraints. (Not currently a problem.)

### Decision 2: Multi-doc package over single SKILL.md
**Date**: 2026-03-08  
**Context**: Initial SKILL.md was growing beyond 500 lines, violating progressive disclosure  
**Options considered**:
1. Flat single file — rejected: no progressive disclosure, forces full load on every trigger
2. **Multi-doc with semantic router — chosen**: loads only what task requires
**Implications**: SKILL.md is the only entry point. All others load conditionally.

### Decision 3: CTMv3 boot protocol as formal state machine
**Date**: 2026-05-11  
**Context**: Daeron's usage pattern shows agents re-encoding topology that already exists,
because there was no protocol for detecting "has this been run here before?"
Mentat plugin and MCP server both have state machine behavior; CTM didn't.  
**Options considered**:
1. Mention warm/cold start in SKILL.md as a note — rejected: not operational, agents skip notes
2. **Separate BOOT_PROTOCOL.md as mandatory pre-phase — chosen**: formal state machine,
   explicit discovery sequence, liveness gates, cold/warm branching
**Implications**: BOOT_PROTOCOL.md loads before Phase 0 for any repo task.

### Decision 4: DOT_TOPOLOGY.md as topology encoding (not setup guide)
**Date**: 2026-05-11  
**Context**: .xyz directories (.github, .claude, .codex, .sovereign) were mentioned in
session discussions but not formally encoded as topology signals in the skill  
**Options considered**:
1. Include as a section in SKILL.md Phase 5 — rejected: Phase 5 would bloat to 200+ lines
2. Include as part of TOPOLOGY.md — rejected: dot directories are a cross-cutting concern,
   not specific to any one domain topology
3. **Separate DOT_TOPOLOGY.md — chosen**: loaded when ecosystem integration is in scope,
   encodes each directory type as a topology signal category
**Implications**: Every CTM cold start now includes a .sovereign/ initialization.

### Decision 5: ARCHITECTURE_MAP.md as a required output artifact (not a bonus)
**Date**: 2026-05-11  
**Context**: The ARCHITECTURE_MAP.md in Somnus-MCP is the single best navigational
artifact in Daeron's system. Agents entering that codebase cold orient in < 5 minutes.
Nothing in the CTMv2 skill mandated this pattern for new codebases.  
**Options considered**:
1. Recommend as optional — rejected: "optional" means it won't be built under time pressure
2. **Mandate in Phase 5 and formalize as ARCHITECTURE_MAP_TEMPLATE.md — chosen**:
   traversal map is now a required Phase 5 artifact with a formal construction protocol
**Implications**: Every CTM encoding now produces ARCHITECTURE_MAP.md.

---

## Rejected Alternatives (Graveyard)

### Rejected: Workflow checklists as skill output
**What it was**: Skills as SOPs — numbered step lists for how to do X  
**Why it looked appealing**: Immediately actionable, easy to verify execution  
**Why rejected**: Doesn't survive refactors. Produces pattern-matching not understanding.
Agents execute the list without knowing why, fail at step boundaries when reality diverges.  
**Status**: Permanently rejected.

### Rejected: Flat AGENTS.md as the entire skill
**What it was**: Putting all CTM content into a single AGENTS.md / CLAUDE.md  
**Why it looked appealing**: Single file, always-loaded, no routing complexity  
**Why rejected**: Context window economics. Everything-in-one-file means full load
every trigger. A 2000-line AGENTS.md is wasteful when only 200 lines are relevant per task.  
**Status**: Permanently rejected. AGENTS.md is the operational posture layer,
not the domain knowledge layer. They are different things.

### Rejected: Auto-generated ARCHITECTURE_MAP from code AST
**What it was**: Programmatically generate the traversal map from code analysis  
**Why it looked appealing**: Always accurate, never stale, no manual update  
**Why rejected**: AST-generated maps encode structure, not navigational questions.
They tell you what exists, not how to think about it. The question-oriented
structure of ARCHITECTURE_MAP.md is the human/agent design decision — it cannot
be automated. Line anchors can be refreshed programmatically; the question graph cannot.  
**Status**: Partial automation possible for line anchor refresh (future work). 
Full generation permanently rejected.

---

## Open Questions

| Question | Assumption Made | Impact if Wrong |
|----------|----------------|-----------------|
| Does .sovereign/ dir conflict with any existing tool? | No other tool claims .sovereign/ | Would need to rename to .somnus/ or .ctm/ |
| Should ARCHITECTURE_MAP.md live at repo root or in skill package? | Repo root — it's for agents entering the project, not for the skill | If at skill root, it serves skill-level navigation only, missing the cross-agent value |
| Should CLAUDE.md extend AGENTS.md or be standalone? | Extends AGENTS.md | If standalone, divergence risk is much higher; but some projects have no AGENTS.md |

---

## TEMPLATE: Copy and Fill for Each Skill Package

```markdown
# PROVENANCE — [Skill/Domain Name]

## Snapshot Lineage

| Version | Date | Source Project | Source Snapshot | Changes from Previous |
|---------|------|---------------|-----------------|----------------------|
| v1.0 | [date] | [project] | [snapshot tag] | Initial extraction |

**Current authoritative snapshot**: [version] — [path or git tag]  
**SHA-256 manifest hash**: [hash from manifest.json]

---

## Architectural Decisions (Chronological)

### Decision [n]: [Short title]
**Date**: [YYYY-MM-DD]  
**Context**: [What forced this decision]  
**Options considered**:
1. [Option A]: — rejected because [reason]
2. **[Option B — chosen]**: — chosen because [reason]
**Implications**: [What this constrains downstream]  
**Revisit condition**: [Under what circumstances should this be reconsidered]

---

## Rejected Alternatives (Graveyard)

### Rejected: [Name]
**What it was**: [Description]  
**Why it looked appealing**: [The seductive part]  
**Why it was rejected**: [The actual problem]  
**Status**: Permanently rejected | Deferred | Superseded by [alternative]

---

## Open Questions

| Question | Assumption Made | Impact if Wrong |
|----------|----------------|-----------------|
| [Question] | [Assumption] | [What breaks] |

---

## Integration History

| Module | Source | Integrated | I_eff | Status | Notes |
|--------|--------|-----------|-------|--------|-------|
| [module.py] | [project v.x] | [date] | [0.xx] | Active | [notes] |

---

## Session Log

| Date | Agent | Action | Topology Drift? | Next Recommended Action |
|------|-------|--------|----------------|------------------------|
| [date] | [agent] | [action] | yes/no | [action] |
```

---

## Why Provenance Is Non-Optional

The re-discovery loop: agent encounters a problem, doesn't know domain history,
proposes Solution A. Solution A was tried 3 months ago, failed for a subtle reason
that took 3 days to discover, explicitly rejected. Agent spends 3 days re-discovering
the same failure.

In Daeron's system with multiple AI collaborators (Codex, Claude, Claude Code, Kimi, Gemini)
operating across multiple sessions: the re-discovery loop is not hypothetical.
PROVENANCE.md is the collective memory of the system — independent of any agent's
context window, independent of any session's continuity.

An agent that takes a significant action without logging it has violated the
traceability principle regardless of whether the action was technically correct.
