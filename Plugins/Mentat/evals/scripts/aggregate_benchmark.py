#!/usr/bin/env python3
"""Multi-run benchmarking for the Mentat eval rig.

Stochastic criteria (predictive_routing_accuracy) have natural run-to-run
variance from the Thompson sampler. A single run can give a misleading score
either way — passing by luck or failing on a tail draw. This script runs the
harness N times and aggregates:

  - mean / stddev / min / max of the aggregate score
  - per-criterion mean / stddev of raw_score
  - flake rate per scenario (fraction of runs that flipped pass↔fail)

Outputs `evals/output/benchmark.json` and `evals/output/benchmark.html`.

Usage:

  python3 scripts/aggregate_benchmark.py --runs 10
  python3 scripts/aggregate_benchmark.py --runs 25 --rubric predictive_routing
"""
from __future__ import annotations

import argparse
import html
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_HERE = Path(__file__).resolve().parent
_EVALS_ROOT = _HERE.parent
_PLUGIN_ROOT = _EVALS_ROOT.parent
for p in (_PLUGIN_ROOT, _EVALS_ROOT.parent):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from evals.harness import Harness, Report  # noqa: E402


_RUBRIC_PATH_DEFAULT = _EVALS_ROOT / "rubric.json"
_OUTPUT_DIR_DEFAULT = _EVALS_ROOT / "output"

