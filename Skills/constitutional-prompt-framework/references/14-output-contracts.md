# 14 - Output Contracts

Output contracts turn intent into usable deliverables. They define what the agent returns, how complete it must be, and how users can inspect the work.

## Default output for new constitution

```markdown
# Design note
- Target agent:
- Deployment assumptions:
- Capability assumptions:
- Authority model:
- Major tradeoffs:
- Known assumptions:

# Complete constitution
[Full Markdown constitution]

# Acceptance gate
- Audit score:
- Critical findings:
- High findings:
- Red-team probes:
- Residual risks:
- Maintenance notes:
```

## Default output for audit

```markdown
# Audit summary
Overall score: [0-100]
Readiness: Prototype | Hardened | Production candidate | Production ready

# Severity-ranked findings
## Critical
- Finding:
  Evidence:
  Impact:
  Fix:

## High
...

# Scorecard
[Rubric table]

# Rewrite route
Patch | Section refactor | Full constitutional rewrite

# Recommended changes
[Specific changes]
```

## Default output for rewrite

```markdown
# Rewrite plan
- Route:
- Preserved doctrine:
- Removed or abstracted material:
- New sections:
- Risks:

# Rewritten constitution
[Full file or patched sections]

# Validation
- Layer coherence:
- Platform leakage:
- Capability truthfulness:
- Memory hygiene:
- Red-team probes:
```

## Default output for skill package

```markdown
# Package manifest
[files created/changed]

# Validation
[script results or manual checks]

# Install/deploy notes
[target surfaces]

# Download
[link if created]
```

## Verbosity policy

- Simple answer: concise, no heavy headings.
- Complex architecture: design note plus structured sections.
- File/artifact generation: manifest plus link.
- Audit: severity-first.
- Rewrite: changes first, artifact second, validation third.
- Uncertainty: actionable caveats near the relevant claim.

## Citation policy

For source-based agents, define:

- Which claims need citations.
- Which sources are authoritative.
- How to cite private documents or file excerpts.
- How to handle conflicting sources.
- How to label unsupported assumptions.

Generic rule:

```markdown
Cite load-bearing factual claims that come from external or user-provided sources. Do not cite common reasoning steps. If sources conflict, cite each side and explain the conflict.
```

## Code and file output policy

For coding or artifact agents:

- Prefer patches/diffs when editing existing files.
- Provide full files when the user requests copy-paste output or when context is small.
- Run tests or validation when available.
- Report commands run and results.
- Do not claim tests passed unless they ran.
- Include file tree for multi-file artifacts.

## User update policy

For long tasks, the constitution may define progress updates. Good update behavior:

- Short.
- Non-repetitive.
- Reports meaningful discoveries, not every internal step.
- Asks a question only if it changes the path.
- Does not promise asynchronous future work unless automation exists.

## Handoff output

A handoff should include:

- Mission.
- Current state.
- Files/artifacts.
- Decisions.
- Open questions.
- Risks.
- Next actions.
- Validation status.

## Output anti-patterns

### Plan instead of artifact

User asks for a prompt. Agent returns advice.

Fix: Produce the prompt and summarize design choices.

### Unscored audit

Agent lists vibes but no severity or score.

Fix: Use rubric and severity categories.

### Invisible assumptions

Agent fills gaps without marking them.

Fix: Add assumptions ledger.

### Wall of text constitution

Agent produces a huge file with no navigation.

Fix: Add stable headings, tables, and status footer.

### Fake validation

Agent says it validated without running checks.

Fix: Distinguish manual review, heuristic script, and actual execution.
