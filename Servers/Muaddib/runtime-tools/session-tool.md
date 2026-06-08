### Session Continuity Substrate (`session_manager_tool.py`)

> **bb7_ Doctrine.** Every `bb7_*` method below is a *compiled* tool, not a raw function. The method body wraps session lifecycle (start/pause/resume), episodic + semantic + procedural memory formation, and pattern learning with auto-memory capture, cross-process file locking (`_with_file_lock`), atomic JSON writes (`_write_json_atomic`), and Ebbinghaus-aware importance scoring (`_calculate_content_importance`). bb7_ methods can call each other and compose across tools — see the **Pairing** note for cross-tool composition.

> **Pairing with Memory Continuity Substrate (`memory_tool.py` + `memory_interconnect.py`).** Session is the temporal wrapper; memory is the persistent substrate. `EnhancedSessionTool` instantiates `EnhancedMemoryTool` directly and is the primary caller of `bb7_memory_store`, `bb7_memory_surface_context`, and `bb7_journal_linked_entries`. At session start, the tool auto-surfaces the top-3 most relevant prior memories for the goal (proactive recall). During the session, `_auto_capture_memory` writes breakthrough / insight / achievement / decision / pattern events into the long-term memory store under `session_{id8}_{event_type}_{ts}_{hash8}` keys with importance auto-scored from content keywords, length, and tech-signal density. `bb7_link_memory_to_session` writes the reverse map (`memory_index.json`) so journal entries and memory retrievals can be traced back to the session that produced them. bb7_ chain: `bb7_start_session` → `_auto_capture_memory` → `memory.store` → `memory_interconnect.analyze_memory_entry` → re-indexed for the next session's `bb7_get_session_insights`.

Tools for cognitive session management, automatic memory formation, and productivity tracking.

#### `bb7_start_session`

Start a new enhanced cognitive session with intelligence.
**Internal Composition**: Persists a session file under `data/sessions/{session_id}.json` and an index entry under `session_index.json`, then proactively surfaces up to 3 relevant prior memories via `EnhancedMemoryTool.surface_context()`. The session object holds episodic (events/timeline/breakthroughs/obstacles), semantic (concepts/insights/relationships), and procedural (workflows/patterns) buckets plus intelligence counters.

- **Parameters**:
  - `goal` (string, required): The goal of the session.
  - `context` (string, optional): Additional context for the session.
  - `tags` (array, optional): A list of tags for the session.

#### `bb7_pause_session`

Pause the current active session, capturing environment state for later resumption.
**Internal Composition**: Sets `status="paused"` on the session, captures environment via `_capture_environment_state()` (cwd + git branch), logs a `session_paused` event, and removes the session from the active slot. The session file persists; resume rehydrates it.

- **Parameters**:
  - `reason` (string, optional): Reason for pausing.

#### `bb7_resume_session`

Resume a previously paused session by its ID.
**Internal Composition**: Loads the session file under cross-process file lock, sets `status="active"`, and rehydrates `current_session_id` / `current_session` on the tool instance.

- **Parameters**:
  - `session_id` (string, required): The ID of the session to resume.

#### `bb7_list_sessions`

List all sessions with filtering by status and limit.
**Internal Composition**: Reads `session_index.json`, filters by status, sorts newest-first, and renders each entry with goal + created-at + tags. Returns at most `limit` entries.

- **Parameters**:
  - `status` (string, optional): Filter by status (e.g., `active`, `paused`).
  - `limit` (number, optional): Maximum number of sessions to return.

#### `bb7_log_event`

Log significant events during a session (breakthroughs, achievements, obstacles) with auto-memory capture.
**Internal Composition**: Appends to the session's episodic event log + timeline, categorises into breakthroughs/obstacles/achievements buckets, and triggers `_auto_capture_memory` for high-value event types (`breakthrough`, `major_insight`, `critical_discovery`, `achievement`, `milestone`, `decision`, `solution`) or when content crosses the auto-memory worthiness threshold (keyword match, length > 200, learning-accelerator trigger).

- **Parameters**:
  - `event_type` (string, required): Type of event (e.g., `breakthrough`, `obstacle`).
  - `description` (string, required): Description of the event.
  - `details` (object, optional): Additional structured details.

#### `bb7_capture_insight`

Capture key insights and connect them to concepts and other memories.
**Internal Composition**: Appends to the session's `semantic.key_insights`, updates the per-concept evolution record (`importance_score += 0.1`, capped at 1.0), records relationships in `semantic.relationships` with strength scores from `_calculate_relationship_strength`, and auto-captures into long-term memory when importance > 0.6.

- **Parameters**:
  - `insight` (string, required): The insight to capture.
  - `concept` (string, required): The concept the insight is related to.
  - `relationships` (array, optional): List of related concepts.

