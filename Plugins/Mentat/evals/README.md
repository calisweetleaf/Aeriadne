# Mentat eval rig

A skill-creator-style scoring harness for the Mentat state machine. Three
rubrics, eleven scenarios, one self-contained HTML report.

The rig is the equivalent of a CI pre-merge check for the cognitive
substrate: it does not lint code, it grades behavior. It exists because
Mentat's correctness is non-obvious — a regression in the transition table
or the Thompson sampler is silent until a session goes sideways days later.

## What it grades

| Criterion                              | Weight | Scenarios |
|----------------------------------------|--------|-----------|
| state_transition_correctness           | 0.40   | 5 |
| predictive_routing_accuracy            | 0.30   | 3 |
| persistence_recovery_integrity         | 0.30   | 3 |

The aggregate score is `Σ(weight · raw_score / 5)`. Pass threshold is 0.70.

## How to run

```bash
# full run (writes evals/output/report.html + report.json)
python3 evals/scripts/run_eval.py --rubric all

# single criterion
python3 evals/scripts/run_eval.py --rubric predictive_routing

# stochastic stability check (10 runs, aggregates variance)
python3 evals/scripts/aggregate_benchmark.py --runs 10

# also dump JSON to stdout
python3 evals/scripts/run_eval.py --rubric all --json
```

Exit codes: `0` on harness success (scenarios may still have failed —
read the report). `2` on bad CLI invocation. `3` on harness crash.

The rig is stdlib-only Python ≥ 3.10. No `pytest`. No third-party deps.

## Output

`evals/output/report.html`
:   Self-contained dark-canvas HTML. Drag into a browser.

`evals/output/report.json`
:   Structured `Report` dataclass, JSON-serialized. Consumed by the
    `mentat-eval-grader` sub-agent.

`evals/output/benchmark.json` (from `aggregate_benchmark.py`)
:   Multi-run statistics. Consumed by `mentat-eval-comparator` for
    before/after diffs.

`evals/output/benchmark.html`
:   Visual stability report. Per-scenario `PFPFPP` history strings make
    flake patterns obvious.

## Interpreting scores

Each criterion is graded on a 0..5 ladder:

| Grade | Meaning |
|-------|---------|
| 5     | All scenarios pass — on-spec. |
| 4     | One scenario fails — localized regression. |
| 3     | Two fail — one systematic break. |
| 2     | At least half pass — broad damage. |
| 1     | Most fail — severe regression. |
| 0     | None pass — feature broken or import-broken. |

A passing aggregate (>= 0.70) means the plugin is fit to ship a patch.
A failing aggregate means something material moved and you should run
`scripts/aggregate_benchmark.py` to separate flake from regression.

## Baseline expectation on v0.1

| Criterion                       | Expected |
|---------------------------------|----------|
| state_transition_correctness    | 5/5      |
| predictive_routing_accuracy     | 4–5/5    |
| persistence_recovery_integrity  | 5/5      |

`predictive_routing_accuracy` is stochastic — a single bad seed in
`contested_state` can drop it to 4/5. Run the benchmark with `--runs 25`
to confirm.

## Adding a scenario

1. Pick a criterion. The three scenario modules under `scenarios/` map
   1-1 to the three criteria.
2. Write a `scenario_<id>(workdir) -> ScenarioResult` function. Follow
   the contract in `references/schemas.md`. Confine all I/O to
   `workdir`.
3. Append a `Scenario(...)` entry to that module's `SCENARIOS` list.
4. Add the scenario id to the criterion block in `rubric.json`.

The registry auto-discovers it on next import. The harness will pick it
up immediately — no other registration needed.

## Safety

The harness uses `tempfile.TemporaryDirectory` for every scenario. It
overrides `MENTAT_HOME` so the state machine's persistence layer writes
into the sandbox. It does **not** touch `~/.mentat/` or any of the
operator's actual session state. Safe to run in production.

## Authoring an eval that imports state_machine

The state_machine package lives at `plugin/state_machine/`. The
scenarios under `evals/scenarios/` add the plugin root to `sys.path`
on import so `from state_machine import ...` works whether you run the
script directly or import it as a module. Don't copy the transition
table or reward constants — import them from the source of truth.

## Sub-agents

- `agents/grader.md` — reads `report.json` and writes a one-paragraph
  qualitative assessment with named risks.
- `agents/comparator.md` — diffs two `benchmark.json` files and surfaces
  which criterion regressed.

Both are dispatched manually (not auto-wired) so the harness stays a
hermetic Python program with no model dependency.

## Layout

```
evals/
├── SKILL.md                  trigger phrases and procedure
├── README.md                 this file
├── rubric.json               criteria, weights, scoring guides, scenario lists
├── .gitignore                excludes output/
├── __init__.py               package facade exposing Harness, Report
├── harness.py                grading runner with scoring rule
├── scenarios/
│   ├── __init__.py           registry — auto-imports every scenario module
│   ├── state_transitions.py
│   ├── predictive_routing.py
│   └── persistence_recovery.py
├── scripts/
│   ├── __init__.py
│   ├── run_eval.py           single-run CLI
│   ├── aggregate_benchmark.py  N-run CLI with variance
│   └── generate_report.py    HTML renderer
├── agents/
│   ├── grader.md             qualitative paragraph writer
│   └── comparator.md         before-vs-after diff writer
├── references/
│   └── schemas.md            data shapes + scenario contract
└── output/                   gitignored — reports land here
```
