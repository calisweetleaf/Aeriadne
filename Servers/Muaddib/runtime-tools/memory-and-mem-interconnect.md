### Memory Continuity Substrate (`memory_tool.py`)

> **Doctrine.** The `memory_tool` is **not an ordinary utility rack** — it is the
> continuity substrate that lets clients recover context across turns and
> sessions. It is structured as a three-tier memory hierarchy:
> 1. **Working memory** — LRU in-RAM buffer (capacity 50, instant access, O(1) ops).
> 2. **Long-term store** — JSON file on disk (`data/memory_store.json`, atomic write).
> 3. **Archives** — JSON files in `data/archives/` (old low-importance entries).
>
> Every entry carries **Ebbinghaus forgetting-curve decay metadata**
> (`stability`, `last_accessed`, `access_count`) and a `content_hash` provenance
> trail. Stability grows logarithmically with each reinforced access
> (capped at 60 days), so frequently-referenced memories decay slowly while
> one-off observations fade.
>
> **Pairing.** This module is the **store and lifecycle owner**. The
> `memory_interconnect` module is the **index and search owner**. They share
> a unified consolidation policy (`memory_unified_archive_v1`,
> `ARCHIVE_IMPORTANCE_THRESHOLD = 0.7`, `ARCHIVE_ACCESS_COUNT_THRESHOLD = 5`).
> Core surfaces (`store`, `retrieve`, `delete`, `list`, `stats`, `insights`,
> `consolidate`, `categories`) live here; index surfaces
> (`analyze_entry`, `intelligent_search`, `concept_network`, `cluster`,
> `find_gaps`, `graph`, `consolidate_index`) live in `memory_interconnect.py`.
> The store-to-index call always passes `explicit_ids` to keep the BM25 graph
> policy-identical to the active memory store.

| Subsystem / Class | Role |
|---|---|
| `EnhancedMemoryTool` | Public façade. Owns the `_lock`, the `WorkingMemoryBuffer`, the `_Engine` reference, and the `get_tools()` registry. |
| `WorkingMemoryBuffer` | LRU `OrderedDict` cache (capacity 50). Touch/refresh on every store/retrieve. Invalidated on delete. |
| `_archive_decision()` | Shared retention policy — used by both `consolidate_memories` and the soft-degrade stub. |
| `_decay_score()` / `_reinforce_stability()` | Ebbinghaus math: `R = e^(-elapsed_days / stability)`. |
| `_content_hash()` | Stable SHA-256 for payload provenance. |
| `_load_data()` / `_save_data()` | Atomic JSON read/write with 8-attempt retry on Windows file locks (winerror 5/32). |
| `_normalize_tool_registry()` | Wraps every `bb7_*` tool to tolerate kwargs, dict-style, and positional invocation shapes. |
| `_Engine` (degraded stub) | Explicit no-op engine used when `tools.memory_interconnect` cannot import. Reports `degraded=True` via `health()`. |

**Storage paths:** `data/memory_store.json` (default), configurable via
constructor `storage_file` parameter or `SOVEREIGN_DATA_DIR` env var.
`CATEGORIES = {insights, decisions, patterns, context, solutions, references, goals, technical}`.

**Soft-degrade contract:** If `tools.memory_interconnect` fails to import,
`EnhancedMemoryTool.__init__` constructs an explicit degraded `_Engine` stub
that returns empty concepts, importance=0.5, no related memories, and a
`degraded=True` flag on every result. Core `store`/`retrieve`/`delete`/`list`
operations remain available; only BM25-enriched surfaces report degraded
status through `bb7_memory_stats`.

---

#### `bb7_memory_store`

