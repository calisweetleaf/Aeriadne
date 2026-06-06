## Durable Runtime Update — Live Display Projection Verified (2026-06-04)

- After Codex/MCP gateway reboot, live BB7 output is now using the display
  projection layer.
- `bb7_tool_health_report` rendered as `### bb7_tool_health_report: HEALTHY`
  with compact facts instead of raw JSON. Observed live identity:
  `pid=279417`, `session_id=ses_d9f6d1c251b5`, `transport=stdio`,
  `total_tools=134`, `registered_tools=134`,
  `source_sha256_16=5ba59ef01ffc865e`.
- `bb7_lisan_recall` rendered as `### bb7_lisan_recall: OK` with summarized
  memory lines instead of the full context blob.
- Both projections include the raw-hidden/raw-preserved notice and the
  `SOVEREIGN_DISPLAY_PROJECTION=raw` escape hatch.
- Artifacts written:
  `docs/validation/2026-06-04-display-projection-live-proof.md/json`.
- Future rule remains: the live Markdown projection is human display only;
  never treat it as raw Q-table observation or RFT/distillation payload.

---

## Durable Runtime Update — Display Projection Boundary (2026-06-04)

- Cleaned the noisy JSON display layer in `mcp_server.py` without changing raw
  substrate inputs. Dict/list tool payloads now become concise Markdown at the
  final `_format_tool_result(...)` seam only.
- Raw payload order is locked by validation: trajectory buffer summary, SQLite
  tool usage logging, event-spine `tool_execution_end`, ambient memory exchange,
  sovereign metadata, and auto-reflect all happen before display formatting in
  `handle_call_tool`.
- Projection metadata explicitly says it is not training/substrate truth:
  `projection_for_display_only=true`, `raw_payload_in_content=false`,
  `raw_preserved_before_projection=true`, `not_for_qtable=true`,
  `not_for_observations=true`, `not_for_distillation=true`, and
  `not_for_rft=true`.
- Exact raw JSON display remains available with `SOVEREIGN_DISPLAY_PROJECTION=raw`;
  projection length is bounded by `SOVEREIGN_DISPLAY_PROJECTION_MAX_CHARS`.
- Preformatted MCP `content` payloads bypass projection unchanged.
- Added `scripts/validate_display_projection.py` and artifacts
  `docs/validation/2026-06-04-display-projection.md/json`; validation passed
  `31` checks including raw-order static checks, formatter smoke tests, raw
  escape hatch, MCP content passthrough, boolean success title cleanup, and
  fail-loud raw fallback on projection errors.
- Updated `scripts/run_muadib_one_plane_validation.py` so the strict suite now
  composes self-play, display projection, source gate, runtime audit, live gate,
  and completion audit. Strict source+live suite passed with `ok=true`,
  `source_suite_ok=true`, `completion_ready=true`, `live_status=PASS`, source
  checks `23`, display checks `31`, self-play checks `15`, and source+live gate
  checks `29`.
- Updated `scripts/write_muadib_completion_audit.py` so the generated completion
  audit explicitly records `display_projection_not_substrate_truth=proved`.
- Rule for future work: cleaned Markdown display summaries are for humans only.
  Do not use them as Q-table observations, ambient memory raw payloads, or
  distillation/RFT records.

---

## Durable Validation Update — Post-Reboot Live Parity Complete (2026-06-04)

- Codex/MCP gateway was rebooted/rebound and fresh live health now proves
  current-source registry parity.
- Captured post-reboot health evidence in
  `docs/validation/2026-06-04-bb7-tool-health-post-reboot.json`.
- Fresh `bb7_tool_health_report` evidence:
  - `status=healthy`;
  - `total_tools=134`;
  - `runtime_identity.pid=142824`;
  - `runtime_identity.session_id=ses_4ae8c045bbba`;
  - `runtime_identity.data_dir=/home/daeron/Somnus-MCP/data`;
  - `runtime_identity.source_sha256_16=4600f1e1a25efef7`;
  - `registered_tools` includes `bb7_muadib_mentat_bridge` and
    `bb7_tool_refresh_module`.
- Strict validation passed:
  `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --live-health-json docs/validation/2026-06-04-bb7-tool-health-post-reboot.json --require-live --json`
  => `ok=true`, `source_suite_ok=true`, `completion_ready=true`,
  `live_status=PASS`, source checks `22`, self-play checks `15`, live checks
  `28`, live failed `[]`.
- Generated completion audit now reports `complete=true`,
  `completion_ready=true`, `live_status=PASS`, and no pending requirements.
- Direct `bb7_muadib_mentat_bridge(operation="snapshot")` call succeeded after
  reboot and proved the bridge is live/registry-bound/read-only:
  `mcp_server_is_intelligence=false`, `gateway_process_is_cognition_plane=false`,
  `one_cognition_data_plane=true`, `mutates_mcp_output_adapter=false`, active
  tokenizer checkpoint `checkpoint_v5327.safetensors`, checkpoint format
  `safetensors`, checkpoint bytes `49281756`, advanced bridge active, and
  exoskeleton indexed tools `134`.
- `docs/validation/2026-06-04-muadib-one-plane-gate.*` was refreshed to
  `source_gate_pass_self_play_weights_pass_live_gate_pass`.

---

## Durable Validation Update — Generated Completion Audit (2026-06-04)

- `scripts/write_muadib_completion_audit.py` is now the repo-native generator
  for `docs/validation/2026-06-04-muadib-completion-audit.md/json`.
- `scripts/run_muadib_one_plane_validation.py` invokes the audit writer after
  writing the suite JSON, embeds a `completion_audit` summary, and rewrites the
  suite artifacts so the suite/audit outputs agree.
- `scripts/verify_muadib_one_plane_gate.py` now passes **22** source checks,
  including `completion_audit_writer_present` and
  `completion_audit_artifact_present`.
- `docs/validation/2026-06-04-muadib-one-plane-gate.*` was refreshed to embed
  the 22-check source gate and a `completion_audit_writer` PASS block.
- Full validation passed:
  - `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json`
    => `ok=true`, `source_suite_ok=true`, `completion_ready=false`,
    `live_status=PENDING_RELOAD`, self-play checks `15`, source checks `22`;
  - compile/json validation passed for gateway/Muad'Dib/meta/access-gateway
    files plus all one-plane validation artifacts;
  - synthetic current-source strict live health passed with
    `completion_ready=true`, proving the audit can flip after real live reload.
- Actual connected live health sampled at timestamp `1780577252.1807277`
  remains old-source: `status=healthy`, `total_tools=129`, no
  `runtime_identity`, no `registered_tools`, no bridge/refresh surfaces.
- Do not mark the active one-plane objective complete until a fresh
  post-reload `bb7_tool_health_report` JSON passes:
  `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --live-health-json <health.json> --require-live --json`.

---

## Durable Validation Update — Muad'Dib Completion Audit (2026-06-04)

- Added `docs/validation/2026-06-04-muadib-completion-audit.md` and `.json` as the requirement-by-requirement audit for the active one-plane objective.
- The audit maps the original objective to evidence for: raw JSON adapter preservation, gateway-not-intelligence doctrine, meta-intelligence/Mentat bridge, access gateway doctrine, real Muad'Dib safetensors self-play weights, promotion drift control, one-plane runtime observability, and post-reload live registry proof.
- Current verdict is `complete=false`, `source_suite_ok=true`, `completion_ready=false`, `live_status=PENDING_RELOAD`.
- Live-pending rows roll up to the same blocker: after reload, a fresh `bb7_tool_health_report` must expose current-source `runtime_identity`, deterministic `registered_tools`, `bb7_muadib_mentat_bridge`, and `bb7_tool_refresh_module`.
- `scripts/verify_muadib_one_plane_gate.py` now checks `completion_audit_artifact_present`; source gate passes 21 checks.
- Final completion command remains: `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --live-health-json <health.json> --require-live --json`.

---

## Durable Validation Update — Muad'Dib One-Plane Suite Runner (2026-06-04)

- Added `scripts/run_muadib_one_plane_validation.py` as the repo-native one-plane validation suite runner.
- It composes existing validators instead of duplicating source truth: isolated self-play weights, source one-plane gate, runtime identity audit, and optional post-reload live health JSON.
- It does not instantiate `MCPServer`, restart/signal runtime, mutate canonical data, or touch output adapters.
- Default mode (`--json`) passes when the source suite passes and records `live_status=PENDING_RELOAD`, `completion_ready=false`.
- Strict mode (`--live-health-json <path> --require-live --json`) exits nonzero unless live health proves current-source `runtime_identity` plus `registered_tools`.
- Validation passed:
  - default runner wrote `docs/validation/2026-06-04-muadib-validation-suite.md/json`;
  - missing-live strict mode correctly failed;
  - synthetic current-source live health strict mode passed;
  - source gate now passes 20 checks including `validation_suite_runner_present`.

---

## Durable Validation Update — Isolated Muad'Dib Self-Play Weights (2026-06-04)

- Added `scripts/validate_muadib_self_play_weights.py` as the safe isolated proof path for Muad'Dib self-play tensor weights.
- The validator uses `DigitalTwinTool(data_dir=temp)` only and never imports/instantiates `MCPServer`, so it avoids canonical runtime writes and output-adapter risk.
- Current validation passed 15 checks and wrote real non-empty `.safetensors` candidate files in a temp data dir:
  - archive-only default: `self_play_head_v1.safetensors`, ~19.9 MB, `promoted=false`, `qtable_updated=false`;
  - locked promotion request: `self_play_head_v2.safetensors`, `promotion_requested=true`, `promoted=false`, `active_locked=true`.
- The validator verifies checkpoint sha256 values against the files and cleans the temp data dir after the run.
- Dedicated artifacts: `docs/validation/2026-06-04-muadib-self-play-weights.md` and `.json`.
- `scripts/verify_muadib_one_plane_gate.py` now checks both the isolated validator source and the recorded validation artifact. Source gate now passes 19 checks.
- This proves current source can produce real safetensors self-play weights; it does not by itself prove connected live BB7/SovereignMCP has reloaded current source.

---

## Durable Doctrine Update — Health Registered-Tools Projection (2026-06-04)

- Current-source `bb7_tool_health_report` now emits deterministic `registered_tools=sorted(self.tools.keys())` in addition to `runtime_identity`.
- The one-plane live verifier uses `registered_tools` as the primary registry proof for `bb7_muadib_mentat_bridge` and `bb7_tool_refresh_module`; `unused_tools` is only a backward-compatible fallback.
- Reason: `unused_tools` is session-behavior telemetry and can omit a required surface after that tool has been called. It should not be the sole source/live parity proof.
- This is allowed gateway observability work: it does not alter `_format_tool_result`, JSON-RPC response shape, display cleanup, Muad'Dib weights, or adapter behavior.
- Source validation passed, including a synthetic current-source live health JSON where bridge/refresh were present only in `registered_tools`. Connected live BB7 still reports old 129-tool health without `runtime_identity`/`registered_tools` until reload.

---

## Durable Doctrine Update — HTTPS/Webhook/Hook Access Gateways (2026-06-04)

- The gateway correction applies to access/event surfaces as well as `mcp_server.py`.
- `https_wrapper.py` is authenticated transport plumbing into the existing Somnus-MCP Muad'Dib + `tools/` cognition plane. It is not an intelligence layer, output cleaner, or routine validation surrogate.
- `webhook_engine.py` is gateway event egress for the existing state-machine path. It must not own Muad'Dib weights, Q-table state, registry truth, or a second cognition plane.
- `hook_executor.py` and `HOOK_BRIDGE.md` are lifecycle/event signal gateways. Hooks feed the existing gateway/state-machine path and do not create a second server, second tool plane, or neural owner.
- `scripts/verify_muadib_one_plane_gate.py` now checks `access_gateway_doctrine_recorded`; the source gate currently passes 17 checks including this access-layer invariant.
- Validation artifacts in `docs/validation/2026-06-04-muadib-one-plane-gate.md` and `.json` now record **Access gateway doctrine gate: PASS** while live parity remains pending reload.

---

## Durable Doctrine Update — Bridge Contract Emits Gateway/Cognition Split (2026-06-04)

- `bb7_muadib_mentat_bridge` now emits the gateway doctrine in its JSON contract, not only in documentation.
- Required contract fields include `mcp_server_is_intelligence=false`, `gateway_process_is_cognition_plane=false`, `one_cognition_data_plane=true`, `stdio_gateway_children_may_exist=true`, `gateway_role`, and `cognition_plane_role`.
- Bridge payload includes `gateway.runtime_identity` when current-source `bb7_tool_health_report` provides it. Absence of that field in live health is evidence the connected gateway is old-source, not proof the cognition plane is absent.
- The verifier now checks `bridge_gateway_contract_source_present`; source gate currently passes 16 checks. Temp-data bridge smoke confirmed fake runtime identity is propagated without instantiating a real MCP server or mutating canonical state.

---

## Durable Doctrine Update — Gateway to Muad'Dib/Tools, Not Intelligence Itself (2026-06-04)

