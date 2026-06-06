# Grok Build Command Cheatsheet

## Install

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
grok --version
grok update
```

```powershell
irm https://x.ai/cli/install.ps1 | iex
grok --version
```

## Auth

```bash
grok login
grok login --device-auth
export XAI_API_KEY="xai-..."
```

OIDC env:

```bash
export GROK_OIDC_ISSUER="https://acme.okta.com"
export GROK_OIDC_CLIENT_ID="0oa1b2c3d4e5f6g7h8i9"
export GROK_CLI_CHAT_PROXY_BASE_URL="https://grok-proxy.acme.com/v1"
```

External provider env:

```bash
export GROK_AUTH_PROVIDER_COMMAND="/usr/local/bin/my-auth-provider"
export GROK_AUTH_PROVIDER_LABEL="Acme Corp"
export GROK_AUTH_TOKEN_TTL=3600
```

## Interactive

```bash
grok
grok --cwd ~/projects/my-app
grok --rules "Always use TypeScript. Prefer functional components."
grok --sandbox workspace
grok -m grok-build
grok -c
grok --resume <session-id>
```

Useful slash commands:

```text
/model grok-build
/mcps
/hooks
/plugins
/skills
/terminal-setup
/memory
/flush
/dream
/loop 5m Run tests and report new failures
/plan
/view-plan
```

## Headless

```bash
grok -p "Explain this codebase"
grok -p "Review changes for bugs" --output-format json
grok -p "Run tests and fix failures" --cwd ~/projects/my-app --yolo
grok -p "Review this code" --tools "read_file,grep,list_dir"
grok -p "Review this code" --disallowed-tools "run_terminal_cmd,web_search,web_fetch,search_replace"
```

Safe CI review:

```bash
grok -p "Review this PR for bugs. Return JSON." \
  --output-format json \
  --no-auto-update \
  --permission-mode dontAsk \
  --allow 'Read' \
  --allow 'Grep' \
  --allow 'Bash(git *)' \
  --allow 'Bash(gh *)' \
  --sandbox read-only
```

## Inspect and debug

```bash
grok inspect
grok inspect --json
grok models
grok mcp list
grok mcp list --json
GROK_LOG_FILE=1 GROK_LOG_FILTER=debug grok -p "hello" --output-format json
tail -f ~/.grok/logs/tracing.log
```

## MCP

```bash
grok mcp add my-server --command npx --args "-y @modelcontextprotocol/server-filesystem /tmp"
grok mcp add remote-api --url https://mcp.example.com/api
grok mcp remove my-server
```

## Important paths

```text
~/.grok/config.toml
~/.grok/pager.toml
~/.grok/auth.json
~/.grok/sessions/
~/.grok/memory/
~/.grok/skills/
~/.grok/plugins/
~/.grok/agents/
~/.grok/hooks/
~/.grok/logs/
.grok/config.toml
.grok/skills/
.grok/hooks/
.grok/agents/
.grok/sandbox.toml
.grok/lsp.json
AGENTS.md
```
