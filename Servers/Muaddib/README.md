# Somnus-MCP Neural-Symbolic Cognition Server

Somnus-MCP is a **24/7 autonomous neural-symbolic cognition server** for distributed AI continuity and routing research. MCP JSON-RPC2, stdio, SSE, HTTPS, and webhooks are transport surfaces into one live runtime plane; they are not the architecture.

`mcp_server.py` is the gateway/dispatcher into the 4-7 Muad'Dib + `tools/` cognition layers, not the intelligence itself. Keep transport, registry, lifecycle, raw-output behavior, and final human-facing display projection thin and stable; put neural self-play, routing, reflection, and registry-bound intelligence in `muadib/` and `tools/`.

## Current Architecture (Runtime-Oriented)

Runtime invariants:

- one canonical cognition/data plane shared by all clients/agents; persistent transports should share one gateway process, while stdio clients may spawn per-client gateway children that must not fork data/neural state;
- one distributed cognition data root: `/home/daeron/Somnus-MCP/data`;
- one validation/runtime environment: `/home/daeron/Somnus-MCP/mcp.venv`;
- no per-project BB7 data silos;
- source/schema validation does not require starting or instantiating another `MCPServer()`.
- cleaned Markdown tool-output display is projection only; raw payloads remain the substrate truth for telemetry, memory exchange, Q-table/observation paths, and distillation/RFT.

Control plane:

1. `mcp_server.py` — gateway/dispatcher: transport dispatch, dynamic BB7 surface discovery, canonical data-root enforcement, async bridging, event spine, ambient continuity exchange.
2. `tools/exoskeleton_tool.py` — routing, planning, live catalog sync, Bayesian priors, reflect loop, SessionMomentum integration, golden-path learning.
3. `tools/lisan_al_gaib.py` — spectral intent decomposition, GoldenPathOracle, MCTS/Thompson machinery, distillation/witness components, session-momentum primitives.
4. `muadib/` — neural substrate: DigitalTwinTool, trained Q-table/observation signal, 512-dim catalog embeddings, provenance-tagged advanced bridge.

Continuity substrate:

- `tools/memory_tool.py` — working memory LRU, persistent memory store, BM25/Ebbinghaus surfacing.
- `tools/memory_interconnect.py` — concept graph, relationships, clustering, gap detection.
- `tools/session_manager_tool.py` — cognitive session state, events, insights, workflow records, cross-session intelligence.

Public BB7 surfaces are compiled capability endpoints. They should not be treated as raw one-function utilities; they sit over the memory/session substrate, routing/planning substrate, and persistent event/learning plane.

## Migration Snapshot — 2026-05-27

