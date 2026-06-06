# DOT_TOPOLOGY.md — .xyz Directories as Topology Signals

**Loaded by**: SKILL.md for [INTEGRATE_AGENT_ECOSYSTEM], [COLD_START_REPO],
[BUILD_ARCHITECTURE_MAP], or whenever .github/.claude/.codex/.sovereign work is in scope  
**Purpose**: The directories and config files at a project root are not just
housekeeping. They are the codebase's self-description layer — its topology expressed
as filesystem structure. This document encodes how to read them, what they mean
architecturally, and how to build them correctly as executable ecosystem artifacts.

---

## Core Principle: The Config Spine as Topology Evidence

Before reading a single Python or Go file, read the root-level config spine.
A codebase's config files encode decisions that would take hours to reverse-engineer
from source:
- What dependencies exist → what capabilities are in play
- What entry points are declared → what the intended surface is
- What tool configuration exists → what quality gates are enforced
- What environment variables are required → what external systems are wired in

**The spine is the skeleton. Source is the flesh. Read skeleton first.**

This is especially true in Daeron's system where `manifest.json` exists:
the manifest is the ground-truth snapshot claim. Everything outside the manifest
hash boundary is unverified.

---

## DIRECTORY TAXONOMY

### `.github/` — CI Enforcement and Agent Context

**What it is**: GitHub's special directory for Actions workflows, PR templates, issue
templates, and (since Copilot integration) per-path agent instruction files.

**What it means architecturally**: The `.github/` directory is where topology contracts
become enforceable. If TOPOLOGY.md says "wrappers must be < 200 lines," `.github/`
is where that claim becomes a failing CI check.

**Files that matter for CTM:**

```
.github/
├── copilot-instructions.md     ← Repo-wide agent instruction (Copilot/Claude Code reads this)
│                                  This is effectively a public AGENTS.md. Write it.
├── instructions/               ← Per-path agent context (GitHub Copilot model)
│   ├── backend.instructions.md ← Context injected when working in /backend/
│   ├── tests.instructions.md   ← Context injected when working in /tests/
│   └── {module}.instructions.md
└── workflows/
    ├── topology-enforce.yml    ← CI gate: enforce CTM constraints on every PR
    └── snapshot-verify.yml     ← CI gate: manifest.json hash verification
```

**How to build `copilot-instructions.md`** (the agent-facing root instruction):
```markdown
# [Project Name] — Agent Context

## What This Codebase Is
[2–3 sentences from TOPOLOGY.md: domain, primary purpose, key constraint]

## Architecture
[Paste the dependency graph from TOPOLOGY.md]
[Reference: full topology at ARCHITECTURE_MAP.md]

## What You Cannot Get Wrong (Load-Bearing Concepts)
[3–7 LBCs from TOPOLOGY.md — abbreviated, with the "common misunderstanding" field]

## What Already Exists (Do Not Reimplement)
[Production modules list — integration > implementation]

## Baked-In Decisions (Do Not Question These)
[From TOPOLOGY.md Baked-In Decisions section]

## If Something Smells Wrong
[Top 2–3 pre-failure signatures from FAILURE_GRAMMAR.md]

## Tools
[bb7_ tools if sovereign MCP active; otherwise: project-specific CLI tools]
```

**Topology enforcement workflow** (`topology-enforce.yml` sketch):
```yaml
name: CTM Topology Enforcement
on: [pull_request]
jobs:
  wrapper-size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check wrapper line counts
        run: |
          # Fail if any wrapper exceeds 200 lines (per CONSTITUTION.md)
          for f in $(find . -name "*.py" -path "*/wrappers/*"); do
            lines=$(wc -l < "$f")
            if [ "$lines" -gt 200 ]; then
              echo "FAIL: $f exceeds 200 lines ($lines)"
              exit 1
            fi
          done
  manifest-verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify manifest hash
        run: python3 scripts/verify_manifest.py  # if manifest.json exists
```

**Critical note**: `.github/` hooks only run if pushed to GitHub. For local enforcement,
use pre-commit hooks (see below). Never assume `.github/` covers local dev.

