# Runtime Tools — Somnus Tool Neural-Network Server

**Canonical status:** single operational entrypoint for `runtime-tools/`.
**Generated/updated:** 2026-06-06 (America/Chicago).
**Source probe:** `mcp.venv/bin/python` imported active `tools/*.py` modules using `mcp_server.py` discovery constants without instantiating `MCPServer`.

## 0. Reading contract

This document is the compact runtime map. Older leaf files in this directory may remain useful as historical or deeper module notes, but this `README.md` is the current routing document when names disagree. Runtime truth still comes from source registration plus live `bb7_tool_health_report` after process reload.

## 1. Non-negotiable runtime invariants

- Somnus-MCP is a **24/7 autonomous tool neural-network server**, not a public productized MCP catalog.
- This private install is the authoritative live server/control plane; public releases or snapshots are non-authoritative copies.
- `mcp_server.py` is the gateway/dispatcher: transport, registry, lifecycle, telemetry, raw-result boundary, and final display projection. It is not the intelligence layer.
- Intelligence/routing lives in `muadib/`, `tools/exoskeleton_tool.py`, `tools/lisan_al_gaib.py`, and the shared `/home/daeron/Somnus-MCP/data` substrate.
- `/home/daeron/Somnus-MCP/data` is the global continuity plane for all connected agents and gateways. Do not create alternate per-client/per-project BB7 data roots.
- Raw dict/list/string payloads must be preserved for event telemetry, ambient memory exchange, Q-table/observations, MuadDib self-play, and distillation/RFT **before** any final human-facing display projection.
- `SOVEREIGN_DISPLAY_PROJECTION=raw` is the raw-display escape hatch; projection output must never be fed back as substrate truth.
- `tools/enhanced_web_tool.py` is the only active web source. Do not resurrect `web_tool.py`.
- `tools/shell_tool.py` and `tools/vscode_terminal_tool.py` are MCP terminal/tool-server surfaces. Codex local execution still uses native shell/Bash by policy unless Daeron specifically asks for BB7 shell surfaces.
- `tools/code_analysis_tool.py` is restored. It intentionally coexists with `tools/enhanced_code_analysis_tool.py`; the enhanced module is loaded after the baseline module so enhanced `bb7_security_audit` wins the duplicate name.
- Retired scratch copies are not active tools: `tools/project_context_tool (1).py` and `tools/session_manager_enterprise.py` were removed from `tools/` after source probe showed syntax/load failures.
- `databus/openrouter.yaml` defaults to `elephant-alpha` with an intentionally empty `routing.fallback_chain`; OpenRouter wrapper health/dry-run surfaces (`or_health`, `or_dry_run_complete`, `or_dry_run_batch`) are no-network contract checks, and live calls still require a real `OPENROUTER_API_KEY`.

## 2. Active source inventory

- Active source modules with `get_tools()`: **18**
- Active registered surface names from source probe: **141**
- Source-probe failures after retirement: **0**
  - none

