---
description: Build or rebuild ARCHITECTURE_MAP.md — the agent-navigable traversal map that answers "where is X" without a guide.
agent: ctmv3-architect
subtask: true
---

Build ARCHITECTURE_MAP.md — the traversal map artifact for the repo. Not a summary.
Not a README replacement. A structured navigation document: question-oriented entry
points, module ownership map, and routing from any task type to the relevant files.

Maps to: SKILL.md [BUILD_ARCHITECTURE_MAP] and BOOT_PROTOCOL.md Phase 5 artifact.

## Prerequisite

TOPOLOGY.md must exist. The traversal map is derived from the topology. Without it
the map has no basis.

```bash
test -f TOPOLOGY.md && echo "present — proceed" || echo "absent — run /ctmv3-activate first"
```

If TOPOLOGY.md is absent, halt and direct the operator to /ctmv3-activate.

## Safety check

If ARCHITECTURE_MAP.md already exists and --force is NOT in $ARGUMENTS:

```bash
test -f ARCHITECTURE_MAP.md && echo "exists" || echo "absent"
```

If it exists:
> ARCHITECTURE_MAP.md already exists. Pass --force to rebuild, or read the existing
> map first to determine whether it needs updating.

Do not overwrite without --force.

## Invocation

```bash
python3 -m ctmv3 architecture-map --json --project-root "$PWD" $ARGUMENTS
```

## What the engine must produce

ARCHITECTURE_MAP.md must contain at minimum:
- ROOT node: what this repo is in two sentences
- At least 3 branch nodes: major logical areas (API layer, core engine, tests, etc.)
- Entry vector table: task type → relevant directory/file → first file to read
- Mermaid dependency diagram (mandatory if 4+ top-level modules)
- "Where is X" index: common agent questions mapped to answer paths

The map must answer these questions without requiring further exploration:
- Where is the main entry point?
- Where are the tests?
- Where is configuration loaded?
- Where is error handling concentrated?
- What files must not be modified without careful review?

## Report back

Confirm ARCHITECTURE_MAP.md was written. State: number of top-level nodes in the map,
whether a Mermaid diagram was produced, the three highest-complexity areas (DENSE
nodes), and whether the "Where is X" index covers at least 5 common entry questions.
