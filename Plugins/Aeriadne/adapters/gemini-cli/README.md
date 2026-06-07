# Gemini-CLI Adapter — Aeriadne

Aeriadne projects two skills into Gemini-CLI via the standard extension format:
a `gemini-extension.json` manifest, a `GEMINI.md` context file loaded into every
session, and a `skills/` directory for skill references.

---

## Canonical source

```text
/home/daeron/Repositories/Somnus-Intellligence-Stack/Plugins/Aeriadne
```

## Projection map

| Aeriadne surface                              | Gemini-CLI surface                              |
|:----------------------------------------------|:------------------------------------------------|
| `skills/constitutional-prompt-framework/`     | `aeriadne/skills/cpf/SKILL.md` + GEMINI.md section |
| `skills/aeriadne-marketplace-operator/`       | `aeriadne/skills/mop/SKILL.md` + GEMINI.md section |
| `agents/subagents/*.md`                       | GEMINI.md subagent delegation notes             |
| No native plugin manifest                     | `gemini-extension.json` (extension format)      |

Gemini-CLI extensions do **not** support native subagent spawning or slash command
delegation chains (unlike OpenCode's `agent:` + `subtask:` front-matter). The
approach is:

1. `GEMINI.md` injects the skill content and trigger phrases into every session.
2. Slash commands (TOML) provide structured entry points.
3. `skills/` directory holds SKILL.md files that Gemini reads on demand.

---

## Install

```bash
cd /home/daeron/Repositories/Somnus-Intellligence-Stack/Plugins/Aeriadne/adapters/gemini-cli
bash install.sh
```

The installer copies `aeriadne/` to `~/.gemini/extensions/aeriadne/` and
verifies the extension loads.

After install, **restart Gemini-CLI**. Verify:
```
/extensions list
```
Confirm `aeriadne` appears.

---

## Extension surface

```text
~/.gemini/extensions/aeriadne/
├── gemini-extension.json        extension manifest
├── GEMINI.md                    context loaded into every session
├── commands/aeriadne/
│   ├── cpf.toml                 /aeriadne:cpf — invoke CPF skill
│   ├── audit.toml               /aeriadne:audit — audit a constitution
│   ├── port.toml                /aeriadne:port — port to platform
│   ├── package.toml             /aeriadne:package — run marketplace operator
│   └── validate.toml            /aeriadne:validate — run validation gates
└── skills/
    ├── cpf/SKILL.md             CPF skill reference (copied by install.sh via cp -r)
    └── mop/SKILL.md             Marketplace operator skill reference
```

---

## Gemini-CLI extension caveats (verified 2026-06-07, v0.45.2)

### Commands use TOML, not Markdown

Unlike Claude Code (`.md`) and OpenCode (`.md`), Gemini-CLI extension commands
are TOML files with a `prompt` field. The `prompt` is injected as a model message.

### No native subagent API

Gemini-CLI does not have an `@agent-name` invocation surface in extensions. The
GEMINI.md context teaches the model to act in specialized modes when asked.

### No session-start auto-hook for CPF

Unlike CTMv3's `ctmv3-session-start.sh`, CPF does not need a session-start boot.
The GEMINI.md context is always loaded. Invoke via `/aeriadne:cpf` explicitly.

### Context file is the primary surface

`GEMINI.md` is the most reliable control point. If slash commands conflict with
user/project commands, Gemini-CLI renames them with a dot prefix (`/aeriadne.cpf`).
The GEMINI.md trigger phrases remain effective regardless.

---

## Boundary

- Do not vendor BB7/SovereignMCP into this extension. Sovereign MCP is already
  wired in `~/.gemini/settings.json` via the live server.
- SKILL.md files in `skills/` are copies of the canonical source. Update the
  canonical source first, then re-run `install.sh` to propagate.
- Do not edit installed files directly — edit the adapter source and reinstall.
