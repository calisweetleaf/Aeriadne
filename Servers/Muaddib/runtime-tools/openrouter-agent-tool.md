### OpenRouter Agent Execution Plane (`openrouter_agent_tool.py`)

`tools/openrouter_agent_tool.py` exposes the BB7 multi-agent execution surface backed by OpenRouter. It is not a planner-only facade: `bb7_agent_run` asks an OpenRouter model for structured JSON steps, then can execute real registered MCP `bb7_*` tools through the live server registry when `execute_tools=true`.

Runtime role:
- Creates execution nodes under the shared canonical data root.
- Shares the same tool registry that `mcp_server.py` assembled for the live process.
- Supports cross-agent handoff files and message channels.
- Logs agent runs and distillation trajectories for later learning.
- Requires `OPENROUTER_API_KEY` only for live model-backed runs; health/list/status surfaces remain usable without a key.

#### Runtime registration and tool execution

`mcp_server.py` loads this module during dynamic tool discovery, then calls `OpenRouterAgentTool.register_tools(self.tools)` after registration completes. That gives the agent plane callable access to the current MCP tool map.

Important execution behavior:
- Tool invocation is registry-bound, not a sibling server or duplicate tool plane.
- `_execute_tool_call()` returns an error object when the registry is unavailable or a requested tool name is unknown.
- `_invoke_tool_callable()` tries no-arg, kwargs, and dict-style invocation and awaits async results.
- `execute_tools=false` keeps the model loop from actually calling MCP tools, but still records model iterations.

#### Configuration

OpenRouter configuration is resolved at call time from environment and repo `.env` values without overriding existing process variables.

| Setting | Purpose | Default / fallback |
|---|---|---|
| `OPENROUTER_API_KEY`, `OPENROUTER_KEY`, `OR_API_KEY` | Required secret for `bb7_agent_run`. | No default; missing key raises `AgentNotConfiguredError`. |
| `OPENROUTER_AGENT_MODEL`, `OPENROUTER_MODEL` | Agent model override. | `elephant-alpha` |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL. | `https://openrouter.ai/api/v1` |
| `OPENROUTER_APP_NAME` | App title sent to OpenRouter. | `SovereignMCP Agent` |
| `OPENROUTER_SITE_URL` | Site URL sent to OpenRouter. | `https://localhost` |

The lazy OpenRouter client is created from `databus/openrouter.yaml` via `SovereignOpenRouterClient.create(...)`.

#### Persistence

All agent-plane state resolves through `SOVEREIGN_DATA_DIR`, then `MCP_DATA_DIR`, then `/home/daeron/Somnus-MCP/data`.

| Path | Write pattern | Purpose |
|---|---|---|
| `data/agents/agent_state.json` | Atomic temp + `os.replace` | Aggregate run counters and last update timestamp. |
| `data/agents/agent_runs.jsonl` | Append JSONL | Per-run summary with status, model lineage, tool counts, duration, and `trajectory_id`. |
| `data/agents/nodes/{node_id}.json` | Atomic temp + `os.replace` | Latest state for each execution node. |
| `data/agents/messages/{channel}.jsonl` | Append JSONL | Shared cognitive message channels such as `executions`, `errors`, and `handoffs`. |
| `data/agents/handoffs/{agent}_pending.json` | Direct JSON overwrite | Pending handoff context for a target agent type. |
| `data/distillation_dataset/*.jsonl` and legacy `data/distillation/*.jsonl` | OpenRouter distillation logger | Lossless trajectory capture from `bb7_agent_run`. |

#### Agent types

| Agent type | Description | Default max iterations | Main tool posture |
|---|---|---:|---|
| `planner` | Multi-step execution planning with tool execution. | 50 | Context resurrection, workspace loading, routing/planning, memory/session writes, agent handoff/call. |
| `debugger` | Error diagnosis with tool execution. | 30 | Memory recall/search, system/process/shell diagnostics, code/security analysis, screenshots, handoff/call. |
| `analyzer` | Deep code analysis with execution. | 20 | Memory recall/store, code/project/security analysis, file search/read, event logging, handoff/call. |
| `doc` | Documentation generation with execution. | 15 | Memory recall/search/store, project/file/code analysis, dependency/recent-change reads, event logging, handoff. |

#### `bb7_agent_health`

Return OpenRouter agent-plane health and configuration visibility.

**Internal Composition**: Calls `_openrouter_config()` after `.env` hydration, reports canonical directories, API-key presence, selected model, registered-tool count, available agent configs, and aggregate run counters.

- **Parameters**: none.
- **Returns**: `status`, `canon_data_dir`, `agents_dir`, `nodes_dir`, `messages_dir`, `api_key_configured`, `model`, `tools_registered`, `available_agents`, `agent_configs`, and `state` counters.

