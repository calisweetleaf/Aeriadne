# Somnus-MCP Architecture

**Date:** 2026-05-27  
**Runtime:** 24/7 autonomous neural-symbolic cognition server  
**Canonical data root:** `/home/daeron/Somnus-MCP/data`  
**Canonical Python environment:** `/home/daeron/Somnus-MCP/mcp.venv`

Somnus-MCP is not a passive MCP tool rack and not a coding-agent harness. MCP JSON-RPC2, stdio, SSE, HTTPS, and webhooks are transport surfaces into a single live cognition plane. The durable system is the BB7/Lisan/Muad'Dib neural-symbolic substrate plus the shared distributed cognition data root.

`mcp_server.py` is the gateway/dispatcher into the 4-7 Muad'Dib + `tools/` cognition layers, not the intelligence itself. It owns transport, registry assembly, raw JSON/result boundary preservation, telemetry, lifecycle plumbing, and final human-facing display projection. Neural weights, self-play, routing, reflection, memory synthesis, and higher-order answer compilation belong in `muadib/` and `tools/`.

## 1. Architectural Invariants

1. **One cognition/data plane**: all clients and agents must route into the same 24/7 Muad'Dib + `tools/` substrate and canonical data root. Persistent transports should share one gateway process; stdio clients may spawn per-client gateway children, but those gateways must not fork data/neural state.
2. **One distributed cognition root**: `/home/daeron/Somnus-MCP/data` holds memory, sessions, exoskeleton state, Muad'Dib digital twin state, distillation traces, optimization state, and cross-agent activity.
3. **One validation environment**: Python validation uses `mcp.venv/bin/python`. Do not use system Python for runtime checks.
4. **No duplicate tool planes**: modules integrated into `tools/` must bind to the live registry or expose new surfaces directly. They must not instantiate sibling tools and fork state.
5. **Source/schema truth vs live runtime truth**: source edits and `tool_manifest.json` can be validated without a restart; the already-running process reports live truth through BB7/SovereignMCP. If it does not hot-reload, live parity is pending operator lifecycle.
6. **Gateway thinness**: changes to `mcp_server.py` should be gateway-level only unless proven otherwise. Do not move neural/control-plane ownership into the gateway merely because a transport/display issue is visible there.
7. **Display projection is not substrate truth**: cleaned Markdown summaries are emitted only at the final MCP `content` seam. Raw dict/list payloads remain the inputs for trajectory buffers, tool usage logs, event-spine summaries, ambient memory exchange, sovereign metadata, auto-reflect, Q-table observations, and RFT/distillation. `SOVEREIGN_DISPLAY_PROJECTION=raw` is the escape hatch for canonical raw JSON display.

## 2. Layer Model

```text
Transport wrappers
  ├── JSON-RPC2 / stdio
  ├── Streamable HTTP / SSE
  ├── HTTPS wrapper
  └── webhook engine
        ↓
mcp_server.py
  ├── dynamic tool discovery
  ├── canonical data-root enforcement
  ├── async invocation bridge
  ├── ambient memory/session exchange
  ├── live registry + health telemetry
  └── human display projection after raw-substrate capture
        ↓
BB7 compiled capability surfaces
  ├── files / shell / web / project context / analysis
  ├── memory continuity surfaces
  ├── session continuity surfaces
  ├── exoskeleton / Lisan routing surfaces
  └── registry-bound meta-intelligence facade
        ↓
Neural-symbolic routing/planning substrate
  ├── tools/exoskeleton_tool.py
  ├── tools/lisan_al_gaib.py
  └── muadib/*
        ↓
Shared persistence plane
  └── /home/daeron/Somnus-MCP/data
```

## 3. Continuity Substrate

These files are public surfaces over persistent cognition, not ordinary stateless utilities:

| File | Runtime role |
|---|---|
| `tools/memory_tool.py` | Working-memory LRU, persistent long-term memory, BM25/Ebbinghaus surfacing, context resurrection support. |
| `tools/memory_interconnect.py` | BM25 concept graph, memory relationships, clustering, consolidation, knowledge-gap detection. |
| `tools/session_manager_tool.py` | Cognitive session state, event/insight capture, workflow records, cross-session pattern and intelligence layer. |

