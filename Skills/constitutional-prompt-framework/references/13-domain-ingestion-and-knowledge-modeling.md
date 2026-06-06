# 13 - Domain Ingestion and Knowledge Modeling

Domain notes become useful only after they are structured. This reference explains how to convert source material into a domain model inside a constitution.

## Ingestion goal

The agent should not merely carry domain text. It should know how to use it.

Transform source material into:

- Canonical facts.
- Entities and roles.
- Glossary.
- Taxonomies.
- Workflows.
- Decision rules.
- Constraints.
- Examples.
- Counterexamples.
- Open questions.
- Deprecated or superseded material.

## Extraction pass

Read source material and extract:

```markdown
## Extracted domain model

### Mission facts
- [facts tied to purpose]

### Entities
- [entity]: [role, relationship, constraints]

### Terms
- [term]: [definition]

### Workflows
- [workflow]: [steps, triggers, outputs]

### Decisions
- [decision]: [status, rationale, date if known]

### Constraints
- [constraint]: [scope, authority]

### Examples
- [example]: [what it demonstrates]

### Open questions
- [question]: [impact]
```

## Canonicalization rules

- Prefer current, explicit, and repeated facts over isolated fragments.
- Mark uncertainty rather than smoothing it away.
- Preserve source language when it carries technical meaning.
- Replace symbolic language with operational definitions unless symbolic terms are canonical handles.
- Avoid mixing assumptions with facts.

## Domain placement

Place the domain model in the middle of the constitution. Keep opening and closing bands reserved for control logic.

Use subheadings that can be found by search. Avoid burying facts in prose.

## Status tags

Use status tags for facts:

- `Canonical`: confirmed and active.
- `Assumed`: inferred but not confirmed.
- `Deprecated`: previously true or previously used, now replaced.
- `Open`: unresolved.
- `Sensitive`: minimize exposure.
- `Platform-bound`: only valid in a specific environment.

## Knowledge conflict handling

When sources conflict:

1. Prefer higher-authority source.
2. Prefer newer source if authority is equal.
3. Preserve both with status if conflict matters.
4. Ask or mark open if the conflict affects output.
5. Do not silently merge incompatible facts.

## Example conversion

Raw note:

```text
The agent should be sharp and never waste my time. It needs to use files before guessing. It should remember core project things but not random temporary details.
```

Constitutional conversion:

```markdown
### Evidence before speculation
- Principle: When the task references available files or project artifacts, inspect them before making file-specific claims.
- Rationale: File-backed tasks fail when the agent guesses from memory.
- Failure mode: Summarizing, editing, or diagnosing a file without reading it.
- Required behavior: Use file capability first; if unavailable, state that limitation and request excerpts or proceed with assumptions.

### Memory threshold
- Principle: Remember only durable project facts, explicit preferences, reusable workflows, and corrections that will improve future work.
- Rationale: Memory should preserve signal, not task noise.
- Failure mode: Storing transient details from a single session as global doctrine.
- Required behavior: Use the narrowest scope and update existing entries before creating new ones.
```

## Domain ingestion anti-patterns

### Note dump

Pasting raw notes without structure.

Fix: Extract facts, terms, workflows, and decisions.

### Secret stuffing

Embedding sensitive information because it appeared in source notes.

Fix: Redact and preserve abstract behavior.

### Lore without semantics

Keeping symbolic labels that the agent cannot operationalize.

Fix: Define each symbolic label as behavior, role, workflow, or constraint.

### Unversioned canon

Treating all source material as equally current.

Fix: Add status tags and dates where available.

## Domain model audit questions

- Are canonical facts separated from assumptions?
- Are key terms defined?
- Are workflows actionable?
- Are sensitive facts minimized?
- Are conflicts marked?
- Are deprecated facts labeled?
- Are examples tied to behavior?
- Could the agent use the domain section without the original source notes?
