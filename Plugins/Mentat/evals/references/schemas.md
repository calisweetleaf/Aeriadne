# Mentat eval rig — schemas reference

This document captures the data shapes consumed and produced by the
evaluation harness. Anyone adding a new criterion, scenario, or report
consumer should start here.

## `rubric.json`

Top-level schema:

```jsonc
{
  "version": "0.2.0",                          // semver string
  "name": "mentat-state-machine-rubric",       // short rubric id
  "description": "...",                        // human-readable summary
  "criteria": [<Criterion>, ...],              // 1+ criterion blocks
  "aggregate_formula": "sum(weight * (score / 5)) over criteria",
  "pass_threshold": 0.7                        // float in [0, 1]
}
```

`Criterion` block:

```jsonc
{
  "id": "state_transition_correctness",        // slug, also a Python identifier
  "name": "State-Transition Correctness",      // titlecase, for the report
  "description": "...",                        // paragraph; rendered into card
  "weight": 0.4,                               // float; weights MUST sum to 1.0
  "scoring_guide": {                           // 0..5 ladder, all keys required
    "0": "...",
    "1": "...",
    "2": "...",
    "3": "...",
    "4": "...",
    "5": "..."
  },
  "scenarios": ["boot", "write_loop", ...]    // ids that must exist in the registry
}
```

## Scenario function contract

A scenario is a callable:

```python
def scenario_<id>(workdir: pathlib.Path) -> ScenarioResult:
    ...
```

- **workdir** is a per-scenario `tempfile.TemporaryDirectory` path. Any
  filesystem side effects MUST be confined to this directory. If your
  scenario imports the state-machine session module, set
  `os.environ["MENTAT_HOME"] = str(workdir)` for the duration of the
  scenario and restore the prior value in a `finally`.

- **return value** is a `ScenarioResult` from `evals.scenarios`:

  ```python
  @dataclass
  class ScenarioResult:
      passed: bool        # the assertion that the scenario tested
      evidence: str       # one or more lines, human-readable
      details: dict       # structured payload for deep debugging
  ```

  The harness catches uncaught exceptions and reports them as a failed
  scenario with `details["traceback"]` populated. Do not catch your own
  unexpected exceptions inside a scenario unless you have a reason to —
  the harness wraps the call.

To register a new scenario:

1. Add the scenario function to one of the modules in
   `evals/scenarios/`.
2. Append a `Scenario(...)` entry to that module's `SCENARIOS` list.
3. Add the scenario's `id` to the appropriate criterion's `scenarios`
   array in `rubric.json`.

The registry auto-loads on import. If two scenarios share an id, the
registry raises at import time — pick a unique slug.

## Report dataclass shape

`evals.harness.Report` is the structured object the harness returns.
JSON-serialized via `dataclasses.asdict`, it looks like:

```jsonc
{
  "rubric_name": "mentat-state-machine-rubric",
  "rubric_version": "0.2.0",
  "timestamp": "2026-05-10T18:00:00Z",
  "aggregate_score": 0.823,
  "pass_threshold": 0.7,
  "passed_aggregate": true,
  "duration_ms": 142.7,
  "markdown_summary": "...",
  "criterion_scores": [
    {
      "id": "state_transition_correctness",
      "name": "State-Transition Correctness",
      "description": "...",
      "weight": 0.4,
      "raw_score": 5,
      "pass_count": 5,
      "scenario_count": 5,
      "scenarios": [<ScenarioOutcome>, ...]
    }
  ],
  "scenarios": [<ScenarioOutcome>, ...]   // flat copy of all scenarios
}
```

`ScenarioOutcome`:

```jsonc
{
  "criterion_id": "state_transition_correctness",
  "scenario_id": "boot",
  "scenario_name": "Boot",
  "description": "SESSION_START on a fresh FSA lands in PLANNING.",
  "passed": true,
  "evidence": "...",
  "error": null,
  "duration_ms": 1.2,
  "details": { /* free-form */ }
}
```

## Scoring rule

`grade(pass_count, total)` maps to the 0..5 ladder declared in
`scoring_guide`:

| pass_count vs total | grade |
|---|---|
| 0 of any total | 0 |
| total - 1 = 1 fail | 4 |
| total - 2 = 2 fails | 3 |
| pass_count >= total / 2 | 2 |
| pass_count = total | 5 |
| else | 1 |

Aggregate score is then `sum(weight * grade / 5)` across all criteria.

## `benchmark.json`

Multi-run output from `scripts/aggregate_benchmark.py`:

```jsonc
{
  "metadata": {
    "rubric_name": "...",
    "rubric_version": "0.2.0",
    "runs": 10,
    "timestamp": "2026-05-10T18:00:00Z",
    "total_duration_ms": 1480.2,
    "pass_threshold": 0.7
  },
  "aggregate_score": {"mean": 0.823, "stddev": 0.014, "min": 0.81, "max": 0.85, "n": 10},
  "criteria": [
    {
      "id": "predictive_routing_accuracy",
      "name": "...",
      "weight": 0.3,
      "scenario_count": 3,
      "raw_score_stats": {"mean": 4.2, "stddev": 0.42, "min": 4, "max": 5, "n": 10},
      "pass_count_stats": {"mean": 2.6, "stddev": 0.49, "min": 2, "max": 3, "n": 10},
      "scenario_flake": {
        "cold_start":     {"pass_rate": 1.0, "flake": false, "history": [true, true, ...]},
        "warm_table":     {"pass_rate": 1.0, "flake": false, "history": [...]},
        "contested_state":{"pass_rate": 0.6, "flake": true,  "history": [true, false, ...]}
      }
    }
  ],
  "per_run": [
    { "i": 0, "aggregate_score": 0.83, "passed_aggregate": true,
      "criterion_scores": [{"id": "...", "raw_score": 5, "pass_count": 5}, ...] }
  ]
}
```

A scenario is `flake = true` when its `history` contains both pass and
fail outcomes across the N runs. Stable scenarios show `flake = false`
regardless of whether they all-passed or all-failed (consistency is
not the same as correctness — read the `pass_rate`).
