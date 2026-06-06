"""Scenario registry for the Mentat eval harness.

Each scenario module exports a `SCENARIOS` list of `Scenario` instances.
The harness imports `REGISTRY` from this package and dispatches by id.

A scenario is a pure callable taking a `tempfile.TemporaryDirectory` path and
returning a `ScenarioResult`. The harness wraps the call in try/except so a
crash inside one scenario never breaks the whole run.

`Scenario` and `ScenarioResult` live in `_types.py` to avoid circular
imports — scenario modules import from `_types` while still being importable
from the package facade.
"""
from __future__ import annotations

from ._types import Scenario, ScenarioResult
from . import persistence_recovery, predictive_routing, state_transitions


REGISTRY: dict[str, Scenario] = {}


def _register(module) -> None:
    for s in module.SCENARIOS:
        if s.id in REGISTRY:
            raise RuntimeError(f"duplicate scenario id: {s.id}")
        REGISTRY[s.id] = s


_register(state_transitions)
_register(predictive_routing)
_register(persistence_recovery)


__all__ = ["Scenario", "ScenarioResult", "REGISTRY"]
