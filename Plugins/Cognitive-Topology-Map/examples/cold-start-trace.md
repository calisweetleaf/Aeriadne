# examples/cold-start-trace.md — Cold-Start Activation Trace

**Scenario**: Running `python -m ctmv3 activate --project-root /path/to/hypothetical/repo` on a fresh Python+TypeScript web service with no prior CTMv3 artifacts.
**Engine version**: CTMv3 v1.1.0
**Date of trace**: 2026-05-23
**Purpose**: Walk an operator or agent through every step of a cold-start activation so they know exactly what the engine does, in what order, and why.

All file paths and content shown below are specific to the hypothetical repo. The engine behavior is exact — derived by reading the actual engine source at `core/ctmv3/core/`.

---

## Pre-State: The Hypothetical Repository

Before activation, the repo is a bare Python/TypeScript web service:

```
/path/to/hypothetical/repo/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          Flask route handlers
│   │   └── models.py          SQLAlchemy models
│   ├── services/
│   │   ├── auth.py
│   │   └── data_pipeline.py
│   └── __init__.py
├── tests/
│   ├── test_routes.py
│   └── test_pipeline.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── api/client.ts
│   └── package.json           TypeScript/React frontend
├── requirements.txt           Python dependencies (Flask, SQLAlchemy, etc.)
├── pyproject.toml             [project] name = "webservice" (Python packaging)
├── package.json               Root package.json for monorepo tooling
├── .env.example               DATABASE_URL, SECRET_KEY, etc.
└── README.md
```

**CTM presence signals**: None. No `.sovereign/`, no `AGENTS.md`, no `ARCHITECTURE_MAP.md`, no `CLAUDE.md`, no `PROVENANCE.md`. This is a clean cold start.

---

## The Command Invoked

```bash
python3 -m ctmv3 activate --project-root /path/to/hypothetical/repo
```

This calls `cli.py:cmd_activate()` (line 96) which immediately delegates to `activate.py:run()` (line 49).

---

## Phase 0: Boot Discovery (`boot.py:discover()`)

**Source**: `core/ctmv3/core/boot.py`, function `discover()`, lines 117-213.

The engine runs a read-only scan of the repo. No writes occur in this phase.

### Step 1-2: Tier 1 and Tier 2 signal scan

The engine checks each path in TIER1_PATHS (boot.py line 47-52) and TIER2_PATHS (lines 54-60):

```
Checking .sovereign              -> ABSENT
Checking ARCHITECTURE_MAP.md    -> ABSENT
Checking .claude/CLAUDE.md      -> ABSENT
Checking AGENTS.md              -> ABSENT

Checking .github/copilot-instructions.md -> ABSENT
Checking .codex/skills          -> ABSENT
Checking PROVENANCE.md          -> ABSENT
Checking manifest.json          -> ABSENT
Checking golden_paths.json      -> ABSENT
```

### Step 3: Config spine scan (Tier 3)

The engine checks each path in TIER3_PATHS (boot.py lines 62-71):

```
Checking pyproject.toml  -> PRESENT  (Python packaging)
Checking setup.py        -> ABSENT
Checking setup.cfg       -> ABSENT
Checking go.mod          -> ABSENT
Checking go.sum          -> ABSENT
Checking Cargo.toml      -> ABSENT
Checking package.json    -> PRESENT  (Node/TypeScript tooling)
Checking .env.example    -> PRESENT
```

### Steps 4-7: PROVENANCE.md, manifest.json, session_state.json

```
PROVENANCE.md:         ABSENT
manifest.json:         ABSENT
.sovereign/session_state.json: ABSENT (no .sovereign/ dir)
```

### Signal Inventory Output

```json
{
  "project_root": "/path/to/hypothetical/repo",
  "tier1_signals": [],
  "tier2_signals": [],
  "tier3_signals": ["pyproject.toml", "package.json", ".env.example"],
  "provenance_present": false,
  "manifest_present": false,
  "last_session": null,
  "branch": "COLD_START",
  "config_spine": {
    "pyproject.toml": true,
    "setup.py": false,
    "setup.cfg": false,
    "go.mod": false,
    "go.sum": false,
    "Cargo.toml": false,
    "package.json": true,
    ".env.example": true
  },
  "session_state_valid": false,
  "session_timestamp": null
}
```

