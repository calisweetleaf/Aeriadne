# CTMv3 Cursor Adapter

The CTMv3 Cursor adapter wires the CTMv3 workspace activation engine into Cursor
as a Cursor Rules file, a set of Cursor Commands, and a set of bash script wrappers.

CTMv3 is a codebase activation and workspace onboarding system. It is not a skill maker.
Its purpose is to enter a repo, install the full agent-operability structure, and make the
codebase living for ongoing agent work. The adapter provides a Cursor-native interface to
the Python engine at the path where you installed ctmv3-plugin.

---

## Why Cursor Has the Cleanest Contract for a 5th Adapter

Cursor Rules (.mdc files) and Cursor Commands are file-based and read at editor start.
No daemon, no IPC, no plugin manifest format that changes with every editor update.
The adapter installs three things:

1. A Cursor Rule (`.cursor/rules/ctmv3.mdc`) that loads CTMv3 cognitive doctrine
   into the agent context for every session.
2. A set of Cursor Commands (`.cursor/commands/ctmv3-*.md`) that expose each CTMv3
   subcommand as a slash-command in the Cursor Command Palette.
3. Bash wrappers (`scripts/`) that shell out to `python3 -m ctmv3` with sane defaults.

If Cursor updates its schema, only the MDC frontmatter needs revision. The engine
and scripts are unchanged.

---

## Requirements

- Cursor IDE (version supporting `.cursor/rules/` and `.cursor/commands/`)
- Python 3.9+ with the ctmv3 engine installed: `python3 -m ctmv3 version`

To install the core engine from source:

```bash
pip install -e /path/to/ctmv3-plugin/core/
```

---

## Install

### Project scope (installs to `.cursor/` in the current directory)

```bash
cd /path/to/your/repo
bash /path/to/ctmv3-plugin/cursor/install.sh
```

### Global scope (installs to `~/.cursor/` for all projects)

```bash
bash /path/to/ctmv3-plugin/cursor/install.sh global
```

The installer copies:
- `.cursor/rules/ctmv3.mdc` to `<target>/.cursor/rules/`
- `.cursor/commands/ctmv3-*.md` to `<target>/.cursor/commands/`
- `scripts/` wrappers to `<target>/.cursor/scripts/ctmv3/`

Restart Cursor after installing for rules and commands to take effect.

---

## Commands

All commands are invoked from the Cursor Command Palette with a leading `/`.

### `/ctmv3-boot`

Runs the BOOT_PROTOCOL.md discovery sequence. Determines whether the current repo is
COLD, WARM, or PARTIAL in under 60 seconds. Read-only. Always the first step.

### `/ctmv3-activate`

Full workspace activation. Runs Phase 0-5 cold-start: domain archaeology, topology
construction, failure grammar, architecture map, sovereign init, and ecosystem setup.

WARNING: Creates or overwrites multiple artifact files. If CTMv3 artifacts already
exist, the command halts and asks for confirmation unless `--force` is passed.

### `/ctmv3-warm`

Warm session resume. Reads PROVENANCE.md, validates topology currency, and runs
targeted archaeology on drifted areas only. Use at the start of any work session
in an already-activated repo.

### `/ctmv3-architecture-map`

Build or rebuild ARCHITECTURE_MAP.md. Requires TOPOLOGY.md to exist first.

### `/ctmv3-sovereign-init`

Initialize `.sovereign/` — the session continuity anchor. Creates session_state.json
and topology_fingerprint.txt.

### `/ctmv3-dot-init`

Initialize the agent ecosystem directories: `.claude/`, `.codex/`, and `.github/`.

### `/ctmv3-fingerprint`

Recompute topology_fingerprint.txt. Detects topology drift since the last session.

### `/ctmv3-session-close`

Close the current work session cleanly. Updates PROVENANCE.md Session Log and
syncs `.sovereign/session_state.json`.

### `/ctmv3-status`

Show activation status: artifacts present, session state, fingerprint match, and
recommended next command. Read-only.

### `/ctmv3-chain`

Walk the full golden-path domino chain from boot. Executes commands in sequence per
pre-chain rules until terminal. Output is a JSON array of GoldenPathSignal envelopes.

---

## Direct Script Invocation

