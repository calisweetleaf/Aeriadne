# Grok Build Configuration Field Guide

This guide condenses the uploaded xAI Grok Build user guide into a setup-oriented runbook for Codex.

## Configuration surfaces

Grok uses several layers. Pick the smallest layer that solves the task.

| Surface | File or command | Scope | Use it for |
| --- | --- | --- | --- |
| CLI flags | `grok ... --flag` | One run | temporary model, cwd, prompt, permissions, sandbox, output format |
| Environment variables | shell or CI secrets | Process | auth secrets, feature toggles, endpoint overrides, log settings |
| Global config | `~/.grok/config.toml` | User | model defaults, UI, tool settings, auth provider, memory, subagents, skills, plugins, notifications, permissions |
| Pager config | `~/.grok/pager.toml` | User | alternate screen, scrollback layout, prompt display, animation, plugin UI visibility |
| Project config | `.grok/config.toml` | Project | MCP servers, plus `[permission]` rules when using project-level policy |
| Project rules | `AGENTS.md`, `.grok/rules/*.md` | Directory tree | coding standards, build/test commands, architecture notes |
| Project extensions | `.grok/skills`, `.grok/hooks`, `.grok/agents`, `.grok/sandbox.toml`, `.grok/lsp.json` | Project | reusable workflows, safety gates, custom agents, sandbox profiles, LSP |

General precedence is CLI flags, then environment variables, then `~/.grok/config.toml`, then remote settings, then defaults.

## Installation and basic verification

macOS, Linux, Windows through Git Bash:

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

First interactive launch:

```bash
grok
```

Headless smoke test:

```bash
grok -p "hello" --output-format json
```

## Authentication decision tree

Use browser auth for a normal workstation:

```bash
grok login
```

Use device code auth for SSH, Docker, or remote machines without a local browser:

```bash
grok login --device-auth
```

Use API key auth for CI or automation:

```bash
export XAI_API_KEY="xai-..."
grok -p "Run the tests" --output-format json
```

Use OIDC when an organization wants IdP login:

```toml
[grok_com_config.oidc]
issuer = "https://acme.okta.com"
client_id = "0oa1b2c3d4e5f6g7h8i9"
# scopes = ["openid", "profile", "email", "offline_access"]
# audience = "https://api.acme.com"
```

Use an external auth provider for enterprise, CI, air-gapped, or custom auth flows:

```toml
[auth]
auth_provider_command = "/usr/local/bin/my-auth-provider"
auth_provider_label = "Acme Corp"
auth_token_ttl = 3600
```

External auth stdout must contain only the token or token JSON. Status output belongs on stderr.

Auth priority is `XAI_API_KEY`, then OIDC silent refresh, then external auth provider, then browser login.

## Global `~/.grok/config.toml` sections

Common sections:

```toml
[cli]
auto_update = true

[models]
default = "grok-build"
web_search = "grok-4.20-multi-agent"

[ui]
simple_mode = true
vim_mode = false
default_selected_permission = "allow_once"

[session]
auto_compact_threshold_percent = 85
load_envrc = true

[tools]
respect_gitignore = true

[toolset.bash]
timeout_secs = 120.0
output_byte_limit = 65536
```

Other supported sections include `[auth]`, `[grok_com_config.oidc]`, `[model.<name>]`, `[mcp_servers.<name>]`, `[memory]`, `[subagents]`, `[skills]`, `[plugins]`, `[compat.cursor]`, `[compat.claude]`, `[ui.notifications]`, `[telemetry]`, and `[permission]`.

## Project `.grok/config.toml`

Use project `.grok/config.toml` primarily for `[mcp_servers]`. The permissions guide also shows project-level `[permission]` rules. Do not put UI, auth, model, memory, toolset, notification, telemetry, skills, or plugins config here unless the installed CLI verifies support.

```toml
# .grok/config.toml
[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
enabled = true
```

Grok walks from current directory up to repo root. A server defined closer to the current directory replaces a global server with the same name.

## MCP servers

Hosted HTTP/SSE MCP:

```toml
[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
enabled = true

[mcp_servers.internal-tools]
url = "https://mcp.internal.example.com/mcp"
headers = { "Authorization" = "Bearer ${INTERNAL_MCP_TOKEN}" }
```

Local stdio MCP:

```toml
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]

[mcp_servers.postgres]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
```

Useful commands:

```bash
grok mcp list
grok mcp list --json
grok mcp add my-server --command npx --args "-y @modelcontextprotocol/server-filesystem /tmp"
grok mcp add remote-api --url https://mcp.example.com/api
grok mcp remove my-server
grok inspect --json
```

Use `${VAR}` or `${VAR:-default}` for secrets and environment-dependent values.

## Permissions

Modes:

| Mode | Behavior | Use case |
| --- | --- | --- |
| `default` | prompt for anything not pre-approved | interactive daily use |
| `dontAsk` | silently deny anything not allowlisted or fast-path safe | CI and high security |
| `bypassPermissions` | auto-allow nearly everything | trusted environments only |
| `acceptEdits` | auto-allow edits | edit-heavy trusted work |
| `plan` | plan-mode-specific behavior | structured planning |
| `auto` | experimental classifier | future use |