#### `bb7_record_workflow`

Record a procedural workflow or pattern discovered during the session.
**Internal Composition**: If a workflow with the same name already exists in `procedural.workflows`, increments its `frequency` and updates its `steps` + `last_used`; otherwise appends a new entry. Workflows are surfaced in `bb7_get_session_insights` and `bb7_cross_session_analysis`.

- **Parameters**:
  - `workflow_name` (string, required): Name of the workflow.
  - `steps` (array, required): List of steps in the workflow.
  - `context` (string, optional): Additional context.

#### `bb7_update_focus`

Update current attention focus, energy level, and momentum state.
**Internal Composition**: Writes the focus tuple into `metadata.attention_focus / energy_level / momentum / focus_updated`, then logs a `focus_shift` event including the energy level so `_extract_energy_progression` can build the per-session trajectory.

- **Parameters**:
  - `focus_areas` (array, required): List of areas currently being focused on.
  - `energy_level` (string, optional): Current energy level (e.g., `high`, `low`).
  - `momentum` (string, optional): Current momentum state.

#### `bb7_link_memory_to_session`

Manually link a persistent memory key to the current session context.
**Internal Composition**: Writes a union-merged entry into `data/sessions/memory_index.json` under both `memory_to_sessions[memory_key]` and `session_memories[current_session_id]`. Reverse map enables `bb7_journal_linked_entries` and `bb7_memory_get_related` to surface session provenance.

- **Parameters**:
  - `memory_key` (string, required): The key of the memory to link.

#### `bb7_auto_memory_stats`

Get statistics on how many memories have been automatically captured during the current session.
**Internal Composition**: Reads `current_session.intelligence.auto_captured_memories` counter (incremented inside `bb7_log_event` and `bb7_capture_insight` whenever `_auto_capture_memory` fires). Returns a formatted string summary.

#### `bb7_get_session_summary`

Get a comprehensive summary of a specific session's history, insights, and workflows.
**Internal Composition**: Reads the session file and renders header (goal, created, last_updated, status, tags) + last 10 episodic events + top 5 concepts by insight count + last 5 key insights + workflows with frequency + current focus / energy / momentum. Lightweight read-only surface.

- **Parameters**:
  - `session_id` (string, required): The ID of the session.

#### `bb7_get_session_insights`

Get intelligent analysis and metrics for a specific session (auto-memories, concept network).
**Internal Composition**: Reads the session file and renders an intelligence report: duration, auto-captured memory count, event/breakthrough/obstacle/achievement totals, top 5 concepts by importance score, learned workflows, and success indicators (duration > 30 min + insight count > 2 + auto-memories > 3).

- **Parameters**:
  - `session_id` (string, optional): The ID of the session (defaults to current).

#### `bb7_cross_session_analysis`

Analyze patterns, success factors, and evolving concepts across multiple recent sessions.
**Internal Composition**: Loads the session index, reads all session files newer than `days_back`, computes common goal themes via `Counter(goal_words).most_common(5)`, classifies sessions as successful (success_score ≥ 3 from duration + insights + auto-memories), aggregates success factors from `metadata.attention_focus`, and lists evolving concepts (those appearing in 2+ sessions).

- **Parameters**:
  - `days_back` (number, optional): Number of days to look back.

#### `bb7_session_recommendations`

Generate intelligent recommendations based on past sessions.
**Internal Composition**: Thin lambda wrapping `_generate_session_recommendations(goal)`. Computes goal-word Jaccard similarity against past session goals, returns top 5 similar sessions, derives success factors from `learned_patterns.successful_workflows`, computes `success_probability = min(0.9, 0.5 + 0.1 * len(similar_sessions))`, and picks `optimal_duration` as the max observed across matching workflows. Output is `json.dumps(..., indent=2)`.

- **Parameters**:
  - `goal` (string, required): The goal of the new session.

#### `bb7_learned_patterns`

Get the learned patterns from sessions.
**Internal Composition**: Thin lambda returning `json.dumps(self.learned_patterns, indent=2)`. The patterns store holds `{successful_workflows, common_obstacles, productivity_patterns, decision_patterns, learning_accelerators}` — populated incrementally by `_analyze_session_patterns` and consumed by `_is_memory_worthy` and `bb7_session_recommendations`.

#### `bb7_session_intelligence`

Get the session intelligence data.
**Internal Composition**: Thin lambda returning `json.dumps(self.session_intelligence, indent=2)`. The intelligence store holds `{session_success_predictors, optimal_session_lengths, focus_transition_patterns, energy_level_correlations, goal_achievement_factors}` — derived from cross-session analysis and used to drive `_generate_session_recommendations`.
