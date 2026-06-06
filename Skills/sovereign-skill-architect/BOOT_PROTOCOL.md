# BOOT_PROTOCOL.md — Session State Machine: Cold vs Warm Entry

**Loaded by**: SKILL.md for any repo entry, encoding, or warm-start task  
**Purpose**: Determine in < 60 seconds whether this is a cold or warm entry,
then branch execution correctly. The state machine that makes
"if not run → run; if run → continue" a formal protocol rather than operator memory.

---

## The Core Problem This Solves

Without a boot protocol, every agent session starts from zero. The agent reads the
codebase as if it has never been touched, re-discovers topology that was already encoded,
proposes paths that were already rejected, and re-establishes context that PROVENANCE.md
already has. This is the re-discovery loop — one of the primary sources of wasted compute
in multi-agent, multi-session collaborative development.

The boot protocol eliminates this. It answers: "What do I already know, and what do I
need to learn?" before any work begins.

---

## STATE MACHINE DIAGRAM

```
AGENT ENTERS REPO / SESSION BEGINS
            │
            ▼
    ┌──────────────────────┐
    │  DISCOVERY SEQUENCE  │  (< 60 seconds, read-only, no writes)
    │  (see Section 2)     │
    └──────────┬───────────┘
               │
       ┌───────┴────────┐
       │                │
   ARTIFACTS        NO ARTIFACTS
   FOUND            FOUND
       │                │
       ▼                ▼
  WARM CHECK         COLD START
  (Section 3)        (Section 4)
       │
  ┌────┴──────────┐
  │               │
VALID           STALE /
WARM STATE      INCOMPLETE
  │               │
  ▼               ▼
CONTINUE        PARTIAL
(Section 3.3)   ARCHAEOLOGY
                (Section 4,
                targeted)
```

---

## Section 1: What Counts as a CTM Artifact?

The following files/directories are CTM presence signals.
Their presence, absence, and content determine the boot branch.

```
TIER 1 — Strong signals (any one = CTM has been run here)
  .sovereign/                 ← sovereign session state directory
  ARCHITECTURE_MAP.md         ← traversal map artifact
  .claude/CLAUDE.md           ← Claude-specific context
  AGENTS.md                   ← agent operational posture

TIER 2 — Supporting signals (indicate partial CTM or related tooling)
  .github/copilot-instructions.md
  .codex/skills/
  PROVENANCE.md (at repo root, not just in skill package)
  manifest.json               ← Somnus snapshot marker
  golden_paths.json           ← exoskeleton golden paths at repo root

TIER 3 — Config spine signals (always present in real projects, read for archaeology)
  pyproject.toml / setup.py / setup.cfg
  go.mod / go.sum
  Cargo.toml
  package.json
  *.toml / *.yaml / *.json at repo root
  .env.example (signals env var requirements without exposing secrets)
```

---

## Section 2: Discovery Sequence (Always First)

Run this read-only scan before any action. Do not write anything during discovery.

**Step 1 — Root scan** (list top-level files and directories):
```bash
ls -la {project_root}/
```
Target: identify Tier 1, 2, 3 signals. Build the signal inventory.

**Step 2 — .xyz directory inventory**:
```bash
ls -la {project_root}/.github/ 2>/dev/null || echo "absent"
ls -la {project_root}/.claude/ 2>/dev/null || echo "absent"
ls -la {project_root}/.codex/ 2>/dev/null || echo "absent"
ls -la {project_root}/.sovereign/ 2>/dev/null || echo "absent"
```

**Step 3 — Config spine read**:
Read (do not execute) any Tier 3 files present. Extract:
- Declared dependencies → what modules are in play
- Entry points → what is the main execution surface
- Tool configuration → what quality gates exist (pytest, mypy, ruff, etc.)

**Step 4 — AGENTS.md / CLAUDE.md presence check**:
If present, read them. They may already encode the operational posture
this session was going to build. Do not duplicate what already exists.

**Step 5 — PROVENANCE.md check** (at repo root or .sovereign/):
If present, read the Session Log section. What was the last action?
What was the snapshot at last encoding?

**Step 6 — manifest.json check**:
If present, this is a Somnus snapshot-locked project. The manifest hash
is ground truth for what is production-stable. Do not assume files outside
the manifest are production-stable.

**Output**: Signal inventory:
```
TIER_1_SIGNALS: [list what was found]
TIER_2_SIGNALS: [list what was found]
TIER_3_SIGNALS: [list what was found]
PROVENANCE_PRESENT: yes/no
MANIFEST_PRESENT: yes/no
LAST_SESSION: [date + last action, or "none"]
BRANCH: COLD_START | WARM_START | PARTIAL
```

---

## Section 3: Warm Start Protocol

**Trigger**: At least one Tier 1 signal present, PROVENANCE.md readable, Session Log
has a recent entry (< 30 days).

### 3.1 Warm Validity Check

Ask three questions:
1. **Topology still valid?** — Has significant new code been added since last encoding?
   Check: git log since PROVENANCE.md Session Log timestamp (if git available), or
   check manifest.json hash against current file hashes.
