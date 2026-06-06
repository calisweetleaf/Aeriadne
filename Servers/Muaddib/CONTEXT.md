## Current State — 2026-06-04: Live Display Projection Verified After Reboot

Post-reboot live behavior now proves the display cleanup is active in the
connected MCP gateway.

Evidence:
- Live `bb7_tool_health_report` returned Markdown projection beginning
  `### bb7_tool_health_report: HEALTHY`, not raw JSON.
- Live health facts in the projection: `total_tools=134`,
  `registered_tools=134`, `pid=279417`, `session_id=ses_d9f6d1c251b5`,
  `transport=stdio`, `data_dir=/home/daeron/Somnus-MCP/data`,
  `source_sha256_16=5ba59ef01ffc865e`.
- Live `bb7_lisan_recall` returned Markdown projection beginning
  `### bb7_lisan_recall: OK` and summarized memory lines without dumping the
  full context blob.
- Both live outputs include the raw-hidden/raw-preserved notice and the
  `SOVEREIGN_DISPLAY_PROJECTION=raw` escape hatch.

Artifacts:
- `docs/validation/2026-06-04-display-projection-live-proof.md`
- `docs/validation/2026-06-04-display-projection-live-proof.json`

Operational meaning:
- The source-level display projection from the prior section is now loaded in
  the live Codex/MCP gateway.
- Cleaned Markdown summaries remain human display only; raw substrate payloads
  still feed telemetry, memory exchange, Q-play, observations, and
  RFT/distillation before projection.

---

## Current State — 2026-06-04: Display Projection Layer Cleaned

The human-facing MCP display seam has been cleaned without changing the raw
substrate paths used by Q-play, observations, memory exchange, or RFT/distillation.

What changed:
- `mcp_server.py` now projects verbose dict/list tool payloads into concise
  Markdown key facts at the final `_format_tool_result(...)` seam.
- Projection is default-on for raw dict/list payloads but remains display-only:
  `meta.display_projection` marks `projection_for_display_only=true`,
  `raw_payload_in_content=false`, `raw_preserved_before_projection=true`,
  `not_for_qtable=true`, `not_for_observations=true`,
  `not_for_distillation=true`, and `not_for_rft=true`.
- Preformatted MCP `content` payloads are honored unchanged.
- `SOVEREIGN_DISPLAY_PROJECTION=raw` restores canonical raw JSON display;
  `SOVEREIGN_DISPLAY_PROJECTION_MAX_CHARS` bounds Markdown projection length.
- Tool-specific projectors now summarize the noisy surfaces that triggered this
  work: `bb7_exo_bootstrap`, `bb7_lisan_recall`, `bb7_exo_briefing`,
  `bb7_tool_health_report`, and `bb7_muadib_mentat_bridge`.

Raw-substrate guardrail:
- Static validation confirms `_trajectory_buffer.append`, `_log_tool_usage`,
  event-spine `tool_execution_end`, `_schedule_tool_exchange_memory_persist`,
  `_build_sovereign_meta`, and `_auto_reflect_tool_call` all occur before
  `_format_tool_result(...)` in `handle_call_tool`.
- Therefore the display projection is not fed back as raw Q-table observation,
  ambient memory payload, or RFT/distillation payload.

Validation:
- `mcp.venv/bin/python -m py_compile mcp_server.py scripts/validate_display_projection.py scripts/verify_muadib_one_plane_gate.py scripts/run_muadib_one_plane_validation.py scripts/write_muadib_completion_audit.py` passed.
- `mcp.venv/bin/python scripts/validate_display_projection.py --json` passed
  `31` checks and wrote `docs/validation/2026-06-04-display-projection.md/json`.
- `mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py --live-health-json docs/validation/2026-06-04-bb7-tool-health-post-reboot.json --json` passed
  `29` source+live checks.
- `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --live-health-json docs/validation/2026-06-04-bb7-tool-health-post-reboot.json --require-live --json` passed with
  `ok=true`, `source_suite_ok=true`, `completion_ready=true`,
  `live_status=PASS`, self-play `ok=true`, display projection `ok=true`,
  source checks `23`, display checks `31`, and source+live gate checks `29`.
- The generated completion audit now includes
  `display_projection_not_substrate_truth=proved` alongside the original
  one-plane requirements and remains `complete=true` with no pending IDs.

Operational meaning:
- The connected live process will show the cleaned display layer after normal
  gateway/client reload onto this source; until then, source artifacts prove the
  seam and `SOVEREIGN_DISPLAY_PROJECTION=raw` remains the exact-display escape.
- Do not route the Markdown display summary into Q-play, observation logs, or
  RFT exports as if it were the original raw tool result.

---

## Current State — 2026-06-04: Post-Reboot Live Parity Passed

Codex was rebooted and the connected Somnus-MCP gateway now reports
current-source live registry parity.

What changed:
- Captured fresh post-reboot health evidence in
  `docs/validation/2026-06-04-bb7-tool-health-post-reboot.json`.
- Ran strict one-plane suite with that live health JSON:

```bash
mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py \
  --live-health-json docs/validation/2026-06-04-bb7-tool-health-post-reboot.json \
  --require-live \
  --json
```

- `docs/validation/2026-06-04-muadib-validation-suite.json` now reports:
  - `ok=true`;
  - `source_suite_ok=true`;
  - `completion_ready=true`;
  - `live_status=PASS`;
  - source checks `22`;
  - self-play checks `15`;
  - live checks `28`.
- The generated completion audit now reports:
  - `complete=true`;
  - `completion_ready=true`;
  - `live_status=PASS`;
  - `pending_requirement_ids=[]`.
- `docs/validation/2026-06-04-muadib-one-plane-gate.*` was refreshed from
  `source_gate_pass_self_play_weights_pass_live_gate_pending_reload` to
  `source_gate_pass_self_play_weights_pass_live_gate_pass`.

Live evidence:
- Fresh `bb7_tool_health_report` after reboot:
  - `status=healthy`;
  - `total_tools=134`;
  - `runtime_identity.pid=142824`;
  - `runtime_identity.session_id=ses_4ae8c045bbba`;
  - `runtime_identity.data_dir=/home/daeron/Somnus-MCP/data`;
  - `runtime_identity.source_sha256_16=4600f1e1a25efef7`;
  - `registered_tools` includes both `bb7_muadib_mentat_bridge` and
    `bb7_tool_refresh_module`.
- Direct `bb7_muadib_mentat_bridge(operation="snapshot")` call succeeded and
  proved:
  - `mcp_server_is_intelligence=false`;
  - `gateway_process_is_cognition_plane=false`;
  - `one_cognition_data_plane=true`;
  - `mutates_mcp_output_adapter=false`;
  - active tokenizer checkpoint is `checkpoint_v5327.safetensors`;
  - advanced bridge is active;
  - exoskeleton indexes `134` tools.
- Direct source+live verifier command passes 28 checks:

```bash
mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py \
  --live-health-json docs/validation/2026-06-04-bb7-tool-health-post-reboot.json \
  --json
```

Operational meaning:
- The original one-plane objective is now fully evidenced in source and live
  runtime: `mcp_server.py` remained gateway/raw JSON boundary, Muad'Dib has real
  safetensors self-play/active checkpoints, Mentat/meta bridge is live and
  read-only, access surfaces remain gateways, and the connected process proves
  one canonical data plane.

---

## Current State — 2026-06-04: Completion Audit Writer Integrated

The Muad'Dib one-plane completion audit is now generated and suite-integrated,
not a one-off hand-written artifact.

What changed:
- Added/locked `scripts/write_muadib_completion_audit.py` as the repo-native
  audit synthesizer.
- `scripts/run_muadib_one_plane_validation.py` now refreshes
  `docs/validation/2026-06-04-muadib-completion-audit.md` and `.json` after it
  writes the suite JSON.
- `scripts/verify_muadib_one_plane_gate.py` now checks both:
  - `completion_audit_writer_present`;
  - `completion_audit_artifact_present`.
- `docs/validation/2026-06-04-muadib-one-plane-gate.*` was refreshed so the
  source gate count matches current source.

Validation performed:
- `mcp.venv/bin/python -m py_compile` passed for the gateway, Muad'Dib,
  exoskeleton, meta bridge, validation scripts, and access gateway files.
- `mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py --json` passes
  **22** source checks.
- `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json`
  passes with `source_suite_ok=true`, `completion_ready=false`,
  `live_status=PENDING_RELOAD`, self-play checks `15`, source checks `22`, and
  runtime audit `mutated_runtime=false`.
- Synthetic current-source live health passes strict mode with
  `completion_ready=true`, proving the gate can flip only when live health has
  current-source `runtime_identity` + `registered_tools`.
- Actual connected `bb7_tool_health_report` sampled at timestamp
  `1780577252.1807277` still reports `total_tools=129` with no
  `runtime_identity`, no `registered_tools`, no `bb7_muadib_mentat_bridge`, and
  no `bb7_tool_refresh_module`.

Operational meaning:
- Source/proof work is complete for the audit-generator lane.
- The active one-plane objective is **not complete** until the operator reloads
  the MCP client/gateway, captures a fresh current-source health report, and
  strict suite mode passes:

```bash
mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py \
  --live-health-json /path/to/bb7_tool_health_report.json \
  --require-live \
  --json
```

---

## Current State — 2026-06-04: Completion Audit Artifact Added

The active Muad'Dib one-plane objective now has a requirement-by-requirement completion audit.

What changed:
- Added `docs/validation/2026-06-04-muadib-completion-audit.md` and `.json`.
- The audit maps the original objective into explicit requirements:
  - raw JSON/output adapter preservation;
  - `mcp_server.py` as gateway, not intelligence;
  - `tools/meta_intelligence_engine.py` as Muad'Dib/Mentat bridge;
  - HTTPS/webhook/hook access surfaces as gateways;
  - Muad'Dib safetensors self-play weights;
  - archive-only / lock semantics to prevent silent active-weight drift;
  - one-plane runtime identity/registry proof;
  - post-reload live gate.
- `scripts/verify_muadib_one_plane_gate.py` now checks `completion_audit_artifact_present`.

Validation performed:
- `mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py --json` now passes 21 source checks.
- `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json` passes source suite with `completion_ready=false` and `live_status=PENDING_RELOAD`.
- The completion audit reports `complete=false` because live current-source health is still missing.

Operational meaning:
- Source-side work is strongly evidenced, including real safetensors self-play weights.
- Do not complete the active goal until the audit has no live-pending rows and strict suite mode passes with real post-reload health.

---

## Current State — 2026-06-04: One-Plane Validation Suite Runner Added

The Muad'Dib one-plane proof chain now has a repo-native suite runner.

What changed:
- Added `scripts/run_muadib_one_plane_validation.py`.
- The runner composes:
  - `scripts/validate_muadib_self_play_weights.py`;
  - `scripts/verify_muadib_one_plane_gate.py`;
  - `scripts/audit_mcp_runtime_identity.py`;
  - optional post-reload `--live-health-json`.
- It writes `docs/validation/2026-06-04-muadib-validation-suite.md` and `.json` by default.
- It does not instantiate `MCPServer`, restart/signal live processes, mutate canonical runtime state, or touch output adapters.
- Default mode passes when the source suite is valid and records `live_status=PENDING_RELOAD`.
- Strict completion mode uses `--live-health-json <path> --require-live` and fails unless live current-source health passes.

Validation performed:
- `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json` passed with `source_suite_ok=true`, `completion_ready=false`, `live_status=PENDING_RELOAD`.
- `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --require-live --skip-self-play --no-write-artifacts --json` correctly exited nonzero without live health.
- Synthetic current-source health passed strict mode with `completion_ready=true`.
- `scripts/verify_muadib_one_plane_gate.py --json` now passes 20 source checks including `validation_suite_runner_present`.

Operational meaning:
- Before reload: use the runner to prove source/self-play/runtime-audit state.
- After reload: provide fresh `bb7_tool_health_report` JSON with `runtime_identity` + `registered_tools` and run strict mode to decide whether the active goal can complete.

---

## Current State — 2026-06-04: Isolated Muad'Dib Self-Play Weights Validation Added

The Muad'Dib self-play weight lane now has a reusable isolated validator and validation artifact.

What changed:
- Added `scripts/validate_muadib_self_play_weights.py`.
- The validator instantiates only `DigitalTwinTool(data_dir=temp)`, never `MCPServer`.
- It runs archive-only self-play (`promote=false`, `update_qtable=false`) and verifies a non-empty `.safetensors` candidate checkpoint is written in the temp data dir.
- It then enables the promotion lock and verifies a `promote=true` request still archives a `.safetensors` candidate without promoting active/champion state.
- Added `docs/validation/2026-06-04-muadib-self-play-weights.md` and `.json`.
- `scripts/verify_muadib_one_plane_gate.py` now checks both the isolated validator source and the recorded self-play validation artifacts.

Validation performed:
- `mcp.venv/bin/python scripts/validate_muadib_self_play_weights.py --json` passed 15 checks.
- The archive-only run wrote `self_play_head_v1.safetensors` (~19.9 MB), reported `promoted=false`, and reported `qtable_updated=false`.
- The locked promotion run wrote `self_play_head_v2.safetensors`, reported `promotion_requested=true`, `promoted=false`, and `active_locked=true`.
- The temp validation data directory was cleaned up after the run.
- `mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py --json` now passes 19 source checks including `isolated_self_play_weight_validator_present` and `self_play_weight_validation_artifacts_present`.

Operational meaning:
- This proves current source can produce real safetensors self-play weights without using JSON as weight storage.
- This does not prove the connected live BB7 gateway has reloaded current source; live parity still requires `bb7_tool_health_report.runtime_identity` plus `registered_tools` after MCP reload.

---

## Current State — 2026-06-04: Health Registry Projection Hardened

The post-reload live gate now has a stable registry proof path.

What changed:
- `mcp_server.py::_tool_health_report_impl` now emits deterministic `registered_tools=sorted(self.tools.keys())`.
- `scripts/verify_muadib_one_plane_gate.py` now requires current-source health to expose that deterministic registry projection and uses `registered_tools` as the primary live proof for `bb7_muadib_mentat_bridge` and `bb7_tool_refresh_module`.
- `unused_tools` remains accepted only as a backward-compatible fallback because a tool disappears from that projection after it is called.
- `MCP_SPEC.md`, `README.md`, `ARCHITECTURE.md`, `workflows-new.md`, and `docs/validation/2026-06-04-muadib-one-plane-gate.*` now document this contract.

Validation performed:
- `mcp.venv/bin/python -m py_compile mcp_server.py scripts/verify_muadib_one_plane_gate.py` passed.
- `mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py --json` passed source mode.
- Synthetic current-source live health with bridge/refresh only in `registered_tools` passed `scripts/verify_muadib_one_plane_gate.py --live-health-json`.
- Connected live BB7/SovereignMCP still reports old 129-tool health without `runtime_identity` or `registered_tools`; live parity remains pending reload.

Operational meaning:
- Post-reload completion proof should inspect `runtime_identity` plus `registered_tools`, not just `status=healthy` and not only `unused_tools`.
- This is source/live observability work in the gateway, not an MCP output/display adapter change.

---

## Current State — 2026-06-04: Access Gateways Aligned With Muad'Dib/Tools Doctrine

The gateway correction now covers the access/event layer, not only `mcp_server.py`.

What changed:
- `scripts/verify_muadib_one_plane_gate.py` now includes `access_gateway_doctrine_recorded`.
- The verifier requires `docs/https_wrapper_endpoints.md`, `HOOK_BRIDGE.md`, `https_wrapper.py`, `webhook_engine.py`, `hook_executor.py`, `MCP_SPEC.md`, and `workflows-new.md` to state the access/event surfaces are gateways into the same Muad'Dib + `tools/` cognition plane.
- `docs/validation/2026-06-04-muadib-one-plane-gate.md` and `.json` were refreshed with an explicit **Access gateway doctrine gate: PASS** status.

