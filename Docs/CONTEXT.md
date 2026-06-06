# Somnus-Intellligence-Stack Context

_Last updated: 2026-06-06_

## Current operating frame

This repository is the consolidation/staging workspace for Somnus agent-operability assets: skills, plugins, subagents, Muaddib/Sovereign server references, and marketplace/adapter packaging. It is not the full Modern-ML working repository; it is the private-marketplace and distribution-prep layer.

## Active consolidation state

- `skills/grok-build-configurator/` is staged as the canonical Grok Build configurator skill package for this repo.
- `/home/daeron/.local/bin/grok` sources the Grok skill from this repo and syncs it into `/home/daeron/.grok/runtime-home/skills/grok-build-configurator` on each launch, preserving the one-skill isolated Grok runtime.
- The active Grok runtime remains stripped: no MCP servers, plugins, hooks, agents, subagents, cross-runtime compatibility scans, or Grok memory surfaces.
- `plugins/Aeriadne/` is the active CPF/private-marketplace plugin package and the package-local proof pattern for marketplace manifests, cards, adapters, registry, and MCP/server cards.
- The root `README.md` has been upgraded to the Somnus v3 Design System layout, with the SVG/PNG header, clean badges, and a custom Unicode plugin triad matrix.
- `plugins/old/` has been deleted from the staging tree by operator decision.

## Distribution posture

GitHub/private repo should act as the source transport and audit surface. The marketplace/registry layer should act as the install/discovery/version surface, with runtime-specific adapters for Codex, Claude Code, OpenCode, and Grok Build. Open-source payload should include server/package code, manifests, docs, cards, installers, and examples; it should not include Muaddib flywheel data, private BB7 memory/state, sessions, q-tables, auth material, logs, checkpoints, or stale legacy plugin archives.

## 2026-06-06 update — Documentation sweep and GitHub About alignment

- Staged and verified new root `README.md` conforming to Somnus DS v3.
- Created `desk/PLAN.md` to map out remaining documentation and registry layout tasks.
- Prepared plain-text, operator-grade candidate descriptions for the GitHub About tab under the 350-character limit.

## Next sweep targets

1. Build root-level `Registry/`, `Marketplace/`, `Adapters/`, and `MCP/`/`Servers/` surfaces.
2. Verify the active plugin triad package state: Aeriadne, Cognitive-Topology-Map/CTMv3, and Mentat.
3. Apply the terminal-frame documentation aesthetic to individual plugin READMEs (`Plugins/Mentat/README.md`, etc.).
4. Run a public-clean audit before any private repo push.
