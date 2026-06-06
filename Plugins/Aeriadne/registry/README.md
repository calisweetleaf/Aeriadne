# Aeriadne Registry

This directory is the v1 local marketplace registry for Aeriadne.

It is intentionally small and private-first. The goal is to make package contents queryable and installable later without turning the plugin into a public marketplace prematurely.

## Files

- `aeriadne.plugin.json` — JSON package card for clients/scripts that expect JSON.
- `plugins.yaml` — plugin inventory.
- `skills.yaml` — bundled skill inventory.
- `agents.yaml` — agent/subagent prompt pack inventory.
- `mcp_servers.yaml` — canonical MCP/server reference inventory.

## Rules

- Registry status must match evidence.
- Installed status requires install verification.
- MCP servers should be cataloged by canonical reference unless intentionally vendored.
- Do not include secrets, tokens, auth files, runtime databases, sessions, or caches.
