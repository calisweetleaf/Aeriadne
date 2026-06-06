---
description: Report current CTMv3 workspace state — artifact inventory, session state, topology validity
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
argument-hint: "[--project-root PATH]"
---
# /ctmv3:status

Workspace status report. Reads the current CTMv3 artifact set and session state, then
produces a structured summary without making any writes. Use at any point to inspect
the workspace state.

## Invocation

```bash
python3 -m ctmv3 status --json $ARGUMENTS
```

## What the engine reports

```json
{
  "artifact_inventory": {
    "TOPOLOGY.md": "present | absent | stale",
    "FAILURE_GRAMMAR.md": "present | absent",
    "ARCHITECTURE_MAP.md": "present | absent | stale",
    "PROVENANCE.md": "present | absent | empty_log",
    "AGENTS.md": "present | absent",
    "CLAUDE.md": "present | absent",
    ".sovereign/": "present | absent | malformed",
    ".claude/settings.json": "present | absent",
    ".github/copilot-instructions.md": "present | absent"
  },
  "session_state": {
    "last_agent": "string or null",
    "last_action": "string or null",
    "last_timestamp": "ISO datetime or null",
    "open_tasks": [...],
    "topology_hash_current": "sha256:... or null",
    "topology_hash_stored": "sha256:... or null",
    "topology_drifted": true | false
  },
  "boot_state": "COLD | WARM | PARTIAL | WARM_STALE",
  "completeness_score": "0-8 (one point per CTMv3 output contract item)",
  "missing_artifacts": [...]
}
```

The completeness_score maps to the CTMv3 output contract (SKILL.md Output Contract
section): 1 point each for the 5 CTMv2 outputs + 3 CTMv3 additions.

## If engine is unavailable

Run these checks manually and report results:
```bash
ls .sovereign/ 2>/dev/null || echo "absent"
ls TOPOLOGY.md ARCHITECTURE_MAP.md AGENTS.md CLAUDE.md PROVENANCE.md 2>/dev/null
cat .sovereign/session_state.json 2>/dev/null || echo "absent"
```

## Report back

Format the output as:

Artifact inventory: [table with file / status]
Session state: last agent, last action, timestamp, open tasks
Boot state: COLD / WARM / PARTIAL / WARM_STALE
Completeness: N/8 — list what is missing
Topology drift: yes/no — if yes, state which hash changed

Do not make any recommendations unless the completeness score is below 6 or topology
has drifted. In those cases, state the single most impactful next command to run.
