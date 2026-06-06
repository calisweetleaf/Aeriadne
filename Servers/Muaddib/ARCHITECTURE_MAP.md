# Somnus Architecture Map

> **THIS IS NOT AN MCP SERVER.**
> It is a **24/7 autonomous tool neural network server** — always running, always scoring, always learning.
> `bb7_*` methods **compile smarter answers** by routing through the neural-symbolic stack before returning.
> The neural plane is the runtime truth: every answer is scored, ranked, context-aware, and connected to continuity state.

**How to use this document:** Start at the question that matches what you're trying to understand.
Each node answers one question and points you to the next level — file, line number, what to look for.
This is a traversal map, not a summary. Follow the branches.

---

## ROOT: What is the Lisan Al Ghaib?

A **24/7 autonomous neural-symbolic orchestrator** running behind JSON-RPC2/stdio, SSE, HTTPS, and webhook transport adapters.
It is already alive before any model joins it. Client-side golden-path behavior improves the quality and explicitness of routing/reflection, but the runtime also maintains autonomous cycles, live-state sync, telemetry, ambient memory exchange, and neural checkpoints without being reduced to a passive tool rack.

**Four layers, read in this order. Important: `mcp_server.py` is the gateway into the 4-7 Muad'Dib + `tools/` cognition layers, not the intelligence itself.**

```
mcp_server.py                      →  gateway/dispatcher: transports, registry, raw JSON boundary, lifecycle telemetry
  └── tools/exoskeleton_tool.py    →  cognitive backbone, bb7_* answer compilation surface
        └── tools/lisan_al_gaib.py →  intent decomposition, MCTS planning, Thompson bandit, golden path oracle
              └── muadib/muaddib.py + advanced_bridge.py
                     →  Muad'Dib neural substrate: Q-table TD-learning + provenance-tagged feature bridge
                        bb7_dt_* surface (internal, not registered standalone)
```

**bb7_* do NOT just execute tasks.** They route your request through:
1. Spectral intent decomposition (Lisan)
2. Thompson-sampled reliability scoring
3. SessionMomentum V3 (Wasserstein + 7-signal manifold)
4. Neural Q-bonus from Digital Twin
5. Advanced bridge features (trained_q + co-occurrence, when `MUADIB_ADVANCED_MODE=1`)
...and return a smarter answer than any single tool would produce alone.

---

## BRANCH A: How does a tool call flow?

**Entry point:** `mcp_server.py:3116` → `handle_call_tool()`

1. Receives `tools/call` JSON-RPC2 request
2. Looks up tool by name in `self.tools` dict
3. **If tool name starts with `bb7_exo_`** → syncs exoskeleton catalog first (line 3194)
4. Invokes via `_invoke_tool_callable()` (line 3280) — handles both kwargs and dict-style tools
5. Appends event-spine telemetry and sovereign metadata
6. Schedules ambient tool-exchange memory/session persistence
7. Applies tool-level observation/auto-reflect paths where enabled
8. Projects dict/list payloads into a concise human-facing `content` block
   only after raw-substrate capture. Set `SOVEREIGN_DISPLAY_PROJECTION=raw`
   to show canonical raw JSON instead.

**→ If you want to understand the routing intelligence applied before execution:**
Go to BRANCH B (bb7_lisan_intend / bb7_exo_route).
Explicit route/plan calls still matter for deliberate planning; the autonomous cycle and ambient exchange continue maintaining substrate state between client calls.

**→ If you want to understand what happens after execution:**
Go to BRANCH C (continuity, observation, and learning).

---

## BRANCH B: How does the symbolic routing work?

The routing is client-initated and drive, but the server pro-actively is helping

### B1: bb7_exo_bootstrap

`tools/exoskeleton_tool.py:1781`