- `tools/file_tool.py` is the promoted advanced `FileTool` with compatibility aliases preserved: `bb7_append_file`, `bb7_get_file_info`, `bb7_file_cache_stats`, legacy `pattern` search support, and raw `bb7_read_file` by default.
- New file surfaces: `bb7_copy_file`, `bb7_move_file`, `bb7_delete_file`, `bb7_file_info`, `bb7_operation_history`.
- `golden_paths.json` is executable routing config only; extracted metadata/audit notes live in `golden_paths_meta.json`.
- `tools/meta_intelligence_engine.py` is a registry-bound facade exposing `bb7_code_consciousness`, `bb7_context_weaver`, `bb7_creative_problem_solver`, and `bb7_muadib_mentat_bridge`. It composes the live BB7 registry and bounded Mentat sidecar artifacts without instantiating sibling tools, mutating Muad'Dib weights/Q-table state, or touching the MCP output adapter. The Muad'Dib/Mentat bridge contract explicitly treats `mcp_server.py` as gateway into Muad'Dib/tools, not as the intelligence layer.
- `mcp_server.py` now includes guarded `bb7_tool_refresh_module` for allowlisted registry-bound facade parity. It refreshes `meta_intelligence_engine` in-place, reattaches registry-bound facades, and resyncs exoskeleton catalog without starting a second server, rerunning full boot lifecycle loops, or altering output formatting.
- `muadib/` now has a safetensors-first self-play lane: `MuadDibSelfPlayHead` trains bounded candidate policy/value weights, `bb7_dt_self_play` writes/archives `.safetensors` checkpoints by default, `bb7_dt_self_play_lock` pins active/champion promotion when reproducibility matters, and `bb7_dt_checkpoint_status` reports active tensor checkpoints plus lock state. JSON is metadata/ledger only.
- Isolated weight validation is available via `mcp.venv/bin/python scripts/validate_muadib_self_play_weights.py --json`. It uses a temporary `DigitalTwinTool(data_dir=...)`, writes real `.safetensors` candidates, verifies archive-only and locked-promotion semantics, and avoids `MCPServer`/canonical data/output-adapter side effects.
- Full one-plane validation is available via `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json`. The runner composes self-play weights, source gate, runtime identity audit, optional live health, and then refreshes the generated completion audit. After MCP reload, add `--live-health-json <health.json> --require-live` to make the same suite a strict completion gate.
- Requirement-by-requirement completion status is generated by `scripts/write_muadib_completion_audit.py` and lives in `docs/validation/2026-06-04-muadib-completion-audit.md` / `.json`. After the Codex/MCP gateway reboot on 2026-06-04 and the display projection cleanup, strict source+live validation passed: source checks `23`, display checks `31`, self-play checks `15`, source+live gate checks `29`, `completion_ready=true`, and `live_status=PASS`.
- The existing autonomous exo cycle now calls bounded Muad'Dib self-play on a cadence without changing `mcp_server.py` output formatting. Defaults: `MUADIB_SELF_PLAY_ENABLED=1`, `MUADIB_SELF_PLAY_INTERVAL_CYCLES=32`, `MUADIB_SELF_PLAY_EPISODES=4`, `MUADIB_SELF_PLAY_MAX_STEPS=3`, `MUADIB_SELF_PLAY_PROMOTE=0`, `MUADIB_SELF_PLAY_LOCK_ACTIVE=0`, `MUADIB_SELF_PLAY_UPDATE_QTABLE=0`. Safetensors locks the storage/integrity boundary; continuous self-play archives candidate weights by default and advances active/champion weights only when promotion is explicitly allowed.
- Human display cleanup is now handled by `mcp_server.py` at the final `_format_tool_result(...)` seam. Dict/list payloads render as compact Markdown key facts with a raw fingerprint and display-only metadata (`not_for_qtable`, `not_for_observations`, `not_for_distillation`, `not_for_rft`); preformatted MCP `content` blocks pass through unchanged; `SOVEREIGN_DISPLAY_PROJECTION=raw` restores canonical raw JSON display. Validate with `mcp.venv/bin/python scripts/validate_display_projection.py --json`.
- `TRASH/MAYBE-TOOLS/intelligent_automation_tool.py` is not registered because `tools/auto_tool_module.py` already owns the automation/optimization surface.
- `TRASH/MAYBE-TOOLS/ai_system_integration.py` is blocked on Linux until rewritten behind platform guards.

## Golden Path Operating Posture

Do not run bootstrap/category scans as a ritual. Use the live BB7 plane according to task scope:

- cold workspace entry: load/recover context;
- uncertain or multi-step work: route/plan/intend;
- direct targeted work: execute the relevant BB7 surface;
- after substantive work: call `bb7_exo_reflect` so the substrate learns.

## Data Root and Persistence

Canonical persistence root for this workspace/runtime:

- `/home/daeron/Somnus-MCP/data`

All major state persists under this root: memory, sessions, exoskeleton, planner, distillation, logs, event streams, digital twin observations, and Q-table state.

## Development and Validation

Use the repo venv for Python checks:

