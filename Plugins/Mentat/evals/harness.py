"""Grading runner for the Mentat eval rig.

A `Harness` reads `rubric.json`, dispatches each criterion's scenarios through
the registry, scores 0..5 by pass count, and rolls up the weighted aggregate.

Public surface:

  Harness(rubric_path).run(filter_criterion=None) -> Report

  Report is a dataclass with:
    .aggregate_score        float in [0, 1]
    .criterion_scores       list[CriterionScore]
    .scenarios              list[ScenarioOutcome]  (flat, all)
    .timestamp              ISO 8601 string
    .markdown_summary       human-readable digest

The harness creates ONE `tempfile.TemporaryDirectory` per scenario and passes
the path in. Scenarios that touch the filesystem must respect that workdir.
Nothing under ~/.mentat is ever written to.
"""
from __future__ import annotations

import json
import tempfile
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .scenarios import REGISTRY, Scenario, ScenarioResult


# ---------------------------------------------------------------------------
# Data classes for structured reporting
# ---------------------------------------------------------------------------


@dataclass
class ScenarioOutcome:
    criterion_id: str
    scenario_id: str
    scenario_name: str
    description: str
    passed: bool
    evidence: str
    error: Optional[str] = None
    duration_ms: float = 0.0
    details: dict = field(default_factory=dict)


@dataclass
class CriterionScore:
    id: str
    name: str
    description: str
    weight: float
    raw_score: int               # 0..5 discrete grade
    pass_count: int
    scenario_count: int
    scenarios: list[ScenarioOutcome]

    @property
    def normalized(self) -> float:
        return self.raw_score / 5.0

    @property
    def weighted_contribution(self) -> float:
        return self.weight * self.normalized


@dataclass
class Report:
    """Complete grading output for one harness run."""
    rubric_name: str
    rubric_version: str
    timestamp: str
    aggregate_score: float
    pass_threshold: float
    passed_aggregate: bool
    criterion_scores: list[CriterionScore]
    scenarios: list[ScenarioOutcome]
    duration_ms: float
    markdown_summary: str

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Scoring rule
# ---------------------------------------------------------------------------


