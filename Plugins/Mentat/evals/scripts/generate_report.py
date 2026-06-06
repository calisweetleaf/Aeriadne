"""HTML renderer for the eval `Report` dataclass.

Renders a self-contained HTML document with:

  - dark canvas / surface palette
  - brand gradient (#3b82f6 → #8b5cf6) on headers + score bars
  - Inter for body text, JetBrains Mono for evidence/code, Orbitron for
    rubric title chrome
  - terminal-style chrome for failure logs
  - criterion cards with per-scenario evidence
  - no external assets except Google Fonts

The output is portable: drag into a browser and it renders. No JS required —
all charts and visuals are CSS / inline SVG.
"""
from __future__ import annotations

import html
import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evals.harness import CriterionScore, Report, ScenarioOutcome


_BRAND_GRADIENT = "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)"
_FONTS = (
    "https://fonts.googleapis.com/css2"
    "?family=Inter:wght@400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500;700"
    "&family=Orbitron:wght@500;700&display=swap"
)


_STYLES = """
:root {
  --bg-0: #07080d;
  --bg-1: #0d111c;
  --bg-2: #141a2b;
  --surface: rgba(255, 255, 255, 0.03);
  --surface-strong: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.09);
  --border-strong: rgba(255, 255, 255, 0.18);
  --text-0: #f5f6fb;
  --text-1: #c4c8d4;
  --text-2: #8189a0;
  --text-3: #545b73;
  --accent-blue: #3b82f6;
  --accent-violet: #8b5cf6;
  --accent-green: #34d399;
  --accent-red: #f87171;
  --accent-amber: #fbbf24;
  --grad-brand: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  --grad-pass: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  --grad-fail: linear-gradient(135deg, #b91c1c 0%, #f87171 100%);
  --shadow-card: 0 1px 0 rgba(255,255,255,0.04) inset,
                 0 20px 50px -20px rgba(0,0,0,0.7);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  background:
    radial-gradient(at 20% -10%, rgba(59,130,246,0.10), transparent 50%),
    radial-gradient(at 80% 110%, rgba(139,92,246,0.10), transparent 50%),
    var(--bg-0);
  color: var(--text-0);
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

main {
  max-width: 1160px;
  margin: 0 auto;
  padding: 56px 32px 80px;
}

/* ---------- Header ---------- */
.header {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 36px 40px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
  box-shadow: var(--shadow-card);
  margin-bottom: 36px;
  position: relative;
  overflow: hidden;
}

.header::before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--grad-brand);
  opacity: 0.08;
  pointer-events: none;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.title {
  font-family: "Orbitron", "Inter", sans-serif;
  font-weight: 700;
  font-size: 24px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: var(--grad-brand);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: var(--text-2);
  font-size: 13px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 500;
}

/* Aggregate verdict block */
.verdict {
  display: flex;
  align-items: center;
  gap: 32px;
  margin-top: 12px;
  padding: 24px 28px;
  border-radius: 14px;
  border: 1px solid var(--border-strong);
  background: var(--bg-1);
}

.score-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.score-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }

.score-ring .track {
  fill: none;
  stroke: rgba(255,255,255,0.08);
  stroke-width: 12;
}

.score-ring .progress {
  fill: none;
  stroke-width: 12;
  stroke-linecap: round;
  stroke: url(#brandGradient);
}

.score-ring .label {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.score-ring .label .value {
  font-family: "JetBrains Mono", monospace;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-0);
}

.score-ring .label .of {
  color: var(--text-2);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.verdict-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.verdict-label {
  font-family: "Orbitron", "Inter", sans-serif;
  font-weight: 700;
  font-size: 28px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.verdict-label.pass { color: var(--accent-green); }
.verdict-label.fail { color: var(--accent-red); }

.verdict-meta {
  color: var(--text-2);
  font-size: 13px;
  font-family: "JetBrains Mono", monospace;
}

/* ---------- Criterion cards ---------- */
.criteria {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.criterion {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--bg-1);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.criterion-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 28px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.criterion-head-left h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-0);
  margin-bottom: 4px;
}

.criterion-head-left .id {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-2);
  letter-spacing: 0.04em;
}

.criterion-grade {
  display: flex;
  align-items: center;
  gap: 16px;
  font-family: "JetBrains Mono", monospace;
}

.grade-pill {
  padding: 6px 14px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid transparent;
}

.grade-pill.g-5 { background: rgba(52, 211, 153, 0.18); color: var(--accent-green); border-color: rgba(52,211,153,0.4); }
.grade-pill.g-4 { background: rgba(96, 165, 250, 0.18); color: #93c5fd; border-color: rgba(96,165,250,0.4); }
.grade-pill.g-3 { background: rgba(251, 191, 36, 0.18); color: var(--accent-amber); border-color: rgba(251,191,36,0.4); }
.grade-pill.g-2 { background: rgba(251, 146, 60, 0.18); color: #fb923c; border-color: rgba(251,146,60,0.4); }
.grade-pill.g-1 { background: rgba(248, 113, 113, 0.18); color: var(--accent-red); border-color: rgba(248,113,113,0.4); }
.grade-pill.g-0 { background: rgba(248, 113, 113, 0.28); color: var(--accent-red); border-color: rgba(248,113,113,0.5); }

.criterion-meta {
  font-size: 12px;
  color: var(--text-2);
  letter-spacing: 0.04em;
}

.criterion-body { padding: 24px 28px; }

.criterion-description {
  color: var(--text-1);
  font-size: 14px;
  margin-bottom: 20px;
  line-height: 1.6;
}

.score-bar-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}

.score-bar-track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  background: var(--grad-brand);
  border-radius: 999px;
}

.score-bar-label {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  color: var(--text-2);
  min-width: 90px;
  text-align: right;
}

/* ---------- Scenario rows ---------- */
.scenarios {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-2);
  padding: 14px 18px;
  display: grid;
  grid-template-columns: 84px 1fr auto;
  gap: 18px;
  align-items: start;
}

.scenario.pass { border-left: 3px solid var(--accent-green); }
.scenario.fail { border-left: 3px solid var(--accent-red); }

.scenario-mark {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  padding: 5px 10px;
  border-radius: 6px;
  text-align: center;
  width: 64px;
}

.scenario-mark.pass {
  background: rgba(52, 211, 153, 0.12);
  color: var(--accent-green);
}
.scenario-mark.fail {
  background: rgba(248, 113, 113, 0.16);
  color: var(--accent-red);
}

.scenario-body { min-width: 0; }

.scenario-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-0);
  margin-bottom: 4px;
}

.scenario-id {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-2);
  margin-bottom: 8px;
}

.scenario-evidence {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  color: var(--text-1);
  background: var(--bg-0);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
}

.scenario.fail .scenario-evidence {
  border-color: rgba(248, 113, 113, 0.25);
  background:
    linear-gradient(180deg, rgba(248,113,113,0.04), transparent 50%),
    var(--bg-0);
}

.scenario-duration {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-3);
  white-space: nowrap;
}

/* Terminal chrome for failure tracebacks */
.terminal {
  margin-top: 10px;
  background: #050608;
  border: 1px solid rgba(248, 113, 113, 0.4);
  border-radius: 8px;
  overflow: hidden;
}

.terminal-chrome {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border-bottom: 1px solid var(--border);
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-2);
  letter-spacing: 0.08em;
}

.terminal-dots {
  display: flex;
  gap: 6px;
}
.terminal-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--bg-2);
}
.terminal-dot:nth-child(1) { background: #f87171; }
.terminal-dot:nth-child(2) { background: #fbbf24; }
.terminal-dot:nth-child(3) { background: #34d399; }

.terminal-body {
  padding: 14px 16px;
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  color: #f87171;
  white-space: pre-wrap;
  line-height: 1.5;
  max-height: 240px;
  overflow: auto;
}

/* ---------- Footer ---------- */
.footer {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  flex-wrap: wrap;
  gap: 12px;
}

/* Print-friendly */
@media print {
  body { background: white; color: black; }
  .scenario, .criterion { break-inside: avoid; }
}
"""


