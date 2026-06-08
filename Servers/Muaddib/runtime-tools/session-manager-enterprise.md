### Session Manager Enterprise (`session_manager_enterprise.py`)

> **Doctrine.** The enterprise session manager is the **heavyweight,
> analytics-rich** variant of `session_manager_tool.py`. It is a parallel
> implementation, not a successor — the two modules coexist and both
> register bb7_ tools under different class-discovery priorities. The
> enterprise variant adds ML-based productivity insights, session templates,
> cross-session merging, real-time dashboards, and cognitive-state
> analytics that the base `session_manager_tool` does not provide.
>
> **Pairing.** Heavy overlap with `session_manager_tool.py`
> (`runtime-tools/session-tool.md`): both expose `bb7_start_session`,
> `bb7_end_session`, etc. — but the implementations, schemas, and storage
> paths differ. The enterprise variant uses `UltimateSessionManager` and
> persists to its own `data/enterprise_sessions/` subtree. **Pick one per
> workflow** to avoid telemetry divergence.

| Subsystem / Class | Role |
|---|---|
| `UltimateSessionManager` | Public façade. Holds the full session database, background monitor threads, and the analytics ML cache. |
| `SessionSnapshot` / `ProductivityMetrics` / `SessionTemplate` / `TeamInsight` | Data containers used across all bb7_ surfaces. |
| `AdvancedCodeExecutor` | Sandbox-style executor for `bb7_execute_session_analysis` and `bb7_experiment_with_hypothesis`. Has its own security validator and safe-environment builder. |
| `_initialize_directory_structure` / `_initialize_all_databases` | SQLite-backed analytics DBs at boot. |
| `_start_background_services` / `_background_monitor_loop` / `_system_monitor_loop` | Background threads for continuous monitoring. |
| `_data_access_callback` | Centralised read path for analytics queries. |
| `_generate_default_analysis_code` | Builds default analysis notebooks for common `analysis_type` values. |

**Storage paths:** `data/enterprise_sessions/` (sessions), `data/analytics/`
(SQLite DBs for productivity / goals / cognitive state), and a session
template registry.

**Soft-degrade contract:** All `bb7_*` methods are `async` and tolerate
missing optional inputs (inherit_from, template_id, etc.). Background
services can be disabled via `enable_background=false` on
`bb7_start_session`.

---

#### `bb7_start_session`

Start an "ultimate" AI collaboration session with comprehensive
intelligence, pattern recognition, and predictive insights. Generates
a `ult_<ts>_<hash>` session ID and persists the goal/context/tags to
the enterprise session DB.
**Internal Composition**: Calls `UltimateSessionManager.bb7_start_session()`.
Validates inputs, generates session ID, optionally inherits context from
`inherit_from`, applies a `template_id` if supplied, spawns the background
monitor when `enable_background=true`.

- **Parameters**:
  - `goal` (string, required): Session goal statement.
  - `context` (string, optional): Initial situational context.
  - `session_type` (string, optional): Session type tag (default: `"general"`).
  - `tags` (array of strings, optional): Classification tags.
  - `inherit_from` (string, optional): Session ID to inherit context from.
  - `template_id` (string, optional): Session template to apply.
  - `enable_background` (boolean, optional): Spawn background monitor (default: true).

#### `bb7_end_session`

End the current session with comprehensive analysis, learning capture,
and pattern updates. Updates productivity counters, runs an end-of-session
analysis pass, and writes a final summary to the session DB.
**Internal Composition**: Calls `UltimateSessionManager.bb7_end_session()`.
Validates an active session is present, captures success rating +
achievements + challenges + learnings, updates the analytics DB.

- **Parameters**:
  - `summary` (string, optional): Free-form end-of-session summary.
  - `success_rating` (number, optional): 0.0–1.0 self-rating.
  - `achievements` (array of strings, optional): What was accomplished.
  - `challenges` (array of strings, optional): What blocked progress.
  - `learnings` (array of strings, optional): What was learned.

#### `bb7_execute_session_analysis`