Operational meaning:
- `https_wrapper.py` is authenticated transport plumbing into the existing cognition plane, not a separate intelligence layer, output cleaner, or routine validation surrogate.
- `webhook_engine.py` is gateway event egress, not a second cognition plane or owner of weights/Q-table/registry truth.
- `hook_executor.py` / `HOOK_BRIDGE.md` are lifecycle/event signal ingress into the existing gateway/state-machine path, not a second server or tool plane.
- The intelligence remains behind the gateway in `muadib/` and `tools/`: weights, self-play, routing, reflection, memory synthesis, and higher-order answer compilation stay there.

Validation performed:
- `mcp.venv/bin/python -m py_compile mcp_server.py tools/meta_intelligence_engine.py scripts/verify_muadib_one_plane_gate.py scripts/audit_mcp_runtime_identity.py https_wrapper.py webhook_engine.py hook_executor.py` passed.
- `mcp.venv/bin/python -m json.tool tool_manifest.json` passed.
- `mcp.venv/bin/python -m json.tool docs/validation/2026-06-04-muadib-one-plane-gate.json` passed.
- `mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py --json` passed 17 checks, including `access_gateway_doctrine_recorded`.

Live runtime caveat:
- Connected live BB7/SovereignMCP still reports old 129-tool health without `runtime_identity`, so live parity is still pending client/MCP reload. Do not mark the objective complete until post-reload live health passes `scripts/verify_muadib_one_plane_gate.py --live-health-json`.

---

## Current State — 2026-06-04: Bridge Emits Gateway/Cognition Contract

The Muad'Dib/Mentat bridge now surfaces the gateway doctrine in its machine-readable payload, not only in docs.

What changed:
- `tools/meta_intelligence_engine.py::bb7_muadib_mentat_bridge` contract now includes:
  - `gateway_role`
  - `cognition_plane_role`
  - `one_cognition_data_plane=true`
  - `stdio_gateway_children_may_exist=true`
  - `mcp_server_is_intelligence=false`
  - `gateway_process_is_cognition_plane=false`
- Bridge payload now includes a `gateway` block derived from `bb7_tool_health_report.runtime_identity` when the answering gateway exposes current-source health identity.
- The bridge recommendation list now explicitly says to treat `mcp_server.py` as gateway into Muad'Dib + tools, not as the intelligence layer.
- `README.md`, `ARCHITECTURE.md`, `MCP_SPEC.md`, `workflows-new.md`, `tool_manifest.json`, validation artifacts, and `scripts/verify_muadib_one_plane_gate.py` were updated to require/document the bridge gateway contract.

Validation performed:
- `mcp.venv/bin/python -m py_compile mcp_server.py tools/meta_intelligence_engine.py scripts/verify_muadib_one_plane_gate.py scripts/audit_mcp_runtime_identity.py` passed.
- Temp-data bridge smoke with fake `bb7_tool_health_report.runtime_identity` confirmed the bridge emits `mcp_server_is_intelligence=false`, `gateway_process_is_cognition_plane=false`, `one_cognition_data_plane=true`, and `gateway.identity_available=true`.
- `scripts/verify_muadib_one_plane_gate.py --json` now passes 16 checks, including `bridge_gateway_contract_source_present`.
- `scripts/audit_mcp_runtime_identity.py --json` remains read-only and reports two stdio gateway children sharing the canonical data root.

Live runtime caveat:
- Connected live BB7/SovereignMCP still reports old 129-tool health without `runtime_identity`, so live parity is still pending client/MCP reload.

---

## Current State — 2026-06-04: Gateway Doctrine Locked

User correction integrated: `mcp_server.py` is the gateway/dispatcher into the 4-7 Muad'Dib + `tools/` cognition layers, not the intelligence itself and not the place to move heavy neural ownership.

What changed:
- `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `ARCHITECTURE_MAP.md`, `MCP_SPEC.md`, `workflows-new.md`, and `5-26-2026-muaddib-mcp-filetree.md` now state the gateway doctrine explicitly.
- Runtime invariant language was refined from process-worship to one cognition/data plane: persistent transports should share one gateway process, while stdio clients may spawn per-client gateway children that must not fork data/neural state.
- `mcp_server.py` should remain thin around transport, registry, lifecycle, raw JSON boundary, telemetry, and source/live observability.
- Neural self-play, routing, reflection, memory synthesis, and higher-order answer compilation remain in `muadib/` and `tools/`.

Operational meaning:
- Do not use an observed output/display issue as a reason to grow `mcp_server.py` into the intelligence layer.
- The source/live identity work identifies which gateway process is answering; it does not redefine the cognition plane as the gateway PID.
- The remaining live caveat persists until the connected BB7/SovereignMCP gateway reloads current source and passes the live gate.

---

## Current State — 2026-06-04: Self-Play Promotion Defaults Flipped to Archive-Only

The promotion-lock correction is now stricter: continuous self-play no longer advances active/champion weights by default. Safetensors are real weights, but safetensors alone do not freeze semantic model state; promotion policy does.

What changed:
- `DigitalTwinTool.bb7_dt_self_play(...)` now defaults `promote=False`.
- `ExoskeletonTool.bb7_dt_self_play(...)` now defaults `promote=False`.
- The autonomous exo cycle now reads `MUADIB_SELF_PLAY_PROMOTE` with default `False`/`0`.
- `tool_manifest.json`, `README.md`, `MCP_SPEC.md`, `workflows-new.md`, `ARCHITECTURE.md`, `PLAN.md`, and validation artifacts were updated to describe archive-only default semantics.

Operational meaning:
- Continuous self-play may still generate candidate `.safetensors` archives.
- Active/champion weights advance only when the operator explicitly opts into promotion (`promote=true` or `MUADIB_SELF_PLAY_PROMOTE=1`) and the active promotion lock is not set.
- This prevents accidental drift from the autonomous cadence while preserving the self-play data/checkpoint lane.

Validation performed:
- `mcp.venv/bin/python -m py_compile mcp_server.py muadib/muaddib.py tools/exoskeleton_tool.py scripts/verify_muadib_one_plane_gate.py` passed.
- `mcp.venv/bin/python -m json.tool tool_manifest.json` passed.
- Import/signature smoke confirmed DigitalTwinTool and ExoskeletonTool `bb7_dt_self_play.promote` defaults are `False`.
- `scripts/verify_muadib_one_plane_gate.py --json` now includes and passes `self_play_promotion_defaults_archive_only`.

Live runtime caveat:
- The connected live MCP process still reports 129 tools before reload, so treat the running process as old-source until live health proves otherwise.

---

## Current State — 2026-06-04: Meta Bridge Gameplan Surface Added

The one-plane gameplan now has explicit Mentat scope and a read-only Muad'Dib/Mentat bridge surface.

What changed:
- Added `.mentat/scope.md` for the Muad'Dib one-plane gameplan. In scope: preserve raw JSON boundary, keep one server/data plane, use `tools/meta_intelligence_engine.py` as a registry-bound facade, keep Mentat as observer/conductor, and validate without duplicate runtimes. Out of scope: broad output adapter cleanup, second trainer/server/data plane, Mentat ownership of weights/Q-table, and unbounded self-play.
- Added a "Plan Tasks — Muad'Dib One-Plane Gameplan" section to `PLAN.md`.
- Added `bb7_muadib_mentat_bridge` to `tools/meta_intelligence_engine.py` and `tool_manifest.json`.
- The bridge calls already-registered live BB7 surfaces when available (`bb7_dt_checkpoint_status`, `bb7_dt_advanced_features`, `bb7_exo_state`, `bb7_tool_health_report`) and reads bounded Mentat sidecar files (`~/.mentat`, workspace `.mentat/scope.md`).
- The bridge contract explicitly says it does not instantiate sibling tools, start a server, mutate Muad'Dib weights, mutate Q-table state, or alter the MCP output adapter/display boundary.

Validation performed:
- `mcp.venv/bin/python -m py_compile tools/meta_intelligence_engine.py` passed.
- `mcp.venv/bin/python -m json.tool tool_manifest.json` passed.
- Smoke test with a fake attached tool plane confirmed JSON parses, live registry stubs are called, Mentat scope is included, and contract booleans remain read-only.
- Source boundary check confirmed `mcp_server.py` still owns `_format_tool_result` with `json.dumps(payload, indent=2)` and contains no bridge-specific output adapter special case.

Live runtime caveat:
- Source/schema exposes `bb7_muadib_mentat_bridge` after server/module reload. The already-running process may not expose it until the operator lifecycle reloads the tool plane.

---

## Current State — 2026-06-04: Guarded Facade Refresh Surface Added

Source now includes a guarded in-place refresh surface for source/live parity of registry-bound facades.

What changed:
- Added built-in `bb7_tool_refresh_module` to `mcp_server.py`.
- Current allowlist is intentionally narrow: `meta_intelligence_engine` only.
- The refresh path reloads/rebuilds the facade inside the existing `MCPServer` instance, atomically replaces that module's tool entries, reattaches registry-bound facades, reattaches exoskeleton/OpenRouter agent registry consumers, and resyncs exoskeleton catalog.
- It explicitly does not rerun full `register_tools()`, does not start a second server, does not start another autonomous cycle, and does not alter the JSON-RPC/display output adapter.
- Initial boot now also calls `_attach_registry_bound_facades()` after module registration so `meta_intelligence_engine.py` is actually bound to the live registry instead of merely existing as a tool module.

Validation performed:
- `mcp.venv/bin/python -m py_compile mcp_server.py tools/meta_intelligence_engine.py` passed.
- `mcp.venv/bin/python -m json.tool tool_manifest.json` passed.
- Smoke with a fresh `MCPServer` instance showed source boot registers 134 tools, includes `bb7_muadib_mentat_bridge`, attaches the meta facade to `server.tools`/`server.tool_modules`, refreshes `meta_intelligence_engine` with `started_server=false`, `reran_register_tools=false`, `output_adapter_touched=false`, and rejects disallowed `exoskeleton_tool` refresh.
- Raw output boundary check still confirms `_format_tool_result`, `json.dumps(payload, indent=2)`, and normal formatted result calls.
- Added and ran `scripts/verify_muadib_one_plane_gate.py`; source mode now passes and covers raw JSON boundary, bridge/refresh source surfaces, Muad'Dib self-play surfaces, manifest/docs/scope/plan, and recorded live caveats.
- Wrote validation artifacts:
  - `docs/validation/2026-06-04-muadib-one-plane-gate.md`
  - `docs/validation/2026-06-04-muadib-one-plane-gate.json`

Validation caveat:
- `mcp_server.py` enforces canonical `/home/daeron/Somnus-MCP/data`; the fresh-instance smoke could not use a temp data root and wrote normal runtime artifacts including `data/digital_twin/checkpoint_v5270.safetensors` during exoskeleton/Muad'Dib warm-up.
- The currently connected live MCP process still reports 129 tools and does not yet expose `bb7_tool_refresh_module`/`bb7_muadib_mentat_bridge`; those surfaces become live after the process reloads into the new source.

---

## Current State — 2026-06-04: Muad'Dib Promotion Lock Clarified

Correction locked: safetensors locks the tensor serialization/integrity boundary, not semantic immutability. With continuous self-play enabled, weights are live unless active/champion promotion is pinned.

What changed:
- Added `bb7_dt_self_play_lock` to pin/unpin active self-play promotion while allowing candidate self-play to continue writing `.safetensors` archives.
- `bb7_dt_self_play` now distinguishes `promotion_requested` from `promoted`; active locks force archive-only training even when callers request promotion.
- `bb7_dt_checkpoint_status` reports `active_locked`, `lock_source`, and `locked_checkpoint`.
- Self-play pruning now protects the active/locked checkpoint so `MUADIB_SELF_PLAY_PROMOTE=0` or a promotion lock cannot silently orphan the pinned active head after enough candidates accumulate.
- Autonomous cadence events now include promotion-requested and active-lock fields.

Operational meaning:
- Archive-only default path: keep `MUADIB_SELF_PLAY_PROMOTE=0` (the default); continuous self-play writes candidate safetensors without advancing active/champion weights.
- Live learning path: deliberately set `MUADIB_SELF_PLAY_PROMOTE=1` and keep `MUADIB_SELF_PLAY_LOCK_ACTIVE=0`; active weights advance by atomic checkpoint promotion.
- Reproducible/champion path: call `bb7_dt_self_play_lock(locked=true, reason=...)` or set `MUADIB_SELF_PLAY_LOCK_ACTIVE=1`; candidate checkpoints continue, active weights remain pinned even if promotion is requested.

Validation performed:
- `mcp.venv/bin/python -m py_compile muadib/muaddib.py tools/exoskeleton_tool.py mcp_server.py` passed.
- `mcp.venv/bin/python -m json.tool tool_manifest.json` passed.
- Temp-root `DigitalTwinTool` smoke confirmed lock prevents promotion while archiving candidates, unlock restores promotion, and `qtable_updated=false`.
- Temp-root prune smoke confirmed an old locked active checkpoint is preserved while later candidate archives are pruned.
- Exoskeleton wrapper smoke confirmed `bb7_dt_self_play`, `bb7_dt_self_play_lock`, and `bb7_dt_checkpoint_status` appear in `get_tools()`.
- Source boundary check confirmed `_format_tool_result` still exists with `json.dumps(payload, indent=2)` and normal formatted tool-result calls.

---

## Current State — 2026-06-04: Muad'Dib Continuous Self-Play Cadence Wired

Bounded continuous self-play is now wired into the existing `mcp_server.py` autonomous exo cycle without changing the JSON-RPC result adapter or display/content-block formatting boundary.

What changed:
- Added safe env parsing helpers in `mcp_server.py` (`_env_bool`, `_env_int`) so cadence knobs cannot break import/startup.
- Extended the existing Muad'Dib telemetry block in `_autonomous_exo_cycle_loop` to call `exo.bb7_dt_self_play(...)` on cadence.
- Defaults: enabled, every 32 cycles (~24 minutes at 45s/cycle), 4 episodes, 3 steps, archive completed safetensors candidates without promotion, do **not** update the real Q-table.
- On success, appends a `muadib_self_play_checkpoint` event with checkpoint name, safetensors format, promotion flag, avg reward/loss, and Q-table update flag.
- On failure, logs a warning (`Muad'Dib telemetry/self-play fail`) rather than silently passing.

Cadence env knobs:
- `MUADIB_SELF_PLAY_ENABLED` (default `1`)
- `MUADIB_SELF_PLAY_INTERVAL_CYCLES` (default `32`, min `4`)
- `MUADIB_SELF_PLAY_EPISODES` (default `4`)
- `MUADIB_SELF_PLAY_MAX_STEPS` (default `3`)
- `MUADIB_SELF_PLAY_PROMOTE` (default `0`; archive-only, explicit opt-in for active/champion evolution)
- `MUADIB_SELF_PLAY_UPDATE_QTABLE` (default `0`)

Validation performed:
- `mcp.venv/bin/python -m py_compile mcp_server.py tools/exoskeleton_tool.py muadib/muaddib.py muadib/neural_config.py` passed.
- Source boundary check confirmed `_format_tool_result` still exists with `json.dumps(payload, indent=2)` and the autonomous self-play hook is present.

---

## Current State — 2026-06-04: Muad'Dib Safetensors Self-Play Checkpoint Slice

The Muad'Dib neural substrate now has a safetensors-first self-play/checkpoint path without changing `mcp_server.py` output adapter semantics.

What changed:
- Added `SelfPlayConfig` and `MuadDibSelfPlayHead` to `muadib/neural_config.py`; this is a compact policy/value head for bounded self-play over tool IDs.
- Updated `muadib/muaddib.py` so tokenizer checkpoints prefer `checkpoint_vN.safetensors`; existing `checkpoint_vN.pt` files remain load-only migration fallback.
- Added `bb7_dt_self_play` and `bb7_dt_checkpoint_status` to the DigitalTwinTool surface and exposed exoskeleton wrappers using the already-loaded live tool catalog.
- Updated `tool_manifest.json` and `requirements.txt` (`safetensors`).