| Group | Module | Surfaces | Role |
|---|---|---|---|
| Continuity | `memory_tool.py` | 14 | Long-term memory, BM25/Ebbinghaus surfacing, context resurrection, import/export, and workspace context loading. |
| Continuity | `memory_interconnect.py` | 9 | Memory graph/concept network, relationship analysis, clustering, consolidation, and gap detection. |
| Execution surfaces | `file_tool.py` | 12 | Filesystem capability surface with FSTIP sparse reads/writes, search, metadata, copy/move/delete, and operation history. |
| Execution surfaces | `shell_tool.py` | 4 | MCP-hosted command/process/system utility surface. Codex itself should still use native shell for ordinary local terminal work. |
| Execution surfaces | `vscode_terminal_tool.py` | 6 | VS Code terminal-context surface: terminal status, environment, command history, cd/which/path intelligence, and dev-context hints. |
| Continuity | `thought_journal_tool.py` | 11 | Chronological reasoning journal, decisions, conflicts, task state, and reflective summaries. |
| External information | `enhanced_web_tool.py` | 4 | Sole active web surface: URL fetch/search/webpage analysis/download. Legacy web_tool.py is intentionally absent. |
| Agent/planning | `openrouter_planner_tool.py` | 3 | OpenRouter-backed planning facade with dry-run/health posture and elephant-alpha default routing. |
| Agent/planning | `openrouter_agent_tool.py` | 9 | Asynchronous OpenRouter multi-agent orchestration and handoff plane; live calls require a real OpenRouter key. |
| Continuity | `session_manager_tool.py` | 16 | Shared cognitive session continuity substrate with events, insights, workflow records, recommendations, and memory/session links. |
| Execution surfaces | `visual_tool.py` | 5 | GUI/visual/OCR/screenshot surface with Linux headless-safe pyautogui optionality. |
| Code/project understanding | `project_context_tool.py` | 4 | Project structure/dependency/recent-change/code-metrics summaries over the repo without using the retired broken copy. |
| Autonomy substrate | `auto_tool_module.py` | 10 | Autonomic optimization/performance/cognitive tuning experiments and proactive suggestions. |
| Code/project understanding | `code_analysis_tool.py` | 4 | Restored baseline code-analysis surface: overview, suggestions, security audit compatibility, and safe execution helpers. |
| Code/project understanding | `enhanced_code_analysis_tool.py` | 4 | Advanced code-analysis surface: AST/CFG/data-flow/type/security analysis and RestrictedPython execution/audit logs. |
| Autonomy substrate | `exoskeleton_tool.py` | 22 | Main BB7 compiled control-plane surface: route, plan, reflect, Lisan/MuadDib bridge wrappers, health, and tool catalog sync. |
| Autonomy substrate | `ai_system_integration_fixed.py` | 1 | Registry-visible AI/system integration shim currently exposing a narrow integration capability. |
| Autonomy substrate | `meta_intelligence_engine.py` | 4 | Registry-bound meta-intelligence facade: context weaver, code consciousness, creative solver, MuadDib/Mentat bridge. |

### Duplicate-name resolution

- `bb7_security_audit`: `code_analysis_tool.py` -> `enhanced_code_analysis_tool.py`

## 3. Module details and active surfaces

### `memory_tool.py`

**Group:** Continuity
**Role:** Long-term memory, BM25/Ebbinghaus surfacing, context resurrection, import/export, and workspace context loading.

| Surface | Description |
|---|---|
| `bb7_memory_bulk_store` | Atomically store multiple memory entries in a single disk write. entries_json must be a JSON array of {key, value, category, importance, tags} objects. |
| `bb7_memory_categories` | List available memory categories with descriptions. |
| `bb7_memory_consolidate` | Archive old low-importance memories, prune BM25 index. Memories with importance >= 0.7 or access_count >= 5 are always retained. |
| `bb7_memory_delete` | Delete a memory entry by key. |
| `bb7_memory_export` | Export all memories as Markdown (default) or JSON. |
| `bb7_memory_get_related` | Fetch semantically related memories for a given key using BM25. |
| `bb7_memory_insights` | Narrative insights combining local stats and BM25 network analysis. |
| `bb7_memory_list` | List memory keys with filtering (prefix, category, min_importance) and sorting (timestamp/importance/access/alphabetical/decay). |
| `bb7_memory_retrieve` | Retrieve a memory by key. Updates Ebbinghaus stability (reinforces retention). Use include_related=true for full metadata. |
| `bb7_memory_search` | BM25-powered semantic search with Ebbinghaus decay reranking. |
| `bb7_memory_stats` | Comprehensive memory statistics including decay, access patterns, and category breakdown. |
| `bb7_memory_store` | Store a key-value memory with category, importance (0-1), tags, and automatic BM25 indexing + Ebbinghaus decay initialisation. |
| `bb7_memory_surface_context` | Proactively surface the most relevant memories for a given context blob using BM25 + Ebbinghaus decay weighting. Call at session start to recover relevant prior knowledge. |
| `bb7_memory_timeline` | Chronological view of memories created or updated recently. Shows Ebbinghaus retention score for each entry. |

### `memory_interconnect.py`

**Group:** Continuity
**Role:** Memory graph/concept network, relationship analysis, clustering, consolidation, and gap detection.