- `mcp_server.py` is the gateway/dispatcher into the 4-7 Muad'Dib + `tools/` cognition layers. It is not the intelligence itself.
- Keep `mcp_server.py` thin around transport, registry, lifecycle, raw JSON/result-boundary preservation, telemetry, and source/live observability.
- Neural weights, self-play, routing, reflection, memory synthesis, and higher-order answer compilation belong in `muadib/` and `tools/`.
- Interpret “one server one plane” as one canonical cognition/data/neural plane. Stdio can create per-client gateway child processes; that is not automatically a second cognition plane if they share the canonical data root and do not fork neural/persistence state.
- Source/live identity reports identify the gateway process answering a call; they are evidence for parity, not a claim that the gateway PID is the whole system.

---

## Durable Doctrine Update — Muad'Dib/Mentat One-Plane Bridge (2026-06-04)

- `tools/meta_intelligence_engine.py` now exposes source surface `bb7_muadib_mentat_bridge` as a read-only one-plane snapshot facade.
- The bridge composes existing live BB7 registry calls (`bb7_dt_checkpoint_status`, `bb7_dt_advanced_features`, `bb7_exo_state`, `bb7_tool_health_report`) and bounded Mentat sidecar file reads (`~/.mentat`, workspace `.mentat/scope.md`).
- It must remain observer/conductor-only: no sibling tool instantiation, no second server, no Muad'Dib weight mutation, no Q-table mutation, and no `mcp_server.py` output adapter/display-boundary changes.
- `.mentat/scope.md` and `PLAN.md` now encode the one-plane gameplan scope: preserve raw JSON until display boundary, use meta-intelligence as a registry-bound facade, keep Mentat as conductor/tap, and avoid duplicate runtimes.
- Source/schema validation passed for the bridge; live runtime exposure may require server/module reload because source truth and already-running registry truth can diverge.

### Guarded facade refresh addendum (2026-06-04)

- `mcp_server.py` now includes source surface `bb7_tool_refresh_module`, allowlisted for `meta_intelligence_engine` only. Its purpose is source/live parity for registry-bound facades without starting a second server or rerunning full boot lifecycle side effects.
- Initial boot now calls `_attach_registry_bound_facades()` so `meta_intelligence_engine.py` receives references to the existing `server.tools` and `server.tool_modules` maps.
- Refresh validation showed source boot registers 134 tools including `bb7_muadib_mentat_bridge` and `bb7_tool_refresh_module`; the refresh result reports `started_server=false`, `reran_register_tools=false`, and `output_adapter_touched=false`.
- Added `scripts/verify_muadib_one_plane_gate.py` as the deterministic gate. Source mode checks raw JSON boundary, no output-adapter special cases, meta bridge/refresh source, Muad'Dib self-play/checkpoint/lock surfaces, autonomous cadence, manifest/docs/scope/plan coverage, and recorded live caveats. Live mode additionally expects a `bb7_tool_health_report` JSON with at least 134 tools and visible `bb7_muadib_mentat_bridge`/`bb7_tool_refresh_module`.
- Validation artifacts were written to `docs/validation/2026-06-04-muadib-one-plane-gate.md` and `.json`; they record source gate PASS and live gate PENDING RELOAD.
- Gotcha: `mcp_server.py` enforces canonical `/home/daeron/Somnus-MCP/data`, so fresh `MCPServer` smoke tests can write real runtime artifacts. The 2026-06-04 refresh smoke wrote `data/digital_twin/checkpoint_v5270.safetensors` during normal Muad'Dib warm-up.
- Current live MCP process remained healthy but still reported 129 tools before reload; live exposure of the new refresh/bridge surfaces requires process reload/hot-load into the updated source.

---

## Durable Doctrine Update — Muad'Dib Promotion Lock Semantics (2026-06-04)

- Safetensors locks tensor serialization/integrity, not semantic immutability. With continuous self-play enabled, active weights advance whenever complete candidates are promoted.
- Distinguish candidate training, checkpoint archiving, and active/champion promotion. A locked active head should still allow candidate self-play archives, but must not swap the live in-memory head or active pointer.
- `bb7_dt_self_play` now reports both `promotion_requested` and `promoted`; promotion locks force archive-only training even when a caller requests promotion.
- Promotion must be opt-in by default at both public surfaces and autonomous cadence: `DigitalTwinTool.bb7_dt_self_play(promote=false)`, `ExoskeletonTool.bb7_dt_self_play(promote=false)`, and `MUADIB_SELF_PLAY_PROMOTE=0`. This prevents continuous self-play from drifting active/champion weights merely because candidate safetensors are being produced.
- Continuous self-play must stay archive-only by default: `MUADIB_SELF_PLAY_PROMOTE=0` and `bb7_dt_self_play(promote=false)` prevent active/champion drift while still writing real safetensors candidates. Use `bb7_dt_self_play_lock(locked=true, reason=...)` or `MUADIB_SELF_PLAY_LOCK_ACTIVE=1` when reproducibility/champion pinning matters. Use explicitly unlocked promotion for deliberate live learning only.
- Self-play pruning must preserve active/locked checkpoints, especially when `MUADIB_SELF_PLAY_PROMOTE=0` or promotion lock leaves the active checkpoint older than recent candidates.

---

## Durable Doctrine Update — Muad'Dib Continuous Self-Play Cadence (2026-06-04)

- Bounded continuous Muad'Dib self-play now belongs to the existing `mcp_server.py` autonomous exo cycle; do not start a second trainer daemon or duplicate server plane for this.
- The cadence calls `exo.bb7_dt_self_play(...)`, so it uses the existing exoskeleton live tool catalog and DigitalTwin instance.
- Defaults are conservative: enabled every 32 cycles, 4 episodes, 3 steps, archive complete safetensors candidates without promotion, and keep `MUADIB_SELF_PLAY_UPDATE_QTABLE=0` so synthetic play does not contaminate the real operator-trained Q-table or drift active/champion weights.
- Autonomous self-play is lifecycle training only. It must not be used as a reason to alter `_format_tool_result`, raw JSON preservation, JSON-RPC response shape, HTTPS wrapper output, or display/content-block cleanup behavior.
- Failures must be visible (`warning` log/event diagnostics) rather than silent `pass`; ordinary tool serving should continue if self-play fails.

---

## Durable Doctrine Update — Muad'Dib Safetensors Self-Play (2026-06-04)

- JSON is not neural weights. JSON files in the Muad'Dib checkpoint path are metadata, active pointers, metrics, ledgers, and compatibility state only.
- Actual tensor weights must be written as `.safetensors` when `safetensors` is available. Legacy `.pt` tokenizer checkpoints remain load-only migration fallback; new tokenizer saves prefer `checkpoint_vN.safetensors`.
- Continuous self-play should not lock a single static weight file and should not mutate live model weights in-place. Train a candidate copy, write a complete safetensors checkpoint atomically, then promote the active pointer/reference.
- Synthetic self-play must not poison the real operator-trained Q-table by default. Keep `update_qtable=false` unless explicitly doing synthetic-data experiments.
- The first implemented self-play lane is `MuadDibSelfPlayHead` (`muadib/neural_config.py`) exposed through `bb7_dt_self_play` and `bb7_dt_checkpoint_status` wrappers on the exoskeleton's live Muad'Dib instance. `mcp_server.py` output formatting was intentionally left unchanged.

---

## Durable Doctrine Update — Production-Grade Robustness Audit and Fixes (2026-06-03)

- **Loud Code Doctrine**: Imports of optional neural/lisan/substrate components wrapped in `try/except` must catch `ImportError` explicitly, and let any syntax or code regression errors throw/log loudly at `ERROR` level with track trace (instead of silently disabling the modules).
- **Cleanup Leftover Temp Files**: Systems utilizing atomic file write patterns (writing `.tmp` files and swapping) must clean up after themselves. Implemented a startup scan in `mcp_server.py` to delete leftover `*.tmp` files from aborted runs, recovering over 100MB of storage.
- **Connection Integrity**: All persistent resource handles (such as SQLite3 database connections like `self._distillation_conn`) must be explicitly closed in the server `shutdown` lifecycle to ensure data integrity.
- **Exceptions in Daemon Threads**: Background perpetual cycle exceptions must not pass silently; they should log debug or warning messages to expose underlying failures without spamming standard output.
- **Codex History Ingest**: Codex rollouts/histories are ingested from the operator's global plane (`/home/daeron/.codex/history.jsonl`) rather than local workspace directories. This is now formally documented in `MCP_SPEC.md`.

---

## Durable Doctrine Update — System-wide Tool and Spec Documentation Complete (2026-06-03)

- Fully documented all 10 tools under `tools/auto_tool_module.py` (`bb7_analyze_workflow_patterns`, `bb7_performance_optimization`, `bb7_intelligent_automation`, `bb7_cognitive_optimization`, `bb7_optimization_results`, `bb7_adaptive_learning`, `bb7_workspace_context_loader`, `bb7_show_available_capabilities`, `bb7_auto_session_resume`, `bb7_intelligent_tool_guide`) in `workflows-new.md` with detailed descriptions.
- Documented all 12 tools under `tools/file_tool.py` in `workflows-new.md` and detailed their full parameters and internal mappings in `MCP_SPEC.md`.
- Documented all 3 tools under `tools/meta_intelligence_engine.py` (`bb7_code_consciousness`, `bb7_context_weaver`, `bb7_creative_problem_solver`) in `workflows-new.md` and added a new section with parameters and internal compositions in `MCP_SPEC.md`.
- Documented `tools/openrouter_planner_tool.py` (3 tools) and `tools/openrouter_agent_tool.py` (9 tools) under section 1.4 in `workflows-new.md` to match their active specifications.
- Expanded the documentation of `tools/thought_journal_tool.py` (11 tools) to include complete parameter specifications and detailed listings in both `workflows-new.md` and `MCP_SPEC.md`.
- Verified system health and received runtime confirmation that the memory, interconnect, web, visual, auto, and meta intelligence engines are fully wired up and logging properly.


---

## Durable Doctrine Lock — Somnus-MCP Neural Substrate Migration (2026-05-27)

- Somnus-MCP is a 24/7 autonomous neural-symbolic cognition server, not a passive MCP server or flat tool harness.
- MCP JSON-RPC2/stdio/SSE/HTTPS/webhooks are transport adapters. The control plane is `mcp_server.py` + `tools/exoskeleton_tool.py` + `tools/lisan_al_gaib.py` + `muadib/*` + the continuity substrate.
- `bb7_*` methods are public answer-compilation surfaces. Describe them as routing/scoring/synthesis endpoints, not one-shot function calls.
- Canonical data root is `/home/daeron/Somnus-MCP/data`; current docs must not use `C:/Users/treyr/mcp/data` except as historical context.
- Canonical environment is `/home/daeron/Somnus-MCP/mcp.venv`; do not assume `.venv` or system Python.
- `tools/memory_tool.py`, `tools/memory_interconnect.py`, and `tools/session_manager_tool.py` are continuity substrate. They preserve memory, relationships, sessions, events, insight links, and cross-turn recoverability.
- `golden_paths.json` is executable routing config only. Audit/history metadata belongs in `golden_paths_meta.json`; Lisan/exoskeleton must filter malformed or metadata entries before routing.
- Distillation is a non-blocking telemetry/RFT witness flywheel. It is retrospective; it is not the primary decision authority.
- The Golden Path doctrine is not a fixed bootstrap ritual. Use route/plan/recall/reflect according to task scope and avoid ceremonial tool sequences that suppress learned routing.
- Advanced file migration preserves compatibility names (`bb7_append_file`, `bb7_get_file_info`, `bb7_file_cache_stats`) while adding copy/move/delete/info/history surfaces.
- `TRASH/MAYBE-TOOLS/ai_system_integration.py` is blocked on Linux by Windows-only imports and unsafe eager system-management initialization; do not auto-discover it until rewritten behind platform guards.
- Meta-intelligence must bind to the live registry through `attach_tool_plane(...)`; it must not instantiate sibling tools and create duplicate stale cognition planes.

## Advanced Bridge Signal Architecture (2026-05-23)

- Real signals in this codebase: Q-table TD values (trained_q), observation-buffer co-occurrence (trained_cooccur). These are the only signals worth blending with meaningful weight.
- `aeron_neural_memory` and `NeuralSubstrateTokenizer` weights reset every process start — they are structural scaffolding, not trained signal sources yet.
- `tool_modality.py` forward passes are all `torch.randn()` stubs — never blend their outputs into routing.
- Provenance tagging is the right pattern for mixed-reliability signal fusion: assign a weight at creation time based on signal origin, so untrained sources auto-downweight rather than requiring manual alpha tuning per signal.
- `DigitalTwinBackbone` internal attrs: `._qtable` (QTable), `._buffer` (ObservationBuffer), `._session_tail` (Dict). `DigitalTwinTool` owns it as `.backbone` (not `._backbone`).
- Circuit breaker should be lazy half-open (check elapsed time on next call), not a reset thread — fewer moving parts for a 24/7 server.

## Golden Path Doctrine Lesson (2026-05-08)

