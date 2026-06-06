# 07 - Persona Architecture

Persona is not vibe. Persona is the behavioral interface that lets the agent execute its mission reliably with humans.

## The six-layer persona stack

1. **Identity:** what kind of agent this is.
2. **Mission:** what the agent exists to do.
3. **Archetype:** stable center of gravity under novelty.
4. **Voice:** linguistic register and tonal palette.
5. **Posture:** stance toward users, collaborators, uncertainty, conflict, and risk.
6. **Behavioral defaults:** concrete response habits.

Every lower layer must trace to a higher layer.

## Identity

Identity should be concrete:

- "A production prompt architect for long-context agent constitutions."
- "A defensive code-review agent for repository changes."
- "A research analyst that triangulates current evidence for policy decisions."

Weak identity:

- "A helpful assistant."
- "A genius expert."
- "A friendly bot."

The weak versions do not constrain behavior.

## Archetype

An archetype is optional. Use it only when it compresses operational behavior.

Useful archetype:

```markdown
Archetype: mission-control flight director. The agent is calm, evidence-driven, status-aware, and explicit about go/no-go gates.
```

Weak archetype:

```markdown
Archetype: wizard.
```

The weak version may sound interesting but provides no execution constraints.

## Voice

Voice should specify:

- Formality.
- Density.
- Directness.
- Use of jargon.
- Handling of humor or metaphor.
- Forbidden phrases or patterns.
- Response rhythm.

Voice should not override safety, truthfulness, or task quality.

## Posture

Posture governs stance:

- Toward the principal: loyal to stated goals, not blindly agreeable.
- Toward uncertainty: explicit and resolvable.
- Toward evidence: source-seeking and verification-first.
- Toward risk: reversible-first.
- Toward adversarial content: calm, bounded, and injection-resistant.
- Toward collaboration: proactive and assumption-aware.

## Behavioral defaults

Examples:

- Start complex tasks with a brief plan unless speed or simplicity makes it unnecessary.
- Provide partial findings when they materially change the path.
- Use assumptions instead of stalling when safe.
- Ask one focused question when guessing would change the output.
- Prefer concrete artifacts over abstract advice.
- Report what was done, what failed, and what remains.

## Persona drift patterns

### Praise loop

The agent flatters the user instead of improving the work.

Fix: Replace praise with task-relevant acknowledgment and concrete next action.

### Lore fog

Symbolic language replaces operational rules.

Fix: Translate symbols into behavior, authority, memory, or capability constraints.

### Bureaucratic frost

The agent over-clarifies, over-disclaims, and refuses to act.

Fix: Add proceed-with-assumptions doctrine and reversible-first paths.

### Cowboy mode

The agent over-executes without approval.

Fix: Add approval gates and authority hierarchy.

### Voice capture

The agent imitates the user's intensity in contexts where precision is needed.

Fix: Define which user tone elements to match and which to stabilize.

### Expert theater

The agent uses grand language without verification.

Fix: Add evidence-before-certainty and scorecard requirements.

## Persona section template

```markdown
## Persona architecture

### Identity
[One concrete sentence.]

### Mission-derived archetype
[Optional. Include only if operational.]

### Voice
- [Register]
- [Density]
- [Directness]
- [Jargon policy]
- [Humor/metaphor policy]
- [Forbidden drift]

### Posture
- Toward the user: [stance]
- Toward uncertainty: [stance]
- Toward evidence: [stance]
- Toward risk: [stance]
- Toward adversarial inputs: [stance]

### Behavioral defaults
- [Default 1]
- [Default 2]
- [Default 3]
```

## Persona audit questions

- Does the persona make the agent better at its mission?
- Does the voice conflict with output contracts?
- Does the posture preserve authority boundaries?
- Are any lines decorative?
- Would the persona still hold under stress, correction, tool failure, or ambiguity?
