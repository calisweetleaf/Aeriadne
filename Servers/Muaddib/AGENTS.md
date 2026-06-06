# AGENTS Override: Runtime Control Plane (Somnus-MCP)

## 0) Precedence

This file is the highest-priority local override for this workspace.
If any instruction in other local docs conflicts with this file, this file wins.

Primary objective: deterministic autonomous orchestration with explicit persistence and reflection.

You must use and read [ARCHITECTURE.md](file:///home/daeron/Somnus-MCP/ARCHITECTURE.md), [ARCHITECTURE_MAP.md](file:///home/daeron/Somnus-MCP/ARCHITECTURE_MAP.md), [MEMORY.md](file:///home/daeron/Somnus-MCP/MEMORY.md), [CONTEXT.md](file:///home/daeron/Somnus-MCP/CONTEXT.md), and [5-26-2026-muaddib-mcp-filetree.md](file:///home/daeron/Somnus-MCP/5-26-2026-muaddib-mcp-filetree.md) to navigate and enhance the map of the codebase as you go.

This is NOT an MCP server. It is a **24/7 autonomous tool neural network server** — always running, always learning, always scoring. `bb7_*` surface methods do not simply execute tasks; they **compile a smarter answer** by routing through the neural-symbolic stack (Q-table + Thompson bandit + SessionMomentum V3 + Muad'Dib bridge) before returning. Muad'Dib is fully tied into Lisan al-Gaib and runs continuously with one shared data dir.

## 1) Mission

Somnus-MCP is autonomy research infrastructure.
Coding is one capability surface, not the center.

Work in this repo should prioritize:

1. control-plane correctness,
2. reasoning continuity,
3. durable state,
4. documentation fidelity to runtime truth.

## 2) Runtime Truth (Current)

**One server. One `data/` dir. One `mcp.venv`.** All clients (Codex, Claude, Claude Code, custom agents) send calls to the same running process. You do not start or activate anything — you send it a call and it answers. The server has been running and training since January 2026.

- **venv:** `mcp.venv/` at project root — used by all callers. Torch 2.11.0+cpu, Python 3.12+.
- **data dir:** `data/` at project root (or `SOVEREIGN_DATA_DIR` if set). One dir, shared across all sessions and clients.
- **Q-table:** months of real tool-call observations. `data/digital_twin/qtable.json` + `observations.json`.

[mcp_server.py](file:///home/daeron/Somnus-MCP/mcp_server.py) is the active orchestration layer.

Gateway doctrine (2026-06-04): `mcp_server.py` is the gateway/dispatcher into the 4-7 Muad'Dib + `tools/` cognition layers. It is not the intelligence itself and should not become the heavy neural surface. Keep it thin around transport, registry, raw JSON boundaries, telemetry, and one-plane lifecycle; route neural/self-play/control-plane work into `muadib/` and `tools/`.

Display projection doctrine (2026-06-04): cleaned tool output belongs only at
the final human-facing MCP `content` display seam. Raw payloads must already
have passed through telemetry, ambient memory exchange, sovereign metadata,
Q-table/observation paths, and distillation/RFT capture before projection.
`SOVEREIGN_DISPLAY_PROJECTION=raw` restores canonical raw JSON display; never
feed the display projection back into Q-play, observations, or RFT as if it
were the original result.

### 2.1 Capability & Tool Modules

The server dynamically loads modules from the `tools/` directory. The active core modules include:

1. `memory_tool` — BM25 semantic storage and memory retrieval
2. `memory_interconnect` — Memory network relationship graphing and gap analysis
3. `file_tool` — Complete filesystem utilities and metadata statistics
4. `shell_tool` — Sandbox command execution and process lists
5. `enhanced_web_tool` — Fetch URLs, multi-engine search, and SEO auditing
6. `openrouter_planner_tool` — LLM-backed long-horizon planning facade
7. `openrouter_agent_tool` — Asynchronous multi-agent cognitive orchestration plane
8. `session_manager_tool` — Focus tracking, session telemetry, and pattern learning
9. `visual_tool` — OCR, template matching, window manipulation, and screenshots
10. `project_context_tool` — Project dependency extraction and structure summary
11. `auto_tool_module` — Autonomic performance/cognitive optimization experiments
12. `exoskeleton_tool` — Main control-plane router and execution checkpoint manager
13. `enhanced_code_analysis_tool` — AST-based Python analysis, data-flow analysis, and secure code run in RestrictedPython
14. `thought_journal_tool` — Chronological reasoning, decision tracking, and conflict detection

### 2.2 Security & Transport Layer

The system runs with a secure network wrap and automated hooks lifecycle:

- **HTTPS Security Wrapper ([https_wrapper.py](file:///home/daeron/Somnus-MCP/https_wrapper.py))**:
  - Implements API Key Bearer Authentication. The active API key is generated securely at startup and stored in `data/security/api_key.txt` with restrictive `0600` permissions.
  - Implements rate limiting (100 requests/minute default) with a background IP cleanup thread to prevent OOM.
  - Generates audit trails to `data/security/security.log`.
  - Exposes RESTful endpoints, SSE real-time streams (`/events` and `/mcp`), webhooks registration, OpenAPI spec (`/openapi.json`), and Claude configuration.
- **Webhook Dispatch Engine ([webhook_engine.py](file:///home/daeron/Somnus-MCP/webhook_engine.py))**:
  - Outbound delivery with HMAC-SHA256 payload signing.
  - Exponential backoff retries (3 attempts: 1s → 4s → 16s).
  - Idempotency key tracking on every payload.
  - Persistence in `data/security/webhooks.json` (active registrations) and dead-letter queue in `data/security/webhook_dead_letters.jsonl` (failed deliveries).
- **Hook Bridge ([hook_executor.py](file:///home/daeron/Somnus-MCP/hook_executor.py) / [HOOK_BRIDGE.md](file:///home/daeron/Somnus-MCP/HOOK_BRIDGE.md))**:
  - Unifies Claude Code hooks with the MCP state machine.
  - Discovers hooks centrally in `/home/daeron/Somnus-MCP/hooks_manifest.json` and auto-triggers executions in-process or via CLI on events: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, and `Stop`.

### 2.3 Neural Substrate (Muad'Dib)

Wired directly into the exoskeleton for telemetry scoring and MCTS value evaluation:

- `muadib/muaddib.py` — `DigitalTwinTool`, Q-table backbone, `bb7_dt_encode_catalog` (512-dim embedding API).
- `muadib/advanced_bridge.py` — `AdvancedModalityBridge` (provenance-tagged signal extraction: trained_q, trained_cooccur, untrained_embed).
- `muadib/neural_config.py` — `NeuralNetConfig`, `SubstrateConfig`.
- `muadib/aeron_neural_memory.py` — `NeuralSubstrateTokenizer` (active when torch available).

Neural-symbolic wiring status (as of 2026-05-23): **COMPLETE + ADVANCED BRIDGE ACTIVE**
- `subsystems=[mcts,thompson,session_momentum_v3]` active on every server boot.
- 110 tools encoded to 512-dim manifold M in 2 chunks at startup.
- MCTS planner: 100 simulations, 15% adversarial injection, Pareto-optimal selection.
- Thompson bandit: Beta posterior conditioned on category + neural Q-bonus.
- SessionMomentum V3: Wasserstein change-point detection, 7-signal manifold, active.
- Advanced bridge: provenance-tagged signal extraction, circuit-broken, fail-open — **always active** (set `MUADIB_ADVANCED_MODE=0` to emergency-disable only).
- New public surface: `bb7_dt_advanced_features` (exposed via exoskeleton wrapper).

## 3) The Golden Path (Per-Turn)

You are already in the tool plane. The exoskeleton, Muad'Dib, and Lisan are running.
Every tool call is observed, scored, and learned from. There is no startup ritual.

### 3.1 Anchor 1: Know Where You Are & Recover

- Read [AGENTS.md](file:///home/daeron/Somnus-MCP/AGENTS.md), [CONTEXT.md](file:///home/daeron/Somnus-MCP/CONTEXT.md), [MEMORY.md](file:///home/daeron/Somnus-MCP/MEMORY.md).
- Hook Bridge auto-triggers **`SessionStart`** hooks to resume state when initialized.
- Check prior work and rollouts:
  - `bb7_workspace_context_loader` when entering a workspace you haven't touched this session.
  - `bb7_auto_session_resume` to check for prior work — once per workspace entry.
  - History is synced automatically via the state machine ingesting global Codex history from `/home/daeron/.codex/history.jsonl`.
  - Execute `bb7_lisan_recall` when you need context resurrected.

### 3.2 Anchor 2: Walk the Path (Routing & Planning)

Use only task-relevant tools. Let the neural substrate guide routing.
- The Hook Bridge fires **`UserPromptSubmit`** on user input.
- Use `bb7_exo_route` or `bb7_exo_plan` to rank and select candidate tools using Thompson bandit Beta draws and MCTS simulations.
- Do NOT call bootstrap → categories → route as a ritual.

### 3.3 Anchor 3: Execution Lifecycle & Ambient Exchange

- Before executing any tool, Hook Bridge triggers **`PreToolUse`** to run security reminders and verification matchers.
- Run the compiled `bb7_*` capability surfaces. Under the hood:
  - Every tool execution result triggers an **Ambient Memory Exchange** cycle.
  - The result is indexed for concepts via `bb7_memory_analyze_entry` and auto-saved to memory with the key format `mcp_exchange::ses_{session_id}::{timestamp}::{tool_name}`.
- Hook Bridge triggers **`PostToolUse`** to clean output and inject neural attention weights.

### 3.4 Persist & Reflect

1. `bb7_capture_insight` / `bb7_memory_store` to save critical lessons.
2. `bb7_link_memory_to_session` / `bb7_log_event`.
3. `bb7_exo_reflect` — the critical learning step. Don't skip it after real work.
4. `bb7_exo_kpi_report` for long chains.
5. On graceful exit or ralph-loop resets, the Hook Bridge fires **`Stop`** to write handoffs and serialize state.

## 4) Journal Policy

External journal-first operation is deprecated.

Primary continuity path:
- `lisan` + memory/session persistence.

If legacy journal endpoints are available:
- treat as compatibility-only,
- never make them mandatory.

## 5) File Intelligence Doctrine

Primary comprehension path for source code:

1. `bb7_analyze_code_complete(file_path=...)`
2. `bb7_lisan_recall(context=...)`

Guidance:
- Do not default to shell text-dumping for understanding code.
- Use direct file reads when analyzer output is insufficient, especially for non-code artifacts.

## 6) Runtime Awareness

Always detect runtime context before acting (Linux vs Windows vs VPS).
Use host-safe paths and project `.venv` conventions.

Current canonical Linux data root:
- `/home/daeron/Somnus-MCP/data`

Do not create per-project persistence silos for BB7 state.

OpenRouter test posture:
- `scripts/start_server.sh` sources a root `.env` before launching `mcp_server.py`.
- `databus/openrouter.yaml` defaults to `elephant-alpha` and intentionally keeps `routing.fallback_chain` empty.
- Live `tools/openrouter_agent_tool.py` / `tools/openrouter_planner_tool.py` calls still require a real `OPENROUTER_API_KEY`; use health or dry-run validation until the key is populated locally.

## 7) Context and Memory Loop

Before substantial work:
1. Read [AGENTS.md](file:///home/daeron/Somnus-MCP/AGENTS.md).
2. Read [CONTEXT.md](file:///home/daeron/Somnus-MCP/CONTEXT.md).
3. Read [MEMORY.md](file:///home/daeron/Somnus-MCP/MEMORY.md).
4. Read [workflows-new.md](file:///home/daeron/Somnus-MCP/workflows-new.md) when relevant.

After major transitions:
1. Update [CONTEXT.md](file:///home/daeron/Somnus-MCP/CONTEXT.md) with current state.
2. Update [MEMORY.md](file:///home/daeron/Somnus-MCP/MEMORY.md) with durable lessons and decisions.
3. Extend [README.md](file:///home/daeron/Somnus-MCP/README.md) when architecture/contracts change.

Never delete [CONTEXT.md](file:///home/daeron/Somnus-MCP/CONTEXT.md) or [MEMORY.md](file:///home/daeron/Somnus-MCP/MEMORY.md).

## 8) Execution Guardrails

- Prefer reversible and auditable actions.
- Avoid destructive operations unless explicitly authorized.
- Keep architecture claims tied to active runtime registration, not stale manifest-only assumptions.
- For full validation passes, generate detailed terminal output plus markdown and JSON artifacts.
- **Fail LOUD**: All code, lifecycle steps, and imports must fail loud with explicit logs. No silent failures or swallowed exceptions.

<!-- OP_SOTA_SYNC_START: TOKEN_DENSITY_GOVERNOR -->
## 9) Token Density Governor

- **Echo Invariant:** MCP display output must not replicate filesystem state already known to the host or generated by the model. Full file echoes, verbose raw JSON, and broad unbounded payloads are context-compilation failures unless explicitly required for audit.
- **Sparse Return Enforcement:** File modifications should return verification manifests containing target path, bounded delta windows, liveness/validation status, and compact fingerprints. Unchanged file text must remain on disk.
- **Read Governor:** Large or naked file reads should return bounded `start_line`/`end_line` windows, semantic-target windows, or structural skeletons. Full raw reads require explicit `allow_large_raw=True` intent.
- **Projection Boundary:** Display projection is final human/model-facing presentation only. Raw payloads must remain preserved before projection for telemetry, memory exchange, Q-table/observation, and distillation/RFT capture.
- **Sub-Agent Context Protection:** Heavy sweeps, multi-file graph traces, and raw data profiling should execute in isolated workers or server-side stores that return semantic summaries to the primary high-context thread.
<!-- OP_SOTA_SYNC_END: TOKEN_DENSITY_GOVERNOR -->

## 10) Reference & Specification Maps

Refer to the following documents for comprehensive specifications and workflow guides:

- **Capability & Tool Workflows**: [workflows-new.md](file:///home/daeron/Somnus-MCP/workflows-new.md)
- **State Machine & Substrate Specifications**: [MCP_SPEC.md](file:///home/daeron/Somnus-MCP/MCP_SPEC.md)
- **JSON-Based Hook Integration**: [HOOK_BRIDGE.md](file:///home/daeron/Somnus-MCP/HOOK_BRIDGE.md)
- **HTTPS & Webhook Endpoints**: [docs/https_wrapper_endpoints.md](file:///home/daeron/Somnus-MCP/docs/https_wrapper_endpoints.md)
