### Exoskeleton Tools (`exoskeleton_tool.py`)

Control-plane layer providing stateful, Bayesian tool routing, plan execution checkpointing, and multi-AI coordination. All routing decisions improve over time via Beta-distribution priors updated on each `bb7_exo_reflect` call.

#### `bb7_exo_bootstrap`

Initializes capability context for a turn. Returns current tool index counts, category distribution, manifest status, and active tool priors/diagnostics.
**Internal Composition**: Synthesizes the runtime environment state by orchestrating calls to `_refresh_catalog_from_manifest_if_changed`, `_maybe_sync_live_tools`, and `_tool_prior_diagnostics` to ensure the session operates on fresh tool priors.

- **Parameters**:
  - `include_recent_outcomes` (boolean, optional): Include recent plan outcomes in payload (default: `true`).
  - `include_healthcheck` (boolean, optional): Include live tool health check (default: `true`).

#### `bb7_exo_list_tool_categories`

List all tool categories with sample tool names and neighboring categories.

#### `bb7_exo_category_specific_tools`

List all tools in a specific category, sorted by reliability, with required params.

- **Parameters**:
  - `category` (string, required): Category name (e.g., `memory`, `file`, `shell`).
  - `limit` (integer, optional): Max tools to return (default: 20).

#### `bb7_exo_route`

Retrieve ranked candidate tools for an intent using TF-IDF semantic scoring, category graph neighbors, and Beta-distribution reliability priors.
**Internal Composition**: Compiles results from `_SpectralIntentDecomposer` for semantic intent matching and `_ThompsonContextualBandit` for Bayesian posterior sampling to provide context-conditioned tool routing.

- **Parameters**:
  - `intent` (string, required): The task or goal to find tools for.
  - `max_candidates` (integer, optional): Number of candidates to return (default: 12).
  - `include_neighbors` (boolean, optional): Include category-graph neighbors (default: `true`).
  - `neighbor_distance` (integer, optional): Graph hop distance for neighbors, 0-3 (default: 1).

#### `bb7_exo_plan`

Generate candidate multi-step execution chains.
**Internal Composition**: Delegates to `_MCTSPlanner` for Monte Carlo tree search when lisan subsystems are active. Runs 100 simulations with adversarial failure injection, using `bb7_dt_encode_catalog` for neural value function estimation, and selects Pareto-optimal branches. Falls back to beam search (`_make_plans`) when lisan subsystems are unavailable. Returns ranked plans with confidence scores, token estimates, failure points, and fallback chains.

- **Parameters**:
  - `intent` (string, required): The task or goal to plan for.
  - `context` (string, optional): Additional context to incorporate into scoring.
  - `beam_width` (integer, optional): Number of candidate plans to generate, 1-6 (default: 3).
  - `max_chain_length` (integer, optional): Maximum steps per plan, 2-8 (default: 4).

#### `bb7_exo_reflect`

Update Beta priors after execution and append a row to the execution history JSONL.
**Internal Composition**: Acts as a state synthesizer that calls `_apply_reflect_mutations` to update `_ThompsonContextualBandit` priors, updates the `_TopologicalMomentumManifold` via `_update_session_momentum`, and injects neural attention weights from the Digital Twin into the momentum graph.

- **Parameters**:
  - `plan_id` (string, required): Plan identifier from `bb7_exo_plan`.
  - `tools_used` (array or string, required): List (or comma-separated string) of tools executed.
  - `success` (boolean, required): Whether the execution succeeded.
  - `error` (string, optional): Error message if execution failed.
  - `intent` (string, optional): Original intent, used to update intent-to-tool mappings.
  - `recovery_strategy` (string, optional): What recovery was applied, if any.

#### `bb7_exo_state`

Return raw exoskeleton state: top tool priors, top chain priors, discovered macros, and known recovery strategies.

- **Parameters**:
  - `limit` (integer, optional): Max rows per section (default: 15).

#### `bb7_exo_get_recent_activity`

Get recent activity from all AI instances for multi-AI coordination.

