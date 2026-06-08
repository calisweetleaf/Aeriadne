### Muad'Dib Neural Substrate (`muadib/`)

> **Doctrine.** The `muadib/` package is the **neural substrate** —
> the 512-dimensional embedding manifold M that all tool scores flow through.
> It connects the symbolic rule-reasoning layer (`exoskeleton` / `lisan`) to
> a learned, continuous representation of tool semantics. Every `bb7_dt_*`
> tool here is a read-only or training-side surface — they observe, score,
> encode, persist, and inspect the digital twin. They never mutate the
> server lifecycle, output adapters, or the symbolic state of the
> exoskeleton.
>
> **Pairing.** Upstream of `exoskeleton` (which calls `bb7_dt_q_scores`
> for the Thompson-bandit bonus and `bb7_dt_observe` after every tool
> execution). Downstream of `data/digital_twin/` (the JSON + safetensors
> persistence layer). The advanced-bridge surface
> (`bb7_dt_advanced_features`) crosses into the modality-bridge layer
> (`muadib/advanced_bridge.py`); when `MUADIB_ADVANCED_MODE=0` the call
> returns `{"ok": false, "reason": "bridge_disabled"}` and never raises.

The `muadib/` package provides a 512-dimensional embedding manifold M that all tool scores flow through. It connects the symbolic rule-reasoning layer (exoskeleton / lisan) to a learned, continuous representation of tool semantics.

#### `muadib/muaddib.py` — `DigitalTwinTool`

The Digital Twin's primary tool class. Hosts `bb7_dt_encode_catalog`, the catalog-scale encoding API added 2026-04-24.

**`bb7_dt_encode_catalog(tool_names: List[str], tool_categories: Optional[Dict[str, str]]) -> Dict`**

Encodes a list of tool names into 512-dim embeddings. Handles chunked encoding transparently: catalogs larger than `max_seq_len=64` are split across multiple forward passes and merged. Return schema:

```json
{
  "ok": true,
  "embeddings": { "<tool_name>": [<float>, ...] },
  "d_model": 512,
  "encoded_count": <int>,
  "chunks": <int>
}
```

Contrast with the lower-level `bb7_dt_encode`, which accepts `List[Dict]` and does not handle chunking. `bb7_dt_encode_catalog` is the correct API for exoskeleton catalog operations.

#### `muadib/neural_config.py`

Provides `NeuralNetConfig`, `SubstrateConfig`, and `NeuralSubstrateTokenizer` — the configuration layer for the digital twin's neural backbone.

As of 2026-06-04 it also provides the bounded self-play neural primitive:

- `SelfPlayConfig` — compact policy/value-head configuration for continuous Muad'Dib self-play.
- `MuadDibSelfPlayHead` — isolated policy/value module trained on candidate self-play trajectories over tool IDs.

Checkpoint doctrine:

