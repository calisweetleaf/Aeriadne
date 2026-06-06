---
description: Initialize or reinitialize .sovereign/ — the session continuity anchor directory for CTMv3.
agent: ctmv3-architect
subtask: true
---

Initialize the .sovereign/ directory — CTMv3's session continuity anchor. Creates
session_state.json, topology_fingerprint.txt, and optionally golden_paths.json.
This is Phase 5 (partial) of the cold-start sequence; it should normally be called
via /ctmv3-activate rather than directly.

Use directly when .sovereign/ is absent or corrupted in an otherwise activated repo.

## Safety check

If .sovereign/ already exists and --force is NOT in $ARGUMENTS:

```bash
test -d .sovereign && echo "exists" || echo "absent"
```

If it exists:
> .sovereign/ already exists. Contents:
> (list .sovereign/ directory)
> Pass --force to reinitialize, or read session_state.json to check current state.

Do not overwrite without --force.

## Invocation

```bash
python3 -m ctmv3 sovereign-init --json --project-root "$PWD" $ARGUMENTS
```

## What gets created

.sovereign/ directory containing:

- session_state.json — initialized state:
  ```json
  {
    "boot_state": "COLD | WARM",
    "last_agent": null,
    "last_timestamp": null,
    "last_action": null,
    "topology_hash": "<fingerprint of TOPOLOGY.md if present>",
    "open_tasks": [],
    "warm_start_valid": false
  }
  ```
- topology_fingerprint.txt — hash of current TOPOLOGY.md content for drift detection.
  If TOPOLOGY.md does not exist yet, this file is seeded empty and flagged for update.
- golden_paths.json — seeded from existing workflows if bb7 system is present, or
  created empty for later population.
- PROVENANCE.md symlink or copy — if PROVENANCE.md exists at repo root, link it here
  as well so session state and provenance are co-located.

## Report back

Confirm .sovereign/ was created. List each file created. State the topology hash
written to topology_fingerprint.txt and whether golden_paths.json was seeded with
existing workflow data or initialized empty.