Critical invariant:
- JSON is metadata/ledger only. Neural tensor weights are `.safetensors`. Continuous self-play trains a candidate copy, writes a complete safetensors checkpoint atomically, then promotes the active head pointer/reference. It does not mutate live weights in-place.
- Synthetic self-play does **not** update the real Q-table by default (`update_qtable=false`) to protect months of real operator/tool observations.
- `mcp_server.py` was intentionally not modified; raw JSON remains preserved until the existing display/content-block boundary.

Validation performed in `mcp.venv`:
- `python -m py_compile muadib/neural_config.py muadib/muaddib.py muadib/__init__.py tools/exoskeleton_tool.py` passed.
- `python -m json.tool tool_manifest.json` passed.
- Temp-root `DigitalTwinTool.bb7_dt_self_play(...)` produced/promoted `self_play_head_v1.safetensors` and left Q-table updates disabled by default.
- Temp-root tokenizer encode/save produced active `checkpoint_v1.safetensors`.
- Temp-root `ExoskeletonTool.bb7_dt_self_play(...)` wrapper worked and `get_tools()` includes `bb7_dt_self_play` + `bb7_dt_checkpoint_status`.

---

## Current State — 2026-06-03: Production-Grade Robustness Audit and Fixes

A comprehensive production-grade robustness audit was performed, and all discovered issues were resolved:
- **Syntax Errors Fixed**: Misplaced code in `tools/lisan_al_gaib.py` (which had disabled neural/lisan subsystems on startup) and casing typos in `muadib/memory_attention_classes.py` were corrected, achieving 100% syntax compliance.
- **Resource Leaks Purged**: Added a startup cleanup routine in `mcp_server.py` that scans the canonical `data/` directory and unlinks stray `*.tmp` files from aborted runs, reclaiming over 100MB of disk space.
- **Unclosed Database Connections**: Hardened shutdown lifecycle in `mcp_server.py` by cleanly closing the SQLite3 distillation database connection (`self._distillation_conn`).
- **Fail LOUD Exceptions**: Upgraded silent `except Exception: pass` blocks in the core autonomous loop of `mcp_server.py` and optional module imports/persist routines in `tools/exoskeleton_tool.py` to log warnings/debug messages, preserving the "fail LOUD" doctrine.
- **Codex History Ingestion Spec**: Updated `MCP_SPEC.md` to document that rollout/conversation history is ingested from the operator's global plane (`/home/daeron/.codex/history.jsonl`) rather than local project boundaries.

---

## Previous State — 2026-06-03: System-wide Tool and Spec Documentation Complete

The codebase-wide tool documentation has been successfully completed in the live workspace doctrine (`workflows-new.md`) and specification (`MCP_SPEC.md`):
- Detailed coverage added to `workflows-new.md` for `tools/auto_tool_module.py` (all 10 tools, including `bb7_workspace_context_loader`, `bb7_auto_session_resume`, `bb7_show_available_capabilities`, `bb7_intelligent_tool_guide`, and optimization tools).
- Added detailed descriptions for `tools/file_tool.py` (all 12 tools, including `bb7_read_file`, `bb7_write_file`, `bb7_copy_file`, `bb7_move_file`, `bb7_delete_file`, etc.) in both `workflows-new.md` and `MCP_SPEC.md` along with complete parameter specs.
- Added detailed descriptions and parameter specifications for `tools/meta_intelligence_engine.py` (`bb7_code_consciousness`, `bb7_context_weaver`, `bb7_creative_problem_solver`) in both `workflows-new.md` and `MCP_SPEC.md`.
- Documented `tools/openrouter_planner_tool.py` (3 tools) and `tools/openrouter_agent_tool.py` (9 tools) under section 1.4 in `workflows-new.md` to match their active specifications.
- Added detailed descriptions and complete parameter specifications for `tools/thought_journal_tool.py` (all 11 tools) in both `workflows-new.md` and `MCP_SPEC.md`.
- User confirmed that the core capability, memory, and facade engines (`memory_tool.py`, `memory_interconnect.py`, `web_tool.py`, `enhanced_web_tool.py`, `visual_tool.py`, `auto_tool_module.py`, and `meta_intelligence_engine.py`) are successfully wired up and logging in the live runtime.

---

## Current State — 2026-05-27: Neural Substrate Migration Doctrine Lock

Somnus-MCP is not a passive MCP server/tool harness. It is a 24/7 autonomous neural-symbolic cognition server. MCP JSON-RPC2, stdio, SSE, HTTPS, and webhook endpoints are transport surfaces into the single live BB7/Lisan/Muad'Dib plane.

Runtime invariants:
- canonical data root: `/home/daeron/Somnus-MCP/data`;
- canonical Python environment: `/home/daeron/Somnus-MCP/mcp.venv`;
- source/schema validation uses `mcp.venv/bin/python`;
- no `.venv` assumption and no per-project BB7 data silos;
- `tools/memory_tool.py`, `tools/memory_interconnect.py`, and `tools/session_manager_tool.py` are continuity substrate, not auxiliary helper tools;
- live runtime truth is queried through the existing BB7/SovereignMCP plane, not by instantiating a parallel `MCPServer()`.

Migration state this session:
- `tools/file_tool.py` was promoted to the advanced `FileTool` surface with compatibility aliases/shims retained: `bb7_append_file`, `bb7_get_file_info`, `bb7_file_cache_stats`, legacy `pattern` support, and raw `bb7_read_file` by default. New surfaces are `bb7_copy_file`, `bb7_move_file`, `bb7_delete_file`, `bb7_file_info`, and `bb7_operation_history`.
- `golden_paths.json` now contains executable workflow entries only. Extracted audit/history metadata lives in `golden_paths_meta.json`. Lisan and exoskeleton now filter metadata/malformed entries before spectral indexing, chain-prior seeding, matching, and auto-promotion.
- `tools/meta_intelligence_engine.py` is integrated as a registry-bound facade, not a second tool container. It exposes `bb7_code_consciousness`, `bb7_context_weaver`, and `bb7_creative_problem_solver` and attaches to the live registry via `mcp_server.py`.
- `TRASH/MAYBE-TOOLS/intelligent_automation_tool.py` was not copied because `tools/auto_tool_module.py` already owns that optimization surface. `TRASH/MAYBE-TOOLS/ai_system_integration.py` remains blocked by Windows-only imports and unsafe eager initialization.
- `tool_manifest.json`, `MCP_SPEC.md`, `ARCHITECTURE.md`, `ARCHITECTURE_MAP.md`, `MEMORY.md`, and the filetree map were updated to the memory-continuity doctrine.

Historical note: entries below preserve chronology and may contain superseded Windows paths, old tool counts, mandatory-loop language, or stale module status. For current work, prefer this top section, `AGENTS.md`, `MCP_SPEC.md`, `ARCHITECTURE.md`, `ARCHITECTURE_MAP.md`, and live health.

---

## Current State — 2026-05-22: Server Active Externally, Repository De-initialized & Documentation Updated

**Active External Server Running** — The secure HTTPS server is currently running in the background at `https://0.0.0.0:8443` inside the `mcp.venv` virtual environment (running with `--external --host 0.0.0.0` to permit tunnel proxy requests from external services like ChatGPT/Grok).

**Repository de-initialized from Git control** — Removed the `.git` directory from `/home/daeron/Somnus-MCP` to prevent accidental secret leakage from this working directory.

**Tunnel Vision Prevention Doctrine integrated into `AGENTS.md`** — Added guidelines requiring a zoom-in/zoom-out reading cycle (read file -> zoom out to map context -> re-zoom back) using `5-22-2026-muaddib-mcp-filetree.md` to maintain structural context and avoid tunnel vision.

**Exposing Secure HTTPS Wrapper Guide Added** — Created a comprehensive setup manual in `docs/expose_mcp_to_internet.md` detailing how to securely expose the local HTTPS server to external services (ChatGPT Actions, Grok, etc.) using `ngrok` or Cloudflare Tunnels (incorporating parameters like `--external` and bypassing local SSL verification).

---

## Previous State — 2026-05-09: HTTPS Universal Integration Layer + MCP Streamable HTTP

**Extended `https_wrapper.py` into a universal integration gateway** — ChatGPT Actions, Claude Desktop, webhooks, SSE events.

**New files:**
- `webhook_engine.py` (310 lines) — HMAC-SHA256 signed outbound webhooks, exponential backoff (1s/4s/16s), dead-letter persistence to `data/security/webhook_dead_letters.jsonl`, thread-safe registration to `data/security/webhooks.json`
- `sse_broadcaster.py` (200 lines) — Thread-safe SSE broadcaster with per-client queues, heartbeat keep-alive (30s default), dead client reaping, streaming generators for both stdlib and FastAPI
- `openapi_builder.py` (275 lines) — Dynamic OpenAPI 3.1 spec from live `mcp_server.tools` dict (120 tools → 127 paths), ChatGPT `ai-plugin.json` manifest, Claude Desktop `mcpServers` config generator

**Extended files (additive only, zero rewrites):**
- `https_wrapper.py` — 8 new endpoints: `/.well-known/ai-plugin.json`, `GET /events` (SSE), `GET /mcp` (Streamable HTTP SSE), `GET /webhooks`, `GET /claude-config`, `POST /webhooks/register`, `POST /webhooks/unregister`. External cert support (`MCP_EXTERNAL_CERT`/`MCP_EXTERNAL_KEY` env vars). Static OpenAPI replaced with dynamic `build_openapi_spec()`. Webhook/SSE engines wired into handler factory.
- `mcp_api.py` — SSE streaming via `GET /mcp/stream` (FastAPI StreamingResponse), `Mcp-Session-Id` header on `/rpc` responses, dynamic OpenAPI at `/openapi-live.json`, ChatGPT manifest at `/.well-known/ai-plugin.json`
- `config_manager.py` — New `IntegrationConfig` dataclass: webhook settings, SSE heartbeat, ChatGPT plugin metadata, MCP Streamable HTTP toggle, external cert paths, CORS. Env var overrides: `MCP_EXTERNAL_CERT`, `MCP_EXTERNAL_KEY`, `MCP_ENABLE_WEBHOOKS`, `MCP_ENABLE_SSE`.

**NOT touched:** `mcp_server.py`, `muadib/*`, `tools/*`

**Verified endpoints (live server, all 200):**
- `GET /health` → ok
- `GET /.well-known/ai-plugin.json` → name=sovereign_mcp
- `GET /openapi.json` → 127 paths, OpenAPI 3.1.0
- `GET /claude-config` → mcpServers config
- `POST /webhooks/register` → webhook registered
- `GET /webhooks` → 1 webhook listed
- `POST /mcp tools/list` → 120 tools

**Env:** `mcp.venv` at `/home/daeron/Somnus-MCP/mcp.venv` — torch 2.11.0+cpu, Python 3.12.3, Linux.

---



**Doctrine transition: Mandatory Turbo Loop → Golden Path 3-Anchor Model**

The rigid 11-step mandatory per-turn exoskeleton loop has been replaced across all control-plane documents:
- `AGENTS.override.md` (global): 3-anchor model (Know Where You Are, Walk the Path, Remember What Matters)
- `AGENTS.md` (Somnus-MCP root): Updated to Golden Path section
- `.codex/AGENTS.md`: Surgical edits — workflow tables removed, exo loop reframed as tool-plane inhabitation
- `workflows.md` (global): Turbo Loop → Golden Path anchors, anti-collapse guardrail #5 added (no ritual calls)
- `AGENTS.runtime.md`: Regenerated from updated sources
- `MEMORY.md`
- `CONTEXT.md`

**Telemetry-driven findings (from 3,421 plan executions):**
- The old sync ritual consumed 28% of all tool calls (bootstrap→categories→route, every turn)
- `bb7_exo_reflect` was called only 3 times (0.04%) — Codex was performing ceremony but skipping the learning step
- 96.3% of all invocations were bb7_ tools vs 3.7% native Codex tools
- 1,087 calls to deprecated journal tools despite workflows.md deprecation notice
- `bb7_run_command` (shell) dominated at 16.4% — path of least resistance

**Codex Distillation Pipeline (NEW):**
- `scripts/codex_distill_formatter.py` — converts `.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` into Somnus trajectory format
- Purpose: seed base dataset from Codex cognitive trajectories for tool-routing behavior (not coding ability)
- Output: `data/distillation/codex_trajectories_YYYY-MM-DD.jsonl` (10 files, 25 trajectories, 2,562 BB7 steps)
- Schema matches existing `data/distillation/` format for RFT pipeline compatibility

**Files changed:**
- `AGENTS.md` (Somnus root) — Golden Path section replaces Mandatory Turn Loop
- `.codex/AGENTS.md` — Workflow tables removed, exo loop reframed, Quick Reference updated
- `scripts/codex_distill_formatter.py` — NEW: Codex rollout → Somnus trajectory formatter

**Data filetree reference:** `data/5-7-filetree-mcp-datadir.md`

**Env:** `mcp.venv` at `/home/daeron/Somnus-MCP/mcp.venv` — torch 2.11.0+cpu, Python 3.12.3, Linux.

---

## Previous State — 2026-05-05: HTTPS Wrapper DARPA-GRADE + 27/27 E2E PASS

**`https_wrapper.py` production audit: 27/27 PASS, 0 FAIL**

Fixes applied (was non-functional, now fully operational):
- **SSL cert crash**: `x509.IPAddress("127.0.0.1")` → `x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))` — was crashing on every startup
- **Dead method calls**: `MCPServer.call_tool()`, `get_server_info()`, `health_check()`, `get_tool_info()` did not exist. Rewired all endpoints to use `handle_request()` and `handle_call_tool()` via proper JSON-RPC dispatch
- **Phantom import**: `from mcp_server import handle_jsonrpc_request` did not exist. Replaced with `self.mcp_server.handle_request()`
- **Bare excepts**: All `except:` changed to `except OSError as e:` with logging
- **External access mode**: Added `--external` flag + `allow_external` parameter. Enables Custom GPT / Claude plugin / Codex agent connections from non-localhost origins
- **CORS**: Dynamic origin header based on access mode (`*` for external, `https://localhost` for local)
- **Missing dep**: Added `cryptography` to `requirements.txt` (installed in mcp.venv)

**Verified endpoints** (HTTPS, TLS 1.2+, 2048-bit RSA cert, API key auth):
- `GET /` — server info (120 tools, external_access flag)
- `GET /tools` — full tool catalog via JSON-RPC tools/list relay (120 tools)
- `GET /health` — status: ok
- `GET /metrics` — performance counters + security metrics
- `GET /api-info` — 7 documented endpoints
- `POST /mcp` — JSON-RPC 2.0 gateway (tools/list + tools/call verified)
- `POST /tools/{name}` — direct tool invocation via handle_call_tool

**Usage modes:**
- Local (default): `python https_wrapper.py` → localhost:8443, API key auth
- External: `python https_wrapper.py --external --host 0.0.0.0` → Custom GPTs, Claude plugins, Codex agents
- FastAPI alternative: `mcp_api.py` (uvicorn, separate tool registry)

---



**DARPA-Grade Production Audit: 62/62 PASS, 0 FAIL**

Full lifecycle verified in `mcp.venv` (Python 3.12.3, torch 2.11.0+cpu):
- 120 tools registered across 13 modules
- Muad'Dib twin: 652 observations, 326 states, 340 Q-entries, 123/4096 vocab, 3 neural checkpoints (47MB each)
- Q-table convergence: 339/339 entries have non-zero learned values
- Exoskeleton: 154 tool priors, 330 chain priors, 6 discovered macros
- Distillation: 1,760 trajectories across 8 daily shards + index + high-value/failure buckets
- Hooks: 8 hooks across 5 events (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop)
- Codex overlay: `_feed_codex_tool_to_twin()` wired at `mcp_tool_call_end` (success) and `function_call_output` (error detection)
- `~/.codex/history.jsonl`: 5,507 records (6.5MB) feeding Q-table in real time

**New files this session:**
- `intelligent_output_hook.py` — PostToolUse hook: cleans JSON output, injects muadib neural context via `systemMessage`
- `hooks_manifest.json` updated — `sovereign-intelligence/intelligent_output_cleaner` added to PostToolUse array