- **Parameters**:
  - `limit` (integer, optional): Max entries per section (default: 10).

#### `bb7_exo_briefing`

Generate a natural-language markdown briefing for the current intent.

- **Parameters**:
  - `intent` (string, required): The user-facing goal or task description.
  - `max_recommendations` (integer, optional): Max tools to surface (default: 5).

#### `bb7_exo_preemptive_recovery`

Analyse a planned workflow for failure risks before execution.

- **Parameters**:
  - `intent` (string, required): The task intent to plan for.
  - `risk_tolerance` (string, optional): `conservative`, `moderate`, or `aggressive` (default: `moderate`).

#### `bb7_exo_route_focused`

Token-efficient routing: return only the top-N tools with a one-liner each.

- **Parameters**:
  - `intent` (string, required): The task intent.
  - `top_n` (integer, optional): Number of tools to surface, 1-15 (default: 5).

#### `bb7_exo_execute_step`

Record a single step execution in a checkpointed plan.

- **Parameters**:
  - `plan_id` (string, required): Plan identifier from `bb7_exo_plan`.
  - `step_index` (integer, required): 0-based index of the step in the chain.
  - `tool_name` (string, optional): Tool that was executed.
  - `result_summary` (string, optional): Brief description of the step outcome.
  - `success` (boolean, optional): Whether the step succeeded (default: `true`).
  - `dry_run` (boolean, optional): Preview the mutation without writing to disk (default: `false`).

#### `bb7_exo_resume_plan`

Resume a checkpointed plan from where it left off.

- **Parameters**:
  - `plan_id` (string, optional): Plan identifier to resume.

#### `bb7_exo_kpi_report`

Generate a KPI report for one or all active plans.

- **Parameters**:
  - `plan_id` (string, optional): Specific plan to report on.

#### `bb7_exo_suggest_next`

Orchestration prediction: suggest next tools/actions given current context. Key for chaining memory→analysis→execution workflows.

- **Parameters**:
  - `current_tool` (string, optional): Tool that was just executed (for momentum prediction).
  - `current_category` (string, optional): Category of current work (alternative to current_tool).
  - `intent` (string, optional): Optional intent to find next steps for.

#### `bb7_lisan_recall` (2026-04-10 ADDED)

Context Resurrection: single-call session recovery for long-horizon tasks.
**Internal Composition**: Compiles context by orchestrating calls to `bb7_memory_surface_context` for BM25 memory retrieval, reading `active_plans.json` and `cross_ai_activity.jsonl`, generating topological momentum context via `_get_momentum_context()`, and surfacing decisions via `CognitiveJournalSubsystem`.

- **Parameters**:
  - `context` (string, required): Current task description or session context text.
  - `max_memories` (number, optional): Max memories to surface (default: 5).
  - `include_plans` (boolean, optional): Include active plan checkpoints (default: true).
  - `include_activity` (boolean, optional): Include cross-AI activity (default: true).
  - `include_decisions` (boolean, optional): Include prior decisions from cognitive journal (default: true).

#### `bb7_lisan_distill` (2026-04-10 ADDED)

Explicit distillation: log a complete LLM trajectory for RFT training data.
**Internal Composition**: Delegates entirely to `DistillationSubsystem.log_full_trajectory` and `DistillationSubsystem._evaluate_heuristics` to store and analyze agent session telemetry.

- **Parameters**:
  - `trajectory` (array, required): List of message dicts (role/content/tool_calls).
  - `source_plane` (string, optional): Origin identifier (default: bb7_agent_harness).
  - `session_id` (string, optional): Session identifier (auto-detected if omitted).
  - `total_tokens` (number, optional): Total tokens consumed.
  - `latency_seconds` (number, optional): Wall-clock seconds.
  - `tool_error_count` (number, optional): Number of tool errors encountered.

#### `bb7_lisan_intend` (2026-04-10 ADDED)

Expose spectral intent analysis as a direct tool.
**Internal Composition**: Compiles analysis directly from `_SpectralIntentDecomposer.spectral_similarity()` and `_SpectralIntentDecomposer.entropy_gate()`, along with topological momentum bonuses, synthesizing internal reasoning into an externally accessible representation.

