#!/usr/bin/env python3
"""CLI front door for the Mentat eval harness.

Usage:

  python3 scripts/run_eval.py --rubric all
  python3 scripts/run_eval.py --rubric state_transition_correctness --json
  python3 scripts/run_eval.py --rubric all --output /tmp/mentat-report.html

Always writes:

  ${CLAUDE_PLUGIN_ROOT}/evals/output/report.json
  ${CLAUDE_PLUGIN_ROOT}/evals/output/report.html (or --output path)

Exit codes:
  0  harness ran end-to-end (scenarios may have failed — the report shows it)
  2  bad CLI invocation
  3  harness itself crashed (uncaught exception outside scenario try/except)
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path


# Resolve the evals package whether we're invoked as a script or via -m.
_HERE = Path(__file__).resolve().parent
_EVALS_ROOT = _HERE.parent
_PLUGIN_ROOT = _EVALS_ROOT.parent
for p in (_PLUGIN_ROOT, _EVALS_ROOT.parent):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from evals.harness import Harness, Report  # noqa: E402
from evals.scripts.generate_report import render_html  # noqa: E402


_RUBRIC_PATH_DEFAULT = _EVALS_ROOT / "rubric.json"
_OUTPUT_DIR_DEFAULT = _EVALS_ROOT / "output"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mentat-eval",
        description="Run the Mentat state-machine eval rig.",
    )
    p.add_argument(
        "--rubric",
        choices=[
            "all",
            "state_transition_correctness",
            "state_transitions",
            "predictive_routing_accuracy",
            "predictive_routing",
            "persistence_recovery_integrity",
            "persistence_recovery",
        ],
        default="all",
        help="Run a single criterion or all criteria. Short names (state_transitions, "
             "predictive_routing, persistence_recovery) are aliases.",
    )
    p.add_argument(
        "--rubric-file",
        type=Path,
        default=_RUBRIC_PATH_DEFAULT,
        help=f"Path to rubric.json (default: {_RUBRIC_PATH_DEFAULT})",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"HTML output path (default: {_OUTPUT_DIR_DEFAULT}/report.html)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Also emit the JSON report to stdout.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable summary on stdout.",
    )
    return p.parse_args()


_ALIAS = {
    "state_transitions": "state_transition_correctness",
    "predictive_routing": "predictive_routing_accuracy",
    "persistence_recovery": "persistence_recovery_integrity",
}


def main() -> int:
    args = _parse_args()
    rubric_path: Path = args.rubric_file
    if not rubric_path.exists():
        print(f"rubric file not found: {rubric_path}", file=sys.stderr)
        return 2

    filter_criterion: str | None = args.rubric
    if filter_criterion in _ALIAS:
        filter_criterion = _ALIAS[filter_criterion]
    if filter_criterion == "all":
        filter_criterion = None

    output_dir: Path = (args.output.parent if args.output else _OUTPUT_DIR_DEFAULT)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path: Path = args.output if args.output else (output_dir / "report.html")
    json_path: Path = output_dir / "report.json"

    try:
        harness = Harness(rubric_path)
        report = harness.run(filter_criterion=filter_criterion)
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc(file=sys.stderr)
        return 3

    _write_outputs(report, html_path=html_path, json_path=json_path)

    if not args.quiet:
        _print_summary(report, html_path=html_path, json_path=json_path)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))

    return 0


def _write_outputs(report: Report, html_path: Path, json_path: Path) -> None:
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    html_path.write_text(render_html(report), encoding="utf-8")


def _print_summary(report: Report, html_path: Path, json_path: Path) -> None:
    print("=" * 72)
    print(f"Mentat eval rig — {report.rubric_name} v{report.rubric_version}")
    print(f"timestamp: {report.timestamp}    runtime: {report.duration_ms:.1f} ms")
    print("=" * 72)
    for c in report.criterion_scores:
        verdict = "PASS" if c.raw_score >= 3 else "FAIL"
        print(
            f"  [{verdict}] {c.name:42s} "
            f"{c.raw_score}/5  "
            f"({c.pass_count}/{c.scenario_count} pass)  "
            f"weight={c.weight:.2f}  contrib={c.weighted_contribution:.3f}"
        )
    print("-" * 72)
    verdict = "PASS" if report.passed_aggregate else "FAIL"
    print(
        f"  aggregate: {report.aggregate_score:.3f} / 1.000   "
        f"threshold: {report.pass_threshold:.2f}   verdict: {verdict}"
    )
    print("-" * 72)
    print(f"  report.json: {json_path}")
    print(f"  report.html: {html_path}")
    print("=" * 72)


if __name__ == "__main__":
    raise SystemExit(main())
