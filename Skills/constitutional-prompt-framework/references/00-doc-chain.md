# 00 - Doctrine Chain

This file is the navigation layer for the Constitutional Prompt Framework. Use it to decide which references to load and in what order.

## Core path for a full new build

1. Read `01-constitutional-prompt-theory.md` to set the mental model.
2. Read `02-derivation-guide.md` to run the authoring procedure.
3. Read `03-layer-contracts.md` to enforce section responsibility.
4. Read `04-authority-and-governance.md` and `05-rules-of-engagement-patterns.md` to encode the hard control plane.
5. Read `06-operating-doctrine-library.md` and `07-persona-architecture.md` to encode behavior and voice.
6. Read `08-capability-dispatch.md` and `09-memory-continuity.md` to bind action to available capability and continuity.
7. Read `13-domain-ingestion-and-knowledge-modeling.md` if the prompt must carry private or domain-specific knowledge.
8. Read `14-output-contracts.md` to specify deliverable shape.
9. Finish with `15-audit-checklist.md`, `16-evaluation-rubric.md`, and `17-red-team-suite.md`.

## Core path for a prompt audit

1. Read the target prompt once without editing.
2. Load `15-audit-checklist.md`.
3. Load `16-evaluation-rubric.md`.
4. Load `18-anti-patterns.md`.
5. Use `17-red-team-suite.md` to probe likely failure modes.
6. Output severity-ranked findings, scorecard, and a rewrite route from `19-rewrite-playbook.md`.

## Core path for a rewrite

1. Extract canonical mission and non-negotiables from the original.
2. Identify accidental complexity, duplication, platform leakage, vague slogans, and orphan constraints.
3. Use `19-rewrite-playbook.md` to choose patch, section refactor, or full constitutional rewrite.
4. Use `03-layer-contracts.md` to rebuild the file.
5. Use `15-audit-checklist.md` and `16-evaluation-rubric.md` before final delivery.

## Core path for platform porting

1. Read the source constitution and mark all platform assumptions.
2. Load `10-platform-binding-matrix.md`.
3. Load `21-interoperability-notes.md`.
4. Replace concrete tools with capability categories when moving toward portability.
5. Bind capability categories to concrete tools only when moving toward a named target platform.
6. Add graceful degradation for any capability that may not exist.

## Core path for skill packaging

1. Use `SKILL.md` as the entrypoint and keep frontmatter precise.
2. Use references for heavy doctrine and templates for repeatable artifacts.
3. Add scripts only when deterministic validation or transformation helps.
4. Validate package structure with `scripts/validate_skill_package.py`.
5. Keep all local/private/runtime assumptions out of general instructions.

## Reference responsibilities

| File | Responsibility | Load when |
|---|---|---|
| `01-constitutional-prompt-theory.md` | Mental model and invariants | Any substantial work |
| `02-derivation-guide.md` | Step-by-step build process | New build, full rewrite |
| `03-layer-contracts.md` | Layer boundaries and cross-layer tests | Any build or audit |
| `04-authority-and-governance.md` | Override rules, escalation, approvals | Safety, autonomy, sensitive actions |
| `05-rules-of-engagement-patterns.md` | Hard constraint encoding | ROE design or audit |
| `06-operating-doctrine-library.md` | Soft defaults and tradeoffs | Behavior and quality design |
| `07-persona-architecture.md` | Voice and posture derived from mission | Persona-heavy prompts |
| `08-capability-dispatch.md` | Tool and connector use rules | Agents with capabilities |
| `09-memory-continuity.md` | Memory and state behavior | Any persistent or long-running agent |
| `10-platform-binding-matrix.md` | Target platform adaptation | Porting or deployment |
| `11-security-privacy-safety.md` | Sensitive inputs and safe action | Private, regulated, destructive, external-facing tasks |
| `12-long-context-and-compaction.md` | Attention survival and prompt budgeting | Long prompts, heavy context, compaction risk |
| `13-domain-ingestion-and-knowledge-modeling.md` | Domain knowledge extraction | Project-specific or expert prompts |
| `14-output-contracts.md` | Response and artifact formats | User-facing deliverables |
| `15-audit-checklist.md` | Finding and severity structure | Audit and QA |
| `16-evaluation-rubric.md` | Scoring and acceptance gates | Production readiness |
| `17-red-team-suite.md` | Adversarial prompt tests | Stress testing |
| `18-anti-patterns.md` | Failure patterns and fixes | Rewrite, audit, hardening |
| `19-rewrite-playbook.md` | Patch and refactor strategy | Editing existing prompts |
| `20-deployment-and-maintenance.md` | Release and versioning | Production handoff |
| `21-interoperability-notes.md` | Skill portability | Multi-platform skills |
| `22-glossary.md` | Shared vocabulary | Clarification |
| `23-schema-driven-authoring.md` | Machine-readable spec pipeline | Repeatable builds, team review, renderer use |
| `24-failure-mode-atlas.md` | Bad behavior to structural defect map | Debugging prompt failures |

## Loading discipline

Do not load everything for a tiny task. Do load everything necessary for a production-grade constitution or when the user explicitly requests maximal work. When token budget is constrained, load the map, theory, derivation, layer contracts, authority, capability, memory, audit, and rubric docs first.

## Output expectation after chained use

For schema-driven builds, use `23-schema-driven-authoring.md` after the derivation guide and before final editing. For failure diagnosis, use `24-failure-mode-atlas.md` before choosing the rewrite route.

A chained build should finish with:

- A design note.
- A complete constitution.
- A scorecard.
- At least 5 red-team probes.
- Residual risk list.
- Maintenance and deployment notes.

A chained audit should finish with:

- Severity-ranked findings.
- Evidence pointers.
- Scorecard.
- Rewrite route.
- Patched sections or full rewrite if requested.
