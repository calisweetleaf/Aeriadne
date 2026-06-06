---
description: Close a CTMv3 work session — update PROVENANCE.md session log, sync session_state.json, log any topology drift or rejected paths.
agent: ctmv3-architect
subtask: true
---

Close the current CTMv3 work session cleanly. Updates PROVENANCE.md Session Log,
syncs .sovereign/session_state.json, and logs any topology drift or rejected paths
discovered during the session.

Every CTMv3-active session must close cleanly. Agents that skip session close create
stale state that corrupts the next agent's warm start.

## Required parameters

This command requires two arguments:
- `--agent NAME` — the agent identifier for this session (e.g., ctmv3-architect, claude-code)
- `--action SUMMARY` — one-line summary of the last substantive action taken

If either is absent from $ARGUMENTS, pause and ask the operator:
> What agent name should be logged for this session?
> What was the last substantive action taken? (one line)

Do not proceed until both are provided.

## Invocation

```bash
python3 -m ctmv3 session-close --json --project-root "$PWD" $ARGUMENTS
```

## What gets updated

PROVENANCE.md Session Log entry appended:
```
| <date> | <agent> | <last-action> | <topology-drift: yes/no> | <next recommended action> |
```

.sovereign/session_state.json updated:
```json
{
  "last_agent": "<agent>",
  "last_timestamp": "<ISO datetime>",
  "last_action": "<summary>",
  "topology_hash": "<current TOPOLOGY.md hash>",
  "open_tasks": ["<any tasks flagged during session>"],
  "warm_start_valid": true
}
```

If topology drifted during the session:
- Update affected TOPOLOGY.md sections.
- Set topology_hash to new fingerprint in session_state.json.

If a path was rejected during the session:
- Log in PROVENANCE.md Rejected Alternatives (Graveyard) section.

## If engine unavailable

Update the files manually:

```bash
# Append session log to PROVENANCE.md
# Update .sovereign/session_state.json directly
```

Report what was written and flag that the engine was unavailable.

## Report back

Confirm PROVENANCE.md Session Log was updated with the correct entry. State whether
topology drift was detected and logged. State whether any paths were added to the
Graveyard. Confirm session_state.json warm_start_valid is now true.