- **Parameters**:
  - `user_message` (string, required): The user's natural language message or task description.
  - `verbosity` (string, optional): Output verbosity — minimal | normal | detailed (default: normal).

#### `bb7_dt_advanced_features`

Query Muad'Dib advanced modality features for candidate tools.
**Internal Composition**: Wraps `DigitalTwinTool.bb7_dt_advanced_features` with session defaults, returning per-tool provenance-tagged scores when `MUADIB_ADVANCED_MODE=1`. Always safe to call — returns `{ok: False, reason: ...}` when the bridge is off or the neural twin is unavailable.

- **Parameters**:
  - `candidates` (array, required): List of tool names to evaluate.
  - `category` (string, optional): Tool category context (default: `misc`).
  - `session_id` (string, optional): Session identifier (defaults to active session).
  - `recent_tools` (array, optional): Recent tool names for co-occurrence signal (defaults to session history).

#### `bb7_dt_self_play`

Run bounded Muad'Dib self-play against the live tool catalog.
**Internal Composition**: Delegates to `DigitalTwinTool.bb7_dt_self_play`, training an isolated candidate policy/value head, saving real tensor weights as safetensors, and promoting only when explicitly requested after a complete atomic checkpoint write. JSON is metadata/ledger only.

- **Parameters**:
  - `episodes` (integer, optional): Number of bounded self-play episodes (default: 32, max: 512).
  - `max_steps` (integer, optional): Tools per simulated episode (default: 4, max bounded by self-play config).
  - `learning_rate` (number, optional): Optional AdamW learning rate override.
  - `promote` (boolean, optional): Request promotion of the complete candidate safetensors checkpoint to active head (default: false / archive-only). Ignored when the active promotion lock is set.
  - `update_qtable` (boolean, optional): Whether synthetic self-play should also update the real Q-table (default: false).
  - `session_id` (string, optional): Session identifier for optional synthetic Q-table observations.

#### `bb7_dt_self_play_lock`

Lock or unlock Muad'Dib self-play active-head promotion.
**Internal Composition**: Delegates to `DigitalTwinTool.bb7_dt_self_play_lock` to pin or release the active/champion self-play head. Continuous self-play may still train and archive candidate safetensors checkpoints while the active head is locked.

- **Parameters**:
  - `locked` (boolean, optional): True to pin active/champion weights; false to allow promotion again.
  - `reason` (string, optional): Optional operator-readable reason persisted to checkpoint metadata.
  - `operator` (string, optional): Optional actor/source label for the lock mutation (default: `exoskeleton`).

#### `bb7_dt_checkpoint_status`

Inspect Muad'Dib tokenizer and self-play checkpoint state.
**Internal Composition**: Delegates to `DigitalTwinTool.bb7_dt_checkpoint_status`, returning active safetensors pointers, promotion-lock state, and legacy `.pt` migration fallback files.

### Lisan al-Gaib Prescient Subsystems (`lisan_al_gaib.py`)

The prescient engines that compose the `bb7_*` tool responses. None of these are MCP tool surfaces on their own — they are instantiated and orchestrated by `ExoskeletonTool` (and by `bb7_agent_harness` for distillation) to deliver the live "compiling a smarter answer" behaviour of the `bb7_*` endpoints. Six novel subsystems fused into a single prescient intelligence layer: Spectral Intent Decomposition, Thompson Sampling with Contextual Bandits, Monte Carlo Tree Search Planning, Topological Momentum Manifold, Narrative Synthesis Cortex, and Autonomous Meta-Learning — plus the Golden Path / Session Momentum / Cognitive Journal / Distillation stack that the exoskeleton consumes.

#### `_SpectralIntentDecomposer` (internal subsystem)

