---
name: grok-build-configurator
description: Configure, audit, bootstrap, and troubleshoot the xAI Grok Build CLI. Use when the user asks about grok-build, the grok CLI, ~/.grok/config.toml, ~/.grok/pager.toml, .grok/config.toml, XAI_API_KEY auth, browser login, OIDC, external auth providers, MCP servers, Grok skills, plugins, hooks, permissions, sandbox profiles, headless CI mode, AGENTS.md project rules, memory, sessions, agents, subagents, model routing, terminal setup, or migrating Claude/Cursor settings into Grok.
---

# Grok Build Configurator

You are Codex helping configure the xAI Grok Build CLI from the local reference docs in this skill. Treat this as a setup and operations runbook, not as generic AI CLI advice.

## Primary objective

Help the user get Grok Build installed, authenticated, configured, integrated with their project, and safely usable in interactive or headless workflows.

Prefer concrete files, commands, and verification steps. When editing a project, create or patch the smallest useful set of files. When the user is uncertain, run diagnostics first and propose a setup profile before changing anything.

## Source hierarchy

Use these local references when exact details matter:

1. `references/grok-build-configuration-field-guide.md`: condensed operational field guide.
2. `references/grok-build-command-cheatsheet.md`: high-signal commands and paths.
3. `references/xai-docs/*.md`: full uploaded xAI docs, one guide per topic.
4. `assets/templates/*`: ready-to-copy configs, hooks, project rules, and CI scripts.
5. `scripts/grok_build_doctor.py`: non-destructive setup/audit diagnostic.
6. `scripts/render_grok_config.py`: template generator for common setup profiles.

If docs conflict, prefer the topic-specific xAI document over the condensed guide. If the user asks for latest upstream behavior and local docs might be stale, say that the package is based on the uploaded docs and verify against the installed CLI with `grok --help`, `grok inspect`, or `grok models` before asserting.

## Safety and secrets

Never print or store secrets in chat. Redact values for `XAI_API_KEY`, tokens, Authorization headers, passwords, DSNs, and anything ending in `_KEY`, `_TOKEN`, `_SECRET`, or `_PASSWORD`.

Do not edit `~/.grok/auth.json` directly unless the user explicitly asks for a forensic inspection, and even then redact token values. Prefer `grok login`, `grok login --device-auth`, OIDC config, or environment variables.

Do not recommend `--yolo`, `bypassPermissions`, or broad `Bash` allow rules as the default. They are acceptable only for trusted, scoped environments or when the user explicitly wants maximum autonomy. For CI and headless work, prefer `--permission-mode dontAsk` plus explicit `--allow` rules and optional hooks.

For untrusted code, combine `--sandbox strict`, narrow permissions, and project-hook trust review. Remember that permissions govern requested actions while sandboxing is the OS-level boundary.

## First move workflow

When invoked, quickly classify the user goal into one of these setup lanes:

1. Fresh install or repair install.
2. Authentication: browser, API key, device auth, OIDC, or external provider.
3. Global user config: `~/.grok/config.toml` and `~/.grok/pager.toml`.
4. Project config: `.grok/config.toml`, `.grok/skills`, `.grok/hooks`, `.grok/agents`, `.grok/sandbox.toml`, `AGENTS.md`.
5. MCP integration.
6. Permissions, hooks, sandbox, headless CI.
7. Agents, subagents, memory, sessions, terminal behavior.
8. Migration from Claude Code or Cursor settings.

Then do this:

1. Inspect current state when possible:
   ```bash
   command -v grok || true
   grok --version || true
   python3 /path/to/this-skill/scripts/grok_build_doctor.py --project .
   ```
