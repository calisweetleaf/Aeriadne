# Current Codex Configuration Surfaces — 2026-06-04

This reference is for configuring Codex itself, not Hermes. Verify live state before applying because Codex is moving quickly.

## Official sources checked

- Codex manual helper: `/home/daeron/.codex/skills/.system/openai-docs/scripts/fetch-codex-manual.mjs`
- Manual cache: `/tmp/openai-docs-cache/codex-manual.md`
- Official docs:
  - https://developers.openai.com/codex/config-basic
  - https://developers.openai.com/codex/config-advanced
  - https://developers.openai.com/codex/guides/agents-md
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/codex/mcp
  - https://developers.openai.com/codex/hooks
  - https://developers.openai.com/codex/permissions
  - https://developers.openai.com/codex/plugins
  - https://developers.openai.com/codex/memories
  - https://developers.openai.com/codex/subagents

## Local runtime snapshot

Observed 2026-06-04T17:20:00-05:00 in `/home/daeron/.codex` after the minimal-loadout pass:

- Host: Ubuntu/Kubuntu 24.04.4 LTS, bash.
- Codex command: `/home/daeron/.nvm/versions/node/v24.14.0/bin/codex`.
- Codex version: `codex-cli 0.137.0`.
- `codex --strict-config doctor --json`: `overallStatus = ok`; unrestricted filesystem and network enabled; approval policy Never.
- Auth: ChatGPT file tokens configured; do not print `auth.json`.
- MCP servers enabled: `SovereignMCP`, `codegraph`, `mentat`.
- Plugins enabled locally: `mentat@local` and `ctmv3-workspace-activator@local` only.
- Standalone custom skill directories: `academic-whitepaper-engine` and `codex-config-topology` only.
- Bundled system skill `SKILL.md` files are archived under `/home/daeron/.codex/skills.archive/20260604_1715_system_skill_registry_suppression/` to keep their registry entries out of prompt context while preserving scripts/resources on disk.
- Project-local `/home/daeron/.codex/.codex/config.toml` sets `project_doc_max_bytes = 0` so the CODEX_HOME repo does not double-load `AGENTS.override.md`; global user config still keeps project docs enabled elsewhere.
- Features of interest: `plugins=true`, `hooks=true`, `memories=true`, `multi_agent=true`, `browser_use=true`, `computer_use=true`, `shell_tool=true`, `unified_exec=true`, `goals=true`; `multi_agent_v2=false`, `enable_fanout=false`, `child_agents_md=false`.

## Configuration precedence

Official order, highest to lowest:

1. CLI flags and `--config` overrides.
2. Project `.codex/config.toml` files, root down to current directory, only in trusted projects; closest wins.
3. Profile files selected by `--profile profile-name`, now `~/.codex/profile-name.config.toml`.
4. User config `~/.codex/config.toml`.
5. System config `/etc/codex/config.toml` on Unix if present.
6. Built-in defaults.

Do not use stale `[profiles.<name>]` assumptions without verifying current docs.

## User config and project config

User config owns provider/auth-adjacent behavior and global runtime defaults.

Project config loads only in trusted projects. Relative paths in project config resolve relative to that project's `.codex/` directory. Project-local config cannot override provider/auth/profile/notification/telemetry-style keys such as provider definitions, `profile`, `profiles`, base URLs, notification commands, or telemetry.

## AGENTS and project docs

Official discovery:

- Global scope reads `CODEX_HOME/AGENTS.override.md` if it exists, otherwise `CODEX_HOME/AGENTS.md`. Only the first non-empty file at this global level is used.
- Project scope walks from project root to current directory. In each directory it checks `AGENTS.override.md`, then `AGENTS.md`, then names in `project_doc_fallback_filenames`.
- Codex includes at most one file per directory.
- Files closer to the current directory appear later and can override earlier guidance.
- Loading stops at `project_doc_max_bytes`.

Implication for Daeron's desired Hermes-like stack: `MEMORY.md`, `CONTEXT.md`, `USER.md`, and `SOUL.md` are not automatically all loaded just because they exist. They must be selected by discovery, explicitly read by operating doctrine, injected by hooks, or summarized in an aggregator file.

## Skills

Skills are directories containing `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`. Codex loads only a compact skill list initially and reads a full skill only when invoked explicitly or matched implicitly by description. Keep descriptions clear and front-loaded.

Skill locations include repo `.agents/skills`, user `$HOME/.agents/skills`, admin `/etc/codex/skills`, and system bundled skills. Local authoring can use symlinks, but validate actual paths.

## MCP

MCP gives Codex external tools and context. Current supported transports include STDIO and streamable HTTP. HTTP servers can use bearer tokens or OAuth where supported. MCP server instructions are read alongside server tools; keep the first 512 characters self-contained.

Config lives under `[mcp_servers.<name>]` in `config.toml`; plugin-provided MCP servers are controlled under plugin config. Use `codex mcp list --json` for clean machine-readable state.

For BB7/Sovereign, Codex config can make MCP always available and set tool approval policies, but it cannot make BB7 an OpenAI-native built-in tool without runtime/source support.

## Hooks

Hooks run lifecycle shell commands. Active sources can include user and project `hooks.json` plus inline `[hooks]` tables. Multiple matching hooks can run; command hooks for an event can execute concurrently. Project hooks require trusted projects.

Schema gotcha: hook JSON emitted to stdout must match the event schema. For additional context, include the matching `hookSpecificOutput.hookEventName` where required. Events that do not allow hook-specific output should emit nothing.

## Memories

Official Codex Memories are off by default and can be enabled in `[features]` with `memories = true`. They are a helpful local recall layer, not binding governance. Required rules belong in `AGENTS.md`, checked-in docs, or explicit hooks/skills.

Daeron's environment also has BB7/Sovereign memory; keep BB7 persistence rooted at `/home/daeron/Somnus-MCP/data`.

## Permissions and sandboxing

Codex has older sandbox settings and newer beta permission profiles. In current local config, older sandbox mode is active: danger/full unrestricted filesystem with network enabled and approval Never. Permission profiles are not the same as sandbox mode; do not mix or assume composition.

Built-in permission profiles include `:read-only`, `:workspace`, and `:danger-full-access`. Use `:danger-full-access` only when broad local access is intentional.

## Subagents

Subagents are useful for manual read-heavy exploration, test triage, summarization, and non-overlapping workstreams. They are not a substitute for a stable control plane. Avoid parallel writes unless explicitly scoped.

## App server and OAuth boundary

Codex app-server/runtime surfaces can exist separately from CLI. Do not enable/migrate app-server, remote MCP OAuth, or cross-provider account flows unless Daeron explicitly authorizes the account boundary change.