Execute advanced Python analysis on session data with optional ML
capabilities. Generates default analysis code based on `analysis_type`
when no explicit `code` is supplied, executes it through the
`AdvancedCodeExecutor` sandbox.
**Internal Composition**: Calls `UltimateSessionManager.bb7_execute_session_analysis()`.
Composes `_generate_default_analysis_code` (when `code=""`) →
`AdvancedCodeExecutor.execute_code()` → analytics DB write.

- **Parameters**:
  - `code` (string, optional): Explicit Python analysis code; defaults are generated from `analysis_type` if empty.
  - `analysis_type` (string, optional): Default-code generator key (default: `"general"`).
  - `save_notebook` (boolean, optional): Save the executed notebook to disk (default: false).
  - `experiment_name` (string, optional): Notebook filename (default: `"analysis_<ts>"`).
  - `enable_ml` (boolean, optional): Allow ML library imports in the sandbox (default: false).

#### `bb7_generate_productivity_insights`

Generate AI-powered productivity insights with ML analysis and
actionable recommendations. Time-series correlation, predictions, and
optional reusable analysis code generation.
**Internal Composition**: Calls `UltimateSessionManager.bb7_generate_productivity_insights()`.
Composes `_analyze_time_productivity_patterns` + prediction models +
optional code generation via `bb7_execute_session_analysis`.

- **Parameters**:
  - `insight_type` (string, optional): `comprehensive`, `time_correlation`, or focused key (default: `"comprehensive"`).
  - `time_period` (integer, optional): Look-back window in days (default: 30).
  - `generate_code` (boolean, optional): Emit reusable analysis code (default: true).
  - `include_predictions` (boolean, optional): Include ML predictions (default: true).

#### `bb7_create_session_template`

Create intelligent session templates with AI optimization and success
pattern analysis. Can be derived from a prior successful session or
auto-generated from `work_type`.
**Internal Composition**: Calls `UltimateSessionManager.bb7_create_session_template()`.
Composes the prior-session data (when `based_on_session` is supplied) →
AI optimisation pass → template registry write.

- **Parameters**:
  - `template_name` (string, required): Template display name.
  - `based_on_session` (string, optional): Source session ID to derive from.
  - `work_type` (string, optional): Work-type tag (default: `"general"`).
  - `auto_generate` (boolean, optional): Auto-generate template fields via AI (default: true).
  - `optimization_level` (string, optional): `basic`, `standard`, or `deep` (default: `"standard"`).

#### `bb7_start_background_session`

Start a background session with continuous monitoring and automatic
insight generation. Runs in a daemon thread without blocking the caller.
**Internal Composition**: Calls `UltimateSessionManager.bb7_start_background_session()`.
Spawns a `bg_<ts>_<hash>` session, registers a background monitor
thread, sets `auto_insights` interval.

- **Parameters**:
  - `goal` (string, optional): Background goal (default: `"Background productivity monitoring"`).
  - `context` (string, optional): Initial context.
  - `monitoring_level` (string, optional): `low`, `standard`, or `high` (default: `"standard"`).
  - `auto_insights` (boolean, optional): Auto-emit insights on the configured interval (default: true).

#### `bb7_merge_sessions`

Merge multiple sessions with intelligent context combination. Strategies
include `sequential`, `parallel`, `thematic`, and `intelligent` (the
default — picks the strategy that maximises context overlap).
**Internal Composition**: Calls `UltimateSessionManager.bb7_merge_sessions()`.
Loads all `session_ids`, runs the merge strategy, optionally creates a
new merged session with `create_new_session=true`.

- **Parameters**:
  - `session_ids` (array of strings, required): Source session IDs (must have ≥ 2 entries).
  - `merge_name` (string, optional): Display name for the merged artefact (default: `"Merged Session Analysis"`).
  - `merge_strategy` (string, optional): `sequential`, `parallel`, `thematic`, or `intelligent` (default: `"intelligent"`).
  - `create_new_session` (boolean, optional): Persist the merge as a new session (default: false).

#### `bb7_export_analytics`