- JSON is metadata/ledger/pointer state only. It is not neural weight storage.
- Actual tensor weights are `.safetensors` when the `safetensors` package is available.
- Existing `checkpoint_vN.pt` tokenizer files are load-only migration fallback. New tokenizer saves prefer `checkpoint_vN.safetensors`.
- Self-play trains a candidate copy, writes `data/digital_twin/self_play/self_play_head_vN.safetensors` atomically, and archives by default. Promotion to active/champion is explicit opt-in after the checkpoint is complete.
- Safetensors locks the serialization/integrity boundary, not semantic immutability. Continuous self-play can keep producing candidate weights; active/champion weights are pinned only when promotion is disabled or the active promotion lock is set.
- Synthetic self-play does not update the real DigitalTwin Q-table by default; callers must set `update_qtable=true` explicitly for synthetic-data experiments.
- The existing `mcp_server.py` autonomous exo cycle invokes bounded self-play through `exo.bb7_dt_self_play(...)`. This is lifecycle training only; it does not modify the JSON-RPC result adapter or display/content-block formatting boundary.
- Autonomous cadence defaults: `MUADIB_SELF_PLAY_ENABLED=1`, `MUADIB_SELF_PLAY_INTERVAL_CYCLES=32`, `MUADIB_SELF_PLAY_EPISODES=4`, `MUADIB_SELF_PLAY_MAX_STEPS=3`, `MUADIB_SELF_PLAY_PROMOTE=0`, `MUADIB_SELF_PLAY_LOCK_ACTIVE=0`, `MUADIB_SELF_PLAY_UPDATE_QTABLE=0`. Continuous self-play therefore archives candidate safetensors by default; active/champion weights advance only when promotion is explicitly enabled and the promotion lock is not set.
- Isolated validation command: `mcp.venv/bin/python scripts/validate_muadib_self_play_weights.py --json`. This uses `DigitalTwinTool(data_dir=temp)` only, writes temporary `.safetensors` candidates, verifies archive-only and locked-promotion semantics, cleans the temp data dir, and does not instantiate `MCPServer` or mutate the canonical data plane.
- Display projection validator: `mcp.venv/bin/python scripts/validate_display_projection.py --json`. This performs static source-order checks and `object.__new__(MCPServer)` formatter smoke tests only. It proves raw telemetry/memory/Q/RFT paths occur before projection, verifies the raw JSON escape hatch, and writes `docs/validation/2026-06-04-display-projection.md/json`.
- Full source/live validation suite: `mcp.venv/bin/python scripts/run_muadib_one_plane_validation.py --json`. Add `--live-health-json <path> --require-live` after the MCP client/gateway reloads to turn the same suite into the strict completion gate. The runner composes existing validators, refreshes the generated completion audit through `scripts/write_muadib_completion_audit.py`, and never instantiates `MCPServer`, restarts/signals live processes, or mutates output adapters.
- Completion audit generator: `mcp.venv/bin/python scripts/write_muadib_completion_audit.py --json`. It reads validation JSON artifacts, writes `docs/validation/2026-06-04-muadib-completion-audit.md/json`, and can move from `pending_live_reload` to complete only when the supplied suite artifact has `completion_ready=true` and `live_status=PASS`.

#### `bb7_dt_self_play`

Run bounded Muad'Dib self-play through the exoskeleton's live DigitalTwin instance.

**Internal Composition**: Uses the live exoskeleton tool catalog, trains a candidate `MuadDibSelfPlayHead`, writes safetensors weights, updates self-play metadata, and optionally promotes the complete candidate as the active self-play head.

- **Parameters**:
  - `episodes` (integer, optional): bounded self-play episode count (default `32`, max `512`).
  - `max_steps` (integer, optional): tools per simulated episode (default `4`, bounded by self-play config).
  - `learning_rate` (number, optional): AdamW learning-rate override.
  - `promote` (boolean, optional): request promotion of the fully written candidate checkpoint (default `false` / archive-only). Ignored when the active promotion lock is set.
  - `update_qtable` (boolean, optional): also record synthetic observations into the real Q-table (default `false`).
  - `session_id` (string, optional): session identifier for optional synthetic observations.

#### `bb7_dt_self_play_lock`

Lock or unlock active/champion self-play promotion without stopping candidate training.

**Internal Composition**: Mutates only `data/digital_twin/self_play/checkpoint_meta.json` promotion-lock metadata. Continuous cadence may still write candidate `.safetensors` checkpoints, but locked active checkpoints are protected from pruning and cannot be swapped into the live in-memory head until unlocked or overridden by `MUADIB_SELF_PLAY_LOCK_ACTIVE`.

- **Parameters**:
  - `locked` (boolean, optional): `true` to pin active/champion weights; `false` to allow promotion again.
  - `reason` (string, optional): operator-readable reason persisted into checkpoint metadata.
  - `operator` (string, optional): actor/source label for the lock mutation.

#### `bb7_dt_checkpoint_status`

Inspect tokenizer/self-play checkpoint state without loading or mutating weights.

Returns safetensors availability, active tokenizer checkpoint metadata, legacy `.pt` migration files, active self-play checkpoint metadata, promotion-lock state, and self-play safetensors file list.

#### `bb7_dt_observe`

