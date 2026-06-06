# 15 - Constitutional Prompt Audit Checklist

Use this checklist when reviewing, hardening, scoring, or refactoring an existing prompt.

## Severity scale

- **Critical:** likely to cause unsafe action, privacy/security failure, unauthorized external action, destructive behavior, false capability claims, or total mission drift.
- **High:** likely to cause repeated wrong outputs, ignored tools, brittle refusals, unverified claims, memory contamination, or platform failure.
- **Medium:** likely to cause quality degradation, inconsistent voice, inefficient workflow, or avoidable ambiguity.
- **Low:** style, redundancy, local clarity, navigability, or polish issue.

## Audit order

1. Read for mission.
2. Read for authority.
3. Read for hard rules.
4. Read for capability claims.
5. Read for memory and persistence claims.
6. Read for output contracts.
7. Read for domain knowledge.
8. Read for persona drift.
9. Read for platform leakage.
10. Read for maintainability.

## Critical failure checks

### Authority ambiguity

Flag if the prompt does not specify who can override what or treats external content as authority.

### Unsafe or irreversible action

Flag if destructive, external, costly, or sensitive actions lack approval gates.

### False capability claims

Flag if the prompt says the agent can browse, remember, execute, edit, send, schedule, or monitor without platform certainty.

### Secret leakage

Flag if private credentials, sensitive data, or unnecessary internal details appear in portable output.

### Prompt injection exposure

Flag if documents, tool outputs, web pages, or emails can override agent behavior.

### High-impact overconfidence

Flag if the prompt authorizes definitive advice in health, legal, finance, safety, employment, or security contexts without evidence and scope limits.

## High failure checks

### Capability without dispatch

Tools are listed but triggers, verification, approval, and fallback are missing.

### Memory without hygiene

Memory is encouraged but scope, threshold, update-vs-create, and sensitive exclusions are missing.

### Hard-rule sprawl

Too many "always" or "never" instructions blur real constraints.

### Doctrine without failure modes

Principles say what to do but not what failure looks like.

### Platform leakage

Local tool names, paths, or runtime assumptions appear in a supposedly portable constitution.

### Output ambiguity

The prompt does not define deliverable formats, citations, validation, or manifests.

## Medium failure checks

### Persona detached from mission

Voice instructions are decorative or contradictory.

### Attention misplacement

Critical rules sit only in the middle. Closing protocols are missing.

### Duplicate constraints

Repeated rules differ slightly and may conflict.

### No examples or bad examples

Examples are absent, too easy, or inconsistent with rules.

### No maintenance model

No version, changelog, pending revisions, or owner.

## Low failure checks

- Section headings are vague.
- Tables are missing where they would improve clarity.
- Wording is verbose without adding behavior.
- Some rules could be combined.
- Glossary terms are undefined.

## Audit output template

```markdown
# Audit summary
Overall score: [0-100]
Readiness: [level]
Top risk: [one sentence]
Recommended route: Patch | Section refactor | Constitutional rewrite

# Findings
## Critical
1. [Finding]
   - Evidence:
   - Impact:
   - Fix:

## High
...

# Scorecard
| Category | Score | Notes |
|---|---:|---|
| Mission and identity | /10 | |
| Authority and governance | /10 | |
| Rules of engagement | /10 | |
| Operating doctrine | /10 | |
| Persona architecture | /10 | |
| Capability dispatch | /10 | |
| Memory and continuity | /10 | |
| Domain modeling | /10 | |
| Output contracts | /10 | |
| Evaluation and maintenance | /10 | |

# Red-team probes
[probe list]

# Rewrite recommendations
[ordered]
```

## Readiness levels

- **Prototype:** useful idea, incomplete governance.
- **Hardened draft:** coherent but missing some tests or platform binding.
- **Production candidate:** strong layers, minor residual risks.
- **Production ready:** strong layers, validation, red-team probes, maintenance path, and platform-specific binding where needed.