```bash
mcp.venv/bin/python -m py_compile tools/file_tool.py tools/lisan_al_gaib.py tools/exoskeleton_tool.py tools/meta_intelligence_engine.py mcp_server.py
mcp.venv/bin/python -m py_compile muadib/neural_config.py muadib/muaddib.py
mcp.venv/bin/python scripts/validate_display_projection.py --json
mcp.venv/bin/python scripts/verify_muadib_one_plane_gate.py
mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json
mcp.venv/bin/python scripts/write_muadib_completion_audit.py --json
mcp.venv/bin/python -m json.tool golden_paths.json
mcp.venv/bin/python -m json.tool golden_paths_meta.json
mcp.venv/bin/python -m json.tool tool_manifest.json
```

Do not start/stop/restart or instantiate a parallel server for routine source/schema validation. Live runtime truth comes from the existing BB7/SovereignMCP plane (`ping_server`, `bb7_tool_health_report`, `bb7_lisan_intend`). Current-source health payloads include `runtime_identity` (`pid`, `ppid`, `session_id`, `transport`, canonical `data_dir`, source/control-file digests) plus deterministic `registered_tools` so source/live parity can be tied to the exact process and registry answering the call.

## Distillation Pipeline

The system implements a telemetry flywheel for Reinforcement Fine-Tuning:

- Captures cognitive trajectories from `bb7_agent_run` executions
- Logs to `data/distillation_dataset/trajectories_YYYY-MM-DD.jsonl`
- Auto-tags with heuristics: `contains_tool_error`, `deep_tool_chain`, `high_latency`
- Enables behavioral cloning on smaller models

See [Sovereign MCP Distillation Pipeline.md](Sovereign%20MCP%20Distillation%20Pipeline.md) for detailed schema.

## Additional Validation Notes

Historical test harnesses may still exist under `tests/`. When running them, use `mcp.venv/bin/python`, keep writes explicit, and do not create a second live cognition process unless the operator is intentionally performing server lifecycle work.

```bash
mcp.venv/bin/python tests/validate_exoskeleton_v1.py
mcp.venv/bin/python tests/validate_openrouter_planner_tool.py
```

## Known Kinks (Current Doctrine)

1. `bb7_agent_run` requires `OPENROUTER_API_KEY`; without it, live agent-run calls fail or should be dry-run/health-checked.
2. `visual_tool` can degrade in headless Linux environments without `DISPLAY`.
3. Exact live tool count, loaded modules, and registry surfaces are runtime snapshots; use `bb7_tool_health_report` instead of inferring from disk layout. For parity-sensitive work, inspect both `runtime_identity` and `registered_tools` before claiming the running process has loaded current source. Treat `unused_tools` as backward-compatible session-behavior evidence only.
4. Source/schema truth may be ahead of the already-running process until normal operator/server lifecycle reloads the live plane.
5. Display projection is a `mcp_server.py` formatter change. If the connected
   Codex/MCP process was already running when the source changed, live tool
   output can remain raw until the client/gateway reconnects even though source
   validation passes.

## Documentation Map

- [AGENTS.md](AGENTS.md): local runtime override for coding agents
- [workflows.md](workflows.md): autonomy-mode execution doctrine
- [CONTEXT.md](CONTEXT.md): rolling project state
- [MEMORY.md](MEMORY.md): durable lessons and decisions
- [MCP_SPEC.md](MCP_SPEC.md): expanded architecture and persistence details
- [Sovereign MCP Distillation Pipeline.md](Sovereign%20MCP%20Distillation%20Pipeline.md): RFT telemetry architecture

## License

MIT

## 2026-04-13: OpenRouter Distillation Pipeline Reactivation

- OpenRouter planner and agent surfaces now emit trajectory-level distillation records on every run.
- New async writer path lives in `databus/openrouter_wrapper.py` (`OpenRouterDistillationLogger`).
- Distillation output now dual-writes for compatibility:
  - `data/distillation_dataset/` (V2-oriented corpus + index/high-value/failure buckets)
  - `data/distillation/` (legacy shard continuity)
- `bb7_agent_run` and `bb7_planner_plan` responses now include `trajectory_id` for downstream review/export linking.