| Surface | Description |
|---|---|
| `bb7_memory_analyze_entry` | Index a memory entry using BM25, extract concepts, and map relationships to existing memories. |
| `bb7_memory_cluster` | Group indexed memories into BM25 semantic clusters. |
| `bb7_memory_concept_network` | Get the network of memories and related concepts for a given concept. |
| `bb7_memory_consolidate_index` | Archive low-importance old memories and prune all indices. Fixes orphaned concept refs from the original implementation. |
| `bb7_memory_extract_concepts` | Extract key BM25 tokens/concepts from text. |
| `bb7_memory_find_gaps` | Find concepts referenced in multiple memories but lacking a dedicated entry. |
| `bb7_memory_get_insights` | Formatted insights report about the memory network: density, top concepts, important memories. |
| `bb7_memory_graph` | Export memory relationship graph in Graphviz DOT format for visualisation. |
| `bb7_memory_intelligent_search` | BM25-ranked semantic search across all indexed memories. Significantly more accurate than keyword search. |

### `file_tool.py`

**Group:** Execution surfaces
**Role:** Filesystem capability surface with FSTIP sparse reads/writes, search, metadata, copy/move/delete, and operation history.

| Surface | Description |
|---|---|
| `bb7_append_file` | Append content to a file while preserving the historical append surface. |
| `bb7_copy_file` | Copy files or directories with metadata preservation and overwrite control. |
| `bb7_delete_file` | Delete files or directories with optional backup. Directories and no-backup deletes require force=true. |
| `bb7_file_cache_stats` | Compatibility shim for the removed legacy file content cache; reports operation-history state. |
| `bb7_file_info` | Get comprehensive information about a file or directory. |
| `bb7_get_file_info` | Compatibility alias for bb7_file_info. |
| `bb7_list_directory` | List directory contents with detailed metadata, sorting, and file-type insight. |
| `bb7_move_file` | Move or rename files and directories. |
| `bb7_operation_history` | View file operation history, statistics, and patterns for workflow optimization. |
| `bb7_read_file` | Read a file with FSTIP token isolation. Prefer start_line/end_line or semantic_target for bounded reads; large naked reads return a structural skeleton unless allow_large_raw=true. |
| `bb7_search_files` | Bounded recursive file search with name/content matching. Accepts both legacy pattern and new name_pattern. |
| `bb7_write_file` | Write or create a file with optional backup, directory creation, encoding selection, and executable bit support. |

### `shell_tool.py`

**Group:** Execution surfaces
**Role:** MCP-hosted command/process/system utility surface. Codex itself should still use native shell for ordinary local terminal work.

| Surface | Description |
|---|---|
| `bb7_get_command_history` | 📜 View command execution history with performance analysis, success rates, and usage patterns. Perfect for reviewing recent development activities, analyzing command performance, and identifying frequently used commands for automation opportunities. Provides insights into command efficiency and suggests optimizations. |
| `bb7_get_system_info` | 💻 Get comprehensive system information including hardware specs, OS details, running processes, disk usage, memory utilization, and network status. Perfect for troubleshooting, performance monitoring, and understanding your development environment. Provides actionable insights for system optimization and resource management. |
| `bb7_list_processes` | 📊 List and analyze running processes with intelligent filtering, resource usage analysis, and performance insights. Perfect for troubleshooting resource issues, monitoring system performance, and identifying processes that may be affecting development work. Provides actionable recommendations for process management and optimization. |
| `bb7_run_command` | ⚡ Execute shell commands safely with intelligent output analysis, error diagnosis, and security controls. Perfect for development tasks, system administration, and automation. Provides detailed execution results, performance metrics, and actionable suggestions for command optimization and troubleshooting. |

### `vscode_terminal_tool.py`

**Group:** Execution surfaces
**Role:** VS Code terminal-context surface: terminal status, environment, command history, cd/which/path intelligence, and dev-context hints.

