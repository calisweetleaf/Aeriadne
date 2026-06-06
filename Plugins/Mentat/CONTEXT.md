# Repository Context: Mentat

This document tracks the codebase topology, components, and development standards.

## Codebase Topology
- **`plugin/`**: The core Mentat plugin implementation.
  - **`adapters/`**: Adapters for Gemini and Codex environments.
  - **`state_machine/`**: State transition logic and predictive routing (Q-table).
  - **`monitors/`**: Session watchers for drift, entropy, and telemetry.
  - **`webhook_engine/`**: Webhook emission and dead-letter queueing.
  - **`evals/`**: Scenario harnesses and benchmarking scripts.
- **`helpers/`**: Conductor, Medic, and Quartermaster operational playbooks.
- **`style/`**: Specifications including provenance, SOTA checklist, and style sheets.

## Active Rules & Environment
- **Virtual Environment**: Run commands in the `.venv` or corresponding python environment.
- **Failure Etiquette**: Ensure all errors fail loud and write logs/telemetry to stdout/stderr.
- **Verification**: Run verify steps (e.g. scripts/smoke tests) after modifying plugin components.
- **Scope Discipline**: Respect `.mentat/scope.md` to prevent drifting.
