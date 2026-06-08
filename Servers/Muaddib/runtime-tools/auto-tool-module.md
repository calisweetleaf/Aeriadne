### Intelligent Optimization Tools (`auto_tool_module.py`)

> **bb7_ doctrine:** `bb7_` is not the tool — it compiles a smarter tool. Each `bb7_*` method on this module is a composed *router* that fans intent into multiple internal helpers and, in four cases, into cross-module `bb7_*` methods owned by other tool files. Callers can chain `bb7_*` methods across files; the category map below documents which surface owns which method.

> **Pairing: this is the central capability router.** `auto_tool_module.py` does not own the `memory`, `project_context`, `execution`, or `web` `bb7_*` methods it lists in its category map — those are defined in [`memory-and-mem-interconnect`](memory-and-mem-interconnect.md), [`project-context-tool`](project-context-tool.md), [`shell-tool`](shell-tool.md) + [`vscode-terminal-tool`](vscode-terminal-tool.md), and [`enhanced-web-tool`](enhanced-web-tool.md) respectively. The four `auto_activation` methods on this module (`bb7_workspace_context_loader`, `bb7_show_available_capabilities`, `bb7_auto_session_resume`, `bb7_intelligent_tool_guide`) and the six `automation` methods are the only `bb7_*` methods defined in source here. Treat this file as the **router/orchestrator** that any operator's first-turn load should consult via `bb7_workspace_context_loader` → `bb7_show_available_capabilities` → `bb7_intelligent_tool_guide`.

> **Source-file ownership clarification (2026-06-06):** The `web` category references in the source `tool_categories` dict (lines 74-80) name two files — `enhanced_web_tool.py` and `web_tool.py` — but `web_tool.py` does **not exist** in `tools/`. All five `web` `bb7_*` methods are defined in `tools/enhanced_web_tool.py` (class `WebTool`). The category-map references to `web_tool.py` in this table are historical and should be read as `enhanced_web_tool.py`. Do not introduce a `tools/web_tool.py` to match the stale string.

#### Tool Category Map (`self.tool_categories`)

The category map (lines 47-89) is the authoritative cross-module index of `bb7_*` methods exposed by the runtime. **Bold** entries are defined in this file; others are cross-module references.

| Category | Methods (count) | Owner File |
|---|---|---|
| `auto_activation` | `bb7_workspace_context_loader`, `bb7_show_available_capabilities`, `bb7_auto_session_resume`, `bb7_intelligent_tool_guide` (4) | `auto_tool_module.py` (this file) |
| `memory` | `bb7_memory_store`, `bb7_memory_retrieve`, `bb7_memory_list`, `bb7_memory_search`, `bb7_memory_stats`, `bb7_memory_insights` (6) | `memory_tool.py` |
| `project_context` | `bb7_analyze_project_structure`, `bb7_get_project_dependencies`, `bb7_get_recent_changes`, `bb7_get_code_metrics` (4) | `project_context_tool.py` |
| `execution` | `bb7_run_command`, `bb7_terminal_run_command`, `bb7_terminal_status`, `bb7_terminal_environment` (4) | `shell_tool.py` + `vscode_terminal_tool.py` |
| `web` | `bb7_fetch_url`, `bb7_download_file`, `bb7_check_url_status`, `bb7_search_web`, `bb7_extract_links` (5) | `enhanced_web_tool.py` |
| `automation` | `bb7_analyze_workflow_patterns`, `bb7_performance_optimization`, `bb7_intelligent_automation`, `bb7_cognitive_optimization`, `bb7_optimization_results`, `bb7_adaptive_learning` (6) | `auto_tool_module.py` (this file) |

**Storage**: SQLite-backed at `data/optimization/patterns.db` (`workflow_patterns` + `optimization_insights`) and `data/optimization/performance.db` (`performance_metrics` + `optimization_experiments`). Recommendations cache at `data/optimization/recommendations.json`. Honors `SOVEREIGN_DATA_DIR` env var; defaults to `/home/daeron/Somnus-MCP/data`. Class: `IntelligentOptimizationTool`.

---

#### `bb7_workspace_context_loader`

Load workspace context, recent memory keys, active/paused session counts, and tool-inventory hints in a single line-oriented report. This is the canonical **SessionStart** entry point.