| Surface | Description |
|---|---|
| `bb7_terminal_cd` | 📁 Navigate directories with intelligent context tracking, project detection, and workspace awareness. Perfect for development workflow navigation with automatic environment detection, project structure analysis, and smart suggestions for development tasks. Maintains directory context across VS Code terminal sessions with comprehensive path intelligence. |
| `bb7_terminal_environment` | 🌍 Analyze and display VS Code terminal environment with intelligent insights about development setup, tool availability, and configuration optimization. Perfect for troubleshooting environment issues, setting up new projects, and ensuring proper development tool configuration. Provides actionable recommendations for environment improvement. |
| `bb7_terminal_history` | 📜 Display and analyze terminal command history with intelligent insights, pattern detection, and usage analytics. Perfect for reviewing recent development activities, identifying workflow patterns, finding frequently used commands, and optimizing development processes. Provides smart suggestions for command automation and workflow improvement. |
| `bb7_terminal_run_command` | ⚡ Execute commands in VS Code terminal context with intelligent output analysis, directory tracking, and environment awareness. Perfect for development workflows, build processes, testing, and automation. Maintains session continuity and provides smart error diagnosis with actionable solutions for common development scenarios. |
| `bb7_terminal_status` | 🖥️ Get comprehensive VS Code terminal status including session information, environment variables, development context, and integration state. Perfect for understanding your current development environment, troubleshooting terminal issues, and optimizing your workflow setup. Provides actionable insights for terminal configuration and usage. |
| `bb7_terminal_which` | 🔍 Locate executables and analyze command availability in VS Code terminal environment with intelligent path analysis, version detection, and alternative suggestions. Perfect for troubleshooting missing commands, verifying tool installations, and understanding your development environment setup. Provides comprehensive tool availability analysis. |

### `thought_journal_tool.py`

**Group:** Continuity
**Role:** Chronological reasoning journal, decisions, conflicts, task state, and reflective summaries.

| Surface | Description |
|---|---|
| `bb7_journal_add_outcome` | Retrospectively record what happened as a result of a thought or decision. For decisions, validated=true marks as confirmed, validated=false marks as invalidated. |
| `bb7_journal_capture_decision` | Record a decision with full provenance: rationale, alternatives considered, constraints, risk assessment, and success criteria. This creates an auditable decision trail. |
| `bb7_journal_detect_conflicts` | Find decisions that may contradict each other. Uses BM25 similarity + negation word detection to identify decisions where one affirms what another denies. |
| `bb7_journal_generate_retrospective` | Generate a structured retrospective from the last N days of journal entries. Includes decisions made, insights, hypothesis validation, open questions, and decision quality metrics. |
| `bb7_journal_get_decision_trail` | Get the chronological decision history for a topic. Shows decisions, their rationale, status, and outcomes — and flags potential contradictions. |
| `bb7_journal_get_reasoning_chain` | Reconstruct the reasoning chain that led to a specific decision. Follows linked thoughts and infers additional supporting entries using BM25 similarity. |
| `bb7_journal_linked_entries` | Reverse lookup: given a memory key, return all journal entries that linked to it. Useful for understanding why a memory was created or what decisions reference it. |
| `bb7_journal_record_thought` | Record a thought, insight, hypothesis, observation, or question with confidence level and optional links to memories and files. Creates durable reasoning provenance for future sessions. |
| `bb7_journal_search` | BM25-ranked full-text search across all journal entries. |
| `bb7_journal_stats` | Journal statistics: entry counts by type, decision quality score, outcome tracking rate, confidence averages, and top tags. |
| `bb7_journal_surface_relevant` | Proactively surface journal entries most relevant to the current context. Applies a recency boost to recent entries. Use at session start to recover relevant prior reasoning. |

### `enhanced_web_tool.py`

**Group:** External information
**Role:** Sole active web surface: URL fetch/search/webpage analysis/download. Legacy web_tool.py is intentionally absent.

