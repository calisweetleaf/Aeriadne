# DOCTRINE STACK

Load this when the task depends on injected documents, precedence, or first-mission behavior.

## First-mission load order

1. `AGENTS.md`
2. `AGENTS.override.md`
3. `OPSEC.md`
4. `STYLE.md`
5. `MCP_SPEC.md`
6. `default.rules` when permission surfaces matter
7. `tool_manifest.json` when tool catalog or BB7 coverage matters

## File roles

| File | Role |
|---|---|
| `AGENTS.md` | main identity, baseline posture, environment framing |
| `AGENTS.override.md` | active runtime override for workspace-specific turn law |
| `OPSEC.md` | constitutional development and production methodology |
| `STYLE.md` | coding and output discipline |
| `MCP_SPEC.md` | canonical BB7 and MCP tool semantics, especially exo loop behavior |
| `default.rules` | explicit command permission evidence |
| `tool_manifest.json` | authoritative live tool definitions |

## Interpretation rule

Do not flatten these into one blended summary too early. Preserve the role of each file, then derive the joint behavior.

## Missing-file rule

If the operator references `workflows.md` or another injected file that is not present, say so explicitly and request the missing file before making claims that depend on it.