#### `bb7_agent_list`

List all configured agent types and their allowed tool sets.

**Internal Composition**: Reads static `AGENT_CONFIGS` for descriptions, tool lists, and max-iteration defaults.

- **Parameters**: none.
- **Returns**: `agents` keyed by `planner`, `debugger`, `analyzer`, and `doc`.

#### `bb7_agent_capabilities`

Return the detailed capability contract for one agent type.

**Internal Composition**: Validates `agent_type` against `AGENT_CONFIGS` and returns that agent's description, tool allowlist, and iteration limit.

- **Parameters**:
  - `agent_type` (string, required): `planner`, `debugger`, `analyzer`, or `doc`.
- **Error behavior**: Unknown agent types return `status=error` with the available agent list.

#### `bb7_agent_nodes`

List execution-node state files from the shared cognitive plane.

**Internal Composition**: Scans `data/agents/nodes/*.json` and returns successfully decoded node-state payloads.

- **Parameters**: none.
- **Returns**: `nodes` and `count`.

#### `bb7_agent_messages`

Read agent-plane messages from a channel JSONL file.

**Internal Composition**: Reads `data/agents/messages/{channel}.jsonl` and filters messages by timestamp.

- **Parameters**:
  - `channel` (string, optional): Message channel to read. Defaults to `general`.
  - `since` (number, optional): Unix timestamp filter. Defaults to `0`.
- **Returns**: `messages`, `channel`, and `count` when the channel exists; empty messages when it does not.

#### `bb7_agent_handoff`

Write pending handoff context for another agent type.

**Internal Composition**: Validates the target agent, then writes `data/agents/handoffs/{to_agent}_pending.json` with `from_agent`, `to_agent`, `context`, `task`, and timestamp.

- **Parameters**:
  - `to_agent` (string, required): Target agent type.
  - `context` (string, required): Context being passed forward.
  - `task` (string, required): Follow-up task for the target agent.
- **Error behavior**: Unknown target agent returns `status=error`.

#### `bb7_agent_call`

Return a non-blocking call acknowledgement for another agent type.

**Internal Composition**: Validates the target agent and returns a queued-task acknowledgement. Current implementation does not create a node or execute the target agent inline.

- **Parameters**:
  - `agent_type` (string, required): Target agent type.
  - `task` (string, required): Task description.
  - `context` (string, optional): Optional additional context.
- **Error behavior**: Unknown target agent returns `status=error`.

#### `bb7_agent_run`

Run an OpenRouter-backed agent loop with optional real MCP tool execution.

**Internal Composition**: Builds an execution prompt from `AGENT_CONFIGS`, calls `SovereignOpenRouterClient.complete(...)`, parses the model's JSON response, optionally executes the selected MCP tool through the registered live tool map, publishes execution/error messages, saves node state, appends a run record, and logs a distillation trajectory.

- **Parameters**:
  - `agent_type` (string, required): `planner`, `debugger`, `analyzer`, or `doc`.
  - `task` (string, required): Task to execute.
  - `context` (string, optional): Prior context injected into the loop.
  - `model` (string, optional): Per-run model override.
  - `temperature` (number, optional): Clamped to `0.0` through `1.0`; default `0.3`.
  - `max_iterations` (number, optional): Overrides the agent default.
  - `execute_tools` (boolean, optional): Execute selected MCP tools when true; default `true`.
- **Hard gate**: Raises `AgentNotConfiguredError("OPENROUTER_API_KEY not set")` when no key is configured.
- **Return shape on success**: `status=ok`, `node_id`, `agent_type`, `task`, `iterations`, `tools_executed`, `canon_data_dir`, `final_phase`, `all_results`, and `trajectory_id`.
- **Return shape on caught runtime error**: `status=error`, `error`, `iterations`, and `trajectory_id`.

#### `bb7_agent_status`

Return currently active in-memory execution nodes.

**Internal Composition**: Reads `self._active_nodes`, not the persisted node directory.

- **Parameters**: none.
- **Returns**: `active_nodes`, `canon_data_dir`, and `total_nodes`.

#### Operational caveats

- Use `bb7_agent_health` before `bb7_agent_run` to confirm `api_key_configured=true`, selected model, and nonzero `tools_registered`.
- A healthy source file does not prove the live process has reloaded it; live truth comes from `bb7_tool_health_report` and `bb7_agent_health`.
- `bb7_agent_run` can cause real tool side effects because it executes registered MCP tools when `execute_tools=true`.
- Distillation capture is part of the agent run path; do not treat the human-facing display projection as the raw trajectory payload.
