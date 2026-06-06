# 12 - Long-Context and Compaction Resilience

Long-context prompts fail when critical instructions are buried, duplicated, or phrased without structure. Compaction can make this worse by preserving summaries while losing nuance.

## Position strategy

### Opening band

Put here:

- Identity.
- Mission.
- Authority.
- Non-negotiable constraints.
- Capability truthfulness.
- Safety and privacy boundaries.

The opening band should be short enough to survive summarization and strong enough to boot the agent's behavior.

### Middle band

Put here:

- Domain knowledge.
- Glossary.
- Taxonomies.
- Examples.
- Extended doctrine.
- Detailed workflows.

Use clear headings, stable labels, and tables. The middle is where retrieval and skim-readability matter.

### Closing band

Put here:

- Operational protocols.
- Output contracts.
- Current state.
- Living status.
- Final reminders.

The closing band is close to generation and should reinforce what the agent must do in the immediate answer.

## Token budgeting

Use size intentionally:

- 1K to 2.5K tokens: small role prompt or task-specific instruction.
- 2.5K to 6K tokens: minimum viable constitution.
- 6K to 12K tokens: robust production constitution.
- 12K to 20K tokens: heavy doctrine or domain prompt.
- Above 20K tokens: justify with navigable domain content, examples, and evals.

A large prompt without navigation is worse than a shorter prompt with strong layer contracts.

## Redundancy strategy

Some redundancy is useful if it reinforces critical constraints in different bands. Bad redundancy repeats wording. Good redundancy restates a core invariant in the layer where it applies.

Example:

- Opening: "Do not claim unavailable capabilities."
- Capability section: "Each capability must have availability, trigger, verification, and fallback."
- Output section: "Report what was actually done, not what was intended."

These reinforce the same truth through different interfaces.

## Compaction survival cards

For very long constitutions, include a small "survival card" near the end:

```markdown
## Compaction survival card
If context is compressed, preserve these invariants:
1. [Mission]
2. [Authority hierarchy]
3. [Hard ROE]
4. [Capability truthfulness]
5. [Memory policy]
6. [Output contract]
7. [Current state]
```

## Navigation labels

Use durable headings:

- `Authority and governance`
- `Rules of engagement`
- `Capability posture`
- `Memory and continuity`
- `Output contracts`
- `Living status`

Avoid whimsical headings that obscure searchability.

## Examples as anchors

Examples can help behavior survive abstraction, but only if they align with rules. Include:

- Standard success case.
- Ambiguous request case.
- Tool unavailable case.
- Approval gate case.
- Refusal and safe alternative case.

## Anti-compaction checklist

- Are critical rules in opening or closing bands?
- Does the middle have searchable headings?
- Are examples consistent with rules?
- Is there a survival card?
- Are domain facts labeled with status and version?
- Is there a living footer?
- Can a summary preserve the mission without losing authority boundaries?

## Summary protocol for handoff

When a long conversation must be compressed or handed off, preserve:

1. Mission.
2. Current state.
3. Authority constraints.
4. Decisions made.
5. Open questions.
6. File/artifact paths.
7. Validation status.
8. Next actions.
9. Risks.

Do not preserve transient chatter unless it affects decisions.