Export comprehensive analytics for external analysis tools with privacy
controls. Supports `csv`, `json`, and Markdown; optional `zip` or `tar`
compression; privacy-safe redaction toggle.
**Internal Composition**: Calls `UltimateSessionManager.bb7_export_analytics()`.
Gathers analytics data per `categories`, applies privacy redaction when
`include_privacy_safe=true`, compresses per `compression`, writes
`export_<ts>_<hash>` artefact.

- **Parameters**:
  - `format` (string, optional): `csv`, `json`, or `markdown` (default: `"csv"`).
  - `time_range` (integer, optional): Look-back window in days (default: 30).
  - `categories` (array of strings, optional): Analytics categories to include (default: `["all"]`).
  - `external_tool` (string, optional): Target external tool hint (default: `"general"`).
  - `include_privacy_safe` (boolean, optional): Apply privacy redaction (default: true).
  - `compression` (string, optional): `none`, `zip`, or `tar` (default: `"none"`).

#### `bb7_goal_achievement_tracking`

Advanced goal achievement tracking with ML predictions and optimization
strategies. Per-category breakdown with forward-looking prediction
horizon.
**Internal Composition**: Calls `UltimateSessionManager.bb7_goal_achievement_tracking()`.
Composes `_analyze_goal_achievement_comprehensive` + ML prediction model
+ optimization recommendations.

- **Parameters**:
  - `type` (string, optional): Analysis type key (default: `"comprehensive"`).
  - `category` (string, optional): Goal category filter, or `"all"` (default: `"all"`).
  - `time_period` (integer, optional): Look-back window in days (default: 30).
  - `prediction_horizon` (integer, optional): Forward-looking prediction window in days (default: 7).
  - `optimization_suggestions` (boolean, optional): Include optimization recommendations (default: true).

#### `bb7_session_dashboard`

Real-time session dashboard with comprehensive metrics, optional charts,
and predictive analytics. Three dashboard types: `current`, `historical`,
or `predictive`.
**Internal Composition**: Calls `UltimateSessionManager.bb7_session_dashboard()`.
Composes `_refresh_dashboard_data` (when `refresh_data=true`) + chart
rendering + predictive analytics.

- **Parameters**:
  - `dashboard_type` (string, optional): `current`, `historical`, or `predictive` (default: `"current"`).
  - `include_charts` (boolean, optional): Render inline chart blocks (default: true).
  - `time_range` (integer, optional): Look-back window in days (default: 7).
  - `refresh_data` (boolean, optional): Force a fresh analytics query (default: true).

#### `bb7_experiment_with_hypothesis`

Test productivity hypotheses with scientific rigor, statistical analysis,
and optional code execution. Default experiment code is auto-generated
when `experiment_code` is empty.
**Internal Composition**: Calls `UltimateSessionManager.bb7_experiment_with_hypothesis()`.
Generates `exp_<ts>_<hash>` ID, executes the hypothesis test through
`AdvancedCodeExecutor` with statistical confidence thresholds, saves
the experiment notebook.

- **Parameters**:
  - `hypothesis` (string, required): Free-form hypothesis statement.
  - `experiment_code` (string, optional): Explicit experiment code; defaults generated when empty.
  - `auto_generate_code` (boolean, optional): Auto-generate experiment code from the hypothesis (default: true).
  - `save_experiment` (boolean, optional): Save the executed notebook (default: true).
  - `statistical_confidence` (number, optional): Required confidence level 0.0–1.0 (default: 0.95).

#### `bb7_cognitive_state_analysis`

Analyse cognitive state, flow patterns, mental performance, and
optimization opportunities. Three analysis depths and four time windows.
**Internal Composition**: Calls `UltimateSessionManager.bb7_cognitive_state_analysis()`.
Composes `_analyze_current_cognitive_state` + historical pattern walk +
optional biometric integration + recommendations.

- **Parameters**:
  - `analysis_depth` (string, optional): `basic`, `standard`, or `deep` (default: `"standard"`).
  - `time_window` (string, optional): `current`, `hourly`, `daily`, or `weekly` (default: `"current"`).
  - `include_recommendations` (boolean, optional): Emit optimization recommendations (default: true).
  - `biometric_integration` (boolean, optional): Pull biometric data when available (default: false).
