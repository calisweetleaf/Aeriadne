# FAILURE GRAMMAR

**Purpose**: Describe what wrong looks like before it becomes obvious.

## Pre-Failure Signatures

### Signature 1: Premature summary smoothness
The response becomes polished too early.

Smell:
- elegant overview
- little mention of uncertainty
- no coverage ledger
- weak or absent distinction between stable and provisional beliefs

### Signature 2: Section skipping by vibe
The model claims understanding without explicit traversal.

Smell:
- headings cited, body ignored
- appendices or footnotes omitted without declaration
- dense tables, figures, or annexes not accounted for

### Signature 3: Local-only competence
Each file is summarized well, but the corpus still has no global model.

Smell:
- no explanation of why these files were assembled together
- no cross-document contradiction analysis
- no hierarchy between normative and descriptive sources

### Signature 4: Tool underuse
The chat remains purely verbal when externalized artifacts would reduce error.

Smell:
- many entities but no ledger
- timelines discussed but not written
- contradictions described narratively instead of tabulated

### Signature 5: Memory eagerness
The model wants to persist facts before ambiguity is resolved.

Smell:
- immediate memory update after first pass
- no stable versus provisional split
- no note about sensitivity or privacy

## False Success Patterns

1. A concise executive summary that hides unread sections.
2. A stack of per-file notes with no cross-document synthesis.
3. A confident answer that never states what remains unknown.
4. Memory updates that later turn out to encode speculative interpretations.
5. A tooling-rich run that still lacks conceptual integration.

## Recovery Protocols

### Recovery A: Coverage reset
- stop generating conclusions
- rebuild the corpus manifest
- mark covered, sampled, deferred, and unread sections
- resume only after the gaps are visible

### Recovery B: Corpus re-centering
- ask what the corpus is for
- classify each document by role: normative, descriptive, historical, speculative, obsolete, supporting, appendix
- rebuild the global model from roles instead of summaries

### Recovery C: Memory quarantine
- retract any unstable memory write if possible
- move uncertain items into `MEMORY_CANDIDATES.md`
- split stable, provisional, unresolved

### Recovery D: Tool escalation
- create or update the contradiction matrix
- externalize timelines, entity ledgers, and glossaries
- if external freshness matters, run targeted web checks

## Rejection Criteria

Treat the run as incomplete if any one of these is true:
1. some files or major sections were skipped without declaration
2. the output cannot explain why the documents belong together
3. memory was updated before stabilization

## Diagnostic Questions

Ask these when quality feels off:
- what have i not actually read yet
- what claim am i repeating without clear evidence
- which document is normative here
- what would overturn my current interpretation
- what should be externalized right now instead of held implicitly