- Refreshes tool catalog from `tool_manifest.json`
- Syncs live tools (calls `_maybe_sync_live_tools` at line 603)
- Returns orientation and recommended-loop hints for cold starts or capability drift
- Returns healthcheck for 5 critical tools
- Returns recent outcomes (last 5) from `data/exoskeleton/exoskeleton_state.json`

**→ Call this on cold entry, workspace re-entry, capability drift, or when you need a full orientation snapshot. Do not use it as a ritual every turn.**

### B2: bb7_lisan_intend

`tools/exoskeleton_tool.py:3173`

- Takes `user_message` string
- Runs `_SpectralIntentDecomposer.spectral_similarity()` against every tool in catalog
- Applies `entropy_gate()` to avoid premature category commitment
- Calls `_match_golden_path()` (line 871) to find a pre-trained workflow
- Returns: decomposed intents, primary intent, recommended categories, momentum bonus, golden path match

**What _match_golden_path does** (`exoskeleton_tool.py:871`):

1. Tries `GoldenPathOracle` (spectral matching via lisan) first
2. Falls back to use-case substring scoring if oracle unavailable
3. Checks both `golden_paths.json` AND `auto_discovered_workflows.json`
4. Returns path data if score ≥ 1.0, else None

**→ Call this second, pass the user's message verbatim.**

### B3: bb7_exo_route OR bb7_exo_plan

`tools/exoskeleton_tool.py:1886` / `1915`

**bb7_exo_route** → calls `_score_tools()` at line 1544

`_score_tools()` scoring formula (line 1621):

```
score = (0.40 × semantic)
      + (0.20 × intent_match)
      + (0.15 × composability)    ← neighbor graph traversal
      + (0.15 × reliability)      ← Bayesian Thompson sampling prior
      - (0.10 × latency_penalty)
```

Where `semantic = 0.55 × lexical + 0.45 × spectral` (if lisan available).
Then momentum bonus applied on top (up to +0.25) via `_compute_momentum_bonus()` (line 1031).

**bb7_exo_plan** → calls `_make_plans()` at line 1673

- Generates candidate tool chains (beam search, beam_width=3)
- Saves best plan to `data/exoskeleton/active_plans.json`
- Returns plan_id for use in bb7_exo_reflect

**→ Use route for single-step tool selection. Use plan for multi-step chain planning.**

### B4: Execute actual tools

Run the tools recommended by route/plan.

### B5: bb7_exo_reflect

`tools/exoskeleton_tool.py:1980`

Pass: `plan_id`, `tools_used` (list), `success` (bool), `intent` (optional).

What happens:

1. `_apply_reflect_mutations()` (line 1292) — updates Bayesian priors (alpha/beta) per tool
2. `_update_session_momentum()` (line 936) → logs tool to `session_state["tool_sequence"]`
   → calls `_detect_active_workflow()` (line 1002) to check if sequence matches a golden path prefix
3. Appends to `data/exoskeleton/cross_ai_activity.jsonl`
4. `CognitiveJournalSubsystem.record_decision()` — logs decision provenance
5. `record_mcts_signal()` (line 2064) — propagates outcome to planner training
6. If success and chain ≥ 2 tools → `_promote_successful_chain_to_workflow()` (line 712)
   → if reliability ≥ 0.75 → `_auto_promote_to_golden_paths()` (line 799)
   → writes new entry to `golden_paths.json` (closes the learning loop)

**→ Call this after substantive execution. Direct calls still enter ambient observation paths, but explicit reflect is the high-quality chain-learning signal.**

---

## BRANCH C: What happens after execution (continuity, observation, and learning)?

Execution does not end at raw tool output. The server records and distributes
context through multiple non-blocking paths before the final display projection:

