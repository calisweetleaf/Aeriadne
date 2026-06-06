---
description: Build the .xyz directory ecosystem — .claude/, .codex/, .github/ with agent context files
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
  - Write
  - Edit
argument-hint: "[--project-root PATH] [--skip-github] [--force]"
---
# /ctmv3:dot-init

Build the .xyz directory ecosystem. Produces .claude/settings.json, CLAUDE.md,
.github/copilot-instructions.md, .github/instructions/ per-path files for DENSE modules,
and optionally .github/workflows/ enforcement gates.

Maps to: DOT_TOPOLOGY.md § Build sequence + BOOT_PROTOCOL.md Phase 5 ecosystem artifact
construction.

## Prerequisites

TOPOLOGY.md and ARCHITECTURE_MAP.md must exist. The .xyz artifacts are derived from the
topology — building them before topology is complete produces empty or wrong hooks.

```bash
test -f TOPOLOGY.md && test -f ARCHITECTURE_MAP.md && echo "ok" || echo "prereqs missing"
```

If prerequisites are missing, stop. Do not build .github/ before TOPOLOGY.md is complete.

## Invocation

```bash
python3 -m ctmv3 dot-init --json $ARGUMENTS
```

## What the engine produces

Always:
- .claude/settings.json — permissions allow/deny list seeded from TOPOLOGY.md constraints
- CLAUDE.md at repo root — Claude Code-specific operational context:
    1. What this project is (from TOPOLOGY.md domain)
    2. Where the traversal map is (→ ARCHITECTURE_MAP.md)
    3. Available tools and how to call them
    4. Boot protocol summary (cold/warm check, .sovereign/ location)
    5. Operations requiring explicit Daeron confirmation
- .github/copilot-instructions.md — repo-wide agent instruction from TOPOLOGY.md summary

For DENSE topology nodes (where complexity concentrates):
- .github/instructions/{module}.instructions.md — per-path context injected when working
  in that module's directory

Unless --skip-github is passed:
- .github/workflows/topology-enforce.yml — CI gate enforcing TOPOLOGY.md constraints
- .pre-commit-config.yaml — local enforcement for wrapper sizes and provenance reminders

## Safety check

If any target file already exists and --force is not in $ARGUMENTS, report the list of
existing files and ask which should be overwritten. Default behavior: skip existing files,
create missing ones.

## Report back

List every file created or updated. For each .github/instructions/ file created, state
which module it covers and what the injected context focuses on. Flag any file that was
skipped because it already existed.