2. **Provenance coherent?** — Does the Session Log's last action match the current
   state of AGENTS.md and ARCHITECTURE_MAP.md?
3. **No rejected path in play?** — Does the current task match anything in
   PROVENANCE.md's Rejected Alternatives (Graveyard)?

If all three pass → proceed to 3.3 (Continue).
If any fail → proceed to Partial Archaeology (3.2).

### 3.2 Partial Archaeology (Warm but Stale)

Do not rebuild from scratch. Target the delta:
- What changed since last encoding?
- Which TOPOLOGY.md sections are stale?
- Does ARCHITECTURE_MAP.md need a new branch or node?

Update only the affected documents. Log the delta in PROVENANCE.md Session Log.

### 3.3 Warm Continue Protocol

```
□ Read PROVENANCE.md Session Log → confirm last state
□ Verify topology not drifted (see 3.1)
□ Load TOPOLOGY.md → identify relevant section for current task
□ Proceed with task per SKILL.md semantic router
□ After substantive work: update PROVENANCE.md Session Log
□ bb7_exo_reflect (if bb7 session active)
```

---

## Section 4: Cold Start Protocol

**Trigger**: No Tier 1 signals present, or PROVENANCE.md absent/unreadable.

Cold start is full Phase 0–5 archaeology. No shortcuts.

### 4.1 Cold Start Sequence

```
□ Run discovery sequence (Section 2) — build signal inventory
□ Read all Tier 3 config spine files → extract dependency + entry point map
□ Phase 0: Domain archaeology (SKILL.md Phase 0 questions, all 7)
□ Phase 1: Build TOPOLOGY.md
□ Phase 2: Build FAILURE_GRAMMAR.md (at minimum: pre-failure signatures)
□ Phase 3: Entry vector analysis → encode in new skill's semantic router
□ Phase 4: Seed PROVENANCE.md with initial snapshot lineage
□ Phase 5: Build ecosystem artifacts
     □ ARCHITECTURE_MAP.md (see ARCHITECTURE_MAP_TEMPLATE.md)
     □ .sovereign/session_state.json (initialize)
     □ AGENTS.md if absent (see AGENTS_ADDENDUM.md)
     □ CLAUDE.md if Claude Code is primary agent
     □ .github/ hooks if enforcement gates needed
     □ golden_paths.json seeded if bb7 system present
```

### 4.2 Cold Start Ordering — Why This Order

1. **Config spine first** — before reading any Python/Go/Ada file, read the config.
   pyproject.toml tells you the module structure. go.mod tells you the import graph.
   These are the skeleton. Source code is the flesh. Read skeleton first.

2. **TOPOLOGY.md before ARCHITECTURE_MAP.md** — the traversal map comes from the topology,
   not the other way around. Don't write the map until you know the territory.

3. **AGENTS.md before .github/ hooks** — the agent posture defines what the hooks enforce.
   Hook-first is enforcement without definition.

4. **.sovereign/ last** — session state anchors to the completed artifacts.
   Initializing it before the artifacts exist creates a stale anchor.

### 4.3 Cold Start Minimum Viable Output

If time/context is constrained, this is the minimum that constitutes a meaningful cold start:
1. TOPOLOGY.md with at least Load-Bearing Concepts and Complexity Distribution
2. PROVENANCE.md initialized with snapshot lineage and first session log
3. ARCHITECTURE_MAP.md with ROOT node and at least 3 branches

Everything else can be added in subsequent warm sessions.

---

## Section 5: Session Close Protocol

Every CTM-active session must close cleanly. Agents that don't close sessions create
stale state that corrupts the next agent's warm start.

```
□ Update PROVENANCE.md Session Log:
    Date | Agent | Last action | Topology drift? | Next recommended action
□ If topology drifted: update TOPOLOGY.md affected sections
□ If new path was rejected: log in PROVENANCE.md Graveyard
□ If bb7 session: bb7_exo_reflect with plan_id + intent
□ If .sovereign/ present: update session_state.json with:
    last_agent, timestamp, last_action, topology_hash, open_tasks
```

---

## Section 6: Boot Protocol Failure Modes

**Failure mode 1: Artifact present but wrong** — AGENTS.md exists but was written for a
different codebase or is copy-pasted boilerplate. Symptom: AGENTS.md references modules
that don't exist in this repo. Recovery: read AGENTS.md first, diff against actual
repo structure, rebuild affected sections only.

**Failure mode 2: PROVENANCE.md exists but Session Log is empty** — someone initialized
the file but never logged a session. Treat as cold start: topology is unverified.

**Failure mode 3: manifest.json hash mismatch** — current files don't match the manifest
hash. This means code changed after the last snapshot. Do not treat prior topology as
ground truth. Run targeted archaeology on changed files before continuing.

**Failure mode 4: .sovereign/ present but session_state.json is malformed or empty** —
treat as partial cold start. Do not attempt to parse malformed state; seed fresh.

**Failure mode 5: Multiple AGENTS.md files at different directory levels** — the operative
AGENTS.md is the one closest to the project root that applies to the current task path.
Do not merge multiple AGENTS.md files; they may have conflicting authority.