- The rigid 11-step mandatory per-turn exoskeleton loop ("Turbo Loop") was consuming 28% of all tool calls as ceremonial overhead.
- Telemetry from 3,421 plan executions showed Codex performing the sync ritual but skipping `bb7_exo_reflect` (only 3 calls = 0.04%).
- The old loop created a compliance pattern where Codex favored `bb7_run_command` (shell) at 16.4% because it was the fastest path to output after burning 11 calls on ceremony.
- Deprecated journal tools were still being called 1,087 times despite deprecation notice — Codex follows what's prescribed, not what's deprecated.
- Replaced with 3-anchor Golden Path model: Know Where You Are → Walk the Path → Remember What Matters.
- Key architectural insight: Muad'Dib Q-table + Thompson bandit + SessionMomentum V3 are always running and learning from every tool call. Prescribing exact tool sequences overrides the neural-symbolic routing that's already doing the work.
- The doctrine must never prescribe "always call X before Y" unless X is genuinely a prerequisite. The tool plane is a medium to inhabit, not a checklist to perform.
- Distillation pipeline expanded: `scripts/codex_distill_formatter.py` converts `.codex/sessions/` rollout files into Somnus trajectory format for tool-routing behavior seeding (not coding ability).

## Lessons Learned

- Kimi CLI rejects MCP config files containing a UTF-8 BOM; ensure `.kimi/mcp.json` is saved without BOM (`Format-Hex` should start with `7B`).
- Kimi's JSON-RPC client rejects `null` ids on error responses; normalize all outbound ids to string/int (fallback `0`) when the request id is missing or invalid.
- MCP tool responses must include `content` blocks (`[{"type":"text","text":...}]`); wrapping raw outputs avoids CallToolResult validation failures.
- Memory tool lambdas must use parameter names that match manifest schemas (`key`, `value`, etc.) to prevent argument binding errors.
- MSS screenshots on Windows can fail with `BGRX` decoder issues; constructing images from `BGRA` and converting to RGB avoids the crash.
- RestrictedPython `compile_restricted` may omit an `errors` attribute; guard with `getattr` before accessing.
- RestrictedPython `compile_restricted` return types vary by version; handle CompileResult vs direct code object (and tuple fallback) to avoid `'code' object has no attribute 'code'`.
- `bb7_python_execute_secure` smoke test passed after the compile-return handling fix; logs in `mcp/logs/smoke_bb7_python_execute_secure_20260108_184724.md` and `.json`.
- FastAPI now proxies JSON-RPC via `/rpc` into the in-process `MCPServer`; auth middleware still required. Batch JSON-RPC is rejected; only single-object requests accepted.

## Future Considerations

- When generating JSON config files on Windows, explicitly save as UTF-8 without BOM to avoid parsing errors in Kimi.
- Keep server-side JSON-RPC responses strictly compliant with the client schema (no `null` ids, avoid extraneous stdout noise).
- For any new tools, return structured `content` blocks instead of ad-hoc `output` strings to stay MCP-compliant.

## Tooling Gotchas (2026-01-09)

- SovereignMCP MCP tools can intermittently time out with `deadline has elapsed` (~60s); when diagnosing, run tools in small batches and keep a PowerShell fallback path for basic filesystem/process inspection.
- Some MCP tool calls can return `aborted by user` if the harness cancels a long-running call; treat as infra noise and retry the tool individually when needed.

## Async Tool Invocation Lessons (2026-02-09)

- The MCP server must support mixed callable styles because this codebase currently contains both:
  - legacy tools registered with `parameters` and functions expecting kwargs (`fn(path=...)`)
  - newer tools registered with `inputSchema` and functions expecting a single dict argument (`fn({"command": ...})`).
- A single hard-coded invocation style (`tool_function(arguments)` or `tool_function(**arguments)`) breaks one half of the tool ecosystem. Invocation must attempt both styles in a controlled fallback sequence.
- Async handling must detect both:
  - coroutine functions
  - sync functions that return awaitables/coroutines.
- Safe sync-bridge rule:
  - use `asyncio.run()` when no loop is running
  - if an event loop is already running, execute coroutine in a dedicated thread+loop to avoid `RuntimeError: asyncio.run() cannot be called from a running event loop`.
- `aiohttp` timeout usage is strict: pass `aiohttp.ClientTimeout(total=...)` rather than raw integers when building request timeouts in refactored async call paths.
- `WebTool` session lifecycle rule:
  - create `ClientSession` lazily (`_get_session`) to avoid loop ownership problems during startup/import.
  - provide `close()` and call it during server shutdown to prevent unclosed-session warnings.
- Shutdown architecture rule:
  - `MCPServer.shutdown()` should iterate `tool_modules`, call `close()` if available, and await it when it returns an awaitable.
- Test harness rule:
  - `tests/comprehensive_tool_validation.py` cannot call tools synchronously without awaitable detection.
  - `run_tool()` should execute awaitables and optionally resolve missing `bb7_` prefix for backward compatibility in older test names.

## Event Loop Stability Lessons (2026-02-09)

- Using `asyncio.run()` per tool invocation is unsafe for long-lived async resources (like `aiohttp.ClientSession`) because each call creates/closes a distinct event loop.
- A cached async resource is loop-affine; reusing it across closed/replaced event loops can trigger `Event loop is closed`.

### Neural-Symbolic Orchestration (`Muad'Dib` + `Lisan al-Gaib`)

The `Muad'Dib` neural substrate is surgically integrated into the `Lisan al-Gaib` routing and planning systems.

- **Graceful Fallback:** Neural logic *must* degrade transparently. Every injection point (`spectral_similarity`, MCTS value function, etc.) defaults back to pure statistical logic if `torch` is unavailable or if tensor operations fail. This ensures server boot stability.
- **Blending Weight:** The neural priors are blended at ~20-30% weight initially (e.g., $w=0.30$ for neural cosine similarity, $\alpha_{shift} = \text{Q\_bonus} \times 2.0$ for bandits). This prevents the un-trained substrate from immediately overwhelming empirical statistics.
- **Persistent Observation:** The neural tokenizer observes the full tool payload during MCTS `search` via the value function. MCTS rollout telemetry (`record_mcts_signal`) forces backpropagation into the cognitive journal to align both discrete search and neural embedding updates.
- **Telemetry Loop:** The perpetual `_autonomous_exo_cycle_loop` manages neural telemetry every 4 cycles and `bb7_dt_save` every 16 cycles, removing the need for user-triggered state flushes.

### Persistence & Reload Boundaries

- Prefer a single shared background async loop for sync->async bridging inside the server runtime.
- `asyncio.run_coroutine_threadsafe()` on that shared loop provides deterministic coroutine execution from sync code without loop churn.
- Server shutdown order matters:
  - close async tool resources first (using the shared loop),
  - then stop/cleanup the shared loop.
- Web session rule for defensive tooling:
  - if cached session loop differs from the currently running loop, discard/recreate the session instead of attempting reuse.
- Regression reproduction sequence that must remain green:
  - `check_url_status`
  - `fetch_url`
  - `search_web`
  - `download_file`
  - `check_url_status`

## MCP Integration Gotcha (2026-02-09)

- Some SovereignMCP wrapper calls (`bb7_memory_store`, `bb7_capture_insight`) can still fail with positional-argument errors (`missing required positional argument`) depending on which MCP server process/version is active.
- When this happens, persist state in project memory files (`MEMORY.md`, `CONTEXT.md`, `.claude/memory/*`) and treat wrapper-tool memory calls as best-effort until server instance alignment is verified.

## Quick Retry Observation (2026-02-09, Codex MCP Wrapper)

- `ping_server` is healthy (`status=alive`) and reports `tool_count=71`, but the web tool path remains unstable in this active server instance.
- Reproduction in `C:/Users/treyr/mcp`:
  - `bb7_check_url_status("https://example.com")` -> `Event loop is closed`
  - `bb7_fetch_url("https://example.com")` -> `Event loop is closed`
  - `bb7_search_web("OpenAI")` -> `Event loop is closed`
  - `bb7_extract_links("https://example.com")` -> `No links found in https://example.com`
- Native PowerShell baseline still succeeds:
  - `Invoke-WebRequest https://example.com` -> `200`
- Additional bug surfaced:
  - `extract_links` only treats upstream fetch failure as fatal when the response starts with `Error:` or `HTTP Error`.
  - `fetch_url` currently returns failures as `Error fetching ...`, so `extract_links` can incorrectly return `No links found...` and hide the real transport/runtime error.
- Practical interpretation:
  - The currently active MCP server process for this client is still in a bad async loop/session state (or not running the intended fixed process), even though the process responds to health checks.

## Tool Availability Diagnostics (2026-02-09)

- Manifest exposure is not equivalent to runtime usability:
  - `tool_manifest.json` can list full capability, while live MCP transport may still execute with stale dispatcher semantics.
- Signature symptom of stale transport dispatcher:
  - tools that expect kwargs/no-args fail with positional-dict errors (`takes 0 positional arguments but 1 was given`, `missing required positional argument`, `unhashable type: 'dict'`).
  - tools that accept one dict argument often still work, creating a false sense of partial health.
- Multiple concurrent `mcp_server.py` processes increase risk of clients binding to old behavior.
- Killing stale server processes can fix process drift but will drop existing MCP transports; clients must restart/reconnect.
- To maximize actual tool usage by the assistant:
  - ensure transport health first (single fresh server process, correct file path, restarted clients),
  - then enforce preflight tool checks (`ping_server`, memory read/write, one terminal tool, one web tool) before complex tasks.

## Tool Manifest Synchronization Pattern (2026-02-10)

- Symptom observed:
  - Runtime server reported `TOTAL TOOLS REGISTERED: 75`, while `tool_manifest.json` declared only 70 tool entries.
  - This creates hard-to-debug behavior where tool discovery, routing, and confidence differ between runtime and manifest-driven clients.
- Root cause:
  - Newly added router/control tools from `tools/auto_tool_module.py` and built-in `ping_server` were registered in `MCPServer` but not copied into `tool_manifest.json`.
- Canonical reconciliation workflow:
  1. Instantiate `MCPServer()` from workspace code.
  2. Build `server_tool_names = set(server.tools.keys())`.
  3. Load `tool_manifest.json` and build `manifest_tool_names = set(entry["name"] for entry in tools)`.
  4. Compute:
     - `missing_in_manifest = server_tool_names - manifest_tool_names`
     - `extra_in_manifest = manifest_tool_names - server_tool_names`
  5. Add missing entries with `name`, `description`, and `input_schema`.
  6. Re-run comparison until both diffs are empty.
- Missing tools that were added in this sync:
  - `bb7_auto_session_resume`
  - `bb7_intelligent_tool_guide`
  - `bb7_show_available_capabilities`
  - `bb7_workspace_context_loader`
  - `ping_server`
- Post-fix validation snapshot:
  - `manifest_count = 75`
  - `server_count = 75`
  - `missing_in_manifest = []`
  - `extra_in_manifest = []`
- Operational rule to keep:
  - Any change to `get_tools()` output (or built-in tool registration like `ping_server`) must include same-turn updates to `tool_manifest.json`.
  - Treat "manifest parity check" as required before declaring tool registration complete.

## Exoskeleton V1 Control-Plane Pattern (2026-02-10)

- Objective completed:
  - Build an interface layer that makes tool capability space explorable and composable per turn without requiring full-manifest prompt injection.
- Architecture implemented:
  - New module: `tools/exoskeleton_tool.py`
  - Persistent state path: `data/exoskeleton/`
    - `exoskeleton_state.json` for priors, mappings, recovery strategies, macro discoveries
    - `execution_history.jsonl` for append-only reflection telemetry
- Retrieval strategy used in V1:
  - Lightweight lexical semantic scoring (token overlap weighted by local IDF from `tool_manifest.json`)
  - Intent-conditioned category weighting using keyword maps
  - Category-graph expansion with bounded neighbor distance
  - Composite ranking signal:
    - semantic score
    - intent/category match
    - composability score from graph neighborhood overlap
    - reliability prior from beta-style alpha/beta counters
    - latency penalty by category
- Planning strategy used in V1:
  - Generate multiple candidate chains (`balanced`, `reliability-first`, `analysis-deep`) with beam cap
  - For each plan, emit:
    - confidence
    - token estimate
    - estimated latency
    - failure points (low reliability + required params)
    - fallback chain
    - contract validity flag
- Reflection loop implemented:
  - `bb7_exo_reflect` updates tool and chain priors with decay + reinforcement
  - records error-linked recovery strategy hints
  - reinforces intent-to-tool mapping frequencies
  - mines repeated successful sequences into discovered macro candidates
- Registration/integration details:
  - `mcp_server.py` loads `ExoskeletonTool` via module list
  - server capabilities include `"exoskeleton"`
  - `tool_manifest.json` contains all `bb7_exo_*` schemas
  - `README.md` documents exoskeleton tools and persisted state files
- Validation workflow (non-pytest) added:
  - `tests/validate_exoskeleton_v1.py`
  - Executes full exoskeleton lifecycle and MCP registration/parity checks
  - Emits markdown + JSON artifacts in `logs/`
  - 2026-02-10 run passed:
    - `logs/exoskeleton_v1_validation_20260210_050020.md`
    - `logs/exoskeleton_v1_validation_20260210_050020.json`
- Critical operational rule:
  - After adding or removing tools, always run server-vs-manifest parity check before claiming capability availability.
  - Current verified parity snapshot after Exoskeleton V1: `82 == 82`.
- Quality fix:
  - Updated validator time calls from `datetime.utcnow()` to timezone-aware `datetime.now(timezone.utc)` to avoid deprecation warnings.

## Visual Tool Failure Pattern + Fix (2026-02-10)

- Symptom:
  - Visual tool category looked unstable despite registration success.
  - `bb7_window_info` returned runtime error on Windows in active environment.
- Reproduced concrete failure:
  - `module 'win32gui' has no attribute 'IsZoomed'` from `tools/visual_tool.py` Windows window-state branch.
