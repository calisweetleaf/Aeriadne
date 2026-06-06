---
description: Initialize the .xyz agent ecosystem directories (.claude/, .codex/, .github/) for a CTMv3-activated repo.
agent: ctmv3-architect
subtask: true
---

Initialize the agent ecosystem directories — .claude/, .codex/, and optionally .github/.
This is Phase 5 (partial) of the cold-start sequence and is normally called as part of
/ctmv3-activate. Use directly to add or repair missing ecosystem directories in a repo
that already has other CTMv3 artifacts.

Corresponds to SKILL.md [INTEGRATE_AGENT_ECOSYSTEM] and DOT_TOPOLOGY.md.

## Prerequisite

AGENTS.md should exist before .github/ hooks are created — the agent posture defines
what the hooks enforce. If AGENTS.md is absent, the engine will create a minimal one
before building hooks.

```bash
test -f AGENTS.md && echo "present" || echo "absent — will be created"
```

## Safety check

Check which directories already exist:

```bash
test -d .claude && echo ".claude present" || echo ".claude absent"
test -d .codex && echo ".codex present" || echo ".codex absent"
test -d .github && echo ".github present" || echo ".github absent"
```

For any directory that already exists and --force is NOT in $ARGUMENTS: skip that
directory and report it was already present. Do not overwrite existing content.

## Invocation

```bash
python3 -m ctmv3 dot-init --json --project-root "$PWD" $ARGUMENTS
```

## What gets created

.claude/ (if absent):
- settings.json — Claude Code permissions: allows ctmv3 commands, denies rm -rf / sudo

.codex/ (if absent):
- skills/ directory — placeholder for Codex skill installs

.github/ (if absent and project has CI signals in Tier 3 config):
- copilot-instructions.md — repo-wide agent instruction (derived from AGENTS.md)
- instructions/ — per-path agent context files (created empty, populated from TOPOLOGY.md)
- workflows/topology-enforce.yml — CI hook enforcing topology contracts (if CI is active)

## Report back

List each directory and file created. For any directory that was skipped (already
existed), state what was found there. Flag any enforcement hook that could not be
created and why (e.g., no CI config detected, .github/ already has conflicting files).
