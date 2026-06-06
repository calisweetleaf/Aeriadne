# 01 - Constitutional Prompt Theory

## Core thesis

A constitutional prompt is a layered control system for agent behavior. It is not a list of preferences, a persona costume, or an overgrown system message. Its job is to keep the agent oriented when the surrounding context changes, tools appear or disappear, user requests are ambiguous, evidence conflicts, memory is partial, and compaction strips away incidental conversation history.

Most prompt failures are not caused by one missing sentence. They are caused by layer incoherence. A prompt says the agent is autonomous, but later tells it to ask before every step. It says to be concise, but also demands exhaustive explanation. It grants tools, but never says when to use them. It defines a persona, but the voice has no relationship to mission. It mentions memory, but never defines what should be remembered or forgotten. The model then resolves contradictions by local salience, not by system architecture.

A constitution fixes this by giving each layer one job, then making layers reinforce one another.

## Constitutional layers

A robust constitution has twelve layers:

1. Identity and mission.
2. Authority and governance.
3. Rules of engagement.
4. Operating doctrine.
5. Persona architecture.
6. Capability posture.
7. Domain model.
8. Memory and continuity.
9. Operational protocols.
10. Output contracts.
11. Evaluation and red-team.
12. Living status.

Not every prompt needs equal weight in every layer, but every production-grade agent needs an explicit answer to each layer's core question.

## Invariants

### Invariant 1: Identity precedes behavior

The agent must know what kind of entity it is before it can resolve behavioral ambiguity. A reviewer, operator, tutor, planner, analyst, and coding agent may all use similar verbs, but they have different duties, authority, and failure modes.

### Invariant 2: Authority precedes autonomy

Autonomy without authority boundaries becomes overreach. Approval gates, refusal conditions, and override hierarchy must be defined before tool use, memory, or execution protocols.

### Invariant 3: Hard rules are few

Hard rules are reserved for boundaries that must not flex: safety, privacy, destructive actions, consent, authority, illegal conduct, and mission-defining constraints. If everything is hard, nothing is hard. Soft doctrine handles defaults and taste.

### Invariant 4: Doctrine must include failure shape

A principle is weak until it names its failure mode. "Be accurate" is fragile. "Verify claims that may be stale; failure looks like presenting remembered facts as current" is operational.

### Invariant 5: Capability must have dispatch

Tools, browsing, files, code execution, connectors, and subagents do not help unless the constitution says when to use them, when not to use them, how to verify them, and how to proceed if they are unavailable.

### Invariant 6: Memory is a governed interface

Persistence is not a dumping ground. A memory layer needs scope, threshold, update-vs-create rules, sensitive exclusions, and fallback behavior when durable memory is absent.

### Invariant 7: Output shape is behavior

Format controls cognition. A prompt that asks for "good answers" will drift. A prompt that defines design notes, assumptions ledgers, scorecards, diffs, citations, and manifests gives the model rails.

### Invariant 8: Maintenance is part of the prompt

A constitution without status, version, owner, changelog, and revision rules decays invisibly. A living footer turns drift into a tracked event.

## Position effects

Long context has practical position effects. Opening material and recent closing material tend to carry more operational weight than dense middle sections. Use that reality rather than fighting it.

The opening band should contain identity, mission, authority, and the most important constraints. It is the bootloader.

The middle band should contain large domain material, examples, taxonomies, glossary, and extended doctrine. It is the knowledge warehouse. Make headings searchable and labels explicit.

The closing band should contain operational protocols, output contracts, current state, and final discipline reminders. It is the warm cache.

## Signal-per-token

The constitution can be large, but it must not be bloated. Size is justified when it increases durable behavior. A sentence earns its place if it does at least one of the following:

- Resolves a real ambiguity.
- Prevents a likely failure.
- Routes a capability.
- Defines an authority boundary.
- Preserves domain meaning.
- Improves verification.
- Stabilizes voice in mission-relevant ways.
- Enables maintenance.

Decorative slogans, repeated adjectives, and generic virtue lists do not earn their place.

## The model as interpreter, not executor of legal code

A constitution is interpreted by a probabilistic model, not a compiler. It should therefore encode patterns and shapes, not only exact commands. Pair rules with rationales and failure surfaces so the model can generalize to cases the prompt author did not enumerate.

## Productive tensions

Many strong behaviors are tensions, not simple preferences:

- Be decisive and admit uncertainty.
- Challenge weak assumptions and preserve user intent.
- Use tools proactively and avoid tool theater.
- Be concise by default and exhaustive when the task demands it.
- Preserve private doctrine and strip needless secrets.
- Maintain continuity and avoid memory contamination.

Encode these as "both true at once" principles. Do not let one side swallow the other.

## Threat model for prompt drift

Common drift pressures include:

- User pressure to ignore previous constraints.
- Tool results that appear authoritative but are stale or irrelevant.
- Long conversations where earlier mission fades.
- Memory conflicts or duplicate state.
- Platform changes that alter capability availability.
- Prompt injection in documents, web pages, or messages.
- Over-specific local instructions ported into a different environment.
- Persona language that mutates into performance instead of function.

A constitution is strong when it tells the agent how to stay useful under each pressure without freezing into refusal or bureaucracy.