- Root cause:
  - `pywin32` surface can vary by environment/version; `IsZoomed` is not universally exposed on `win32gui`.
- Fix pattern:
  - Prefer robust layered state detection:
    1. `win32gui.IsIconic(hwnd)` for minimized
    2. `win32gui.IsZoomed(hwnd)` only if `hasattr(win32gui, "IsZoomed")`
    3. fallback to `win32gui.GetWindowPlacement(hwnd)` with `win32con.SW_MAXIMIZE` / `SW_SHOWMAXIMIZED`
    4. safe default `Normal` on inspection exceptions
- Additional reliability fix:
  - Standalone visual tool runner used async/await against sync methods in `__main__`.
  - Updated to direct sync calls and safe console output handling for cp1252 unicode/emoji terminals.
- Test alignment lesson:
  - Several validation scripts were still targeting deprecated visual endpoints (`bb7_screen_capture`, `bb7_visual_diff`, `bb7_window_manager`, `bb7_active_window`, `bb7_keyboard_input`, `bb7_mouse_control`, `bb7_clipboard_manage`).
  - Updated visual validation surfaces to current registered tools:
    - `bb7_take_screenshot`
    - `bb7_window_info`
    - `bb7_find_on_screen`
    - `bb7_click_element`
    - `bb7_screen_monitor`
- Safety/testing pattern for visual actions:
  - Use low-risk args for click validation (`element="-1,-1"`) and treat deterministic bounds error as valid execution signal.
  - This validates control path without causing unwanted UI interactions.
- Validation evidence captured:
  - Terminal run: `tests/visual_tools_test.py` passed `5/5`.
  - Direct server probes via `handle_call_tool` confirmed window-info crash resolved.
  - Saved reports:
    - `logs/visual_tool_fix_validation_20260210_095220.md`
    - `logs/visual_tool_fix_validation_20260210_095220.json`

## Full Tool Reliability Lessons (2026-02-10)

- Exoskeleton method contract migration gotcha:
  - `tools/exoskeleton_tool.py` now returns Python dicts from public methods.
  - Existing validators (`tests/validate_exoskeleton_v1.py`) were still assuming JSON-string payloads and calling `json.loads(...)` directly.
  - Durable compatibility pattern:
    - treat dict as canonical,
    - parse only when payload is a string,
    - fail fast for all other payload types.

- Async web search resilience pattern:
  - DuckDuckGo instant-answer endpoint can return empty/non-JSON payloads even with `format=json`.
  - If code assumes `json.loads(raw_text)` always succeeds, the tool degrades into opaque runtime errors.
  - Fix pattern implemented in `tools/web_tool.py`:
    - validate query upfront,
    - clamp `num_results`,
    - enforce HTTP status check before parsing,
    - on JSON decode failure, return structured fallback with response preview instead of exception text.
  - Result: no coroutine/runtime failures, deterministic tool output even when upstream response quality is poor.

- Web tool error propagation pattern:
  - `extract_links` originally only treated `Error:` and `HTTP Error` prefixes as fatal.
  - Upstream `fetch_url` can emit variants such as `Error fetching ...` and `URL Error: ...`.
  - Fix implemented:
    - centralized `_looks_like_error_payload(...)` helper with normalized error marker detection,
    - use helper in `extract_links` before HTML parsing.
  - Side benefit:
    - avoids false success responses like `No links found ...` when fetch actually failed.

- Relative URL normalization lesson:
  - Manual string concatenation for relative link reconstruction is brittle.
  - Replaced manual assembly with `urllib.parse.urljoin(...)` in `extract_links`.
  - This handles root-relative, directory-relative, and absolute links correctly.

- Visual analysis key-guard lesson:
  - Screenshot analysis output may omit expected keys on degraded paths (`{'error': ...}` payload).
  - Direct indexing (e.g., `analysis['colors']`) can cause tool-level exceptions after successful capture.
  - Hardening pattern applied in `tools/visual_tool.py`:
    - use `.get(...)` with defaults for all analysis keys,
    - include optional analysis-note line if analysis engine reports an error,
    - never throw on analysis formatting path.

- Terminal PATH hygiene on Windows:
  - PATH can include entries that are files (not directories), quoted entries, or malformed values.
  - Scanning logic that assumes every PATH entry is a directory can raise `NotADirectoryError` and destabilize discovery tools.
  - Fixes in `tools/vscode_terminal_tool.py`:
    - `_iter_valid_path_directories()` added to sanitize, dequote, dedupe, and filter to existing directories only.
    - `_find_similar_commands()` now uses sanitized PATH entries and catches filesystem exceptions.
    - `_analyze_path_environment()` distinguishes:
      - invalid path entry,
      - existing-but-not-directory entry.
    - `_find_command_alternatives()` now:
      - includes valid PATH dirs + platform-specific defaults,
      - handles Windows `PATHEXT`,
      - dedupes by normalized real paths.

- Terminal navigation bug pattern:
  - In `bb7_terminal_cd`, `project_info` was assigned only inside `if analyze_context:` but later referenced unconditionally.
  - This produced runtime error when `analyze_context=False`:
    - `cannot access local variable 'project_info' where it is not associated with a value`.
  - Fix:
    - initialize `project_info = {}` before conditional branch.

- Standalone runner contract:
  - Several tool modules had `__main__` blocks incorrectly using async/await against sync methods.
  - Even when MCP runtime is correct, standalone smoke runs can create false-negative debugging noise.
  - Updated `tools/vscode_terminal_tool.py` standalone block to direct sync calls.

- Full-surface validation pattern (new canonical smoke gate):
  - Added `tests/validate_all_tools_exo_sweep.py` as non-pytest end-to-end sweep.
  - Properties:
    - executes via `MCPServer.handle_call_tool(...)` (actual MCP call path),
    - runs Exoskeleton preflight (`bootstrap`/`route`/`plan`),
    - runs all registered tools with safe, schema-aware sample args,
    - retries once for missing-required-arg errors,
    - writes markdown + JSON artifacts in `logs/`.
  - Observed outcomes:
    - first pass: `81/82` due true `bb7_terminal_cd` local-variable bug + strict failure classifier.
    - post-fix pass: `82/82` (`100%`).
  - Artifact (latest green run):
    - `logs/all_tools_exo_sweep_20260210_100816.md`
    - `logs/all_tools_exo_sweep_20260210_100816.json`

- Manifest parity remains critical after every tool change:
  - Post-fix parity check confirms:
    - `server_count = 82`
    - `manifest_count = 82`
    - `missing_in_manifest = []`
    - `extra_in_manifest = []`
  - Keep this parity check as a mandatory post-change gate.

## Advanced Shell Standalone Direct Tool Bridge (2026-02-10)

- Objective:
  - Make `advanced_ai_shell.py` capable of direct native tool execution from `mcp/tools` without MCP server transport dependency.
  - Ensure shell module can be copied to other codebases and still use BB7 tools by path, not by live MCP connection.

- Architectural decisions:
  - Added `NativeToolBridge` inside `advanced_ai_shell.py` as the interface layer.
  - Bridge resolves tools directory in this priority:
    1. explicit `AIShellSettings.native_tools_dir`
    2. env `AI_SHELL_NATIVE_TOOLS_DIR`
    3. `<advanced_ai_shell.py dir>/tools`
    4. `<cwd>/tools`
  - Bridge indexing supports both MCP tool map formats encountered in this repo:
    - `{"tool_name": callable}`
    - `{"tool_name": {"function": callable, ...metadata...}}`
  - Invocation policy supports heterogeneous tool signatures:
    - kwargs style (`fn(**arguments)`)
    - dict style (`fn(arguments)`)
    - no-arg style (`fn()`)
  - Async handling:
    - coroutine functions awaited directly
    - sync functions run in thread
    - awaitable return values awaited
  - Duplicate tool names:
    - first registration wins
    - duplicate warning logged
    - avoids runtime crash from collision.

- Command-plane integration decisions:
  - Native command parsing added directly to `AdvancedAIShell.execute_command()` before VM/container routing.
  - Supported commands:
    - `tool list [prefix]`
    - `tool call <tool_name> [json_args]`
    - direct `bb7_*` tool invocation with optional JSON args
  - Native command path allowed even when shell has not completed full VM initialization.
    - This is required for standalone/local direct tool usage.

- Standalone safety hardening:
  - External imports (`core.*`, `projects.*`) are now default-safe fallbacks.
  - External integration loading is opt-in only via env:
    - `AI_SHELL_LOAD_EXTERNAL_INTEGRATIONS=1`
  - Fallback classes keep module importable in isolated/agnostic environments.
  - This prevents silent failures where unrelated external project modules break direct tool usage.

- Validation implementation:
  - Added non-pytest validator:
    - `tests/validate_advanced_shell_native_tools.py`
  - Validation outputs:
    - terminal step trace
    - markdown report
    - json manifest
  - Passing artifact set:
    - `logs/advanced_shell_native_tools_validation_20260210_110707.md`
    - `logs/advanced_shell_native_tools_validation_20260210_110707.json`

- Key gotcha discovered and fixed:
  - Initial bridge indexed `0` tools despite successful module imports.
  - Root cause:
    - loader assumed `get_tools()` values were direct callables
    - `auto_tool_module` and others return metadata dict entries containing `"function"`.
  - Fix:
    - normalize tool entry extraction to accept both callable and dict-with-function formats.

## Skill Authoring Pattern (2026-02-10): War Room Architect Skill

- Created a new custom skill in workspace:
  - `skills/custom/war-room-architect/`
- Generation flow used:
  1. Ran `init_skill.py` with deterministic interface metadata to generate folder + base files.
  2. Replaced template `SKILL.md` with production planning persona contract.
  3. Ran `quick_validate.py` and resolved encoding issue.
- Important gotcha:
  - `quick_validate.py` reads files with default Windows cp1252 behavior when no encoding is provided.
  - Non-ASCII glyphs (curly quotes, emoji/check-mark symbols) can fail validation even when markdown renders correctly.
  - Resolution: keep `SKILL.md` ASCII-safe when targeting this validator flow.
- Skill semantics implemented:
  - mandatory output structure
  - upgrades matrix schema with implementation snippets
  - explicit ROI/complexity/priority scoring
  - phase roadmap + closing ritual
- Validation result:
  - `Skill is valid!`

## Advanced Shell Spec Synchronization Pattern (2026-02-10)

- Goal:
  - Align `ADVANCED_AI_SHELL_SPEC.md` with the current behavior of `advanced_ai_shell.py` after native direct-tool bridge additions.
  - Produce a portable spec suitable for moving `advanced_ai_shell.py` + spec into other codebases.

- What changed in spec:
  - Full rewrite of `ADVANCED_AI_SHELL_SPEC.md` as version `1.1`.
  - Updated metadata:
    - file size reference now `~2548 lines` (from older `~2170`)
    - last-updated date now `2026-02-10`.
  - Added explicit "operation modes":
    - standalone default mode with fallback integrations
    - opt-in external integrations via `AI_SHELL_LOAD_EXTERNAL_INTEGRATIONS`.
  - Added complete `NativeToolBridge` contract:
    - load/index flow, locks, close lifecycle
    - tools-dir resolution order
    - supported tool export shapes from `get_tools()`
    - module-level prefix scanning
    - invocation fallback order and error semantics.
  - Added execute-command native routing behavior:
    - `tool list`, `tool call`, direct `bb7_*`
    - native command execution allowed before full shell init.
  - Added native settings/env vars to configuration section:
    - `enable_native_tools`
    - `native_tools_dir`
    - `native_tool_prefix`
    - `AI_SHELL_ENABLE_NATIVE_TOOLS`
    - `AI_SHELL_NATIVE_TOOLS_DIR`
    - `AI_SHELL_NATIVE_TOOL_PREFIX`.
  - Added native usage examples for both command and direct API paths.

- Important alignment lesson:
  - For this shell, spec drift risk is highest in "integration assumptions":
    - old docs implied external integrations are always present,
    - current code is intentionally standalone-first with optional integration load.
  - Any future update touching startup/import logic must update docs in lockstep for:
    - `AI_SHELL_LOAD_EXTERNAL_INTEGRATIONS`
    - fallback class behavior
    - portability guarantees.

- Durable documentation checklist for `advanced_ai_shell.py`:
  1. confirm file length/version markers are refreshed.
  2. document any new `AIShellSettings` fields and their `AI_SHELL_` env names.
  3. document any new `execute_command` interception path before context routing.
  4. document native bridge call shape contracts when invocation behavior changes.
  5. keep quick-start examples covering both normal VM execution and direct native tool calls.

## Live MCP Wrapper Verification Pattern (2026-02-10)

- Trigger:
  - User reported concern that MCP usage was not actually working and requested MCP-first behavior.

- Validation approach that worked in-session:
  1. Read project continuity files via MCP (`bb7_read_file` on `CONTEXT.md` and `MEMORY.md`).
  2. Confirm transport (`ping_server`) and baseline capability surface.
  3. Probe exoskeleton layer:
     - `bb7_exo_bootstrap`
     - `bb7_exo_list_tool_categories`
     - `bb7_exo_state`
     - `bb7_exo_route`
     - `bb7_exo_plan`
     - `bb7_exo_reflect`
  4. Probe core operational tools:
     - memory read/write
     - terminal status
     - system info
     - visual window info
  5. Run sequential web regression sequence:
     - `check_url_status -> fetch_url -> search_web -> extract_links -> check_url_status`
     - specifically to detect previous `Event loop is closed` regression.

