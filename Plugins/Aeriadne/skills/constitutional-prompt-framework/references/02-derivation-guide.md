# 02 - Derivation Guide

Use this guide when authoring a substantial agent constitution from scratch or re-deriving one from loose notes.

## Phase 0: Establish mission gravity

Extract the irreducible mission in one sentence:

```text
This agent exists to [perform work] for [principal/user] under [constraints] so that [success condition].
```

Then expand it into three operational statements:

- What the agent must optimize for.
- What the agent must refuse or avoid.
- What the agent must preserve across time.

If the mission cannot be stated, do not draft persona yet. Persona before mission is paint on fog.

## Phase 1: Classify the agent

Identify the agent type:

- Coding agent.
- Research agent.
- Analyst.
- Reviewer.
- Planner.
- Orchestrator.
- Creative collaborator.
- Tutor.
- Domain specialist.
- Operations agent.
- Multi-agent coordinator.
- Hybrid.

Then identify the deployment surface at the minimum needed resolution:

- Chat-only.
- Web agent.
- API agent.
- IDE agent.
- Local CLI.
- Repository-scoped coding agent.
- Workspace agent with files.
- Connector-enabled agent.
- Multi-agent runtime.
- Unknown or portable.

For unknown or portable targets, write conditional protocols. Example: "When file-reading capability is available, inspect source files before editing. If unavailable, request pasted excerpts or proceed from supplied text with an assumptions ledger."

## Phase 2: Extract non-negotiables

Group constraints into four buckets:

1. **Authority:** who can override what, who approves irreversible actions, which instructions outrank others.
2. **Safety and security:** illegal, harmful, destructive, privacy, credential, or exfiltration boundaries.
3. **Mission-critical correctness:** failures that would defeat the agent's purpose.
4. **Operational integrity:** no false claims, no fake tools, no hidden background work, no fabricated evidence.

Only constraints in these buckets are candidates for hard rules.

## Phase 3: Build the opening band

The opening band should answer:

- What is this agent?
- What does it exist to do?
- Who does it serve?
- What is its authority model?
- What must never be compromised?

A strong opening band is concrete and low-theater. It does not need lore unless lore is functional compression for project doctrine.

## Phase 4: Write rules of engagement

Create 5 to 12 hard rules. For each rule, include:

- Trigger.
- Rule.
- Why it matters.
- Surface pattern of violation.
- Recovery behavior.

Example:

```markdown
### No destructive action without approval
- Trigger: Any file deletion, irreversible external action, account change, publish action, or action that could cost money.
- Rule: Do not execute until the authorized operator explicitly approves the exact action.
- Rationale: Autonomy must not cross irreversible boundaries without consent.
- Failure mode: Treating a broad task request as permission to delete, publish, submit, or charge.
- Recovery: Pause, explain the intended action, ask for approval, and offer a reversible alternative.
```

Do not turn style preferences into hard rules. "Be concise" is doctrine. "Never reveal private credentials" is a hard rule.

## Phase 5: Write operating doctrine

Operating doctrine contains soft principles. Use tetrads:

```markdown
### Principle name
- Principle: Default to [behavior] unless [exception].
- Rationale: [structural reason].
- Failure mode: [bad behavior shape].
- Required behavior: [observable pattern].
```

Good doctrine resolves tradeoffs:

- Proceed with explicit assumptions unless missing information would invert the answer.
- Challenge weak premises while preserving user intent.
- Use tools when evidence matters, not to decorate a response.
- Favor concrete artifacts over vague advice.
- Make uncertainty actionable.

## Phase 6: Derive persona from mission

Persona has six layers:

1. Identity.
2. Mission.
3. Archetype.
4. Voice.
5. Posture.
6. Behavioral defaults.

Every persona rule must answer: why this and not the opposite?

If the answer is "because it sounds cool," remove it. If the answer is "because the agent handles high-stakes architecture and must communicate in precise, direct language," keep it.

## Phase 7: Bind capabilities

For each capability category, specify:

- Trigger.
- Use case.
- Non-use case.
- Verification.
- Approval gate.
- Fallback.

Capability categories include:

- Files and workspace.
- Web or research.
- Code execution.
- Documents and artifacts.
- Connectors.
- Calendar, email, or personal data.
- Subagents or reviewers.
- External APIs.
- Human approval.

Do not claim a capability exists. Write the protocol conditionally if availability is uncertain.

## Phase 8: Build memory and continuity

Decide whether durable memory exists. If yes, define:

- What earns memory.
- What is forbidden from memory.
- How to update existing memory instead of creating duplicates.
- Scope boundaries.
- User review or consent behavior.

If no memory exists or availability is uncertain, define:

- Session-local assumptions ledger.
- Handoff summaries.
- State snapshots.
- No false persistence claims.

## Phase 9: Ingest domain knowledge

For domain-heavy prompts, do not paste blobs blindly. Transform source material into:

- Canonical facts.
- Glossary.
- Entities and roles.
- Workflows.
- Decision rules.
- Known constraints.
- Examples and counterexamples.
- Open questions.

Place large domain material in the middle with clear headings.

## Phase 10: Define protocols

Add handlers for common situations:

- Starting a task.
- Planning.
- Asking clarifying questions.
- Making assumptions.
- Using tools.
- Evaluating evidence.
- Writing code.
- Editing files.
- Producing artifacts.
- Reporting uncertainty.
- Recovering from errors.
- Escalating or refusing.
- Finalizing deliverables.

Protocols convert values into repeatable execution.

## Phase 11: Define output contracts

Specify default output forms:

- Design note.
- Implementation plan.
- Full artifact.
- Patch or diff.
- Scorecard.
- Audit report.
- Red-team report.
- Manifest.
- Handoff summary.

Include verbosity rules and citation rules when relevant.

## Phase 12: Add evaluation

Add acceptance gates:

- Layer coherence score.
- Authority safety score.
- Capability dispatch score.
- Memory hygiene score.
- Output contract score.
- Platform portability score.
- Red-team survival score.

Use `16-evaluation-rubric.md`.

## Phase 13: Add living status

Every production constitution ends with:

```markdown
## Living status
Version: [semver or date]
Owner: [owner]
Last updated: [date]
Target platform: [platform or portable]
Known risks: [list]
Pending revisions: [list]
Changelog: [path or inline]
```

## Phase 14: Audit and revise

Run this pass:

- Does the opening band carry mission and authority?
- Are hard rules few and real?
- Does doctrine include failure modes?
- Does persona serve mission?
- Are capabilities routed with fallbacks?
- Is memory governed?
- Are outputs explicit?
- Is domain knowledge navigable?
- Does the ending reinforce execution?
- Can a future maintainer understand why every major section exists?

## Authoring heuristic

Draft in this order:

1. Mission.
2. Authority.
3. Hard ROE.
4. Capability dispatch.
5. Memory.
6. Output contracts.
7. Doctrine.
8. Persona.
9. Domain knowledge.
10. Protocols.
11. Evaluation.
12. Living status.

Then reorder into final constitution structure.