- appends event-spine telemetry under the shared data root;
- schedules ambient memory exchange so tool-call results can be searched later;
- links useful observations to the session continuity layer;
- updates tool-level health and observation metadata;
- optionally records non-blocking distillation/RFT witness traces when enabled;
- returns MCP-compliant `content` blocks to the transport client. Current-source
  gateways summarize verbose dict/list payloads as Markdown key facts and hide
  raw JSON from the display by default while marking projection metadata as
  `not_for_qtable`, `not_for_observations`, `not_for_distillation`, and
  `not_for_rft`. Raw display remains available with
  `SOVEREIGN_DISPLAY_PROJECTION=raw`.

Distillation observes trajectories retrospectively. It is not the prospective routing authority. Explicit route/plan calls and `bb7_exo_reflect` remain the deliberate control-plane path for substantial work.

---

## BRANCH D: How do golden paths work?

Golden paths are pre-trained workflow templates stored in `golden_paths.json`.
They represent collective intelligence — proven tool sequences.

**File:** `/home/daeron/Somnus-MCP/golden_paths.json`

**Structure per path:**

```json
{
  "chain": ["bb7_exo_bootstrap", "bb7_lisan_intend", "bb7_exo_route"],
  "priors": {"alpha": 8.0, "beta": 2.0},
  "use_cases": ["session start", "tool routing"],
  "description": "...",
  "tags": [...]
}
```

**How matching works:** `GoldenPathOracle.match_golden_path()` at `lisan_al_gaib.py:1283`

1. Spectral cosine similarity between intent and path document (65% weight)
2. Fisher information weighting — rare n-gram matches score higher (35% weight)
3. Threshold: composite score must be ≥ 0.15 to return a match

**Where the oracle lives:** `lisan_al_gaib.py:1191` → `GoldenPathOracle` class

**How new paths get added:**
`bb7_exo_reflect` → success + chain ≥ 2 → `_promote_successful_chain_to_workflow` (712)
→ if 5+ successes and reliability ≥ 0.75 → `_auto_promote_to_golden_paths` (799)
→ writes `auto_discovered_<name>` key to `golden_paths.json`

**Also checked:** `data/exoskeleton/auto_discovered_workflows.json` (lower bar, intermediate store)

---

## BRANCH E: How does the cognitive substrate (lisan_al_gaib.py) work?

Six subsystems, each independently instantiable:

| Subsystem | Class | Line | Purpose |
|-----------|-------|------|---------|
| Spectral decomposition | `_SpectralIntentDecomposer` | 55 | char n-gram + positional TF-IDF + entropy gate |
| Golden path oracle | `GoldenPathOracle` | 1191 | spectral matching against golden_paths.json |
| Cognitive journal | `CognitiveJournalSubsystem` | ~2400+ | decision provenance, MCTS signals |
| Distillation | `DistillationSubsystem` | ~2500+ | trajectory logging to JSONL/SQLite |
| Narrative engine | `NarrativeEngine` | ~? | LLM-optimized reasoning text generation |
| Meta-learning | embedded in oracle/exoskeleton | — | online prior updates, auto golden path discovery |

**How lisan is loaded into exoskeleton:** `exoskeleton_tool.py:19-43`

```python
from tools.lisan_al_gaib import (
    CognitiveJournalSubsystem,
    GoldenPathOracle,
    NarrativeEngine,
    _SpectralIntentDecomposer,
)
```

Instantiated at `exoskeleton_tool.py:238-268` in `ExoskeletonTool.__init__`.

**_SpectralIntentDecomposer in detail** (`lisan_al_gaib.py:55`):

- `rebuild_idf(tool_catalog)` — computes IDF from full tool corpus (smoothed log)
- `spectral_similarity(query, tool_text)` — cosine similarity in positional TF-IDF n-gram space
- `entropy_gate(category_scores)` — when top-2 scores within epsilon, broadens rather than commits

---

## BRANCH F: Naming conventions

Three layers, three prefixes:

```
bb7_<name>   →  public MCP tool surface
                 registered in ExoskeletonTool.get_tools()
                 what clients (Codex, Claude Code) call via JSON-RPC2
                 example: bb7_exo_bootstrap, bb7_lisan_intend, bb7_exo_reflect

_<name>      →  internal implementation — the actual machine
                 contains the algorithmic logic
                 called by bb7_ methods
                 examples: _score_tools (1544), _make_plans (1673),
                           _apply_reflect_mutations (1292), _update_session_momentum (936),
                           _detect_active_workflow (1002), _match_golden_path (871),
                           _reliability (1425), _compute_momentum_bonus (1031),
                           _promote_successful_chain_to_workflow (712),
                           _auto_promote_to_golden_paths (799)

cc8_<name>   →  FUTURE: proposed rename target for _ methods at exoskeleton level
                 intent: make the bb7/cc8 duality explicit in code
                 cc8 = sovereign system-level calls (autonomous layer)
                 bb7 = public MCP surface (client-facing layer)
                 NOT implemented yet — this is a naming convention proposal
```

**Pattern:** every `bb7_*` method is a public compilation endpoint. Some are thin transport wrappers, but the doctrine-level meaning is stable public surface over internal scoring, routing, memory lookup, state mutation, reflection, neural signal fusion, and output synthesis.

---

## BRANCH G: Client drift — diagnosing when deliberate routing is skipped

**Symptom:** a client makes direct `bb7_*` calls for substantial work without route/plan context or explicit reflect. The server still records events, ambient memory exchange, and auto-observation paths; what is missing is deliberate intent routing, plan-chain context, and high-quality `bb7_exo_reflect` reinforcement.

**No hard server rejection exists.** Direct calls are valid. For substantial work, clients should use route/plan/recall when useful and reflect after meaningful execution.

**How to diagnose:**

Step 1 — Check recent route/plan/recall usage when a task should have needed it:

```
grep -E "bb7_exo_(route|plan)|bb7_lisan_(intend|recall)" data/events.jsonl | tail -10
```

Step 2 — Check if reflect is being called after meaningful work:

```
grep "bb7_exo_reflect" data/exoskeleton/cross_ai_activity.jsonl | tail -10
```

Step 3 — Check if priors are updating:

```
mcp.venv/bin/python - <<'PY'
import json
from pathlib import Path
s=json.loads(Path('data/exoskeleton/exoskeleton_state.json').read_text())
priors=s.get('chain_priors',{})
print(f'{len(priors)} chain priors')
for k,v in list(priors.items())[:3]:
    print(k, 'success:', v.get('successes'))
PY
```

Step 4 — Check active plans:

```
cat data/exoskeleton/active_plans.json
```

If empty or stale timestamps while complex work is happening, the plan layer is being underused.

**Root causes of drift:**

- old mandatory-loop docs causing ceremony instead of intelligent routing;
- client treating BB7 as a flat utility list;
- stale transport bound to an old runtime;
- multiple process drift or split data roots.

---

## BRANCH H: In-process momentum scratchpad vs persistent session continuity

`ExoskeletonTool.session_state` is a per-process scratchpad initialized each process start. Persistent continuity lives in `/home/daeron/Somnus-MCP/data`: exoskeleton state, category transitions, session files, memory store, memory graph, and event streams.

```python
self.session_state = {
    "session_id": ...,
    "recent_tools": [],        # last N tool calls with category
    "recent_categories": [],   # category sequence
    "tool_sequence": [],       # full sequence for workflow detection
    "intent_history": [],
    "active_workflow": None,   # set by _detect_active_workflow()
}
```

`category_transitions` — persistent, at `data/exoskeleton/category_transitions.json`:

- Learned probability matrix: P(next_category | current_category)
- Updated by `_update_session_momentum()` on each reflect call
- Feeds `_compute_momentum_bonus()` to boost contextually appropriate tools

**Momentum bonus cap:** +0.25 max (line 1031+), broken down:

- Active workflow position match: up to +0.20
- Category adjacency: +0.12
- Same category continuation: +0.08
- Learned transition probability: up to +0.08
- Recency decay bonus: +0.05