---

### `.claude/` — Claude Code Context

**What it is**: Claude Code's configuration directory. Claude Code reads
`settings.json` for permissions and behavioral configuration, and looks for
`CLAUDE.md` either here or at the project root.

**Files:**
```
.claude/
├── settings.json     ← Claude Code permissions + tool allow/deny lists
└── CLAUDE.md         ← Claude-specific operational context (may also live at root)
```

**`settings.json` structure**:
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
      "Write(manifest.json)"  // snapshot files are read-only by doctrine
    ]
  },
  "env": {
    "SOVEREIGN_DATA_DIR": "./data",
    "SOVEREIGN_DISTILLATION_ENABLED": "0"  // off by default, explicit opt-in
  }
}
```

**`CLAUDE.md` vs `AGENTS.md`**: CLAUDE.md is Claude Code-specific. AGENTS.md is
agent-agnostic. If only one agent will ever operate here, CLAUDE.md alone is sufficient.
If multiple agents (Codex + Claude Code + future), AGENTS.md is the canonical posture
and CLAUDE.md may extend it with Claude-specific tool protocols.

**What CLAUDE.md should encode** (minimum viable):
1. What this project is (2 sentences)
2. Where the topology map is (`→ ARCHITECTURE_MAP.md`)
3. What tools are available and how to call them
4. The boot protocol summary (cold/warm, .sovereign/ check)
5. What operations require explicit Daeron confirmation before executing

---

### `.codex/` — Codex Skill Installation and Agent State

**What it is**: Codex's home directory in the project. Codex installs skills here,
maintains its AGENTS.md reference, and expects session continuity artifacts.

**Files:**
```
.codex/
├── skills/
│   └── {skill-name}/       ← CTM skill packages installed for this repo
│       ├── SKILL.md
│       ├── TOPOLOGY.md
│       └── ...
└── session/                ← Codex session state (if maintained)
    └── last_session.json
