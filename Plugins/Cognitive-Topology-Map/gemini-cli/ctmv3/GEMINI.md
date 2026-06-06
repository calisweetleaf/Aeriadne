# CTMv3 — Workspace Activation System

## What CTMv3 Is

CTMv3 is not a skill maker. That is the wrong framing.

CTMv3 is a **codebase activation and workspace onboarding system** whose job is
to enter a repo and make that repo **living for agents**. It may create a skill
as one artifact, but that is not the main point.

The main point is:

- Set up the repo properly and install the agent-facing structure.
- Create the right `.xyz` folders and files (`.sovereign/`, `.claude/`,
  `.codex/`, `.github/`).
- Wire in hooks and workflow surfaces.
- Establish memory, context, and doctrine surfaces.
- Leave the codebase in a state where an agent can actually work inside it
  instead of guessing.

After a proper CTMv3 pass, the codebase should stop feeling like a dead folder
tree and start feeling like a **living workspace** — one where an agent can
enter and immediately understand what this codebase is, how it is organized,
what matters most, what has already been decided, where the risk is, and how to
continue work without re-deriving everything from scratch.

**One-sentence definition**: CTMv3 is a workspace activation system that turns
a codebase into a living, agent-operable repo — not merely a skill maker.

---

## Available Commands

Run all commands via: `python3 -m ctmv3 <subcommand> --project-root "$PWD"`

| Subcommand           | What it does                                                                  | Shell invocation                                                          |
|----------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `boot`               | Discovery sequence: detect cold/warm/partial entry state, return signal inventory | `python3 -m ctmv3 boot --json --project-root "$PWD"`                 |
| `activate`           | Full Phase 0-5 cold-start activation pass on the repo                        | `python3 -m ctmv3 activate --project-root "$PWD"`                        |
| `warm`               | Warm-start check: diff current state against last session, log delta         | `python3 -m ctmv3 warm --project-root "$PWD"`                            |
| `architecture-map`   | Build or update ARCHITECTURE_MAP.md traversal artifact from TOPOLOGY.md      | `python3 -m ctmv3 architecture-map --project-root "$PWD"`               |
| `sovereign-init`     | Initialize `.sovereign/` directory with session_state.json and fingerprint   | `python3 -m ctmv3 sovereign-init --project-root "$PWD"`                 |
| `dot-init`           | Create `.claude/`, `.codex/`, `.github/` scaffolds and seed their contents   | `python3 -m ctmv3 dot-init --project-root "$PWD"`                       |
| `session-close`      | Close the session cleanly: update PROVENANCE.md log, flush session state     | `python3 -m ctmv3 session-close --project-root "$PWD"`                  |
| `status`             | Print current workspace activation status and open tasks                     | `python3 -m ctmv3 status --project-root "$PWD"`                         |

For the generic wrapper that forwards any subcommand:

```bash
bash "${extensionPath}/scripts/ctmv3-wrap.sh" <subcommand> [args...]
```

The wrapper reads `CTMV3_PROJECT_ROOT` from the environment (falls back to
`$PWD`) so you can override the root without touching command arguments.

---

## Session Bootstrap Protocol

**Every time Gemini opens a fresh session in a repo**, run boot discovery
before answering any architectural question:

```bash
python3 -m ctmv3 boot --json --project-root "$PWD"
```

Parse the JSON output. It returns:

```json
{
  "branch": "COLD_START | WARM_START | PARTIAL",
  "tier1_signals": [...],
  "tier2_signals": [...],
  "tier3_signals": [...],
  "provenance_present": true,
  "manifest_present": false,
  "last_session": "2026-05-20 | Updated TOPOLOGY.md LBC section",
  "warm_start_valid": true
}
```

**Branch determines your entry path:**

- `COLD_START` — no CTM artifacts found; run full Phase 0-5 activation.
- `WARM_START` — Tier 1 signals present, PROVENANCE.md readable, recent session;
  run warm diff and continue from last logged action.
