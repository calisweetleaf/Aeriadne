# MEMORY

## Durable Decisions

- `Modern-ML` is an **onboarding/control-plane and private marketplace staging workspace** for agent operability, not a generic ML repo and not the whole sovereign ML empire.
- **Codex is the active state machine.** Plugins, skills, hooks, Mentat, CTMv3, BB7/Sovereign, and CodeGraph are assistive cognitive/environment/state-machine support surfaces.
- Plugins are **not** BB7 replacements. They make the environment smarter, offload cognition, route context, inject state, package skills/agents, and improve Codex state transitions.
- Active server/MCP plane for current Codex work is `/home/daeron/Somnus-MCP`, with `SOVEREIGN_DATA_DIR=/home/daeron/Somnus-MCP/data`.
- `Servers/Muaddib -> /home/daeron/Repositories/Muaddib` is a visible workspace mirror/symlink artifact, but it is not the active Codex server root.
- `ARCHITECTURE_MAP.md` is the interaction-level companion to inventory docs and should explain how planes interlock, not just where files live.
- `ECOSYSTEM_ADOPTION_MAP.md` is the broader coverage companion and should explain which repos/domains are visibly represented by the current onboarding stack.
- `REPO_ENTRY_MATRIX.md` is the operational readiness companion and should track repo-by-repo doctrine presence, mirror coverage, primary entry surfaces, and practical onboarding readiness.

## Plugin/Package Ontology

- **Aeriadne = current canonical CPF/private-marketplace plugin package** in `plugins/Aeriadne/`.
- Aeriadne is a **skill-activated plugin**: the plugin shell handles manifests, registry, marketplace, adapters, agent prompt packs, and MCP/server cards; the skills remain the executable cognitive payloads.
- Aeriadne contains exactly two first-class skills in v1:
  - `constitutional-prompt-framework`
  - `aeriadne-marketplace-operator`
- `constitutional-prompt-framework` is copied from `/home/daeron/.codex/skills/custom/constitutional-prompt-framework`; the direct custom skill remains the authoring source and should not be deleted without explicit approval.
- `aeriadne-marketplace-operator` is the new package/registry/adapter/marketplace/MCP-card skill. It prevents CPF from becoming overloaded with marketplace mechanics.
- Expected Codex exposure after future install:
  - `aeriadne:constitutional-prompt-framework`
  - `aeriadne:aeriadne-marketplace-operator`
- The earlier `CPF-Plugin-Ariadne` / `cpf-plugin-ariadne` naming is now alias/conflict metadata only; canonical id is `aeriadne`.
- **Codex Config Topology plugin shell = deleted from staging** by operator decision; the standalone `codex-config-topology` skill remains useful.
- **CTMv3 / Cognitive-Topology-Map = workspace activation / topology package** in `plugins/Cognitive-Topology-Map/`. Do not describe it as merely a skill maker.
- **Mentat = plugin/runtime substrate** in `plugins/Mentat/`.

## Durable Structure Facts

- Agent entries under `Agents/` are mostly symlinked/mirrored from `/home/daeron/.claude/agents/`.
- Skill entries under `Skills/` are mixed topology:
  - some are local to this repo,
  - many are symlinked/mirrored from `/home/daeron/.opencode/skills/custom/`.
- The active Sovereign MCP server is rooted at `/home/daeron/Somnus-MCP` outside this workspace.
- The stack is split across:
  - local Modern-ML payloads,
  - symlinked install/canonical roots,
  - the local Codex plugin cache,
  - the local plugin marketplace,
  - and the external Somnus-MCP server plane.
- `plugins/Aeriadne/mcp/` is a catalog/reference corner. It must not vendor BB7/SovereignMCP or create a per-plugin BB7 data root.

## Codex Config Topology — Plugin Shell Deletion Note

- Old plugin shell deleted from this staging tree; no longer in the active plugin triad.
- Previously installed as `codex-config-topology@local` (still active in Codex config if not uninstalled).

## Aeriadne Staging Facts — 2026-06-05

- `plugins/Aeriadne/` exists and contains plugin metadata, registry, marketplace cards, adapters, agents, MCP cards, scripts, tests, and two skills.
- `aeriadne` is not yet installed/enabled in Codex.
- Expected plugin-skill exposure after install:
  - `aeriadne:constitutional-prompt-framework`
  - `aeriadne:aeriadne-marketplace-operator`
- Validation evidence from `plugins/Aeriadne/`:
  - package validator: `PASS`
  - JSON manifests: `PASS`
  - TOML manifest: `PASS`
  - plugin metadata mirrors identical: `PASS`
  - CPF skill package validation: `PASS`
  - CPF example constitution linter: `PASS`
  - CPF example constitution score: `87/100`, production candidate
  - CPF static evals: `PASS`
  - CPF render fixture wrote `/tmp/aeriadne-cpf-rendered-check.md` (`3165` bytes)