```

**Installation note**: When Daeron says "install this skill for Codex in this repo,"
the output goes to `.codex/skills/{skill-name}/`. The global skill location is
`~/.codex/skills/`. Per-repo skills in `.codex/skills/` override or extend global skills
for that specific repo.

**AGENTS.md placement**: AGENTS.md lives at project root, not inside `.codex/`.
Codex reads it from root. `.codex/` is operational state, not instruction.

---

### `.sovereign/` — Session Continuity and Exoskeleton State

**What it is**: Daeron's sovereign session state directory. The most important
`.xyz` directory for CTM purposes. Its presence signals that the exoskeleton + bb7
system has been active in this repo.

**Files:**
```
.sovereign/
├── session_state.json        ← Current session: agent, timestamp, last action, tasks
├── golden_paths.json         ← Repo-specific golden paths (extends global)
├── PROVENANCE.md             ← Mirror or symlink of skill PROVENANCE.md
└── topology_fingerprint.txt  ← Hash of TOPOLOGY.md + ARCHITECTURE_MAP.md at last session
```

**`session_state.json` structure**:
```json
{
  "session_id": "...",
  "last_agent": "Claude Code",
  "last_timestamp": "2026-05-11T...",
  "last_action": "Updated TOPOLOGY.md LBC section for async boundary",
  "open_tasks": [
    "Build .github/topology-enforce.yml",
    "Seed golden_paths.json with session bootstrap path"
  ],
  "topology_hash": "sha256:...",
  "warm_start_valid": true
}
```

**`topology_fingerprint.txt`**: After building or updating TOPOLOGY.md and
ARCHITECTURE_MAP.md, write a SHA-256 hash of both files here. The BOOT_PROTOCOL.md
warm check uses this to detect topology drift since last session.

**`golden_paths.json` at `.sovereign/`**: This file seeds repo-specific golden paths
for the exoskeleton. It should contain at minimum the session bootstrap path:
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

---

## CONFIG FILE SPINE: What Each File Reveals

### `pyproject.toml` / `setup.py`
Read before any Python file. Extract:
- `[tool.pytest.ini_options]` → what test structure is in play
- `[tool.mypy]` → type strictness level (impacts wrapper typing requirements)
- `[tool.ruff]` / `[tool.black]` → code style enforcement exists
- `dependencies` / `install_requires` → what is in the dependency graph
- `[project.scripts]` → entry points → the bb7-facing surface

### `go.mod`
- Module path → canonical import prefix (all imports must use this)
- Go version → language feature availability
- `require` block → what external systems are wired in

### `Cargo.toml`
- `[features]` block → optional capability flags
- `[[bin]]` → multiple binaries = multiple entry points, each is a topology node
- `[workspace]` → monorepo structure

### `manifest.json` (Somnus-specific)
**This is the most important config file in Daeron's system.**
- SHA-256 hash of the snapshot state
- File list = canonical production file set
- Version tag = snapshot lineage anchor
- If present: any file NOT in the manifest is either new (post-snapshot) or experimental
- **Never modify manifest.json during a session. It is read-only by doctrine.**

### `golden_paths.json` (at repo root, not .sovereign/)
- Pre-trained workflow templates for this repo's bb7 system
- If present: the exoskeleton has been active here
- Read before any bb7 routing work — these are the proven chains

### `AGENTS.md` / `CLAUDE.md` (at repo root)
These are the most information-dense config files for agent topology.
They encode the operational posture of all prior agent sessions. Read them before
beginning any archaeology — they may have already encoded what you're about to encode.

---

## PRE-COMMIT HOOKS AS LOCAL TOPOLOGY ENFORCEMENT

`.github/` workflows only fire on push. Pre-commit hooks fire on every local commit.
For Daeron's system, pre-commit is the right enforcement layer for:
- Wrapper line count limits
- Type hint completeness checks
- Manifest hash verification (prevent accidental modification)
- PROVENANCE.md Session Log update reminder

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: wrapper-size-check
        name: CTM Wrapper Size Gate
        entry: python3 scripts/check_wrapper_sizes.py
        language: python
        types: [python]
      - id: provenance-reminder
        name: PROVENANCE Session Log Reminder
        entry: bash -c 'echo "Did you update PROVENANCE.md Session Log?"'
        language: system
        always_run: true
        pass_filenames: false
```

---

## BUILD SEQUENCE FOR ECOSYSTEM ARTIFACTS

When running Phase 5 (ecosystem artifact construction) from SKILL.md:

```
1. Read config spine → extract dependency map
2. Build or update TOPOLOGY.md if needed
3. Build ARCHITECTURE_MAP.md from TOPOLOGY.md (see ARCHITECTURE_MAP_TEMPLATE.md)
4. Create .sovereign/ → initialize session_state.json + topology_fingerprint.txt
5. Create/update AGENTS.md at root
6. Create/update .claude/settings.json + CLAUDE.md (if Claude Code is primary)
7. Create .github/copilot-instructions.md from TOPOLOGY.md summary
8. Create .github/instructions/ per-path files for high-complexity modules (DENSE nodes)
9. Create .github/workflows/ enforcement gates (wrapper size, manifest verify, etc.)
10. Optionally: create .pre-commit-config.yaml for local enforcement
11. Update PROVENANCE.md Session Log with this build action
```

**Never build `.github/` before TOPOLOGY.md is complete.** The hooks enforce the
topology contracts. If the topology is unknown, the hooks are either empty (useless)
or wrong (harmful).

---

## ANTI-PATTERNS IN DOT DIRECTORY WORK

- ❌ Copying `.github/` from another repo without adapting to this topology
- ❌ Writing `copilot-instructions.md` as a flat description instead of a navigable map
- ❌ Creating `.sovereign/session_state.json` before the topology artifacts are complete
- ❌ Using `manifest.json` as a mutable tracking file — it is a snapshot claim, not a log
- ❌ Putting operational logic inside `.claude/settings.json` — settings are permissions,
  not instructions; instructions go in CLAUDE.md
- ❌ Building pre-commit hooks that block on linting when the codebase is mid-refactor —
  gates should enforce structural invariants, not style, during active development phases