**`mcp_server.py` changes:**
- `_feed_codex_tool_to_twin()` bridge method added (line ~1397): resolves twin from exoskeleton, infers category from catalog, parses codex duration formats, calls `bb7_dt_observe()`
- `_process_codex_rollout_records()`: `mcp_tool_call_end` events now feed twin (success path); `function_call_output` feeds twin on error detection (Traceback/Exception/Error: patterns)
- `_last_fc_tool` tracker variable pairs function_call with its output for error attribution

**`requirements.txt` updated:** added `httpx`, `pyyaml`, `torch` (were installed in venv but undeclared)

**Env:** `mcp.venv` at `/home/daeron/Somnus-MCP/mcp.venv` — torch 2.11.0+cpu, Python 3.12.3, Linux.

---



## Previous State — 2026-05-23: Muad'Dib Neural Substrate Wiring Complete

**Muad'Dib Neural Substrate — All 8 Wiring Gaps Closed:**

The neural-symbolic routing transition is complete. `bb7_exo_plan` and `bb7_exo_route` now run full neural-MCTS hybrid scoring on every call. Server init log confirms:

```
ExoskeletonTool ready: 110 indexed tools, 34 golden paths, neural_twin=active, subsystems=[mcts,thompson,session_momentum_v3]
```

**Files changed:**
- `muadib/tool_modality.py` — `MemorySystem`, `EnhancedRSLMemorySystem`, `ReasoningMode` stubs added to `except ImportError` fallback (Gap #1)
- `muadib/muaddib.py` — `bb7_dt_encode_catalog(List[str], Optional[Dict])` added with transparent chunking for catalogs > `max_seq_len`; registered in `get_tools()` (Gaps #2, #3)
- `tools/exoskeleton_tool.py` — 6 targeted edits:
  - Imported `_MCTSPlanner`, `_ThompsonContextualBandit`, `SessionMomentum` from lisan (Gap #5, #7, #8)
  - `_cached_neural_attention`, `_mcts_planner`, `_thompson_bandit`, `_session_momentum` initialized in `__init__` with post-init spectral refresh (Gaps #4, #5, #7, #8)
  - `_refresh_spectral_catalog` rewired to `bb7_dt_encode_catalog`, per-category attention weights computed and injected into decomposer + manifold (Gaps #3, #6)
  - `_reliability_sampled()` added (Thompson Beta draw + neural Q-bonus); wired into `_score_tools` (Gap #7)
  - `_update_session_momentum` + `_compute_momentum_bonus` delegate to `SessionMomentum` V3 (Gap #8)
  - `_value_fn` in MCTS block fixed; MCTS output normalized to full plan schema (Gap #3 extension)

**Live verification (mcp.venv):**
- 110/110 tools encoded in 2 chunks, 512-dim embeddings
- 11 categories in `_cached_neural_attention` + manifold weights
- `_mcts_planner` type: `_MCTSPlanner`, `_thompson_bandit` type: `_ThompsonContextualBandit`
- `bb7_exo_plan` returns `mcts=True`, `tree_reward`, `adversarial_survived`, `plan_id: mcts_*`
- Phase 1 smoke test: `PASSED`

**Critical implementation pattern discovered:**
`_refresh_spectral_catalog()` is called during `_load_catalog()` (early init) before `_digital_twin` and `_session_momentum` exist. Fix: add a second `_refresh_spectral_catalog()` call at the very end of `__init__` after all subsystems are initialized. This pattern applies to any future subsystem that depends on late-initialized attributes.

**Env:** `mcp.venv` at `/home/daeron/Somnus-MCP/mcp.venv` — torch 2.11.0+cpu, Python 3.12.3.

---

## Previous State — 2026-04-15: Hook Bridge Optimization

**Hook Bridge Integration (LIVE):**

- Created `hooks_manifest.json` — unified registry of all Claude Code plugin hooks (hookify, ralph-loop, security-guidance, explanatory-output-style)
- Created `hook_executor.py` — JSON-based hook executor with CLI + library interface
- Updated `settings.json` to pass `SOVEREIGN_HOOKS_MANIFEST` + `SOVEREIGN_AUTO_HOOK_TRIGGER` to MCP server
- Hooks now discoverable + auto-triggerable without shell/RPC indirection
- Integration model: **State machine (exo_bootstrap → domino chain) → hooks as first-class events**

**Architecture:**

- `hooks_manifest.json` defines all hooks + auto-trigger rules (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop)
- `hook_executor.py` provides: (a) CLI for manual execution, (b) library for MCP integration, (c) dry-run + introspection
- `hooksIntegration` section in settings.json enables sync between Claude Code + MCP server
- Documentation: `HOOK_BRIDGE.md` explains flow, domino chain integration, environment improvements

**Validation:**

- `hook_executor.py --list` → lists all hooks by event type ✓
- `hook_executor.py --list-events` → lists available events ✓
- `hook_executor.py PreToolUse --dry-run` → shows what would execute ✓
- Hook executor ready for integration as bb7_tool in mcp_server.py

---

## Previous State

- Kimi MCP config at `C:/Users/treyr/.kimi/mcp.json` cleaned to remove UTF-8 BOM so CLI can parse JSON.
- MCP server now normalizes JSON-RPC response IDs to non-null strings/ints (fallback `0`) to satisfy Kimi's client validator.
- MCP server now formats tool responses into MCP-compliant `content` blocks via `_format_tool_result`, so tools return data Kimi accepts.
- Memory tool lambdas updated to accept `key`/`value` args as defined in the manifest.
- Visual tool MSS capture now converts BGRA frames safely (avoids BGRX decoder errors).
- RestrictedPython compilation in code analysis tool now handles missing `errors` attribute safely.
- RestrictedPython compilation now handles both CompileResult and direct code object returns to avoid `'code' object has no attribute 'code'`.
- `bb7_python_execute_secure` smoke test passed; report at `mcp/logs/smoke_bb7_python_execute_secure_20260108_184724.md`, manifest at `mcp/logs/smoke_bb7_python_execute_secure_20260108_184724.json`.
- FastAPI layer now exposes `/rpc` JSON-RPC endpoint that forwards to in-process `MCPServer` with auth middleware; supports HTTPS when cert/key provided.

## Open Items

- Rerun `kimi` tool calls to verify `content` responses fix validation errors; confirm screenshot capture succeeds after BGRA conversion.
- Run a full MCP tool smoke sweep in small batches; current harness shows intermittent 60s timeouts and occasional aborted calls (see `mcp/logs/mcp_tools_smoke_2026-01-09.md`).

## Update 2026-02-09 (Async Web Tools + Mixed Invocation Compatibility)

- `tools/web_tool.py` was refactored from sync `urllib` calls to async `aiohttp` methods (`fetch_url`, `download_file`, `check_url_status`, `search_web`, `extract_links`).
- Web tool now creates `aiohttp.ClientSession` lazily via `_get_session()` and uses explicit `aiohttp.ClientTimeout(total=...)` objects (not raw int timeout values).
- `mcp_server.py` tool invocation path now supports both:
  - legacy kwargs tools: `fn(**arguments)` based on `parameters`
  - newer dict-style tools: `fn(arguments)` based on `inputSchema`
  - plus awaitable return values and coroutine functions in both paths.
- `mcp_server.py` adds `_run_coroutine_sync()` and `_invoke_tool_callable()` to safely execute async tools from the existing sync call path.
- `mcp_server.py` `shutdown()` now closes async tool resources (including `aiohttp` sessions) by calling module `close()` methods and awaiting when needed.
- `tests/comprehensive_tool_validation.py` `run_tool()` now handles async tool functions/results and resolves missing `bb7_` prefixes for compatibility.
- `requirements.txt` now includes `aiohttp`.

## Validation 2026-02-09

- Syntax check passed:
  - `mcp_server.py`
  - `tools/web_tool.py`
  - `tests/comprehensive_tool_validation.py`
- Runtime validation passed after installing `aiohttp` into `mcp.venv`:
  - `tools/call` for `bb7_check_url_status` returns MCP `result.content` (no coroutine leak).
  - `tools/call` for `bb7_read_file` still works, confirming mixed sync/async compatibility.
  - `ToolValidator.run_tool("check_url_status", "https://example.com")` returns executed string output (not coroutine object).

## Update 2026-02-09 (Event Loop Closed Regression Fix)

- External reproduction found repeated web calls failing with `Event loop is closed` after initial success.
- Root cause: per-call `asyncio.run(...)` loop churn combined with cached `aiohttp.ClientSession` bound to the first loop.
- `mcp_server.py` now maintains a shared background async event loop for all coroutine tool execution:
  - `_async_loop_worker`
  - `_ensure_async_loop`
  - `_stop_async_loop`
  - `_run_coroutine_sync` now uses `asyncio.run_coroutine_threadsafe(...)`.
- `mcp_server.py` shutdown now stops the shared async loop after closing tool resources.
- `tools/web_tool.py` now discards cached sessions when loop mismatch/closure is detected in `_get_session` to avoid reusing invalid session-loop bindings.
- Revalidated sequence (`check_url_status -> fetch_url -> search_web -> download_file -> check_url_status`) through `tools/call`: all calls returned results, no `Event loop is closed`.
- Regression validation report saved to:
  - `mcp/logs/event_loop_closed_fix_validation_20260209_1536.md`
  - `mcp/logs/event_loop_closed_fix_validation_20260209_1536.json`

## Update 2026-02-09 (Quick Live Retry in Active Codex Session)

- Retest executed in `C:/Users/treyr/mcp` against current MCP process used by this client.
- `ping_server` returned healthy (`status=alive`, `tool_count=71`), but web calls still failed with `Event loop is closed`:
  - `bb7_check_url_status("https://example.com")`
  - `bb7_fetch_url("https://example.com")`
  - `bb7_search_web("OpenAI")`
- `bb7_extract_links("https://example.com")` returned `No links found...` instead of surfacing the upstream fetch/runtime failure.
- Native network baseline still works (`Invoke-WebRequest https://example.com` -> `200`), so this is MCP async runtime/session-state specific.
- Immediate debugging note:
  - `extract_links` currently masks `fetch_url` errors that begin with `Error fetching ...` because it only checks for `Error:` / `HTTP Error` prefixes.

## Update 2026-02-09 (Why Only a Subset of Tools Get Used)

- Runtime diagnosis shows a transport/runtime mismatch between declared tool manifest and live MCP transport behavior:
  - `tool_manifest.json` advertises 73 tools.
  - In-process server loads 71 tools in current branch.
  - MCP wrapper calls from this Codex session showed mixed behavior:
    - Some tools worked (`bb7_get_system_info`, `bb7_terminal_status`).
    - Several failed with positional-arg errors (`ping_server`, `bb7_memory_stats`, `bb7_memory_store`, `bb7_memory_retrieve`, `bb7_auto_memory_stats`), indicating old dict-positional dispatch semantics on the live transport.
- Process inspection showed multiple concurrent `mcp_server.py` Python processes from different start times/executables, which can leave clients pinned to stale dispatcher behavior.
- During cleanup, all Python `mcp_server.py` processes were terminated; this closed the MCP wrapper transport for the current Codex session (`Transport closed`), meaning session-level MCP wrappers require client/server reinitialization.

## Practical Remediation

- Restart MCP clients (Codex host session, VS Code MCP client, Kimi MCP client) so they reconnect to a single fresh server process using `C:/Users/treyr/mcp/mcp.venv/Scripts/python.exe C:/Users/treyr/mcp/mcp_server.py`.
- Ensure only one active `mcp_server.py` process per client transport.
- Re-run a small health matrix after restart:
  - `ping_server`
  - `bb7_memory_stats`
  - `bb7_memory_store`
  - `bb7_memory_retrieve`
  - `bb7_get_system_info`
  - `bb7_terminal_status`
- If positional-arg failures persist after restart, the live transport is still running old dispatcher code and must be re-bound to this workspace file version.

## Update 2026-02-10 (Tool Manifest Synced to 75 Tools)

- `tool_manifest.json` was updated to match the server's live registered tool inventory (75 tools).
- Added 5 previously missing tool definitions:
  - `bb7_auto_session_resume`
  - `bb7_intelligent_tool_guide`
  - `bb7_show_available_capabilities`
  - `bb7_workspace_context_loader`
  - `ping_server`
- Verification performed by loading `MCPServer()` and diffing server tool names against `tool_manifest.json`.
- Validation result:
  - `manifest_count = 75`
  - `server_count = 75`
  - `missing_in_manifest = []`
  - `extra_in_manifest = []`
- Outcome: manifest and runtime are now aligned for the full 75-tool surface area.

## Update 2026-02-10 (Exoskeleton V1 Implemented + Validated)

1. The `bb7_exo_bootstrap` process validates the underlying `mcp_server.py` registry to detect divergence.
2. The `tools/lisan_al_gaib.py` orchestrator parses intent, matches against golden paths, checks neural Q-bonuses, and scores tools using a blended manifold (Semantic + Spectral + Neural Embedding + Composable + Neural Value).
3. The `bb7_exo_plan` method delegates to `_MCTSPlanner`, simulating rollout chains informed by both empirical reliability and the Muad'Dib neural value-head.
4. The `bb7_exo_reflect` endpoint receives the outcome, propagates it to the twin's Q-table, updates session momentum (injecting neural attention), and commits MCTS signals to the cognitive journal.

- Added new module `tools/exoskeleton_tool.py` with 7 control-plane tools:
  - `bb7_exo_bootstrap`
  - `bb7_exo_list_tool_categories`
  - `bb7_exo_category_specific_tools`
  - `bb7_exo_route`
  - `bb7_exo_plan`
  - `bb7_exo_reflect`
  - `bb7_exo_state`
- Registered `('exoskeleton_tool', 'ExoskeletonTool')` in `mcp_server.py` and added:

3. **Neural-Symbolic Substrate (Muad'Dib Phase 1)**
   - The Muad'Dib neural substrate (`muaddib.py`) is now surgically wired into Lisan al-Gaib.
   - **Embeddings:** Neural embeddings are cached in `_SpectralIntentDecomposer` and blended (30%) with spectral similarity during routing.
   - **Priors:** The Digital Twin's Q-table bonuses explicitly condition the Thompson Contextual Bandit's $\alpha$ prior.
   - **Momentum:** Neural attention weights from the KG-enhanced layer are injected into the Topological Momentum Manifold.
   - **Rollout:** MCTS planning (`_MCTSPlanner`) now utilizes a neural value function closure (blended 30% with geometric reliability) during tree simulation.
   - **Telemetry:** The `_autonomous_exo_cycle_loop` logs twin status every 4 cycles and persists checkpoints every 16 cycles.
   - All neural injections feature graceful pure-Python fallback when `torch` is absent or the tensor logic throws. 

- Added server metadata.
- Added exoskeleton tool definitions to `tool_manifest.json` and documented them in `README.md`.
- Added non-pytest validator `tests/validate_exoskeleton_v1.py` that:
  - runs bootstrap/route/plan/reflect/state end-to-end
  - verifies server registration for all exoskeleton tools
  - verifies manifest-server tool parity
  - writes both markdown and JSON validation artifacts under `logs/`
- Validation run passed fully:
  - report: `logs/exoskeleton_v1_validation_20260210_050020.md`
  - manifest/log: `logs/exoskeleton_v1_validation_20260210_050020.json`
- Current live parity snapshot during validation:
  - `manifest_count = 82`
  - `server_count = 82`
  - `missing_in_manifest = []`
  - `extra_in_manifest = []`

## Update 2026-02-10 (Visual Tool Reliability + Test Alignment Fix)

- Root cause identified for visual failures:
  - `bb7_window_info` on Windows failed with `module 'win32gui' has no attribute 'IsZoomed'`.
  - Visual validation scripts were still testing removed/legacy visual tool names (`bb7_screen_capture`, `bb7_window_manager`, `bb7_active_window`, etc.).
- `tools/visual_tool.py` updates:
  - Hardened window state detection in `_get_windows_window_info`:
    - uses `win32gui.IsIconic` for minimized state
    - uses `IsZoomed` when available
    - falls back to `GetWindowPlacement` + `SW_MAXIMIZE/SW_SHOWMAXIMIZED`
    - defaults safely to `Normal` on inspection errors
  - Fixed standalone test block (`__main__`) to call sync methods directly (removed incorrect `await` usage).
  - Added safe print behavior in standalone mode for Windows consoles that cannot render emoji/unicode.
- Test updates for current visual API:
  - `tests/visual_tools_test.py` now validates:
    - `bb7_take_screenshot`
    - `bb7_window_info`
    - `bb7_find_on_screen`
    - `bb7_click_element`
    - `bb7_screen_monitor`
  - `tests/comprehensive_tool_validation.py` visual section updated to same tool set and low-risk args.
  - `tests/comprehensive_validation.py` visual tool inventory and runtime test path updated to current MCP call style.
- Validation results:
  - `python tests/visual_tools_test.py` passed `5/5`.
  - Direct `handle_call_tool` probes confirmed:
    - `bb7_window_info` now returns normal window report (no `IsZoomed` crash).
    - screenshot/monitor/find/click behavior all execute.
  - Non-pytest validation artifacts generated:
    - `logs/visual_tool_fix_validation_20260210_095220.md`
    - `logs/visual_tool_fix_validation_20260210_095220.json`

## Update 2026-02-10 (Full 82-Tool Exo Sweep + Reliability Fixes)

- Updated `tools/web_tool.py` reliability in async paths:
  - Added `_looks_like_error_payload()` to normalize/propagate upstream textual failures.
  - Hardened `bb7_search_web` with:
    - query validation,
    - bounded `num_results`,
    - explicit HTTP status handling,
    - non-JSON fallback response (DuckDuckGo sometimes returns empty/non-JSON payloads).
  - Updated `bb7_extract_links` to:
    - treat all upstream fetch errors consistently (not just `Error:`/`HTTP Error`),
    - use `urllib.parse.urljoin(...)` for robust relative URL resolution.
- Updated `tools/visual_tool.py` screenshot analysis output safety:
  - `bb7_take_screenshot` now guards missing analysis keys (`colors`, `brightness`, `complexity`, `text_regions`) and emits analysis notes instead of raising key errors.
- Updated `tools/vscode_terminal_tool.py` terminal robustness:
  - Fixed real bug in `bb7_terminal_cd` where `project_info` could be referenced before assignment when `analyze_context=False`.
  - Hardened PATH handling:
    - `_analyze_path_environment` now distinguishes invalid PATH entries vs entries that exist but are not directories.
    - `_find_similar_commands` now scans only valid PATH directories and catches `NotADirectoryError`/`OSError`.
    - `_find_command_alternatives` now uses cross-platform path candidates (including Windows `System32`/`SysWOW64`) with dedupe and executable-suffix handling.
  - Added missing `re` import used by `_get_command_version`.
  - Fixed standalone `__main__` test path to call sync methods directly (removed incorrect async `await` usage).
- Updated Exoskeleton validator compatibility:
  - `tests/validate_exoskeleton_v1.py` now supports dict-returning Exo methods directly and still accepts legacy JSON-string payloads.
- Added new full non-pytest sweep validator:
  - `tests/validate_all_tools_exo_sweep.py`
  - Runs Exo preflight (`bb7_exo_bootstrap`/`route`/`plan`) and full `tools/call` sweep for all registered tools.
  - Emits terminal detail + markdown + JSON artifacts.
- Validation results:
  - `python tests/validate_exoskeleton_v1.py` passed.
    - `logs/exoskeleton_v1_validation_20260210_100639.md`
    - `logs/exoskeleton_v1_validation_20260210_100639.json`
  - `python tests/validate_all_tools_exo_sweep.py` passed with `82/82`.
    - `logs/all_tools_exo_sweep_20260210_100816.md`
    - `logs/all_tools_exo_sweep_20260210_100816.json`
- Manifest parity rechecked post-fix:
  - `server_count = 82`
  - `manifest_count = 82`
  - `missing_in_manifest = []`
  - `extra_in_manifest = []`

## Update 2026-02-10 (Standalone Advanced AI Shell Native Tool Bridge)

- Goal:
  - Enable `advanced_ai_shell.py` to call `mcp/tools/*.py` directly without MCP server transport.
  - Support standalone execution so tool routing works even when MCP wrapper transport is unavailable.
- Core implementation in `advanced_ai_shell.py`:
  - Added native bridge settings in `AIShellSettings`:
    - `enable_native_tools`
    - `native_tools_dir`
    - `native_tool_prefix`
  - Added `NativeToolBridge` for:
    - tools directory resolution (`AI_SHELL_NATIVE_TOOLS_DIR`, configured path, local defaults)
    - dynamic module import and class/module tool extraction
    - support for both tool map shapes:
      - direct callable values
      - metadata dict values with `"function"` callable
    - mixed invocation fallbacks:
      - `fn(**kwargs)`
      - `fn(arguments_dict)`
      - `fn()`
    - async and sync callable execution
    - close lifecycle for tool instances exposing `close()`
  - Integrated bridge into `AdvancedAIShell`:
    - `initialize_native_tools()`
    - `list_native_tools(prefix=None)`
    - `call_native_tool(tool_name, arguments)`
    - native command routing in `execute_command()`:
      - `tool list [prefix]`
      - `tool call <tool_name> [json_args]`
      - direct `bb7_*` invocation (`bb7_tool_name {"arg":"value"}`)
    - native tool commands can run even when full shell/VM init has not completed.
  - Added shutdown cleanup for native bridge and reset of initialized state.
- Standalone hardening:
  - Reworked top-level external integration imports in `advanced_ai_shell.py` to default-safe standalone mode.
  - Added fallback classes for unavailable external modules (`ArtifactManager`, Git integration, `ProjectStatus`).
  - Added opt-in external loading via `AI_SHELL_LOAD_EXTERNAL_INTEGRATIONS` to avoid cross-project import coupling in standalone mode.
- Validation:
  - Added non-pytest validator: `tests/validate_advanced_shell_native_tools.py`.
  - Validator confirms:
    - native bridge indexing
    - direct tool invocation API calls
    - command-level routing (`tool list`, `tool call`, direct `bb7_*`)
    - graceful shutdown
  - Latest run passed:
    - report: `logs/advanced_shell_native_tools_validation_20260210_110707.md`
    - manifest: `logs/advanced_shell_native_tools_validation_20260210_110707.json`
- Observed behavior:
  - One duplicate registration warning remains during indexing:
    - `bb7_memory_consolidate` duplicate from `memory_tool` vs `memory_interconnect` load order.
  - Current bridge behavior keeps first registration and logs warning.

## Update 2026-02-10 (New Custom Skill: War Room Architect)

- Created a new reusable skill scaffold using `skill-creator` tooling:
  - Skill name: `war-room-architect`
  - Path: `skills/custom/war-room-architect/`
  - Files:
    - `skills/custom/war-room-architect/SKILL.md`
    - `skills/custom/war-room-architect/agents/openai.yaml`
- `SKILL.md` now defines a strict planning-output contract with:
  - required section order
  - upgrades matrix with ROI/complexity/priority
  - explicit closing ritual requirements
  - war-room tone and formatting rules
  - prohibited output patterns
- Validation completed:
  - Command: `python C:/Users/treyr/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/treyr/mcp/skills/custom/war-room-architect`
  - Result: `Skill is valid!`

## Update 2026-02-10 (Advanced Shell Spec Synced to Current Implementation)

- Rewrote `ADVANCED_AI_SHELL_SPEC.md` to match current `advanced_ai_shell.py` behavior and API.
- Updated spec metadata to:
  - `Version: 1.1`
  - file size reference `~2548 lines`
  - `Last Updated: 2026-02-10`
- Added explicit operation-mode split:
  - standalone mode (fallback integrations)
  - opt-in integration mode via `AI_SHELL_LOAD_EXTERNAL_INTEGRATIONS`
- Added first-class documentation for `NativeToolBridge`:
  - tools directory resolution order
  - class/module indexing behavior
  - callable shape fallback order (`kwargs`, `dict`, `no-arg`)
  - duplicate-tool handling and lifecycle close behavior
- Added shell-native command routing contract under `execute_command()`:
  - `tool list [prefix]`
  - `tool call <tool_name> [json_args]`
  - direct `bb7_*` invocation
  - note that native tool commands can run before full shell initialization
- Updated settings/env var documentation to include native bridge controls:
  - `enable_native_tools`
  - `native_tools_dir`
  - `native_tool_prefix`
  - `AI_SHELL_NATIVE_TOOLS_DIR`
  - `AI_SHELL_ENABLE_NATIVE_TOOLS`
  - `AI_SHELL_NATIVE_TOOL_PREFIX`
- Added updated quick-start and usage examples for direct native tool execution paths.

## Update 2026-02-10 (Live MCP Wrapper Health Probe - Codex Session)

- User requested MCP-first verification because tool usage felt unreliable.
- Verified MCP transport from this active session using BB7 tools directly (not shell fallback):
  - `ping_server` -> `alive`, `tool_count: 82`
  - Exoskeleton control-plane calls succeeded:
    - `bb7_exo_bootstrap`
    - `bb7_exo_list_tool_categories`
    - `bb7_exo_state`
    - `bb7_exo_route`
    - `bb7_exo_plan`
    - `bb7_exo_reflect`
  - Core ops calls succeeded:
    - `bb7_memory_stats`
    - `bb7_memory_store`
    - `bb7_memory_retrieve`
    - `bb7_terminal_status`
    - `bb7_get_system_info`
    - `bb7_window_info`
  - Web sequence succeeded in order:
    - `bb7_check_url_status(https://example.com)` -> 200
    - `bb7_fetch_url(https://example.com)` -> 200 + content
    - `bb7_search_web("OpenAI")` -> graceful non-JSON fallback response (no runtime error)
    - `bb7_extract_links(https://example.com)` -> extracted IANA link
    - second `bb7_check_url_status` -> 200
- Regression check outcome:
  - No `Event loop is closed` failure reproduced in this session.
  - No positional-argument invocation failures observed in tested tools.
- New verification memories recorded:
  - `mcp_probe_2026_02_10_live`
  - `mcp_health_probe_2026_02_10_codex_session`

## Update 2026-02-10 (Full 85-Tool Sweep Re-run + Fix to 100%)

- User requested a fresh full sweep from this session.
- Executed full non-pytest validator through MCP terminal tool:
  - `tests/validate_all_tools_exo_sweep.py`
- First run result:
  - `85 tested`
  - `84 passed`
  - `1 failed` (`bb7_python_execute_secure`)
  - report: `logs/all_tools_exo_sweep_20260210_140145.md`
  - JSON: `logs/all_tools_exo_sweep_20260210_140145.json`
- Failure root cause from artifact:
  - `NameError: name '_print_' is not defined`
  - occurred in restricted execution path for `bb7_python_execute_secure`.
- Fix implemented in `tools/enhanced_code_analysis_tool.py`:
  - imported `PrintCollector` when `RestrictedPython` is available.
  - added `_FallbackPrintCollector` for fallback compatibility.
  - wired `_print_` into `restricted_globals` in both RestrictedPython and fallback modes.
  - surfaced RestrictedPython collected `printed` output into stdout buffer for consistent result formatting.
- Validation after fix:
  - re-ran `tests/validate_all_tools_exo_sweep.py`
  - `85/85 passed` (`100%`, `0` failed, `0` warnings)
  - report: `logs/all_tools_exo_sweep_20260210_140431.md`
  - JSON: `logs/all_tools_exo_sweep_20260210_140431.json`
- Note on transport state:
  - direct wrapper call to `bb7_python_execute_secure` still showed old `_print_` failure before transport/process refresh,
    while fresh sweep-instantiated server passed; this indicates active wrapper process/version drift.

## Update 2026-02-10 (Codex Runtime Introspection: Local vs Remote Control Surfaces)

- Completed local runtime introspection for installed Codex CLI to map modifiable layers and extension points.
- Confirmed execution chain:
  - `C:/Users/treyr/AppData/Roaming/npm/codex.ps1` -> Node launcher
  - `C:/Users/treyr/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js`
  - native binary `.../vendor/x86_64-pc-windows-msvc/codex/codex.exe`
- Confirmed package/runtime metadata:
  - `@openai/codex` version `0.98.0`
  - local binaries include `codex.exe`, `codex-command-runner.exe`, `codex-windows-sandbox-setup.exe`, bundled `rg.exe`.
- Confirmed local control surfaces under `C:/Users/treyr/.codex/`:
  - `config.toml` (model/features/project trust + MCP server registrations)
  - `AGENTS.md` and `AGENTS.override.md` (instruction overlays)
  - `rules/default.rules` (approval prefix rules)
  - `policy/default.codexpolicy` (policy gates)
  - `skills/` (skill-triggered instruction bundles)
- Confirmed MCP integration for this environment:
  - `codex mcp list` shows `SovereignMCP` enabled via local `pwsh` command launching `mcp_server.py` in `mcp.venv`.
- Confirmed observable prompt/session event schema from local logs:
  - session JSONL event types include `session_meta`, `turn_context`, `response_item`, `event_msg`.
  - `session_meta` includes base instructions; `turn_context` includes user instruction overlays and runtime policy fields.
- Limitation documented:
  - prompt serialization internals, UI rendering internals, and model-request orchestration are inside native `codex.exe` (not directly editable via local JS wrapper).

## Update 2026-02-10 (Session-End Capability Exploration + Session Linking)

- Ran full exoskeleton inventory and session-link pass on current MCP tool surface.
- Exo inventory snapshot:
  - `bb7_exo_bootstrap` reports `indexed_tools=82` across 11 categories.
  - categories include: `analysis`, `execution`, `exoskeleton`, `files`, `memory`, `misc`, `project_context`, `sessions`, `system`, `visual`, `web`.
- Ran category-specific exploration using:
  - `bb7_exo_category_specific_tools` for all categories.
  - `bb7_exo_route` for targeted intents (security, automation, visual, memory, session continuity, project-context analysis).
- Per-user request, executed full tool surface sweep (not just listing):
  - command: `python tests/validate_all_tools_exo_sweep.py`
  - result: `85/85 passed`, `0 failed`, `0 warnings`.
  - artifacts:
    - `logs/all_tools_exo_sweep_20260210_213933.md`
    - `logs/all_tools_exo_sweep_20260210_213933.json`
- Important discrepancy captured:
  - Exoskeleton index currently reports `82` tools while runtime sweep validates `85`.
  - Missing from exo catalog but present in sweep include:
    - `bb7_exo_briefing`
    - `bb7_exo_preemptive_recovery`
    - `bb7_exo_route_focused`
  - implication: exo catalog/index sync lag against live server registry.
- Session tools were actively used to create links and continuity:
  - started session: `3be3797a-6fba-464d-a366-4b99cadf39d6`
  - logged event, captured insight, recorded workflow, updated focus
  - stored and linked memories:
    - `tool_capability_map_2026_02_10_full_inventory`
    - `tool_surface_mismatch_2026_02_10_exo82_vs_sweep85`

## Update 2026-02-11 (Exoskeleton Full-Capability Patch)

- User requested full patch so exoskeleton reliably exposes all tools and avoids partial-capability behavior.
- Patched `tools/exoskeleton_tool.py`:
  - Added live registry provider support:
    - `attach_live_tools_provider(...)`
    - `_maybe_sync_live_tools(...)`
  - Added robust live sync internals:
    - `_required_params_from_tool_info(...)`
    - `_rebuild_idf(...)`
    - `sync_from_live_tools(...)` now updates existing entries and returns `{added, updated}`.
  - Added live-sync checks at start of all public exo APIs:
    - `bb7_exo_bootstrap`, `bb7_exo_list_tool_categories`, `bb7_exo_category_specific_tools`,
      `bb7_exo_route`, `bb7_exo_plan`, `bb7_exo_state`,
      `bb7_exo_briefing`, `bb7_exo_preemptive_recovery`, `bb7_exo_route_focused`.
  - Fixed logic bugs in phase-2 methods:
    - `bb7_exo_briefing` now reads `top_tools` and `candidate_plans` correctly.
    - `bb7_exo_preemptive_recovery` now reads `candidate_plans` correctly.
    - `bb7_exo_route_focused` now reads `top_tools` correctly.
  - Fixed `_find_alternative_tool(...)` return shape to match caller expectations (dict with name/reliability).
- Patched `mcp_server.py`:
  - Added `_sync_exoskeleton_catalog()` helper.
  - In `register_tools()`, attach live tools provider to exoskeleton and sync immediately.
  - In `handle_list_tools()`, sync exoskeleton catalog before returning tool list.
  - In `handle_call_tool()`, sync on exo-tool calls (`bb7_exo_*`) before execution.
- Expanded `tests/validate_exoskeleton_v1.py`:
  - Expected exo tool set updated from 7 to 10 tools.
  - Added runtime checks for:
    - `bb7_exo_briefing`
    - `bb7_exo_preemptive_recovery`
    - `bb7_exo_route_focused`
  - Added server parity check: `len(exo.tool_catalog) == len(server.tools)`.
- Validation results:
  - `python -m py_compile tools/exoskeleton_tool.py mcp_server.py tests/validate_exoskeleton_v1.py` passed.
  - `python tests/validate_exoskeleton_v1.py` passed.
    - report: `logs/exoskeleton_v1_validation_20260211_004137.md`
    - JSON: `logs/exoskeleton_v1_validation_20260211_004137.json`
  - `python tests/validate_all_tools_exo_sweep.py` passed (`85/85`, 100%).
    - report: `logs/all_tools_exo_sweep_20260211_004223.md`
    - JSON: `logs/all_tools_exo_sweep_20260211_004223.json`
- Operational note:
  - The currently connected MCP wrapper transport can still report old exo state (`indexed_tools=82`) until that process is restarted/rebound.
  - Fresh-process validations in this workspace now show exo catalog/server parity at `85`.
- Status (2026-02-11): Centralized all active MCP persistence under `C:/Users/treyr/mcp/data` by default/environment (`SOVEREIGN_DATA_DIR`) and removed reliance on relative `data/` resolution in active modules.
- Status (2026-02-11): `mcp_server.py` now resolves `data_dir` before logging initialization and instantiates tools with centralized persistence kwargs when supported.
- Status (2026-02-11): Updated active modules (`session_manager_tool.py`, `exoskeleton_tool.py`, `auto_tool_module.py`, `web_tool.py`, `visual_tool.py`) to use canonical data roots and repo-root manifest references.
- Status (2026-02-11): Added non-pytest validation artifacts proving all checked persistence paths resolve under `C:/Users/treyr/mcp/data`.

## Update 2026-02-11 (Exoskeleton Bootstrap Diagnostics + No-Bootstrap Validation)

- Patched `tools/exoskeleton_tool.py` `bb7_exo_bootstrap` to force a live-catalog sync and return explicit diagnostics:
  - `catalog_sync` (`added`/`updated`)
  - `live_provider_attached`
  - `exo_tools_registered`
  - `manifest_path`
  - `manifest_present`
  - `manifest_mtime`
- Added new non-pytest validator:
  - `tests/validate_exo_bootstrap_independence.py`
  - Verifies `bb7_exo_state`, `bb7_exo_route`, and `bb7_exo_plan` succeed before any manual `bb7_exo_bootstrap` call.
  - Verifies exo indexed-tool count remains equal to `len(MCPServer().tools)` before and after bootstrap.
  - Writes markdown + JSON artifacts in `logs/`.
- Validation runs completed:
  - `python tests/validate_exo_bootstrap_independence.py`
    - `logs/exo_bootstrap_independence_validation_20260211_020626.md`
    - `logs/exo_bootstrap_independence_validation_20260211_020626.json`
  - `python tests/validate_exoskeleton_v1.py`
    - `logs/exoskeleton_v1_validation_20260211_020634.md`
    - `logs/exoskeleton_v1_validation_20260211_020634.json`
  - `python tests/validate_all_tools_exo_sweep.py`
    - `logs/all_tools_exo_sweep_20260211_020703.md`
    - `logs/all_tools_exo_sweep_20260211_020703.json`
- Operational reality confirmed:
  - Fresh-process workspace validations are green at `85/85`.
  - Current live MCP wrapper still reports `tool_count=82`, `indexed_tools=82`, `exoskeleton=7`, indicating stale runtime/transport process not yet rebound to latest code.

## Update 2026-02-11 (Exoskeleton Concurrent Init Race Fixed)

- Root cause confirmed for intermittent “exoskeleton missing / tools drop to 75” failures:
  - `tools/exoskeleton_tool.py` used a shared fixed temp file (`exoskeleton_state.json.tmp`) for JSON writes.
  - Parallel server startups could collide on rename and throw `WinError 32`, causing exoskeleton module load failure.
- Applied fix in `tools/exoskeleton_tool.py`:
  - `_write_json(...)` now uses unique temp files per write (`pid+thread+uuid`) plus retry/backoff on transient Windows lock errors.
  - `_append_jsonl(...)` now retries on transient lock errors.
  - `_save_state(...)` now logs persistence warnings instead of failing tool registration.
- Added race-specific non-pytest validator:
  - `tests/validate_exoskeleton_concurrent_init.py`
  - launches parallel child initializations across rounds and asserts no exoskeleton registration failures.
- Validation results after fix:
  - `logs/exoskeleton_concurrent_init_validation_20260211_021640.md` / `.json` passed.
  - `logs/exo_bootstrap_independence_validation_20260211_021646.md` / `.json` passed.
  - `logs/exoskeleton_v1_validation_20260211_021652.md` / `.json` passed.
  - `logs/all_tools_exo_sweep_20260211_021715.md` / `.json` passed (`85/85`).
- Live wrapper still reports `82` tools in this session despite repo validations being green, consistent with stale external MCP process state.

## Update 2026-02-11 (Callable Tool Normalization Between MCP and Exoskeleton)

- Implemented cross-layer normalization so exoskeleton catalog sync uses the same acceptance model as MCP `tools/list` for callable tools.
- Root mismatch fixed:
  - `mcp_server.py` previously allowed callables in `handle_list_tools` but sent raw `self.tools` to exoskeleton sync.
  - `tools/exoskeleton_tool.py::sync_from_live_tools` previously dropped non-dict entries.
- `mcp_server.py` changes:
  - Added `_normalize_live_tool_for_exoskeleton(tool_name, tool_info)`.
  - `_sync_exoskeleton_catalog()` now builds a normalized dict-backed tool map before calling `exo.sync_from_live_tools(...)`.
  - Normalizer also maps `input_schema` -> `inputSchema` for live-sync schema compatibility.
- `tools/exoskeleton_tool.py` changes:
  - `attach_live_tools_provider` and `sync_from_live_tools` now accept `Dict[str, Any]` (not dict-only metadata typing).
  - `sync_from_live_tools` now defensively normalizes callable entries and logs unsupported metadata types.
  - `_required_params_from_tool_info` now supports both `inputSchema` and `input_schema` and no longer short-circuits on empty `parameters` lists.
- Validation update in `tests/validate_exoskeleton_v1.py`:
  - Added explicit non-pytest checks for:
    - callable live-tool ingestion into `tool_catalog`
    - `input_schema.required` extraction into `required_params`
  - Added summary/report line for callable sync counts.
- Validation results:
  - `python -m py_compile mcp_server.py tools/exoskeleton_tool.py tests/validate_exoskeleton_v1.py` passed.
  - `python tests/validate_exoskeleton_v1.py` passed with new checks.
  - New artifacts:
    - `logs/exoskeleton_v1_validation_20260211_055111.md`
    - `logs/exoskeleton_v1_validation_20260211_055111.json`
- Outcome:
  - Callable tools can now be represented consistently in both MCP outward listing and exoskeleton cognitive catalog sync.
  - Schema-required parameter extraction now works for live metadata provided as `input_schema`.

## Update 2026-02-11 (Live Browser/Web Tool Trial in Active Session)

- User requested immediate live verification of browser/web tools due prior instability.
- Executed direct runtime calls (no restart/resume) for all web tools:
  - `bb7_check_url_status("https://example.com")` -> success, HTTP 200.
  - `bb7_fetch_url("https://example.com")` -> success, HTML content returned (513 bytes).
  - `bb7_extract_links("https://example.com")` -> success, extracted `https://iana.org/domains/example`.
  - `bb7_search_web("OpenAI", num_results=3)` -> executed without crash; DuckDuckGo returned non-JSON payload fallback (graceful degraded response, no exception).
  - `bb7_download_file("https://example.com", "C:/Users/treyr/mcp/data/validation/browser_tool_download_example.html")` -> success, file saved and verified (513 bytes).
- Outcome:
  - Browser/web tool stack is operational in this active Codex session.
  - Only observed degradation is expected search fallback behavior when upstream provider returns non-JSON content.

## Update 2026-02-11 (Exoskeleton Prior Persistence Diagnostics + Manifest Refresh)

- User raised concern that exoskeleton priors (`alpha`/`beta`) might reset to `0.0` on restart and asked for explicit manifest pull behavior.
- Investigation findings (live evidence):
  - `data/exoskeleton/exoskeleton_state.json` shows non-zero priors (`alpha_or_beta_zero_count=0`).
  - Direct persistence probe across fresh instances succeeded:
    - before `bb7_exo_reflect`: `alpha=13.553976`, `beta=1.0`, `successes=13`
    - after reflect + new `ExoskeletonTool()` instance: `alpha=14.486206`, `beta=1.0`, `successes=14`
  - Conclusion: priors are persisting; they are not resetting to `0.0` in workspace code.
- Implemented hardening in `tools/exoskeleton_tool.py`:
  - Added manifest mtime tracking and explicit refresh path:
    - `_get_manifest_mtime`
    - `_refresh_catalog_from_manifest_if_changed`
  - `bb7_exo_bootstrap` now performs manifest refresh check before live sync.
  - Added `_tool_prior_diagnostics` and exposed in bootstrap payload:
    - `tool_prior_count`, alpha/beta min/max, `zero_alpha_or_beta_count`, `cold_start_count`, `state_file`.
  - Bootstrap payload now includes `manifest_refresh` and `prior_diagnostics` fields.
- Validator enhancements in `tests/validate_exoskeleton_v1.py`:
  - Added checks for bootstrap diagnostics fields.
  - Added cleanup step for synthetic callable/schema test tools to prevent polluting persisted priors.
- Validation results:
  - `python -m py_compile tools/exoskeleton_tool.py tests/validate_exoskeleton_v1.py` passed.
  - `python tests/validate_exoskeleton_v1.py` passed with new checks.
    - `logs/exoskeleton_v1_validation_20260211_074606.md`
    - `logs/exoskeleton_v1_validation_20260211_074606.json`
  - `python tests/validate_all_tools_exo_sweep.py` passed `85/85`.
    - `logs/all_tools_exo_sweep_20260211_074536.md`
    - `logs/all_tools_exo_sweep_20260211_074536.json`
- Runtime caveat:
  - In this active wrapper session, `bb7_exo_bootstrap` response shape can still reflect older process payload until that wrapper transport is rebound, even though fresh-process validations are green.

## Update 2026-02-11 (Post-Reset Verification: Partial Success)

- User reported reset completed and requested confirmation.
- Live exo bootstrap now includes new fields from latest patch (`manifest_refresh`, `prior_diagnostics`), indicating updated code is loaded in this runtime.
- Current bootstrap snapshot shows:
  - `indexed_tools=85`
  - `manifest_refresh` present
  - `prior_diagnostics` present (`tool_prior_count=85`, `zero_alpha_or_beta_count=0`)
- Web sanity checks in this session remain healthy:
  - `bb7_check_url_status(https://example.com)` -> `200`
  - `bb7_fetch_url(https://example.com)` -> content returned
  - `bb7_search_web("OpenAI")` -> graceful non-JSON fallback, no crash
- Process sanity check still shows multiple MCP servers:
  - active `mcp_server.py` PIDs observed: `20088`, `17624`, `15484`, `23040`
- Conclusion:
  - Reset is only partial; runtime is newer but still not a single canonical MCP process.

## Update 2026-02-12 (SPEC Extension: Exoskeleton Runtime + Global Persistence)

- Extended `SPEC.md` in place (no rewrite) with a new section:
  - `Exoskeleton Runtime, Golden Paths, and Persistence Contract (2026-02-12)`
- Added explicit startup flow from MCP client launch -> config -> `mcp_server.py` -> tool registration -> exoskeleton init/sync.
- Added Mermaid flowcharts for:
  - system startup sequence,
  - exoskeleton load/save lifecycle.
- Documented exact persistence roles of:
  - `data/exoskeleton/exoskeleton_state.json`
  - `data/exoskeleton/execution_history.jsonl`
  - `data/exoskeleton/category_transitions.json`
  - `golden_paths.json`
- Clarified behavior: exoskeleton does **not** write on every call; writes occur at mutation boundaries (especially `bb7_exo_reflect`).
- Added persistence matrix distinguishing globally-anchored modules vs relative-path risk if tools are instantiated outside centralized server constructor flow.

## Update 2026-02-12 (SPEC Extended with Detailed Persistence Inventory)

- Extended `SPEC.md` again (append-only) with a new deep section:
  - `Detailed Persistence Inventory and Timing Matrix (2026-02-12)`.
- Added per-module persistence tables covering:
  - server-level artifacts (`mcp_server.log`, `shutdown_status.json`),
  - exoskeleton files (`exoskeleton_state.json`, `execution_history.jsonl`, `category_transitions.json`, plus manifest/golden path roles),
  - memory/session/optimization artifacts,
  - web/visual/terminal/file/project/shell persistence behavior.
- Added end-to-end Mermaid sequence diagram showing startup load and runtime save events.
- Clarified what is auto-loaded at startup versus saved on tool-call mutation boundaries.
- Reinforced canonical root contract via `SOVEREIGN_DATA_DIR` and continuity rule for single global data root usage.

## Update 2026-02-12 (OpenRouter Planner Tool First Pass)

- Implemented new module: `tools/openrouter_planner_tool.py`.
- Added planner tools:
  - `bb7_planner_health`
  - `bb7_planner_template`
  - `bb7_planner_plan`
- Integration details:
  - Registered planner module in `mcp_server.py` tool module list as:
    - `('openrouter_planner_tool', 'OpenRouterPlannerTool')`
  - Added 3 planner tool definitions to `tool_manifest.json`.
- Persistence contract:
  - Planner uses canonical global root (`SOVEREIGN_DATA_DIR`, default `C:/Users/treyr/mcp/data`).
  - Planner artifacts now persist under:
    - `C:/Users/treyr/mcp/data/planner/planner_state.json`
    - `C:/Users/treyr/mcp/data/planner/planner_runs.jsonl`
- OpenRouter config model:
  - `OPENROUTER_API_KEY` (required for live calls)
  - `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`)
  - `OPENROUTER_PLANNER_MODEL` (default `openai/gpt-4o-mini`)
  - `OPENROUTER_APP_NAME`, `OPENROUTER_SITE_URL` (optional request headers)
- Planner API behavior:
  - `bb7_planner_plan` supports `dry_run=true` for deterministic local validation without network/API key.
  - Includes retries, timeout bounds, JSON parsing fallback, and run telemetry logging.
- Non-pytest validation added:
  - `tests/validate_openrouter_planner_tool.py`
  - Produces markdown + JSON artifacts in `logs/`.
- Latest validation run passed:
  - `logs/openrouter_planner_validation_20260212_095549.md`
  - `logs/openrouter_planner_validation_20260212_095549.json`

## 2026-02-26 - Journal Tool Status

- New thought journal module is active and functional in the running MCP environment.
- Confirmed operational functions: record thought, capture decision, add outcome, search, stats.
- Current behavior detail for integrators: creation methods return human-readable strings containing `[id: ...]`; downstream calls require ID extraction.
- Immediate next integration target: expose/normalize structured JSON outputs for all journal methods to improve planner/tool-chain composability.

## Update 2026-02-27 (Memory Tools Error-Hardening)

- `tools/memory_tool.py` and `tools/memory_interconnect.py` were updated with invocation-compatibility wrappers.
- Both modules now normalize tool-call argument styles (`kwargs`, positional args, and single positional dict argument).
- `get_tools()` now returns a wrapped registry that is tolerant of legacy dispatch patterns, including empty dicts passed to no-arg callables.
- Compile/runtime checks for both modules passed.
- Memory-related end-to-end probe across server-registered memory tools passed with no execution errors.
- Direct dict-style tool calls for both modules were explicitly validated and passed.

## Update 2026-02-27 (Strict Schema Compatibility)

- Patched `mcp_server.py` `handle_list_tools` legacy parameter conversion so array properties always include `items` in emitted `inputSchema`.
- This resolves strict validator error for `SovereignMCP_bb7_memory_store` where `tags` previously surfaced as `type=array` without `items`.
- Added schema-focused non-pytest validator run with artifacts in `logs/`:
  - `schema_items_validation_20260226_220835.md`
  - `schema_items_validation_20260226_220835.json`

## Update 2026-02-27 (Runtime Overhead Reduction)

- `vscode_terminal_tool` has been decommissioned from active runtime.
- `mcp_server.py` no longer registers `('vscode_terminal_tool', 'VSCodeTerminalTool')`.
- Source file moved to backup archive:
  - `tools/backup_20260114_213833/vscode_terminal_tool.py`
- `tool_manifest.json` pruned of `bb7_terminal_*` entries.
- Fresh-process validation confirms runtime now exposes 115 tools and no terminal-tool namespace.

## Update 2026-02-27 (Golden Paths Terminal Cleanup + VSCode Removal Verification)

- `golden_paths.json` was updated to remove `terminal_automation_workflow` entirely.
- `system_diagnostics_workflow` no longer depends on `bb7_terminal_status`; it now uses `bb7_run_command` and outputs `diagnostic_output`.
- File-level verification checks now show no matches for `vscode`, `bb7_terminal_*`, or `terminal_automation_workflow` in:
  - `golden_paths.json`
  - `mcp_server.py`
  - `tool_manifest.json`
- Fresh-process runtime verification (`MCPServer()` from workspace code) reports:
  - `tool_count=115`
  - `has_terminal_tools=False`
  - `has_vscode_terminal_module=False`
- Note: the currently attached long-lived wrapper can still report stale exoskeleton counts (e.g., 121) until that external transport/process is restarted.

## Update 2026-03-01 (Workflows Expansion: Exoskeleton + Thought Journal Deep Ops)

- Expanded `workflows.md` with two new implementation-grounded sections:
  - `## 15. Exoskeleton Deep Ops (Based on tools/exoskeleton_tool.py)`
  - `## 16. Thought Journal Deep Ops (Based on tools/thought_journal_tool.py)`
- Exoskeleton additions now document runtime behavior directly from `tools/exoskeleton_tool.py`, including:
  - canonical control loop (`bb7_exo_bootstrap -> bb7_exo_route -> bb7_exo_plan -> bb7_exo_execute_step -> bb7_exo_reflect`),
  - momentum-aware routing signals,
  - checkpoint/resume/KPI lifecycle,
  - preemptive risk gating thresholds,
  - persistence file map under `C:/Users/treyr/mcp/data/exoskeleton`.
- Thought Journal additions now document real tool contract from `tools/thought_journal_tool.py`, including:
  - string-return creation behavior with `[id: <8-hex>]` extraction requirement,
  - canonical provenance loop (thought -> decision -> outcome),
  - BM25 retrieval patterns and conflict detection usage,
  - reverse memory-link lookup flow,
  - persistence/index files under sovereign data root.
- Navigation followed `codebase-omniscient.md` discipline: read target implementation files first, then update workflows with implementation-accurate guidance.
- This update is documentation-only (no runtime code changes in `tools/*` in this pass).

## Update 2026-03-06 (Lag / Timeout Hardening Without Splitting `data/`)

- Investigated user-reported long-run lag and `bb7_search_files` 120s timeouts under multi-agent usage with a shared `C:/Users/treyr/mcp/data` directory.
- Root-cause pattern confirmed:
  - `mcp_server.py` stdio loop is synchronous and processes one request at a time.
  - `bb7_search_files` previously used raw `Path.rglob(...)` with no internal timeout, no pruning, and misleading search counters.
  - multiple MCP server processes are currently active on this machine, all sharing the same data/log paths.
  - several shared-state writers still relied on process-local locks plus fixed `.tmp` file names, which is unsafe on Windows across processes.
- Runtime/code changes completed:
  - `tools/file_tool.py`
    - bounded `bb7_search_files` with internal time budget
    - short ripgrep probe, then bounded `os.walk(...)` fallback
    - skip Windows reparse points
    - prune common generated directories
    - return partial results instead of waiting for outer client timeout
  - `mcp_server.py`
    - debounce repeated `_sync_exoskeleton_catalog()` calls
    - emit slow-tool warnings for calls taking `>= 5s`
  - `tools/memory_tool.py`
  - `tools/memory_interconnect.py`
  - `tools/thought_journal_tool.py`
    - replaced fixed `.tmp` writes with unique temp files + retry/backoff on transient Windows lock errors
- Validation:
  - `py_compile` passed for all changed Python files.
  - direct broad search smoke:
    - `FileTool().search_files("C:\\Users\\treyr", "workflows.md", 50)`
    - now returns in about `15s` with bounded partial output instead of hanging until client-side timeout.
  - temp-dir smoke passed for:
    - `EnhancedMemoryTool.store(...)`
    - `MemoryInterconnectionEngine.analyze_memory_entry(...)`
    - `ThoughtJournalTool.bb7_journal_record_thought(...)`
- Follow-up:
  - consider extending unique-temp atomic write helpers into `session_manager_tool.py`
  - consider optional schema-level timeout/include-exclude controls for `bb7_search_files`

## Update 2026-03-06 (Session Manager Concurrency Hardening)

- Completed the next shared-data-dir hardening pass in `tools/session_manager_tool.py`.
- Root-cause detail:
  - aggregate files (`session_index.json`, `memory_index.json`) were already hardened,
  - but active-session mutators still trusted long-lived `self.current_session` state and only locked at write time,
  - which left a stale read-modify-write window for concurrent processes writing the same session document.
- Runtime/code changes completed:
  - added `_mutate_active_session(...)` to reload the active session under the per-session file lock, apply the mutation, and atomically rewrite before releasing the lock.
  - moved these active-session mutation paths onto that helper:
    - `bb7_log_event`
    - `bb7_capture_insight`
    - `bb7_record_workflow`
    - `bb7_update_focus`
    - `bb7_pause_session`
  - updated `bb7_resume_session` to do its read/modify/write under the same session-file lock instead of loading and saving in separate steps.
  - replaced remaining direct session-file reads in:
    - `bb7_get_session_insights`
    - `bb7_cross_session_analysis`
    - `bb7_get_session_summary`
    with `_read_json_file(...)` for transient Windows lock tolerance.
- Validation:
  - `C:/Users/treyr/mcp/mcp.venv/Scripts/python.exe -m py_compile tools/session_manager_tool.py tests/validate_session_manager_concurrency.py`
  - `C:/Users/treyr/mcp/mcp.venv/Scripts/python.exe tests/validate_session_manager_concurrency.py`
  - latest validator output:
    - `session_index_count=6`
    - `unique_session_ids=6`
    - `memory_links_for_session=8`
    - `reverse_hits=8`
    - `session_event_count=10`
    - `unique_note_events=10`
    - `session_manager concurrency smoke ok`
- Follow-up:
  - shared runtime topology is still per-client stdio process launch; a single canonical daemon is still the next architectural step.
  - stale external clients can still hold old session ids/process views at the product level even though file-level session writes are now serialized safely.

## 2026-03-11 - Workspace Loader MCP-Level Fix

- Updated `tools/auto_tool_module.py` so `bb7_workspace_context_loader` accepts optional `workspace_path`.
- Loader now reports `workspace_source` and warns/falls back to process cwd when the provided path is missing.
- Tool metadata in `get_tools()` now advertises `workspace_path` for the loader.
- Operational note: the currently running MCP process may need restart/reload to expose the new parameter live.

## Update 2026-04-08 (Workflow Doc Refactor + Zo Node Recon)

- Replaced `workflows.md` with an operational playbook tailored to long-session agent work instead of a broad tool encyclopedia.
- New workflow doctrine explicitly encodes:
  - deterministic per-turn loop (`exo -> journal -> execute -> reflect`),
  - tool-budget governor targeting `~20 tool calls / 100 interactions`,
  - context compression and durable-memory rules,
  - runtime shell access boundaries,
  - cloud-node decision workflow for `zo.computer`.
- User intent emphasized non-code-agent posture and context constraints; rewrite reflects that explicitly.
- Live web recon performed for `zo.computer`:
  - pricing tiers and compute envelope reviewed,
  - SSH/remote-IDE path validated via official docs,
  - security/provider posture reviewed.
- Session persistence:
  - memory key `somnus_workflows_rewrite_non_code_ops_2026_04_08` stored and linked.

## Update 2026-04-08 (Workflow Driver Realignment: Lisan + Exo)

- `workflows.md` was rewritten again to align directly with implementation surfaces in:
  - `tools/lisan_al_gaib.py`
  - `tools/exoskeleton_tool.py`
  - `tools/enhanced_code_analysis_tool.py`
  - `tools/shell_tool.py`
  - `tools/web_tool.py`
  - `tools/visual_tool.py`
  - `tools/memory_tool.py`
  - `tools/memory_interconnect.py`
  - `tools/session_manager_tool.py`
  - `tools/project_context_tool.py`
  - `tools/auto_tool_module.py`
- New `workflows.md` now treats exoskeleton+lisan as the primary control plane and de-emphasizes legacy external journal-first operation.
- Added explicit module topology, canonical turbo loop, file-intelligence doctrine, anti-collapse guardrails, and budget governor.
- User-directed posture lock: autonomy experiment first, no drift back to generic coding-agent behavior.

## Update 2026-04-08 (Docs Realignment + Runtime Drift Snapshot)

- Completed docs-only realignment pass for current architecture.
- Rewrote `AGENTS.md` as runtime override aligned to:
  - `mcp_server.py` orchestration role,
  - exoskeleton + lisan primary control plane,
  - journal de-emphasis (compatibility-only),
  - canonical turbo loop and persistence/reflect requirements.
- Rewrote `README.md` to remove stale claims (old tool counts, VSCode terminal references) and reflect active module registration.
- Updated `workflows.md` to explicitly include `mcp_server.py` as control-plane orchestrator and add runtime-check warning for legacy `bb7_journal_*` catalog entries.

### Runtime checks performed

- `ping_server` returned `tool_count=105` in this Linux session.
- `bb7_tool_health_report` showed active loaded modules include:
  - memory, file, shell, web, session, project_context, auto_tool_module, exoskeleton, enhanced_code_analysis, openrouter planner/agent.
- `visual_tool` failed module load in this headless session with `DISPLAY` error.
- Direct runtime probe confirmed:
  - `bb7_lisan_intend` is callable.
  - `bb7_journal_surface_relevant` is not callable (`Tool not found`) despite catalog visibility.

### Drift/kink summary

- Exoskeleton category/catalog can still surface legacy journal tool names that are not runtime-callable.
- `bb7_agent_run` fails when `OPENROUTER_API_KEY` is unset.
- Manifest/catalog/runtime parity still needs dedicated cleanup to avoid stale route candidates.

## Update 2026-04-08 (Phase A Ambient Continuity Spine + Single-Instance Guard)

- Implemented Phase A passive telemetry in `mcp_server.py` using append-only `events.jsonl` under repo-local canonical data root.
- Added session/turn identity model:
  - `session_id` generated at server init
  - monotonic `turn_id` generated per JSON-RPC request
- Added automatic server-side event hooks (no explicit memory tool call required):
  - `session_start`
  - `memory_context_injected`
  - `request_received`
  - `tool_execution_start`
  - `tool_execution_end` (success/failure with latency and summary)
  - `request_completed`
- Added event schema fields:
  - `event_id`, `ts`, `session_id`, `turn_id`, `event_type`, `source`, `payload_json`, `importance_hint`.
- Added singleton lock (`mcp_server.lock`) so only one active MCP server process can own the same data root at a time; second process now fails fast with explicit pid.
- Added stale-lock recovery behavior: dead holder pid allows lock reclamation on next startup.
- Hardened data-root resolution: server now enforces repo-local `./data` and ignores conflicting external `SOVEREIGN_DATA_DIR` values with explicit stderr warning.
- Fixed proactive-memory injection fallback bug where undefined `e` could be referenced when no exception occurred.
- Verification:
  - `py_compile` passed for `mcp_server.py` and `tools/shell_tool.py`.
  - direct request smoke (`tools/call` -> `ping_server`) produced expected telemetry rows in `data/events.jsonl`.
  - parallel startup test confirmed singleton lock denial for second process.

## Update 2026-04-08 (Data Plane Unification + Manifest Parity Hardening)

- Patched `mcp_server.py` to force canonical process env after resolving `self.data_dir`:
  - sets `SOVEREIGN_DATA_DIR` and `MCP_DATA_DIR` to `/home/daeron/Somnus-MCP/data`.
  - emits explicit stderr override notice when inherited env points elsewhere.
- Patched `tools/openrouter_agent_tool.py` so agent plane persistence no longer depends on static import-time class constants:
  - `OpenRouterAgentTool` now resolves `data_dir` at runtime and exports canonical env values.
  - `ExecutionNode` now receives canonical data dir explicitly per instance.
- Patched `tools/exoskeleton_tool.py` live sync to prune stale catalog entries not present in live tools (`removed` count added).
- Regenerated manifests from live registry:
  - `tool_manifest.json` now exactly matches runtime tools (110/110).
  - `manifest.json` module list now reflects registered module set (13 modules, no duplicate web entry).

### Verification snapshot

- Live parity check: `live=110`, `tool_manifest=110`, `missing=0`, `extra=0`.
- Journal parity check: `journal_in_live=0`, `journal_in_manifest=0`.
- Compile check passed: `mcp_server.py`, `tools/openrouter_agent_tool.py`, `tools/exoskeleton_tool.py`.
- Runtime process audit still shows one older MCP pid inheriting legacy env:
  - pid `13108` has `SOVEREIGN_DATA_DIR=/home/daeron/Projects/mcp_server/data`.
  - that process should be stopped/restarted to fully eliminate split-plane risk.
- Added per-turn ambient memory surfacing hook in `mcp_server.py` for `tools/call` requests:
  - event type: `memory_context_surfaced`
  - context built from method + tool name + argument keys + compact string inputs
  - uses existing weighted memory retrieval path (`surface_context` / `memory_surface_context`)
  - logs result summary to telemetry without modifying tool interfaces.

## Update 2026-04-08 (Fail-Loud Control Plane + Codex Ambient Ingest)

- Hardened `mcp_server.py` with explicit internal failure ledger at `data/internal_failures.jsonl` and surfaced it through `bb7_tool_health_report`.
- Added passive Codex continuity ingest in `mcp_server.py`:
  - reads `.codex/state_5.sqlite` to locate the active rollout for this workspace,
  - ingests rollout deltas plus `.codex/history.jsonl` into `distillation.db` conversation history,
  - promotes current-thread user/assistant messages into memory via `bb7_memory_bulk_store`,
  - augments per-turn ambient surfacing with recent conversation-context retrieval.
- Added offset self-healing for Codex ingest: stale mid-record offsets now realign forward to the next line boundary and log `codex_offset_realigned` loudly instead of silently poisoning continuity.
- Hardened tool/module failure posture:
  - `tools/memory_tool.py` now treats missing/corrupt memory intelligence/storage as explicit runtime errors instead of fallback-noise,
  - `tools/lisan_al_gaib.py` distillation and cognitive-journal write failures now log loudly and raise where appropriate,
  - `tools/exoskeleton_tool.py` `bb7_lisan_recall` now records recall failures in output instead of debug-only swallowing,
  - `tools/session_manager_tool.py` proactive-memory surfacing now logs errors loudly and session responses no longer emit emoji strings.
- Live smoke validation:
  - forced a stale/misaligned Codex ingest offset and verified automatic realignment + logged warning,
  - verified `conversation_history` rows are being appended in `data/distillation.db`,
  - verified `_surface_turn_memory_context(...)` now returns `status=success` with conversation context present.
- Environment/runtime caveat surfaced loudly, not silently:
  - this host is missing `aiohttp`, so `web_tool`, `openrouter_planner_tool`, and `openrouter_agent_tool` fail import and reduce live tool count until dependency/runtime is fixed.

## Update 2026-04-12 (Golden Path Restoration Plan v2)

- `PLAN.md` was rewritten as a handoff-ready hardening contract for always-on single-server orchestration.
- Plan now explicitly covers:
  - analyzer compute stabilization,
  - MCTS/A* routing policy integration,
  - dynamic memory injection protocols,
  - distillation-as-witness posture,
  - OpenRouter reintegration gates.
- Code-verified findings captured in plan:
  - `bb7_security_audit` currently invokes `analyze_file(..., include_security=True)` and inherits heavy defaults,
  - exoskeleton production plan path still template-driven (`_make_plans`),
  - `lisan_al_gaib.py` MCTS subsystem exists but is not production-wired into exo planner.
- Immediate implementation emphasis in plan:
  - split security-only path from deep analysis,
  - add profile-based analysis modes and compute guards,
  - wire MCTS with template fallback,
  - introduce adaptive memory surfacing cadence based on uncertainty/novelty/failure signals.

## Update 2026-04-13 (OpenRouter Distillation Reactivation + Always-On Writes)

- Implemented an always-on distillation pipeline writer in `databus/openrouter_wrapper.py` via:
  - `OpenRouterDistillationLogger`
  - `get_openrouter_distillation_logger(...)` singleton accessor
- New logger behavior:
  - async queue-backed JSONL writes (non-blocking call path)
  - V2-style trajectory records with heuristics/auto-tags
  - writes to both:
    - `data/distillation_dataset/trajectories_YYYY-MM-DD.jsonl`
    - `data/distillation/trajectories_YYYY-MM-DD.jsonl` (legacy compatibility)
  - downstream derivative artifacts:
    - `data/distillation_dataset/trajectory_index.jsonl`
    - `data/distillation_dataset/high_value/high_value_YYYY-MM-DD.jsonl`
    - `data/distillation_dataset/failures/failures_YYYY-MM-DD.jsonl`
- `tools/openrouter_agent_tool.py` now integrates distillation directly:
  - captures incremental trajectory steps during `bb7_agent_run`
  - logs telemetry (latency, iterations, tool error counts, token usage, model lineage)
  - persists `trajectory_id` in both API response and `data/agents/agent_runs.jsonl`
- `tools/openrouter_planner_tool.py` now integrates distillation directly:
  - logs trajectories for both `dry_run` and live `bb7_planner_plan` execution
  - includes `trajectory_id` in API responses and `data/planner/planner_runs.jsonl`
- Runtime-safe import hardening added in `databus/openrouter_wrapper.py`:
  - distillation logger remains importable even if OpenRouter client deps (`pydantic` chain) are unavailable in the current shell environment.
- Validation completed:
  - `python3 -m py_compile databus/openrouter_wrapper.py tools/openrouter_agent_tool.py tools/openrouter_planner_tool.py`
  - smoke execution with `env PYTHONPATH=. python3 scripts/_smoke_distill.py` confirmed:
    - planner dry run returns `trajectory_id`
    - direct stub logging returns `trajectory_id`
    - files update under both `data/distillation_dataset/` and `data/distillation/`

## 2026-04-13 OpenRouter Env Alignment

- Added a root `.env` contract for OpenRouter + data-root variables.
- `scripts/start_server.sh` now sources `.env` before launching the server.
- `databus/openrouter.yaml` now defaults to `elephant-alpha` with an empty fallback chain.
- Live OpenRouter agent/planner calls still need a real `OPENROUTER_API_KEY`; health and dry-run paths remain the safe validation route until the key is set.

## Runtime Persistence Audit — 2026-04-14 (Data Plane / 24-7 State)

- Scope: audited active tool modules and write-path behavior for `/home/daeron/Somnus-MCP/data`.
- Server status: `ping_server` alive; 115 tools registered.
- Loaded modules (`bb7_tool_health_report`): `enhanced_code_analysis_tool`, `openrouter_agent_tool`, `exoskeleton_tool`, `memory_tool`, `thought_journal_tool`, `file_tool`, `openrouter_planner_tool`, `auto_tool_module`, `enhanced_web_tool`, `memory_interconnect`, `shell_tool`, `session_manager_tool`, `project_context_tool`.
- Module load issue: `visual_tool` failed load due missing `DISPLAY` (headless runtime).

### Data root inventory snapshot

- `data/` contains 34 subdirectories and 38 top-level files (270 files total, ~61.56 MB).
- Largest files: `mcp_server.log` (~9.56 MB), `distillation.db` (~9.23 MB), `events.jsonl` (~9.04 MB), `memory_store.json` (~8.61 MB), `concept_index.json` (~5.21 MB), `memory_relationships.json` (~2.95 MB).

### Write-path classification

- Append-only JSONL (good for 24/7):
  - `mcp_server.py`: `events.jsonl`, `internal_failures.jsonl`
  - `tools/exoskeleton_tool.py`: `exoskeleton/execution_history.jsonl`, `cross_ai_activity.jsonl`, `exo_checkpoints.jsonl`
  - `tools/lisan_al_gaib.py`: `distillation/trajectories_YYYY-MM-DD.jsonl`, `exoskeleton/decision_trail.jsonl`
  - `databus/openrouter_wrapper.py`: `distillation_dataset/*.jsonl`, legacy `distillation/*.jsonl`, `trajectory_index.jsonl`, high_value/failures shards
  - `tools/openrouter_agent_tool.py`: `agents/agent_runs.jsonl`, `agents/messages/*.jsonl`
  - `tools/openrouter_planner_tool.py`: `planner/planner_runs.jsonl`
- Atomic snapshot rewrite (temp + `os.replace`, safe against partial writes):
  - `tools/session_manager_tool.py` session/index files
  - `tools/memory_tool.py` `memory_store.json`
  - `tools/memory_interconnect.py` `memory_relationships.json`, `concept_index.json`, `importance_scores.json`
  - `tools/thought_journal_tool.py` `thought_journal.json`, `journal_index.json`, `journal_memory_index.json`
  - `tools/exoskeleton_tool.py` state files (`active_plans.json`, `exoskeleton_state.json`, etc.)
  - `tools/openrouter_agent_tool.py` / `tools/openrouter_planner_tool.py` state files
  - `mcp_server.py` `codex_ingest_state.json`
- Direct overwrite hotspots (non-append semantics):
  - `tools/file_tool.py` `write_file()` uses direct `"w"` (intentionally destructive when called)
  - `tools/openrouter_agent_tool.py` handoff queue file `agents/handoffs/{agent}_pending.json` overwritten per pending handoff
  - `mcp_server.py` shutdown writes `shutdown_status.json` with direct `"w"`

### Current drift / anomalies

- `data/journal_memory_index.json` currently tiny/stale mappings (legacy keys), while `thought_journal.json` is active and receiving new entries.
- Cause pattern: reverse map updates only when journal entries include `linked_memories`; many current entries do not, so reverse-map growth can lag.
- `.venv` not present in repo root; active env dir is `mcp.venv/`.
- `.env` exists but key list did not expose `OPENROUTER_API_KEY`; `bb7_planner_health` and `bb7_agent_health` currently report `api_key_configured=false`.

### Interpretation

- The autonomy server is still active and logging continuously at the server plane (`events.jsonl`), with additional module-specific logs.
- The system is mostly safe against partial-write corruption due broad atomic replace usage.
- Main 24/7 risk is not corruption but scale/latency from repeated full-JSON rewrites of large snapshot files.

## OpenRouter Env/Model Fix Pass — 2026-04-14

Applied targeted edits (user-approved scope only):

- `databus/openrouter.yaml`
- `databus/sovereign_openrouter.py`
- `tools/openrouter_planner_tool.py`
- `tools/openrouter_agent_tool.py`

### What was fixed

- Enforced elephant-alpha as tool-level default model in planner/agent modules.
- Added runtime `.env` hydration inside planner/agent config resolution so env additions can be seen by these tool classes without changing unrelated server code.
- Added API-key alias resolution in planner/agent (`OPENROUTER_API_KEY`, `OPENROUTER_KEY`, `OR_API_KEY`).
- Added env alias support in sovereign YAML interpolation path.
- Updated YAML credential expression to: `${OPENROUTER_API_KEY|OPENROUTER_KEY|OR_API_KEY}`.
- Kept routing fallback chain empty in YAML (no backup fallback model list in config).

### Verification (code-level, local execution)

- `py_compile` succeeded for all edited files.
- Planner/agent module-level health checks executed via local python now resolve model as `elephant-alpha`.
- Alias checks succeeded:
  - `OPENROUTER_KEY=test-key` => planner health reports `api_key_configured=True`.
  - `OR_API_KEY=test-key` => agent health reports `api_key_configured=True`.

### Runtime caveat

- Live MCP instance still reports old qwen model + no key in `bb7_planner_health`/`bb7_agent_health`, indicating current server process is running pre-edit module instances.
- A server restart is required for live MCP tool calls to reflect these code changes.

### Live Validation Continuation — 2026-04-14 (Post-fix)

- Live `bb7_agent_health` and `bb7_planner_health` now resolve `model: elephant-alpha` in active MCP tool responses.
- `api_key_configured` remains `false` in live MCP because no OpenRouter key variable is present in current process env/.env.
- `bb7_planner_plan(dry_run=true)` succeeded with `model: elephant-alpha` and produced trajectory id `895adef2-c1dc-41d4-81c5-03b8edcff97a`.
- `bb7_agent_run` hard-gate correctly fails with `OPENROUTER_API_KEY not set` (expected behavior).
- Restart script confirmed at `scripts/start_server.sh` and it sources repo `.env` before launching server.

### Key-Added Verification Attempt — 2026-04-14 (Follow-up)

- User indicated OpenRouter key was added.
- Live checks still show `api_key_configured=false` for both planner and agent.
- `.env` key presence audit (masked) currently shows empty/missing for:
  - `OPENROUTER_API_KEY`
  - `OPENROUTER_KEY`
  - `OR_API_KEY`
- `~/.codex/config.toml` SovereignMCP env block also shows these key vars empty/missing.
- Live non-dry calls remain hard-gated as expected:
  - `bb7_planner_plan` => OPENROUTER_API_KEY is not set or empty
  - `bb7_agent_run` => OPENROUTER_API_KEY not set

## Update 2026-04-16 (Golden Paths + Initialize Handshake Stabilization)

- Applied targeted fixes in `tools/exoskeleton_tool.py` to make golden path matching and routing behavior coherent:
  - Added `_normalize_golden_match(...)` so matched payloads consistently expose both `name` and `path_name`.
  - `_match_golden_path(...)` now normalizes both oracle and fallback matches.
  - Auto-promotion duplicate guard now checks canonical `auto_discovered_<workflow>` key and dedupes by identical chain.
  - After auto-promotion write, in-memory `self.golden_paths` and `self._golden_oracle.golden_paths` are refreshed immediately.
  - `_score_tools(...)` now accepts optional `golden_match` and applies `golden_path_bonus` to tools in matched golden chain.
  - `bb7_exo_route` and `bb7_exo_plan` now pass matched golden path into scoring and surface `golden_path_match` in responses.
  - `bb7_exo_briefing`/`bb7_lisan_intend` now read `name`/`path_name` robustly.
- Applied startup handshake fix in `tools/meta_intelligence_engine.py`:
  - Removed import-time stdout `print(...)` in fallback import path; replaced with logger warning.
  - This prevents non-JSON stdout contamination before/around `initialize` response.
- Validation run with `./mcp.venv/bin/python`:
  - `py_compile` passed for modified files.
  - Stdio initialize probe now returns clean JSON response line on stdout.
  - Ephemeral stdio `tools/call` probe for `bb7_exo_route` shows `golden_path_match` and `golden_path_bonus` fields as expected.


## Update 2026-06-01 (Linux Headless Visual Tool Startup Hardening)

- Runtime context: local Linux host `daeron-hpenvyx3602in1laptop15ey0xxx`, cwd `/home/daeron/Somnus-MCP`, canonical data root `/home/daeron/Somnus-MCP/data`.
- Symptom: live SovereignMCP health reported `failed_module_loads.visual_tool.error == "'DISPLAY'"` when Codex launched the MCP server without a GUI display environment.
- Root cause: `tools/visual_tool.py` imported `pyautogui` at module import time and only caught `ImportError`; on Linux, `pyautogui -> mouseinfo` can raise `KeyError('DISPLAY')` before `VisualTool` is instantiated.
- Fix: active `tools/visual_tool.py` now detects `DISPLAY` / `WAYLAND_DISPLAY` before importing pyautogui, catches all optional-GUI import failures, records `PYAUTOGUI_IMPORT_ERROR`, sets `PYAUTOGUI_AVAILABLE=False`, and exposes `headless_mode` capability instead of failing module registration.
- Verification: `mcp.venv/bin/python -m py_compile tools/visual_tool.py mcp_server.py` passed. Fresh headless `MCPServer()` init with `DISPLAY` and `WAYLAND_DISPLAY` unset loaded `visual_tool`, registered `bb7_take_screenshot`, `bb7_find_on_screen`, `bb7_click_element`, `bb7_screen_monitor`, and `bb7_window_info`, and reported `visual_failed None` with 129 total tools.
- Operational note: an already-running Codex MCP wrapper may continue showing stale visual_tool failure until the MCP server/client transport is restarted, because loaded Python modules are process-local.

## Update 2026-06-05 (FSTIP File-Surface Token Isolation)

- Implemented the File-Surface Token Isolation Protocol in `tools/file_tool.py` and `mcp_server.py`.
- `bb7_read_file` now supports bounded `start_line`/`end_line` windows and `semantic_target` windows, and large naked reads default to `FILE_READ_ISOLATED` structural skeleton manifests unless `allow_large_raw=True`.
- `bb7_write_file` and `bb7_append_file` now return sparse `FILE_PATCH_SUCCESS` verification manifests with bounded old/new delta windows instead of status strings that encourage context echo.
- Follow-up live reload probe confirmed the active MCP process returned `FILE_PATCH_SUCCESS`; a small source follow-up corrected `_analyze_content(...)` line counting to use `splitlines()` so manifests report logical lines accurately.
- `MCPServer._format_tool_result(...)` now receives tool arguments and applies a file-surface display projection for string-returning file tools:
  - oversized raw `bb7_read_file` text is suppressed at the final display seam,
  - already-sparse verification manifests pass through unchanged,
  - projection metadata marks raw payload preservation before display shaping and excludes projection from Q-table/observation/distillation/RFT lanes.
- Added repo-local Token Density Governor doctrine to `AGENTS.md`.
- Validation passed:
  - `python -m py_compile mcp_server.py tools/file_tool.py`
  - direct FileTool smoke checks for line windows, semantic windows, write/append sparse manifests, and large-read governor
  - direct MCPServer display-projection smoke checks for large read suppression and manifest pass-through
- Validation artifacts:
  - `data/validation/fstip_file_surface_token_isolation_20260605.md`
  - `data/validation/fstip_file_surface_token_isolation_20260605.json`
- Runtime caveat: an already-running MCP server process may need restart/reload before live Codex tool calls reflect the source edits.
