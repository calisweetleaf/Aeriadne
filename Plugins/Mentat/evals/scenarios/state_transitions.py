"""Scenarios for the state_transition_correctness criterion.

Each scenario constructs an `Event` sequence, drives a fresh `StateMachine`
through it, and asserts that:

  - the final state matches `expected_state`,
  - the ordered trace of states matches `expected_transitions`.

The FSA is deterministic, so these are exact equality checks. A scenario fails
loudly with a diff-style evidence string so the operator can spot which
transition broke.

These scenarios import the AUTHORITATIVE state_machine package from
plugin/state_machine/. Do not duplicate the transition table here — that would
mask the very regressions we're trying to catch.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Resolve the plugin root so we can import the state machine package without
# needing to be invoked as a package member ourselves.
_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine import Event, EventClass, State, StateMachine  # noqa: E402


# Scenario / ScenarioResult come from the leaf `_types` module so importing
# this file at package-import time doesn't recurse through the package facade.
from ._types import Scenario, ScenarioResult  # noqa: E402


def _make(id_, name, description, fn):
    return Scenario(id=id_, name=name, description=description, fn=fn)


@dataclass
class _Trace:
    """Result of replaying an event list through a fresh FSA."""
    final: State
    states: list[State]
    transitions: int


def _replay(events: list[Event], initial: State = State.PLANNING) -> _Trace:
    sm = StateMachine(state=initial)
    states: list[State] = [sm.state]
    for ev in events:
        _, nxt, _ = sm.step(ev)
        states.append(nxt)
    return _Trace(final=sm.state, states=states, transitions=sm.transition_count)


def _diff_trace(expected: list[State], actual: list[State]) -> str:
    """Render a human-readable diff between expected and actual trace."""
    pairs = []
    for i, (e, a) in enumerate(zip(expected, actual)):
        marker = "==" if e is a else "!="
        pairs.append(f"  [{i}] expected={e.value:<10} {marker} actual={a.value}")
    if len(actual) > len(expected):
        for i in range(len(expected), len(actual)):
            pairs.append(f"  [{i}] (no expected)   != actual={actual[i].value}")
    elif len(expected) > len(actual):
        for i in range(len(actual), len(expected)):
            pairs.append(f"  [{i}] expected={expected[i].value:<10} != (no actual)")
    return "\n".join(pairs)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def scenario_boot(_workdir: Path):
    """SESSION_START → expects PLANNING."""
    events = [Event(event_class=EventClass.SESSION_START)]
    trace = _replay(events, initial=State.PLANNING)

    expected_states = [State.PLANNING, State.PLANNING]
    expected_final = State.PLANNING

    passed = trace.states == expected_states and trace.final is expected_final
    if passed:
        evidence = f"boot: SESSION_START kept FSA in PLANNING (1 step, {trace.transitions} transitions)"
    else:
        evidence = (
            f"boot: expected final={expected_final.value}, got={trace.final.value}\n"
            + _diff_trace(expected_states, trace.states)
        )
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "expected_final": expected_final.value,
        "actual_final": trace.final.value,
        "trace": [s.value for s in trace.states],
    })


def scenario_write_loop(_workdir: Path):
    """PROMPT_SUBMIT → READ_TOOL → WRITE_TOOL → EXEC_TOOL → VERIFY_TOOL → TOOL_SUCCESS.

    Expected trace (starting from PLANNING):
      PLANNING, PLANNING (prompt), EXPLORING (read), EXECUTING (write),
      EXECUTING (exec), VERIFYING (verify), REFLECTING (success).
    """
    events = [
        Event(event_class=EventClass.PROMPT_SUBMIT),
        Event(event_class=EventClass.READ_TOOL, tool_name="Read"),
        Event(event_class=EventClass.WRITE_TOOL, tool_name="Edit"),
        Event(event_class=EventClass.EXEC_TOOL, tool_name="Bash", payload={"command": "ls"}),
        Event(event_class=EventClass.VERIFY_TOOL, tool_name="Bash", payload={"command": "pytest"}),
        Event(event_class=EventClass.TOOL_SUCCESS),
    ]
    trace = _replay(events, initial=State.PLANNING)

    expected_states = [
        State.PLANNING,    # initial
        State.PLANNING,    # PROMPT_SUBMIT (PLANNING + PROMPT_SUBMIT → PLANNING)
        State.EXPLORING,   # READ_TOOL
        State.EXECUTING,   # WRITE_TOOL
        State.EXECUTING,   # EXEC_TOOL (still executing)
        State.VERIFYING,   # VERIFY_TOOL
        State.REFLECTING,  # TOOL_SUCCESS
    ]
    expected_final = State.REFLECTING

    passed = trace.states == expected_states and trace.final is expected_final
    if passed:
        evidence = (
            f"write_loop: traversed {len(events)} events, ended in REFLECTING "
            f"({trace.transitions} transitions)"
        )
    else:
        evidence = (
            f"write_loop: expected final={expected_final.value}, got={trace.final.value}\n"
            + _diff_trace(expected_states, trace.states)
        )
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "expected_final": expected_final.value,
        "actual_final": trace.final.value,
        "trace": [s.value for s in trace.states],
    })


def scenario_verify_loop(_workdir: Path):
    """VERIFYING → TOOL_ERROR (→ EXECUTING) → VERIFY_TOOL → TOOL_SUCCESS (→ REFLECTING).

    Models the test-fails-then-fix loop. Start from VERIFYING directly because
    in production we'd already be there after an exec; we only care that the
    error → retry → success cycle is well-formed.
    """
    events = [
        Event(event_class=EventClass.TOOL_ERROR),
        Event(event_class=EventClass.VERIFY_TOOL, tool_name="Bash",
              payload={"command": "pytest"}),
        Event(event_class=EventClass.TOOL_SUCCESS),
    ]
    trace = _replay(events, initial=State.VERIFYING)

    expected_states = [
        State.VERIFYING,   # initial
        State.EXECUTING,   # TOOL_ERROR → drop to executing (fix loop)
        State.VERIFYING,   # VERIFY_TOOL → re-verifying
        State.REFLECTING,  # TOOL_SUCCESS → reflecting
    ]
    expected_final = State.REFLECTING

    passed = trace.states == expected_states and trace.final is expected_final
    if passed:
        evidence = (
            "verify_loop: VERIFYING-error-retry-success cycled cleanly back to REFLECTING"
        )
    else:
        evidence = (
            f"verify_loop: expected final={expected_final.value}, got={trace.final.value}\n"
            + _diff_trace(expected_states, trace.states)
        )
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "expected_final": expected_final.value,
        "actual_final": trace.final.value,
        "trace": [s.value for s in trace.states],
    })


def scenario_drift_recovery(_workdir: Path):
    """any state + SCOPE_DRIFT_DETECTED → DRIFTING; PROMPT_SUBMIT → PLANNING.

    Verifies the drift override for several initial states.
    """
    initials = [State.PLANNING, State.EXPLORING, State.EXECUTING, State.VERIFYING,
                State.REFLECTING, State.BLOCKED]
    failures: list[str] = []
    for initial in initials:
        trace = _replay(
            [
                Event(event_class=EventClass.SCOPE_DRIFT_DETECTED),
                Event(event_class=EventClass.PROMPT_SUBMIT),
            ],
            initial=initial,
        )
        expected_states = [initial, State.DRIFTING, State.PLANNING]
        if trace.states != expected_states or trace.final is not State.PLANNING:
            failures.append(
                f"  from {initial.value}: got {[s.value for s in trace.states]}"
            )

    passed = not failures
    if passed:
        evidence = (
            f"drift_recovery: SCOPE_DRIFT_DETECTED → DRIFTING → PROMPT_SUBMIT → "
            f"PLANNING held for all {len(initials)} initial states"
        )
    else:
        evidence = "drift_recovery: failures:\n" + "\n".join(failures)
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "tested_initials": [s.value for s in initials],
        "failure_count": len(failures),
    })


def scenario_compact_resume(_workdir: Path):
    """any state + PRE_COMPACT → COMPACTING; POST_COMPACT → REFLECTING."""
    initials = [State.PLANNING, State.EXPLORING, State.EXECUTING, State.VERIFYING,
                State.REFLECTING, State.BLOCKED, State.DRIFTING]
    failures: list[str] = []
    for initial in initials:
        trace = _replay(
            [
                Event(event_class=EventClass.PRE_COMPACT),
                Event(event_class=EventClass.POST_COMPACT),
            ],
            initial=initial,
        )
        expected_states = [initial, State.COMPACTING, State.REFLECTING]
        if trace.states != expected_states or trace.final is not State.REFLECTING:
            failures.append(
                f"  from {initial.value}: got {[s.value for s in trace.states]}"
            )

    passed = not failures
    if passed:
        evidence = (
            f"compact_resume: PRE_COMPACT → COMPACTING → POST_COMPACT → "
            f"REFLECTING held for all {len(initials)} initial states"
        )
    else:
        evidence = "compact_resume: failures:\n" + "\n".join(failures)
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "tested_initials": [s.value for s in initials],
        "failure_count": len(failures),
    })


SCENARIOS = [
    _make("boot", "Boot",
          "SESSION_START on a fresh FSA lands in PLANNING.",
          scenario_boot),
    _make("write_loop", "Plan → Read → Write → Exec → Verify → Reflect",
          "End-to-end happy-path write loop through the FSA.",
          scenario_write_loop),
    _make("verify_loop", "Verify-fail retry cycle",
          "VERIFYING + TOOL_ERROR drops to EXECUTING then re-verifies on next VERIFY_TOOL.",
          scenario_verify_loop),
    _make("drift_recovery", "Scope-drift universal override",
          "SCOPE_DRIFT_DETECTED forces DRIFTING from any state; PROMPT_SUBMIT returns to PLANNING.",
          scenario_drift_recovery),
    _make("compact_resume", "Compaction handoff",
          "PRE_COMPACT → COMPACTING from any state; POST_COMPACT lands in REFLECTING.",
          scenario_compact_resume),
]