**Classification**: `classify_branch()` (boot.py lines 300-321) sees no Tier 1 signals → returns `"COLD_START"`.

### Guard check (activate.py lines 93-104)

Branch is COLD_START. No protected files exist. No conflict. Execution continues.

### Language detection (activate.py:_detect_language(), lines 256-277)

Config spine shows pyproject.toml=True and package.json=True:

```
found: ["python", "javascript"]
→ language = "mixed (python, javascript)"
```

### Project name inference (architecture_map.py:_infer_project_name(), lines 89-122)

Priority chain:
1. TOPOLOGY.md H1: ABSENT
2. pyproject.toml [project].name: parses line `name = "webservice"` → returns `"webservice"`

**Project name**: `"webservice"`

---

## Phase 1: TOPOLOGY.md scaffolding

**Source**: `activate.py` lines 129-134; `templates.py:render_topology()`; template at `core/ctmv3/core/templates/TOPOLOGY.md.template`

The engine calls:
```python
tmpl.render_topology(
    "webservice",
    "2026-05-23",
    "mixed (python, javascript)",
    HAS_PYPROJECT="yes",
    HAS_GOMOD="no",
    HAS_CARGO="no",
    HAS_PACKAGEJSON="yes",
    HAS_MANIFEST="no",
    HAS_AGENTS="no",
    HAS_CLAUDE="no",
    HAS_SOVEREIGN="no",
    HAS_GITHUB="no",
)
```

**File written**: `/path/to/hypothetical/repo/TOPOLOGY.md`

**Content** (relevant sections shown):

```markdown
# TOPOLOGY — webservice

**Snapshot**: v1.0 — 2026-05-23
**Language**: mixed (python, javascript)
**Complexity**: UNKNOWN — fill after archaeology

---

## Load-Bearing Concepts

[TODO: Identify 3-7 concepts whose misunderstanding causes cascading failures.
...

## Config File Spine

| File | Present | What It Encodes |
|------|---------|-----------------|
| pyproject.toml | yes | [dependencies, entry points, tool config] |
| go.mod | no | [module path, Go version, require block] |
| Cargo.toml | no | [features, binary entry points, workspace] |
| package.json | yes | [scripts, dependencies, main entry] |
| manifest.json | no | [snapshot version, hash, production file set] |
| AGENTS.md | no | [agent posture, last encoding summary] |
| CLAUDE.md | no | [Claude Code session history, operational constraints] |
| .sovereign/ | no | [warm start validity, last session timestamp] |
| .github/ | no | [CI enforcement, agent context files] |
```

**Status recorded**: `TOPOLOGY.md -> "created"`

---

## Phase 2: FAILURE_GRAMMAR.md scaffolding

**Source**: `activate.py` lines 137-140; `templates.py:render_failure_grammar()`

**File written**: `/path/to/hypothetical/repo/FAILURE_GRAMMAR.md`

Content is the FAILURE_GRAMMAR template rendered with PROJECT_NAME="webservice" and TODAY="2026-05-23". The template provides the taxonomy structure (Pre-Failure Signatures, False Success Patterns, Pre-Failure Countermeasures) with `[TODO: ...]` markers for the operator/agent to fill with domain-specific content.

**Status recorded**: `FAILURE_GRAMMAR.md -> "created"`

---

## Phase 3: PROVENANCE.md scaffolding

**Source**: `activate.py` lines 143-148; `templates.py:render_provenance()`

**File written**: `/path/to/hypothetical/repo/PROVENANCE.md`

Content rendered from PROVENANCE.md.template with the initial Session Log row pre-filled:

```markdown
# PROVENANCE — webservice

...

## Session Log

| Date | Agent | Action | Topology Drift? | Next Recommended Action |
|------|-------|--------|----------------|------------------------|
| 2026-05-23 | CTMv3 Engine | Initial activation — scaffolded CTMv3 artifacts | no | Fill TOPOLOGY.md LBCs and ARCHITECTURE_MAP.md branches |
```