def grade(pass_count: int, total: int) -> int:
    """Convert pass_count / total into the 0..5 discrete grade.

    5 = all pass
    4 = exactly one fail
    3 = exactly two fails
    2 = at most half pass (but more than zero)
    1 = exactly one passes (only when total > 4 — otherwise this collapses into 2)
    0 = none pass

    The rubric spec calls for an explicit ladder that's easy to explain to
    a human reader. We codify it here so it's tested-against, not implicit.
    """
    if total <= 0:
        return 0
    if pass_count == 0:
        return 0
    if pass_count == total:
        return 5
    fails = total - pass_count
    if fails == 1:
        return 4
    if fails == 2:
        return 3
    # Past this point we're judging "half pass" vs "most fail".
    half = total / 2.0
    if pass_count >= half:
        return 2
    return 1


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class Harness:
    """Top-level eval runner. Holds the rubric and dispatches scenarios."""

    def __init__(self, rubric_path: Path):
        self.rubric_path = rubric_path
        self.rubric = json.loads(rubric_path.read_text(encoding="utf-8"))

    def run(self, filter_criterion: Optional[str] = None) -> Report:
        """Execute every scenario in every criterion (or just one criterion).

        filter_criterion may be:
          - None or "all"  → run everything
          - a criterion id ("state_transition_correctness" etc.) → only that one
        """
        t0 = time.perf_counter()
        criteria_scores: list[CriterionScore] = []
        flat_scenarios: list[ScenarioOutcome] = []

        for crit in self.rubric["criteria"]:
            if filter_criterion not in (None, "all", crit["id"]):
                continue
            outcomes: list[ScenarioOutcome] = []
            for scen_id in crit["scenarios"]:
                scen = REGISTRY.get(scen_id)
                if scen is None:
                    outcomes.append(ScenarioOutcome(
                        criterion_id=crit["id"],
                        scenario_id=scen_id,
                        scenario_name=scen_id,
                        description="",
                        passed=False,
                        evidence=f"scenario id not found in registry: {scen_id}",
                        error="missing_scenario",
                    ))
                    continue
                outcome = self._run_one(crit["id"], scen)
                outcomes.append(outcome)

            pass_count = sum(1 for o in outcomes if o.passed)
            raw = grade(pass_count, len(outcomes))
            criteria_scores.append(CriterionScore(
                id=crit["id"],
                name=crit["name"],
                description=crit["description"],
                weight=crit["weight"],
                raw_score=raw,
                pass_count=pass_count,
                scenario_count=len(outcomes),
                scenarios=outcomes,
            ))
            flat_scenarios.extend(outcomes)

        aggregate = sum(c.weighted_contribution for c in criteria_scores)
        threshold = float(self.rubric.get("pass_threshold", 0.7))
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        duration_ms = (time.perf_counter() - t0) * 1000.0

        report = Report(
            rubric_name=self.rubric.get("name", "mentat-rubric"),
            rubric_version=self.rubric.get("version", "0.0.0"),
            timestamp=ts,
            aggregate_score=round(aggregate, 4),
            pass_threshold=threshold,
            passed_aggregate=aggregate >= threshold,
            criterion_scores=criteria_scores,
            scenarios=flat_scenarios,
            duration_ms=round(duration_ms, 2),
            markdown_summary="",  # filled below
        )
        report.markdown_summary = _render_markdown(report)
        return report

    def _run_one(self, criterion_id: str, scen: Scenario) -> ScenarioOutcome:
        start = time.perf_counter()
        try:
            with tempfile.TemporaryDirectory(prefix="mentat-eval-") as tmp:
                workdir = Path(tmp)
                result: ScenarioResult = scen.fn(workdir)
            err = None
        except Exception as exc:  # pylint: disable=broad-except
            result = ScenarioResult(
                passed=False,
                evidence=f"scenario raised {type(exc).__name__}: {exc}",
                details={"traceback": traceback.format_exc()},
            )
            err = f"{type(exc).__name__}: {exc}"
        dur = (time.perf_counter() - start) * 1000.0
        return ScenarioOutcome(
            criterion_id=criterion_id,
            scenario_id=scen.id,
            scenario_name=scen.name,
            description=scen.description,
            passed=result.passed,
            evidence=result.evidence,
            error=err,
            duration_ms=round(dur, 2),
            details=result.details,
        )


# ---------------------------------------------------------------------------
# Markdown summary renderer
# ---------------------------------------------------------------------------


def _render_markdown(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"# Mentat eval report — {report.timestamp}")
    lines.append("")
    verdict = "PASS" if report.passed_aggregate else "FAIL"
    lines.append(
        f"**Aggregate:** {report.aggregate_score:.3f} / 1.000 "
        f"(threshold {report.pass_threshold:.2f}) — **{verdict}**"
    )
    lines.append(f"**Rubric:** `{report.rubric_name}` v{report.rubric_version}")
    lines.append(f"**Duration:** {report.duration_ms:.1f} ms")
    lines.append("")
    lines.append("## Criteria")
    lines.append("")
    for c in report.criterion_scores:
        lines.append(
            f"### {c.name} — {c.raw_score}/5 "
            f"({c.pass_count}/{c.scenario_count} scenarios) "
            f"weight={c.weight:.2f} contribution={c.weighted_contribution:.3f}"
        )
        lines.append("")
        for s in c.scenarios:
            mark = "PASS" if s.passed else "FAIL"
            lines.append(f"- **{mark}** `{s.scenario_id}` — {s.evidence}")
        lines.append("")
    return "\n".join(lines)


__all__ = ["Harness", "Report", "CriterionScore", "ScenarioOutcome", "grade"]