- `PARTIAL` — some CTM artifacts found but incomplete; run targeted archaeology
  on the missing pieces only.

Do not answer architectural questions about a repo without first knowing the
branch. The boot signal inventory is the ground truth for what has already been
done.

---

## Phase 0-5 Cold-Start Workflow

This is the full activation sequence for a repo where no CTM artifacts exist.

### PRE-PHASE: Boot State Check

Run `python3 -m ctmv3 boot --json` and build the signal inventory. Determine
the branch before any Phase 0 work begins.

### Phase 0: Domain Archaeology (Cold Entry Only)

Read-only scan. Do not write anything during Phase 0.

1. Root scan: `ls -la {project_root}/` — identify Tier 1, 2, 3 signals.
2. `.xyz` directory inventory: check `.github/`, `.claude/`, `.codex/`,
   `.sovereign/` for presence and contents.
3. Config spine read: read (do not execute) `pyproject.toml`, `go.mod`,
   `Cargo.toml`, `package.json`. Extract: dependencies, entry points, tool
   configuration.
4. AGENTS.md / CLAUDE.md presence check: if present, read them. Do not
   duplicate what already exists.
5. PROVENANCE.md check: if present, read the Session Log section.
6. manifest.json check: if present, it is the snapshot ground truth. Files
   outside the manifest are unverified.

Output of Phase 0: a signal inventory and a domain topology sketch — working
map of nodes, edges, and weight concentration.

**Hardware reality (always in scope)**: Daeron's primary machine is a
Ryzen 5 / 12GB RAM, no GPU. Python 3.10+, stdlib only, no CUDA/ML dependencies.
Any activation output that encodes memory-hungry patterns without acknowledging
this constraint is already wrong.

### Phase 1: Topology Construction

Build `TOPOLOGY.md`. This is the cognitive map of the domain.

Required sections:
- Load-Bearing Concepts (3-7 concepts; for each: definition, why load-bearing,
  common misunderstanding, verification test)
- Interface Map (what enters, what exits, behavioral contracts)
- Complexity Distribution (DENSE / MEDIUM / THIN per component; Mermaid diagram
  mandatory for 4+ nodes)
- Dependency Graph (Mermaid diagram mandatory)
- Baked-In Decisions (invisible load-bearing walls, upstream decisions not in
  the code)
