---
description: Run the CTMv3 boot protocol — determine cold/warm/partial state in under 60 seconds. Read-only. Always the first step for any repo entry task.
---

Boot state check. Runs the BOOT_PROTOCOL.md discovery sequence to determine whether
the current repo is COLD, WARM, or PARTIAL. Read-only — writes nothing.

This is the mandatory first step before any CTMv3 work session. The output determines
which branch the session takes.

## Invocation

```bash
python3 -m ctmv3 boot --json --project-root "$PWD"
```

## What the engine checks

Tier 1 signals (any one means CTMv3 has been run here):
- .sovereign/ directory
- ARCHITECTURE_MAP.md at project root
- .claude/CLAUDE.md
- AGENTS.md at project root

Tier 2 signals (partial CTMv3 or related tooling):
- .github/copilot-instructions.md
- .codex/skills/
- PROVENANCE.md at repo root
- manifest.json
- golden_paths.json

Tier 3 signals (config spine — read for archaeology regardless of boot state):
- pyproject.toml, go.mod, Cargo.toml, package.json, *.toml/*.yaml/*.json at root

## Branch determination and agent guidance

- COLD — no Tier 1 signals. Repo is cold. Recommend: `/ctmv3-activate`
- WARM (valid) — Tier 1 signals present, PROVENANCE.md readable, last session recent.
  Report last session summary and open tasks. Recommend: `/ctmv3-warm`
- WARM (stale) — artifacts present but topology may have drifted.
  Recommend: `/ctmv3-warm`
- PARTIAL — some Tier 1 signals present, others absent.
  Recommend: `/ctmv3-activate` to complete the artifact set.

## If engine unavailable

```bash
ls -la .sovereign/ 2>/dev/null || echo ".sovereign absent"
test -f AGENTS.md && echo "AGENTS.md present" || echo "AGENTS.md absent"
test -f ARCHITECTURE_MAP.md && echo "ARCHITECTURE_MAP.md present" || echo "absent"
```

## Report back

State the boot result in one line. List Tier 1 signals found. If WARM, summarize the
last session and open tasks. State the recommended next command.