- Observed results (current active Codex session):
  - Transport healthy: `status=alive`, `tool_count=82`.
  - Exoskeleton tools operational and returning structured payloads.
  - Memory store/retrieve operational from wrapper (no positional-arg failure).
  - Web sequence operational with no event-loop crash.
  - `bb7_search_web` returned graceful non-JSON fallback instead of throwing.
  - Visual probe (`bb7_window_info`) returned valid active-window data.

- Practical takeaway:
  - In this session, MCP is functioning and directly usable.
  - Historical instability remains process/transport-instance sensitive; when symptoms return, run the same quick health matrix first before deeper code edits.

- Reusable quick health matrix (minimum):
  - `ping_server`
  - `bb7_exo_bootstrap`
  - `bb7_memory_store` + `bb7_memory_retrieve`
  - `bb7_terminal_status`
  - `bb7_check_url_status` + `bb7_fetch_url`

- Session memory keys recorded during verification:
  - `mcp_probe_2026_02_10_live`
  - `mcp_health_probe_2026_02_10_codex_session`

## RestrictedPython Print Collector Fix Pattern (2026-02-10)

- Symptom in full tool sweep:
  - `bb7_python_execute_secure` failed with:
    - `NameError: name '_print_' is not defined`
  - first observed in:
    - `logs/all_tools_exo_sweep_20260210_140145.md`
    - `logs/all_tools_exo_sweep_20260210_140145.json`
- Root cause:
  - `compile_restricted(...)` rewrites `print(...)` and expects `_print_` to be present in execution globals.
  - `SecurePythonInterpreter._setup_restricted_environment()` did not provide `_print_`.
- Code fix in `tools/enhanced_code_analysis_tool.py`:
  1. import `PrintCollector` from `RestrictedPython.PrintCollector` when available.
  2. define `_FallbackPrintCollector` for non-RestrictedPython/fallback paths.
  3. set `self.restricted_globals['_print_']` to active collector implementation.
  4. after `exec(...)`, read `execution_globals.get('printed')` and append to stdout buffer for consistent output rendering.
- Validation:
  - syntax check passed (`py_compile`).
  - full sweep re-run passed:
    - `85/85`, `0` failures, `0` warnings
    - `logs/all_tools_exo_sweep_20260210_140431.md`
    - `logs/all_tools_exo_sweep_20260210_140431.json`

## Wrapper Process Drift Gotcha (Reconfirmed 2026-02-10)

- Important observed behavior:
  - Active MCP wrapper process can continue serving old module state after code edits.
  - Example:
    - direct wrapper call to `bb7_python_execute_secure` still returned `_print_` failure,
    - while a fresh `MCPServer()` instance in sweep process passed with patched code.
- Practical rule:
  - When behavior differs between wrapper tool calls and local test harness:
    1. trust fresh-process sweep artifacts for code-truth validation,
    2. then refresh/restart wrapper transport to pick up patched module state.

## Codex Runtime Surface Mapping Lessons (2026-02-10)

- Effective local bootstrap chain on Windows:
  - `codex.ps1` is only a thin launcher.
  - `bin/codex.js` selects architecture target, prepends bundled path tools, sets managed-by env flag, then spawns native `codex.exe`.
  - Most behavior beyond startup is in `codex.exe`, not in editable JS.
- Highest leverage local override points are all in `~/.codex`:
  - `config.toml` for defaults and feature flags.
  - `AGENTS.md` / `AGENTS.override.md` for instruction-layer shaping.
  - `skills/` for trigger-based procedural overlays.
  - `rules/*.rules` + `policy/*.codexpolicy` for command approval/policy control.
- `-c key=value`, `--enable`, and `--disable` are hard CLI-level override hooks that can supersede persisted config per run.
- MCP is an explicit extension plane, not implicit discovery:
  - server registration lives in `config.toml` (`[mcp_servers.*]`), validated with `codex mcp list`.
  - in this environment, `SovereignMCP` is wired to `pwsh` + local `mcp_server.py`.
- Prompt-construction observability is available through session logs:
  - `session_meta` captures base/developer instruction payloads.
  - `turn_context` captures runtime policy and user-instruction overlays.
  - This gives an auditable decomposition of instruction layers even when binary internals are opaque.
- Remote-vs-local authority rule of thumb:
  - local controls shape context, tools, and guardrails;
  - remote model/service controls core generation behavior and any non-local policy enforcement.

## Session Tool Linking + Capability Exploration Lessons (2026-02-10)

- User concern validated:
  - tool usage tends to collapse into a small stable subset unless session/memory + exo reflection loops are intentionally executed.
- Practical recovery pattern:
  1. run `bb7_exo_bootstrap`
  2. run `bb7_exo_list_tool_categories`
  3. run `bb7_exo_category_specific_tools` across all categories
  4. run `bb7_exo_route` for target intents
  5. create/activate session (`bb7_start_session`)
  6. log and link findings (`bb7_memory_store`, `bb7_link_memory_to_session`, `bb7_capture_insight`, `bb7_record_workflow`)
  7. close with `bb7_exo_reflect`
- This pass executed full validation sweep and confirmed runtime surface:
  - `tests/validate_all_tools_exo_sweep.py` -> `85/85 passed`
  - artifacts:
    - `logs/all_tools_exo_sweep_20260210_213933.md`
    - `logs/all_tools_exo_sweep_20260210_213933.json`
- Critical mismatch discovered:
  - Exoskeleton currently indexes `82` tools while runtime sweep executes `85`.
  - Missing in exo index include `bb7_exo_briefing`, `bb7_exo_preemptive_recovery`, `bb7_exo_route_focused`.
  - Root lesson:
    - planner catalogs must sync from live runtime registry (or be refreshed at bootstrap), not rely on stale snapshots.
- Session-linking evidence from this run:
  - active session created: `3be3797a-6fba-464d-a366-4b99cadf39d6`
  - linked memory keys:
    - `tool_capability_map_2026_02_10_full_inventory`
    - `tool_surface_mismatch_2026_02_10_exo82_vs_sweep85`
  - workflow recorded:
    - `exo_full_capability_refresh_loop`

## Exoskeleton Full-Capability Patch Lessons (2026-02-11)

- Root architecture lesson:
  - Exoskeleton should not depend solely on static manifest snapshots for routing catalog truth.
  - Catalog must continuously reconcile with live runtime registry to avoid capability drift.
- Implemented reliability pattern:
  1. attach live registry provider from server to exoskeleton (`attach_live_tools_provider`),
  2. run guarded periodic sync in each public exo endpoint (`_maybe_sync_live_tools`),
  3. support both add + update behavior in `sync_from_live_tools`.
- Important bug fixes that impacted real capability quality:
  - `bb7_exo_briefing` was reading wrong keys (`plans`/`tools`) instead of runtime payload keys (`candidate_plans`/`top_tools`).
  - `bb7_exo_preemptive_recovery` was reading `plans` instead of `candidate_plans`.
  - `bb7_exo_route_focused` was reading `tools` instead of `top_tools`.
  - `_find_alternative_tool` returned `str` while caller required structured dict fields; fixed return contract.
- Server integration lesson:
  - Sync once at registration is not enough for long-lived, evolving tool registries.
  - Added sync hook in both `tools/list` and exo-tool execution path for best-effort freshness.
- Validation proof:
  - `tests/validate_exoskeleton_v1.py` expanded to cover all 10 exo tools and catalog parity checks.
  - `tests/validate_all_tools_exo_sweep.py` confirms full runtime surface remains green (`85/85`).
- Operational gotcha remains critical:
  - A live wrapper session can remain stale even when repository code is patched and fresh-process tests pass.
  - If wrapper still reports old tool counts (e.g., exo `82`), restart/rebind transport before concluding patch failure.
- 2026-02-11 canonical persistence decision: Use `SOVEREIGN_DATA_DIR` as authoritative runtime root for all BB7 persistence; default fallback is `C:/Users/treyr/mcp/data`.
- 2026-02-11 boot-sequence gotcha fixed: `mcp_server.py` previously called `setup_logging()` before setting `self.data_dir`, which allowed early log fallback to relative `data/mcp_server.log`; now data dir resolves first, then logging is initialized.
- 2026-02-11 tool-constructor propagation: server now inspects constructor signatures and injects `data_dir` and `storage_file` when accepted, avoiding per-module divergence.
- 2026-02-11 module-level gotcha fixed: several active tools had relative persistence defaults (`Path("data")`/`data/...`), including exoskeleton/session/optimization/web/visual; these now resolve via env-backed canonical paths.
- 2026-02-11 exoskeleton stability decision: resolve `tool_manifest.json` and `golden_paths.json` from repository root (`Path(__file__).resolve().parent.parent`) to prevent working-directory-dependent behavior.
- 2026-02-11 validation pattern: use a non-pytest integration script that emits terminal output plus markdown report and json manifest under `C:/Users/treyr/mcp/data/validation` to verify path invariants.

## Exoskeleton Bootstrap Diagnostics + Independence Lessons (2026-02-11)

- `bb7_exo_bootstrap` should return machine-checkable runtime diagnostics, not just category summaries.
  - Added fields:
    - `catalog_sync` (live add/update counts)
    - `live_provider_attached`
    - `exo_tools_registered`
    - `manifest_path`, `manifest_present`, `manifest_mtime`
  - This makes stale-runtime detection immediate instead of ambiguous.
- Manual bootstrap should not be a functional prerequisite for exo route/plan/state.
  - New validator (`tests/validate_exo_bootstrap_independence.py`) proves:
    - `bb7_exo_state` works before bootstrap.
    - `bb7_exo_route` works before bootstrap.
    - `bb7_exo_plan` works before bootstrap.
    - exo indexed count stays aligned with `len(MCPServer().tools)` both before and after bootstrap.
- Critical drift pattern re-confirmed:
  - Fresh local validations pass at `85` tools while live wrapper can still report `82`.
  - If wrapper returns `82` and `bb7_exo_bootstrap` payload does not include new diagnostics fields, the wrapper is attached to an old process/version.
  - In that state, code changes in workspace are correct but not yet reflected in active transport.
- Durable triage sequence for future sessions:
  1. Run `python tests/validate_exo_bootstrap_independence.py`.
  2. Run `python tests/validate_exoskeleton_v1.py`.
  3. Run `python tests/validate_all_tools_exo_sweep.py`.
  4. Compare with live wrapper:
     - `ping_server.tool_count`
     - `bb7_exo_bootstrap.indexed_tools`
     - exoskeleton category tool count.
  5. If mismatch persists, restart/rebind MCP clients to refresh process state.

## Exoskeleton Concurrent Startup Race (2026-02-11)

- Critical bug identified:
  - During concurrent server startups, `ExoskeletonTool` sometimes failed to load with:
    - `[WinError 32] ... exoskeleton_state.json.tmp -> exoskeleton_state.json`
  - Impact:
    - exoskeleton module not registered,
    - server surface drops (e.g., `75` tools instead of `85`),
    - downstream failures like `Tool not found: bb7_exo_state`.
- Root cause:
  - `_write_json` used a single fixed temp path (`<target>.tmp`), unsafe across processes.
- Fix pattern implemented:
  - Use unique temp file names per write (`pid + thread id + uuid`) in `_write_json`.
  - Retry with backoff on transient Windows file lock errors (`PermissionError`, `winerror` 5/32).
  - Apply similar retry handling to `_append_jsonl`.
  - Make `_save_state` non-fatal (warn instead of raising) so persistence contention cannot block exoskeleton registration.
- New reliability gate added:
  - `tests/validate_exoskeleton_concurrent_init.py`
  - Runs multi-round parallel child initializations and fails if any child misses exoskeleton tools.
  - Output artifacts in `logs/`:
    - `exoskeleton_concurrent_init_validation_<timestamp>.md`
    - `exoskeleton_concurrent_init_validation_<timestamp>.json`
- Post-fix validation status:
  - Concurrent init validation passed.
  - Exo bootstrap independence passed.
  - Exoskeleton v1 validation passed.
  - Full tool sweep passed (`85/85`).
- Operational distinction to remember:
  - Repo/fresh-process correctness can be green while live MCP wrapper still shows stale counts (`82`) if bound to older long-running process set.

## MCP/Exoskeleton Callable Alignment Lessons (2026-02-11)

- Core contract rule:
  - If MCP can surface a tool in `tools/list`, exoskeleton sync should receive an equivalent dict-backed representation for that same tool.
  - Without normalization, callable tools create a split-brain state: discoverable by MCP but invisible to exoskeleton cognition.
- Durable implementation pattern:
  1. Normalize live tool entries before exoskeleton sync in `mcp_server.py`.
  2. Keep exoskeleton sync defensive by accepting `Dict[str, Any]` and wrapping callables when seen.
  3. Preserve invocation metadata while adding compatibility mapping (`input_schema` -> `inputSchema`) for live-sync consumers.
- Required-params extraction gotcha:
  - A default `params = tool_info.get("parameters", [])` causes false short-circuit when params is an empty list.
  - Correct behavior is:
    - use legacy `parameters` only when list is non-empty,
    - otherwise fall through to schema keys (`inputSchema`, `input_schema`).