---

## Quick Reference: Where is X?

| Question | Go to |
|---------|-------|
| Tool dispatch | `mcp_server.py:3116` |
| Autonomous exo cycle / Muad'Dib self-play cadence | `mcp_server.py:_autonomous_exo_cycle_loop` |
| Non-blocking telemetry/witness hook | `mcp_server.py:3304` |
| Distillation init (gated) | `mcp_server.py:481` |
| Exoskeleton class start | `exoskeleton_tool.py:46` |
| Lisan subsystem imports | `exoskeleton_tool.py:19` |
| Lisan subsystem init | `exoskeleton_tool.py:238` |
| bb7_exo_bootstrap | `exoskeleton_tool.py:1781` |
| bb7_lisan_intend | `exoskeleton_tool.py:3173` |
| bb7_exo_route | `exoskeleton_tool.py:1886` |
| bb7_exo_plan | `exoskeleton_tool.py:1915` |
| bb7_exo_reflect | `exoskeleton_tool.py:1980` |
| bb7_lisan_recall | `exoskeleton_tool.py:2948` |
| bb7_muadib_mentat_bridge | `tools/meta_intelligence_engine.py` read-only one-plane Mentat/Muad'Dib facade |
| bb7_tool_refresh_module | `mcp_server.py` guarded in-place refresh for allowlisted registry-bound facades |
| bb7_dt_self_play | `tools/exoskeleton_tool.py` wrapper over `muadib/muaddib.py` |
| bb7_dt_self_play_lock | `tools/exoskeleton_tool.py` wrapper over Muad'Dib self-play promotion metadata |
| bb7_dt_checkpoint_status | `tools/exoskeleton_tool.py` wrapper over Muad'Dib checkpoint metadata |
| Muad'Dib self-play head | `muadib/neural_config.py` → `MuadDibSelfPlayHead` |
| Muad'Dib self-play weights | `data/digital_twin/self_play/self_play_head_v*.safetensors` |
| Muad'Dib tokenizer weights | `data/digital_twin/checkpoint_v*.safetensors`; `.pt` is legacy load fallback |
| _score_tools | `exoskeleton_tool.py:1544` |
| _make_plans | `exoskeleton_tool.py:1673` |
| _apply_reflect_mutations | `exoskeleton_tool.py:1292` |
| _update_session_momentum | `exoskeleton_tool.py:936` |
| _detect_active_workflow | `exoskeleton_tool.py:1002` |
| _compute_momentum_bonus | `exoskeleton_tool.py:1031` |
| _match_golden_path | `exoskeleton_tool.py:871` |
| _reliability | `exoskeleton_tool.py:1425` |
| _promote_successful_chain | `exoskeleton_tool.py:712` |
| _auto_promote_to_golden_paths | `exoskeleton_tool.py:799` |
| _maybe_sync_live_tools | `exoskeleton_tool.py:603` |
| GoldenPathOracle | `lisan_al_gaib.py:1191` |
| match_golden_path | `lisan_al_gaib.py:1283` |
| _SpectralIntentDecomposer | `lisan_al_gaib.py:55` |
| spectral_similarity | `lisan_al_gaib.py:117` |
| entropy_gate | `lisan_al_gaib.py:160` |
| Golden paths file | `golden_paths.json` (repo root) |
| Auto-discovered workflows | `data/exoskeleton/auto_discovered_workflows.json` |
| Category transitions | `data/exoskeleton/category_transitions.json` |
| Exoskeleton state + priors | `data/exoskeleton/exoskeleton_state.json` |
| Cross-AI activity log | `data/exoskeleton/cross_ai_activity.jsonl` |
| Active plans | `data/exoskeleton/active_plans.json` |
| Distillation trajectories | `data/distillation/trajectories_*.jsonl` |
| Events log | `data/events.jsonl` |