The scripts installed to `.cursor/scripts/ctmv3/` can be called from any terminal
or from a Cursor terminal panel:

```bash
# Boot discovery
bash .cursor/scripts/ctmv3/ctmv3-boot.sh

# Full activation
bash .cursor/scripts/ctmv3/ctmv3-activate.sh

# Warm start
bash .cursor/scripts/ctmv3/ctmv3-warm.sh

# Architecture map
bash .cursor/scripts/ctmv3/ctmv3-architecture-map.sh

# Sovereign init
bash .cursor/scripts/ctmv3/ctmv3-sovereign-init.sh

# Dot init (all .xyz dirs)
bash .cursor/scripts/ctmv3/ctmv3-dot-init.sh

# Fingerprint
bash .cursor/scripts/ctmv3/ctmv3-fingerprint.sh

# Session close
bash .cursor/scripts/ctmv3/ctmv3-session-close.sh

# Status
bash .cursor/scripts/ctmv3/ctmv3-status.sh

# Full golden-path chain from boot
bash .cursor/scripts/ctmv3/ctmv3-chain.sh
```

All scripts default `PROJECT_ROOT` to `$PWD`. Pass a path as the first argument
to target a different repo.

---

## Per-Command Reference

| Script                       | CTMv3 command      | When to use                                      |
|------------------------------|--------------------|--------------------------------------------------|
| `ctmv3-boot.sh`              | boot               | First thing every session. Cold/warm branch.     |
| `ctmv3-activate.sh`          | activate           | Cold entry: full Phase 0-5 on a new repo.        |
| `ctmv3-warm.sh`              | warm               | Warm entry: diff provenance, continue.           |
| `ctmv3-architecture-map.sh`  | architecture-map   | Build or refresh ARCHITECTURE_MAP.md.            |
| `ctmv3-sovereign-init.sh`    | sovereign-init     | Initialize .sovereign/ after topology is built.  |
| `ctmv3-dot-init.sh`          | dot-init           | Initialize .claude/, .codex/, .github/ dirs.     |
| `ctmv3-fingerprint.sh`       | fingerprint        | Detect topology drift since last session.        |
| `ctmv3-session-close.sh`     | session-close      | Mandatory at session end. Updates PROVENANCE.md. |
| `ctmv3-status.sh`            | status             | Inspect signal inventory and boot state.         |
| `ctmv3-chain.sh`             | chain              | Walk full domino chain. One call, full run.      |

---

## Installed File Layout

```
.cursor/
+-- rules/
|   +-- ctmv3.mdc                  <- Cursor Rules: CTMv3 doctrine (alwaysApply: true)
+-- commands/
|   +-- ctmv3-boot.md
|   +-- ctmv3-activate.md
|   +-- ctmv3-warm.md
|   +-- ctmv3-architecture-map.md
|   +-- ctmv3-sovereign-init.md
|   +-- ctmv3-dot-init.md
|   +-- ctmv3-fingerprint.md
|   +-- ctmv3-session-close.md
|   +-- ctmv3-status.md
|   +-- ctmv3-chain.md
+-- scripts/
    +-- ctmv3/
        +-- ctmv3-boot.sh
        +-- ctmv3-activate.sh
        +-- ctmv3-warm.sh
        +-- ctmv3-architecture-map.sh
        +-- ctmv3-sovereign-init.sh
        +-- ctmv3-dot-init.sh
        +-- ctmv3-fingerprint.sh
        +-- ctmv3-session-close.sh
        +-- ctmv3-status.sh
        +-- ctmv3-chain.sh
```

---

## Troubleshooting

**Commands not appearing in Cursor Command Palette**
Verify `.cursor/commands/` contains the `ctmv3-*.md` files. Restart Cursor after
installing — Cursor loads commands at startup.

**Cursor Rule not loading**
Verify `.cursor/rules/ctmv3.mdc` exists and has valid MDC frontmatter with
`alwaysApply: true`. Restart Cursor.

**`python3 -m ctmv3` not found**
The core engine is not installed. Run:
```bash
pip install -e /path/to/ctmv3-plugin/core/
```

**Scripts run but nothing happens in the repo**
Run `ctmv3-status.sh` first to check the signal inventory. If all tiers are absent,
the repo has no CTM artifacts and needs a cold start via `ctmv3-activate.sh`.
