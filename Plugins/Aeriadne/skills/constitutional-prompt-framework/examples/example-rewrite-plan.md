# Example Rewrite Plan

Source prompt: Thin code reviewer prompt
Date: 2026-06-05
Route: Full constitutional rewrite

## Mission extraction

Canonical mission:

```text
Review repository changes for correctness, security, maintainability, and test risk, then produce actionable findings grounded in inspected evidence.
```

## Preserve

- Direct review style.
- Security and correctness priority.
- Preference for actionable fixes.

## Remove or abstract

| Source element | Action | Reason |
|---|---|---|
| "Be a genius reviewer" | Remove | Ornamental persona without behavior |
| "Always run all tests" | Replace | May be impossible or too costly; needs capability dispatch |
| Local tool names | Abstract | Target is portable |

## Add

| New section | Reason | Failure prevented |
|---|---|---|
| Authority and governance | Resolve instruction conflicts | Prompt injection and unsafe action |
| Rules of engagement | Hard approval and truthfulness | Destructive edits and false validation |
| Capability posture | Tool use triggers and fallback | Tool under-use or theater |
| Memory policy | Avoid storing secrets or transient branch details | Memory contamination |
| Output contracts | Standardize findings | Unusable review output |
| Evaluation | Test behavior | Invisible drift |

## Acceptance criteria

- Score target: 85+
- No critical findings.
- Pass false validation and destructive action probes.
- No platform leakage in portable version.
