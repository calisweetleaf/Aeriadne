---
description: Warm start — resume a CTMv3-encoded session. Reads PROVENANCE.md, checks topology validity, and runs targeted archaeology on drifted areas only.
agent: ctmv3-architect
subtask: true
---

Warm session resume. Runs the BOOT_PROTOCOL.md warm start protocol: reads PROVENANCE.md,
validates topology currency, identifies drift, and performs targeted archaeology on changed
areas only. Does not rebuild from scratch unless --force-full is passed.

Use this command at the start of any work session in a repo that has already been
CTMv3-activated. If boot state is unknown, run /ctmv3-boot first.

## Prerequisite check

Verify at least one Tier 1 artifact exists before invoking the engine:

```bash
test -d .sovereign || test -f ARCHITECTURE_MAP.md || test -f AGENTS.md \
  && echo "Tier 1 present" || echo "No Tier 1 artifacts — run /ctmv3-activate first"
```

If no Tier 1 artifacts are found, halt and direct the operator to /ctmv3-activate.

## Invocation

```bash
python3 -m ctmv3 warm --json --project-root "$PWD" $ARGUMENTS
```

## What the engine does

1. Reads PROVENANCE.md Session Log — extracts last agent, last action, timestamp,
   and open tasks.
2. Runs three warm validity checks (BOOT_PROTOCOL.md Section 3.1):
   - Topology still valid? New code added since last encoding?
   - Provenance coherent? Session log consistent with current AGENTS.md and
     ARCHITECTURE_MAP.md?
   - No rejected path in play? Current task absent from PROVENANCE.md Graveyard?
3. If all three pass: reports warm state, last session summary, and open tasks.
4. If any check fails: runs partial archaeology targeting the delta only. Updates
   affected TOPOLOGY.md sections. Logs the delta in PROVENANCE.md Session Log.
   Does not rebuild artifacts that are not stale.

## Expected JSON output

```json
{
  "warm_valid": true,
  "last_agent": "ctmv3-architect",
  "last_action": "topology draft committed, failure grammar pending",
  "last_timestamp": "2025-01-15T14:32:00Z",
  "open_tasks": ["build FAILURE_GRAMMAR.md", "wire .github/ hooks"],
  "topology_drifted": false,
  "drift_areas": [],
  "partial_archaeology_ran": false,
  "artifacts_updated": []
}
```

## If engine unavailable

Read .sovereign/session_state.json and PROVENANCE.md directly:

```bash
cat .sovereign/session_state.json 2>/dev/null || echo "no session state"
```

Extract last_action and open_tasks manually and report them. Flag that the engine
was unavailable and partial archaeology was skipped.

## Report back

State whether warm start was clean or required partial archaeology. If drift was
detected, name the affected topology areas. List open tasks from the last session.
State what was updated and what the current session should continue from.
