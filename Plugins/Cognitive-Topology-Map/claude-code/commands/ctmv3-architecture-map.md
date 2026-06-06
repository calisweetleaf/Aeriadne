---
description: Build or rebuild ARCHITECTURE_MAP.md — the agent-navigable traversal map for the repo
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
  - Write
  - Edit
argument-hint: "[--project-root PATH] [--force]"
---
# /ctmv3:architecture-map

Build ARCHITECTURE_MAP.md — the traversal-map artifact that answers "where is X" for any
agent entering the repo. This is not a summary or README replacement. It is a structured
navigation document: question-oriented entry points, module ownership map, and path routing
from any task type to the relevant files.

Maps to: SKILL.md [BUILD_ARCHITECTURE_MAP] → BOOT_PROTOCOL.md Phase 5 artifact.

## Prerequisite

TOPOLOGY.md must exist and be non-empty. The traversal map is derived from the topology.
If TOPOLOGY.md is absent or was never built, run /ctmv3:activate first.

Check:
```bash
test -f TOPOLOGY.md && echo "present" || echo "absent"
```

If absent, stop and tell the operator to run /ctmv3:activate first.

## Invocation

```bash
python3 -m ctmv3 architecture-map --json $ARGUMENTS
```

## What the engine produces

ARCHITECTURE_MAP.md must contain at minimum:
- ROOT node: what this repo is in two sentences
- At least 3 branch nodes: major logical areas (e.g., API layer, core engine, tests)
- Entry vector table: task type → relevant directory/file → first file to read
- Mermaid dependency diagram (mandatory for repos with 4+ top-level modules)
- "Where is X" index: common agent questions → answer paths

The map should answer these questions without requiring further exploration:
- Where is the main entry point?
- Where do I find the tests?
- Where is the configuration loaded?
- Where is the error handling concentrated?
- What files must not be modified without careful review?

## Safety check

If ARCHITECTURE_MAP.md already exists and --force is not in $ARGUMENTS, report:
> ARCHITECTURE_MAP.md exists. Pass --force to rebuild, or read the existing map first.

Do not overwrite without --force.

## Report back

Confirm ARCHITECTURE_MAP.md was written. State: number of top-level nodes in the map,
whether a Mermaid diagram was produced, and what the three highest-complexity areas are
(DENSE nodes in the traversal map).