- Diagnostics pattern that helps quickly:
  - Keep warning logs for unsupported sync metadata types and callable-normalization events in exoskeleton live sync.
  - This immediately reveals why tools are skipped during catalog refresh.
- Validation strategy for this class of bug:
  - Add a non-pytest validator step that injects synthetic live tools with:
    - one bare callable
    - one dict tool with `input_schema.required`
  - Assert both catalog presence and `required_params` extraction.
- Regression evidence (green):
  - `tests/validate_exoskeleton_v1.py` now validates callable normalization + schema-required extraction and passed in run `20260211_055111`.

## Live Browser/Web Tool Verification Lesson (2026-02-11)

- A direct in-session trial confirms web tools can run successfully without restarting/resuming when the active runtime is already fresh.
- Verified successful tool behaviors:
  - `bb7_check_url_status` returns HTTP status/headers as expected.
  - `bb7_fetch_url` returns content payload with metadata.
  - `bb7_extract_links` correctly parses absolute URL from example HTML.
  - `bb7_download_file` writes and persists downloaded artifact under `C:/Users/treyr/mcp/data/validation`.
- Search-specific nuance remains important:
  - `bb7_search_web` may return graceful fallback message when DuckDuckGo response is non-JSON.
  - This is not a runtime crash and should be treated as upstream payload variability, not local tool failure.
- Practical triage pattern:
  1. Run check/fetch/extract/download against `https://example.com` for deterministic baseline.
  2. Treat `search_web` fallback-only response as degraded but functional unless exception/error strings appear.

## Exoskeleton Prior-Reset Diagnosis + Fix Pattern (2026-02-11)

- If a user reports alpha/beta priors "resetting" each restart, verify with disk + re-instantiation proof before patching:
  1. inspect `data/exoskeleton/exoskeleton_state.json` for zero counts/ranges,
  2. instantiate `ExoskeletonTool`, run one reflect, instantiate again, compare same tool prior.
- Confirmed behavior in this workspace:
  - priors persist across fresh instances,
  - `alpha_or_beta_zero_count` remains `0`,
  - observed growth in `bb7_exo_bootstrap` prior after reflect proves persistence.
- Implemented reliability upgrade:
  - Exoskeleton now explicitly checks manifest mtime on bootstrap and refreshes manifest-derived catalog when changed.
  - Exoskeleton now surfaces prior persistence diagnostics in bootstrap output, making reset suspicion immediately inspectable.
- Added key helpers in `tools/exoskeleton_tool.py`:
  - `_get_manifest_mtime`
  - `_refresh_catalog_from_manifest_if_changed`
  - `_tool_prior_diagnostics`
- Bootstrap contract now includes:
  - `manifest_refresh`
  - `prior_diagnostics` (count/ranges/zero/cold-start/state file path)
- Test hygiene lesson:
  - Synthetic test-only tools used for callable sync assertions must be cleaned from `tool_catalog` + `tool_priors` before test exit to avoid persistent pollution.
- Operational caveat remains:
  - fresh-process code truth can differ from currently attached wrapper process output until client/server transport is restarted/rebound.

## MCP Reset Verification Pattern (2026-02-11)

- A successful reset should satisfy both conditions:
  1. live payload shape reflects latest code changes,
  2. only one active `mcp_server.py` process is running for the client transport.
- In this check, condition (1) passed and condition (2) failed.
- Diagnostic outcome:
  - New bootstrap fields (`manifest_refresh`, `prior_diagnostics`) prove fresh code is active.
  - Multiple concurrent server PIDs still exist, so stale/parallel process drift remains possible.
- Operational rule:
  - Treat this state as "partially reset" and complete cleanup by terminating duplicate `mcp_server.py` instances, then reconnecting to exactly one canonical server process.

## Exoskeleton/GLOBAL Persistence Clarification (2026-02-12)

> Superseded current-runtime note: this entry is historical. Current Linux canonical data root is `/home/daeron/Somnus-MCP/data`, and current doctrine avoids mandatory per-turn bootstrap rituals.


- User confusion source was valid: exoskeleton grew significantly and introduced `golden_paths.json` + multiple `data/exoskeleton/*` artifacts, creating uncertainty about where continuity actually lives.
- Confirmed canonical runtime pathing:
  - `mcp_server.py` resolves `SOVEREIGN_DATA_DIR` with default `C:/Users/treyr/mcp/data`.
  - Server injects `data_dir` and `storage_file` into tools that support constructor args.
  - `ExoskeletonTool` defaults to same env/global root and stores under `.../data/exoskeleton`.
- Confirmed exoskeleton persistence semantics:
  - state/history are rolling but event-driven, not write-on-every-call.
  - critical writes happen during init/mutation and reflect path (`_save_state`, `_append_jsonl`).
- Golden paths design intent captured:
  - They are bootstrap priors/templates for chain intelligence,
  - not chat memory,
  - used to reduce cold-start behavior in planning/routing.
- Documented architectural warning:
  - `memory_interconnect.py` constructor default `data_dir="data"` is safe when server injects `data_dir`, but risky for standalone/module-direct instantiation where cwd-relative leakage can occur.
- Added durable documentation in `SPEC.md` including:
  - startup flowchart,
  - exoskeleton load/save flowchart,
  - persistence matrix,
  - message-level exo loop recommendation.

## Detailed Persistence Matrix Pass (2026-02-12)

> Superseded current-runtime note: this entry is historical. Current Linux canonical data root is `/home/daeron/Somnus-MCP/data`. Preserve artifact timing lessons, not stale Windows path assumptions.


- User requested highly detailed persistence documentation to reason about exoskeleton/memory/session/global state behavior.
- Added long-form `SPEC.md` extension with:
  - canonical root rule,
  - exact artifact-level mapping by module,
  - load/save timing (startup, runtime call, reflect, shutdown),
  - operation model for cross-chat continuity.
- Important distinctions captured:
  - Exoskeleton writes are event-driven (especially reflect), not every call.
  - Session and memory components are write-on-operation and load-on-operation patterns.
  - Terminal/shell tools mostly keep in-memory runtime state unless explicitly writing files.
  - `memory_interconnect.py` default `data_dir="data"` remains a standalone risk if bypassing server constructor injection.
- Documentation now includes both high-level and detailed flowcharts, enabling planning and implementation decisions without code spelunking each time.

## OpenRouter Planner Integration Pattern (2026-02-12)

> Superseded current-runtime note: this entry is historical. Planner persistence now belongs under `/home/daeron/Somnus-MCP/data/planner` in the Linux runtime doctrine.


- Added a first-pass planner module (`tools/openrouter_planner_tool.py`) designed to keep all planner state global and canonical under `C:/Users/treyr/mcp/data/planner`.
- Tool surface introduced:
  - `bb7_planner_health`: reports config presence + persistence paths + planner state counters.
  - `bb7_planner_template`: emits deterministic planning template for intent/context.
  - `bb7_planner_plan`: OpenRouter-backed plan generation with `dry_run` safety mode.
- Reliability/operational design:
  - Async HTTP via `aiohttp` with lazy `ClientSession` reuse and loop-mismatch guard.
  - Request retry strategy with bounded retry count and sleep backoff.
  - Timeout and parameter clamping for safe runtime behavior.
  - Structured fallback parser to handle non-JSON model responses.
  - Explicit run telemetry append to JSONL for post-hoc diagnostics.
- Persistence details:
  - `planner_state.json` tracks aggregate run counters (`total/success/failed`).
  - `planner_runs.jsonl` captures per-run metadata (request id, duration, token usage when provided, error string).
- Environment contract for OpenRouter:
  - `OPENROUTER_API_KEY` controls live capability.
  - Optional overrides: `OPENROUTER_BASE_URL`, `OPENROUTER_PLANNER_MODEL`, `OPENROUTER_APP_NAME`, `OPENROUTER_SITE_URL`.
- Integration steps completed:
  - Registered module in `mcp_server.py` module load list.
  - Added planner tools to `tool_manifest.json`.
  - Exoskeleton catalog now indexes planner tools (`indexed_tools` advanced to 88 in current bootstrap run).
- Validation pattern used (non-pytest as required):
  - Added `tests/validate_openrouter_planner_tool.py`.
  - Checks registration + `tools/call` execution for health/template/plan(dry_run).
  - Writes required terminal-visible output plus markdown/json artifacts under `logs/`.
- Validation result snapshot:
  - Passed on run `2026-02-12 09:55:49`.
  - Artifacts:
    - `logs/openrouter_planner_validation_20260212_095549.md`
    - `logs/openrouter_planner_validation_20260212_095549.json`
- Important follow-up lesson:
  - In this environment, using small helper patch scripts under `scripts/` is more reliable than long inline chained shell commands due run-command security heuristics.

## 2026-02-26 - Thought Journal Tool Live Smoke Test (Post-Reboot)

- Verified journal tool pipeline is operational in live MCP runtime using `tools/thought_journal_tool.py`.
- Successful end-to-end flow:
  - `bb7_journal_record_thought` -> created entry `[id: 942539b8]`
  - `bb7_journal_capture_decision` -> created entry `[id: 325ca1bd]`
  - `bb7_journal_add_outcome` -> validated decision `325ca1bd`
  - `bb7_journal_search` -> returned 4 matches including new and prior test entries
  - `bb7_journal_stats` -> BM25 indexed docs = 4, decisions=2, validated=1
- Critical implementation note: journal create APIs currently return formatted message strings, not raw IDs.
  - Callers must parse `[id: <hex>]` before calling `bb7_journal_add_outcome`.
  - Recommend future hardening: add structured return mode (`{"entry_id":..., "status":...}`) for automation-safe chaining.
- Encoding note observed in tool output: checkmark/circle glyphs can display as mojibake under cp1252 terminals.
  - Mitigation used during smoke: `PYTHONIOENCODING=utf-8`.

## Update 2026-02-27 (Memory Tool Invocation Compatibility Hardening)

- Scope: Hardened invocation compatibility in `tools/memory_tool.py` and `tools/memory_interconnect.py` to tolerate mixed caller styles.
- Problem class addressed:
  - Legacy dispatchers sometimes pass a single `arguments` dict positionally.
  - Some wrappers invoke tools with kwargs.
  - Some paths pass empty dicts to no-arg tool callables.
  - This can trigger errors like:
    - `takes 0 positional arguments but 1 was given`
    - `missing required positional argument` when args dict is not unpacked.
- Implementation details:
  - Added `Callable` typing import in both files.
  - Added `_merge_tool_arguments(args, kwargs, param_names)` in both classes.
  - Added `_normalize_tool_registry(tools)` in both classes.
    - Wraps each tool callable from `get_tools()`.
    - Supports three invocation modes per tool call:
      1) no-arg call when merged args are empty
      2) kwargs call (`tool_fn(**merged)`)
      3) dict-positional fallback (`tool_fn(args[0])`) for dict-style handlers
    - For no-parameter tools, safely ignores legacy passed argument dicts.
  - Changed `get_tools()` in both files to build `tools = {...}` and return wrapped registry via `self._normalize_tool_registry(tools)`.
- Validation executed:
  - `./mcp.venv/Scripts/python.exe -m py_compile tools/memory_tool.py tools/memory_interconnect.py` (pass)
  - Direct module/runtime probes (pass)
  - Full memory tool server probe across memory + interconnect tool set (pass, zero tool-call errors)
  - Direct dict-style invocation probes for representative tools:
    - `bb7_memory_stats({})`
    - `bb7_memory_store({"key": "k", "value": "v"})`
    - `bb7_memory_get_insights({})`
    - `bb7_memory_analyze_entry({"key": "a", "value": "alpha beta"})`
    - all passed.
- Operational outcome:
  - Memory tool registration is now resilient to mixed invocation semantics at the tool-function level, not only at server dispatcher level.
  - This reduces recurrence risk of cross-client argument-binding regressions.

## Update 2026-04-08 (Project Reorganization: Journal Removal, Spec Cleanup)

> Superseded/contradicted by current runtime: `thought_journal_tool.py` is present and loaded in current source/live snapshots, but journal-first operation remains deprecated. Treat journal endpoints as compatibility/provenance surfaces, not primary continuity.


- Deleted deprecated journal tool: `tools/thought_journal_tool.py`
- Updated `MCP_SPEC.md`:
  - Added Server Orchestration section at top (mcp_server.py)
  - Added Lisan Al-Gaib section
  - Removed duplicate Visual Tools section (maybe/visual_tool.py)
  - Removed duplicate Session Management section (maybe/session_manager_tool.py)
  - Removed duplicate Auto-Activation section
  - Removed all emojis from tool category headers
  - Cleaned corrupted Unicode characters
  - Reorganized Exoskeleton Tools as first tool category
- Updated `README.md` to note lisan_al_gaib integration
- No changes needed to data directory paths: server properly injects data_dir via constructor
- Key insight: tool classes accept data_dir parameter and mcp_server.py _build_tool_instance() injects it correctly

## Update 2026-02-27 (Schema Fix: Array `items` in tools/list)

- User-reported failure: `Invalid schema for function 'SovereignMCP_bb7_memory_store': In context=('properties', 'tags'), array schema missing items`.
- Root cause identified in `mcp_server.py::handle_list_tools` legacy-parameters conversion path:
  - when building `inputSchema.properties`, array metadata lost `items`.
  - strict schema validators reject `type: array` without `items`.
