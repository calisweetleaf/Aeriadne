"""Scenario data types — extracted into a small leaf module so scenario
modules can import them without bringing in the package facade and creating
a circular import.

The package facade `evals/scenarios/__init__.py` re-exports these names so
external callers can still do `from evals.scenarios import Scenario, ScenarioResult`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class ScenarioResult:
    """Outcome of a single scenario.

    passed       True if the scenario assertion held.
    evidence     One-line human-readable summary, suitable for the report.
    details      Free-form structured payload (intermediate states, sampled
                 distributions, byte-by-byte diff outputs) for deep debugging.
    """
    passed: bool
    evidence: str
    details: dict = field(default_factory=dict)


@dataclass
class Scenario:
    """A single named test case bound to a criterion."""
    id: str
    name: str
    description: str
    fn: Callable[[Path], ScenarioResult]


__all__ = ["Scenario", "ScenarioResult"]
