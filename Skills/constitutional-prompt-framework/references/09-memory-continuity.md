# 09 - Memory and Continuity

Memory is a governed interface. It should preserve durable signal and reject noise.

## Memory availability classes

### Durable memory available

The platform can store facts across sessions.

Constitution must define:

- What earns memory.
- What does not earn memory.
- Consent behavior.
- Update-vs-create behavior.
- Sensitive data exclusions.
- Scope boundaries.

### Session memory only

The agent can remember within the current conversation but not across future sessions.

Constitution must define:

- Assumptions ledger.
- State snapshots.
- Handoff summaries.
- No durable persistence claims.

### External state available

The agent can read project files, notes, databases, or knowledge bases.

Constitution must define:

- Canonical source hierarchy.
- Sync behavior.
- Conflict handling.
- Redaction rules.
- Write approval.

### Unknown memory

The platform may or may not persist.

Constitution must define conditional behavior and avoid promises.

## What earns memory

Memory candidates:

- Explicit user requests to remember.
- Durable user preferences that affect future work.
- Canonical project definitions.
- Stable glossary or taxonomy entries.
- Reusable procedures.
- Long-lived constraints.
- Corrections to prior assumptions.

Memory non-candidates:

- One-off task details.
- Temporary emotions or incidental context.
- Secrets, credentials, tokens, private keys.
- Sensitive personal data unless explicitly authorized and necessary.
- Speculation.
- Duplicates of existing memory.
- Data that belongs in a project file instead of personal memory.

## Scope rule

Define where memory belongs:

- User-level: stable preferences and identity-level facts.
- Project-level: project doctrine, naming, architecture, decisions.
- Task-level: current work state and assumptions.
- Artifact-level: changelog, status footer, inline notes.

Default to the narrowest scope that preserves usefulness.

## Threshold rule

A fact earns durable memory only if it is:

- Stable.
- Reusable.
- Confirmed or explicitly provided.
- Helpful for future interactions.
- Safe to store.

## Update-vs-create rule

Search or inspect existing memory/state before creating a new entry. If an entry exists, update it rather than duplicating it. If conflict exists, preserve both only when both are valid in different scopes or time periods.

## Memory contamination patterns

### Preference overgeneralization

A user wants one response in a style. The agent stores it as a global preference.

Fix: Store only durable preferences, not local instructions.

### Project bleed

A project-specific rule becomes global behavior.

Fix: Scope to project.

### Duplicate drift

Several near-identical memories conflict over time.

Fix: Merge and timestamp.

### Secret persistence

Sensitive content is stored because it was useful once.

Fix: Redact and store only the abstract procedure.

### Stale canon

Old project facts remain active after redesign.

Fix: Use versioned memory and deprecate old facts.

## Continuity without durable memory

When durable memory is unavailable, the constitution should require:

- End-of-session handoff when work is complex.
- Status footer in artifacts.
- Assumptions ledger.
- Changelog in long-lived documents.
- Explicit statement that persistence is not guaranteed.

## Handoff summary template

```markdown
## Handoff summary
Mission: [what we are building]
Current state: [what exists]
Decisions made: [canonical decisions]
Open questions: [unresolved]
Risks: [known risks]
Next actions: [ordered]
Files/artifacts: [paths or names]
Assumptions: [current assumptions]
```

## Memory policy template

```markdown
## Memory and continuity

The agent treats memory as governed state, not a transcript dump.

Remember only facts that are stable, reusable, confirmed, safe, and helpful for future work. Do not remember secrets, credentials, sensitive personal data, one-off task details, or speculative inferences.

Before creating a memory, check whether an existing memory or project artifact should be updated. Use the narrowest viable scope: task, artifact, project, then user.

If durable memory is unavailable, maintain session continuity through assumptions ledgers, status snapshots, and handoff summaries. Do not claim future recall unless persistence is actually available.
```

## Memory audit questions

- Does the constitution say what should be remembered?
- Does it say what should not be remembered?
- Does it define scope?
- Does it require update before duplicate creation?
- Does it handle no-memory environments?
- Does it prevent secret or sensitive persistence?
- Does it connect memory to changelog and living status?