| Surface | Description |
|---|---|
| `bb7_analyze_webpage` | Perform comprehensive analysis of webpage structure, content quality, SEO factors, and technical characteristics. Perfect for web development, content auditing, competitor analysis, and understanding webpage architecture. Provides detailed insights into page performance, accessibility, and optimization opportunities. |
| `bb7_download_file` | Download files from web URLs with intelligent handling of different content types, progress tracking, and automatic organization. Perfect for downloading documentation, code samples, data files, and other web resources. Provides safety checks and comprehensive download management with metadata preservation. |
| `bb7_fetch_url` | Fetch and intelligently analyze web content from any URL with automatic content type detection, smart text extraction, and comprehensive metadata analysis. Perfect for documentation research, API exploration, content analysis, and gathering information from web resources. Provides structured output with actionable insights and extracted key information. |
| `bb7_search_web` | Search the web using multiple search engines with intelligent result aggregation and analysis. Perfect for research, finding documentation, discovering code examples, and gathering information on development topics. Provides ranked results with content previews and actionable insights for each found resource. |

### `openrouter_planner_tool.py`

**Group:** Agent/planning
**Role:** OpenRouter-backed planning facade with dry-run/health posture and elephant-alpha default routing.

| Surface | Description |
|---|---|
| `bb7_planner_health` | Return OpenRouter planner configuration and persistence health. |
| `bb7_planner_plan` | Generate a structured execution plan using OpenRouter. |
| `bb7_planner_template` | Generate a planner prompt template for a target intent. |

### `openrouter_agent_tool.py`

**Group:** Agent/planning
**Role:** Asynchronous OpenRouter multi-agent orchestration and handoff plane; live calls require a real OpenRouter key.

| Surface | Description |
|---|---|
| `bb7_agent_call` | Call another agent (non-blocking) |
| `bb7_agent_capabilities` | Get agent capabilities and tools |
| `bb7_agent_handoff` | Hand off to another agent with shared context |
| `bb7_agent_health` | Return agent health with canon data dir info |
| `bb7_agent_list` | List all available agents |
| `bb7_agent_messages` | Get messages from cognitive plane |
| `bb7_agent_nodes` | List all active agent nodes in cognitive plane |
| `bb7_agent_run` | Run agent with ACTUAL tool execution in distributed plane |
| `bb7_agent_status` | Get active agent nodes status |

### `session_manager_tool.py`

**Group:** Continuity
**Role:** Shared cognitive session continuity substrate with events, insights, workflow records, recommendations, and memory/session links.

| Surface | Description |
|---|---|
| `bb7_auto_memory_stats` | Get the statistics of auto-captured memories for the current session. |
| `bb7_capture_insight` | Enhanced insight capture with auto-memory and relationship tracking. |
| `bb7_cross_session_analysis` | Analyze patterns across multiple sessions. |
| `bb7_get_session_insights` | Get comprehensive insights about a session. |
| `bb7_get_session_summary` | Get a detailed summary of a specific session. |
| `bb7_learned_patterns` | Get the learned patterns from sessions. |
| `bb7_link_memory_to_session` | Link a memory key to the current session. |
| `bb7_list_sessions` | List all sessions with optional status filter. |
| `bb7_log_event` | Enhanced event logging with auto-memory formation. |
| `bb7_pause_session` | Pause the current session. |
| `bb7_record_workflow` | Record a procedural workflow or pattern. |
| `bb7_resume_session` | Resume a paused session. |
| `bb7_session_intelligence` | Get the session intelligence data. |
| `bb7_session_recommendations` | Generate intelligent recommendations based on past sessions. |
| `bb7_start_session` | Start a new enhanced cognitive session with intelligence. |
| `bb7_update_focus` | Update current attention focus and energy state. |

### `visual_tool.py`

**Group:** Execution surfaces
**Role:** GUI/visual/OCR/screenshot surface with Linux headless-safe pyautogui optionality.

