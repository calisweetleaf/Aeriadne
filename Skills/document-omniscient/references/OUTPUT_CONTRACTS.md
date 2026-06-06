# OUTPUT CONTRACTS

**Purpose**: Give the skill a wide output palette while preserving a stable quality floor.

## Mandatory outputs

Always include these four blocks in some form:

### 1. Corpus map
Minimum fields:
- file or source name
- type
- likely role in corpus
- status: covered, sampled, deferred, unread
- notes on importance

### 2. Global conceptual model
Explain:
- what the corpus is fundamentally about
- which concepts anchor the whole set
- how the pieces fit together
- what changed from the initial hypothesis

### 3. Contradictions, gaps, and unresolved questions
At minimum:
- contradictions
- missing documents or missing context
- terms that are used inconsistently
- confidence limits

### 4. Memory candidates or memory updates performed
At minimum:
- what is stable enough to remember
- what is not yet stable enough
- what was deliberately excluded for safety or uncertainty

## Adaptive optional outputs

Add these when they would genuinely improve the run:
- glossary or ontology
- entity ledger
- timeline
- decision register
- interface map
- dependency graph
- evidence table
- reading order for a future operator
- action plan or next-step memo
- appendix for quotations, tables, formulas, or page references

## Default response skeleton

```markdown
# [Corpus Title or Working Name]

## Corpus map
[table or structured bullets]

## Global conceptual model
[short synthesis followed by structured subsections as needed]

## Contradictions, gaps, and unresolved questions
[table or bullets]

## Memory candidates / memory updates
[stable / provisional / rejected]
```

## Large-run artifact pattern

For large corpora, prefer a durable artifact such as `CORPUS_SYNTHESIS.md` and keep the chat response focused on:
- what was analyzed
- what the main conclusions are
- what artifacts were created
- what remains unresolved

## Style rules

- prefer structure over ornamental prose
- show why the output sections exist
- state confidence when it matters
- use tables when the corpus has many files, entities, or contradictions
- never present speculative synthesis as settled memory
