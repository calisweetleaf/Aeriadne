# TOOLING PLAYBOOK

**Purpose**: Make tool use a first-class part of corpus reasoning rather than an afterthought.

## Preflight

Before deep reading, determine which capabilities are actually present in the current environment.

Check for:
- project knowledge or file search
- code execution or python
- file creation or artifact generation
- web search
- memory
- image or pdf understanding

Treat `claude_tool_pack.md` as a capability primer, not as hard truth for every session. Use it to think better about what may exist, then validate the current run.

## Code execution and python

Use code execution when it materially improves analysis quality.

High-value uses:
- build a corpus manifest
- produce a coverage matrix
- extract and normalize entity lists
- deduplicate repeated passages or tables
- generate timelines
- cluster repeated themes or terminology
- build contradiction tables
- convert notes into durable artifacts

Useful artifact names:
- `CORPUS_MANIFEST.md`
- `COVERAGE_MATRIX.csv`
- `ENTITY_LEDGER.md`
- `TIMELINE.md`
- `CONTRADICTION_MATRIX.md`
- `MEMORY_CANDIDATES.md`
- `CORPUS_SYNTHESIS.md`

## Project knowledge and file search

When project knowledge or retrieval is present:
- use it before asking the user to re-upload files
- reference filenames explicitly when the corpus is large
- pull targeted context for unresolved questions instead of re-reading the whole set blindly
- when retrieval mode is active, remember that only relevant slices may be returned; ask for the missing slice or widen the query when confidence is low

## File creation and artifacts

Use durable output files when:
- the corpus is large
- the user will want to reuse the synthesis later
- tables or diagrams are easier to inspect than chat prose
- memory is unavailable and a memory artifact is needed instead

Prefer one strong master artifact over many scattered small ones unless the corpus clearly separates into distinct tracks.

## Web search

Use web search only when external freshness matters.

Trigger conditions:
- the corpus depends on current laws, model capabilities, product changes, org charts, or standards
- a document references a missing external source whose current state matters
- the user asks for verification against the outside world

Do not leave the corpus for the web just because the analysis feels hard.

## Memory

Use memory conservatively.

Safe memory targets:
- durable project names and definitions
- stable abbreviations and terminology
- recurring interfaces and invariants
- user-stated preferences that clearly persist across sessions
- important decisions whose rationale is settled

Unsafe memory targets:
- raw notes
- temporary tasks
- secrets
- unstable interpretations
- claims that depend on a single weak source

If memory is not available, create `MEMORY_CANDIDATES.md` and explain why those candidates are or are not ready.

## PDF and visual handling

If the environment supports visual pdf analysis, use it for charts, diagrams, scanned pages, and figure-heavy appendices. If it only supports text extraction, declare the limitation and note where visual evidence may be missing.

## Minimum externalization rule

For any corpus large enough to make hidden state fragile, externalize at least three things:
1. a corpus manifest
2. a contradiction or uncertainty register
3. a memory candidate ledger

## Stop conditions

Do not stop just because a clean summary exists.

Stop when:
- coverage is explicit
- the conceptual model is stable enough to defend
- contradictions are surfaced
- memory work is either completed or intentionally deferred
