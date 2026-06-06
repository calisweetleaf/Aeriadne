"""Mentat eval rig — skill-creator-style scoring harness for the state machine.

This package grades the Mentat state machine, predictive router, and persistence
layer against the rubric defined in `rubric.json`. It does not modify or import
any user state outside of `tempfile.TemporaryDirectory` workspaces.

Top-level entry points:

    from evals.harness import Harness, Report
    from evals.scenarios import REGISTRY

Operator-facing CLI is at `scripts/run_eval.py`. See `README.md` for usage.
"""
from .harness import Harness, Report, CriterionScore, ScenarioOutcome, grade

__all__ = ["Harness", "Report", "CriterionScore", "ScenarioOutcome", "grade"]
