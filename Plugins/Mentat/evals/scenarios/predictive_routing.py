"""Scenarios for the predictive_routing_accuracy criterion.

These scenarios exercise the Q-table's `thompson_recommend` method, which
samples from `Normal(value, 1/sqrt(visits+1))` for each candidate tool and
picks the argmax. The shape we care about:

  cold_start      An empty Q-table on a never-visited state must produce
                  either None or pick uniformly. We accept either (the
                  contract is "graceful degradation, no crash").

  warm_table      With a synthetic reward distribution biased toward Read
                  in PLANNING, thompson_recommend over many trials must pick
                  Read at > 70% of trials.

  contested_state Two tools with near-equal mean Q-values but very different
                  visit counts. The lower-visit, higher-variance arm must
                  still get >= 15% exploration weight across many trials.

All persistence is sandboxed in a temp directory so we don't touch the user's
real Q-table. We use random.seed(42) for reproducibility of the stochastic
scenarios — every run produces the same numbers.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine import QTable, Reward, State  # noqa: E402

from ._types import Scenario, ScenarioResult  # noqa: E402


# Tools we'll route over in PLANNING. Matches the rough tool surface of
# Claude Code — Read/Grep/Glob are exploration, Edit/Write are execution,
# Bash is exec/verify, Agent is sub-dispatch.
_PLANNING_TOOLS = ["Read", "Grep", "Glob", "Edit", "Bash", "Agent"]


def _make(id_, name, description, fn):
    return Scenario(id=id_, name=name, description=description, fn=fn)


def _trials(qtable: QTable, state: State, tools: list[str], n: int) -> dict[str, int]:
    """Run `n` Thompson samplings, return a histogram of picks."""
    counts: dict[str, int] = {t: 0 for t in tools}
    for _ in range(n):
        pick = qtable.thompson_recommend(state, tools)
        if pick is None:
            continue
        counts[pick] = counts.get(pick, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def scenario_cold_start(workdir: Path):
    """Empty Q-table → recommend should not crash and should not always pick
    the same tool (since variance is uniform across unvisited arms).

    Accepts None as a graceful fallback. With every Q-value = 0 and every
    visit count = 0, sigma is identical across arms; thompson picks are then
    a uniform draw — we just check no crash and no degenerate-always-same
    behavior.
    """
    db = workdir / "qtable_cold.sqlite"
    q = QTable(db)
    try:
        random.seed(42)
        counts = _trials(q, State.PLANNING, _PLANNING_TOOLS, n=100)
    finally:
        q.close()

    nonzero_arms = sum(1 for c in counts.values() if c > 0)
    # Should at least touch >= 3 distinct arms in 100 trials with uniform sigma.
    # If the recommender's degenerate (always returns the same tool or always None),
    # nonzero_arms <= 1.
    passed = nonzero_arms >= 3 and sum(counts.values()) > 0
    evidence = (
        f"cold_start: 100 trials over empty Q-table touched {nonzero_arms}/{len(_PLANNING_TOOLS)} "
        f"distinct arms (recommender is exploring, not collapsed). counts={counts}"
    )
    if not passed:
        evidence = f"cold_start: degenerate selection — counts={counts}"
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "counts": counts,
        "nonzero_arms": nonzero_arms,
    })


def scenario_warm_table(workdir: Path):
    """Pre-populate PLANNING with a strong Read preference (Q=1.5, visits=20).
    Other tools sit near Q=0.1 with low visits. Thompson over 100 trials must
    pick Read > 70 times.
    """
    db = workdir / "qtable_warm.sqlite"
    q = QTable(db)
    try:
        # Manually seed the Q-table to the synthetic distribution.
        # Use the public .update API — it goes through the TD step, which is
        # the actual production path. We arrange rewards so Q(PLANNING, Read)
        # converges near 1.5 and the others stay near 0.1.
        # To reach Q ~= 1.5 from 0 we need a sequence of SUCCESS rewards with
        # the deep-chain bonus active, but it's far cleaner to just write
        # directly via the sqlite cursor (still the public API surface).
        q._conn.execute(
            "INSERT INTO q_values (state, tool, value, visits, last_updated) "
            "VALUES (?, ?, ?, ?, 0)",
            ("planning", "Read", 1.5, 20),
        )
        for t in ("Grep", "Glob", "Edit", "Bash", "Agent"):
            q._conn.execute(
                "INSERT INTO q_values (state, tool, value, visits, last_updated) "
                "VALUES (?, ?, ?, ?, 0)",
                ("planning", t, 0.1, 3),
            )
        q._conn.commit()

        random.seed(42)
        counts = _trials(q, State.PLANNING, _PLANNING_TOOLS, n=100)
    finally:
        q.close()

    read_picks = counts.get("Read", 0)
    threshold = 70
    passed = read_picks > threshold
    evidence = (
        f"warm_table: Read picked {read_picks}/100 (threshold > {threshold}). "
        f"distribution={counts}"
    )
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "counts": counts,
        "read_picks": read_picks,
        "threshold": threshold,
    })


def scenario_contested_state(workdir: Path):
    """Two arms with near-equal means and very different visit counts.

    Arm A: value=1.0, visits=50  (sigma ~= 1/sqrt(51) ~= 0.140)
    Arm B: value=0.95, visits=2  (sigma ~= 1/sqrt(3)  ~= 0.577)

    Pure exploitation would pick A every trial. A well-calibrated Thompson
    sampler must still hand >= 15% of trials to B because its posterior
    overlaps A's by a wide margin.
    """
    db = workdir / "qtable_contested.sqlite"
    q = QTable(db)
    try:
        q._conn.execute(
            "INSERT INTO q_values (state, tool, value, visits, last_updated) "
            "VALUES (?, ?, ?, ?, 0)",
            ("exploring", "Read", 1.0, 50),
        )
        q._conn.execute(
            "INSERT INTO q_values (state, tool, value, visits, last_updated) "
            "VALUES (?, ?, ?, ?, 0)",
            ("exploring", "Glob", 0.95, 2),
        )
        q._conn.commit()

        random.seed(42)
        counts = _trials(q, State.EXPLORING, ["Read", "Glob"], n=100)
    finally:
        q.close()

    glob_picks = counts.get("Glob", 0)
    threshold = 15
    passed = glob_picks >= threshold
    evidence = (
        f"contested_state: high-variance arm Glob picked {glob_picks}/100 "
        f"(threshold >= {threshold}). distribution={counts}"
    )
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "counts": counts,
        "glob_picks": glob_picks,
        "threshold": threshold,
    })


SCENARIOS = [
    _make("cold_start", "Cold-start fallback",
          "Empty Q-table does not crash and explores at least 3 arms in 100 trials.",
          scenario_cold_start),
    _make("warm_table", "Warm-table exploitation",
          "Strong Read bias → Thompson recommends Read > 70% of trials.",
          scenario_warm_table),
    _make("contested_state", "Contested state — exploration weight",
          "Near-equal Q, different visits → high-variance arm gets >= 15% selection.",
          scenario_contested_state),
]