Store a key-value memory with category, importance (0-1), tags, and automatic
BM25 indexing + Ebbinghaus decay initialisation. Every entry receives a
`schema_version`, stable `memory_id` (`memory:{key}`), `content_hash`,
`lifecycle_state`, and full provenance metadata.
**Internal Composition**: Calls `EnhancedMemoryTool.store()` which writes
the entry to the JSON store, touches the LRU buffer, and asks the
interconnect engine for concept extraction / related-memory mapping.
AI-importance scoring is automatically boosted when ≥3 related memories
already exist for the new key.

- **Parameters**:
  - `key` (string, required): The unique key to store the value under.
  - `value` (string, required): The value to store.
  - `category` (string, optional): One of `insights`, `decisions`, `patterns`, `context`, `solutions`, `references`, `goals`, `technical`, or `uncategorized` (default: `uncategorized`).
  - `importance` (number, optional): Importance score 0.0–1.0 (clamped, default: 0.5).
  - `tags` (array of strings, optional): Free-form classification tags.

#### `bb7_memory_retrieve`

Retrieve a memory by key. Updates Ebbinghaus stability (reinforces retention
on each read) and touches the LRU working buffer. On miss, falls back to
BM25-suggested similar keys.
**Internal Composition**: Calls `EnhancedMemoryTool.retrieve()`. If `include_related=true`,
the response is enriched with category, importance, tags, concepts, related
memory keys, and the live decay retention percentage.

- **Parameters**:
  - `key` (string, required): The memory key to retrieve.
  - `include_related` (boolean, optional): Include metadata, concepts, and related keys (default: false).

#### `bb7_memory_delete`

Delete a memory entry by key. Invalidates the LRU working buffer entry
and persists the deletion atomically.
**Internal Composition**: Calls `EnhancedMemoryTool.delete()`. Returns an
error string if the key is unknown.

- **Parameters**:
  - `key` (string, required): The key to delete.

#### `bb7_memory_list`

List memory keys with filtering (prefix, category, min_importance) and
sorting (timestamp, importance, access, alphabetical, decay). Each row
is decorated with category badge, importance asterisk, access count,
and live retention percentage.
**Internal Composition**: Calls `EnhancedMemoryTool.list_keys()`.

- **Parameters**:
  - `prefix` (string, optional): Filter keys by prefix.
  - `category` (string, optional): Filter keys by exact category.
  - `min_importance` (number, optional): Minimum importance score filter (default: 0.0).
  - `sort_by` (string, optional): Sort by `timestamp`, `importance`, `access`, `alphabetical`, or `decay` (default: `timestamp`).

#### `bb7_memory_search`

BM25-powered semantic search with Ebbinghaus decay reranking. Fetches
`max_results × 2` candidates from the BM25 index, then re-scores with
`final = bm25 × (0.7 + 0.3 × decay)` so recent memories surface
preferentially.
**Internal Composition**: Calls `EnhancedMemoryTool.intelligent_search()`.
Falls back to substring search via `_simple_search()` when BM25 is unavailable.

- **Parameters**:
  - `query` (string, required): The search query.
  - `max_results` (number, optional): Maximum results to return (default: 5).

#### `bb7_memory_surface_context`

Proactively surface the most relevant memories for a given context blob
using BM25 + Ebbinghaus decay weighting. The "ambient intelligence"
surface — call it at the start of a session to recover relevant prior
knowledge without knowing the keys.
**Internal Composition**: Calls `EnhancedMemoryTool.surface_context()`,
which uses the BM25 engine to fetch `max_results × 3` candidates and
returns the top `max_results` decay-weighted entries with category,
importance, retention %, and concept badges.

- **Parameters**:
  - `context_text` (string, required): Current context or task description to match against.
  - `max_results` (number, optional): Max memories to surface, clamped 1–20 (default: 5).

#### `bb7_memory_bulk_store`

Atomically store multiple memory entries in a single disk write. Validates
every entry's key, value, category, and importance before writing — no
partial writes.
**Internal Composition**: Calls `EnhancedMemoryTool.bulk_store()`. Accepts
a JSON array of `{key, value, category, importance, tags}` objects.