_ALIAS = {
    "state_transitions": "state_transition_correctness",
    "predictive_routing": "predictive_routing_accuracy",
    "persistence_recovery": "persistence_recovery_integrity",
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mentat-eval-benchmark",
        description="Run the Mentat eval harness N times and aggregate variance.",
    )
    p.add_argument("--runs", type=int, default=10,
                   help="Number of harness invocations (default: 10).")
    p.add_argument("--rubric", default="all",
                   help="Filter criterion (alias supported: state_transitions, "
                        "predictive_routing, persistence_recovery).")
    p.add_argument("--rubric-file", type=Path, default=_RUBRIC_PATH_DEFAULT,
                   help=f"Path to rubric.json (default: {_RUBRIC_PATH_DEFAULT})")
    p.add_argument("--output-dir", type=Path, default=_OUTPUT_DIR_DEFAULT,
                   help="Directory for benchmark.json + benchmark.html.")
    p.add_argument("--quiet", action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    rubric_path: Path = args.rubric_file
    if not rubric_path.exists():
        print(f"rubric file not found: {rubric_path}", file=sys.stderr)
        return 2

    filter_criterion: Optional[str] = args.rubric
    if filter_criterion in _ALIAS:
        filter_criterion = _ALIAS[filter_criterion]
    if filter_criterion == "all":
        filter_criterion = None

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    runs: int = max(1, args.runs)
    t0 = time.perf_counter()
    reports: list[Report] = []
    harness = Harness(rubric_path)
    for i in range(runs):
        report = harness.run(filter_criterion=filter_criterion)
        reports.append(report)
        if not args.quiet:
            print(
                f"  run {i+1:>2}/{runs} — aggregate={report.aggregate_score:.3f}  "
                f"{('PASS' if report.passed_aggregate else 'FAIL')}",
                file=sys.stderr,
            )
    duration_ms = (time.perf_counter() - t0) * 1000.0

    bench = _build_benchmark(reports, runs=runs, duration_ms=duration_ms)

    (output_dir / "benchmark.json").write_text(
        json.dumps(bench, indent=2), encoding="utf-8"
    )
    (output_dir / "benchmark.html").write_text(
        _render_html(bench), encoding="utf-8"
    )

    if not args.quiet:
        _print_summary(bench, output_dir)
    return 0


def _build_benchmark(reports: list[Report], *, runs: int, duration_ms: float) -> dict:
    agg_scores = [r.aggregate_score for r in reports]
    crit_ids: list[str] = []
    crit_meta: dict[str, dict] = {}
    for c in reports[0].criterion_scores:
        crit_ids.append(c.id)
        crit_meta[c.id] = {
            "name": c.name,
            "weight": c.weight,
            "raw_scores": [],
            "pass_counts": [],
            "scenario_count": c.scenario_count,
            "scenario_pass_history": {s.scenario_id: [] for s in c.scenarios},
        }

    for r in reports:
        for c in r.criterion_scores:
            crit_meta[c.id]["raw_scores"].append(c.raw_score)
            crit_meta[c.id]["pass_counts"].append(c.pass_count)
            for s in c.scenarios:
                hist = crit_meta[c.id]["scenario_pass_history"]
                hist[s.scenario_id].append(bool(s.passed))

    criterion_summary = []
    for cid in crit_ids:
        m = crit_meta[cid]
        raw = m["raw_scores"]
        scen_flake = {}
        for sid, hist in m["scenario_pass_history"].items():
            pass_rate = sum(1 for v in hist if v) / max(1, len(hist))
            unique = set(hist)
            flake = pass_rate if (len(unique) > 1) else 0.0  # 0.0 if stable
            scen_flake[sid] = {
                "pass_rate": round(pass_rate, 3),
                "flake": len(unique) > 1,
                "history": hist,
            }
        criterion_summary.append({
            "id": cid,
            "name": m["name"],
            "weight": m["weight"],
            "scenario_count": m["scenario_count"],
            "raw_score_stats": _stats(raw),
            "pass_count_stats": _stats(m["pass_counts"]),
            "scenario_flake": scen_flake,
        })

    return {
        "metadata": {
            "rubric_name": reports[0].rubric_name,
            "rubric_version": reports[0].rubric_version,
            "runs": runs,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_duration_ms": round(duration_ms, 2),
            "pass_threshold": reports[0].pass_threshold,
        },
        "aggregate_score": _stats(agg_scores),
        "criteria": criterion_summary,
        "per_run": [
            {
                "i": i,
                "aggregate_score": r.aggregate_score,
                "passed_aggregate": r.passed_aggregate,
                "criterion_scores": [
                    {"id": c.id, "raw_score": c.raw_score, "pass_count": c.pass_count}
                    for c in r.criterion_scores
                ],
            }
            for i, r in enumerate(reports)
        ],
    }


def _stats(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "n": 0}
    n = len(values)
    mean = sum(values) / n
    sd = statistics.stdev(values) if n > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(sd, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "n": n,
    }


def _print_summary(bench: dict, output_dir: Path) -> None:
    print("=" * 72)
    print(
        f"Mentat eval rig — benchmark ({bench['metadata']['runs']} runs, "
        f"{bench['metadata']['total_duration_ms']:.0f} ms total)"
    )
    print("=" * 72)
    a = bench["aggregate_score"]
    print(
        f"  aggregate score : mean={a['mean']:.3f}  stddev={a['stddev']:.3f}  "
        f"min={a['min']:.3f}  max={a['max']:.3f}"
    )
    for c in bench["criteria"]:
        s = c["raw_score_stats"]
        flaky = [sid for sid, info in c["scenario_flake"].items() if info["flake"]]
        flake_str = f" flaky=[{', '.join(flaky)}]" if flaky else ""
        print(
            f"  {c['name']:42s} mean={s['mean']:.2f}/5  σ={s['stddev']:.2f}"
            f"{flake_str}"
        )
    print("-" * 72)
    print(f"  benchmark.json: {output_dir / 'benchmark.json'}")
    print(f"  benchmark.html: {output_dir / 'benchmark.html'}")
    print("=" * 72)


_STYLES_BENCH = """
:root {
  --bg-0: #07080d;
  --bg-1: #0d111c;
  --bg-2: #141a2b;
  --text-0: #f5f6fb;
  --text-1: #c4c8d4;
  --text-2: #8189a0;
  --text-3: #545b73;
  --border: rgba(255,255,255,0.09);
  --accent-green: #34d399;
  --accent-red: #f87171;
  --accent-amber: #fbbf24;
  --grad-brand: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  background:
    radial-gradient(at 20% -10%, rgba(59,130,246,0.10), transparent 50%),
    radial-gradient(at 80% 110%, rgba(139,92,246,0.10), transparent 50%),
    var(--bg-0);
  color: var(--text-0);
  font-family: "Inter", sans-serif;
  font-size: 15px;
  line-height: 1.55;
  min-height: 100vh;
}
main { max-width: 1160px; margin: 0 auto; padding: 56px 32px; }
.header {
  padding: 36px 40px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
  margin-bottom: 36px;
}
.title {
  font-family: "Orbitron", "Inter", sans-serif;
  font-weight: 700; font-size: 24px;
  letter-spacing: 0.06em; text-transform: uppercase;
  background: var(--grad-brand);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}
.subtitle { color: var(--text-2); font-size: 13px; letter-spacing: 0.04em; text-transform: uppercase; }
.aggregate-card {
  margin-top: 24px;
  padding: 24px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 14px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}
.stat-tile {
  display: flex; flex-direction: column; gap: 4px;
}
.stat-tile .lbl {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-2);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.stat-tile .val {
  font-family: "JetBrains Mono", monospace;
  font-size: 26px;
  font-weight: 700;
}
.criterion {
  margin-bottom: 24px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}
.criterion-head {
  padding: 18px 24px;
  border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.criterion-head h3 { font-size: 16px; font-weight: 600; }
.criterion-stats {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  color: var(--text-2);
}
.criterion-body { padding: 16px 24px; }
.scenario-flake {
  display: grid;
  grid-template-columns: 1fr 100px 100px;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
}
.scenario-flake:last-child { border-bottom: none; }
.flake-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.flake-badge.stable { background: rgba(52,211,153,0.18); color: var(--accent-green); }
.flake-badge.flaky  { background: rgba(251,191,36,0.18); color: var(--accent-amber); }
.history { color: var(--text-1); letter-spacing: 0.15em; }
"""


def _render_html(bench: dict) -> str:
    meta = bench["metadata"]
    agg = bench["aggregate_score"]
    crit_blocks = []
    for c in bench["criteria"]:
        s = c["raw_score_stats"]
        rows = []
        for sid, info in c["scenario_flake"].items():
            badge = "flaky" if info["flake"] else "stable"
            history = "".join("P" if v else "F" for v in info["history"])
            rows.append(
                f"<div class='scenario-flake'>"
                f"<div>{html.escape(sid)}</div>"
                f"<div class='history'>{html.escape(history)}</div>"
                f"<div><span class='flake-badge {badge}'>{badge}</span></div>"
                f"</div>"
            )
        crit_blocks.append(f"""
<div class="criterion">
  <div class="criterion-head">
    <h3>{html.escape(c['name'])}</h3>
    <div class="criterion-stats">
      mean={s['mean']:.2f}/5  σ={s['stddev']:.2f}  min={s['min']}  max={s['max']}
    </div>
  </div>
  <div class="criterion-body">
    <div class="scenario-flake" style="font-weight: 600; color: var(--text-2)">
      <div>scenario</div><div>history</div><div>stability</div>
    </div>
    {''.join(rows)}
  </div>
</div>
""")

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mentat eval benchmark — {html.escape(meta['timestamp'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Orbitron:wght@500;700&display=swap">
<style>{_STYLES_BENCH}</style>
</head><body>
<main>
  <section class="header">
    <div class="subtitle">Mentat v0.2 — multi-run benchmark</div>
    <h1 class="title">{html.escape(meta['rubric_name'])}</h1>
    <div class="subtitle">rubric v{html.escape(meta['rubric_version'])} · {meta['runs']} runs · total {meta['total_duration_ms']:.0f} ms · {html.escape(meta['timestamp'])}</div>
    <div class="aggregate-card">
      <div class="stat-tile">
        <span class="lbl">aggregate mean</span>
        <span class="val">{agg['mean']:.3f}</span>
      </div>
      <div class="stat-tile">
        <span class="lbl">stddev</span>
        <span class="val">{agg['stddev']:.3f}</span>
      </div>
      <div class="stat-tile">
        <span class="lbl">min / max</span>
        <span class="val">{agg['min']:.3f} / {agg['max']:.3f}</span>
      </div>
      <div class="stat-tile">
        <span class="lbl">threshold</span>
        <span class="val">{meta['pass_threshold']:.2f}</span>
      </div>
    </div>
  </section>
  {''.join(crit_blocks)}
</main></body></html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
