# 19 - Rewrite Playbook

Use this playbook to decide whether to patch, refactor, or rebuild an existing prompt.

## Rewrite route selection

### Patch

Use when:

- Mission is clear.
- Layers are mostly coherent.
- One or two constraints are missing.
- Platform binding is almost correct.

Output:

- Change summary.
- Patched section.
- Reason for minimal edit.

### Section refactor

Use when:

- One layer is bloated, contradictory, or incomplete.
- ROE and doctrine are mixed.
- Capability or memory section is weak.
- Persona is overgrown but mission is intact.

Output:

- Refactor plan.
- Before/after section.
- Cross-layer impact notes.

### Full constitutional rewrite

Use when:

- Mission is unclear or conflicted.
- Authority model is missing.
- Prompt is mostly vibe or scattered rules.
- Platform leakage is pervasive.
- False capability claims are central.
- Memory or safety failures are structural.

Output:

- Design note.
- Re-derived constitution.
- Audit score.
- Red-team probes.
- Maintenance notes.

## Preservation pass

Before rewriting, extract:

- Core mission.
- Unique doctrine.
- User-specific preferences.
- Domain terms.
- Non-negotiables.
- Useful examples.
- Tone that serves mission.

Do not preserve:

- Duplicates.
- Stale platform names.
- Private secrets in portable prompts.
- Ornamental intensity.
- Contradictory absolutes.
- Unsupported capability claims.

## Refactor sequence

1. Write mission sentence.
2. Build authority hierarchy.
3. Separate hard ROE from soft doctrine.
4. Convert soft doctrine into tetrads.
5. Derive persona from mission.
6. Build capability dispatch.
7. Add memory policy.
8. Structure domain model.
9. Add output contracts.
10. Add evaluation and status.
11. Run audit and score.

## Rewrite plan template

```markdown
# Rewrite plan

## Route
Patch | Section refactor | Full constitutional rewrite

## Preserve
- [doctrine]
- [terms]
- [examples]

## Remove or abstract
- [item] because [reason]

## Add
- [section] because [failure prevented]

## Risks
- [risk]

## Acceptance gate
- [score target]
- [red-team probes]
```

## Diff language

When not producing literal diffs, use change cards:

```markdown
### Change: [name]
- Before: [problem]
- After: [new behavior]
- Reason: [structural reason]
- Affected layers: [layers]
```

## Rewrite integrity checks

- Did the rewrite preserve the user's real mission?
- Did it remove only accidental complexity?
- Did it avoid flattening useful domain nuance?
- Did it introduce any new false capability claims?
- Did it include version and status?
- Did it score better under the rubric?