def render_html(report: "Report") -> str:
    """Render the full report as a self-contained HTML document."""
    ratio = max(0.0, min(1.0, report.aggregate_score))
    progress_deg = ratio * 360.0
    circumference = 2 * 3.14159265 * 50
    progress_offset = circumference * (1 - ratio)
    verdict_class = "pass" if report.passed_aggregate else "fail"
    verdict_text = "PASS" if report.passed_aggregate else "FAIL"

    criteria_html = "\n".join(_render_criterion(c) for c in report.criterion_scores)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Mentat eval report — {html.escape(report.timestamp)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{_FONTS}">
<style>{_STYLES}</style>
</head>
<body>
<svg width="0" height="0" style="position: absolute">
  <defs>
    <linearGradient id="brandGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#8b5cf6" />
    </linearGradient>
  </defs>
</svg>
<main>
  <section class="header">
    <div class="header-row">
      <div>
        <div class="subtitle">Mentat v0.2 — state machine eval rig</div>
        <h1 class="title">{html.escape(report.rubric_name)}</h1>
      </div>
      <div class="subtitle" style="text-align: right">
        <div>rubric v{html.escape(report.rubric_version)}</div>
        <div>{html.escape(report.timestamp)}</div>
        <div>runtime {report.duration_ms:.1f} ms</div>
      </div>
    </div>
    <div class="verdict">
      <div class="score-ring">
        <svg viewBox="0 0 120 120">
          <circle class="track" cx="60" cy="60" r="50" />
          <circle class="progress" cx="60" cy="60" r="50"
                  stroke-dasharray="{circumference:.2f}"
                  stroke-dashoffset="{progress_offset:.2f}" />
        </svg>
        <div class="label">
          <span class="value">{report.aggregate_score:.2f}</span>
          <span class="of">/ 1.00</span>
        </div>
      </div>
      <div class="verdict-detail">
        <div class="verdict-label {verdict_class}">{verdict_text}</div>
        <div class="verdict-meta">
          aggregate threshold: {report.pass_threshold:.2f}
        </div>
        <div class="verdict-meta">
          weighted aggregate = Σ(weight × score / 5)
        </div>
        <div class="verdict-meta">
          {len(report.scenarios)} scenarios across {len(report.criterion_scores)} criteria
        </div>
      </div>
    </div>
  </section>
  <section class="criteria">
    {criteria_html}
  </section>
  <footer class="footer">
    <div>Mentat eval rig — {html.escape(report.rubric_name)} v{html.escape(report.rubric_version)}</div>
    <div>generated {html.escape(report.timestamp)}</div>
  </footer>
</main>
</body>
</html>
"""


def _render_criterion(c: "CriterionScore") -> str:
    grade_class = f"g-{c.raw_score}"
    bar_fill_pct = (c.raw_score / 5.0) * 100.0
    scen_html = "\n".join(_render_scenario(s) for s in c.scenarios)
    return f"""
<div class="criterion">
  <div class="criterion-head">
    <div class="criterion-head-left">
      <h3>{html.escape(c.name)}</h3>
      <div class="id">{html.escape(c.id)}</div>
    </div>
    <div class="criterion-grade">
      <span class="grade-pill {grade_class}">{c.raw_score} / 5</span>
      <span class="criterion-meta">{c.pass_count}/{c.scenario_count} pass · weight {c.weight:.2f} · contrib {c.weighted_contribution:.3f}</span>
    </div>
  </div>
  <div class="criterion-body">
    <p class="criterion-description">{html.escape(c.description)}</p>
    <div class="score-bar-row">
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width: {bar_fill_pct:.1f}%"></div>
      </div>
      <div class="score-bar-label">{c.raw_score}/5 ({bar_fill_pct:.0f}%)</div>
    </div>
    <div class="scenarios">
      {scen_html}
    </div>
  </div>
</div>
"""


def _render_scenario(s: "ScenarioOutcome") -> str:
    cls = "pass" if s.passed else "fail"
    mark_label = "PASS" if s.passed else "FAIL"
    evidence_html = html.escape(s.evidence)
    tb = ""
    if not s.passed and isinstance(s.details, dict):
        traceback_str = s.details.get("traceback")
        if traceback_str:
            tb = f"""
        <div class="terminal">
          <div class="terminal-chrome">
            <div class="terminal-dots">
              <span class="terminal-dot"></span>
              <span class="terminal-dot"></span>
              <span class="terminal-dot"></span>
            </div>
            <span>scenario traceback</span>
          </div>
          <pre class="terminal-body">{html.escape(traceback_str)}</pre>
        </div>"""
    return f"""
<div class="scenario {cls}">
  <div class="scenario-mark {cls}">{mark_label}</div>
  <div class="scenario-body">
    <div class="scenario-name">{html.escape(s.scenario_name)}</div>
    <div class="scenario-id">{html.escape(s.scenario_id)} · criterion {html.escape(s.criterion_id)}</div>
    <div class="scenario-evidence">{evidence_html}</div>{tb}
  </div>
  <div class="scenario-duration">{s.duration_ms:.1f} ms</div>
</div>
"""


__all__ = ["render_html"]
