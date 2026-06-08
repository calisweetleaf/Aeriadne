### Thought Journal Tools (`thought_journal_tool.py`)

> **Doctrine.** The Thought Journal is the **reasoning provenance** layer — it
> captures *why* a decision was made, not just *what* was decided. It exists to
> defeat the "AI amnesia" problem: every new session starts cold, and this
> substrate lets future agents inherit the *chain of reasoning* from prior work.
> External journal-first operation is **deprecated** in favour of `lisan` and
> `memory_tool` / `session_manager_tool` for primary continuity. The Thought
> Journal remains the canonical place for **structured rationale** — alternatives
> considered, risk assessments, success criteria, decision-outcome pairs.
>
> **Pairing.** Sits alongside `memory_tool` (free-form insights) and
> `session_manager_tool` (chronological session telemetry). Use `memory_tool`
> for key-value observations; use this journal for **decision-shaped** entries
> that need to be queried by topic, traced forward to outcomes, or audited.
> `memory_tool.get_related()` and the journal's `get_linked_entries()` are
> intentionally bidirectional — store cross-links via `linked_memories` and
> `linked_files` on every entry.

| Subsystem / Class | Role |
|---|---|
| `ThoughtJournalTool` | Public façade. Owns the `get_tools()` registry and the in-process write lock. |
| `ThoughtEntry` | Lightweight record: type, content, confidence, tags, cross-links. |
| `DecisionEntry` | Heavier record: rationale, alternatives, constraints, risk, success criteria, outcome, validation. |
| `_BM25Index` | Self-contained Okapi BM25 (k1=1.5, b=0.75) inverted index. No circular dependency on `memory_interconnect`. |
| `_entry_id()` | 8-char hex deterministic ID derived from timestamp + content hash. |

**Storage:** `data/thought_journal.json` (entry store) and
`data/journal_index.json` (BM25 inverted index, rebuilt lazily on write).

---

#### `bb7_journal_record_thought`

Record a thought, insight, or observation to the journal. Indexes the entry
in the BM25 inverted index for `search` / `surface_relevant` calls.
**Internal Composition**: Maps to `ThoughtJournalTool.record_thought()`. Validates
`type ∈ {thought, insight, hypothesis, observation, question}`, generates the
8-char hex entry ID, appends to `data/thought_journal.json`, updates BM25
inverted index.

- **Parameters**:
  - `content` (string, required): The thought or reasoning content.
  - `type` (string, optional): One of `thought`, `insight`, `hypothesis`, `observation`, `question` (default: `thought`).
  - `context` (string, optional): Situational context that prompted this thought.
  - `confidence` (number, optional): Confidence level 0.0–1.0 (default: 0.7).
  - `tags` (array of strings, optional): Optional classification tags.
  - `linked_memories` (array of strings, optional): Keys from `memory_tool` to link.
  - `linked_files` (array of strings, optional): File paths relevant to this thought.

#### `bb7_journal_capture_decision`

Record a decision with alternatives considered and rationale. The decision
becomes the root of a `decision_trail`; later `add_outcome` calls attach
validated or invalidated results to this entry.
**Internal Composition**: Maps to `ThoughtJournalTool.capture_decision()`. Validates
the decision type, persists with full provenance metadata, indexes the
rationale and alternatives into BM25.

- **Parameters**:
  - `decision` (string, required): What was decided.
  - `rationale` (string, required): Why this decision was made.
  - `alternatives` (string or array, optional): Alternatives considered.
  - `constraints` (string or array, optional): Constraints that shaped this decision.
  - `risk_assessment` (string, optional): What could go wrong with this decision.
  - `success_criteria` (string, optional): How to know if this decision was correct.
  - `linked_memories` (array of strings, optional): Memory keys relevant to this decision.
  - `linked_files` (array of strings, optional): File paths relevant to this decision.

#### `bb7_journal_add_outcome`