- **Parameters**:
  - `entries_json` (string, required): JSON array of `{key, value, category, importance, tags}` objects.

#### `bb7_memory_get_related`

Fetch semantically related memories for a given key using BM25. Refreshes
the related-memories cache if older than 1 hour.
**Internal Composition**: Calls `EnhancedMemoryTool.get_related()`.

- **Parameters**:
  - `key` (string, required): Memory key to find relations for.
  - `max_results` (number, optional): Max related memories to return, clamped 1–20 (default: 5).

#### `bb7_memory_timeline`

Chronological view of memories created or updated in the last N days.
Each row shows date, key, category, importance, retention %, version,
and tags.
**Internal Composition**: Calls `EnhancedMemoryTool.memory_timeline()`.

- **Parameters**:
  - `days` (number, optional): Look-back window in days, clamped 1–365 (default: 7).
  - `limit` (number, optional): Max entries to show, clamped 1–200 (default: 20).

#### `bb7_memory_export`

Export all memories as a structured Markdown document (grouped by category,
sorted by importance within each group) or as a raw JSON dump.
**Internal Composition**: Calls `EnhancedMemoryTool.export_memories()`.

- **Parameters**:
  - `format` (string, optional): Export format — `markdown` or `json` (default: `markdown`).

#### `bb7_memory_stats`

Comprehensive memory statistics — total entries, storage size, content
volume, schema version, consolidation policy, interconnect availability,
importance distribution, access patterns, working-memory hot set, weekly
activity, and BM25 index health (when interconnect is available).
**Internal Composition**: Calls `EnhancedMemoryTool.get_stats()`, which
folds in `MemoryInterconnectionEngine.index_stats()` when the engine is
non-degraded.

- **Parameters**: None.

#### `bb7_memory_insights`

Narrative insights combining local stats (`EnhancedMemoryTool.get_stats()`)
and BM25 network analysis (top memories, top concepts, network density).
**Internal Composition**: Calls `EnhancedMemoryTool.get_memory_insights()`.

- **Parameters**: None.

#### `bb7_memory_consolidate`

Archive old low-importance low-access entries under the shared production
policy `memory_unified_archive_v1`. Memories with `importance ≥ 0.7` or
`access_count ≥ 5` are always retained. Writes an archive payload with
reasons and provenance, then prunes the BM25/interconnect index by
passing the explicit archived memory IDs to `bb7_memory_consolidate_index`.
**Internal Composition**: Calls `EnhancedMemoryTool.consolidate_memories()`,
which uses the shared `_archive_decision()` retention policy. The matched
memory IDs are then forwarded to `MemoryInterconnectionEngine.consolidate_memories()`
to keep the active store and the BM25 graph policy-identical.

- **Parameters**:
  - `days_old` (number, optional): Age threshold in days (default: 30).

#### `bb7_memory_categories`

List the available memory categories with their descriptions. Static
metadata — returns from the `CATEGORIES` class constant.
**Internal Composition**: Maps to `EnhancedMemoryTool.CATEGORIES`.

- **Parameters**: None.

---

### Memory Interconnect Substrate (`memory_interconnect.py`)

> **Doctrine.** `memory_interconnect` owns the **index and search** surfaces
> only — the BM25 inverted index, concept map, importance-score ledger,
> memory-link graph, and Graphviz DOT export. Core store/list/delete
> surfaces stay in `memory_tool.py`. The two modules share a single
> consolidation policy (`memory_unified_archive_v1`) so the active memory
> store and the BM25 graph can never drift on retention decisions.
>
> **Pairing.** Downstream of `memory_tool` (every `analyze_memory_entry`
> call is triggered by `EnhancedMemoryTool.store()` and `bulk_store()`).
> Upstream of `bb7_memory_consolidate` (which forwards explicit IDs here).
> `session_manager_tool` consumes `get_memory_graph()` for visual session
> debugging; `enhanced_code_analysis_tool` uses `extract_concepts()` for
> identifier extraction in source code.

