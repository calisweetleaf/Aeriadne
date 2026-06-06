# Manifest

Package: `constitutional-prompt-framework`
Release: `10.0.0`
Date: `2026-06-05`

## Purpose

This package is a production-grade skill for deriving, hardening, auditing, porting, evaluating, and maintaining agent constitutions and constitutional prompt frameworks.

## Contents

- `CHANGELOG.md`
- `MANIFEST.md`
- `README.md`
- `RELEASE_NOTES.md`
- `SKILL.md`
- `agents/openai.yaml`
- `assets/single-file-agent-constitution-skeleton.md`
- `assets/templates/agent-constitution-full.md`
- `assets/templates/audit-report-template.md`
- `assets/templates/capability-dispatch-table.md`
- `assets/templates/constitution-spec.example.json`
- `assets/templates/intake-form.md`
- `assets/templates/memory-policy-template.md`
- `assets/templates/platform-binding-template.md`
- `assets/templates/red-team-report-template.md`
- `assets/templates/release-checklist.md`
- `assets/templates/rewrite-plan-template.md`
- `examples/example-agent-constitution.md`
- `examples/example-audit-report.md`
- `examples/example-rewrite-plan.md`
- `examples/rendered-from-spec.md`
- `package-manifest.json`
- `references/00-doc-chain.md`
- `references/01-constitutional-prompt-theory.md`
- `references/02-derivation-guide.md`
- `references/03-layer-contracts.md`
- `references/04-authority-and-governance.md`
- `references/05-rules-of-engagement-patterns.md`
- `references/06-operating-doctrine-library.md`
- `references/07-persona-architecture.md`
- `references/08-capability-dispatch.md`
- `references/09-memory-continuity.md`
- `references/10-platform-binding-matrix.md`
- `references/11-security-privacy-safety.md`
- `references/12-long-context-and-compaction.md`
- `references/13-domain-ingestion-and-knowledge-modeling.md`
- `references/14-output-contracts.md`
- `references/15-audit-checklist.md`
- `references/16-evaluation-rubric.md`
- `references/17-red-team-suite.md`
- `references/18-anti-patterns.md`
- `references/19-rewrite-playbook.md`
- `references/20-deployment-and-maintenance.md`
- `references/21-interoperability-notes.md`
- `references/22-glossary.md`
- `references/23-schema-driven-authoring.md`
- `references/24-failure-mode-atlas.md`
- `schemas/audit-report.schema.json`
- `schemas/constitution-spec.schema.json`
- `schemas/skill-package.schema.json`
- `scripts/_cpf_common.py`
- `scripts/constitution_linter.py`
- `scripts/render_constitution_from_spec.py`
- `scripts/run_static_evals.py`
- `scripts/score_constitution.py`
- `scripts/validate_skill_package.py`
- `tests/README.md`
- `tests/eval_cases.yaml`
- `tests/fixtures/minimal_constitution_spec.json`

## Validation expectation

From the package root:

```bash
python scripts/validate_skill_package.py .
python scripts/constitution_linter.py examples/example-agent-constitution.md
python scripts/score_constitution.py examples/example-agent-constitution.md
python scripts/run_static_evals.py tests/eval_cases.yaml
python scripts/render_constitution_from_spec.py tests/fixtures/minimal_constitution_spec.json -o /tmp/rendered-constitution.md
```

The scripts are deterministic helper checks. They confirm structure, signals, and fixtures, but do not replace expert review.