Record one tool-call observation. Called by the server (via the daemon
thread in ambient-memory-exchange) after every `bb7_` execution. Touches
the tool-vocab and category-vocab, runs a TD-update through the backbone,
and returns the update details. **Never blocks execution.**
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_observe()`. Touches
`self._tool_id()` and `self._category_id()` to keep the tokenizer in sync,
then calls `self.backbone.observe(session_id, ...)`.

- **Parameters**:
  - `tool_name` (string, required): The bb7_ tool name that was called.
  - `category` (string, optional): Tool category for Q-bonus lookups (default: `"misc"`).
  - `success` (boolean, optional): Whether the call succeeded (default: true).
  - `latency_ms` (number, optional): Observed latency in milliseconds (default: 0.0).
  - `chain_length` (integer, optional): Number of tools in the chain so far (default: 1).
  - `session_id` (string, optional): Session identifier (default: `"default"`).
  - `error` (string, optional): Error string when `success=false`.

#### `bb7_dt_q_scores`

Return normalized Q-bonuses for the candidate tool set at the current
session state. Drop-in for the exoskeleton `_score_tools` formula
when wiring is done.
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_q_scores()`. Calls
`self.backbone.q_bonus(session_id, category, candidates, max_bonus)`
and returns the per-tool scores.

- **Parameters**:
  - `candidates` (array of strings, required): Tool names to score.
  - `category` (string, optional): Tool category for Q-bonus lookups (default: `"misc"`).
  - `session_id` (string, optional): Session identifier (default: `"default"`).
  - `max_bonus` (number, optional): Max Q-bonus per tool, clamped 0.0–1.0 (default: 0.25).

#### `bb7_dt_encode`

Project a symbolic tool sequence into the shared d_model manifold.
Phase 1 surface — the tokenizer is randomly initialised, shapes are
correct, projections are not yet semantically meaningful. Downstream
modality heads can be plugged in today against the shape contract.
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_encode()`. Returns
`{"shape": [1, seq, d_model], "hidden_states": nested list}` when torch
is available, or `{"ok": false, "error": "..."}` otherwise. Does not
chunk — for catalogs larger than `max_seq_len=64` use `bb7_dt_encode_catalog`.

- **Parameters**:
  - `tool_sequence` (array of objects, required): List of `{tool_name, category, param_hash}` dicts to encode.

#### `bb7_dt_encode_catalog`

Encode a flat list of tool names into per-tool d_model embedding vectors.
The correct API for batch catalog encoding — callers pass `List[str]`
and receive a dict of `{tool_name: [float, ...] (d_model)}`. Wraps
`bb7_dt_encode()` and handles chunking transparently when the catalog
exceeds `max_seq_len=64`. Each chunk is encoded independently and
the per-tool vectors are assembled into a single flat embeddings dict.
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_encode_catalog()`.
Splits the input into `max_seq_len`-bounded chunks, runs `bb7_dt_encode`
per chunk, merges the per-tool vectors.

- **Parameters**:
  - `tool_names` (array of strings, required): Tool names to encode, in order.
  - `tool_categories` (object, optional): Map of `{tool_name: category_str}`. Defaults to `"misc"` for unknown tools.

#### `bb7_dt_status`

Health / inspection snapshot of the digital twin. **Read-only** — no
mutations, safe to call from any control-plane path.
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_status()`. Composes
`self.backbone.status()` + `_advanced_bridge.health` + vocab counters +
checkpoint metadata.

- **Parameters**: None.

#### `bb7_dt_advanced_features`

Query advanced modality features for candidate tools via the bridge.
Returns per-tool provenance-tagged scores when `MUADIB_ADVANCED_MODE=1`.
Always safe to call — returns `{"ok": false, "reason": "bridge_disabled"}`
when the mode is off, **never raises**.
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_advanced_features()`.
Delegates to `self._advanced_bridge` (the `AdvancedModalityBridge` in
`muadib/advanced_bridge.py`) for provenance-tagged signal extraction
across `trained_q`, `trained_cooccur`, and `untrained_embed` channels.

- **Parameters**:
  - `candidates` (array of strings, required): Tool names to score.
  - `category` (string, optional): Tool category for context (default: `"misc"`).
  - `session_id` (string, optional): Session identifier (default: `"default"`).
  - `recent_tools` (array of strings, optional): Optional recent-tool list for context-aware scoring.

#### `bb7_dt_save`

Manual persistence. Autosave fires every 50 observations anyway; this
is the explicit operator-triggered save path.
**Internal Composition**: Calls `DigitalTwinTool.bb7_dt_save()`. Runs
`self.backbone.save()` + `self._save_vocab()` + `self._save_neural_checkpoint()`
in sequence. Returns `{"ok": true, "saved_at": <ts>}` on success.

- **Parameters**: None.