| Subsystem / Class | Role |
|---|---|
| `MemoryInterconnectionEngine` | Public façade. Owns `_lock`, the BM25 cache, and the persisted JSON indices. |
| `_tokenize()` | Lowercase → non-alphanumeric split (preserve underscores) → stopword filter → Porter-lite stemmer → min-length 3. |
| `_stem()` | Suffix-removal stemmer with 30+ rules and 4-char minimum root. |
| `_update_doc_stats()` | BM25 doc-frequency + per-doc TF bookkeeping under lock. |
| `_compute_idf()` / `_get_idf()` | Robertson-Spärck Jones IDF formula, cached until `idf_dirty`. |
| `_bm25_score()` | Okapi BM25 with `k1=1.5, b=0.75` (standard defaults). |
| `analyze_memory_entry()` | Indexes a memory, extracts concepts, computes importance, finds related. |
| `intelligent_search()` | BM25-ranked retrieval across all indexed memories. |
| `get_concept_network()` | Concept → co-occurring concept map. |
| `cluster_memories()` | Greedy BM25 clustering (similarity > 0.25 against centroid). |
| `find_knowledge_gaps()` | Concept frequency minus dedicated-entry coverage. |
| `get_memory_graph()` | Graphviz DOT export with importance-coloured nodes. |
| `consolidate_memories()` | Archive eligible entries, prune all indices (links, concepts, BM25 df, importance scores). |
| `index_stats()` / `force_rebuild()` | Drift detection (orphan doc_terms, missing doc_terms, stale idf) and full repair path. |

**Storage paths:** `data/memory_relationships.json`, `data/concept_index.json`,
`data/importance_scores.json`, and `data/memory_index_archive_<ts>.json`
for archived batches. All writes are atomic with 8-attempt Windows-retry.

**Soft-degrade contract:** `memory_tool.py` defines an explicit degraded
`_Engine` stub (no raise) when this module fails to import. Core
`store`/`retrieve`/`delete`/`list` operations remain available; BM25-enriched
surfaces report `degraded=True` via `bb7_memory_stats`.

> **Audit history (resolved 2026-06).** Earlier AGENTS notes flagged three
> memory-subsystem defects; all three are now fixed in source:
> 1. `consolidate_memories` `NameError` — variable renamed to `to_archive_set`
>    (line 1330), no longer references the undefined `to_archive`.
> 2. Consolidation-policy divergence — both modules now share
>    `ARCHIVE_IMPORTANCE_THRESHOLD = 0.7` and
>    `ARCHIVE_ACCESS_COUNT_THRESHOLD = 5` under policy version
>    `memory_unified_archive_v1`.
> 3. `INTERCONNECT_IMPORT_ERROR` hard-fail — replaced with the explicit
>    degraded `_Engine` stub (lines 50–132 of `memory_tool.py`) that returns
>    safe no-ops and reports `degraded=True` on every call.

---

#### `bb7_memory_analyze_entry`

Index a memory entry using BM25, extract concepts, and map relationships
to existing memories. The primary ingestion surface — every store
operation in `memory_tool` calls this under the hood.
**Internal Composition**: Calls `MemoryInterconnectionEngine.analyze_memory_entry()`,
which tokenises the value+key, updates per-doc TF and global doc-frequency,
records importance, and finds BM25-ranked related memories. All updates
are persisted atomically.

- **Parameters**:
  - `key` (string, required): The memory key.
  - `value` (string, required): The memory content to index.
  - `source` (string, optional): Source namespace (default: `memory`).

#### `bb7_memory_intelligent_search`

BM25-ranked semantic search across all indexed memories, formatted as
human-readable Markdown. Distinct from `memory_tool.bb7_memory_search`,
which performs the **same BM25 query** but then re-ranks with
`final = bm25 × (0.7 + 0.3 × decay)` — use this one for pure relevance
ranking, use the other for decay-weighted ambient surfacing.
**Internal Composition**: Calls `MemoryInterconnectionEngine.intelligent_search()`
and formats results via `_format_search_results()`.