This is the first row in the Session Log. All subsequent session closes will append rows here via `sovereign.py:update_session_log()`.

**Status recorded**: `PROVENANCE.md -> "created"`

---

## Phase 4: ARCHITECTURE_MAP.md scaffolding

**Source**: `activate.py` lines 151-155; `templates.py:render_architecture_map()`

**File written**: `/path/to/hypothetical/repo/ARCHITECTURE_MAP.md`

Content is the ARCHITECTURE_MAP template rendered with PROJECT_NAME="webservice". The template provides the traversal map skeleton (ROOT node, Branch A, Branch B, Quick Reference) with `[TODO: ...]` markers that the agent fills after reading the codebase.

**Status recorded**: `ARCHITECTURE_MAP.md -> "created"`

---

## Phase 5a: AGENTS.md scaffolding

**Source**: `activate.py` lines 163-166; `templates.py:render_agents_md()`

**File written**: `/path/to/hypothetical/repo/AGENTS.md`

Content is the AGENTS.md template rendered with PROJECT_NAME="webservice". This creates the canonical agent posture document with boot protocol checklist, LBC placeholders, baked-in decisions section, and the CTM artifacts reference table.

**Status recorded**: `AGENTS.md -> "created"`

---

## Phase 5b: CLAUDE.md scaffolding

**Source**: `activate.py` lines 171-174; `templates.py:render_claude_md()`

**File written**: `/path/to/hypothetical/repo/CLAUDE.md`

Note: CLAUDE.md is written at the repo root here. Later in Phase 5d (dot-init claude), the engine also creates `.claude/CLAUDE.md` — but that step detects the root CLAUDE.md exists and skips it per `dot_init.py:init_claude()` line 83: `if root_claude.exists() and not force: results[str(claude_md_path)] = "skipped (root CLAUDE.md exists)"`.

**Status recorded**: `CLAUDE.md -> "created"`

---

## Phase 5c: .sovereign/ initialization

**Source**: `activate.py` lines 179-183; `sovereign.py:init()`

### Directory created:

```
/path/to/hypothetical/repo/.sovereign/
```

### Files written by sovereign.py:init():

**`.sovereign/session_state.json`** — initial session state seeded by `_write_session_state_seed()`:

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "last_agent": "",
  "last_timestamp": "2026-05-23T14:30:00.000000",
  "last_action": "Initial CTMv3 activation",
  "open_tasks": [
    "Fill TOPOLOGY.md LBC sections",
    "Fill ARCHITECTURE_MAP.md branches with file:line anchors",
    "Fill AGENTS.md with project-specific content"
  ],
  "topology_hash": "",
  "warm_start_valid": false
}
```

The `session_id` is a fresh UUID4 generated at init time (sovereign.py line 107: `state["session_id"] = str(uuid.uuid4())`). The `topology_hash` is empty at this point — it gets filled in Phase 5e after the fingerprint is computed.

**`.sovereign/golden_paths.json`** — seeded with the CTM session bootstrap chain:

```json
{
  "ctm_session_bootstrap": {
    "chain": ["bb7_exo_bootstrap", "bb7_lisan_intend", "bb7_exo_route"],
    "priors": {"alpha": 7.0, "beta": 1.0},
    "use_cases": ["CTM session start", "skill-guided repo entry"],
    "tags": ["ctm", "session", "bootstrap"]
  }
}
```

**`.sovereign/topology_fingerprint.txt`** — placeholder only at this stage:

```
sha256:0000000000000000000000000000000000000000000000000000000000000000