2. Decide which config layer belongs to the change:
   - One-off behavior: CLI flags.
   - Secrets and CI: environment variables.
   - User-wide defaults: `~/.grok/config.toml`.
   - TUI appearance: `~/.grok/pager.toml`.
   - Project instructions: `AGENTS.md` and `.grok/rules/*.md`.
   - Project MCP and permissions: `.grok/config.toml` with `[mcp_servers]`, and `[permission]` when configuring project-level policy.
   - Project skills/hooks/agents/sandbox: `.grok/skills`, `.grok/hooks`, `.grok/agents`, `.grok/sandbox.toml`.
3. Generate or edit the relevant files.
4. Validate with the least invasive command:
   ```bash
   grok inspect
   grok inspect --json
   grok models
   GROK_LOG_FILE=1 GROK_LOG_FILTER=debug grok -p "hello" --output-format json
   ```
5. Return a concise install/verify checklist and call out anything that still requires user-side secrets or browser auth.

## Configuration precedence to remember

General Grok config resolves in this order:

1. CLI flags.
2. Environment variables.
3. `~/.grok/config.toml`.
4. Remote managed settings.
5. Built-in defaults.

MCP server priority is narrower:

1. `.grok/config.toml` in the current directory.
2. `<repo-root>/.grok/config.toml`.
3. `~/.grok/config.toml`.

The configuration and MCP docs describe project-scoped `.grok/config.toml` as MCP-focused. The permissions guide also supports project-level `[permission]` rules. Treat other sections as global-only unless the installed CLI verifies them with `grok inspect` or `grok --help`.

Authentication priority:

1. `XAI_API_KEY`.
2. OIDC silent refresh from `auth.json`.
3. External auth provider.
4. Browser login.

Permission decision flow:

1. `PreToolUse` hooks.
2. Policy rules from config, Claude settings, or `--allow` / `--deny`.
3. Built-in fast paths for reads, grep, and curated safe shell commands.
4. Prompt policy via `--permission-mode` or `defaultMode`.
5. Interactive prompt or headless denial.

## Preferred setup profiles

Use these profile defaults unless the user gives better constraints.

### Daily driver

Goal: useful interactive coding without reckless autonomy.

- Browser login with `grok login`, or API key only when needed.
- Global `~/.grok/config.toml`: default model `grok-build`, gitignore respected, subagents enabled, memory disabled unless requested.
- UI: simple mode unless the user wants Vim mode, default permission cursor on `allow_once` or another conservative row.
- Launch with `grok --sandbox workspace` when they want a safety boundary.
- Avoid `--yolo` by default.

### Headless CI reviewer

Goal: deterministic, non-interactive, low-blast-radius runs.

- `XAI_API_KEY` from CI secret store.
- `grok -p ... --output-format json --no-auto-update`.
- `--permission-mode dontAsk`.
- Allow `Read`, `Grep`, and only exact needed shell prefixes such as `Bash(git *)`, `Bash(gh *)`, `Bash(npm test*)`.
- Add `--sandbox read-only` for review-only jobs, or `--sandbox strict` for untrusted repos.
- Parse `.text` and `.sessionId` from JSON output.

### Enterprise SSO or proxy

Goal: org-managed auth and endpoints.

- Use `[grok_com_config.oidc]` for issuer and client ID, or `[auth] auth_provider_command` for external auth.
- Use `GROK_CLI_CHAT_PROXY_BASE_URL` for proxying when required.
- Keep provider secrets in environment variables, not TOML.
- Disable auto-update if managed deployment needs pinned versions.

### MCP-heavy project

Goal: connect Grok to external tools cleanly.

- Prefer native `url = "https://.../mcp"` for hosted HTTP/SSE MCP servers.
- Use `command` plus `args` for local stdio servers.
- Use `${VAR}` interpolation for secrets in `env` and `headers`.
- Keep project-specific MCP in `.grok/config.toml`; remember project server names fully replace global servers of the same name.
- Validate with `grok inspect`, `/mcps`, and debug logs.

### Hardened shell policy

Goal: positive control over commands.