| Surface | Description |
|---|---|
| `bb7_click_element` | 🖱️ Click on visual elements with intelligent targeting, multiple click types, and precise positioning. Perfect for UI automation, testing workflows, and interactive debugging. Supports various click types with smart element detection and coordinate validation. |
| `bb7_find_on_screen` | 🔍 Find visual elements on screen using intelligent pattern matching, color detection, and coordinate identification. Perfect for UI automation, testing, and visual debugging. Provides precise element location with confidence scoring and multiple matching strategies. |
| `bb7_screen_monitor` | 👁️ Monitor screen for changes with intelligent change detection, activity analysis, and automated capture. Perfect for monitoring applications, detecting events, and tracking visual changes during development or testing. Provides comprehensive activity reporting. |
| `bb7_take_screenshot` | Capture screenshots with intelligent analysis, annotation capabilities, and automatic saving. Perfect for documentation, debugging, UI testing, and visual monitoring. Provides comprehensive screen analysis with element detection, color analysis, and visual insights for development workflows. |
| `bb7_window_info` | 🪟 Get comprehensive information about active windows and applications with intelligent analysis and management suggestions. Perfect for window management, application monitoring, and development environment optimization. Provides detailed window properties and actionable insights. |

### `project_context_tool.py`

**Group:** Code/project understanding
**Role:** Project structure/dependency/recent-change/code-metrics summaries over the repo without using the retired broken copy.

| Surface | Description |
|---|---|
| `bb7_analyze_project_structure` | Analyze and summarize project structure in a bounded LLM-friendly format. |
| `bb7_get_code_metrics` | Generate bounded code metrics and statistics in LLM-friendly format. |
| `bb7_get_project_dependencies` | Extract and summarize project dependencies in LLM-friendly format. |
| `bb7_get_recent_changes` | Get recent Git changes in LLM-friendly format. |

### `auto_tool_module.py`

**Group:** Autonomy substrate
**Role:** Autonomic optimization/performance/cognitive tuning experiments and proactive suggestions.

| Surface | Description |
|---|---|
| `bb7_adaptive_learning` | Adapt recommendations to user behavior patterns. |
| `bb7_analyze_workflow_patterns` | Analyze workflow patterns and identify optimization opportunities. |
| `bb7_auto_session_resume` | Recommend whether to resume existing sessions or start a new one. |
| `bb7_cognitive_optimization` | Suggest cognitive strategies to improve focus and decision quality. |
| `bb7_intelligent_automation` | Identify automation opportunities and suggest workflows. |
| `bb7_intelligent_tool_guide` | Map user intent to a recommended set of tools and workflow steps. |
| `bb7_optimization_results` | Retrieve optimization outcomes and recommended next steps. |
| `bb7_performance_optimization` | Run performance optimization analysis and strategy generation. |
| `bb7_show_available_capabilities` | Display categories and available MCP tools. |
| `bb7_workspace_context_loader` | Load all relevant workspace context for session continuity. |

### `code_analysis_tool.py`

**Group:** Code/project understanding
**Role:** Restored baseline code-analysis surface: overview, suggestions, security audit compatibility, and safe execution helpers.

| Surface | Description |
|---|---|
| `bb7_analyze_code` | Perform comprehensive static code analysis including AST parsing, complexity metrics, security auditing, pattern detection, and quality assessment. Perfect for code reviews, security audits, refactoring guidance, and understanding complex codebases. Provides detailed insights with actionable recommendations for code improvement and optimization. |
| `bb7_code_suggestions` | Generate intelligent code improvement suggestions including refactoring opportunities, performance optimizations, security enhancements, and best practice recommendations. Perfect for code reviews, learning, and continuous improvement. Provides specific, actionable suggestions with examples and explanations. |
| `bb7_execute_code_safely` | Execute Python code in a secure sandboxed environment with comprehensive safety controls, resource monitoring, and execution analysis. Perfect for testing code snippets, validating algorithms, running examples, and educational purposes. Provides detailed execution results with performance metrics and security safeguards to prevent system damage. |
| `bb7_security_audit` | Perform detailed security audit of code including vulnerability detection, unsafe pattern identification, and compliance checking. Perfect for security reviews, penetration testing preparation, and ensuring code meets security standards. Provides specific remediation guidance and security best practices recommendations. |

### `enhanced_code_analysis_tool.py`

**Group:** Code/project understanding
**Role:** Advanced code-analysis surface: AST/CFG/data-flow/type/security analysis and RestrictedPython execution/audit logs.

| Surface | Description |
|---|---|
| `bb7_analyze_code_complete` | Complete code analysis with AST parsing, metrics, and security analysis |
| `bb7_get_execution_audit` | Get Python execution audit log with security events |
| `bb7_python_execute_secure` | Secure Python code execution with sandboxing and audit logging |
| `bb7_security_audit` | Security-focused code analysis to identify vulnerabilities and risks |