Every substantial integration must preserve these modules as shared substrate over `/home/daeron/Somnus-MCP/data`. Creating a local `./data` island or instantiating duplicate continuity modules is architectural drift.

## 4. Routing and Planning Substrate

| File | Runtime role |
|---|---|
| `tools/exoskeleton_tool.py` | BB7 control plane: route, plan, reflect, live catalog sync, SessionMomentum integration, golden-path learning. |
| `tools/lisan_al_gaib.py` | Spectral intent decomposition, GoldenPathOracle, Thompson/MCTS machinery, distillation hooks, session-momentum primitives. |
| `muadib/muaddib.py` | DigitalTwinTool, Q-table backbone, observation buffer, 512-dimensional tool-catalog embedding API. |
| `muadib/advanced_bridge.py` | Provenance-tagged advanced feature bridge blending trained Q/co-occurrence signal while downweighting untrained sources. |
| `muadib/aeron_neural_memory.py` | Neural substrate tokenizer/backbone when torch is available. |
| `muadib/neural_config.py` | Neural primitive/config surface, including `NeuralNetConfig`, `SelfPlayConfig`, and the isolated `MuadDibSelfPlayHead`. |

Self-play/weight checkpoint invariant:

- JSON is metadata/ledger only; neural tensor weights live in `.safetensors`.
- Continuous self-play trains a candidate `MuadDibSelfPlayHead` and writes a complete safetensors checkpoint. Autonomous cadence archives candidates by default (`MUADIB_SELF_PLAY_PROMOTE=0`); active/champion weights advance only by explicit promotion when promotion is allowed. `bb7_dt_self_play_lock` or `MUADIB_SELF_PLAY_LOCK_ACTIVE=1` pins the active pointer/reference while candidates continue accumulating.
- Legacy tokenizer `.pt` checkpoints remain load-only migration fallback; new tokenizer saves prefer `checkpoint_vN.safetensors`.
- Synthetic self-play does not update the real Q-table unless `update_qtable=true` is explicitly requested.
- The existing `mcp_server.py` autonomous exo cycle runs bounded self-play on cadence through `exo.bb7_dt_self_play(...)`; it does not alter JSON-RPC response formatting or display-boundary cleanup.
- `scripts/validate_muadib_self_play_weights.py` is the safe isolated validation path for the weight lane. It uses a temporary `DigitalTwinTool(data_dir=...)`, not `MCPServer`, so it can prove safetensors archive/lock behavior without mutating canonical runtime artifacts.
- `scripts/validate_display_projection.py` is the safe display-seam validator. It uses `object.__new__(MCPServer)` formatter smoke tests plus static source ordering checks to prove projection happens after raw telemetry/memory/Q/RFT substrate paths, and it writes `docs/validation/2026-06-04-display-projection.*`.
- `scripts/run_muadib_one_plane_validation.py` is the suite runner for the active one-plane gate. It composes the self-play validator, display projection validator, source gate, runtime audit, and optional post-reload live health JSON; it does not instantiate `MCPServer`, restart/signals runtime, or mutate output adapters.
- Cadence knobs: `MUADIB_SELF_PLAY_ENABLED`, `MUADIB_SELF_PLAY_INTERVAL_CYCLES`, `MUADIB_SELF_PLAY_EPISODES`, `MUADIB_SELF_PLAY_MAX_STEPS`, `MUADIB_SELF_PLAY_PROMOTE`, `MUADIB_SELF_PLAY_LOCK_ACTIVE`, `MUADIB_SELF_PLAY_UPDATE_QTABLE`.

The exoskeleton route/plan/reflect loop should be used when it adds routing value. It is not a ritual checklist. `bb7_exo_reflect` remains critical after real work because it updates priors and teaches the substrate.

## 5. Executable Routing Configuration

`golden_paths.json` is executable workflow configuration only. It contains valid workflow entries with chains and numeric priors. Audit notes and historical metadata live in `golden_paths_meta.json`.

Runtime hardening now exists in both Lisan and exoskeleton:

- metadata keys such as `_meta` are filtered out;
- malformed workflow entries are skipped;
- spectral indexes and chain priors are built from executable entries only;
- auto-promotion writes valid workflow entries without corrupting metadata.