- **Parameters**:
  - `query` (string, required): The search query.
  - `max_results` (number, optional): Maximum results to return (default: 10).

#### `bb7_memory_get_insights`

Formatted insights report about the memory network — total memories,
unique concepts, total relationships, average connections/memory,
network density, BM25 index docs, average document length, top 5
memories by importance, top 10 concepts by coverage.
**Internal Composition**: Calls `MemoryInterconnectionEngine.get_memory_insights()`.

- **Parameters**: None.

#### `bb7_memory_concept_network`

Get the network of memories and co-occurring concepts connected to a
specific term. Returns the memory IDs that reference the concept and
the top-10 most-frequent co-occurring concepts.
**Internal Composition**: Calls `MemoryInterconnectionEngine.get_concept_network()`,
which first tries an exact concept match, then falls back to a Porter-stemmed
match before returning the reference list and co-occurrence counts.

- **Parameters**:
  - `concept` (string, required): The concept to analyse.

#### `bb7_memory_extract_concepts`

Extract key BM25 tokens and concepts from arbitrary text. Returns a
comma-separated list, capped at 30 tokens. Surfaces technical camelCase
and `UPPER_CASE` identifiers verbatim in addition to the stemmed tokens.
**Internal Composition**: Calls `MemoryInterconnectionEngine.extract_concepts()`
using the local tokeniser + heuristic NLP extraction.

- **Parameters**:
  - `text` (string, required): The text to analyse.

#### `bb7_memory_cluster`

Group indexed memories into BM25 semantic clusters using a greedy
centroid-selection algorithm. Each cluster shows up to 5 member keys
plus key concepts; remaining members are summarised.
**Internal Composition**: Calls `MemoryInterconnectionEngine.cluster_memories()`.

- **Parameters**:
  - `n_clusters` (number, optional): Target number of clusters (default: 5).

#### `bb7_memory_find_gaps`

Find concepts referenced in `min_frequency+` memories that lack a
dedicated memory entry. Each gap reports the concept, total frequency,
and up to 3 example memory keys.
**Internal Composition**: Calls `MemoryInterconnectionEngine.find_knowledge_gaps()`.

- **Parameters**:
  - `min_frequency` (number, optional): Minimum reference count to flag as a gap (default: 3).

#### `bb7_memory_graph`

Export the memory relationship graph in Graphviz DOT format. Nodes are
coloured by importance (red ≥ 0.7, yellow 0.4–0.7, green < 0.4); edges
are drawn only when similarity ≥ `min_similarity`.
**Internal Composition**: Calls `MemoryInterconnectionEngine.get_memory_graph()`.

- **Parameters**:
  - `min_similarity` (number, optional): Minimum BM25 similarity to draw an edge (default: 0.3).

#### `bb7_memory_consolidate_index`

Archive eligible interconnect/index entries and prune every relationship,
concept, BM25, and importance-score reference using the shared production
policy `memory_unified_archive_v1`. The store-level
`bb7_memory_consolidate` calls this with the explicit archived memory IDs
so the active memory store and the BM25 graph remain policy-identical.
**Internal Composition**: Calls `MemoryInterconnectionEngine.consolidate_memories()`,
which writes `data/memory_index_archive_<ts>.json`, removes the
relationship-graph nodes, prunes related-memory references and
`concept_index["concepts"]`, decrements BM25 document-frequency counters,
and clears `importance_scores`. Returns post-run `index_stats()`.

- **Parameters**:
  - `age_threshold_days` (number, optional): Age threshold in days for archival, clamped ≥ 1 (default: 30).
  - `explicit_ids` (array of strings, optional): Specific memory IDs such as `memory:some_key` to archive (skips the importance/access policy).