Placeholder — run: python -m ctmv3 fingerprint to compute real hash.
```

This placeholder will be overwritten in Phase 5e.

**Status recorded**: `.sovereign/ -> "initialized"`

---

## Phase 5d: .xyz Directory initialization

**Source**: `activate.py` lines 186-195; `dot_init.py:init_target("all", ...)`

Dispatches to `init_all()` which runs `init_claude()`, `init_codex()`, `init_github()` in sequence.

### .claude/ (init_claude)

**Files written**:

`.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(python:*)",
      "Bash(go build:*)",
      "Read(*)",
      "Write(src/**)",
      "Write(tests/**)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Write(manifest.json)"
    ]
  },
  "env": {
    "SOVEREIGN_DATA_DIR": "./data",
    "SOVEREIGN_DISTILLATION_ENABLED": "0"
  }
}
```

`.claude/CLAUDE.md` — **SKIPPED**: root CLAUDE.md already exists (written in Phase 5b). `init_claude()` line 83 detects this and records `"skipped (root CLAUDE.md exists)"`.

### .codex/ (init_codex)

**Directories created**:
- `.codex/skills/`
- `.codex/session/`

**Files written**:
- `.codex/skills/.gitkeep` — placeholder to track the directory in git

### .github/ (init_github)

**Directories created**:
- `.github/`
- `.github/instructions/`
- `.github/workflows/`

**Files written**:

`.github/copilot-instructions.md` — rendered from copilot-instructions.md.template with PROJECT_NAME="webservice":
```markdown
# webservice — Agent Context

This file provides context for all agents operating in this repository.
...
```

`.github/instructions/README.md` — brief documentation of the instructions/ directory purpose.

`.github/workflows/topology-enforce.yml` — CI workflow that checks for topology drift on PRs.

---

## Phase 5e: Fingerprint computation

**Source**: `activate.py` lines 199-207; `fingerprint.py:write()` and `fingerprint.py:compute()`

The engine computes SHA-256 of TOPOLOGY.md + ARCHITECTURE_MAP.md concatenated (fingerprint.py lines 37-51):

```python
hasher = hashlib.sha256()
# TOPOLOGY.md exists now (written in Phase 1):
hasher.update(TOPOLOGY_MD_bytes)
# ARCHITECTURE_MAP.md exists now (written in Phase 4):
hasher.update(ARCHITECTURE_MAP_MD_bytes)
hash_value = "sha256:" + hasher.hexdigest()
```

**Example output hash** (illustrative — actual value depends on template content):
```
sha256:8f4a1e2b9c3d7f6e0a5b4c8d9e2f1a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f
```

**File overwritten**: `.sovereign/topology_fingerprint.txt`

```
sha256:8f4a1e2b9c3d7f6e0a5b4c8d9e2f1a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f

Sources hashed (in order):
  TOPOLOGY.md: present
  ARCHITECTURE_MAP.md: present

Regenerate with: python -m ctmv3 fingerprint --project-root <path>
```

**Status recorded**: `.sovereign/topology_fingerprint.txt -> "written"`, `report["fingerprint"] = "sha256:8f4a..."`

---

## Phase 5f: Final session state write

**Source**: `activate.py` lines 210-225; `sovereign.py:write_session_state()`

The engine writes the final session state, now including the real topology hash:

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "last_agent": "CTMv3 Engine",
  "last_timestamp": "2026-05-23T14:30:01.234567",
  "last_action": "Initial cold-start activation",
  "open_tasks": [
    "Fill TOPOLOGY.md LBC sections",
    "Fill ARCHITECTURE_MAP.md branches with file:line anchors",
    "Fill AGENTS.md with project-specific content",
    "Fill FAILURE_GRAMMAR.md with domain-specific patterns"
  ],
  "topology_hash": "sha256:8f4a1e2b9c3d7f6e0a5b4c8d9e2f1a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
  "warm_start_valid": false
}
```

Note `warm_start_valid: false` — this is correct. The session was a cold start; the artifacts were just created and have not been reviewed by a human or agent. A future agent should run `ctmv3 warm` to verify the state before trusting the warm-start path.

---

## Full Activation Report (returned from activate.py:run())

