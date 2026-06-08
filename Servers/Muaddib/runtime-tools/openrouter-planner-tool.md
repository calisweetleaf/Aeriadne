### OpenRouter Planner Tool (`openrouter_planner_tool.py`)

> **Doctrine.** This module is the **L1/L2 planner facade** — it composes
> OpenRouter chat completions into structured execution plans and persists
> every run to `data/planner/runs.jsonl` and `data/planner/state.json` for
> audit. The planner is **read-only** with respect to workspace state; it
> emits plans, not actions. Plan execution must be requested by the calling
> agent through a separate tool.
>
> **Pairing.** Sits alongside `openrouter_agent_tool.py`
> (`runtime-tools/openrouter-agent-tool.md`) for the execution plane. The
> planner emits a JSON plan; the agent dispatcher runs it. Also pairs with
> `meta_intelligence_engine.bb7_creative_problem_solver` for upstream
> decomposition — problem decomposition feeds the planner's `intent`
> parameter.
>
> **OpenRouter posture (per AGENTS.md):** `scripts/start_server.sh` sources
> a root `.env` before launching `mcp_server.py`. `databus/openrouter.yaml`
> defaults to `elephant-alpha` and keeps `routing.fallback_chain` empty by
> design. Live planner calls require a real `OPENROUTER_API_KEY`; use
> `bb7_planner_health` for key/model/base-URL validation, and
> `dry_run=true` on `bb7_planner_plan` to preview the request payload
> without consuming API quota.

| Subsystem / Class | Role |
|---|---|
| `OpenRouterPlannerTool` | Public façade. Owns `data/planner/`, the in-memory `_state`, and the live OpenRouter config. |
| `PlannerNotConfiguredError` | Raised when `OPENROUTER_API_KEY` is missing. |
| `PlannerModelExhaustedError` | Raised when retries are exhausted. |
| `_load_state` / `_save_state` | Persistent planner state (total_runs, successful_runs, failed_runs, last_updated). |
| `_append_jsonl` | Atomic append to `runs.jsonl` for full run history. |
| `_hydrate_env_from_dotenv` | Pulls env vars from a local `.env` if present. |
| `_openrouter_config` | Resolves `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL` (with `model_override` per call). |
| `_default_plan_template` | Builds the system-prompt + user-prompt template for a given intent. |
| `_parse_json_or_fallback` | Strict JSON parse of model output; falls back to wrapped Markdown if the model ignores the no-markdown directive. |
| `_log_planner_distillation` | Records distilled step sequences to `runs.jsonl` for replay. |

**Storage paths:** `data/planner/state.json` (counters), `data/planner/runs.jsonl`
(full run history with trajectory steps).

---

#### `bb7_planner_health`

Return OpenRouter planner configuration and persistence health. Safe
to call without a configured API key — only `api_key_configured` will
be `false`.
**Internal Composition**: Calls `OpenRouterPlannerTool.bb7_planner_health()`.
Reads the live OpenRouter config and the in-memory `_state` counters.

- **Parameters**: None.

#### `bb7_planner_template`

Generate a reusable planner prompt template for a target intent. Useful
for previewing what the planner will send to OpenRouter before consuming
API quota. Returns the rendered template as a string.
**Internal Composition**: Calls `OpenRouterPlannerTool.bb7_planner_template()`.
Composes `_default_plan_template(intent, context, max_steps)`.

- **Parameters**:
  - `intent` (string, required): Target intent to plan for.
  - `context` (string, optional): Optional context to include in the template.
  - `max_steps` (number, optional): Maximum number of plan steps, clamped 1–20 (default: 8).

#### `bb7_planner_plan`

Generate a structured execution plan using OpenRouter. The primary
planner surface — call this when you need a JSON execution plan from
a free-form intent.
**Internal Composition**: Calls `OpenRouterPlannerTool.bb7_planner_plan()`.
Builds the request payload (system prompt + user prompt), calls the
OpenRouter `/chat/completions` endpoint with bounded retries, parses
the response via `_parse_json_or_fallback`, persists the full trajectory
to `runs.jsonl`, and updates `_state` counters.

- **Parameters**:
  - `intent` (string, required): What should be planned.
  - `context` (string, optional): Additional planning context.
  - `constraints` (string, optional): Optional constraints for the plan.
  - `max_steps` (number, optional): Maximum steps allowed in returned plan, clamped 1–20 (default: 8).
  - `model` (string, optional): Optional OpenRouter model override (e.g. switch from `elephant-alpha` for a specific run).
  - `temperature` (number, optional): Model temperature 0.0–1.0 (default: 0.2).
  - `retries` (number, optional): Retry count for transient request failures, clamped 0–5 (default: 2).
  - `timeout` (number, optional): Request timeout in seconds, clamped 5–180 (default: 45).
  - `dry_run` (boolean, optional): If true, do not call the API and return the payload preview only (default: false).