- Fix implemented:
  - Enhanced parameter->schema conversion to preserve richer metadata:
    - `type`, `description`, `enum`, `default`
    - `array`: ensure `items` is always present; fallback `{"type": "string"}` when missing
    - `object`: preserve `properties`/`required` or `additionalProperties` when provided
- Verification:
  - `py_compile mcp_server.py` passed.
  - Added non-pytest schema validation script and ran successfully.
  - Confirmed `bb7_memory_store` `tags` property now has `items`.
  - Confirmed no array schemas in `tools/list` output are missing `items`.
- Validation artifacts:
  - `logs/schema_items_validation_20260226_220835.md`
  - `logs/schema_items_validation_20260226_220835.json`

## Update 2026-02-27 (VSCode Terminal Tool Decommissioned)

- User-directed overhead reduction executed.
- Actions completed:
  - Unregistered `vscode_terminal_tool` from `mcp_server.py` module load list.
  - Moved active file from:
    - `tools/vscode_terminal_tool.py`
    - to `tools/backup_20260114_213833/vscode_terminal_tool.py`
  - Removed `bb7_terminal_*` entries from `tool_manifest.json` (6 entries).
- Runtime effect:
  - Server tool count reduced from 121 to 115 in fresh-process validation.
  - No `bb7_terminal_*` tools exposed in runtime registry.
  - `vscode_terminal_tool` no longer appears in `server.tool_modules`.
- Validation (non-pytest):
  - report: `logs/vscode_terminal_tool_drop_validation_20260226_222012.md`
  - manifest: `logs/vscode_terminal_tool_drop_validation_20260226_222012.json`
- Operational note:
  - Existing external clients may need reconnect/restart to drop cached terminal-tool schema from active transport state.

## Golden Paths and Terminal Tool Decommission Verification (2026-02-27)

- Removing `vscode_terminal_tool.py` from module registration is not sufficient by itself; stale references can persist in `golden_paths.json` and still bias exoskeleton routing toward terminal paths.
- `golden_paths.json` must be kept aligned with the active tool surface. For this decommission pass:
  - remove `terminal_automation_workflow`.
  - remove `bb7_terminal_*` calls from `system_diagnostics_workflow`.
  - update workflow descriptions/expected outputs accordingly.
- Canonical verification sequence for this class of change:
  1. `rg` scan `mcp_server.py`, `tool_manifest.json`, `golden_paths.json` for `vscode` and `bb7_terminal_`.
  2. instantiate fresh `MCPServer()` in a new process and verify:
     - tool count,
     - no `bb7_terminal_*` keys,
     - no `vscode_terminal_tool` module.
  3. interpret live wrapper mismatch (`exo_bootstrap` still showing old count) as process staleness, not necessarily code regression.
- Current verified state after cleanup:
  - no terminal/vscode references in active server registration files,
  - fresh runtime tool surface is 115 with no terminal module/tool namespace.

## Workflow Documentation Hardening Pattern (2026-03-01)

- When expanding `workflows.md`, anchor guidance to actual tool implementation files before writing recipes.
- For Exoskeleton (`tools/exoskeleton_tool.py`), critical details to preserve in docs:
  - The full operational loop should include `bb7_exo_execute_step` (not only route/plan/reflect).
  - Routing is momentum-aware, not purely semantic; session recency + learned category transitions can change ranking.
  - `bb7_exo_bootstrap` is a diagnostics call (manifest refresh check, live sync counts, prior health), not just status.
  - Long-running tasks should always use checkpoint + resume + KPI path.
  - Preemptive recovery thresholds are explicit by risk mode (0.80/0.60/0.40).
- For Thought Journal (`tools/thought_journal_tool.py`), critical details to preserve in docs:
  - Creation APIs currently return formatted strings containing IDs; automation must parse ID tokens.
  - Journal persistence is three-part: entries store, BM25 index, reverse memory-key map.
  - Journal quality loop should include retrospective + stats + outcome validation, not just raw entry creation.
  - Reverse lookup (`bb7_journal_linked_entries`) is key for tracing why memory keys exist.
- Durable documentation approach:
  - Add explicit operational sequences and persistence maps,
  - keep examples aligned with current return contracts,
  - prefer implementation-accurate caveats over idealized API assumptions.

## Broad File Search + Shared Global Data Lessons (2026-03-06)

- A `bb7_search_files` timeout from `C:/Users/treyr` is not, by itself, evidence of cache buildup.
- The dominant failure pattern is:
  - huge recursive profile scans,
  - no internal time budget/cancellation,
  - synchronous single-request server handling,
  - multiple agents multiplying the same expensive disk traversal.
- Windows profile roots contain legacy reparse-point/junction directories (`Application Data`, `My Documents`, `Cookies`, etc.); broad recursive tools should explicitly avoid descending into reparse points.
- Tool design rule for broad filesystem scans:
  - add an internal time budget,
  - return partial results when the budget is exhausted,
  - report real traversal stats,
  - prefer bounded/faster engines when available instead of raw `Path.rglob(...)`.
- Shared `C:/Users/treyr/mcp/data` can stay global, but process-local `threading.Lock()` is not enough for multi-process safety.
- For shared JSON persistence on Windows:
  - fixed `<target>.tmp` file names are unsafe under concurrent writers,
  - use unique temp files,
  - replace atomically with `os.replace(...)`,
  - retry/back off on transient lock errors (`winerror 5/32`).
- Repeated exoskeleton live-catalog sync on every turn adds avoidable overhead; debounce it when tool inventory is unchanged.

## Session Document Concurrency Lesson (2026-03-06)

> Superseded current-runtime note: Windows path examples below are historical. Current session documents live under `/home/daeron/Somnus-MCP/data/sessions`.


- Hardening shared aggregate indexes is not sufficient if per-session JSON documents are still mutated from stale in-memory copies.
- For shared session documents under `C:/Users/treyr/mcp/data/sessions`, the safe pattern is:
  - lock the specific session file,
  - reload the latest JSON from disk inside that lock,
  - apply the mutation,
  - atomically replace the file before releasing the lock.
- `self.current_session` is fine as a per-process cache, but it must not be treated as authoritative across multiple server processes.
- Validation for this class of fix should include a same-session multi-process append test, not just index-file creation/link tests.
- Current verified smoke pattern:
  - concurrent session creation preserved all session-index entries,
  - concurrent memory linking preserved all memory-index entries,
  - concurrent `bb7_log_event(\"note\", ...)` workers preserved all unique event appends on one session document.

## Durable Pattern - Workspace Resolution

- `bb7_workspace_context_loader` historically used process `cwd` only; this can drift from Codex shell cwd in multi-workspace flows.
- MCP code now supports explicit `workspace_path` in loader calls to avoid cwd ambiguity.
- If a passed `workspace_path` does not exist, loader emits a warning and falls back to process cwd.
- After code updates, restart/reload MCP server to ensure live schema/dispatch reflects new loader parameter.

## Workflow Governance Lessons (2026-04-08)

- A giant workflows catalog is less useful than an execution governor when sessions exceed ~10M tokens.
- Durable gain came from replacing breadth with a deterministic control loop and a strict tool-budget ladder.
- Explicitly writing shell-boundary truth (what the agent can/cannot access) reduces operator uncertainty and avoids implicit promises.
- For cloud-node decisions, first-party product docs (pricing, SSH setup, security model) should be captured before recommending a plan.
- New durable anchor memory: `somnus_workflows_rewrite_non_code_ops_2026_04_08`.

## Durable Workflow Doctrine Shift (2026-04-08)

- `lisan_al_gaib` is integrated into `exoskeleton_tool` and should be treated as primary orchestration intelligence, not side tooling.
- External journal-first flow is no longer required for primary operation; reasoning continuity can run through `bb7_lisan_recall` + session/memory persistence.
- For source comprehension, default to `bb7_analyze_code_complete` and context resurrection via `bb7_lisan_recall`; avoid shell text-dumping as default understanding path.
- Workflow docs should map to concrete module implementations, not generic tool catalogs.

## Durable Lessons (2026-04-08) - Lisan/Exo Docs Realignment

- Treat `mcp_server.py` as first-class control-plane component in docs and operator doctrine, not only a transport shell.
- External journal-first workflow is deprecated in this repo's current posture; reasoning continuity should be documented around lisan + memory/session persistence.
- Catalog visibility is not proof of runtime callability:
  - legacy `bb7_journal_*` entries can appear in exoskeleton/category listings,
  - runtime call can still return `Tool not found`.
- Keep README/AGENTS/workflows synchronized with live module registration to prevent routing to dead/stale tool names.
- In headless Linux sessions, `visual_tool` can fail on missing `DISPLAY`; this can change effective runtime tool count without code regressions.
- OpenRouter-dependent paths (`bb7_agent_run`) must be documented as conditional on `OPENROUTER_API_KEY`.

## Durable Lessons (2026-04-08) - Ambient Continuity Phase A

- The right insertion point for proactive continuity is `mcp_server.py` request/tool lifecycle, not forcing explicit `memory_store` calls from every agent action.
- A minimal append-only telemetry substrate (`events.jsonl`) with session/turn IDs is enough to unlock ambient continuity without changing stateless tool APIs.
- Enforcing one-process ownership of the shared data plane via lock file prevents silent split-brain memory planes across concurrent coding agents.
- Data root must be canonical and enforced; allowing arbitrary environment overrides can silently fork continuity state.
- Distill can remain retrospective while Lisan stays prospective if both read from the same event substrate.
- Emoji-heavy runtime strings degrade readability; initial scrub applied to `mcp_server.py` and `tools/shell_tool.py` as part of this hardening pass.

## Durable Lessons (2026-04-08) - Data Plane Split-Brain Fixes

- Enforcing canonical data path in `_resolve_data_dir` is not enough; process env must also be overwritten before tool imports to prevent import-time path capture.
- `openrouter_agent_tool` previously ignored injected `data_dir` and used class-level constants from import-time env; this silently reintroduced split-plane writes.
- Exoskeleton live sync must prune removed tools, not only add/update, or stale manifest entries (for example deleted journal tools) continue to leak into routing.
- `tool_manifest.json` should be generated from live `tools/list` output to prevent drift from runtime callable surface.
- A single legacy MCP process with stale `SOVEREIGN_DATA_DIR` can continue writing to old roots even after code hardening; process audit/restart is part of the fix, not optional.
- Startup-only proactive memory injection leaves continuity underutilized; per-turn ambient surfacing can run as telemetry-side context enrichment without breaking stateless tool contracts.

## Durable Lessons (2026-04-08) - Fail Loud + Ambient Codex Continuity

- If continuity is core infrastructure, failure logging cannot rely on the same path that just failed. Keep a separate internal-failure ledger (`data/internal_failures.jsonl`) outside normal telemetry semantics.
- Codex continuity should be ingested at the server/control-plane boundary, not left implicit in the GUI/runtime. Pulling `.codex/state_5.sqlite` + rollout/history deltas gives passive chat/tool continuity without changing tool APIs.
- Offset-based ingest over external logs must defend against mid-record cursors; line-boundary realignment is required for self-healing after buggy or stale cursors.
- Memory injection is stronger when it combines two substrates:
  - weighted memory-tool surfacing from the memory plane,
  - recent conversation-history retrieval from `distillation.db`.
- Production fail-loud posture means optional subsystems may still degrade, but the degradation must be explicit in logs/health/state instead of debug-only fallback.
- Missing runtime dependencies (`aiohttp` here) should be treated as first-class degraded-state signals, not quiet tool shrinkage.

## Golden Path Restoration Lessons (2026-04-12)

- `bb7_security_audit` currently calls `analyze_file(file_path, include_security=True)` without disabling default CFA/DFA/type passes; this couples security audit to heavy full-pipeline compute.
- Analyzer instability on 12-16GB machines is likely amplified by CFG frontier growth and repeated AST traversals in deep mode on large files.
- `tools/lisan_al_gaib.py` contains production-grade MCTS internals, but exoskeleton runtime planning currently still uses template `_make_plans`; MCTS wiring is a restoration priority.
- No A*planner is currently wired in lisan or exoskeleton planning path; if deterministic constrained planning is needed, add explicit A* module and policy-switch in server/exo orchestration.
- Memory should remain dynamic and adaptive: injection cadence should respond to intent entropy, novelty, and failure streaks rather than fixed deterministic patterns.
- Distillation should remain passive telemetry and quality labeling substrate, never the primary decision authority.

## Durable Lessons (2026-04-13) - OpenRouter Distillation Always-On Path

- Distillation reliability for OpenRouter surfaces improves when logging is attached at tool-plane boundaries (`openrouter_wrapper`, planner, agent) instead of only relying on global server-level opt-in gates.
- Keep distillation writer import-light:
  - if logger utilities are colocated with heavy OpenRouter imports, missing deps (e.g., `pydantic`) can cascade and disable telemetry entirely.
  - use graceful import fallback so telemetry path remains available even when model clients are degraded.
- Queue-backed append-only writes + daily shards are sufficient for sustained always-on capture while keeping hot execution paths non-blocking.
- Preserve dual-write compatibility during migration:
  - continue writing legacy `data/distillation/trajectories_*.jsonl`
  - add V2-focused `data/distillation_dataset/` artifacts (main shard + index + high-value + failures).