Character n-gram TF-IDF with positional decay for intent matching. Produces a multi-dimensional spectral signature that is robust to typos, partial matches, and morphological variation. When Muad'Dib neural embeddings are cached, blends them at 30% weight inside `spectral_similarity()`.
**Composition in BB7 plane**: Driven by `_SpectralIntentDecomposer.spectral_similarity()` and `_SpectralIntentDecomposer.entropy_gate()` in `bb7_lisan_intend`; blends through `_score_tools()` for every candidate in `bb7_exo_route` and `bb7_exo_route_focused`. Spectral IDF is rebuilt from the live tool catalog during `_refresh_spectral_catalog()`.

- **Key methods**:
  - `rebuild_idf(tool_catalog: Dict)`: Recompute smoothed log IDF weights from the full tool catalog corpus.
  - `inject_neural_embeddings(embeddings: Dict[str, List[float]])`: Cache Muad'Dib per-tool embeddings for the 30% neural blend.
  - `spectral_similarity(query, tool_text, tool_name="")`: Cosine similarity in positional-TF-IDF n-gram space, optionally blended with neural cosine.
  - `entropy_gate(category_scores, epsilon=0.15)`: Broadens vs. narrows category candidates based on Shannon entropy and top-2 gap.

#### `_ThompsonContextualBandit` (internal subsystem)

Bayesian posterior sampling with context conditioning. Each scoring call draws from `Beta(α, β)`, naturally balancing exploration vs exploitation. Old observations decay at `tau=0.995`, and per-category `context_modifiers` allow a tool to have high reliability for one intent class and low for another. Accepts a `neural_q_bonus` from Muad'Dib that shifts alpha proportionally before sampling.
**Composition in BB7 plane**: Called exclusively from `_reliability_sampled()` inside `bb7_exo_route` / `bb7_exo_route_focused` / `bb7_exo_plan` — the only place where exploration noise is desirable. Chain confidence and failure analysis still use the deterministic `_reliability()` mean.

- **Key methods**:
  - `draw(prior, context_category="", neural_q_bonus=0.0)`: One Thompson sample in `[0.0, 1.0]`.
  - `decay_prior(prior)`: Apply exponential recency decay in-place toward uniform.
  - `update_prior(prior, success, context_category="")`: Apply decay, then add the new observation, then bump per-category modifiers.
  - `counterfactual_regret(chosen_reward, best_possible_reward)`: Non-negative single-round regret.
  - `mean(prior)`: Deterministic posterior mean for non-stochastic paths.

#### `_MCTSPlanNode` (internal subsystem)

Single node in the MCTS search tree for plan exploration. Each node represents a partial tool chain at a specific depth. Children are candidate next-tools. Tracks `visits` and `cumulative_reward` for UCB1 scoring, with a slot-tight `__slots__` declaration to keep allocation cheap across thousands of rollouts.
**Composition in BB7 plane**: Internal to `_MCTSPlanner.search()` and never referenced by BB7 tools directly. `_extract_chain()` walks from a node back to the root to recover the candidate plan.

#### `_MCTSPlanner` (internal subsystem)

Monte Carlo Tree Search for tool chain discovery. UCB1 balances between high-confidence chains and unexplored combinations. Adversarial failure injection (default 15% per node) stress-tests plans before they are returned. Pareto-optimal selection ranks on the (confidence, token-cost) frontier. Optional `neural_value_fn` from Muad'Dib blends at 30% with the reliability-based reward.
**Composition in BB7 plane**: Drives `bb7_exo_plan` whenever Lisan subsystems are loaded. Runs 100 simulations per plan request, expands with Lévy flight heavy-tailed sampling (`α=1.5`), and emits `mcts: true`, `tree_reward`, `adversarial_survived`, `fallback`, and `plan_id` prefixed `mcts_` plans. Falls back to the static `_make_plans` beam search when not loaded.

- **Key methods**:
  - `search(ranked_tools, tool_catalog, reliability_fn, token_estimate_fn, beam_width=3, max_chain_length=4, simulations=60, neural_value_fn=None)`: Run MCTS and return Pareto-optimal plan dicts.
  - `_adversarial_test(chain, reliability_fn, n_trials=5)`: Returns True when the plan survives >60% of stress trials.
  - `_pareto_filter(plans)`: Filter plans to the (confidence, -tokens) Pareto frontier.

