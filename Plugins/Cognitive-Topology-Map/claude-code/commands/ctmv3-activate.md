---
description: Full CTMv3 workspace activation — runs the complete Phase 0-5 cold start on the current repo
allowed-tools:
  - Bash(python3 -m ctmv3 *)
  - Read
  - Write
  - Edit
argument-hint: "[--force] [--project-root PATH]"
---
# /ctmv3:activate

Full workspace activation. Runs the complete CTMv3 Phase 0-5 cold start sequence on the
project root, producing the full artifact set: TOPOLOGY.md, FAILURE_GRAMMAR.md,
ARCHITECTURE_MAP.md, PROVENANCE.md, AGENTS.md, CLAUDE.md, and the .xyz directories
(.sovereign/, .claude/, .codex/, .github/).

This is the entry command for a repo that has never been CTM-encoded. For repos that
have already been activated, use /ctmv3:warm instead.

## Invocation

```bash
python3 -m ctmv3 activate --json $ARGUMENTS
```

Parse the JSON output. The engine will report the boot state it detected (COLD, WARM, or
PARTIAL) and the artifact list it intends to produce.

## Safety check

Before writing anything, check whether any Tier 1 CTM artifacts already exist:
- .sovereign/ directory
- ARCHITECTURE_MAP.md
- AGENTS.md

If any Tier 1 artifact exists and --force is NOT in $ARGUMENTS, pause and report to the
operator:

> CTMv3 artifacts detected. This repo may already be activated. Pass --force to
> overwrite existing artifacts, or run /ctmv3:warm to continue from the current state.

Do not proceed past this check without explicit confirmation or --force.

## Execution sequence

If boot state is COLD or --force is passed:

1. **Scaffold the Workspace**: Run the CTMv3 engine to lay down the raw template structure.
   ```bash
   python3 -m ctmv3 activate --json $ARGUMENTS
   ```
   This will create `TOPOLOGY.md`, `FAILURE_GRAMMAR.md`, `ARCHITECTURE_MAP.md`, `AGENTS.md`, and `CLAUDE.md` filled with `{{PLACEHOLDER}}` tags.

2. **Phase 0 (Domain Archaeology)**: Use your read tools to examine the config spine (`pyproject.toml`, `package.json`, etc.) and the primary source directories. Extract the dependency map, entry points, and architectural logic.

3. **Phase 1-4 (Template Completion - CRITICAL STEP)**: Open each scaffolded artifact and replace every `{{KEY}}` placeholder with deep insights derived from your reading.
   - **TOPOLOGY.md**: Fill out the 3-7 load-bearing concepts, interface map, and complexity distribution.
   - **FAILURE_GRAMMAR.md**: Define what "wrong" looks like in this specific codebase.
   - **ARCHITECTURE_MAP.md**: Build a navigable traversal map of the directories.
   - **AGENTS.md** and **CLAUDE.md**: Fill in the operational posture.
   *Do not stop until all templates are filled with real findings from the codebase.*

4. **Phase 5 (Session Finalization)**: Run the session close protocol to lock in the new topology fingerprint:
   ```bash
   python3 -m ctmv3 session-close $ARGUMENTS
   ```

## Expected artifacts

After successful activation, the following must exist:
- TOPOLOGY.md (load-bearing concepts, interface map, complexity distribution)
- FAILURE_GRAMMAR.md (pre-failure signatures, adversarial patterns if applicable)
- ARCHITECTURE_MAP.md (traversal map, not a summary)
- PROVENANCE.md (snapshot lineage + first session log entry)
- AGENTS.md (operational posture for all agents)
- CLAUDE.md (Claude Code-specific context)
- .sovereign/session_state.json
- .sovereign/topology_fingerprint.txt
- .claude/settings.json

## Report back

Summarize: which artifacts were created, what the detected project type is (Python/Go/etc.),
what the 3 load-bearing concepts are from TOPOLOGY.md, and the warm start state written to
.sovereign/session_state.json. Flag anything that could not be produced.
