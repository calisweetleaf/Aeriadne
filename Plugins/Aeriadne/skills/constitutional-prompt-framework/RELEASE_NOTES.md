# Release Notes - Constitutional Prompt Framework v10

This release rebuilds the original thin skill into a production-grade constitutional prompt architecture package.

## What changed

- Expanded the entry `SKILL.md` into a mode-selecting operational router.
- Added a 25-file chained reference library for theory, derivation, authority, doctrine, persona, capability dispatch, memory, platform binding, security, long-context survival, domain modeling, output contracts, audits, evaluation, red-team probes, anti-patterns, rewrites, deployment, interoperability, schema-driven authoring, and failure diagnosis.
- Added templates for full constitutions, audits, rewrite plans, platform binding, memory policies, capability dispatch, intake, red-team reports, and releases.
- Added deterministic Python scripts for validation, linting, scoring, static eval checks, and spec-to-constitution rendering.
- Added JSON schemas and a JSON-compatible constitution spec pipeline.
- Added examples, eval fixtures, and a machine-readable package manifest.

## Validation run

Validated on 2026-06-05:

```bash
python scripts/validate_skill_package.py .
python scripts/constitution_linter.py examples/example-agent-constitution.md
python scripts/score_constitution.py examples/example-agent-constitution.md
python scripts/run_static_evals.py tests/eval_cases.yaml
python scripts/render_constitution_from_spec.py tests/fixtures/minimal_constitution_spec.json -o /tmp/rendered-constitution.md
```

Result: package validation passed, static eval fixture validation passed, example constitution lint passed, and example constitution scored as production candidate by the heuristic scorer.
