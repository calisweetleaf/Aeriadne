---
description: Warm start — resume a CTMv3-encoded session, running targeted archaeology if topology has drifted
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
  - Write
  - Edit
argument-hint: "[--project-root PATH] [--force-full]"
---
# /ctmv3:warm

Warm session resume. Runs the BOOT_PROTOCOL.md warm start protocol: reads PROVENANCE.md,
checks topology validity, identifies any drift, and performs targeted archaeology on
changed areas only. Does not rebuild from scratch unless --force-full is passed.

Use this command at the start of any session in a repo that has already been CTM-activated.

## Invocation

```bash
python3 -m ctmv3 warm --json $ARGUMENTS
```

## What the engine does

1. Reads PROVENANCE.md Session Log — extracts last agent, last action, timestamp, and
   open tasks.
2. Runs the three warm validity checks from BOOT_PROTOCOL.md Section 3.1:
   - Topology still valid? (new code added since last encoding?)
   - Provenance coherent? (does session log match current AGENTS.md + ARCHITECTURE_MAP.md?)
   - No rejected path in play? (does current task match anything in PROVENANCE.md Graveyard?)
3. If all three pass: reports warm state and continues.
4. If any fail: runs partial archaeology (BOOT_PROTOCOL.md Section 3.2) — targets only
   the delta since last session. Updates affected TOPOLOGY.md sections and logs the delta
   in PROVENANCE.md.

## If engine is absent or fails

If `python3 -m ctmv3 warm` fails, run the discovery manually:
```bash
ls -la .sovereign/ 2>/dev/null || echo "no .sovereign"
```
Then read .sovereign/session_state.json and PROVENANCE.md directly. Report the last
session state from those files and flag that the engine was unavailable.

## Output parsing

```json
{
  "warm_valid": true | false,
  "last_agent": "string",
  "last_action": "string",
  "last_timestamp": "ISO datetime",
  "open_tasks": [...],
  "topology_drifted": true | false,
  "drift_areas": [...],
  "partial_archaeology_ran": true | false,
  "artifacts_updated": [...]
}
```

## Report back

State whether warm start was clean or required partial archaeology. If drift was detected,
name the affected topology areas. List open tasks from the last session. Summarize what
was updated and what the current session should continue from.
