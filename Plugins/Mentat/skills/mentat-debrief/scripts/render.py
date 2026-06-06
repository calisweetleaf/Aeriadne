#!/usr/bin/env python3
"""Deterministic Mentat debrief renderer.

The skill (skills/mentat-debrief/SKILL.md) invokes this script. It reads the
insight bus + Q-table + session record off disk, runs the pure-function
aggregators in ``aggregate.py``, and interpolates a master HTML template via
``string.Template``. No model call, no network. Stdlib only.

Usage:
    python3 render.py --session SESSION_ID --out /tmp/mentat-debrief-<sid>.html
    python3 render.py                                 # auto-resolve session
    python3 render.py --insights-limit 1000

Resolution order for --session:
    1. CLI argument
    2. $CLAUDE_SESSION_ID
    3. ${CLAUDE_PROJECT_DIR}/.mentat/active_session.json
    4. ${MENTAT_HOME}/sessions/active.json (sentinel fallback)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import os
import sqlite3
import string
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TEMPLATE_PATH = HERE / "template.html"

# Make the package importable when run as a script.
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

try:
    from scripts import aggregate  # type: ignore
except ImportError:
    import aggregate  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# Path resolution
# ─────────────────────────────────────────────────────────────────────────────

def mentat_home() -> Path:
    """${MENTAT_HOME} with ~/.mentat fallback. Always exists after call."""
    root = Path(os.environ.get("MENTAT_HOME", Path.home() / ".mentat"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_session_id(cli: str | None) -> str | None:
    if cli:
        return cli
    env = os.environ.get("CLAUDE_SESSION_ID")
    if env:
        return env
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        p = Path(proj) / ".mentat" / "active_session.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("session_id")
            except Exception:
                pass
    # Last-ditch sentinel — handy for the smoke test.
    sentinel = mentat_home() / "sessions" / "active.json"
    if sentinel.exists():
        try:
            return json.loads(sentinel.read_text(encoding="utf-8")).get("session_id")
        except Exception:
            pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Loaders — return plain dicts/lists so the aggregators stay decoupled.
# ─────────────────────────────────────────────────────────────────────────────

def load_insights(session_id: str, limit: int) -> list[dict]:
    p = mentat_home() / "insights" / f"{session_id}.jsonl"
    if not p.exists():
        return []
    out: list[dict] = []
    with p.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except Exception:
                continue
    if limit > 0 and len(out) > limit:
        out = out[-limit:]
    return out


def load_q_table() -> list[dict]:
    """Read the global Q-table dump.

    We deliberately do not import state_machine.QTable to keep this renderer
    standalone — a direct SELECT is faster and dep-free.
    """
    db_path = mentat_home() / "q_table.sqlite"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.execute(
            "SELECT state, tool, value, visits, last_updated "
            "FROM q_values ORDER BY state, value DESC"
        )
        rows = [
            {"state": r[0], "tool": r[1], "value": float(r[2]),
             "visits": int(r[3]), "last_updated": float(r[4])}
            for r in cur.fetchall()
        ]
        conn.close()
        return rows
    except Exception:
        return []


def load_session(session_id: str) -> dict:
    p = mentat_home() / "sessions" / f"{session_id}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Synthesize a minimal session record so the renderer always has shape.
    return {
        "session_id": session_id,
        "state": "planning",
        "chain_depth": 0,
        "drift_count": 0,
        "transition_count": 0,
        "started_at": 0.0,
        "last_event_at": 0.0,
        "last_tool": None,
        "last_tool_success": None,
        "notes": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────────────────────────────────────────

def esc(s: Any) -> str:
    """HTML-escape, coercing to str. Empty input becomes empty string."""
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def pretty_duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    if seconds < 1:
        return f"{seconds:.2f}s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        m = int(seconds // 60)
        s = int(seconds - m * 60)
        return f"{m}m{s:02d}s"
    h = int(seconds // 3600)
    m = int((seconds - h * 3600) // 60)
    return f"{h}h{m:02d}m"


def short_id(sid: str, n: int = 12) -> str:
    if not sid:
        return "(no-session)"
    return sid[:n] if len(sid) > n else sid


# ─────────────────────────────────────────────────────────────────────────────
# Section builders — each returns an HTML fragment as a string.
# ─────────────────────────────────────────────────────────────────────────────

def build_state_gantt(state_time: dict) -> str:
    bars = state_time["bars"]
    max_pct = max((b["pct"] for b in bars), default=1.0) or 1.0
    rows: list[str] = []
    for b in bars:
        state = b["state"]
        width = max(0.5, 100.0 * b["pct"] / max_pct) if max_pct > 0 else 0.5
        rows.append(
            '<div class="row">'
            f'<div class="label-cell">{esc(state)}</div>'
            '<div class="bar-cell">'
            f'<div class="gbar {esc(state)}" style="width:{width:.2f}%"></div>'
            '</div>'
            f'<div class="num-cell">{pretty_duration(b["seconds"])}</div>'
            '</div>'
        )
    return "\n".join(rows)


# Fixed layout for the FSA graph — eight states in a deterministic position.
_NODE_LAYOUT = {
    "planning":   {"x": 80,  "y": 100, "grad": "sg-plan"},
    "exploring":  {"x": 360, "y": 100, "grad": "sg-explore"},
    "executing":  {"x": 560, "y": 200, "grad": "sg-exec"},
    "verifying":  {"x": 760, "y": 120, "grad": "sg-verify"},
    "reflecting": {"x": 760, "y": 340, "grad": "sg-reflect"},
    "blocked":    {"x": 360, "y": 380, "grad": "sg-block"},
    "drifting":   {"x": 660, "y": 40,  "grad": "sg-drift"},
    "compacting": {"x": 80,  "y": 380, "grad": "sg-compact"},
}


def _node_center(state: str) -> tuple[int, int]:
    n = _NODE_LAYOUT.get(state, _NODE_LAYOUT["planning"])
    return n["x"] + 50, n["y"] + 30


def build_fsa_svg(transitions: dict, session: dict) -> tuple[str, str]:
    """Return (edges_svg, nodes_svg)."""
    edges = transitions["edges"]
    visits = transitions["state_visits"]
    most_visited = transitions.get("most_visited") or session.get("state", "planning")
    max_weight = max((e["weight"] for e in edges), default=1)

    # Edges
    edge_parts: list[str] = []
    for e in edges:
        a, b = e["from"], e["to"]
        if a not in _NODE_LAYOUT or b not in _NODE_LAYOUT:
            continue
        x1, y1 = _node_center(a)
        x2, y2 = _node_center(b)
        # Pull the line toward node rectangle edge so the arrow lands cleanly.
        # Simple curve via cubic with midpoint offset.
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        sw = 1.0 + 3.5 * (e["weight"] / max_weight)
        opacity = 0.35 + 0.55 * (e["weight"] / max_weight)
        edge_parts.append(
            f'<path d="M{x1} {y1} Q {mx} {my - 18}, {x2} {y2}" '
            f'stroke="#c4b5fd" stroke-width="{sw:.2f}" fill="none" '
            f'opacity="{opacity:.2f}" marker-end="url(#ar)" />'
            f'<text x="{mx:.0f}" y="{my - 22:.0f}" text-anchor="middle" '
            f'font-family="JetBrains Mono" font-size="9" fill="#a8aec0">'
            f'{esc(e["weight"])}</text>'
        )
    edges_svg = '<g fill="none">' + "\n".join(edge_parts) + "</g>" if edge_parts else (
        '<g><text x="460" y="270" text-anchor="middle" font-family="JetBrains Mono" '
        'font-size="13" fill="#6e7588">No transitions fired this session.</text></g>'
    )

    # Nodes
    node_parts: list[str] = []
    for state, geom in _NODE_LAYOUT.items():
        x, y = geom["x"], geom["y"]
        grad = geom["grad"]
        cls = ' class="pulse-anim"' if state == most_visited else ''
        glow = ' filter="url(#glow-soft)"' if state != most_visited else ''
        v = visits.get(state, 0)
        node_parts.append(
            f'<g{cls}>'
            f'<rect x="{x}" y="{y}" width="100" height="60" rx="10" '
            f'fill="url(#{grad})"{glow}/>'
            f'<text x="{x + 50}" y="{y + 30}" text-anchor="middle" '
            f'font-family="JetBrains Mono" font-size="12" font-weight="600" fill="white">'
            f'{esc(state.upper())}</text>'
            f'<text x="{x + 50}" y="{y + 48}" text-anchor="middle" '
            f'font-family="JetBrains Mono" font-size="10" fill="rgba(255,255,255,0.78)">'
            f'visits {v}</text>'
            f'</g>'
        )
    nodes_svg = "\n".join(node_parts)
    return edges_svg, nodes_svg


def build_edge_table(transitions: dict) -> str:
    edges = transitions["edges"]
    if not edges:
        return '<tr><td colspan="3" style="text-align:center;color:#6e7588;">no edges fired</td></tr>'
    return "\n".join(
        f'<tr><td class="mono">{esc(e["from"])}</td>'
        f'<td class="mono">{esc(e["to"])}</td>'
        f'<td class="mono">{esc(e["weight"])}</td></tr>'
        for e in edges
    )


def build_q_route_blocks(rewards: dict, session: dict) -> str:
    per_state = rewards["per_state_top3"]
    if not per_state:
        return (
            '<div class="empty"><strong>No Q-table entries.</strong>'
            'The Q-table is empty for this project. Run a session that exercises tools '
            'in a few states and re-run the debrief.</div>'
        )
    last_tool = session.get("last_tool")
    blocks: list[str] = []
    for state in ("planning", "exploring", "executing", "verifying",
                  "reflecting", "blocked", "drifting", "compacting"):
        rows = per_state.get(state)
        if not rows:
            continue
        items: list[str] = []
        for r in rows:
            tag = (' <span class="badge ok">last</span>'
                   if r["tool"] == last_tool else '')
            items.append(
                '<tr>'
                f'<td class="mono">{esc(r["tool"])}</td>'
                f'<td class="mono">{r["value"]:+.3f}</td>'
                f'<td class="mono">{esc(r["visits"])}</td>'
                f'<td>{tag}</td>'
                '</tr>'
            )
        blocks.append(
            '<div class="card">'
            f'<div class="ttl">state · {esc(state)}</div>'
            f'<h3>top-3 by Q-value</h3>'
            '<table class="editorial">'
            '<thead><tr><th>Tool</th><th>Value</th><th>Visits</th><th></th></tr></thead>'
            f'<tbody>{"".join(items)}</tbody></table>'
            '</div>'
        )
    return '<div class="card-grid">' + "\n".join(blocks) + "</div>" if blocks else ""


def build_drift_table(drift: dict) -> str:
    rows = drift["rows"]
    if not rows:
        return (
            '<div class="empty"><strong>No scope-drift events.</strong>'
            'The sentinel did not flag any deferred-topic re-injection this session.</div>'
        )
    body = []
    for r in rows:
        body.append(
            '<tr>'
            f'<td class="mono">{esc(r["seq"])}</td>'
            f'<td class="mono">{esc(r["topic"])}</td>'
            f'<td>{esc(r["evidence"])}</td>'
            f'<td class="mono">{esc(r["state"])}</td>'
            '</tr>'
        )
    return (
        '<table class="editorial">'
        '<thead><tr><th>Seq</th><th>Topic</th><th>Evidence snippet</th><th>State at hit</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


def build_subagent_table(subagents: dict) -> str:
    rows = subagents["rows"]
    if not rows:
        return (
            '<div class="empty"><strong>No sub-agents dispatched.</strong>'
            'This session did not fan out to a sub-agent.</div>'
        )
    body = []
    for r in rows:
        if r["success"] is True:
            badge = '<span class="badge ok">ok</span>'
        elif r["success"] is False:
            badge = '<span class="badge crit">fail</span>'
        else:
            badge = '<span class="badge warn">open</span>'
        wt = f'{r["wall_time"]:.1f}s' if r["wall_time"] is not None else '—'
        body.append(
            '<tr>'
            f'<td>{badge}</td>'
            f'<td class="mono">{esc(r["operator"])}</td>'
            f'<td>{esc(r["objective"])}</td>'
            f'<td>{esc(r["deliverable"])}</td>'
            f'<td class="mono">{wt}</td>'
            '</tr>'
        )
    return (
        '<table class="editorial">'
        '<thead><tr><th>Status</th><th>Operator</th><th>Objective</th><th>Deliverable</th><th>Wall-time</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


def build_reward_bars(rows: list[dict], negative: bool = False) -> str:
    if not rows:
        kind = "bottom" if negative else "top"
        return (
            f'<div class="empty"><strong>No {kind} performers.</strong>'
            'The Q-table is too sparse to rank.</div>'
        )
    abs_max = max((abs(r["mean"]) for r in rows), default=1.0) or 1.0
    parts = []
    for r in rows:
        pct = min(100.0, 100.0 * abs(r["mean"]) / abs_max)
        neg_cls = " neg" if r["mean"] < 0 else ""
        parts.append(
            '<div class="spark-row">'
            f'<div class="spark-tool">{esc(r["tool"])}</div>'
            f'<div class="spark-bar{neg_cls}"><div class="spark-fill" style="width:{pct:.1f}%"></div></div>'
            f'<div class="spark-val">{r["mean"]:+.3f}</div>'
            f'<div class="spark-visits">{esc(r["visits"])}×</div>'
            '</div>'
        )
    return "\n".join(parts)


def build_grounding_block(grounding: dict) -> str:
    if grounding["total"] == 0:
        return (
            '<div class="empty"><strong>No grounding signals.</strong>'
            'No SOURCE_GROUNDED / SOURCE_UNGROUNDED insights were emitted this session.</div>'
        )
    samples = grounding["samples"]
    if not samples:
        return (
            f'<p>Score: <strong>{grounding["pct"]}%</strong> grounded '
            f'({grounding["grounded"]} grounded / {grounding["ungrounded"]} ungrounded).</p>'
        )
    rows = []
    for s in samples:
        if s["kind"] == "grounded":
            badge = '<span class="badge ok">grounded</span>'
        else:
            badge = '<span class="badge warn">ungrounded</span>'
        rows.append(
            '<tr>'
            f'<td>{badge}</td>'
            f'<td>{esc(s["claim"])}</td>'
            f'<td class="mono">{esc(s["source"])}</td>'
            '</tr>'
        )
    return (
        f'<p>Score: <strong>{grounding["pct"]}%</strong> grounded '
        f'({grounding["grounded"]} grounded / {grounding["ungrounded"]} ungrounded).</p>'
        '<table class="editorial">'
        '<thead><tr><th>Kind</th><th>Claim</th><th>Source</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def build_contradiction_block(contras: dict) -> str:
    rows = contras["rows"]
    if not rows:
        return (
            '<div class="empty"><strong>No contradictions logged.</strong>'
            'The session held a self-consistent set of claims.</div>'
        )
    body = []
    for r in rows:
        body.append(
            '<tr>'
            f'<td class="mono">{esc(r["seq"])}</td>'
            f'<td>{esc(r["a"])}</td>'
            f'<td>{esc(r["b"])}</td>'
            f'<td>{esc(r["note"])}</td>'
            '</tr>'
        )
    return (
        '<table class="editorial">'
        '<thead><tr><th>Seq</th><th>Claim A</th><th>Claim B</th><th>Note</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


def build_entropy_block(entropy: dict) -> str:
    rows = entropy["rows"]
    if not rows:
        return (
            '<div class="empty"><strong>No entropy spikes.</strong>'
            'The session stayed inside the verify-cadence threshold throughout.</div>'
        )
    body = []
    for r in rows:
        body.append(
            '<tr>'
            f'<td class="mono">{esc(r["seq"])}</td>'
            f'<td class="mono">{esc(r["state"])}</td>'
            f'<td class="mono">{esc(r["chain_depth"])}</td>'
            f'<td>{esc(r["trigger"])}</td>'
            '</tr>'
        )
    return (
        '<table class="editorial">'
        '<thead><tr><th>Seq</th><th>State at spike</th><th>Chain depth</th><th>Trigger</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


def build_tool_ledger_table(tools: dict) -> str:
    rows = tools["rows"]
    if not rows:
        return (
            '<div class="empty"><strong>No tools used.</strong>'
            'This session emitted no REWARD_SIGNAL or TOOL_FAILURE insights with a tool name.</div>'
        )
    body = []
    for r in rows:
        if r["success_rate"] >= 90:
            badge = '<span class="badge ok">healthy</span>'
        elif r["success_rate"] >= 60:
            badge = '<span class="badge warn">mixed</span>'
        elif r["count"] == 0:
            badge = '<span class="badge muted">idle</span>'
        else:
            badge = '<span class="badge crit">flaky</span>'
        body.append(
            '<tr>'
            f'<td>{badge}</td>'
            f'<td class="mono">{esc(r["tool"])}</td>'
            f'<td class="mono">{esc(r["count"])}</td>'
            f'<td class="mono">{r["success_rate"]:.1f}%</td>'
            f'<td class="mono">{r["mean_latency_ms"]:.1f} ms</td>'
            '</tr>'
        )
    return (
        '<table class="editorial">'
        '<thead><tr><th>Health</th><th>Tool</th><th>Calls</th><th>Success rate</th><th>Mean latency</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


def build_forward_cards(forward: dict) -> str:
    actions = forward["actions"]
    if not actions:
        return (
            '<div class="empty"><strong>No forward moves generated.</strong>'
            'The heuristics found no triggers and no fallbacks applied.</div>'
        )
    parts = []
    for a in actions:
        parts.append(
            '<div class="forward-card">'
            f'<span class="pill">state · {esc(a["state"])}</span>'
            f'<h3>{esc(a["headline"])}</h3>'
            f'<p class="why">{esc(a["rationale"])}</p>'
            f'<div class="tied">tied to: {esc(a["tied_to"])}</div>'
            '</div>'
        )
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Top-level render
# ─────────────────────────────────────────────────────────────────────────────

def render_html(session: dict, insights: list[dict], q_table: list[dict]) -> str:
    agg = aggregate.aggregate_all(insights, q_table, session)

    # Banner derived values
    session_id = str(session.get("session_id", "(no-session)"))
    started = float(session.get("started_at", 0.0))
    last_event = float(session.get("last_event_at", 0.0))
    duration = max(0.0, last_event - started) if started else agg["state_time"]["total_seconds"]
    end_state = str(session.get("state", "planning"))

    edges_svg, nodes_svg = build_fsa_svg(agg["transitions"], session)

    state_timeline_note = (
        f'The session entered {agg["transitions"]["edge_count"]} distinct transitions '
        f'and visited {sum(1 for b in agg["state_time"]["bars"] if b["seconds"] > 0)} state(s).'
    )

    # Empty-friendly note if the histogram is degenerate.
    if agg["state_time"]["total_seconds"] <= 0.001:
        state_timeline_note = (
            "No measurable elapsed time in any state — this is a freshly-started "
            "session or the timestamps were not recorded."
        )

    mapping = {
        "session_id_short": esc(short_id(session_id)),
        "rendered_at": esc(_dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "end_state": esc(end_state),
        "end_state_short": esc(end_state.upper()[:6]),
        "duration_pretty": esc(pretty_duration(duration)),
        "total_seconds_pretty": esc(pretty_duration(agg["state_time"]["total_seconds"])),
        "insight_count": esc(len(insights)),
        "q_table_size": esc(len(q_table)),
        "tool_call_count": esc(agg["tools"]["total_calls"]),
        "transition_count": esc(int(session.get("transition_count",
                                                agg["transitions"]["edge_count"]) or 0)),
        "drift_count": esc(agg["drift"]["count"]),
        "spike_count": esc(agg["entropy"]["count"]),
        "dominant_state": esc(agg["state_time"]["dominant_state"]),
        "state_timeline_note": esc(state_timeline_note),
        "most_visited": esc(agg["transitions"]["most_visited"]),
        "edge_count": esc(agg["transitions"]["edge_count"]),

        # SVG and fragment placeholders
        "state_gantt_rows": build_state_gantt(agg["state_time"]),
        "fsa_edges_svg": edges_svg,
        "fsa_nodes_svg": nodes_svg,
        "fsa_edge_table_rows": build_edge_table(agg["transitions"]),
        "q_route_blocks": build_q_route_blocks(agg["rewards"], session),
        "drift_table": build_drift_table(agg["drift"]),
        "subagent_table": build_subagent_table(agg["subagents"]),
        "subagent_success_rate": esc(agg["subagents"]["success_rate"]),
        "subagent_mean_walltime": esc(agg["subagents"]["mean_wall_time"]),
        "subagent_count": esc(agg["subagents"]["count"]),
        "reward_top_bars": build_reward_bars(agg["rewards"]["top"]),
        "reward_bottom_bars": build_reward_bars(agg["rewards"]["bottom"], negative=True),
        "grounding_grounded": esc(agg["grounding"]["grounded"]),
        "grounding_ungrounded": esc(agg["grounding"]["ungrounded"]),
        "grounding_pct": esc(agg["grounding"]["pct"]),
        "grounding_block": build_grounding_block(agg["grounding"]),
        "contradiction_block": build_contradiction_block(agg["contradictions"]),
        "entropy_block": build_entropy_block(agg["entropy"]),
        "tool_ledger_table": build_tool_ledger_table(agg["tools"]),
        "forward_cards": build_forward_cards(agg["forward"]),
    }

    tmpl = string.Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return tmpl.safe_substitute(mapping)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the Mentat session debrief HTML artifact.")
    ap.add_argument("--session", default=None,
                    help="Session ID. Defaults to $CLAUDE_SESSION_ID or active_session.json.")
    ap.add_argument("--out", default=None,
                    help="Output path. Defaults to ./mentat-debrief-<sid>.html.")
    ap.add_argument("--insights-limit", type=int, default=500,
                    help="Cap the insight stream at the last N events (default 500).")
    args = ap.parse_args(argv)

    sid = resolve_session_id(args.session)
    if not sid:
        print("error: no session id (pass --session, set CLAUDE_SESSION_ID, "
              "or write ${CLAUDE_PROJECT_DIR}/.mentat/active_session.json)",
              file=sys.stderr)
        return 2

    session = load_session(sid)
    insights = load_insights(sid, args.insights_limit)
    q_table = load_q_table()

    html_out = render_html(session, insights, q_table)

    out_path = Path(args.out) if args.out else Path.cwd() / f"mentat-debrief-{sid}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")

    size_kb = len(html_out.encode("utf-8")) / 1024.0
    print(f"wrote {out_path} ({size_kb:.1f} KB, {len(insights)} insights, "
          f"{len(q_table)} q-rows, end state {session.get('state','?')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
