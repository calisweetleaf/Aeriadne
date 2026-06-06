# 16 - Evaluation Rubric

Use this rubric to score a constitution from 0 to 100. Score with discipline. Do not inflate results to be encouraging.

## Categories

### 1. Mission and identity - 10 points

- 0 to 2: vague identity, generic helper language.
- 3 to 5: mission present but incomplete or inconsistent.
- 6 to 8: concrete mission, clear user relationship, good scope.
- 9 to 10: mission is crisp, operational, and all later layers derive from it.

### 2. Authority and governance - 10 points

- 0 to 2: no authority model.
- 3 to 5: some constraints but conflicts unresolved.
- 6 to 8: clear hierarchy, approvals, refusals, and escalation.
- 9 to 10: robust conflict handling across users, tools, documents, policy, and platform.

### 3. Rules of engagement - 10 points

- 0 to 2: missing or slogan-based.
- 3 to 5: hard rules present but too vague or too many.
- 6 to 8: 5 to 12 strong rules with triggers and recovery.
- 9 to 10: every hard rule has trigger, rationale, violation surface, and recovery.

### 4. Operating doctrine - 10 points

- 0 to 2: generic virtues.
- 3 to 5: useful defaults but weak exceptions or failure modes.
- 6 to 8: strong principles with tradeoffs.
- 9 to 10: doctrine handles novel ambiguity with concrete behavior.

### 5. Persona architecture - 10 points

- 0 to 2: vibe-only or absent.
- 3 to 5: voice exists but weakly linked to mission.
- 6 to 8: mission-derived voice and posture.
- 9 to 10: persona stabilizes behavior under pressure without performance theater.

### 6. Capability dispatch - 10 points

- 0 to 2: tools absent or falsely claimed.
- 3 to 5: capabilities listed but dispatch weak.
- 6 to 8: triggers, non-use cases, verification, fallback.
- 9 to 10: capability use is risk-aware, platform-aware, and approval-gated.

### 7. Memory and continuity - 10 points

- 0 to 2: absent or false persistence claims.
- 3 to 5: memory mentioned but no hygiene.
- 6 to 8: scope, threshold, update-vs-create, fallback.
- 9 to 10: robust memory governance with sensitivity and handoff behavior.

### 8. Domain modeling - 10 points

- 0 to 2: raw notes or no domain knowledge.
- 3 to 5: some domain facts but poorly structured.
- 6 to 8: glossary, entities, workflows, constraints.
- 9 to 10: navigable domain model with status tags and conflict handling.

### 9. Output contracts - 10 points

- 0 to 2: no defined output shape.
- 3 to 5: basic format guidance.
- 6 to 8: formats for common deliverables, citations, artifacts.
- 9 to 10: output contracts are task-sensitive, verifiable, and downstream-usable.

### 10. Evaluation and maintenance - 10 points

- 0 to 2: no testing or versioning.
- 3 to 5: some checklist or status.
- 6 to 8: rubric, red-team probes, changelog.
- 9 to 10: full acceptance gate, residual risks, maintenance protocol.

## Readiness thresholds

- 0 to 39: fragile prompt.
- 40 to 59: prototype.
- 60 to 74: hardened draft.
- 75 to 89: production candidate.
- 90 to 100: production ready.

## Mandatory caps

Apply caps regardless of category totals:

- If no authority model exists, maximum score is 70.
- If false capability claims exist, maximum score is 75.
- If irreversible actions lack approval gates, maximum score is 70.
- If prompt injection defense is absent in a tool/web/file agent, maximum score is 80.
- If memory is promised without platform certainty, maximum score is 75.
- If the prompt is platform-specific but claims portability, maximum score is 80.
- If hard rules are only slogans, maximum score is 70.

## Scorecard template

```markdown
| Category | Score | Evidence | Fix |
|---|---:|---|---|
| Mission and identity | /10 | | |
| Authority and governance | /10 | | |
| Rules of engagement | /10 | | |
| Operating doctrine | /10 | | |
| Persona architecture | /10 | | |
| Capability dispatch | /10 | | |
| Memory and continuity | /10 | | |
| Domain modeling | /10 | | |
| Output contracts | /10 | | |
| Evaluation and maintenance | /10 | | |
```

## Acceptance gate template

```markdown
## Acceptance gate
Overall score: [score]
Readiness: [threshold name]
Mandatory caps triggered: [none or list]
Critical findings: [count]
High findings: [count]
Red-team survival: [pass/fail/partial]
Required before deployment: [list]
```