### `exoskeleton_tool.py`

**Group:** Autonomy substrate
**Role:** Main BB7 compiled control-plane surface: route, plan, reflect, Lisan/MuadDib bridge wrappers, health, and tool catalog sync.

| Surface | Description |
|---|---|
| `bb7_dt_advanced_features` | Query Muad'Dib advanced modality features for candidate tools. Returns per-tool provenance-tagged scores (trained_q from Q-table, trained_cooccur from observation buffer, untrained_embed from embed table). Requires MUADIB_ADVANCED_MODE=1 to return real signals; returns {ok: false, reason: bridge_disabled} otherwise. Use for routing signal inspection and integration validation. |
| `bb7_dt_checkpoint_status` | Inspect Muad'Dib tokenizer and self-play checkpoint state, including active safetensors pointers, promotion-lock state, and legacy .pt migration fallback files. |
| `bb7_dt_self_play` | Run bounded Muad'Dib self-play against the live tool catalog. Trains an isolated candidate policy/value head, saves real tensor weights as safetensors, and promotes only when explicitly requested after a complete atomic checkpoint write. JSON is metadata/ledger only. |
| `bb7_dt_self_play_lock` | Lock or unlock Muad'Dib self-play active-head promotion. Continuous self-play may still train/archive candidate safetensors checkpoints while the active/champion head is locked. |
| `bb7_exo_bootstrap` | Bootstrap capability-aware context for the exoskeleton control loop. |
| `bb7_exo_briefing` | Generate a natural-language capability narrative with proven workflows, recommendations, and health warnings for the given intent. |
| `bb7_exo_category_specific_tools` | List tools in a category with reliability priors. |
| `bb7_exo_execute_step` | Record a step execution in a checkpointed plan. Call AFTER running the tool to log the outcome. Checkpoints persist across crashes. |
| `bb7_exo_get_recent_activity` | Get recent activity from all AI instances - call at session start to sync context with other AIs. |
| `bb7_exo_kpi_report` | Generate a KPI report for one or all active plans. Shows completion rate, success rate, throughput, health assessment, and aggregate stats. |
| `bb7_exo_list_tool_categories` | List canonical capability categories and counts. |
| `bb7_exo_plan` | Generate candidate tool chains with confidence and fallback. |
| `bb7_exo_preemptive_recovery` | Analyse a planned workflow for failure risks before execution and suggest alternatives for weak links. |
| `bb7_exo_reflect` | Reflect outcomes and update tool/chain priors. |
| `bb7_exo_resume_plan` | Resume a checkpointed plan from where it left off. Returns next tool to execute and full progress state. Call at session start to continue interrupted workflows. Omit plan_id to list all plans. |
| `bb7_exo_route` | Intent-conditioned retrieval with semantic and graph scoring. |
| `bb7_exo_route_focused` | Progressive-disclosure routing: top-N tools with one-liner descriptions and expansion hint. |
| `bb7_exo_state` | Inspect exoskeleton state, priors, and discovered macros. |
| `bb7_exo_suggest_next` | Orchestration prediction: suggest next tools/actions given current context. Key for chaining memory→analysis→execution workflows. |
| `bb7_lisan_distill` | Explicit distillation: log a complete LLM trajectory (role/content/tool_calls list) to the RFT training dataset. Call after bb7_agent_run completes a task. Trajectory format: [{role: user/assistant/tool, content: str, tool_calls: [...]}]. |
| `bb7_lisan_intend` | Expose spectral intent analysis as a direct tool. Given a user message, returns: decomposed intents with confidence scores, recommended tool categories, momentum bonus, and golden path match. Makes lisan's routing reasoning VISIBLE. Use to verify the system's intent interpretation before routing with bb7_exo_route. |
| `bb7_lisan_recall` | Context Resurrection: single-call long-horizon session recovery. Combines relevant memories (BM25), active plan checkpoints, cross-AI activity, session momentum, and prior decisions into one LLM-ready context blob. Call at session start instead of bb7_memory_surface_context + bb7_exo_get_recent_activity separately. |