## 6. File Capability Surface

`tools/file_tool.py` is the promoted advanced `FileTool` surface with old compatibility names preserved.

Existing names retained:

- `bb7_read_file`
- `bb7_write_file`
- `bb7_append_file`
- `bb7_list_directory`
- `bb7_search_files`
- `bb7_get_file_info`
- `bb7_file_cache_stats`

New advanced names:

- `bb7_copy_file`
- `bb7_move_file`
- `bb7_delete_file`
- `bb7_file_info`
- `bb7_operation_history`

Compatibility rules:

- `bb7_read_file` returns raw content by default; analysis/decorated output is opt-in.
- `bb7_get_file_info` aliases `bb7_file_info`.
- `bb7_file_cache_stats` is a shim over operation-history state because the legacy content cache is removed.
- `bb7_search_files` accepts both legacy `pattern` and new `name_pattern`.
- destructive directory delete or no-backup delete requires `force=true`.

## 7. Meta-Intelligence Integration Policy

| Candidate | Current decision | Reason |
|---|---|---|
| `TRASH/MAYBE-TOOLS/meta_intelligence_engine.py` | Integrated as `tools/meta_intelligence_engine.py` after refactor | Now registry-bound through `attach_tool_plane(tools, tool_modules)`; no sibling tool imports or duplicate instantiation. |
| `TRASH/MAYBE-TOOLS/intelligent_automation_tool.py` | Not copied into `tools/` | `tools/auto_tool_module.py` already owns the automation/optimization surface with richer schemas. |
| `TRASH/MAYBE-TOOLS/ai_system_integration.py` | Blocked | Windows-only eager imports (`winreg`, `win32*`, `wmi`) and unfinished/destructive surfaces are unsafe on Linux. |

The meta-intelligence facade exposes implemented registry-bound surfaces:

- `bb7_code_consciousness`
- `bb7_context_weaver`
- `bb7_creative_problem_solver`
- `bb7_muadib_mentat_bridge`

`bb7_muadib_mentat_bridge` is intentionally read-only. It combines live BB7 registry calls for Muad'Dib/exoskeleton state with bounded Mentat sidecar reads (`~/.mentat` and workspace `.mentat/scope.md`) while preserving the one-plane invariant: no sibling tool instantiation, no second server, no Muad'Dib weight mutation, no Q-table mutation, and no `mcp_server.py` output adapter changes. Its contract also exposes gateway doctrine: `mcp_server.py` is gateway/dispatcher into Muad'Dib/tools, not the intelligence or cognition-plane owner.

`bb7_tool_refresh_module` is the guarded source/live parity mechanism for this facade lane. It is allowlisted for `meta_intelligence_engine` only, rebuilds the facade in the existing server instance, reattaches registry-bound facades, resyncs exoskeleton catalog, and avoids rerunning boot lifecycle side effects such as autonomous-cycle startup. It is not a general module reload system.

## 8. Validation Boundary

Use source/schema validation for code edits:

```bash
mcp.venv/bin/python -m py_compile tools/file_tool.py tools/lisan_al_gaib.py tools/exoskeleton_tool.py tools/meta_intelligence_engine.py mcp_server.py
mcp.venv/bin/python -m py_compile muadib/neural_config.py muadib/muaddib.py
mcp.venv/bin/python -m json.tool golden_paths.json
mcp.venv/bin/python -m json.tool golden_paths_meta.json
mcp.venv/bin/python -m json.tool tool_manifest.json
```

Use the existing BB7/SovereignMCP plane for live truth:

- `ping_server`
- `bb7_tool_health_report`
- `bb7_lisan_intend`

For current-source live parity, `ping_server` and `bb7_tool_health_report` include `runtime_identity` with process/session/source-control fingerprints. `bb7_tool_health_report` also includes deterministic `registered_tools`; use it as the registry proof for post-reload gates, with `unused_tools` retained only as backward-compatible session-behavior evidence. Do not treat an old healthy stdio child as current-source merely because it shares the canonical data root.

Do not instantiate a parallel `MCPServer()` or start/stop/restart the server as part of validation.
