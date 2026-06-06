# Plan — Mentat v2 HTML Documentation Update + Packaging

## Phase 1 — Inventory (mentat-cartographer)

- [ ] Read plugin/adapters/codex/ and plugin/adapters/gemini/ fully — capture hook names, config shapes, install flow
- [ ] Read plugin/evals/ fully — harness interface, scenario list, script outputs, rubric scoring
- [ ] Read plugin/webhook_engine/ fully — emitter API, DLQ contract, envelope schema
- [ ] Read plugin/monitors/ fully — what each watcher observes and emits
- [ ] Read plugin/commands/*.md — each slash command's invocation and behavior
- [ ] Read plugin/agents/*.md and helpers/*.md — all 7 agent definitions (4 plugin-scoped + 3 user-scope)
- [ ] Read plugin/skills/mentat-debrief/scripts/ — actual implementation depth of the debrief pipeline
- [ ] Produce a structured inventory: per-subsystem name, file count, LOC, key API surface, status

## Phase 2 — Integration Check (mentat-medic)

- [ ] Run python3 plugin/scripts/integration_smoke.py — capture pass/fail per subsystem
- [ ] Check plugin/.claude-plugin/plugin.json — version field, file manifest accuracy
- [ ] Check plugin/mcp.json and plugin/webhooks.json for schema correctness
- [ ] Verify plugin/adapters/install_universal.sh is executable and paths are correct
- [ ] Report: which subsystems are smoke-test green vs. partial vs. not yet wired

## Phase 3 — HTML Additions (mentat-conductor → mentat-scribe)

- [ ] Insert Somnus DS v3 global styles block into HTML head (if not already present)
- [ ] Add SVG v2 identity banner section near top of doc
- [ ] Add section: Multi-Runtime Adapter System (codex + gemini, with terminal frames showing install flow)
- [ ] Add section: Evals Rig (harness architecture, scenario table, rubric scoring, benchmark output)
- [ ] Add section: Webhook Engine (envelope schema, emitter flow, DLQ, smoke test)
- [ ] Add section: Monitors (archivist, drift_watcher, entropy_watcher — terminal monitor view)
- [ ] Add section: Slash Commands (9 commands table + terminal demo)
- [ ] Add section: Agent Roster (4 plugin-scoped + 3 user-scope — intelligence panel format)
- [ ] Update stat-row stats in hero to v2 actuals (subsystem count, file count, LOC, agent count)
- [ ] Update TOC nav links to include all new sections

## Phase 4 — Repo Cleanup

- [ ] Remove or archive stale root-level files: mentat-file-tree.md (superseded by 5-22-2026 version), Archive.zip if confirmed stale, mentat-plugin.tar.gz if outdated
- [ ] Rebuild mentat-plugin.tar.gz from current plugin/ directory
- [ ] Confirm plugin.json version field matches v2 reality

## Phase 5 — Final Review

- [ ] Verify HTML renders correctly (no broken terminal frames, no overflow issues)
- [ ] Cross-check every new section against scope.md — no deferred topics injected
- [ ] Emit mentat insight: documentation v2 complete
