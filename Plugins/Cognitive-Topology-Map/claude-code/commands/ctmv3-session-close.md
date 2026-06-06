---
description: Close the current CTMv3 session — update PROVENANCE.md, session_state.json, topology fingerprint
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
  - Write
  - Edit
argument-hint: "[--project-root PATH] [--last-action TEXT]"
---
# /ctmv3:session-close

Clean session close. Executes the BOOT_PROTOCOL.md Section 5 close protocol: updates
PROVENANCE.md Session Log, refreshes .sovereign/session_state.json, recomputes the
topology fingerprint if TOPOLOGY.md was modified, and logs any rejected paths to
PROVENANCE.md Graveyard.

Every CTM-active session must close cleanly. Agents that skip this step corrupt the next
agent's warm start.

## Invocation

```bash
python3 -m ctmv3 session-close --json $ARGUMENTS
```

If --last-action is provided in $ARGUMENTS, the engine uses that text as the last_action
field in session_state.json and PROVENANCE.md. Otherwise, the engine will attempt to infer
the last action from recent file modifications.

## What the engine does

1. Reads the current .sovereign/session_state.json to get session_id and prior state.
2. Prompts for (or accepts via --last-action): last action performed this session.
3. Checks whether TOPOLOGY.md was modified since topology_fingerprint.txt was last written.
   If so: recomputes SHA-256 of TOPOLOGY.md + ARCHITECTURE_MAP.md and updates fingerprint.
4. Updates PROVENANCE.md Session Log with:
   ```
   Date | Agent: Claude Code | Last action | Topology drift: yes/no | Next recommended action
   ```
5. Writes updated session_state.json with timestamp, last_action, open_tasks (if any
   were stated in the session), and warm_start_valid: true.

## Before invoking

Before running the engine, ask yourself (and report to the operator):
- Did topology drift this session? (any load-bearing concepts changed?)
- Were any paths rejected that should go to the Graveyard?
- What are the open tasks to carry forward?

Supply these as context when invoking. If open tasks were established during the session,
include them so the engine can write them to session_state.json.

## If engine is unavailable

Manually update:
1. PROVENANCE.md Session Log: append one row — date, agent, last action, drift flag,
   next action.
2. .sovereign/session_state.json: update last_agent, last_timestamp, last_action,
   open_tasks.
3. If TOPOLOGY.md was modified: recompute topology fingerprint manually (SHA-256 of
   TOPOLOGY.md content) and write to .sovereign/topology_fingerprint.txt.

## Report back

Confirm PROVENANCE.md Session Log was updated. State whether topology fingerprint was
refreshed. List the open_tasks written to session_state.json. If any rejected paths
were logged to the Graveyard, name them.
