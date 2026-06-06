# Grok Build Configurator Skill

This skill packages the local xAI Grok Build user-guide corpus into an agent-operable configurator. It helps Codex, Grok Build, Claude Code, OpenCode, and other Somnus-compatible runtimes configure, audit, bootstrap, and troubleshoot Grok Build CLI setups without relying on generic CLI advice.

## Somnus staging status

- Canonical staging path: `/home/daeron/Repositories/Somnus-Intellligence-Stack/skills/grok-build-configurator`
- Active local Grok launcher source: `/home/daeron/.local/bin/grok` copies this directory into `/home/daeron/.grok/runtime-home/skills/grok-build-configurator` on launch.
- Runtime posture: one-skill Grok Build mode; MCP, plugins, hooks, agents, compatibility scans, memory, and subagents remain disabled in the isolated runtime.
- Public-clean posture: no `auth.json`, `.env`, sessions, memories, logs, or Python cache artifacts should ship with this package.

## Install for Codex-style skill runtimes

From this directory:

```bash
./scripts/install_codex_skill.sh
```

Default destination:

```text
$HOME/.agents/skills/grok-build-configurator
```

For repo-scoped use, copy the directory into:

```text
<repo>/.agents/skills/grok-build-configurator
```

For Grok Build native use, copy the directory into either global or project skill roots depending on the intended scope:

```text
~/.grok/skills/grok-build-configurator
<repo>/.grok/skills/grok-build-configurator
```

## What is inside

```text
SKILL.md                                      # skill instructions
references/grok-build-configuration-field-guide.md
references/grok-build-command-cheatsheet.md
references/xai-docs/*.md                     # uploaded xAI docs, copied as lazy references
scripts/grok_build_doctor.py                 # non-destructive Grok setup audit
scripts/render_grok_config.py                # render profiles into reviewable files
assets/templates/*.toml                      # config templates
assets/templates/*.sh                        # CI and hook scripts
assets/templates/hooks/git-gh-only/*         # hard allow-list shell hook
agents/openai.yaml                           # optional Codex/OpenAI UI metadata
agents/AGENTS.md                             # project-rule template for Grok project contexts
manifest.json                                # Somnus staging manifest and exclusion hints
```

## Quick local use

Run the doctor from anywhere:

```bash
python3 /path/to/grok-build-configurator/scripts/grok_build_doctor.py --project .
```

Render a profile for review:

```bash
python3 /path/to/grok-build-configurator/scripts/render_grok_config.py daily --out /tmp/grok-daily
python3 /path/to/grok-build-configurator/scripts/render_grok_config.py ci-safe --out /tmp/grok-ci
python3 /path/to/grok-build-configurator/scripts/render_grok_config.py hardened --out /tmp/grok-hardened
```

Then copy the reviewed files into `~/.grok` or your repo.

## Profiles

- `daily`: interactive workstation profile with sane defaults.
- `ci-safe`: headless JSON, narrow permissions, no auto-update.
- `enterprise-oidc`: organization-managed OIDC/proxy baseline.
- `project-mcp`: repo-scoped MCP plus project rules.
- `hardened`: sandbox plus git/gh-only hook and CI script.

## Notes

This package is based on uploaded docs. Before applying it to a machine with a newer Grok Build CLI, verify behavior with:

```bash
grok --version
grok inspect
grok inspect --json
grok models
grok mcp list --json
```

Treat GitHub as the source transport and the Somnus marketplace/registry layer as the installer/discovery surface. Runtime-specific adapters can point Codex, Claude Code, OpenCode, and Grok Build at the same payload while preserving their distinct manifest/config formats.
