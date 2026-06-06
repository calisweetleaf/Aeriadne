---
description: Initialize agent ecosystem directories — .claude/, .codex/, and .github/ — after TOPOLOGY.md exists. Skips any directory that already exists unless --force is passed.
---

Initialize the agent ecosystem directories for the current repo.

Directories created (by target):
- `claude`: `.claude/CLAUDE.md` — Claude Code session context
- `codex`: `.codex/skills/ctmv3/` — Codex skill symlink
- `github`: `.github/copilot-instructions.md` — Copilot instructions
- `all`: all of the above

Run this after TOPOLOGY.md is complete. The agent posture (AGENTS.md) defines what
the directories encode — creating directories before the posture exists produces
boilerplate without context.

## Invocation

```bash
# Initialize all directories
python3 -m ctmv3 dot-init --json --project-root "$PWD"

# Initialize only .claude/
python3 -m ctmv3 dot-init --json --project-root "$PWD" --target claude

# Force overwrite of existing files
python3 -m ctmv3 dot-init --json --project-root "$PWD" --force
```

## Idempotent

Existing files are skipped unless `--force` is passed. Running twice without `--force`
is safe — the second run reports `skipped` for all files that already exist.
