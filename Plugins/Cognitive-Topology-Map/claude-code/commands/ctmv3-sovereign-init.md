---
description: Initialize or repair .sovereign/ — session state anchor, topology fingerprint, golden paths
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
  - Write
argument-hint: "[--project-root PATH] [--repair]"
---
# /ctmv3:sovereign-init

Initialize the .sovereign/ directory. Creates session_state.json, topology_fingerprint.txt,
and golden_paths.json. If .sovereign/ already exists and is malformed (BOOT_PROTOCOL.md
Section 6, Failure mode 4), pass --repair to seed fresh without deleting existing files.

Maps to: DOT_TOPOLOGY.md § .sovereign/ — the session continuity anchor.
Must run AFTER TOPOLOGY.md and ARCHITECTURE_MAP.md exist (BOOT_PROTOCOL.md Section 4.2
ordering rule: .sovereign/ anchors to completed artifacts, not pre-built artifacts).

## Invocation

```bash
python3 -m ctmv3 sovereign-init --json $ARGUMENTS
```

## Pre-flight check

Before invoking the engine, verify the prerequisites exist:
```bash
test -f TOPOLOGY.md && echo "topology: ok" || echo "topology: MISSING"
test -f ARCHITECTURE_MAP.md && echo "arch-map: ok" || echo "arch-map: MISSING"
```

If either is missing, stop and report which prerequisite is absent. Do not initialize
.sovereign/ before the topology artifacts are complete — this creates a stale anchor.

## What the engine produces

```
.sovereign/
├── session_state.json          <- current session: agent, timestamp, last action, tasks
├── topology_fingerprint.txt    <- SHA-256 of TOPOLOGY.md + ARCHITECTURE_MAP.md
└── golden_paths.json           <- seed golden paths for this repo's bb7 system
```

session_state.json structure:
```json
{
  "session_id": "<generated>",
  "last_agent": "Claude Code",
  "last_timestamp": "<ISO datetime>",
  "last_action": "CTMv3 sovereign-init",
  "open_tasks": [],
  "topology_hash": "sha256:<hash>",
  "warm_start_valid": true
}
```

## Repair mode

If --repair is in $ARGUMENTS and .sovereign/ exists with malformed or empty files,
the engine will reseed only the malformed files. Well-formed files are left intact.

## Report back

Confirm .sovereign/ was created or repaired. State the topology hash written to
topology_fingerprint.txt and whether golden_paths.json was seeded with the ctm_session_bootstrap
path. Flag any file that could not be written.
