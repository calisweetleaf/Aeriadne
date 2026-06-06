# SovereignMCP / BB7 — Canonical Server Card

Type: MCP/server reference  
Status: canonical-reference  
Vendored: no  
Canonical root: `/home/daeron/Somnus-MCP`  
Canonical data root: `/home/daeron/Somnus-MCP/data`

## Purpose

BB7/SovereignMCP is the canonical tool/server plane for memory-first continuity, context resurrection, journal/decision provenance, file/context persistence, cognitive routing, and session-aware orchestration.

Aeriadne references BB7 as the server/tool substrate. Aeriadne does **not** fork it, vendor it, or replace it.

## Capability classes

- `memory_context`
- `context_resurrection`
- `file_context_persistence`
- `journal_decision_provenance`
- `cognitive_routing`
- `session_continuity`
- `agent_orchestration`

## Boundary

Do not copy secrets, runtime databases, session state, auth files, logs, cache directories, or server implementation internals into Aeriadne packages.

## Marketplace meaning

This card lets a private marketplace show that Aeriadne can depend on BB7/Sovereign-style capabilities while preserving the server plane as a separate canonical artifact.
