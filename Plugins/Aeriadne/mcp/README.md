# Aeriadne MCP Corner

This is a marketplace/server catalog corner, not a vendored server bundle.

Aeriadne documents which MCP/server planes a package expects, how they should be described in the registry, and which capability classes they provide. It does not copy BB7/SovereignMCP, CodeGraph, Mentat, runtime databases, auth files, or server source into the plugin package.

## Canonical v1 server card

- `servers/sovereign-bb7.md` — canonical reference for Somnus-MCP / BB7 capability surfaces.

## Capability contracts

- `contracts/tool-capabilities.yaml` — stable capability categories.
- `contracts/client-bindings.yaml` — which clients are expected to bind or only document each capability.

## Rule

Catalog the server plane. Do not vendor it.
