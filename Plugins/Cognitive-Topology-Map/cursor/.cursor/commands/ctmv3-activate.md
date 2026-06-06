---
description: Full CTMv3 workspace activation — Phase 0-5 cold-start: domain archaeology, topology, failure grammar, architecture map, sovereign init, and ecosystem directories.
---

Full workspace activation. Runs Phase 0-5 cold-start on the current repo.

WARNING: Creates or overwrites multiple artifact files. If Tier 1 CTMv3 artifacts
already exist (AGENTS.md, ARCHITECTURE_MAP.md, .sovereign/), the command halts and
reports what was found before proceeding. Pass `--force` to overwrite.

## Invocation

```bash
python3 -m ctmv3 activate --json --project-root "$PWD"
```

With force (overwrites existing artifacts):
```bash
python3 -m ctmv3 activate --json --project-root "$PWD" --force
```

Specific .xyz targets only:
```bash
python3 -m ctmv3 activate --json --project-root "$PWD" --dot-targets claude
```

## What activation builds

Phase 0: Domain archaeology — reads config spine, identifies tech stack and entry points.
Phase 1: TOPOLOGY.md — 7-node cognitive map of the codebase.
Phase 2: FAILURE_GRAMMAR.md — pre-failure signatures and failure attractors.
Phase 3: Entry vector analysis — encodes semantic router for agent entry.
Phase 4: PROVENANCE.md — initial snapshot lineage seeding.
Phase 5: Ecosystem artifacts:
  - ARCHITECTURE_MAP.md
  - .sovereign/session_state.json
  - AGENTS.md (if absent)
  - .claude/CLAUDE.md (if Claude Code is primary agent)
  - .github/copilot-instructions.md (if .github/ requested)

## After activation

Run `/ctmv3-fingerprint` to anchor the topology hash. Then close the session with
`/ctmv3-session-close`. The next agent entry will be a WARM_START.