Headless locked-down example:

```bash
grok -p "Review the API changes" \
  --permission-mode dontAsk \
  --allow 'Read' \
  --allow 'Grep' \
  --allow 'Bash(git *)' \
  --allow 'Bash(gh *)' \
  --deny 'Bash(rm -rf *)'
```

Native permission rules:

```toml
[permission]
rules = [
  { action = "allow", tool = "bash", pattern = "git *" },
  { action = "allow", tool = "bash", pattern = "gh *" },
  { action = "allow", tool = "read" },
  { action = "allow", tool = "grep" },
  { action = "deny",  tool = "bash", pattern = "*" },
  { action = "ask",   tool = "edit" },
]
```

Deny rules win over allow rules. `PreToolUse` hooks run before policy rules.

## Sandbox profiles

| Profile | Reads | Writes | Child network | Use case |
| --- | --- | --- | --- | --- |
| `off` | unrestricted | unrestricted | unrestricted | default |
| `workspace` | everywhere | CWD, `/tmp`, `~/.grok/` | allowed | normal dev |
| `read-only` | everywhere | `~/.grok/` only | blocked | review and exploration |
| `strict` | CWD plus system paths | CWD, `/tmp`, `~/.grok/` | blocked | untrusted code |

Examples:

```bash
grok --sandbox workspace
grok --sandbox read-only
grok --sandbox strict
```

Custom profiles live in `~/.grok/sandbox.toml` or `.grok/sandbox.toml`:

```toml
[profiles.devbox]
extends = "workspace"
restrict_network = true
read_only = ["/data"]
read_write = ["/tmp/scratch"]
deny = ["/data/shared-secrets"]
```

## Hooks

Hook locations include global `~/.grok/hooks/*.json`, project `.grok/hooks/*.json`, plugin hooks, and Claude/Cursor compatibility sources. Project hooks require trust.

Blocking hook shape:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bin/safe-shell.sh", "timeout": 5 }
        ]
      }
    ]
  }
}
```

A `PreToolUse` hook must print JSON like `{"decision":"deny","reason":"..."}` to block. Hook failures fail open, so enforcement hooks must handle their own errors and return an explicit deny.

## Grok skills and plugins

Grok skills live in these locations:

- `./.grok/skills/` for current directory.
- `<repo_root>/.grok/skills/` for repo scope.
- `~/.grok/skills/` for user scope.
- Claude and Cursor skill dirs are scanned by default when compatibility is enabled.

Each Grok skill is a directory with a `SKILL.md` file and YAML front matter containing `name` and `description`.

Plugins can bundle skills, agents, hooks, MCP server configs, and LSP configs. Plugin locations are `.grok/plugins/`, `~/.grok/plugins/`, or temporary `--plugin-dir <PATH>`. Hooks and MCP servers from plugins require trust.

## Project rules

Grok loads project instructions from common filenames including `Agents.md`, `Claude.md`, `CLAUDE.md`, `CLAUDE.local.md`, `AGENT.md`, and `AGENTS.md`. Deeper files are appended later and effectively win on conflicts.

Put actionable rules in `AGENTS.md`: coding conventions, build/test commands, style guides, architecture boundaries, commit/PR requirements. Each file is capped at 10,000 characters.

## Headless mode

Basic:

```bash
grok -p "Your prompt here"
```

Useful flags:

- `--cwd <PATH>` sets working directory.
- `--output-format plain|json|streaming-json` controls output.
- `--permission-mode <MODE>` controls approval behavior.
- `--allow` and `--deny` add permission rules.
- `--tools` and `--disallowed-tools` filter tools in headless only.
- `--sandbox <PROFILE>` applies OS-level restrictions.
- `--no-auto-update` keeps CI stdout clean.
- `-s <ID>`, `--resume <ID>`, and `-c` manage sessions.

JSON output contains `text`, `stopReason`, `sessionId`, and `requestId`.

## Memory

Memory is experimental and disabled by default. Enable it per session, per process, or persistently:

```bash
grok --experimental-memory
export GROK_MEMORY=1
```

```toml
[memory]
enabled = true
```

Force-disable with `--no-memory` or `GROK_MEMORY=0`. Memory files live under `~/.grok/memory/`. Use `/flush`, `/dream`, and `/memory` in the TUI.

## Subagents

Subagents can be enabled or disabled globally:

```toml
[subagents]
enabled = true
default_model = "grok-build"

[subagents.toggle]
explore = true
plan = false

[subagents.models]
explore = "grok-build"
```

`explore` is read-only, `plan` creates structured plans, and `general-purpose` has full capability by default.

## Terminal and pager

`~/.grok/pager.toml` controls TUI appearance. Key section:

```toml
[terminal]
alt_screen = "auto"  # auto, always, never
```

Run `/terminal-setup` inside Grok to diagnose keyboard, colors, mouse, and terminal capability issues.

For tmux truecolor:

```tmux
set -g allow-passthrough on
set -g set-clipboard on
set -as terminal-features ",*:RGB"
```

For shell truecolor:

```bash
export COLORTERM=truecolor
```
