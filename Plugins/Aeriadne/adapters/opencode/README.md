# OpenCode Adapter — Aeriadne

Aeriadne projects two skills into OpenCode via the standard OpenCode agent and command
surface. This adapter is a production install guide, not a stub.

---

## Canonical source

```text
/home/daeron/Repositories/Somnus-Intellligence-Stack/Plugins/Aeriadne
```

OpenCode does not consume `plugin.json` natively. The projection routes are:

| Aeriadne surface          | OpenCode surface                            |
|:--------------------------|:--------------------------------------------|
| `skills/constitutional-prompt-framework/` | `~/.config/opencode/agents/aeriadne-cpf.md` + commands |
| `skills/aeriadne-marketplace-operator/`   | `~/.config/opencode/agents/aeriadne-mop.md` + commands |
| `agents/subagents/*.md`                   | `~/.config/opencode/agents/aeriadne-*.md`   |
| No native plugin manifest                 | N/A — OpenCode does not parse `plugin.json` |

---

## Install scope

**Global** (all projects): `~/.config/opencode/`  
**Project-local** (single repo): `.opencode/` in the project root

For Aeriadne, prefer **global** — CPF and marketplace-operator are cross-repo skills,
not single-project tools.

```bash
# Project-local (default):
bash install.sh
# Global:
bash install.sh global
```

Run `install.sh` with no arguments for project-local install (`.opencode/` in current directory), or pass `global` for system-wide install (`~/.config/opencode/`).

---

## What gets installed

```text
~/.config/opencode/
├── agents/
│   ├── aeriadne-cpf.md               # constitutional-prompt-framework subagent
│   ├── aeriadne-mop.md               # aeriadne-marketplace-operator subagent
│   ├── aeriadne-prompt-architect.md  # subagent: prompt-architect
│   ├── aeriadne-package-cartographer.md # subagent: package-cartographer
│   ├── aeriadne-registry-scribe.md   # subagent: registry-scribe
│   ├── aeriadne-release-sentinel.md  # subagent: release-sentinel
│   └── aeriadne-compatibility-auditor.md # subagent: compatibility-auditor
└── commands/
    ├── aeriadne-cpf.md               # /aeriadne-cpf slash command
    ├── aeriadne-audit.md             # /aeriadne-audit slash command
    ├── aeriadne-port.md              # /aeriadne-port slash command
    ├── aeriadne-package.md           # /aeriadne-package slash command
    └── aeriadne-validate.md          # /aeriadne-validate slash command
```

---

## OpenCode schema assumptions (verified 2026-06-07)

### Agent front-matter

```yaml
---
description: <string>   # required — shown in @ autocomplete
mode: subagent           # required for @-invocable agents
model: <provider/id>     # optional — defaults to session model
temperature: <0.0-1.0>  # optional
permission:
  read: allow|ask|deny
  edit: allow|ask|deny
  write: allow|ask|deny
  bash:
    "*": deny
    "pattern": allow
  glob: allow|ask|deny
  grep: allow|ask|deny
  list: allow|ask|deny
  webfetch: allow|ask|deny
---
```

The `tools:` key is **deprecated**. This adapter uses `permission:`.

### Command front-matter

```yaml
---
description: <string>    # required — shown in / autocomplete
agent: <agent-name>      # optional — delegates to named agent
subtask: true            # optional — runs in subtask context
---
```

`$ARGUMENTS` in the command body is replaced with text passed after the command name.

---

## Verification after install

```bash
# Confirm agents are visible
# In opencode TUI: type @ and look for aeriadne-cpf, aeriadne-mop
# Or check file system:
ls ~/.config/opencode/agents/aeriadne-*.md
ls ~/.config/opencode/commands/aeriadne-*.md
```

Restart OpenCode after install — agents and commands are loaded at startup.

---

## Boundary

- This adapter **projects** skills into OpenCode; it does not copy skill source files.
- The canonical source remains `Plugins/Aeriadne/skills/`.
- `plugin.json`, `.codex-plugin/`, and `.claude-plugin/` are not relevant to OpenCode.
- Do not vendor BB7/SovereignMCP into this adapter — Sovereign MCP is already wired
  in `~/.config/opencode/opencode.jsonc` via the live server at `/home/daeron/Somnus-MCP`.
- Keep the canonical SKILL.md files as the authoritative content source. Agent `.md` files
  in OpenCode are projections, not authoring targets.

---

## Known gaps

- OpenCode has no native plugin manifest registry — no equivalent of Codex's `plugin list`.
- No version pinning or update channel — updating means re-running `install.sh`.
- No session-start hook for auto-loading CPF context on boot (unlike CTMv3's `plugin/ctmv3.ts`).
  The SKILL.md content is embedded in each agent `.md` file directly.
