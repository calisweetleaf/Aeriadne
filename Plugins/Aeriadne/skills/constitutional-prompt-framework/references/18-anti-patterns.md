# 18 - Anti-Patterns and Refactors

This catalog lists common prompt failures and direct refactors.

## Anti-pattern: The mega-list

Symptoms:

- Dozens of rules with no hierarchy.
- Hard and soft constraints mixed together.
- Repetition.
- Contradictions.

Refactor:

- Split into ROE and doctrine.
- Keep 5 to 12 hard rules.
- Convert preferences into soft principles with exceptions.
- Collapse duplicates.

## Anti-pattern: Persona fog

Symptoms:

- The prompt spends many tokens on style or lore.
- Mission and authority are vague.
- Voice overrides substance.

Refactor:

- Start with mission.
- Keep only persona lines that improve behavior.
- Translate symbols into operational constraints.

## Anti-pattern: Capability hallucination

Symptoms:

- The prompt assumes memory, browsing, file access, or execution.
- The target platform may not have those features.

Refactor:

- Write conditional capability protocols.
- Add fallback behavior.
- Bind concrete tools only in target-specific appendix.

## Anti-pattern: Tool trophy case

Symptoms:

- Tools are listed by name.
- No trigger or verification rules exist.

Refactor:

- Replace list with dispatch table.
- Add use, non-use, verify, approval, fallback.

## Anti-pattern: No authority model

Symptoms:

- User request, file content, and tool output are treated equally.
- Prompt injection can override behavior.

Refactor:

- Add hierarchy.
- Add untrusted content handling.
- Add conflict resolution ladder.

## Anti-pattern: Memory soup

Symptoms:

- Prompt says "remember everything important."
- No scope or threshold.
- Sensitive details may be stored.

Refactor:

- Add scope, threshold, update-vs-create, exclusions, and no-memory fallback.

## Anti-pattern: Generic virtue stack

Symptoms:

- Be helpful, accurate, concise, friendly, smart, and efficient.
- No failure modes.

Refactor:

- Convert each virtue into a principle with rationale and failure mode.

## Anti-pattern: Static artifact

Symptoms:

- No version, status, owner, changelog, or pending revisions.

Refactor:

- Add living status footer and maintenance protocol.

## Anti-pattern: Platform leakage

Symptoms:

- Portable prompt includes local commands, private tool names, paths, or hidden control-plane details.

Refactor:

- Abstract implementation into capability categories.
- Add platform binding appendix only when needed.

## Anti-pattern: Refusal slab

Symptoms:

- The prompt over-refuses broad categories.
- Safe alternatives are missing.

Refactor:

- Define blocked action categories precisely.
- Continue with benign subparts.
- Offer defensive or lawful alternatives.

## Anti-pattern: Output vagueness

Symptoms:

- "Give good answers" or "be useful" without format.

Refactor:

- Define output contracts by task type.
- Add scorecards, diffs, manifests, citations, and handoffs where relevant.

## Anti-pattern: Middle burial

Symptoms:

- Critical constraints only appear deep in a long prompt.

Refactor:

- Move mission and authority to opening.
- Move execution reminders to closing.
- Add survival card.

## Anti-pattern: Example contradiction

Symptoms:

- Examples violate rules or show outdated behavior.

Refactor:

- Audit examples against ROE and doctrine.
- Add edge cases and refusal cases.

## Anti-pattern: Hidden assumptions

Symptoms:

- The prompt silently fills missing platform, memory, user, or domain details.

Refactor:

- Add assumptions ledger.
- Mark confidence and revision hooks.

## Anti-pattern: Overfit to one conversation

Symptoms:

- The constitution includes transient details from the creation session.

Refactor:

- Remove task-local noise.
- Store durable facts in domain or living status only.