```json
{
  "phase": "cold_start",
  "signal_inventory": {
    "project_root": "/path/to/hypothetical/repo",
    "tier1_signals": [],
    "tier2_signals": [],
    "tier3_signals": ["pyproject.toml", "package.json", ".env.example"],
    "provenance_present": false,
    "manifest_present": false,
    "last_session": null,
    "branch": "COLD_START",
    "config_spine": {
      "pyproject.toml": true,
      "package.json": true,
      ".env.example": true
    },
    "session_state_valid": false,
    "session_timestamp": null
  },
  "files_written": {
    "/path/to/hypothetical/repo/TOPOLOGY.md": "created",
    "/path/to/hypothetical/repo/FAILURE_GRAMMAR.md": "created",
    "/path/to/hypothetical/repo/PROVENANCE.md": "created",
    "/path/to/hypothetical/repo/ARCHITECTURE_MAP.md": "created",
    "/path/to/hypothetical/repo/AGENTS.md": "created",
    "/path/to/hypothetical/repo/CLAUDE.md": "created",
    "/path/to/hypothetical/repo/.sovereign": "initialized",
    "/path/to/hypothetical/repo/.claude/settings.json": "created",
    "/path/to/hypothetical/repo/.claude/CLAUDE.md": "skipped (root CLAUDE.md exists)",
    "/path/to/hypothetical/repo/.codex/skills": "created",
    "/path/to/hypothetical/repo/.codex/session": "created",
    "/path/to/hypothetical/repo/.codex/skills/.gitkeep": "created",
    "/path/to/hypothetical/repo/.github/instructions": "created",
    "/path/to/hypothetical/repo/.github/workflows": "created",
    "/path/to/hypothetical/repo/.github/copilot-instructions.md": "created",
    "/path/to/hypothetical/repo/.github/workflows/topology-enforce.yml": "created",
    "/path/to/hypothetical/repo/.github/instructions/README.md": "created",
    "/path/to/hypothetical/repo/.sovereign/topology_fingerprint.txt": "written"
  },
  "fingerprint": "sha256:8f4a1e2b9c3d7f6e0a5b4c8d9e2f1a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
  "errors": [],
  "aborted": false,
  "abort_reason": null,
  "project_name": "webservice",
  "today": "2026-05-23"
}
```

---

## PROVENANCE.md Session Log Entry Written

The PROVENANCE.md template pre-fills the initial Session Log row (PROVENANCE.md.template lines 65-67):

```
| 2026-05-23 | CTMv3 Engine | Initial activation — scaffolded CTMv3 artifacts | no | Fill TOPOLOGY.md LBCs and ARCHITECTURE_MAP.md branches |
```

This is the exact format: `| Date | Agent | Action | Topology Drift? | Next Recommended Action |`

Future session closes via `ctmv3 session-close --agent "Claude Code" --action "..."` will append new rows below this one via `sovereign.py:update_session_log()`.

---

## Post-State: The Repository After Activation

```
/path/to/hypothetical/repo/
├── src/                              [unchanged]
├── tests/                            [unchanged]
├── frontend/                         [unchanged]
├── requirements.txt                  [unchanged]
├── pyproject.toml                    [unchanged]
├── package.json                      [unchanged]
├── .env.example                      [unchanged]
├── README.md                         [unchanged]
│
├── TOPOLOGY.md                       [NEW] — topology skeleton; fill LBCs
├── FAILURE_GRAMMAR.md                [NEW] — failure taxonomy skeleton
├── PROVENANCE.md                     [NEW] — decision log with initial session row
├── ARCHITECTURE_MAP.md               [NEW] — traversal map skeleton
├── AGENTS.md                         [NEW] — canonical agent posture document
├── CLAUDE.md                         [NEW] — Claude Code context
│
├── .sovereign/                       [NEW]
│   ├── session_state.json            [NEW] — session continuity anchor
│   ├── golden_paths.json             [NEW] — seeded with ctm_session_bootstrap
│   └── topology_fingerprint.txt      [NEW] — SHA-256 of TOPOLOGY.md + ARCHITECTURE_MAP.md
│
├── .claude/                          [NEW]
│   └── settings.json                 [NEW] — permission allow/deny list
│
├── .codex/                           [NEW]
│   ├── skills/                       [NEW]
│   │   └── .gitkeep                  [NEW]
│   └── session/                      [NEW]
│
└── .github/                          [NEW]
    ├── copilot-instructions.md       [NEW] — repo-wide agent context
    ├── instructions/                 [NEW]
    │   └── README.md                 [NEW]
    └── workflows/
        └── topology-enforce.yml      [NEW] — CI topology enforcement gate
```

---

## Boot State After Activation

Run `ctmv3 boot --project-root /path/to/hypothetical/repo --json` immediately after activation:

