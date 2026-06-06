---
description: Close the current work session cleanly — update PROVENANCE.md Session Log and sync .sovereign/session_state.json. Mandatory at session end.
---

Close the current work session cleanly.

Every CTMv3-active session must close cleanly. Sessions that are not closed create
stale state that corrupts the next agent's warm start. The close command:

1. Recomputes the topology fingerprint and writes it to `.sovereign/topology_fingerprint.txt`
2. Updates `.sovereign/session_state.json` with: last agent, last action, topology hash, warm_start_valid=true
3. Appends a row to PROVENANCE.md Session Log with: date, agent, action, topology drift flag, next recommended action

## Invocation

```bash
python3 -m ctmv3 session-close \
  --json \
  --project-root "$PWD" \
  --agent "Cursor" \
  --action "description of what was accomplished this session" \
  --next-action "description of what the next session should do"
```

If topology changed this session, add `--topology-drift`:
```bash
python3 -m ctmv3 session-close \
  --json \
  --project-root "$PWD" \
  --agent "Cursor" \
  --action "rebuilt TOPOLOGY.md after major refactor" \
  --next-action "update ARCHITECTURE_MAP.md to reflect new structure" \
  --topology-drift
```

## Required fields

- `--agent`: Your agent identifier (e.g. "Cursor", "cursor-composer", "Claude Code")
- `--action`: What was accomplished this session (specific, not generic)
- `--next-action`: Recommended starting point for the next agent session

## After session close

The next `/ctmv3-boot` will find WARM_START. The next `/ctmv3-warm` will load the
session state and report the last action and open tasks.
