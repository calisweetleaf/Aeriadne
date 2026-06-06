---
description: Initialize .sovereign/ — the session continuity anchor. Creates session_state.json and topology_fingerprint.txt. Run after topology artifacts exist.
---

Initialize or reinitialize `.sovereign/` — the session continuity anchor for CTMv3.

The `.sovereign/` directory stores:
- `session_state.json` — last agent, last action, open tasks, topology hash, warm start validity
- `topology_fingerprint.txt` — SHA-256 hash of TOPOLOGY.md + ARCHITECTURE_MAP.md
- `golden_paths.json` — proven tool chains for the repo (if using the bb7 system)

Run this after TOPOLOGY.md and ARCHITECTURE_MAP.md exist. Initializing before the
topology artifacts exist creates a stale anchor.

## Invocation

```bash
python3 -m ctmv3 sovereign-init --json --project-root "$PWD"
```

## Idempotent

If `.sovereign/` already exists, the command reinitializes the session state without
destroying existing data. Run it again after a session state reset if session_state.json
becomes malformed per BOOT_PROTOCOL.md Section 6 Failure 4.

## After initialization

Run `/ctmv3-fingerprint` to compute the initial topology hash, then
`/ctmv3-session-close` to write the first session log entry.
