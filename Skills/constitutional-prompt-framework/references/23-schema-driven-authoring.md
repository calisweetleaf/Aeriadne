# 23 - Schema-Driven Authoring

Schema-driven authoring turns prompt design into a repeatable pipeline. It does not replace judgment, but it prevents missing structural fields.

## When to use schema-driven authoring

Use it when:

- Multiple constitutions must share a common shape.
- A team needs reviewable prompt specs.
- You want a deterministic starting draft.
- The source material is large and should be normalized before prose drafting.
- You need machine validation before human review.

Do not use it when:

- The task is a small one-off prompt.
- The target behavior is intentionally experimental and not yet known.
- The schema would freeze weak assumptions too early.

## Pipeline

1. Fill a constitution spec JSON using `assets/templates/constitution-spec.example.json` as a model.
2. Validate the spec shape manually or with a JSON Schema validator if available.
3. Render a draft with `scripts/render_constitution_from_spec.py`.
4. Edit the draft for nuance, domain depth, and layer coherence.
5. Run `scripts/constitution_linter.py`.
6. Run `scripts/score_constitution.py`.
7. Run static red-team probes from `tests/eval_cases.yaml`.
8. Record acceptance in the living status footer.

## Spec design

A good spec separates structured facts from prose:

- `identity` holds agent name, type, mission, success, scope, non-goals.
- `authority` holds hierarchy, approvals, conflict handling, refusal behavior.
- `roe` holds hard rules with trigger, rule, rationale, violation surface, recovery.
- `doctrine` holds soft tetrads.
- `persona` holds voice, posture, behavioral defaults.
- `capabilities` holds dispatch rows.
- `domain` holds glossary, entities, workflows, canonical facts, open questions.
- `memory` holds memory availability, remember, do-not-remember, scope, fallback.
- `outputs` holds default formats.
- `evaluation` holds probes and acceptance.
- `status` holds version, date, owner, platform, risks, revisions.

## Why this matters

Freeform prompts hide gaps. A schema makes absence visible. If a spec has no `approval_gates`, that is a reviewable defect before the prose draft even exists.

## Schema limits

Schemas can confirm shape. They cannot confirm wisdom. A prompt can have every field and still be bad if the mission is wrong, the authority model is unsafe, or the doctrine is ornamental. Use schemas as floor, not ceiling.