#### `_TopologicalMomentumManifold` (internal subsystem)

Session momentum through topological analysis of tool flow. Maintains three fused signals: (1) exponential-decay attention with `λ=0.7`, (2) spectral graph momentum from learned category transition probabilities blended with category centrality, and (3) Wasserstein-1 change-point detection (Kantorovich–Rubinstein metric, 1D closed form) with an adaptive threshold that grows with session length. When Muad'Dib neural attention weights are injected, the blend is 50% transition + 20% neural + 30% centrality.
**Composition in BB7 plane**: Delegated to from both `_update_session_momentum()` and `_compute_momentum_bonus()` in `ExoskeletonTool`. The V3 manifold's 7-signal bonus replaces weak symbolic momentum via `max(symbolic, V3)` so a strong manifold signal does not double-count.

- **Key methods**:
  - `record_event(tool_name, category, timestamp)`: Append a tool invocation and run change-point detection.
  - `attention_score(tool_name, category)`: Geometric-decay attention in `[0.0, ~1.0]` modulated by dampening.
  - `inject_neural_attention(attention_weights)`: Cache Muad'Dib per-category attention weights.
  - `spectral_graph_momentum(category, transition_matrix)`: Transition × centrality momentum with optional 20% neural blend.
  - `get_dampening()`: Returns the Wasserstein-derived dampening factor in `[0.3, 1.0]`.
  - `get_recent_categories(n=3)` / `get_session_length()`: Read-only accessors for the session window.

#### `GoldenPathOracle` (public subsystem)

Prescient navigation layer for proven workflows. Loads `golden_paths.json` at boot, filters executable entries (chain + priors sanity), and matches user intents through spectral cosine similarity + Fisher information weighting (rare n-gram overlap ∝ IDF², squashed by `tanh`). Entropy-gated disambiguation logs ambiguity when the top-2 matches are within 0.05.
**Composition in BB7 plane**: First-pass matcher in `_match_golden_path()`; consulted by `bb7_exo_route`, `bb7_exo_plan`, and `bb7_lisan_intend`. The `seed_chain_priors()` method is invoked at startup so new sessions inherit wisdom from the collective.

- **Key methods**:
  - `match_golden_path(intent)`: Spectral + Fisher composite match; returns best path dict or `None`.
  - `seed_chain_priors(chain_priors)`: In-place seed of executable chain priors; returns count of seeded chains.
  - `_rebuild_spectral_index()`: Rebuilds the spectral IDF from the golden path corpus after auto-promotion or manifest changes.

#### `SessionMomentum` (public subsystem)

Session-level momentum tracker with manifold delegate. Maintains a 5-tool recency ring, a 3-category recency list, a full sequence, intent history, and an active-workflow pointer. Online-learns a per-row transition probability matrix that normalises on every update.
**Composition in BB7 plane**: Wired into `ExoskeletonTool` via `self._session_momentum`. `update()` is called from `_update_session_momentum()` after every `bb7_exo_reflect`; `compute_momentum_bonus()` returns the 7-signal V3 momentum bonus consumed by `_compute_momentum_bonus()` in the routing scorer.

- **Key methods**:
  - `update(tool_name, category, intent, golden_paths)`: Record an event, run change-point detection, update transition probabilities, and detect an active golden path.
  - `compute_momentum_bonus(tool_name, tool_category)`: 7-signal momentum bonus in `[0.0, 0.30]` after Wasserstein dampening.
  - `get_context_narrative()`: Natural-language session-momentum paragraph for `bb7_exo_briefing`.

#### `_MetaLearningEngine` (internal subsystem)

Autonomous meta-learning: (1) weight tuning via online Brier score gradient descent with EMA smoothing, (2) golden path discovery by mining execution traces for chains that hit `golden_path_min_occurrences` (default 4) at `golden_path_min_success_rate` (default 0.8), (3) capability graph evolution through category co-occurrence, (4) system health scoring from prediction accuracy, exploration ratio, and freshness.
**Composition in BB7 plane**: Internal to the orchestrator; not directly surfaced as a BB7 tool. Predictions are logged from `_score_tools()` and consulted during the weight-adjustment cycle. Discovered golden paths flow back into `golden_paths.json` via the auto-promotion path.