- Include `trajectory_id` in tool responses (`bb7_agent_run`, `bb7_planner_plan`) and run logs so downstream review/export joins are trivial.
- Planner `dry_run` is still useful distillation signal (prompt/payload lineage) and should be logged, not skipped.

## 2026-04-13: OpenRouter Env Contract

- Root `.env` is now the canonical place for OpenRouter + persistence variables.
- Linux startup script sources `.env` before `mcp_server.py` launches.
- `databus/openrouter.yaml` now points at `elephant-alpha` and does not carry a fallback chain.
- `bb7_agent_run` and `bb7_planner_plan` still hard-gate on a real `OPENROUTER_API_KEY`; use dry-run or health checks when the key is absent.

## Durable Lessons (2026-04-14) — Persistence Audit / 24-7 State

- Treat persistence in two lanes:
  1) append-only JSONL/DB for event streams and trajectories,
  2) atomic snapshot files for mutable state/indexes.
- `events.jsonl` is the universal tool-plane audit spine; every tool call is indirectly logged there even if a tool has no dedicated file writer.
- Atomic temp+`os.replace` is already widely implemented; this protects against torn writes but does not reduce rewrite cost at scale.
- Primary long-run bottleneck is full-file JSON snapshots (`memory_store.json`, `concept_index.json`, `memory_relationships.json`, `thought_journal.json`) rather than append-only logs.
- `journal_memory_index.json` can appear stale by design when `linked_memories` are omitted from journal records; stale reverse map != journal inactivity.
- Runtime env caveat: `.env` presence alone is insufficient; active process still reports `api_key_configured=false` for planner/agent when `OPENROUTER_API_KEY` is not visible at runtime.
- Known intentional overwrite surfaces:
  - `file_tool.write_file`
  - `openrouter_agent_tool` pending handoff file (`{agent}_pending.json`)
  - `shutdown_status.json` on graceful server stop

## Durable Lessons (2026-04-14) — OpenRouter Key Visibility + Elephant Model

- Root cause of health mismatch was split config sources:
  - live health used env-only fields with old hardcoded defaults,
  - sovereign client path used YAML defaults.
- To avoid false negatives and stale defaults:
  - planner/agent now default to `elephant-alpha`,
  - both resolve API keys across aliases (`OPENROUTER_API_KEY`, `OPENROUTER_KEY`, `OR_API_KEY`),
  - both hydrate from repo `.env` at config-read time.
- YAML interpolation now supports alias candidates in `${...|...}` form and preserves strict erroring when none are set.
- Live MCP process retains old module objects until restart; file edits alone do not update currently-loaded tool instances.

## Durable Lessons (2026-04-14) — Live Status After OpenRouter Fix

- OpenRouter model routing is now visibly corrected in live health (`elephant-alpha`) without fallback chain in YAML.
- Remaining blocker is credential presence, not routing code.
- Planner dry-run is a reliable non-key smoke test; agent run remains correctly key-gated.
- `scripts/start_server.sh` is the canonical restart path and already sources `.env` with `set -a` export behavior.

## Durable Lessons (2026-04-14) — Key Visibility Follow-up

- Even after user-intent confirmation, runtime truth must come from health + masked env presence checks.
- Current blocker is still credential visibility (no key detected in `.env` nor SovereignMCP env config), not model/routing.
- Hard gates are functioning correctly and prevent accidental mock behavior for live OpenRouter calls.

## Durable Lessons (2026-04-16) — Golden Path + Handshake Fix

- In `tools/exoskeleton_tool.py`, golden-path match payloads from multiple sources (oracle vs fallback) can diverge (`path_name` vs `name`). Normalize once and use the normalized form everywhere.
- Golden-path auto-promotion must refresh both persisted file and in-memory runtime structures (`self.golden_paths`, oracle cache) or new paths do not influence routing until process restart.
- Duplicate suppression for auto-promoted paths should check both canonical key and chain-equivalence, not only one string key comparison.
- If golden paths should actively guide routing, inject matched-chain bonus directly inside scoring (`_score_tools`) rather than only surfacing match text in intent/briefing output.
- MCP stdio initialize can fail from protocol contamination even when core server logic is fine: any import-time `print(...)` to stdout from loaded modules can corrupt handshake framing.
- Replacing startup-time stdout prints with logger warnings (stderr/log path) restores clean initialize responses.
- For this workspace, execute validation with `./mcp.venv/bin/python` for reproducibility.

## Durable Lessons (2026-04-24) — Neural-Symbolic Wiring Completion

### API surface contract: `bb7_dt_encode` vs `bb7_dt_encode_catalog`

- `bb7_dt_encode(tool_sequence: List[Dict])` — low-level, expects `[{"tool_name":..., "category":..., "param_hash":...}]`, returns `"hidden_states"` key. Limited to `max_seq_len=64` per call.
- `bb7_dt_encode_catalog(tool_names: List[str], tool_categories: Optional[Dict])` — catalog-scale API. Converts to proper dict format internally, chunks transparently, returns `"embeddings": {tool_name: [float, ...]}`. Always use this at call sites that have a flat list of tool names.
- **The original bugs**: callers were passing `List[str]` to `bb7_dt_encode` (type error) AND reading `"embeddings"` key that doesn't exist (real key is `"hidden_states"`). Both killed the injection silently. `bb7_dt_encode_catalog` fixes both at the API boundary.

### Early-init vs late-init subsystem ordering in `__init__`

- `_refresh_spectral_catalog()` is called inside `_load_catalog()` which runs early in `__init__` — before `_digital_twin`, `_session_momentum`, and `_cached_neural_attention` exist.
- Any method called early that depends on late-initialized attributes silently no-ops via `getattr(..., None)` guards.
- **Fix pattern**: add a second `_refresh_spectral_catalog()` call at the very end of `__init__`, after all subsystems are live. This ensures caches and manifold weights are populated at startup. Apply this pattern whenever a subsystem init depends on other subsystems being ready.

### `_reliability` vs `_reliability_sampled` split — where each is correct

- `_reliability(tool_name)` — deterministic posterior mean `alpha / (alpha + beta)`. Use for: chain confidence scoring, failure point analysis, alternative tool ranking, recovery strategy selection. Reproducibility matters in these paths.
- `_reliability_sampled(tool_name, context_category)` — stochastic Beta draw conditioned on category + neural Q-bonus. Use for: candidate scoring in `_score_tools` only. Drives organic exploration of under-sampled tools.
- **Never swap them**: deterministic in confidence/failure paths prevents score instability; stochastic in scoring is the only place you want Beta noise.

### MCTS planner output schema mismatch

- `_MCTSPlanner.search()` returns `{chain, confidence, estimated_tokens, tree_reward, failure_points, adversarial_survived}` — does NOT include `plan_id`, `fallback`, `estimated_latency_ms`.
- `bb7_exo_plan` downstream expects `plan_id` as a hard key (no `.get()` fallback) — raises `KeyError` if MCTS output is used raw.
- **Fix pattern**: normalize MCTS output immediately after `.search()` returns, adding `plan_id`, `fallback`, `estimated_latency_ms`. Wrap with `{**raw, "plan_id": ..., "fallback": ..., ...}` so all MCTS-specific fields survive.
- This was previously masked because `_mcts_planner` was never instantiated — the AttributeError bubbled up and was caught by the outer try/except in `bb7_exo_plan`. Instantiating the planner exposed the schema gap.

### muadib `tool_modality.py` import structure

- The file imports `EclogueConfig` from `transformer_backbone` (an external module that doesn't exist in this repo). The `except ImportError` fallback stubs `EclogueConfig` but was missing stubs for `MemorySystem`, `EnhancedRSLMemorySystem`, `ReasoningMode` from the same import line.
- These are only used as Optional type annotations in `UniversalToolControlOutputHead.generate()` — minimal pass stubs are all that's needed.
- `tool_modality.py` uses its own `EclogueConfig` stub internally (not `SubstrateConfig`). The actual routing substrate uses `SubstrateConfig → NeuralNetConfig` in `muaddib.py`. Do not conflate the two.

### Chunked encoding for large catalogs

- `max_seq_len=64` in `SubstrateConfig` means any catalog > 64 tools must be encoded in chunks. With 110 tools, that's 2 forward passes.
- `bb7_dt_encode_catalog` handles this transparently: best-effort per chunk, assembles all embeddings regardless of partial chunk failures.
- Chunk failures should be logged at WARNING (not ERROR) and treated as best-effort — a partial embedding set is better than no embedding injection at all.

### Validation environment

- Always use `mcp.venv` at `/home/daeron/Somnus-MCP/mcp.venv` — torch 2.11.0+cpu, Python 3.12.3.
- `cd /home/daeron/Somnus-MCP && mcp.venv/bin/python -c "..."` is the canonical test invocation.
- The `sys.path.insert(0, '.')` is required for relative imports from workspace root.

## Sovereign Reasoning Architecture (SRA) V1.0 Planning Notes (2026-05-05)

- **Conceptual Shift**: SRA treats the transformer merely as "output muscle" and isolates reasoning into a sovereign substrate (tensor space) via a 4-layer stack: CoT -> Stability Gate -> ToT -> Stability Gate -> Scratchpad Synthesis -> Pre-output Simulation -> Recursive Reflection.
- **Attention Replacement**: Standard attention is bypassed in reasoning in favor of a "Typed Scratchpad" with explicitly prioritized slots (IMMEDIATE, SHORT_TERM, CONTRADICTION, etc.) to heavily reduce O(n²) scaling and explicitly enforce logical structures.
- **Deep Equilibrium (The See-Saw)**: The reasoning passes are recursive. A Stability Matrix checks iterations, only advancing to the generation backbone once the representation achieves mathematical equilibrium (spectral radius < 1).
- **Implementation Status**: As of 2026-05-05, the real reasoning engines are *not* inside the `Somnus-MCP` workspace yet. The design is in the formal specification stage.
- **Architectural Decision Pending**: The user is currently deciding whether to commit to running all 4 reasoning phases for every architecture, or to implement on a per-architecture basis (e.g., some simple setups might just use the Chain of Thought engine without ToT or explicit scratchpad loops).
- **Integration Plan**: When implementation begins, it will follow the Garlic Injection pattern, injecting into the backbone at early/middle/late layers rather than altering the core LLM weights.

## Durable Lesson (2026-05-23 18:15) - Muad'Dib Advanced Integration Planning

- Runtime truth: DigitalTwin wiring is active, but advanced modality stack is not yet first-class in control-plane scoring.
- Future integration must be fail-open with explicit bridge health flags and conservative blending to protect 24/7 reliability.
- Distillation language should remain precise: trajectory capture for RFT flywheel, with .codex/history.json as seed traces, not external-model knowledge distillation.


## 2026-06-01: visual_tool headless Linux DISPLAY startup fix

- User direction: use memory more aggressively (Codex memory + Sovereign/BB7 memory) and resolve the visual tool health degradation.
- Durable gotcha: in Linux MCP startup contexts, `DISPLAY`/`WAYLAND_DISPLAY` may be absent even when an interactive terminal has `DISPLAY=:0`; optional GUI imports must not run before display availability is checked.
- Root cause: `tools/visual_tool.py` only caught `ImportError` around `import pyautogui`, but `mouseinfo` can raise `KeyError('DISPLAY')` during import.
- Fix pattern: treat pyautogui as optional, preflight display env, catch broad import exceptions for GUI stack imports, preserve import error text, and let module registration succeed in `headless_mode`.
- Evidence: fresh headless `MCPServer()` init loaded `visual_tool` and registered all five visual tools with no `failed_loads.visual_tool` entry; py_compile passed for `tools/visual_tool.py` and `mcp_server.py`.
- Restart note: current live MCP health may remain stale until the Codex MCP wrapper restarts and imports the patched module.

## 2026-06-05: FSTIP file-surface token isolation

- Durable rule: MCP/file-tool display output should be a verification vector, not a filesystem echo. Raw file content belongs on disk and in telemetry/persistence lanes, not in the active high-context conversation unless explicitly requested.
- `bb7_read_file` now has bounded read controls: `start_line`, `end_line`, `semantic_target`, and `allow_large_raw`. Prefer line or semantic windows for comprehension; large naked reads return a structural skeleton manifest by default.
- `bb7_write_file` and `bb7_append_file` now emit `FILE_PATCH_SUCCESS` manifests with sparse old/new delta windows. Do not regress these into full rewritten-file echoes.
- Manifest metadata must use logical line counting via `splitlines()`, not literal `"\\n"` token splitting/counting; a live reload probe caught the bad symptom (`Lines: 1` for a three-line delta), and source validation now reports `Lines: 3` correctly.
- `mcp_server.py` now applies a final display-only file-surface projection for string payloads from file tools. This projection must never feed back into Q-table scoring, observations, memory exchange, or distillation/RFT capture; raw payload preservation before projection is the invariant.
- Configuration knobs:
  - `SOVEREIGN_FILE_READ_GOVERNOR_BYTES` defaults to 131072 bytes and clamps between 32768 and 1048576.
  - `SOVEREIGN_FILE_SURFACE_INLINE_MAX_CHARS` defaults to 24000 chars and clamps between 1200 and 50000 at the MCP display seam.
- Validation evidence lives in `data/validation/fstip_file_surface_token_isolation_20260605.{md,json}`.
- Restart/reload caveat: source edits do not mutate already-loaded MCP tool instances; live Codex calls may require server restart/reload to expose new schemas and behavior.