Add a result/outcome to a previously recorded decision or thought. The
`validated` flag is the audit-trail keystone: `true` (confirmed correct),
`false` (proven wrong), `None` (still unverified).
**Internal Composition**: Maps to `ThoughtJournalTool.add_outcome()`. Loads the
entry by 8-char hex ID, appends the outcome to its `outcomes[]` list, and
updates the BM25 index so the outcome is searchable.

- **Parameters**:
  - `entry_id` (string, required): Journal entry ID (8-char hex).
  - `outcome` (string, required): Description of what actually happened.
  - `validated` (boolean, optional): True if confirmed correct, False if wrong, None if unknown.

#### `bb7_journal_search`

Search journal entries by content, tags, or decision rationale using the
self-contained BM25 index.
**Internal Composition**: Maps to `ThoughtJournalTool.search_journal()`. Tokenises
the query through the local stopword set + Porter-lite stemmer, scores
every entry against the BM25 inverted index, sorts by relevance.

- **Parameters**:
  - `query` (string, required): BM25 full-text search query.
  - `max_results` (integer, optional): Maximum results to return (default: 5).
  - `entry_type` (string, optional): Filter by type (e.g. `thought`, `decision`, etc.).

#### `bb7_journal_get_decision_trail`

Get a chronological trail of decisions to understand how a project evolved.
Walks the journal looking for `decision`-type entries and any
subsequently-attached outcomes, returning them in time order.
**Internal Composition**: Maps to `ThoughtJournalTool.get_decision_trail()`.

- **Parameters**:
  - `topic` (string, required): Topic or keyword to trace decisions for.
  - `days` (integer, optional): Look-back window in days (default: 90).

#### `bb7_journal_surface_relevant`

Find journal entries relevant to the current context using semantic search.
The "ambient intelligence" surface — call it at the start of a turn when
you need to inherit prior reasoning without knowing the entry IDs.
**Internal Composition**: Maps to `ThoughtJournalTool.surface_relevant_entries()`.
Performs a BM25 query and returns the top-N entries ranked by relevance.

- **Parameters**:
  - `context_text` (string, required): Context query.
  - `max_results` (integer, optional): Maximum results to return (default: 5).

#### `bb7_journal_detect_conflicts`

Analyze recent entries to find potential contradictions or conflicts. Useful
for catching reasoning drift across long sessions.
**Internal Composition**: Maps to `ThoughtJournalTool.detect_conflicts()`. Walks
recent decisions, looks for opposing `validated` flags on related topics,
emits a conflict report.

- **Parameters**:
  - `topic` (string, optional): Focus conflict detection on a specific topic.

#### `bb7_journal_generate_retrospective`

Generate a retrospective summary for a given time period or topic. Pulls
all journal entries in the window, groups by decision clusters, and emits
a structured report (decisions, outcomes, open questions).
**Internal Composition**: Maps to `ThoughtJournalTool.generate_retrospective()`.

- **Parameters**:
  - `days` (integer, optional): Bounded time window in days (default: 30).

#### `bb7_journal_get_reasoning_chain`

Extract a chain of reasoning across multiple journal entries for a given
topic. Walks backwards from a decision entry through the `linked_memories`
graph to recover the supporting thought trail.
**Internal Composition**: Maps to `ThoughtJournalTool.get_reasoning_chain()`.

- **Parameters**:
  - `decision_id` (string, required): ID of the decision entry to trace supporting thoughts for.

#### `bb7_journal_stats`

Get statistics about the thought journal — entry counts by type, age
distribution, outcome-validation rates, BM25 index health.
**Internal Composition**: Maps to `ThoughtJournalTool.get_stats()`.

- **Parameters**: None.

#### `bb7_journal_linked_entries`

Get entries that are explicitly or implicitly linked to the given memory
key. The reverse-lookup counterpart to `memory_tool.get_related()`.
**Internal Composition**: Maps to `ThoughtJournalTool.get_linked_entries()`.
Searches every entry's `linked_memories[]` for the key, then walks implicit
BM25 similarity to surface unlinked-but-related entries.

- **Parameters**:
  - `memory_key` (string, required): The memory store key to reverse lookup.
  - `include_content` (boolean, optional): Include entry content previews (default: `true`).