- **Key methods**:
  - `log_prediction(tool_name, predicted_reliability, actual_success, context_category="")`: Log a prediction/outcome pair.
  - `compute_weight_adjustment()`: Per-component EMA-smoothed Brier gradient → multiplier dict clamped to `[0.80, 1.25]`.
  - `discover_golden_paths(execution_history)`: Mine successful chains; return promotion candidates.
  - `system_health_score(tool_priors, recent_history_size=0)`: Health diagnostic with prediction accuracy, exploration ratio, freshness, and recommendations.

#### `NarrativeEngine` (public subsystem)

Narrative Synthesis Cortex. Transforms quantitative routing into reasoning scaffolds. Confidence-calibrated language (Bayesian credible intervals, e.g. `94% ± 5% (high confidence)`), token-budget awareness (`minimal: 150`, `normal: 600`, `detailed: 1200`), and multi-voice narrative (golden-path directive voice, exploration curious voice, recovery cautious voice). Uses Thompson sampling exploration scores from the bandit to surface `_get_unexplored_tools()`.
**Composition in BB7 plane**: Invoked from `bb7_lisan_intend` when `verbosity="detailed"` and Lisan subsystems are available. The narrative string is included in the response payload as the `narrative` field.

- **Key methods**:
  - `generate_briefing(intent, intent_category, top_tools, best_chain, golden_match, momentum, include_exploration, verbosity, tool_priors=None)`: Returns the formatted markdown narrative truncated to the token budget.
  - `_minimal_briefing(intent, top_tools)`: One-line directive used for the `verbosity="minimal"` short-circuit.
  - `_format_golden_path(golden_match)`, `_format_learned_chain(best_chain)`, `_format_tool_list(...)`: Section formatters.

#### `TrajectoryBuilder` (public subsystem)

Step accumulator for a single agent run. Field-driven dataclass holding session id, source plane, start time, ordered steps, thought-journal entries, intent provenance, memory context at start, parent/linked trajectory ids, and a monotonic step counter.
**Composition in BB7 plane**: Created by `TelemetryDistillationEngine.new_trajectory_builder()` and consumed by `TelemetryDistillationEngine.finalize_builder()`. Surface area: `add_step()`, `add_journal_entry()`, `set_intent_provenance()`, `set_memory_context()`.

- **Key methods**:
  - `add_step(role, content=None, tool_calls=None, tool_call_id=None, reasoning=None, latency_ms=None, error=None)`: Append one message to the trajectory with offset timing.
  - `add_journal_entry(journal_id, summary)`: Record a thought-journal cross-link.
  - `set_intent_provenance(raw_input, lisan_intent=None, exo_route=None)`: Snapshot intent decomposition for replay.
  - `set_memory_context(surfaces, signals_active, injection_boost)`: Snapshot memory surfaces at session start.

#### `TelemetryDistillationEngine` (public subsystem)

V2 Distillation Engine for Sovereign MCP. Captures lossless cognitive trajectories for Reinforcement Fine-Tuning on a queue-backed daemon writer thread — the agent hot path never blocks on disk I/O. Daily shard rotation under `<data_dir>/distillation_dataset/trajectories_<YYYY-MM-DD>.jsonl`. Schema version `2.0`. Downstream domino hooks fire automatically after each successful disk write.
**Composition in BB7 plane**: Wrapped by the `bb7_lisan_distill` endpoint in `ExoskeletonTool`, which calls `log_full_trajectory()` and `_evaluate_heuristics()` and returns a `trajectory_id` plus heuristic signals. V1-compatible `log_mcp_rpc_stub()` is preserved for external clients (Cursor/Claude) that only have RPC boundaries.