- No git push and no plugin install were performed in the staging pass.

## Gotchas

- Do not describe all of `Skills/` as local; that is false.
- Do not collapse Mentat, CTMv3, Codex Config Topology, Aeriadne, BB7/Sovereign, and the server plane into one layer. They are adjacent support surfaces with different jobs.
- Do not describe `cognitive-topology-v3` as “the skill maker”; that framing loses the codebase-entry / portable-workspace function.
- Do not describe plugins as tool replacements for `bb7_` functions. Use the state-machine support surface framing.
- Do not cite `/home/daeron/Repositories/Muaddib` as the active Codex server plane. Use `/home/daeron/Somnus-MCP` for current active server-plane references.
- The direct `codex-config-topology` authoring skill and the installed `codex-config-topology@local` plugin can coexist.
- The direct `constitutional-prompt-framework` custom skill and staged `Aeriadne` package can coexist; do not remove the direct skill without explicit approval.
- Do not install both `aeriadne@local` and the legacy `cpf-plugin-ariadne@local` unless duplicate CPF exposure is intentional.
- If Daeron says "three plugins," the current active triad is: **Aeriadne**, **Cognitive-Topology-Map (CTMv3)**, **Mentat**. Codex-Config-Topology is skill/control-plane material, not an active plugin shell in this staging tree.

## Recommended Next Structural Move

- Install `aeriadne@local` when approved, using the proven local marketplace/cache pattern from `codex-config-topology@local`.
- Create root-level `Registry/`, `Marketplace/`, `Adapters/`, and `MCP/` surfaces to graduate from package-local to repo-level private marketplace.
- Add `Servers/Somnus-MCP -> /home/daeron/Somnus-MCP` symlink or reference so future cold-entry agents land on the active server plane, not the legacy Muaddib mirror.

## 2026-06-05 — Grok Build configurator staged as canonical skill package

- `skills/grok-build-configurator/` is now the canonical staging copy for the Grok Build configurator skill inside Somnus-Intellligence-Stack.
- `/home/daeron/.local/bin/grok` was updated so the isolated one-skill Grok runtime syncs this repo copy into `/home/daeron/.grok/runtime-home/skills/grok-build-configurator` on launch.
- The repo skill package was cleaned for staging: unsafe local template drift was reset to safer defaults, `scripts/__pycache__/` was removed, `manifest.json` no longer lists `.pyc` artifacts, and the README documents public-clean exclusions.
- Distribution decision: GitHub/private repo is the source/audit transport; the marketplace/registry layer should be the install/discovery/version surface across Codex, Claude Code, OpenCode, and Grok Build via runtime-specific adapters.
- Public/open-source boundary: ship Muaddib/Sovereign server code, schemas/cards/docs/installers/examples; do not ship Muaddib flywheel data, BB7 memories/state, sessions, q-tables, auth material, logs, or checkpoints.

## 2026-06-05 — Aeriadne marketplace package debug and old plugin deletion

- Debug result: the former legacy plugin archive had live `.codex-plugin/` and `.claude-plugin/` marker directories, including a root stale `parallax-narthex` descriptor and legacy `cpf-plugin-ariadne` descriptors. These could confuse recursive marketplace/plugin scans and re-expose archived packages.
- Daeron decided that technical provenance should not be public package material; the old plugin archive was deleted from the staging tree.
- Active CPF/private-marketplace package is `plugins/Aeriadne/` with canonical path `/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne`; old names remain alias/conflict metadata only.
- Aeriadne manifests/docs were realigned from stale `/home/daeron/Projects/Modern-ML/Plugins/Aeriadne` to the actual `Somnus-Intellligence-Stack` repo path.
- Aeriadne validator now gates stale path markers, backup/cache churn, canonical path drift, metadata mirror drift, and reappearance of the deleted legacy archive. Final validation passed with `PYTHONDONTWRITEBYTECODE=1`.

## 2026-06-06 — Documentation sweep and GitHub About alignment

- Performed a comprehensive sweep of the repository's documentation. Created `desk/PLAN.md` mapping the polish plan.
- Reconstructed `README.md` to align with the Somnus Documentation Design System v3, centering the logo, setting up badges, adding a Unicode-based Plugin Triad matrix, detailing Mentat/CTMv3/Aeriadne, and mapping out the marketplace planes.
- Drafted operator-grade, plain-text candidate descriptions for the GitHub About tab to replace the verbose legacy text within the 350-character limit.