**Internal Composition**: Detects project type from marker files (`.git`, `requirements.txt`, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`); reads `data/memory_store.json` to extract the 8 most recent memory keys with timestamps; globs `data/sessions/*.json` and buckets by `status` field into `active` vs `paused`; reports `len(self.tool_categories)` and the total unique tool count derived from the category map; emits `next_step: run bb7_show_available_capabilities for category map`. If `workspace_path` is supplied but does not exist, it falls back to `Path.cwd()` and reports the fallback.

- **Parameters**:
  - `workspace_path` (string, optional): Explicit workspace path. Resolved absolute or relative to process cwd. Falls back to cwd if missing.
  - `include_recent_memories` (boolean, optional, default `true`): Tail `memory_store.json` for the 8 most recent keys with timestamps.
  - `include_active_sessions` (boolean, optional, default `true`): Count active/paused session files in `data/sessions/`.

#### `bb7_show_available_capabilities`

List the full category map or a single category's tools. The simplest capability discovery surface.

**Internal Composition**: Iterates `self.tool_categories` (a `Dict[str, List[str]]`); on `category` filter, normalizes the input, validates against the dict, and emits `category`, `tools_count`, and one bullet per tool. On unfiltered call, emits `available_capabilities` plus per-category counts, the total unique tool count (via set union), and a `tip` line pointing at the filtered variant. Returns `Unknown category` message on bad input.

- **Parameters**:
  - `category` (string, optional): One of `auto_activation`, `memory`, `project_context`, `execution`, `web`, `automation`. Omit for summary view.

#### `bb7_auto_session_resume`

Inspect session state and recommend `resume active` / `resume paused` / `start new` actions. Distinct from `session_manager_tool.py` of the same name (the session_manager copy was a stale doc-rotation duplicate removed 2026-06-06; this version is the canonical one).

**Internal Composition**: Globs `data/sessions/*.json`; classifies each by `status` into `active_sessions` or `paused_sessions`; sorts active by `last_updated`/`created` desc, picks the top; same for paused by `paused_at`/`last_updated`/`created` desc. Emits recommendation + `session_id` + `session_goal`. Falls through to a `start new` recommendation when both buckets are empty. Use `user_intent` to refine the "start new" path.

- **Parameters**:
  - `workspace_path` (string, optional): Workspace to anchor the analysis. Defaults to `Path.cwd()`.
  - `user_intent` (string, optional): Free-form intent. Echoed in the report and changes the empty-state recommendation wording.

#### `bb7_intelligent_tool_guide`

Classify a user query into one or more intent categories, then emit a recommended tool sequence plus a canonical 3-step workflow. The `bb7_intelligent_tool_guide` → `bb7_workspace_context_loader` → category tools → `bb7_memory_store` composition chain is the doctrinal entry-point workflow.

**Internal Composition**: Lowercases the query; scans a hardcoded `intent_map` (categories: `memory`, `project_context`, `execution`, `web`, `automation`) for keyword hits (`memory/remember/store/recall/retrieve/history`, `project/structure/dependency/changes/context`, `run/execute/terminal/command/build/test/debug`, `http/url/web/fetch/download/search/api`, `optimize/workflow/automation/performance/adaptive`); on zero hits, defaults to `auto_activation + project_context`; emits the first 3 tools from each detected category's `tool_categories` list; appends the canonical 3-step workflow.

- **Parameters**:
  - `user_query` (string, **required**): Raw intent. Non-empty string after strip.
  - `context` (string, optional): Free-form context echoed in the report.

#### `bb7_analyze_workflow_patterns`

Run a comprehensive / depth-specific analysis of workflow patterns over a sliding time window. Stores resulting insights back to `patterns.db` for future adaptive learning.

**Internal Composition**: Composes `_collect_workflow_patterns` (SQL query on `workflow_patterns` with `last_seen >= cutoff_date`; falls back to `_generate_baseline_patterns` when empty/error), `_analyze_productivity_patterns` (per-pattern-type insight extraction from `pattern_data` JSON, threshold-gated on `efficiency_score`), `_analyze_efficiency_patterns` (averages `efficiency_score`, buckets high-frequency and low-efficiency patterns), `_identify_optimization_opportunities` (high-freq low-eff + medium-freq mid-eff gating), and `_generate_pattern_recommendations` (3-tier rec set keyed off `avg_efficiency`). Persists results via `_store_optimization_insights` (bulk-insert into `optimization_insights` with millisecond-unique IDs).

- **Parameters**:
  - `analysis_depth` (string, optional, default `comprehensive`): Depth label passed to pattern collector.
  - `time_range_days` (number, optional, default `30`): Sliding window for `last_seen >=` filter.

#### `bb7_performance_optimization`

Run a real-time performance baseline + bottleneck analysis, then start a tracked experiment in `performance.db`. Pair with `bb7_optimization_results` to close the experiment loop.

**Internal Composition**: Composes `_collect_performance_baseline` (psutil probes: `cpu_percent`, `virtual_memory`, `disk_usage`, `psutil.pids()`, `boot_time`; plus `session_active` + `optimization_level` metadata), `_identify_performance_bottlenecks` (CPU>80%, MEM>85%, DISK>90%/80%, processes>200 thresholds), `_generate_optimization_strategies` (per-bottleneck strategy + `comprehensive` vs `performance` strategy sets), `_generate_realtime_optimizations` (live `psutil` recheck + workspace-size rglob heuristic), `_predict_performance_improvements` (count-bucketed percentage ranges), and `_start_optimization_experiment` (inserts `opt_{epoch}` row into `optimization_experiments` with `status='running'`). Returns experiment ID for follow-up via `bb7_optimization_results`.

- **Parameters**:
  - `optimization_type` (string, optional, default `comprehensive`): `comprehensive` or `performance` mode label.
  - `target_metrics` (array, optional): List of metric names to focus the bottleneck pass on.

#### `bb7_intelligent_automation`

Discover automation opportunities in the workspace and suggest structured workflows. Adaptive learning mode augments with `_generate_learning_insights`.

**Internal Composition**: Composes `_identify_automation_opportunities` (returns 3 canned opportunities: `Automated Project Context Loading` High/Low, `Smart Memory Capture` Med/Med, `Performance Monitoring` Med/Low), `_suggest_automation_workflows` (top-3 opportunity → workflow conversion with `name`/`description`/`trigger`/`action`), `_predict_upcoming_tasks` (returns 2 hardcoded predictions with `confidence` and `preparation` strings), `_generate_learning_insights` (3 hardcoded insights — only invoked when `learning_mode=True`), and `_generate_proactive_actions` (4 hardcoded proactive actions).

- **Parameters**:
  - `automation_scope` (string, optional, default `workspace`): Scope label passed to opportunity detector.
  - `learning_mode` (boolean, optional, default `true`): Toggle `_generate_learning_insights` emission.

#### `bb7_cognitive_optimization`

Return cognitive pattern analysis + enhancement strategies + focus + creativity + decision-support recommendations. The `focus_area` switch extends the enhancement list with creativity-specific tips.

**Internal Composition**: Composes `_analyze_cognitive_patterns` (returns hardcoded `focus_duration`, `peak_hours`, `cognitive_load`, `decision_quality` dict — not measured from real session data), `_generate_cognitive_enhancements` (4 base enhancements plus 2 creativity-scope extensions), `_optimize_focus_strategies` (4 focus optimization strings), `_suggest_creativity_boosters` (3 creativity tips), and `_provide_decision_support` (3 decision-support tips). All helpers return hardcoded strings; the tool is advisory scaffolding, not measured analytics.

- **Parameters**:
  - `focus_area` (string, optional): One of `creativity` for creativity-scope extension; other values use the base enhancement set.
  - `personalization_level` (string, optional, default `adaptive`): Personalization depth label.

#### `bb7_optimization_results`

Read a specific experiment by ID or summarize the overall optimization state with success metrics and next-step recommendations.

**Internal Composition**: When `experiment_id` is set, queries `optimization_experiments` by primary key via `_get_experiment_results` and computes per-metric percent improvement between `baseline` and `optimized` JSON. When unset, composes `_get_performance_trends` (4 hardcoded trend strings), `_get_active_optimizations` (3 hardcoded active-optimization strings), `_calculate_success_metrics` (4 hardcoded `metric: value` pairs — `Overall Performance: Good (78/100)`, etc.), and, when `include_recommendations=True`, `_generate_next_optimizations` (4 hardcoded recommendations). All trend/metric strings are currently hardcoded — there is no live aggregation across experiments.

- **Parameters**:
  - `experiment_id` (string, optional): Omit for overall status; pass an `opt_{epoch}` ID returned by `bb7_performance_optimization`.
  - `include_recommendations` (boolean, optional, default `true`): Toggle `_generate_next_optimizations` emission.

#### `bb7_adaptive_learning`

Emit learning-pattern analysis + behavioral adaptations + personalization updates + predictive insights + learning optimization recommendations. `adaptation_speed` switches between fast/conservative adaptation messaging.

**Internal Composition**: Composes `_analyze_learning_patterns` (4 hardcoded fields: `velocity`, `retention`, `adaptation`, `style`), `_generate_behavioral_adaptations` (3 base adaptations plus `fast`/`slow` speed branches), `_update_personalizations` (4 hardcoded personalization strings), `_generate_predictive_insights` (3 hardcoded predictions including a 45-75 minute session-length estimate), and `_recommend_learning_optimizations` (4 hardcoded recs). All outputs are advisory scaffolding.

- **Parameters**:
  - `learning_scope` (string, optional, default `comprehensive`): Scope label.
  - `adaptation_speed` (string, optional, default `moderate`): One of `slow` / `moderate` / `fast`; `fast` appends a rapid-learning message, `slow` appends a conservative-validation message.