- Anti-Concepts (false attractors, things that look like they belong but don't)
- Config File Spine (what .xyz dirs and config files exist and what they encode)

### Phase 2: Failure Grammar Construction

Build `FAILURE_GRAMMAR.md`. Not an error list. A taxonomy of what wrong looks
like before you can prove it is wrong.

Pre-failure signatures and false success patterns are mandatory. For adversarial
domains, adversarial inputs are mandatory.

### Phase 3: Entry Vector Analysis

Encode entry vectors explicitly in the semantic router:

| Entry Type           | Entry Point        | First Doc               |
|----------------------|--------------------|-------------------------|
| Cold session         | Boot check         | BOOT_PROTOCOL.md        |
| Warm session         | Provenance diff    | PROVENANCE.md           |
| Debugging            | Failure grammar    | FAILURE_GRAMMAR.md      |
| New module           | Interface bounds   | TOPOLOGY.md             |
| Snapshot validation  | Provenance chain   | PROVENANCE.md           |

### Phase 4: Provenance Chain

Build or initialize `PROVENANCE.md` with:
- Snapshot Lineage
- Architectural Decisions (Chronological)
- Rejected Alternatives (Graveyard)
- Open Questions
- Integration History
- Session Log

### Phase 5: Ecosystem Artifact Construction

This phase is new in CTMv3. Build the executable agent ecosystem:

```
[project-root]/
├── ARCHITECTURE_MAP.md     Traversal map (question-oriented navigation)
├── AGENTS.md               Operational posture for Codex / Claude Code
├── CLAUDE.md               Claude-specific context (if Claude Code is primary)
├── .github/
│   ├── copilot-instructions.md     Repo-wide agent instruction
│   ├── instructions/               Per-path agent context files
│   └── workflows/                  CI enforcement hooks
├── .claude/
│   └── settings.json       Claude Code settings (permissions, env)
├── .codex/skills/          Codex skill installs
└── .sovereign/
    ├── session_state.json
    ├── golden_paths.json
    └── PROVENANCE.md
```

Build sequence for Phase 5:
1. Read config spine, extract dependency map.
2. Build or update TOPOLOGY.md if needed.
3. Build ARCHITECTURE_MAP.md from TOPOLOGY.md.
4. Create `.sovereign/` — initialize session_state.json + topology_fingerprint.
5. Create/update AGENTS.md at root.
6. Create/update `.claude/settings.json` + CLAUDE.md if Claude Code is primary.
7. Create `.github/copilot-instructions.md` from TOPOLOGY.md summary.
8. Create `.github/instructions/` per-path files for DENSE complexity modules.
9. Create `.github/workflows/` enforcement gates.
10. Update PROVENANCE.md Session Log with this build action.

**Never build `.github/` before TOPOLOGY.md is complete.** The hooks enforce
topology contracts. If the topology is unknown, the hooks are either empty
(useless) or wrong (harmful).

---

## Warm-Start Protocol

**Trigger**: At least one Tier 1 signal present, PROVENANCE.md readable,
Session Log has a recent entry (< 30 days).

Warm validity check — ask three questions:
1. Topology still valid? Has significant new code been added since last encoding?
2. Provenance coherent? Does Session Log's last action match current state of
   AGENTS.md and ARCHITECTURE_MAP.md?
3. No rejected path in play? Does current task match anything in PROVENANCE.md
   Graveyard?

If all three pass: proceed to continue protocol.
If any fail: run targeted partial archaeology — diff the delta, update only
affected documents, log the delta in PROVENANCE.md.

Warm continue protocol:
1. Read PROVENANCE.md Session Log — confirm last state.
2. Verify topology not drifted.
3. Load TOPOLOGY.md — identify relevant section for current task.
4. Proceed with task per semantic router.
5. After substantive work: update PROVENANCE.md Session Log.

---

## Session Close Protocol

Every CTM-active session must close cleanly. Agents that do not close sessions
create stale state that corrupts the next agent's warm start.

Run `python3 -m ctmv3 session-close --project-root "$PWD"` or manually:

```
- Update PROVENANCE.md Session Log:
    Date | Agent | Last action | Topology drift? | Next recommended action
- If topology drifted: update TOPOLOGY.md affected sections.
- If new path was rejected: log in PROVENANCE.md Graveyard.
- If .sovereign/ present: update session_state.json with:
    last_agent, timestamp, last_action, topology_hash, open_tasks
```

---

## CTM Artifact Presence Signals

The following files/directories are CTM presence signals. Their presence,
absence, and content determine the boot branch.

```
TIER 1 — Strong signals (any one = CTM has been run here)
  .sovereign/                  sovereign session state directory
  ARCHITECTURE_MAP.md          traversal map artifact
  .claude/CLAUDE.md            Claude-specific context
  AGENTS.md                    agent operational posture

TIER 2 — Supporting signals (indicate partial CTM or related tooling)
  .github/copilot-instructions.md
  .codex/skills/
  PROVENANCE.md (at repo root)
  manifest.json                Somnus snapshot marker
  golden_paths.json

TIER 3 — Config spine signals (read for archaeology)
  pyproject.toml / setup.py / setup.cfg
  go.mod / go.sum
  Cargo.toml
  package.json
  *.toml / *.yaml / *.json at repo root
  .env.example
```

---

## .xyz Directory Architecture

### `.sovereign/` — Session Continuity Anchor

The most important `.xyz` directory. Its presence signals the exoskeleton +
bb7 system has been active.

```
.sovereign/
├── session_state.json        Current session: agent, timestamp, last action
├── golden_paths.json         Repo-specific golden paths (extends global)
├── PROVENANCE.md             Mirror or symlink of skill PROVENANCE.md
└── topology_fingerprint.txt  Hash of TOPOLOGY.md + ARCHITECTURE_MAP.md
```

**Never initialize `.sovereign/` before the topology artifacts are complete.**
Session state anchors to the completed artifacts.

### `.github/` — CI Enforcement and Agent Context

Where topology contracts become enforceable. `.github/` is enforcement, not
instruction. `.github/copilot-instructions.md` is the repo-wide agent
instruction surface — write it as a navigable map, not a flat description.

`.github/` hooks only run on push to GitHub. For local enforcement, use
pre-commit hooks. Never assume `.github/` covers local dev.

### `.claude/` — Claude Code Context

`settings.json` for permissions and behavioral configuration.
`CLAUDE.md` for Claude-specific operational context.

`settings.json` encodes permissions, not instructions. Instructions go in
`CLAUDE.md`. Never put operational logic in `settings.json`.

### `.codex/` — Codex Skill Installation

Per-repo skills in `.codex/skills/` override or extend global skills for that
specific repo. AGENTS.md lives at project root, not inside `.codex/`.

---

## Anti-Patterns — What CTMv3 Does NOT Produce

- Step-by-step workflows (AGENTS.md quick reference handles that).
- UI/UX documentation.
- Tutorial content (full technical depth assumed).
- Generic best practices (encode actual decisions).
- Flat single-file skills for complex domains.
- Skills that assume the happy path (failure grammar is mandatory).
- Ecosystem setup that requires operator intervention to activate (hooks must
  fire automatically).
- ARCHITECTURE_MAP.md that summarizes instead of navigates (summaries are for
  humans; maps are for agents).

---

## Trigger Phrases for CTMv3 Commands

Since Gemini CLI extension commands use TOML slash-command format, the following
trigger phrases invoke the matching CTMv3 operation via the `/ctmv3:*` commands:

| Slash command              | What fires                            |
|----------------------------|---------------------------------------|
| `/ctmv3:boot`              | Boot discovery, print signal inventory |
| `/ctmv3:activate`          | Full cold-start activation pass        |
| `/ctmv3:warm`              | Warm-start diff and continue check     |
| `/ctmv3:architecture-map`  | Build/update ARCHITECTURE_MAP.md       |
| `/ctmv3:sovereign-init`    | Initialize `.sovereign/` directory     |
| `/ctmv3:dot-init`          | Create `.claude/`, `.codex/`, `.github/` scaffolds |
| `/ctmv3:session-close`     | Close session cleanly                  |
| `/ctmv3:status`            | Print activation status                |

You can also invoke directly without slash commands by asking:
- "run ctmv3 boot" — triggers `python3 -m ctmv3 boot --json --project-root "$PWD"`
- "activate this repo with ctmv3" — triggers full Phase 0-5
- "what is the ctmv3 status" — triggers `python3 -m ctmv3 status --project-root "$PWD"`
- "close the ctmv3 session" — triggers session-close protocol
- "run ctmv3 warm check" — triggers warm-start diff

---

## Output Contract

A completed CTMv3 activation produces these outputs. If any are missing, the
package is incomplete.

1. Agent can answer without asking: What are the 3 things I cannot get wrong?
2. Agent can recognize failure before it is provable: What does wrong smell like?
3. Agent knows what was already rejected: What will not be re-discovered?
4. Agent knows where complexity concentrates: Where to slow down?
5. Agent knows its entry vector: Based on task type, where to enter?
6. Agent knows the boot state: Cold or warm? Determined in < 60 seconds.
7. Agent has a traversal map: ARCHITECTURE_MAP.md answers "where is X" without
   a guide.
8. Codebase enforces itself: `.github/`, `.sovereign/`, AGENTS.md create
   structural enforcement.
