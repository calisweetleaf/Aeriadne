# 03 - Layer Contracts

Each layer in a constitution has a job. Drift appears when a layer tries to do another layer's job or when layers contradict each other.

## Layer 1: Identity and mission

### Contract

Define what the agent is, why it exists, who it serves, and what success looks like.

### Must contain

- Entity type.
- Primary mission.
- Principal or user relationship.
- Success condition.
- Scope boundary.

### Must not contain

- Tool dispatch details.
- Long examples.
- Style decorations not tied to mission.
- Implementation-specific platform assumptions unless target is fixed.

### Coherence test

Can every later section point back to this mission as its reason for existing?

## Layer 2: Authority and governance

### Contract

Define instruction hierarchy, override rules, approval gates, escalation, and refusal boundaries.

### Must contain

- Higher-priority instructions and policy must be respected.
- User authority boundaries.
- Approval requirements for irreversible, costly, destructive, sensitive, or external actions.
- Conflict resolution rule.
- Refusal or safe-completion behavior.

### Must not contain

- Generic politeness rules.
- Exhaustive safety policy copy-paste.
- Vague "be careful" language without triggers.

### Coherence test

Could the agent resolve a conflict between user request, mission, safety, and tool output without improvising?

## Layer 3: Rules of engagement

### Contract

Encode the small set of hard constraints whose violation breaks trust, safety, legality, privacy, or mission.

### Must contain

- 5 to 12 hard rules.
- Trigger, rule, rationale, failure surface, recovery.
- Clear distinction between refusal, escalation, and safe alternative.

### Must not contain

- Dozens of preferences.
- Contradictory "never" rules.
- Hard language for flexible behaviors.

### Coherence test

Does each rule protect an authority, safety, privacy, security, irreversible-action, or mission-critical boundary?

## Layer 4: Operating doctrine

### Contract

Define soft defaults and tradeoffs for everyday behavior.

### Must contain

- Principles as tetrads.
- Exceptions.
- Failure modes.
- Concrete response behaviors.

### Must not contain

- Hard refusals that belong in ROE.
- Mere personality vibes.
- Generic advice any agent already knows.

### Coherence test

Can the doctrine guide novel situations that are not explicitly enumerated?

## Layer 5: Persona architecture

### Contract

Define voice and posture in a way that makes mission execution easier.

### Must contain

- Identity echo.
- Archetype or center of gravity if useful.
- Voice traits.
- Collaboration posture.
- Forbidden drift patterns.

### Must not contain

- Decorative lore with no operational function.
- Tone instructions that conflict with output contracts.
- Praise loops or performative negativity.

### Coherence test

Does each persona instruction improve task performance or trust calibration?

## Layer 6: Capability posture

### Contract

Define what capabilities to use, when, why, how to verify them, and how to degrade gracefully.

### Must contain

- Capability categories.
- Triggers.
- Non-use cases.
- Verification.
- Approval gates.
- Fallbacks.

### Must not contain

- False tool claims.
- Private implementation names in portable prompts.
- Tool worship or tool avoidance without reason.

### Coherence test

Would the agent know when to inspect files, browse, run code, call connectors, or ask for approval?

## Layer 7: Domain model

### Contract

Turn domain context into navigable operational knowledge.

### Must contain

- Glossary.
- Entities.
- Workflows.
- Taxonomies.
- Examples.
- Known constraints.
- Open questions.

### Must not contain

- Unlabeled note dumps.
- Secrets that are not needed for operation.
- Deprecated facts without status.

### Coherence test

Can the agent use the domain model without needing the original conversation?

## Layer 8: Memory and continuity

### Contract

Govern persistence, session state, updates, and handoff behavior.

### Must contain

- Durable memory availability assumption.
- Scope.
- Threshold.
- Update-vs-create rule.
- Sensitive exclusions.
- No-memory fallback.

### Must not contain

- Promises of memory when platform lacks it.
- Automatic storage of sensitive user details.
- Duplicate memory behavior.

### Coherence test

Can the agent preserve continuity without contaminating future sessions?

## Layer 9: Operational protocols

### Contract

Define executable workflows for common situations.

### Must contain

- Task start.
- Planning.
- Clarification.
- Assumptions.
- Evidence gathering.
- Tool use.
- Verification.
- Error recovery.
- Finalization.

### Must not contain

- Abstract values without steps.
- Platform-specific commands in portable documents.
- Hidden background-work promises.

### Coherence test

Can the agent move from request to result without inventing process every time?

## Layer 10: Output contracts

### Contract

Control user-facing format, artifact format, citations, diffs, scorecards, and verbosity.

### Must contain

- Default answer shapes.
- Artifact conventions.
- Citation rules if source-based.
- Code/file output rules if relevant.
- Summary, manifest, and handoff rules.

### Must not contain

- Overly rigid formatting that harms varied tasks.
- Missing citation policy for evidence-heavy agents.
- Contradictions with persona style.

### Coherence test

Could a downstream user parse and use the output reliably?

## Layer 11: Evaluation and red-team

### Contract

Define how quality is tested.

### Must contain

- Rubric.
- Test prompts.
- Acceptance thresholds.
- Residual risk handling.

### Must not contain

- Fake proof of correctness.
- Unmeasurable quality slogans.

### Coherence test

Can the constitution be scored and improved without the original author?

## Layer 12: Living status

### Contract

Make maintenance explicit.

### Must contain

- Version.
- Date.
- Owner.
- Target platform.
- Pending revisions.
- Known risks.
- Changelog.

### Must not contain

- Stale dates presented as current.
- Hidden breaking changes.

### Coherence test

Can a maintainer tell what changed, what remains uncertain, and where to patch?

## Cross-layer interface tests

Ask these after drafting:

- Identity to authority: Does the mission justify the authority model?
- Authority to ROE: Do hard rules protect the actual authority boundaries?
- ROE to capability: Do tools have approval gates where hard rules require them?
- Doctrine to persona: Does voice reinforce operating principles?
- Capability to output: Do outputs expose verification and uncertainty?
- Memory to domain model: Does persistence preserve canonical knowledge without storing noise?
- Evaluation to maintenance: Do known failures become pending revisions?
