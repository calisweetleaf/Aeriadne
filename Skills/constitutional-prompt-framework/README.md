# Constitutional Prompt Framework v10

This skill package turns agent prompt design into an engineering discipline. It is built for deriving, hardening, auditing, porting, and maintaining dense single-file agent constitutions and reusable prompt frameworks.

A constitution is not a role prompt with extra adjectives. It is a layered operating document that defines mission, authority, rules of engagement, doctrine, persona, capabilities, memory, output contracts, evaluation, and maintenance.

## Package goals

- Produce complete single-file agent constitutions from loose notes or existing prompts.
- Refactor brittle prompts into coherent layered systems.
- Audit prompts with severity rankings, scorecards, and red-team probes.
- Port prompts across ChatGPT, Codex, Claude, Copilot, Cursor, IDE agents, local CLIs, API agents, and custom orchestrators without lying about capabilities.
- Preserve private doctrine while stripping platform leakage when portability is requested.
- Provide deterministic scripts for package validation, constitution linting, rubric scoring, and static evals.

## File map

- `SKILL.md`: the entrypoint the agent loads after skill invocation.
- `agents/openai.yaml`: OpenAI-facing interface metadata.
- `references/`: chained doctrine library.
- `assets/templates/`: copyable prompt, audit, rewrite, and deployment templates.
- `examples/`: example outputs and miniature fixtures.
- `tests/`: static eval probes, fixtures, and acceptance gates.
- `schemas/`: machine-readable contracts for specs, audit reports, and package manifests.
- `scripts/`: deterministic helper tools, including spec rendering.
- `CHANGELOG.md`: version history.
- `MANIFEST.md`: package contents and validation notes.

## Recommended use

Invoke the skill with the raw prompt, target agent idea, or task description. For maximal output, ask for design note, constitution, audit score, and red-team probes in one pass.

Example:

```text
Use $constitutional-prompt-framework to rewrite the attached agent prompt as a production-grade platform-agnostic constitution. Preserve the mission, strip platform leakage, add authority rules, capability dispatch, memory policy, output contracts, audit score, and red-team probes.
```

## Local validation

From the package root:

```bash
python scripts/validate_skill_package.py .
python scripts/constitution_linter.py examples/example-agent-constitution.md
python scripts/score_constitution.py examples/example-agent-constitution.md
python scripts/run_static_evals.py tests/eval_cases.yaml
python scripts/render_constitution_from_spec.py tests/fixtures/minimal_constitution_spec.json -o /tmp/rendered-constitution.md
```

These scripts use the Python standard library only.

## Design philosophy

The framework optimizes for coherent behavior under stress. It assumes that most prompt drift comes from layer incoherence, not missing slogans. The fix is to make each layer do one job, then force every layer to reinforce the others.

The result should read like a flight manual for cognition: clear enough to execute, strict enough to survive stress, and modular enough to maintain.
