---
description: "Full CTMv3 workspace activation — runs the complete Phase 0-5 cold-start on the current project root. DESTRUCTIVE: creates multiple artifact files. Review scope before confirming."
agent: ctmv3-architect
subtask: true
---

OPERATOR WARNING: This command runs the full CTMv3 cold-start sequence. It will create
or overwrite: TOPOLOGY.md, FAILURE_GRAMMAR.md, ARCHITECTURE_MAP.md, PROVENANCE.md,
AGENTS.md, CLAUDE.md, .sovereign/, .claude/, and optionally .github/ and .codex/.
If any Tier 1 CTMv3 artifacts already exist (AGENTS.md, ARCHITECTURE_MAP.md,
.sovereign/), you must pass --force or this command will halt and ask you to confirm.

Do not proceed past the safety check below without explicit operator acknowledgment.

## Safety check

Before invoking any engine command, scan for existing Tier 1 artifacts:

```bash
test -f AGENTS.md && echo "AGENTS.md present" || echo "absent"
test -f ARCHITECTURE_MAP.md && echo "ARCHITECTURE_MAP.md present" || echo "absent"
test -d .sovereign && echo ".sovereign/ present" || echo "absent"
```

If any Tier 1 artifact exists and `--force` is NOT in $ARGUMENTS:

> HALT. CTMv3 Tier 1 artifacts detected. This repo may already be activated.
> Pass --force to overwrite, or run /ctmv3-warm to resume from current state.
> Confirm you want to proceed before continuing.

Wait for operator confirmation before proceeding.

## Invocation

```bash
python3 -m ctmv3 activate --json --project-root "$PWD" $ARGUMENTS
```

Parse the JSON output. The engine reports detected boot state (COLD, WARM, PARTIAL)
and the artifact list it intends to produce.

## Execution sequence (if COLD_START or --force)

1. Discovery scan (read-only): scan root-level config spine, .xyz directories,
   AGENTS.md / CLAUDE.md if present. Build signal inventory.

2. Read all Tier 3 config files (pyproject.toml, go.mod, Cargo.toml, package.json,
   manifest.json). Extract dependency map and entry points. Do not execute them.

3. Run each phase in order, verifying output before proceeding:
   ```bash
   python3 -m ctmv3 topology --json --project-root "$PWD" $ARGUMENTS
   python3 -m ctmv3 failure-grammar --json --project-root "$PWD" $ARGUMENTS
   python3 -m ctmv3 architecture-map --json --project-root "$PWD" $ARGUMENTS
   python3 -m ctmv3 sovereign-init --json --project-root "$PWD" $ARGUMENTS
   python3 -m ctmv3 dot-init --json --project-root "$PWD" $ARGUMENTS
   ```

4. After each phase, verify the expected output file was created:
   ```bash
   test -f TOPOLOGY.md && echo "OK" || echo "MISSING — halt"
   ```
   If any expected file is missing, report the failure and stop immediately.

## Expected artifacts after successful activation

- TOPOLOGY.md
- FAILURE_GRAMMAR.md
- ARCHITECTURE_MAP.md
- PROVENANCE.md
- AGENTS.md
- CLAUDE.md
- .sovereign/session_state.json
- .sovereign/topology_fingerprint.txt
- .claude/settings.json

## Report back

State: which artifacts were created, detected project type (Python/Go/Rust/etc.),
the 3 load-bearing concepts identified in TOPOLOGY.md, the warm start state written
to .sovereign/session_state.json, and any artifact that could not be produced with
the reason.
