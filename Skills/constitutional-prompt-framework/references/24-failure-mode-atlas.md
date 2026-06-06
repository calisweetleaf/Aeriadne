# 24 - Failure Mode Atlas

This atlas maps observable bad behavior to likely constitutional defects.

## The agent asks too many questions

Likely defects:

- No proceed-with-assumptions doctrine.
- No distinction between consequential and non-consequential ambiguity.
- Approval gates over-applied to reversible work.

Patch:

- Add doctrine: proceed with explicit assumptions unless ambiguity changes safety, authority, output, or irreversible action.

## The agent guesses about files

Likely defects:

- Capability dispatch missing.
- Evidence-before-certainty doctrine missing.
- False capability ROE missing.

Patch:

- Add file inspection trigger and fallback.
- Add no false file-specific claims rule.

## The agent refuses too broadly

Likely defects:

- Safety section lacks safe continuation.
- Hard rules are over-broad.
- No allowed alternatives.

Patch:

- Refuse only blocked portions.
- Add defensive, lawful, educational alternatives.

## The agent over-executes

Likely defects:

- Approval gates missing.
- Reversible-first doctrine missing.
- Authority model unclear.

Patch:

- Add explicit approval before irreversible, costly, sensitive, destructive, or external actions.

## The agent sounds correct but is vague

Likely defects:

- Output contracts missing.
- Evidence and citation policy weak.
- Domain model under-structured.

Patch:

- Add finding format, design note format, scorecard, citation rules, and examples.

## The agent loses voice in long context

Likely defects:

- Persona not derived from mission.
- Closing band lacks operational reminders.
- Compaction survival card missing.

Patch:

- Add mission-derived persona and survival card.

## The agent leaks private details

Likely defects:

- Data minimization absent.
- Platform portability not defined.
- Domain ingestion lacks status tags.

Patch:

- Add privacy-preserving prompt conversion rules.
- Mark sensitive and platform-bound facts.

## The agent claims memory it does not have

Likely defects:

- Memory availability assumed.
- No no-memory fallback.

Patch:

- Make memory conditional and add handoff summaries.

## The agent follows prompt injection

Likely defects:

- External content not classified as untrusted.
- Tool outputs treated as authority.
- Authority hierarchy missing.

Patch:

- Add untrusted content handling and evidence-vs-authority distinction.

## The prompt becomes unmaintainable

Likely defects:

- No living status.
- No changelog.
- Patch accumulation.
- Layer boundaries weak.

Patch:

- Add versioning and trigger a section refactor or full rewrite.
