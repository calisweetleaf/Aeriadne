# Somnus-Intellligence-Stack Context

_Last updated: 2026-06-05_

## Current operating frame

This repository is the consolidation/staging workspace for Somnus agent-operability assets: skills, plugins, subagents, Muaddib/Sovereign server references, and marketplace/adapter packaging. It is not the full Modern-ML working repository; it is the private-marketplace and distribution-prep layer.

## Active consolidation state

- `skills/grok-build-configurator/` is staged as the canonical Grok Build configurator skill package for this repo.
- `/home/daeron/.local/bin/grok` sources the Grok skill from this repo and syncs it into `/home/daeron/.grok/runtime-home/skills/grok-build-configurator` on each launch, preserving the one-skill isolated Grok runtime.
- The active Grok runtime remains stripped: no MCP servers, plugins, hooks, agents, subagents, cross-runtime compatibility scans, or Grok memory surfaces.
- `plugins/Aeriadne/` is the active CPF/private-marketplace plugin package and the package-local proof pattern for marketplace manifests, cards, adapters, registry, and MCP/server cards.
- `plugins/old/` has been deleted from the staging tree by operator decision; old CPF/Parallax/Codex-Config-Topology plugin packages are not public/staged package material.

## Distribution posture

GitHub/private repo should act as the source transport and audit surface. The marketplace/registry layer should act as the install/discovery/version surface, with runtime-specific adapters for Codex, Claude Code, OpenCode, and Grok Build. Open-source payload should include server/package code, manifests, docs, cards, installers, and examples; it should not include Muaddib flywheel data, private BB7 memory/state, sessions, q-tables, auth material, logs, checkpoints, or stale legacy plugin archives.

## 2026-06-05 update — Aeriadne active marketplace package, old plugin archive deleted

- Working directory for the pass: `/home/daeron/Repositories/Somnus-Intellligence-Stack`.
- Debug finding: the former legacy plugin archive had live runtime marker directories (`.codex-plugin/`, `.claude-plugin/`) that could let recursive plugin/marketplace scans expose stale archived packages, including legacy `cpf-plugin-ariadne`, as active installables.
- Initial fix quarantined those descriptors, then Daeron decided the technical provenance was not needed for public/private staging.
- Final fix: deleted the entire legacy plugin archive from the staging tree. `plugins/Aeriadne/` is now the single active CPF/private-marketplace package surface.
- Aeriadne manifests, registry card, marketplace card, adapter docs, README, MANIFEST, roadmap, and validation artifacts are realigned to `/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne`.
- Aeriadne validator now gates stale path markers, backup/cache churn, exact manifest mirror equality, canonical path, and reappearance of the deleted legacy archive.
- Validation passed with `PYTHONDONTWRITEBYTECODE=1`: package validator PASS, JSON/TOML parse PASS, CPF skill validator PASS, stale path scan PASS, deleted-archive scan PASS, transient artifact scan PASS.

## Next sweep targets

1. Build root-level `Registry/`, `Marketplace/`, `Adapters/`, and `MCP/`/`Servers/` surfaces.
2. Verify the active plugin triad package state: Aeriadne, Cognitive-Topology-Map/CTMv3, and Mentat.
3. Decide whether Codex Config Topology remains skill-only or is later rebuilt as a fresh control-plane package; do not resurrect the deleted old plugin shell.
4. Run a public-clean audit before any private repo push: secrets, sessions, data roots, q-tables, `.pyc`, logs, archives, generated backups, and deleted legacy package remnants.
