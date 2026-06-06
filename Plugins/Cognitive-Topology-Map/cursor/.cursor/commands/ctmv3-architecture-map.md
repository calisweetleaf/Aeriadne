---
description: Build or rebuild ARCHITECTURE_MAP.md — the traversal map that answers "where is X" without requiring a guide. Requires TOPOLOGY.md to exist first.
---

Build or rebuild ARCHITECTURE_MAP.md. This is the traversal map for the codebase —
the document that answers "where is X implemented" for any agent or human entering
the repo for the first time.

Requires TOPOLOGY.md to exist. Run `/ctmv3-activate` first if TOPOLOGY.md is absent.

## Invocation

```bash
python3 -m ctmv3 architecture-map --json --project-root "$PWD"
```

Overwrite existing (e.g. after topology drift):
```bash
python3 -m ctmv3 architecture-map --json --project-root "$PWD" --force
```

Extract project name from TOPOLOGY.md header:
```bash
python3 -m ctmv3 architecture-map --json --project-root "$PWD" --from-topology
```

## When to run this

- After `/ctmv3-activate` completes the topology build.
- After `/ctmv3-fingerprint` reports `drift_detected` — the map may be stale.
- After significant structural changes to the codebase (new modules, renamed dirs).

## Output

The `status` field in the JSON output will be:
- `written` — new map written to ARCHITECTURE_MAP.md
- `skipped` — existing file preserved (pass `--force` to overwrite)

After the map is written, run `/ctmv3-session-close` to anchor the session state.
