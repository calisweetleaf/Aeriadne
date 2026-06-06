---
description: Run the CTMv3 boot protocol — determine cold/warm/partial state in < 60 seconds
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
argument-hint: "[--project-root PATH]"
---
# /ctmv3:boot

Boot state check. Runs the BOOT_PROTOCOL.md discovery sequence to determine whether the
current repo is in COLD, WARM, or PARTIAL state. Read-only — does not write anything.

This is the mandatory first step for any repo entry task. The output determines which
branch the session takes.

## Invocation

```bash
python3 -m ctmv3 boot --json $ARGUMENTS
```

## What the engine checks

The engine scans for CTM presence signals in three tiers:

Tier 1 (strong signals — any one means CTM has been run):
- .sovereign/ directory
- ARCHITECTURE_MAP.md
- .claude/CLAUDE.md
- AGENTS.md

Tier 2 (supporting signals — partial CTM or related tooling):
- .github/copilot-instructions.md
- .codex/skills/
- PROVENANCE.md at repo root
- manifest.json
- golden_paths.json

Tier 3 (config spine — always read for archaeology):
- pyproject.toml, go.mod, Cargo.toml, package.json, *.toml/*.yaml/*.json at root

## Output parsing

The JSON output will contain:

```json
{
  "boot_state": "COLD | WARM | PARTIAL",
  "tier1_signals": [...],
  "tier2_signals": [...],
  "tier3_signals": [...],
  "provenance_present": true | false,
  "manifest_present": true | false,
  "last_session": "date + last action, or null",
  "warm_valid": true | false,
  "warm_validity_reason": "string if not valid"
}
```

## Branch determination

Based on output:

- COLD — no Tier 1 signals. Tell the operator: repo is cold. Recommend /ctmv3:activate.
- WARM (valid) — Tier 1 signals present, PROVENANCE.md readable, last session < 30 days.
  Tell the operator what the last session recorded and what the open tasks are.
- WARM (stale) — artifacts present but topology may have drifted or PROVENANCE.md session
  log is stale. Tell the operator which signals failed warm validity. Recommend
  /ctmv3:warm to run targeted archaeology.
- PARTIAL — some Tier 1 signals present, others missing. List what is present and what
  is absent. Recommend /ctmv3:activate --force to complete the artifact set.

## Report back

State the boot result in one line, then list: Tier 1 signals found, last session summary
(if warm), and the recommended next command.
