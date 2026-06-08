### Meta Intelligence Engine (`meta_intelligence_engine.py`)

> **Doctrine.** The Meta Intelligence Engine is the **registry-bound
> orchestrator** — it never instantiates sibling tools, never mutates server
> lifecycle, and never touches Q-table state, output adapters, or model
> weights. It is explicitly designed as a **read-only synthesis plane** that
> calls live `bb7_*` tools through the registered tool table, gathers their
> outputs, and emits bounded JSON reports. All four surfaces here are
> cross-tool composition calls; none of them is a single-tool invocation.
>
> **Pairing.** Upstream of everything. `bb7_code_consciousness` composes
> `bb7_analyze_code_complete` + `bb7_analyze_project_structure` + memory
> search + `bb7_lisan_recall`. `bb7_context_weaver` composes
> `bb7_workspace_context_loader` + `bb7_lisan_recall` + `bb7_auto_session_resume`
> + memory insights + recent changes. `bb7_creative_problem_solver` composes
> `bb7_lisan_intend` + memory search. `bb7_muadib_mentat_bridge` is the
> only read-only diagnostic surface that crosses plane boundaries
> (Muad'Dib + exoskeleton + Mentat).
>
> **Soft-degrade contract:** When a called tool is missing from the registry
> (e.g., Lisan or Muad'Dib not initialised), the call returns a JSON
> `{"available": false, "skipped": true, "reason": "..."}` entry — the
> overall surface still returns a valid JSON report with whichever sources
> were available. The agent never crashes on a missing dependency.

| Subsystem / Class | Role |
|---|---|
| `IntelligentToolOrchestrator` | Public façade. Holds the live `tools` registry reference and the `data_dir`. |
| `attach_tool_plane` | Injects the live tool registry at boot. |
| `_coerce_arguments` / `_tool_callable` / `_invoke_live_tool` | Argument normalisation and live-tool invocation with tool-existence guard. |
| `_first_available_call` | Tries a list of tool names in priority order, returns the first successful result. |
| `_compact_result` / `_json` | Bounded result serialisation (default 6000 chars). |
| `_read_json_path` / `_read_text_path` / `_tail_jsonl_path` | Bounded file reads (max 5000 chars text) for bridge snapshot assembly. |
| `_synthesize_architectural_intent` | Composes the code/structure/memory/lisan sources into a single architectural-understanding report. |
| `_synthesize_context_state` | Composes workspace/recall/session/memory/changes into a continuity state. |
| `_decompose_problem` | Splits a free-form problem into bounded subproblems using `_lens_for_sentence`. |

---

#### `bb7_code_consciousness`

Architectural and contextual understanding through the live BB7 plane.
The "what is this file/role, and what does the project think of it?"
surface — call it before deciding whether to refactor, extend, or
deprecate a module.
**Internal Composition**: Calls `IntelligentToolOrchestrator.bb7_code_consciousness()`.
Composes `bb7_analyze_code_complete` (only if the target is a single Python
file) + `bb7_analyze_project_structure` + `bb7_memory_intelligent_search`
(or `bb7_memory_search` fallback) + `bb7_lisan_recall`. Synthesises
the four sources via `_synthesize_architectural_intent`.

- **Parameters**:
  - `operation` (string, optional): Must be `"understand_intent"` (default: `"understand_intent"`).
  - `file_path` (string, optional): Target file or directory (default: `"."`).
  - `query` (string, optional): The intent question (default: derived from `file_path`).
  - `max_depth` (integer, optional): Max directory depth for project structure (default: 3).
  - `max_memories` (integer, optional): Max memories to surface per call (default: 5).
  - `include_hidden` (boolean, optional): Include hidden files in project structure walk (default: false).

#### `bb7_context_weaver`

Synthesise workspace, memory, session, and recent-changes context into
a single continuity report. The "where am I and what's been happening?"
surface — call it at the start of a session to recover the prior
working state.
**Internal Composition**: Calls `IntelligentToolOrchestrator.bb7_context_weaver()`.
Composes `bb7_workspace_context_loader` + `bb7_lisan_recall` +
`bb7_auto_session_resume` + `bb7_memory_get_insights` (or
`bb7_memory_surface_context` fallback) + `bb7_get_recent_changes`.

- **Parameters**:
  - `operation` (string, optional): Must be `"synthesize_context"` (default: `"synthesize_context"`).
  - `context` (string, optional): Free-form context to synthesise (default: `"current workspace continuity"`).
  - `task` (string, optional): Alias for `context`.
  - `workspace_path` (string, optional): Explicit workspace path.
  - `max_memories` (integer, optional): Max memories per source (default: 7).
  - `days` (integer, optional): Look-back window for recent changes (default: 7).

#### `bb7_creative_problem_solver`

Problem decomposition with Lisan intent analysis and memory context. The
"how do I break this into bounded subproblems?" surface — call it when
facing an underspecified or open-ended request that needs structured
sub-tasks before execution.
**Internal Composition**: Calls `IntelligentToolOrchestrator.bb7_creative_problem_solver()`.
Composes `bb7_lisan_intend` (intent analysis of the problem statement) +
`bb7_memory_intelligent_search` (or `bb7_memory_search` fallback). Splits
the problem into bounded subproblems via `_decompose_problem` with
`_lens_for_sentence` heuristics.

- **Parameters**:
  - `operation` (string, optional): Must be `"decompose_challenge"` (default: `"decompose_challenge"`).
  - `problem` (string, required): The problem statement to decompose.
  - `challenge` (string, optional): Alias for `problem`.
  - `prompt` (string, optional): Alias for `problem`.
  - `constraints` (array of strings or string, optional): Hard constraints on the decomposition.
  - `goals` (array of strings or string, optional): Goal statements to satisfy.
  - `max_memories` (integer, optional): Max memories per source (default: 5).

#### `bb7_muadib_mentat_bridge`

Read-only one-plane bridge snapshot across Muad'Dib checkpoint state,
exoskeleton health, and Mentat conductor artifacts. The only
`meta_intelligence_engine` surface that crosses plane boundaries — it
inspects the neural substrate, the control-plane, and the cognitive
substrate in a single call without mutating any of them.
**Internal Composition**: Calls `IntelligentToolOrchestrator.bb7_muadib_mentat_bridge()`.
Reads Muad'Dib checkpoint JSON, exoskeleton health markers, and Mentat
insight/handoff/scope JSONL files via bounded `_read_*_path` helpers
(5000 chars default). Returns a unified snapshot with all three planes
plus a `live_calls` block listing the last N exoskeleton dispatches.

- **Parameters**:
  - `operation` (string, optional): Must be `"snapshot"` (default: `"snapshot"`).
  - `workspace_path` (string, optional): Workspace to inspect.
  - `mentat_root` (string, optional): Mentat data root override.
  - `mentat_session_id` (string, optional): Mentat session id to inspect, or `"latest"` (default: `"default"`).
  - `max_insights` (integer, optional): Max insights to include (default: 8).
  - `max_handoff_chars` (integer, optional): Max characters from handoff payload (default: 5000).
  - `include_handoff` (boolean, optional): Include Mentat handoff payload (default: true).
  - `include_insights` (boolean, optional): Include Mentat insights (default: true).
  - `include_scope` (boolean, optional): Include Mentat scope state (default: true).
  - `include_live_calls` (boolean, optional): Include last N exoskeleton dispatches (default: true).
  - `exo_limit` (integer, optional): Max exoskeleton dispatches to include (default: 5).
  - `candidates` (array of strings or string, optional): Restrict snapshot to specific candidate names.
