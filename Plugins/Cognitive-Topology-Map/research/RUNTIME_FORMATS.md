# Runtime Plugin Formats — Authoritative Reference

This document is the canonical reference for plugin/skill/extension formats across the four AI coding agent runtimes that CTMv3 must support. Each section is precise enough that an adapter author can write working integration code without consulting primary sources. All claims are cited inline.

Sources consulted: [Anthropic Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/), [OpenAI Codex Docs](https://developers.openai.com/codex/), [Gemini CLI Docs](https://geminicli.com/docs/) and [GitHub source](https://github.com/google-gemini/gemini-cli), [opencode.ai Docs](https://opencode.ai/docs/), and official GitHub repositories.

---

## Table of Contents

1. [Claude Code (Anthropic)](#1-claude-code-anthropic)
2. [Codex CLI (OpenAI)](#2-codex-cli-openai)
3. [Gemini CLI (Google)](#3-gemini-cli-google)
4. [opencode (sst/opencode)](#4-opencode-sstopencode)
5. [Cross-runtime command surface table](#5-cross-runtime-command-surface)

---

## 1. Claude Code (Anthropic)

### 1.1 Directory Layout

Claude Code supports two configuration tiers: **standalone** (`.claude/` per-project or `~/.claude/` global) and **plugins** (a distributable self-contained directory with a manifest).

#### Standalone layout

```
.claude/                          # project-scoped standalone config
├── CLAUDE.md                     # persistent instructions for all sessions
├── settings.json                 # project settings
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md              # required
│       └── (optional supporting files)
├── commands/                     # legacy flat command files (still supported)
│   └── deploy.md
├── agents/
│   └── <agent-name>.md
├── hooks/
│   └── hooks.json
└── .mcp.json                     # project-scoped MCP servers

~/.claude/                        # global standalone config
├── CLAUDE.md
├── skills/
├── agents/
└── settings.json
```

#### Plugin layout

```
<plugin-root>/
├── .claude-plugin/
│   └── plugin.json               # REQUIRED manifest (only file here)
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       └── scripts/              # optional helper scripts
├── commands/                     # legacy; prefer skills/
├── agents/
│   └── <agent-name>.md
├── hooks/
│   └── hooks.json
├── .mcp.json                     # MCP server configs
├── .lsp.json                     # LSP server configs
├── monitors/
│   └── monitors.json
├── bin/                          # executables added to PATH while plugin is active
├── settings.json                 # default settings applied on enable
└── README.md
```

Sources: [Claude Code — Create plugins](https://docs.anthropic.com/en/docs/claude-code/plugins), [Plugins reference](https://docs.anthropic.com/en/docs/claude-code/plugins-reference)

### 1.2 Manifest Schema — `.claude-plugin/plugin.json`

```json
{
  "name": "my-plugin",
  "description": "Shown in plugin manager when browsing or installing.",
  "version": "1.0.0",
  "author": {
    "name": "Author Name",
    "url": "https://example.com"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Unique identifier; becomes the skill namespace prefix (e.g., `/my-plugin:skill-name`). Must be kebab-case. |
| `description` | string | Recommended | Shown in plugin manager UI. |
| `version` | string | Optional | If set, users get updates only when this bumps. If omitted with git distribution, every commit SHA is treated as a new version. |
| `author` | object | Optional | Attribution only; `name` and `url` sub-fields. |

Source: [Claude Code — Create plugins](https://docs.anthropic.com/en/docs/claude-code/plugins)

### 1.3 Skill Files — `SKILL.md`

Each skill lives in a directory whose name becomes the command name. The `SKILL.md` file has two parts: YAML frontmatter and markdown body.

#### Frontmatter fields

```yaml
---
description: "Summarize uncommitted git changes and flag risky edits."
allowed-tools:
  - Bash
  - Read
disable-model-invocation: false
context: fork
agent: Explore
---
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `description` | string | — | Tells Claude when to load/use the skill automatically. Strongly recommended. |
| `allowed-tools` | string[] | parent session's tools | Grant Claude access to these tools without per-use approval when the skill is active. |
| `disable-model-invocation` | boolean | false | When `true`, Claude will NOT trigger this skill automatically; only explicit `/skill-name` invocation works. |
| `context` | string | inline | Set to `"fork"` to run the skill in an isolated subagent context. The skill body becomes the subagent prompt. |
| `agent` | string | default | Agent type for `context: fork` runs (e.g., `Explore`, `Plan`, or a custom agent name). |

The skill body is standard markdown with instructions. The `$ARGUMENTS` placeholder captures user-provided arguments when the skill is invoked as `/skill-name arg1 arg2`.

Dynamic context injection with shell commands uses the `` !`command` `` syntax — the output replaces the placeholder before Claude reads the skill.

Sources: [Claude Code — Extend Claude with skills](https://docs.anthropic.com/en/docs/claude-code/slash-commands)

#### Skill file locations

| Scope | Path |
|---|---|
| Project skill (standalone) | `.claude/skills/<name>/SKILL.md` |
| Global skill (standalone) | `~/.claude/skills/<name>/SKILL.md` |
| Legacy flat command | `.claude/commands/<name>.md` or `~/.claude/commands/<name>.md` |
| Plugin skill | `skills/<name>/SKILL.md` at plugin root |

Plugin skills are namespaced: a skill `hello` in a plugin named `my-plugin` is invoked as `/my-plugin:hello`. Standalone skills are invoked as `/hello`.

### 1.4 Agent Files — `agents/<name>.md`

Custom subagents are Markdown files with YAML frontmatter.

```markdown
---
name: security-reviewer
description: Reviews code changes for security issues. Use proactively when security-sensitive files change.
model: sonnet
effort: high
maxTurns: 20
tools:
  - Read
  - Bash
  - Grep
disallowedTools:
  - Write
  - Edit
permissionMode: default
isolation: worktree
---

You are a security-focused code reviewer. Analyze the provided code for vulnerabilities, injection risks, insecure defaults, and OWASP Top 10 issues. Return a structured report.
```

| Frontmatter field | Type | Notes |
|---|---|---|
| `name` | string | Required. Display identifier. |
| `description` | string | Claude uses this to decide when to auto-delegate. |
| `model` | string | Model alias (`sonnet`, `haiku`, `opus`) or full model ID. |
| `effort` | string | `low`, `medium`, `high`. Controls reasoning effort / extended thinking budget. |
| `maxTurns` | integer | Max agentic turns before forced text-only response. |
| `tools` | string[] | Allowlist. Unspecified tools are inherited from parent session. |
| `disallowedTools` | string[] | Explicit deny list. Overrides `tools`. |
| `permissionMode` | string | Override permission prompt behavior. |
| `skills` | string[] | Skills whose full content is preloaded at subagent startup. |
| `memory` | boolean/string | Persistent memory directory for the subagent. |
| `isolation` | string | Only valid value is `"worktree"` — gives the subagent its own git checkout. |
| `background` | boolean | Run the subagent in background (non-blocking). |
| `hooks` | object | Inline hooks config — not supported for plugin-shipped agents. |
| `mcpServers` | object | Inline MCP server config for this subagent only. |

Plugin-shipped agents do NOT support `hooks`, `mcpServers`, or `permissionMode` frontmatter for security reasons.

Sources: [Claude Code — Plugins reference — Agents](https://docs.anthropic.com/en/docs/claude-code/plugins-reference), [Create custom subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)

### 1.5 Hook Configuration

Hooks are defined in `hooks/hooks.json` (plugin) or `.claude/hooks/hooks.json` (standalone), or inline in `settings.json`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/validate-bash.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format-code.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/session_init.py"
          }
        ]
      }
    ]
  }
}
```

#### Hook events

| Event | Cadence | Notes |
|---|---|---|
| `SessionStart` | Once per session | Session begins or resumes. |
| `Setup` | Once on `--init-only` / `--init` in `-p` mode | One-time CI/script preparation. |
| `UserPromptSubmit` | Once per turn | Before Claude processes the prompt. |
| `UserPromptExpansion` | Once per command expansion | When a typed command expands to a prompt. Can block expansion. |
| `InstructionsLoaded` | On file load | When CLAUDE.md or `.claude/rules/*.md` files load. |
| `PreToolUse` | Every tool call | Before a tool executes. Can block execution. |
| `PermissionRequest` | On permission dialog | When a permission prompt appears. |
| `PermissionDenied` | On denial | Return `{retry: true}` to tell the model it may retry. |
| `PostToolUse` | Every tool call | After a tool succeeds. |
| `PostToolUseFailure` | Every tool failure | After a tool fails. |
| `PostToolBatch` | After parallel tool batch | Before next model call. |
| `SubagentStart` | On subagent spawn | When a subagent starts. |
| `SubagentStop` | On subagent finish | When a subagent completes. |
| `TaskCreated` | On task creation | Via `TaskCreate` tool. |
| `TaskCompleted` | On task completion | Via task completion. |
| `Notification` | On notification | When Claude sends a notification. |
| `TeammateIdle` | On teammate idle | In agent teams. |
| `Stop` | Once per turn | When Claude finishes responding. |
| `StopFailure` | On API error | Turn ends due to error; output ignored. |
| `ConfigChange` | On config file change | During a live session. |
| `CwdChanged` | On `cd` | Working directory changes. |
| `FileChanged` | On watched file change | `matcher` specifies which filenames to watch. |
| `WorktreeCreate` | On worktree creation | Replaces default git behavior. |
| `WorktreeRemove` | On worktree removal | At session exit or subagent finish. |
| `PreCompact` | Before compaction | Before context compaction runs. |

#### Hook handler types

```json
{
  "type": "command",
  "command": "path/to/script.sh",
  "statusMessage": "Optional status message displayed while running"
}
```

```json
{
  "type": "http",
  "url": "https://my-server.example.com/hook",
  "headers": { "Authorization": "Bearer token" }
}
```

```json
{
  "type": "prompt",
  "prompt": "Analyze the tool call and return JSON with decision field."
}
```

```json
{
  "type": "mcp",
  "tool": "server-name/tool-name"
}
```

Hook handlers receive a JSON object via stdin (command hooks) or as HTTP POST body (HTTP hooks). They communicate results through exit codes and stdout JSON.

**Exit codes**: `0` = allow/pass, `1` = hook failure (logged but not blocking), `2` = block the tool call.

**JSON output** (stdout, exit 0): return `{"decision": "block", "reason": "..."}` to block, `{"decision": "allow"}` to allow, or `{"decision": "escalate"}` to show a permission prompt.

**Plugin environment variables**: `$CLAUDE_PLUGIN_ROOT` (installed plugin root), `$CLAUDE_PLUGIN_DATA` (writable data directory).

Sources: [Claude Code — Hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks), [Plugins reference — Hooks](https://docs.anthropic.com/en/docs/claude-code/plugins-reference)

### 1.6 MCP Integration

Project-scoped MCP: `.mcp.json` in project root (checked into version control).  
Local-scoped MCP: stored in `~/.claude.json` under the project path (private to one user).  
User/global MCP: `~/.claude.json` user-global section.  
Plugin-bundled MCP: `.mcp.json` at plugin root.

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "node",
      "args": ["./dist/mcp-server.js"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    },
    "remote-server": {
      "type": "streamable-http",
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ${TOKEN}" }
    }
  }
}
```

Add a server via CLI: `claude mcp add --transport http my-server https://api.example.com/mcp`

Source: [Claude Code — Connect to tools via MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)

### 1.7 Permission / Allow-List Model

Skills can specify `allowed-tools` in frontmatter to grant the skill's execution context access to those tools without per-use approval. The user's `settings.json` `permissions` object governs the global baseline.

Subagents inherit parent permissions by default. The `permissionMode` frontmatter field can override:
- `default` — standard permission prompts
- `acceptEdits` — auto-accept file edits
- `bypassPermissions` — skip all prompts (requires explicit user enablement)

Plugin-shipped agents cannot set `permissionMode` for security reasons.

### 1.8 Marketplace

Claude Code has two public marketplaces:
- `claude-plugins-official` — curated Anthropic plugins, auto-available.
- `claude-plugins-community` — third-party submissions. Add with: `/plugin marketplace add anthropics/claude-plugins-community`

Install: `/plugin install plugin-name@marketplace-name`  
Test locally: `claude --plugin-dir ./my-plugin`  
Reload during development: `/reload-plugins`

---

## 2. Codex CLI (OpenAI)

### 2.1 Directory Layout

```
~/.codex/                         # global Codex config home (CODEX_HOME default)
├── config.toml                   # main config (MCP, features, hooks inline)
├── hooks.json                    # global hooks (alternative to inline config.toml)
├── AGENTS.md                     # global instructions
└── AGENTS.override.md            # temporary global override

<repo-root>/
├── AGENTS.md                     # project-scoped instructions
├── .agents/
│   └── skills/
│       └── <skill-name>/
│           ├── SKILL.md          # required
│           └── scripts/          # optional helper scripts
├── .codex/
│   ├── config.toml               # project-scoped config (trusted projects only)
│   └── hooks.json                # project-scoped hooks
└── agents/
    └── openai.yaml               # subagent registration and UI metadata

<plugin-root>/
├── .codex-plugin/
│   └── plugin.json               # REQUIRED manifest
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── hooks/
│   └── hooks.json                # default; overridden by manifest hooks field
├── .mcp.json                     # bundled MCP servers
└── .app.json                     # app/connector integrations
```

Skill location precedence for scanning (all named `REPO`-scope, from innermost to outermost):
1. `$CWD/.agents/skills` (current dir)
2. `$CWD/../.agents/skills` (parent)
3. `$REPO_ROOT/.agents/skills` (repo root)
4. `$HOME/.agents/skills` (user global)
5. System/admin locations

Sources: [Codex — Agent Skills](https://developers.openai.com/codex/skills), [Codex — Customization](https://developers.openai.com/codex/concepts/customization)

### 2.2 Skill Files — `SKILL.md`

```markdown
---
name: commit
description: Stage and commit changes in semantic groups. Use when the user wants to commit, organize commits, or clean up a branch before pushing.
---

1. Run `git status` to see all changes.
2. Group related changes into logical commits.
3. Stage and commit each group with a clear message.
```

**Required frontmatter fields:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Required. Unique identifier. Used in `$name` mention syntax and implicit matching. |
| `description` | string | Required. Codex uses this for implicit matching. Front-load key trigger words. |

**Optional frontmatter fields (via `agents/openai.yaml`):**

The `agents/openai.yaml` file at the skill directory root declares additional metadata and invocation policy:

```yaml
# agents/openai.yaml
allow_implicit_invocation: false   # default: true
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `allow_implicit_invocation` | boolean | `true` | When `false`, Codex will not implicitly choose this skill from prompt context. Explicit `$skill-name` mention still works. |

The full `openai.yaml` also declares MCP tool dependencies:

```yaml
# agents/openai.yaml
allow_implicit_invocation: true
mcp_servers:
  - figma
  - linear
```

Source: [Codex — Agent Skills](https://developers.openai.com/codex/skills)

### 2.3 Skill Invocation

- **Explicit**: Type `$skill-name` in a prompt (CLI/IDE) or run `/skills` to get a picker.
- **Implicit**: Codex automatically selects a skill when the user's prompt matches the skill `description`. Can be disabled per skill with `allow_implicit_invocation: false`.

Context budget: Codex includes metadata (name + description + path) for all skills in the initial context, capped at ~2% of the model context window (8,000 chars when window size is unknown). When many skills are installed, descriptions may be truncated or skills omitted; a warning is shown.

### 2.4 Plugin Manifest — `.codex-plugin/plugin.json`

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Reusable greeting workflow",
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "hooks": "./hooks/hooks.json",
  "apps": "./.app.json",
  "author": "author-name",
  "homepage": "https://example.com",
  "repository": "https://github.com/example/my-plugin",
  "license": "MIT",
  "keywords": ["git", "workflow"],
  "interface": {
    "displayName": "My Plugin",
    "shortDescription": "A brief tagline",
    "longDescription": "Full paragraph description.",
    "developerName": "Author Name",
    "category": "productivity",
    "capabilities": ["file-editing", "git"],
    "websiteURL": "https://example.com",
    "privacyPolicyURL": "https://example.com/privacy",
    "termsOfServiceURL": "https://example.com/terms",
    "defaultPrompt": "Use $commit to stage and commit changes.",
    "brandColor": "#4A90E2",
    "composerIcon": "./assets/icon-32.png",
    "logo": "./assets/logo.svg",
    "screenshots": ["./assets/screenshot1.png"]
  }
}
```

All paths in the manifest must start with `./` and resolve relative to the plugin root.

Source: [Codex — Build plugins](https://developers.openai.com/codex/plugins/build)

### 2.5 Hook Configuration — `hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.codex/hooks/session_start.py",
            "statusMessage": "Loading session notes"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.codex/hooks/validate_command.sh"
          }
        ]
      }
    ]
  }
}
```

**Hook events:**

| Event | Scope | Notes |
|---|---|---|
| `SessionStart` | Thread/subagent start | Once per session launch. |
| `SubagentStart` | Subagent start | When a subagent is spawned. |
| `UserPromptSubmit` | Turn | Before prompt is processed. |
| `PreToolUse` | Turn (every tool call) | Can intercept Bash, file edits, MCP calls. |
| `PermissionRequest` | Turn | Before approval prompt appears. |
| `PostToolUse` | Turn (every tool call) | After tool produces output. |
| `PreCompact` | Turn | Before context compaction. |
| `PostCompact` | Turn | After context compaction. |
| `SubagentStop` | Turn | When a subagent finishes. |
| `Stop` | Turn | When conversation turn ends. |

The `matcher` field is a regex string. Use `"*"`, `""`, or omit it entirely to match all occurrences of that event.

**Feature flag**: Hooks are on by default. To disable:
```toml
# ~/.codex/config.toml
[features]
hooks = false
```
The old `codex_hooks` key is a deprecated alias for `hooks`. Use `hooks` for all new configuration.

**Hook trust**: Non-managed hooks must be reviewed and trusted before running. Codex records trust against the current hash of the hook definition. Use `/hooks` in the CLI to review, trust, or disable hooks.

**Plugin hooks**: By default, Codex loads `hooks/hooks.json` from the plugin root. The manifest `hooks` field can override this. Plugin hooks are non-managed and require user trust.

Plugin hooks receive environment variables `$PLUGIN_ROOT` and `$PLUGIN_DATA`. Also sets `$CLAUDE_PLUGIN_ROOT` and `$CLAUDE_PLUGIN_DATA` for cross-runtime compatibility.

Sources: [Codex — Hooks](https://developers.openai.com/codex/hooks), [Codex — Build plugins](https://developers.openai.com/codex/plugins/build)

### 2.6 Subagent Registration — `agents/openai.yaml`

```yaml
# .agents/skills/my-skill/agents/openai.yaml
allow_implicit_invocation: true
mcp_servers:
  - figma-mcp
  - linear-mcp
model: gpt-5.5
model_reasoning_effort: high
```

Subagent workflows in Codex are prompt-driven rather than file-declared: there is no separate subagent manifest file analogous to Claude Code's `agents/` directory. Specialized subagents are invoked by instructing Codex to "spawn agents" or "delegate in parallel". The `agents/openai.yaml` file within a skill directory controls that skill's UI presentation and invocation behavior, not a separate named subagent.

Source: [Codex — Subagents concepts](https://developers.openai.com/codex/concepts/subagents)

### 2.7 MCP Integration — `config.toml`

```toml
# ~/.codex/config.toml

[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]

[mcp_servers.figma]
command = "npx"
args = ["-y", "figma-mcp"]
env = { FIGMA_TOKEN = "..." }
cwd = "/home/user/projects"
startup_timeout_sec = 30
tool_timeout_sec = 120
enabled = true
required = false
enabled_tools = ["get_file", "get_component"]
disabled_tools = ["delete_frame"]
default_tools_approval_mode = "prompt"

[mcp_servers.my-remote]
url = "https://my-mcp-server.example.com"
bearer_token_env_var = "MY_TOKEN_ENV"
```

**STDIO server fields:**
- `command` (required): Command to start the server.
- `args` (optional): Argument array.
- `env` (optional): Environment variable map.
- `env_vars` (optional): Variable names to pass through from Codex's environment.
- `cwd` (optional): Working directory.
- `experimental_environment` (optional): Set to `"remote"` for remote executor.

**HTTP server fields:**
- `url` (required): Server address.
- `bearer_token_env_var` (optional): Env var name holding bearer token.
- `http_headers` (optional): Static header map.
- `env_http_headers` (optional): Header-to-env-var map.

**Common options:**
- `startup_timeout_sec` (default: 10)
- `tool_timeout_sec` (default: 60)
- `enabled` (default: true)
- `required`: Fail startup if the server can't connect.
- `enabled_tools`: Tool allow list.
- `disabled_tools`: Tool deny list (applied after `enabled_tools`).
- `default_tools_approval_mode`: `"auto"`, `"prompt"`, or `"approve"`.

Plugin-bundled MCP: declared in `.mcp.json` at plugin root, referenced from `plugin.json` as `"mcpServers": "./.mcp.json"`. Users can override per-plugin MCP settings via:
```toml
[plugins.my-plugin.mcp_servers.server-name]
enabled_tools = ["safe_tool"]
```

Source: [Codex — Model Context Protocol](https://developers.openai.com/codex/mcp)

### 2.8 Permission / Allow-List Model

Skills have no built-in permission model themselves — tool access is governed by global Codex settings. The `enabled_tools` / `disabled_tools` fields on MCP server config are the primary tool-filtering mechanism for external tools. Built-in tools are configured globally in `config.toml`.

### 2.9 Marketplace

- Repo-scoped: `$REPO_ROOT/.agents/plugins/marketplace.json`
- Personal: `~/.agents/plugins/marketplace.json`
- Add a marketplace: `codex plugin marketplace add owner/repo`
- Install plugin: via Codex plugin directory UI or CLI

Installed plugins are cached to `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`.

---

## 3. Gemini CLI (Google)

### 3.1 Directory Layout

Extensions are distinct from per-project/user command files. Extensions are installed globally and may contain commands, MCP servers, and context.

```
~/.gemini/
├── extensions/
│   └── <extension-name>/
│       ├── gemini-extension.json   # REQUIRED manifest
│       ├── GEMINI.md               # optional context file (or custom name)
│       ├── commands/
│       │   └── <command>.toml      # custom slash commands
│       ├── hooks/
│       │   └── hooks.json          # lifecycle hooks (NOT in manifest)
│       ├── agents/
│       │   └── <agent>.md          # agent definitions
│       ├── skills/
│       │   └── <skill-name>/
│       │       └── SKILL.md
│       └── policies/
│           └── *.toml              # policy rules
├── commands/                       # global user commands (no extension needed)
│   └── <command>.toml
└── settings.json                   # global settings including mcpServers

<project-root>/
├── .gemini/
│   ├── commands/                   # project-scoped commands
│   │   └── <command>.toml
│   └── settings.json               # project-scoped settings
└── GEMINI.md                       # project context instructions
```

Sources: [Gemini CLI — Extension reference](https://geminicli.com/docs/extensions/reference/), [Gemini CLI GitHub — extension.ts](https://github.com/google-gemini/gemini-cli/blob/main/packages/a2a-server/src/config/extension.ts), [Gemini CLI — Custom commands](https://github.com/google-gemini/gemini-cli/blob/HEAD/docs/cli/custom-commands.md)

### 3.2 Extension Manifest — `gemini-extension.json`

```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "description": "My awesome extension",
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["${extensionPath}/dist/server.js"],
      "cwd": "${extensionPath}"
    }
  },
  "contextFileName": "GEMINI.md",
  "excludeTools": ["run_shell_command"],
  "migratedTo": "https://github.com/new-owner/new-extension-repo",
  "plan": {
    "directory": ".gemini/plans"
  },
  "settings": [
    {
      "name": "API_KEY",
      "description": "API key for the service",
      "required": true
    }
  ],
  "themes": []
}
```

#### TypeScript schema (from source)

```typescript
interface ExtensionConfig {
  name: string;                              // required; must match directory name
  version: string;                           // required
  description?: string;
  mcpServers?: Record<string, MCPServerConfig>;
  contextFileName?: string | string[];       // name(s) of context files to load
  excludeTools?: string[];                   // tools excluded from the model
  migratedTo?: string;                       // URL if extension has moved
  plan?: { directory: string };
  settings?: SettingDefinition[];
  themes?: ThemeDefinition[];
}
```

| Field | Required | Notes |
|---|---|---|
| `name` | Yes | Must match the extension directory name. Lowercase, numbers, dashes only. |
| `version` | Yes | Semver string. |
| `description` | No | Human-readable description. |
| `mcpServers` | No | Map of server name → `MCPServerConfig`. See section 3.5. |
| `contextFileName` | No | Filename(s) for persistent context. Defaults to loading `GEMINI.md` if present. |
| `excludeTools` | No | Array of tool names to exclude from the model globally (separate from MCP-level excludeTools). |
| `migratedTo` | No | URL of replacement extension. |
| `plan` | No | Directory for plan storage. |
| `settings` | No | Settings to collect at install time; stored in `.env` within extension dir. |

**Important**: `excludeTools` at the manifest level differs from `excludeTools` within an `mcpServers` entry. Manifest-level excludes apply to all tools (including built-in tools like `run_shell_command`). MCP-level excludes apply only to that server's tools.

**Variable substitution**: Use `${extensionPath}` in paths to reference the extension's absolute installation directory. Path separators can be written as `${/}` for cross-platform compatibility (e.g., `"${extensionPath}${/}dist${/}server.js"`).

Source: [Gemini CLI — Extension reference](https://geminicli.com/docs/extensions/reference/), [GitHub source — extension.ts](https://github.com/google-gemini/gemini-cli/blob/main/packages/a2a-server/src/config/extension.ts)

### 3.3 Custom Slash Commands — TOML Format

Commands are `.toml` files placed in a `commands/` directory.

```toml
# .gemini/commands/changelog.toml
# Invoked as: /changelog 1.2.0 added "New feature"

description = "Adds a new entry to the CHANGELOG.md file."
prompt = """
# Task: Update Changelog

You are an expert maintainer. A user has indicated a new change: {{args}}

Add the appropriate entry to CHANGELOG.md.
"""
```

```toml
# .gemini/commands/git/fix.toml
# Invoked as: /git:fix "Button is misaligned"

description = "Generates a fix for a given issue."
prompt = "Please provide a code fix for the issue described here: {{args}}."
```

```toml
# .gemini/commands/grep-code.toml
# Arguments in shell blocks are auto-escaped

description = "Search code for a pattern and summarize."
prompt = """
Please summarize the findings for the pattern `{{args}}`.

Search Results:
!{grep -r {{args}} .}
"""
```

#### TOML command fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `prompt` | string | Yes | The prompt sent to the model. May be multi-line. |
| `description` | string | No | Shown in `/help`. If omitted, generated from filename. |

#### Argument handling

- Use `{{args}}` placeholder to inject user-provided arguments.
- When `{{args}}` appears inside a shell injection block `!{...}`, arguments are **automatically shell-escaped** to prevent injection.
- When `{{args}}` appears in the main prompt body, arguments are injected raw.
- If `{{args}}` is absent from the prompt, any user-typed arguments are appended to the prompt after two newlines (default behavior).

#### Naming and namespacing

- A file at `~/.gemini/commands/test.toml` → `/test`
- A file at `<project>/.gemini/commands/git/commit.toml` → `/git:commit`
- Subdirectory path separators are converted to colons.

#### Precedence

Project commands (`.gemini/commands/`) take precedence over user global commands (`~/.gemini/commands/`).

Extension commands have the lowest precedence. When an extension command name conflicts with a user or project command, the extension command is prefixed: `/extensionname.commandname`.

Reload without restart: `/commands reload`

Source: [Gemini CLI — Custom commands](https://github.com/google-gemini/gemini-cli/blob/HEAD/docs/cli/custom-commands.md)

### 3.4 GEMINI.md Context Files

`GEMINI.md` provides persistent context injected into every session where the extension is active (or when found in project root / user global location).

In `gemini-extension.json`, set `"contextFileName": "GEMINI.md"` (or a custom name). If the field is omitted but a `GEMINI.md` file exists in the extension directory, it is loaded automatically.

`contextFileName` accepts a string or array of strings (multiple context files merged).

### 3.5 MCP Integration

#### In `settings.json` (user global or project)

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./dist/server.js"],
      "env": { "API_KEY": "$MY_API_TOKEN" },
      "cwd": "./server-directory",
      "timeout": 30000,
      "trust": false,
      "includeTools": ["safe_tool", "reader"],
      "excludeTools": ["dangerous_tool"]
    }
  },
  "mcp": {
    "serverCommand": "global-start-command",
    "allowed": ["server-a", "server-b"],
    "excluded": ["server-c"]
  }
}
```

#### In extension `gemini-extension.json`

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["${extensionPath}/dist/server.js"],
      "cwd": "${extensionPath}"
    }
  }
}
```

Note: Extension-defined MCP servers do **not** support the `trust` field. All other fields are supported.

#### Tool filtering precedence

When the same MCP server is declared in both an extension and `settings.json`, the `settings.json` version takes precedence for scalar fields. For tool lists, the merge is security-first:
- `excludeTools`: Union of both sources. If either blocks a tool, it remains blocked.
- `includeTools`: Intersection. Only tools in both allowlists are enabled.
- `excludeTools` always takes precedence over `includeTools`.

Source: [Gemini CLI — MCP servers](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html), [Gemini CLI — Extension reference](https://geminicli.com/docs/extensions/reference/)

### 3.6 Hook Configuration — `hooks/hooks.json`

Hooks are **not** declared in `gemini-extension.json`. They must be in a separate `hooks/hooks.json` file within the extension directory.

```json
{
  "PreToolUse": [
    {
      "matcher": "run_shell_command",
      "hooks": [
        {
          "type": "command",
          "command": "${extensionPath}/hooks/validate-shell.sh"
        }
      ]
    }
  ]
}
```

The hook schema follows the same structure as Claude Code hooks: event name → array of matcher/handler groups. The Gemini CLI hook system is architecturally similar to Claude Code's (both derive from shared open standards work). However, the full event list for Gemini CLI hooks is not fully documented publicly at time of writing — the available events include at minimum `PreToolUse`, `PostToolUse`, and `SessionStart`.

Source: [Gemini CLI — Extension reference — Hooks](https://geminicli.com/docs/extensions/reference/)

### 3.7 Agent Files — `agents/<name>.md`

Extensions can bundle agent definitions in an `agents/` directory. These follow the Agent Skills open standard Markdown-with-frontmatter format (same schema as Claude Code plugin agents). The Gemini CLI agent integration derives from shared standards work at [agentskills.io](https://agentskills.io/).

### 3.8 Policy Engine — `policies/*.toml`

Extensions can contribute policy rules to the Gemini CLI Policy Engine. Place `.toml` files in a `policies/` directory at the extension root. These files are automatically loaded when the extension is active.

Policy rules from extensions run at tier 2 (below user/admin policies, above default rules).

### 3.9 Extension Management CLI

```bash
gemini extensions install <github-url-or-local-path> [--ref <ref>] [--auto-update]
gemini extensions uninstall <name>
gemini extensions disable <name> [--scope user|workspace]
gemini extensions enable <name> [--scope user|workspace]
gemini extensions update <name>
gemini extensions update --all
gemini extensions new <path> [mcp-server|context|custom-commands]
gemini extensions link <path>     # symlink for local development
```

### 3.10 Project-scoped vs Global Install

| Scope | Path | Notes |
|---|---|---|
| User commands | `~/.gemini/commands/*.toml` | Available in all projects. |
| Project commands | `<project>/.gemini/commands/*.toml` | Project-specific; can be version-controlled. |
| User settings / MCP | `~/.gemini/settings.json` | Global MCP, themes, preferences. |
| Project settings / MCP | `<project>/.gemini/settings.json` | Project-scoped; takes precedence over user. |
| Extensions (global only) | `~/.gemini/extensions/<name>/` | Extensions are always globally installed. |
| Project context | `<project>/GEMINI.md` | Injected in sessions run from that directory. |
| Global context | `~/.gemini/GEMINI.md` | Injected in all sessions. |

---

## 4. opencode (sst/opencode)

**Stability note**: opencode's plugin system is young and actively evolving. The TypeScript plugin API (`@opencode-ai/plugin`) and hook event names may change between releases. The patterns documented here are current as of May 2026 (opencode v0.x). Adapter authors should pin to a specific opencode version and check the changelog before updating.

Source: [opencode.ai Docs](https://opencode.ai/docs/)

### 4.1 Directory Layout

```
~/.config/opencode/               # global user config
├── opencode.json                 # global config
├── tui.json                      # global TUI config
├── AGENTS.md                     # global instructions
├── agents/
│   └── <agent-name>.md
├── commands/
│   └── <command>.md
├── plugins/
│   └── my-plugin.ts              # or .js
└── skills/                       # global skills (Claude Code compat)

<project-root>/
├── opencode.json                 # project config (highest precedence among standard configs)
├── tui.json                      # project TUI config
├── AGENTS.md                     # project instructions
└── .opencode/
    ├── agents/
    │   └── <agent-name>.md
    ├── commands/
    │   └── <command>.md
    └── plugins/
        └── my-plugin.ts          # or .js
```

**Load order** (all plugins run in sequence — hooks from all sources fire):
1. Global config (`~/.config/opencode/opencode.json`)
2. Project config (`opencode.json`)
3. Global plugin directory (`~/.config/opencode/plugins/`)
4. Project plugin directory (`.opencode/plugins/`)

Both `agents/` and `commands/` directories support singular names (`agent/`, `command/`) for backwards compatibility.

Source: [opencode — Config](https://opencode.ai/docs/config/), [opencode — Plugins](https://opencode.ai/docs/plugins/)

### 4.2 Config Schema — `opencode.json`

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4",
  "default_agent": "build",
  "autoupdate": true,
  "plugin": ["opencode-wakatime", "@my-org/custom-plugin"],
  "instructions": ["CONTRIBUTING.md", "docs/guidelines.md", ".cursor/rules/*.md"],
  "permission": {
    "bash": "allow",
    "edit": "ask",
    "write": "ask"
  },
  "mcp": {
    "jira": {
      "type": "remote",
      "url": "https://jira.example.com/mcp",
      "enabled": true
    },
    "local-server": {
      "type": "local",
      "command": "node",
      "args": ["./dist/mcp-server.js"]
    }
  },
  "server": {
    "port": 4096,
    "hostname": "localhost"
  },
  "command": {
    "test": {
      "template": "Run the full test suite with coverage report.",
      "description": "Run tests with coverage",
      "agent": "build",
      "model": "anthropic/claude-3-5-sonnet-20241022"
    }
  }
}
```

### 4.3 Plugin Files — TypeScript/JavaScript Modules

Plugins are TypeScript or JavaScript modules placed in `.opencode/plugins/` (project) or `~/.config/opencode/plugins/` (global). Files are auto-loaded at startup. Bun is the runtime.

#### Basic structure

```typescript
import type { Plugin } from "@opencode-ai/plugin"

export const MyPlugin: Plugin = async ({ project, client, $, directory, worktree }) => {
  // Initialization code runs once at startup

  return {
    // Return an object mapping event names to handlers
    "tool.execute.before": async (input, output) => {
      // input: the original tool call info
      // output: mutable object to modify before execution
    },
    "session.idle": async ({ event }) => {
      // fires when a session becomes idle
    },
  }
}
```

#### Plugin context object

| Property | Type | Notes |
|---|---|---|
| `project` | object | Current project information. |
| `directory` | string | Current working directory. |
| `worktree` | string | Git worktree path. |
| `client` | SDKClient | Full SDK client for interacting with opencode's API. |
| `$` | BunShell | Bun's shell API for executing commands. |

#### Available hook events

**Command events:**
- `command.executed`

**File events:**
- `file.edited`
- `file.watcher.updated`

**Installation events:**
- `installation.updated`

**LSP events:**
- `lsp.client.diagnostics`
- `lsp.updated`

**Message events:**
- `message.part.removed`
- `message.part.updated`
- `message.updated`

**Provider events:**
- `provider.auth.updated`

**Session events:**
- `session.chat.updated` — fires when session chat content changes
- `session.created`
- `session.deleted`
- `session.error`
- `session.idle`
- `session.updated`

**Tool events:**
- `tool.execute.after`
- `tool.execute.before`
- `tool.state.updated`

**Experimental events:**
- `experimental.chat.system.transform` — modify the system prompt
- `experimental.session.compacting` — fires before LLM generates compaction summary; inject context via the `prompt` property

Source: [opencode — Plugins](https://opencode.ai/docs/plugins/)

#### Custom tools in plugins

```typescript
import { type Plugin, tool } from "@opencode-ai/plugin"

export const CustomTools: Plugin = async (ctx) => {
  return {
    tool: {
      mytool: tool({
        description: "A custom tool",
        args: {
          foo: tool.schema.string(),
        },
        async execute(args, context) {
          const { directory, worktree } = context
          return `Hello ${args.foo} from ${directory}`
        },
      }),
    },
  }
}
```

#### npm-published plugins

Add to `opencode.json`:
```json
{
  "plugin": ["opencode-wakatime", "@my-org/custom-plugin"]
}
```

Bun automatically installs and caches packages in `~/.cache/opencode/node_modules/`.

#### Dependencies for local plugins

Create `package.json` in the config directory (global or project):
```json
{
  "dependencies": {
    "shescape": "^2.1.0"
  }
}
```
opencode runs `bun install` at startup. Plugins can then `import` these packages.

### 4.4 Agent Files — `agents/<name>.md`

```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
permission:
  bash: deny
  edit: deny
  write: deny
  read: allow
hidden: false
---

You are a thorough code reviewer. Focus on maintainability, correctness, and adherence to project conventions. Do not modify files.
```

| Frontmatter field | Type | Notes |
|---|---|---|
| `description` | string | What the agent does and when to use it. Used for `@agent` autocomplete and subagent auto-selection. |
| `mode` | string | `primary`, `subagent`, or `all`. Default: `all`. Controls where the agent appears (Tab cycle vs `@` mention). |
| `model` | string | Model in `provider/model` format. Overrides global default. |
| `temperature` | float | LLM temperature. |
| `tools` | object | Deprecated. Use `permission` instead. Key: tool name, value: boolean. |
| `permission` | object | Fine-grained permission map. Values: `allow`, `deny`, `ask`. |
| `hidden` | boolean | Hide from `@` autocomplete (used for programmatic agents). |
| `max_steps` | integer | Max agentic iterations before forced text-only response. |
| `prompt` | string | Path to a separate system prompt file. |

**Agent mode values:**
- `primary`: Agent appears in the Tab-cycle for the main conversation. User can switch to it with Tab.
- `subagent`: Agent is available only via `@agent-name` mention or automatic delegation. Subagents are invoked in a child session.
- `all`: Agent is available both ways (default).

**Subagent invocation:**
```
@general help me search for this function
```

**Primary agent switching:** Tab key (or configured `switch_agent` keybind).

**Built-in agents**: `build` (primary, all tools), `plan` (primary, no edits), `general` (subagent, full access except todo), `explore` (subagent, read-only), `scout` (subagent, external research read-only).

Source: [opencode — Agents](https://opencode.ai/docs/agents/)

### 4.5 Command Files — `commands/<name>.md`

```markdown
---
description: Run tests with coverage
agent: build
model: anthropic/claude-3-5-sonnet-20241022
subtask: true
---

Run the full test suite with coverage report and show any failures.
Focus on the failing tests and suggest fixes.

Here are the current test results:
!`npm test`

Recent git commits:
!`git log --oneline -5`
```

| Frontmatter field | Type | Notes |
|---|---|---|
| `description` | string | Shown in TUI autocomplete when typing `/`. |
| `agent` | string | Agent to use for executing this command. If the agent is a subagent, triggers subagent invocation by default. |
| `model` | string | Model override for this command. |
| `subtask` | boolean | Force subagent invocation even if `agent.mode` is `primary`. |

#### Template features

- `$ARGUMENTS` — replaced with all user-provided arguments after the command name.
- `$1`, `$2`, `$3` ... — positional argument placeholders.
- `` !`command` `` — execute a shell command and inject output into the prompt.
- `@filename` — include a file's contents in the prompt.

Invocation: `/command-name [arguments]`

File name becomes command name: `test.md` → `/test`, available from the next session start.

Source: [opencode — Commands](https://opencode.ai/docs/commands/)

### 4.6 MCP Integration

```json
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": "node",
      "args": ["./dist/mcp-server.js"],
      "env": { "API_KEY": "${MY_API_KEY}" }
    },
    "remote-server": {
      "type": "remote",
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ${TOKEN}" },
      "enabled": true
    }
  }
}
```

The `mcp` object in `opencode.json` maps server names to server configurations. Merging follows the standard config precedence: project config values override global values.

### 4.7 Permission / Allow-List Model

Permissions are configured at the global or project config level under the `permission` key:

```json
{
  "permission": {
    "bash": "allow",
    "edit": "ask",
    "write": "deny",
    "read": "allow"
  }
}
```

Per-agent permission overrides are set in the agent's frontmatter `permission` object. Agent permissions override the global config for sessions using that agent.

The `tools` frontmatter field in agents is deprecated in favor of `permission`.

**Task tool permissions** (controls which subagents an agent can spawn):
```yaml
permission:
  task: "agent-name-*"    # glob pattern
```

### 4.8 Rules / Instructions — `AGENTS.md`

opencode reads `AGENTS.md` from multiple locations (project root, global). It also supports `CLAUDE.md` as a fallback (for users migrating from Claude Code). Precedence (first match wins per category):
1. Local `AGENTS.md` (traversing up from current directory)
2. `CLAUDE.md` (if no `AGENTS.md`)
3. Global `~/.config/opencode/AGENTS.md`
4. Global `~/.claude/CLAUDE.md` (if no opencode global file)

Additional instruction files can be declared in `opencode.json`:
```json
{
  "instructions": ["CONTRIBUTING.md", "docs/guidelines.md", ".cursor/rules/*.md"]
}
```

Source: [opencode — Rules](https://opencode.ai/docs/rules/)

### 4.9 SDK Client in Plugins

Plugins receive `ctx.client`, an SDK client organized into sub-clients:

| Sub-client | Key methods |
|---|---|
| `session` | `list()`, `create()`, `get()`, `delete()`, `prompt()`, `status()`, `abort()`, `fork()`, `share()` |
| `config` | `get()`, `update()` |
| `command` | `list()` |
| `file` | `list()`, `read()`, `status()` |
| `find` | `text()`, `files()`, `symbols()` |
| `tool` | `ids()`, `list()` |
| `mcp` | `status()`, `add()`, `connect()`, `disconnect()` |
| `tui` | `appendPrompt()`, `submitPrompt()`, `executeCommand()`, `showToast()` |
| `app` | `log()`, `agents()` |
| `vcs` | `get()` |

The complete API is auto-generated from OpenAPI specs at `packages/sdk/js/src/gen/`.

Source: [opencode-plugins-manual — SDK client](https://github.com/joshuadavidthomas/opencode-plugins-manual/blob/main/docs/08-sdk-client.md)

---

## 5. Cross-runtime Command Surface

The seven CTMv3 commands and how they are invoked on each runtime. The convention for each runtime's skill/command namespace is:
- **Claude Code plugin**: `/ctmv3:<command>` (namespaced under the `ctmv3` plugin)
- **Claude Code standalone**: `/<command>` (if installed standalone in `.claude/skills/`)
- **Codex CLI**: `$ctmv3-<command>` (skill mention syntax; implicit invocation also available)
- **Gemini CLI extension**: `/ctmv3:<command>` (namespaced extension command via `commands/ctmv3/<command>.toml`)
- **Gemini CLI standalone**: `/<command>` (project command in `.gemini/commands/<command>.toml`)
- **opencode**: `/<command>` (markdown command in `.opencode/commands/<command>.md`)

| CTMv3 Command | Claude Code (plugin) | Claude Code (standalone) | Codex CLI | Gemini CLI (extension) | Gemini CLI (standalone) | opencode |
|---|---|---|---|---|---|---|
| `activate` | `/ctmv3:activate` | `/activate` | `$ctmv3-activate` | `/ctmv3:activate` | `/activate` | `/activate` |
| `boot` | `/ctmv3:boot` | `/boot` | `$ctmv3-boot` | `/ctmv3:boot` | `/boot` | `/boot` |
| `warm` | `/ctmv3:warm` | `/warm` | `$ctmv3-warm` | `/ctmv3:warm` | `/warm` | `/warm` |
| `architecture-map` | `/ctmv3:architecture-map` | `/architecture-map` | `$ctmv3-architecture-map` | `/ctmv3:architecture-map` | `/architecture-map` | `/architecture-map` |
| `sovereign-init` | `/ctmv3:sovereign-init` | `/sovereign-init` | `$ctmv3-sovereign-init` | `/ctmv3:sovereign-init` | `/sovereign-init` | `/sovereign-init` |
| `dot-init` | `/ctmv3:dot-init` | `/dot-init` | `$ctmv3-dot-init` | `/ctmv3:dot-init` | `/dot-init` | `/dot-init` |
| `session-close` | `/ctmv3:session-close` | `/session-close` | `$ctmv3-session-close` | `/ctmv3:session-close` | `/session-close` | `/session-close` |

#### Notes

**Claude Code plugin mode** (`/ctmv3:<command>`):  
Skills live in `skills/<command>/SKILL.md` at the plugin root. The plugin name is `ctmv3` as set in `.claude-plugin/plugin.json`. The colon separator is automatic.

**Claude Code standalone mode** (`/<command>`):  
Skills live in `.claude/skills/<command>/SKILL.md` or `.claude/commands/<command>.md`. The slash command name is the directory/file name directly.

**Codex CLI** (`$ctmv3-<command>`):  
Each command is a separate skill in `.agents/skills/ctmv3-<command>/SKILL.md`. The `$` prefix in the prompt explicitly mentions the skill. Codex may also auto-select skills based on description matching (implicit invocation). Using a consistent prefix like `ctmv3-` prevents name collisions with other installed skills. Alternatively, all seven commands can be sub-skills with a shared description prefix.

**Gemini CLI extension mode** (`/ctmv3:<command>`):  
Commands live in `commands/ctmv3/<command>.toml` within the extension directory. The subdirectory name (`ctmv3`) becomes the namespace prefix, and the file name becomes the command name, joined by a colon. After install, commands become `/ctmv3:activate`, etc.

**Gemini CLI standalone mode** (`/<command>`):  
Commands live in `.gemini/commands/<command>.toml` in the project root (or `~/.gemini/commands/` globally). No namespace prefix is added.

**opencode** (`/<command>`):  
Commands live in `.opencode/commands/<command>.md` (project) or `~/.config/opencode/commands/<command>.md` (global). Invoked with `/command-name` directly. No namespace mechanism exists for standalone commands; consider a naming prefix like `ctmv3-activate` if collision avoidance is needed (`/ctmv3-activate`).

---

## Appendix: Cross-runtime Feature Matrix

| Feature | Claude Code | Codex CLI | Gemini CLI | opencode |
|---|---|---|---|---|
| Skill/command file format | `SKILL.md` (YAML frontmatter + markdown) | `SKILL.md` (YAML frontmatter + markdown) | `.toml` (TOML fields) | `.md` (YAML frontmatter + markdown) |
| Plugin manifest | `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` | `gemini-extension.json` | No manifest; plugins are JS/TS modules |
| Namespace prefix | Plugin: `/plugin-name:skill` | `$skill-name` | Extension: `/ext-name:cmd` (dot sep for conflict) | No namespace; flat `/command` |
| Hook config file | `hooks/hooks.json` | `hooks/hooks.json` (or `config.toml`) | `hooks/hooks.json` (NOT in manifest) | TypeScript event handler in plugin module |
| MCP config | `.mcp.json` (project) or `~/.claude.json` | `config.toml` `[mcp_servers.X]` | `settings.json` `mcpServers` | `opencode.json` `mcp` object |
| Subagent file format | `agents/<name>.md` (YAML frontmatter + markdown) | Prompt-driven; `agents/openai.yaml` for metadata | `agents/<name>.md` | `agents/<name>.md` (YAML frontmatter + markdown) |
| Implicit skill invocation | Yes (controlled by `disable-model-invocation`) | Yes (controlled by `allow_implicit_invocation`) | N/A (commands are explicit only) | Agents: auto-delegation by description match |
| Project-scoped config | `.claude/` | `.codex/`, `.agents/` | `.gemini/` | `.opencode/`, `opencode.json` |
| Global config | `~/.claude/` | `~/.codex/` | `~/.gemini/` | `~/.config/opencode/` |
| Context/instructions file | `CLAUDE.md` | `AGENTS.md` (+ override variants) | `GEMINI.md` | `AGENTS.md` (falls back to `CLAUDE.md`) |
| Marketplace/distribution | Yes (`claude-plugins-official`, community) | Yes (marketplace.json catalogs) | No formal marketplace (GitHub install) | npm packages |
| Agent Skills standard | Yes (agentskills.io with extensions) | Yes (agentskills.io base) | Yes (agentskills.io base) | No (proprietary TypeScript module) |
