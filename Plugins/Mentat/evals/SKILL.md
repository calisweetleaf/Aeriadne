---
name: mentat-eval
description: |
  Run the Mentat state-machine evaluation harness against the v0.2 codebase.
  Scores the plugin on three rubrics — state-transition correctness, predictive-routing
  accuracy, and persistence-recovery integrity — and emits a self-contained HTML
  report at evals/output/report.html plus a structured JSON report.
when_to_use: |
  Trigger phrases: "run mentat evals", "score mentat", "test mentat", "evaluate
  mentat", "grade mentat", "regression-check mentat", "is mentat working",
  "did the FSA regress". Fire automatically before merging a Mentat patch that
  touches state_machine/*, before publishing a release, and after upgrading
  Claude Code (the hook contract drift surface).
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/evals/scripts/run_eval.py*)"
---

You are about to grade the Mentat state machine against three rubrics. The
harness is deterministic for state-transition and persistence scenarios, and
stochastic for predictive-routing (which uses Thompson sampling). For
stochastic criteria, run the benchmark aggregator if you need a confidence
interval; for spot-checks, a single run is enough.

Procedure:

1. Run the full eval rig.

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/evals/scripts/run_eval.py --rubric all
   ```

   This produces two files under `${CLAUDE_PLUGIN_ROOT}/evals/output/`:
   - `report.json` — structured per-scenario evidence + aggregate score
   - `report.html` — self-contained, browser-renderable visual report

2. Read the JSON report. Surface to the operator:
   - The aggregate weighted score (0.0 — 1.0)
   - Per-criterion 0..5 grades
   - Any scenarios that failed, with their evidence string

3. If the aggregate score regressed vs. a prior run, dispatch the
   `mentat-eval-comparator` sub-agent against the two `benchmark.json` files
   to surface which criterion drifted.

4. If predictive-routing failed and the operator wants a stability check,
   run the multi-run benchmark:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/evals/scripts/aggregate_benchmark.py --runs 10
   ```

   This writes `benchmark.json` + `benchmark.html` under `evals/output/`.

The harness is stdlib-only Python ≥ 3.10. It uses `tempfile.TemporaryDirectory`
for all persistence side effects — it will NOT touch the operator's real
`~/.mentat/` data. Safe to run in production.

The rubric is defined in `${CLAUDE_PLUGIN_ROOT}/evals/rubric.json`. Adding a
new scenario is documented in `${CLAUDE_PLUGIN_ROOT}/evals/references/schemas.md`.