- **Key methods**:
  - `new_trajectory_builder(source_plane, session_id, parent_trajectory_id=None)`: V2 factory for incremental `TrajectoryBuilder` accumulation.
  - `finalize_builder(builder, telemetry=None)`: V2 enqueue + return `trajectory_id` without blocking.
  - `log_full_trajectory(source_plane, session_id, trajectory, telemetry=None, ...)`: V1-compatible primary method; non-blocking.
  - `log_mcp_rpc_stub(method_name, arguments, result, latency)`: V1 RPC-boundary stub for external MCP clients.
  - `add_downstream_hook(hook)`: Register a callable fired after each successful disk write (runs in the writer thread).
  - `_evaluate_heuristics(...)`: Diagnostic heuristics (`contains_tool_error`, `deep_tool_chain`, `high_latency`, `many_iterations`) and positive auto-tags (`lisan_high_confidence`, `mcts_planned`, `memory_enriched`, `deep_clean_chain`, `planner_fallback`).

#### `StdioTranscriptCapture` (public subsystem)

Wraps `sys.stdin` / `sys.stdout` to capture the raw JSON-RPC 2.0 stream at the transport boundary. Every request frame and every response frame is written to `<transcript_dir>/stdio_<session_id>.jsonl`. The server code itself needs no changes — it still reads from `sys.stdin` and writes to `sys.stdout`. Capture failures never crash the server.
**Composition in BB7 plane**: Not directly bound to a `bb7_*` endpoint. Installed before the MCP server's stdio read loop begins to feed external-RPC trajectories into the distillation dataset. Useful for offline RFT dataset construction from third-party MCP clients.

- **Key methods**:
  - `install()`: Monkey-patch `sys.stdin` and `sys.stdout` with capturing wrappers.
  - `uninstall()`: Restore the original streams.

#### `_CapturingReader` / `_CapturingWriter` (internal helpers)

`TextIOWrapper`-based stdin and stdout wrappers used by `StdioTranscriptCapture`. Every line read or written is appended to the transcript before being returned or sent. All other stream methods are delegated to the wrapped object. Failures in capture are swallowed so the transport layer stays healthy.

#### `CognitiveJournalSubsystem` (public subsystem)

Lightweight decision provenance layer that absorbs the `thought_journal_tool` capabilities into the Lisan plane. NOT an MCP tool itself — internal API called by `ExoskeletonTool`. Five capabilities: decision provenance (decision + rationale + alternatives + constraints), conflict detection (negation-word heuristic on overlapping tokens), retrospective generation (N-day window markdown), reasoning chain tracing (follows `linked_decision_ids` recursively), and bidirectional memory linking (`memory_key` → `decision_ids` reverse map).
**Composition in BB7 plane**: Initialised inside `ExoskeletonTool.__init__`. `record_decision()` is called from `bb7_exo_reflect` with the executed chain; `record_mcts_signal()` closes the planning-training feedback loop. `surface_relevant()` is consumed by `bb7_lisan_recall` to populate the *Prior Decisions* section of the context blob. Trails are append-only JSONL at `<data_dir>/exoskeleton/decision_trail.jsonl`.

- **Key methods**:
  - `record_decision(decision, rationale, alternatives=None, constraints=None, risk_assessment="", success_criteria="", linked_memory_keys=None, linked_decision_ids=None, outcome=None, validated=None, plan_id="", tools_used=None)`: Returns `decision_id`.
  - `record_mcts_signal(decision_id, outcome, validated, mcts_planner=None)`: Patch outcome/validated and feed reward to the MCTS head.
  - `detect_conflicts(topic="", lookback_days=90)`: Negation-word contradiction scan.
  - `get_decision_trail(topic, lookback_days=90, max_results=20)`: Token-overlap scored search.
  - `generate_retrospective(lookback_days=30)`: Structured markdown retrospective.
  - `surface_relevant(context_text, max_results=5)`: Replaces `bb7_journal_surface_relevant` for session resumption.
  - `get_reasoning_chain(decision_id)`: Recursively follows `linked_decision_ids`.
  - `linked_by_memory_key(memory_key)`: Reverse map lookup.