### `ai_system_integration_fixed.py`

**Group:** Autonomy substrate
**Role:** Registry-visible AI/system integration shim currently exposing a narrow integration capability.

| Surface | Description |
|---|---|
| `bb7_system_comprehensive_operation` | (no inline description) |

### `meta_intelligence_engine.py`

**Group:** Autonomy substrate
**Role:** Registry-bound meta-intelligence facade: context weaver, code consciousness, creative solver, MuadDib/Mentat bridge.

| Surface | Description |
|---|---|
| `bb7_code_consciousness` | Registry-bound architectural consciousness: compiles code analysis, project context, memory substrate, and Lisan recall without instantiating sibling tools. |
| `bb7_context_weaver` | Registry-bound context synthesis across workspace, memory, session continuity, recent changes, and Lisan context resurrection. |
| `bb7_creative_problem_solver` | Registry-bound problem decomposition that uses Lisan intent and memory context when available, then emits bounded execution-ready subproblems. |
| `bb7_muadib_mentat_bridge` | Read-only one-plane bridge snapshot across Muad'Dib checkpoint state, exoskeleton health, and Mentat conductor artifacts. Uses the live registry and bounded Mentat file reads; treats mcp_server.py as gateway into Muad'Dib/tools and does not instantiate sibling tools or mutate weights, Q-table state, server lifecycle, or output adapters. |

## 4. Runtime-tools leaf-file status

Leaf docs should be treated as optional expansion notes beneath this README. Keep them only when they match active source truth.

| Leaf file | Current status |
|---|---|
| `runtime-tools/ai-system-integration.md` | satellite / expansion note |
| `runtime-tools/auto-tool-module.md` | satellite / expansion note |
| `runtime-tools/code-analysis-tool.md` | active expansion note; should stay aligned with this README |
| `runtime-tools/enhanced-code-analysis-tool.md` | active expansion note; should stay aligned with this README |
| `runtime-tools/enhanced-web-tool.md` | active sole web-surface expansion note |
| `runtime-tools/exo-and-lisan.md` | satellite / expansion note |
| `runtime-tools/file-tool.md` | satellite / expansion note |
| `runtime-tools/memory-and-mem-interconnect.md` | satellite / expansion note |
| `runtime-tools/meta-intelligence-engine.md` | satellite / expansion note |
| `runtime-tools/muaddib-network.md` | satellite / expansion note |
| `runtime-tools/openrouter-agent-tool.md` | satellite / expansion note |
| `runtime-tools/openrouter-planner-tool.md` | satellite / expansion note |
| `runtime-tools/project-context-tool.md` | active expansion note; should stay aligned with this README |
| `runtime-tools/session-manager-enterprise.md` | stale after `session_manager_enterprise.py` retirement; merge useful prose into this README or `session-tool.md`, then archive/remove |
| `runtime-tools/session-tool.md` | active session_manager_tool expansion note |
| `runtime-tools/shell-tool.md` | active expansion note; should stay aligned with this README |
| `runtime-tools/thought_journal_tool.md` | satellite / expansion note |
| `runtime-tools/visual-tool.md` | satellite / expansion note |
| `runtime-tools/vscode-terminal-tool.md` | active expansion note; should stay aligned with this README |

## 5. Validation posture

Use source/schema checks for code edits and live BB7 calls only for live process truth. Do not infer current-source parity from a still-running stale stdio child.

```bash
cd /home/daeron/Somnus-MCP
mcp.venv/bin/python -m py_compile mcp_server.py tools/*.py
mcp.venv/bin/python -m json.tool tool_manifest.json >/dev/null 2>&1 || true
codegraph sync /home/daeron/Somnus-MCP
```

Live/source parity check after reload:

```text
bb7_tool_health_report(include_failed_loads=true, include_failed_calls=true)
```

Expected post-reload source truth for this pass: no failed source loads from `project_context_tool (1)` or `session_manager_enterprise`; `bb7_security_audit` origin should be enhanced code analysis because baseline code analysis loads before enhanced code analysis.