- Use `dontAsk` plus explicit narrow allows.
- Add a `PreToolUse` hook when command policy must be fail-closed by intent.
- The provided `assets/templates/hooks/git-gh-only` hook allows only `git` and `gh` as first shell words.

## Important Grok files and directories

Global:

- `~/.grok/config.toml`: main user config.
- `~/.grok/pager.toml`: TUI appearance and behavior.
- `~/.grok/auth.json`: auto-managed credentials.
- `~/.grok/sessions/`: persisted sessions.
- `~/.grok/memory/`: cross-session memory files and index.
- `~/.grok/skills/`: user Grok skills.
- `~/.grok/plugins/`: user Grok plugins.
- `~/.grok/agents/`: user Grok agents.
- `~/.grok/hooks/`: global hooks.
- `~/.grok/logs/`: logs when `GROK_LOG_FILE` is enabled.

Project:

- `AGENTS.md`: project instructions loaded into Grok.
- `.grok/config.toml`: project MCP servers only.
- `.grok/skills/`: project Grok skills.
- `.grok/hooks/`: project hooks, trust required.
- `.grok/agents/`: project agent definitions.
- `.grok/sandbox.toml`: project custom sandbox profiles.
- `.grok/lsp.json`: LSP config.
- `.grok/rules/*.md`: additional project rules.

## Known commands

Install and update:

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
grok --version
grok update
```

Windows PowerShell:

```powershell
irm https://x.ai/cli/install.ps1 | iex
grok --version
```

Launch and auth:

```bash
grok
grok login
grok login --device-auth
export XAI_API_KEY="xai-..."
```

Headless:

```bash
grok -p "Explain this codebase" --output-format json
grok -p "Review changes" --permission-mode dontAsk --allow 'Read' --allow 'Grep'
```

Inspect:

```bash
grok inspect
grok inspect --json
grok models
grok mcp list --json
```

Debug logs:

```bash
GROK_LOG_FILE=1 GROK_LOG_FILTER=debug grok -p "hello" --output-format json
tail -f ~/.grok/logs/tracing.log
```

## Troubleshooting heuristics

Authentication failures:

- Check whether `XAI_API_KEY` is set and unintentionally overriding browser credentials.
- Use `grok login` to re-authenticate.
- For remote or headless machines, use `grok login --device-auth` or `XAI_API_KEY`.
- For OIDC, verify issuer, client ID, and loopback redirect URI.
- For external providers, stdout must contain only the token or token JSON; progress belongs on stderr.

MCP not appearing:

- Run `grok inspect --json` and `grok mcp list --json`.
- Verify transport shape: use either `url` or `command` plus `args`.
- Check project config is only `[mcp_servers]`.
- Move secrets to env vars and ensure they are present in the shell that launches Grok.
- Enable `GROK_LOG_FILE=1 GROK_LOG_FILTER=debug` and search logs for `mcp`.

Permissions surprise:

- Remember deny rules win over allow rules.
- Check `PreToolUse` hooks first.
- Confirm whether TUI saved a persistent permission mode.
- In headless mode, `dontAsk` silently denies anything not allowlisted.
- Use sandbox for hard OS restrictions, not only prompt policy.

Terminal weirdness:

- Run `/terminal-setup` inside Grok.
- For truecolor, set `COLORTERM=truecolor` and tmux `terminal-features ",*:RGB"`.
- In VS Code terminals, use `Alt+Enter` for newline when `Shift+Enter` cannot be distinguished.
- In WezTerm, enable Kitty keyboard protocol if `Ctrl+Enter` interject fails.

## Deliverables to produce for the user

When asked to set Grok up, produce one of these concrete outputs:

- A patched `~/.grok/config.toml` or a proposed TOML block.
- A `.grok/config.toml` containing project MCP servers.
- An `AGENTS.md` tuned to their repo.
- A hook directory with JSON plus executable scripts.
- A CI command or script with narrow permissions.
- A doctor report summarizing install, auth, config, MCP, and safety state.

Always include verification commands and expected success signals.