```json
{
  "project_root": "/path/to/hypothetical/repo",
  "tier1_signals": ["ARCHITECTURE_MAP.md", "AGENTS.md"],
  "tier2_signals": ["PROVENANCE.md"],
  "tier3_signals": ["pyproject.toml", "package.json", ".env.example"],
  "provenance_present": true,
  "manifest_present": false,
  "last_session": "| 2026-05-23 | CTMv3 Engine | Initial activation — scaffolded CTMv3 artifacts | no | Fill TOPOLOGY.md LBCs and ARCHITECTURE_MAP.md branches |",
  "branch": "WARM_START",
  "config_spine": { ... },
  "session_state_valid": true,
  "session_timestamp": "2026-05-23T14:30:01.234567"
}
```

The repo went from `COLD_START` to `WARM_START` in a single activation pass. All seven `tier1_signals` criteria are not required simultaneously — `ARCHITECTURE_MAP.md` and `AGENTS.md` are sufficient Tier 1 signals, and PROVENANCE.md has a populated Session Log.

---

## What the Agent Should Do Next

The activation scaffolds the shape but does not fill the content. The artifacts are skeletons — every `[TODO: ...]` marker is a question the next agent or operator must answer by reading the actual source code.

### Priority order for the next session:

1. **Read ARCHITECTURE_MAP.md** — it shows you what questions the map is trying to answer. The ROOT node is what you fill first. Each branch node has a question at the top.

2. **Run `ctmv3 warm`** — verifies that the freshly created session state is coherent and that the fingerprint matches. This transitions the session from "just activated" to "ready to continue."

3. **Read the actual repo source** — `src/api/routes.py`, `src/services/data_pipeline.py`, `requirements.txt`. Extract the Load-Bearing Concepts for this specific codebase and fill `TOPOLOGY.md`.

4. **Fill ARCHITECTURE_MAP.md** — once you have LBCs from TOPOLOGY.md, you can anchor each branch node to specific `file:line` references in the source.

5. **Fill AGENTS.md** — copy the top 3 LBCs from TOPOLOGY.md with their common misunderstandings. This is what any future agent reads in 30 seconds before working.

6. **Close the session** — run `ctmv3 session-close --agent "Claude Code" --action "Filled TOPOLOGY.md LBCs, ARCHITECTURE_MAP.md branches" --next-action "Fill FAILURE_GRAMMAR.md"` to log the work and update the topology fingerprint.

The archaeology work (steps 3-5) is the human/agent contribution. CTMv3 provides the structure; the content comes from reading the actual code.

---

## Key Engine Behaviors Demonstrated in This Trace

1. **Read-only Phase 0**: The discovery sequence (boot.py:discover) makes no writes whatsoever. It is safe to run on any repo, any state.

2. **Strict phase ordering** (BOOT_PROTOCOL.md Section 4.2): TOPOLOGY.md before PROVENANCE.md before ARCHITECTURE_MAP.md before .sovereign/. The session state anchor is always written last because it anchors to the completed artifacts, not to partial work.

3. **Idempotency**: Running `ctmv3 activate` a second time on this repo will detect the Tier 1 signals, classify as WARM_START, find AGENTS.md exists, and abort with `"Repo has existing CTM artifacts: ['AGENTS.md', ...]. Pass --force to overwrite..."`. The second run cannot corrupt the first activation's work.

4. **Project name inference chain**: pyproject.toml was found with `name = "webservice"`. The engine used that rather than falling through to the directory name fallback.

5. **Language detection from config spine**: Two config spine signals (pyproject.toml → Python, package.json → JavaScript) produced `"mixed (python, javascript)"` in TOPOLOGY.md.

6. **.claude/CLAUDE.md skip**: Because CLAUDE.md was written at the repo root in Phase 5b, dot_init skips `.claude/CLAUDE.md` rather than writing a duplicate. One canonical CLAUDE.md per repo, not two.

7. **Fingerprint is written twice**: First as a placeholder (sovereign.py:init), then as the real hash (fingerprint.py:write in Phase 5e). The placeholder prevents any code from reading an absent fingerprint file during the brief window between .sovereign/ creation and hash computation.
