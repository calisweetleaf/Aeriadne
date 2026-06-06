"""Pure-function aggregators over the raw insight stream + Q-table dump.

Every function in this module takes ``(insights, q_table, session)`` and returns
a plain ``dict`` of computed metrics. No I/O, no template knowledge, no globals.
The renderer composes these into the HTML; the smoke test exercises them with
synthetic input.

``insights`` is a list of dicts (one per JSONL line, parsed). Each carries:
    type        — InsightType value (e.g. "state_transition", "scope_drift")
    state       — optional state at emission
    timestamp   — float epoch seconds
    seq         — append order
    payload     — type-specific dict

``q_table`` is a list of {state, tool, value, visits, last_updated} rows.

``session`` is the Session dataclass serialized: session_id, state, started_at,
last_event_at, transition_count, drift_count, last_tool, last_tool_success.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

# Insight type tokens — duplicated from state_machine/insights.py so this module
# stays import-free against the rest of the plugin. The values are stable.
T_STATE_TRANSITION = "state_transition"
T_SCOPE_DRIFT = "scope_drift"
T_SOURCE_GROUNDED = "source_grounded"
T_SOURCE_UNGROUNDED = "source_ungrounded"
T_REWARD_SIGNAL = "reward_signal"
T_SUBAGENT_DISPATCH = "subagent_dispatch"
T_SUBAGENT_RETURN = "subagent_return"
T_TOOL_FAILURE = "tool_failure"
T_ENTROPY_SPIKE = "entropy_spike"
T_CONTRADICTION = "contradiction"
T_Q_ROUTE_HINT = "q_route_hint"

ALL_STATES = (
    "planning", "exploring", "executing", "verifying",
    "reflecting", "blocked", "drifting", "compacting",
)


def _ts(insight: dict) -> float:
    return float(insight.get("timestamp", 0.0))


def _type(insight: dict) -> str:
    return str(insight.get("type", ""))


def state_time_histogram(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Seconds spent in each state, derived from STATE_TRANSITION timestamps.

    Walk the transitions in seq order. Between transition[i] and transition[i+1]
    the machine was in transition[i].next. The last transition's tail runs to
    session.last_event_at (or session.started_at if the session is brand new).
    """
    transitions = sorted(
        [i for i in insights if _type(i) == T_STATE_TRANSITION],
        key=lambda i: _ts(i),
    )
    seconds: dict[str, float] = {s: 0.0 for s in ALL_STATES}
    if not transitions:
        # No transitions logged — attribute everything to the current state.
        total = max(0.0, float(session.get("last_event_at", 0.0)) - float(session.get("started_at", 0.0)))
        seconds[str(session.get("state", "planning"))] += total
    else:
        # Span before first transition (initial PLANNING).
        first_state = transitions[0]["payload"].get("prev", "planning")
        head = _ts(transitions[0]) - float(session.get("started_at", _ts(transitions[0])))
        if head > 0:
            seconds[first_state] = seconds.get(first_state, 0.0) + head
        # Inter-transition spans.
        for idx, t in enumerate(transitions):
            current = t["payload"].get("next", t.get("state", "planning"))
            next_ts = _ts(transitions[idx + 1]) if idx + 1 < len(transitions) else float(
                session.get("last_event_at", _ts(t))
            )
            dur = max(0.0, next_ts - _ts(t))
            seconds[current] = seconds.get(current, 0.0) + dur

    total = sum(seconds.values()) or 1.0
    bars = []
    for s in ALL_STATES:
        sec = round(seconds.get(s, 0.0), 2)
        bars.append({
            "state": s,
            "seconds": sec,
            "pct": round(100.0 * sec / total, 2),
        })
    return {
        "total_seconds": round(total, 2),
        "bars": bars,
        "dominant_state": max(bars, key=lambda b: b["seconds"])["state"] if bars else "planning",
    }


def transition_edges(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Edge weights (prev -> next counts) and per-state visit totals."""
    edges: Counter = Counter()
    state_visits: Counter = Counter()
    for i in insights:
        if _type(i) != T_STATE_TRANSITION:
            continue
        p = i.get("payload") or {}
        prev = p.get("prev", "planning")
        nxt = p.get("next", "planning")
        edges[(prev, nxt)] += 1
        state_visits[nxt] += 1
    sorted_edges = [
        {"from": a, "to": b, "weight": w}
        for (a, b), w in sorted(edges.items(), key=lambda kv: kv[1], reverse=True)
    ]
    most_visited = state_visits.most_common(1)[0][0] if state_visits else str(
        session.get("state", "planning")
    )
    return {
        "edges": sorted_edges,
        "state_visits": dict(state_visits),
        "most_visited": most_visited,
        "edge_count": len(sorted_edges),
    }


def drift_events(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Every SCOPE_DRIFT with full payload, ordered by sequence."""
    rows = []
    for i in insights:
        if _type(i) != T_SCOPE_DRIFT:
            continue
        p = i.get("payload") or {}
        rows.append({
            "seq": int(i.get("seq", 0)),
            "timestamp": _ts(i),
            "topic": str(p.get("topic", "")),
            "deferred_at": str(p.get("deferred_at", "") or ""),
            "evidence": str(p.get("evidence", "")),
            "state": str(i.get("state", "") or ""),
        })
    rows.sort(key=lambda r: r["seq"])
    return {"rows": rows, "count": len(rows)}


def reward_distribution(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Per-tool mean Q-value across states (top-5 + bottom-5 + per-state top-3).

    Pulls from the Q-table dump (which already encodes the TD-updated values),
    not from REWARD_SIGNAL insights — the Q-table is the authoritative summary.
    """
    by_tool: dict[str, list[float]] = defaultdict(list)
    by_tool_visits: dict[str, int] = defaultdict(int)
    by_state_tool: dict[str, list[tuple[str, float, int]]] = defaultdict(list)
    for row in q_table:
        state = str(row.get("state", ""))
        tool = str(row.get("tool", ""))
        value = float(row.get("value", 0.0))
        visits = int(row.get("visits", 0))
        if not tool:
            continue
        by_tool[tool].append(value)
        by_tool_visits[tool] += visits
        by_state_tool[state].append((tool, value, visits))

    means = []
    for tool, vals in by_tool.items():
        mean = sum(vals) / len(vals) if vals else 0.0
        means.append({
            "tool": tool,
            "mean": round(mean, 4),
            "visits": by_tool_visits[tool],
            "states": len(vals),
        })
    means.sort(key=lambda m: m["mean"], reverse=True)
    top = means[:5]
    bottom = list(reversed(means[-5:])) if len(means) > 5 else []

    per_state_top3 = {}
    for state, rows in by_state_tool.items():
        rows.sort(key=lambda r: r[1], reverse=True)
        per_state_top3[state] = [
            {"tool": t, "value": round(v, 4), "visits": n}
            for (t, v, n) in rows[:3]
        ]

    return {
        "top": top,
        "bottom": bottom,
        "per_state_top3": per_state_top3,
        "all_means": means,
    }


def subagent_ledger(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Pair SUBAGENT_DISPATCH events with their SUBAGENT_RETURN by dispatch id.

    If a dispatch has no matching return (still running, or crashed), it appears
    with success=None and wall_time=None. The ledger sorts by dispatch time.
    """
    dispatches = {}
    for i in insights:
        t = _type(i)
        if t == T_SUBAGENT_DISPATCH:
            p = i.get("payload") or {}
            did = str(p.get("dispatch_id") or p.get("id") or f"d{i.get('seq', 0)}")
            dispatches[did] = {
                "dispatch_id": did,
                "operator": str(p.get("operator", p.get("agent", "subagent"))),
                "objective": str(p.get("objective", p.get("prompt", "")))[:200],
                "dispatched_at": _ts(i),
                "returned_at": None,
                "success": None,
                "wall_time": None,
                "deliverable": "",
            }
        elif t == T_SUBAGENT_RETURN:
            p = i.get("payload") or {}
            did = str(p.get("dispatch_id") or p.get("id") or "")
            if did and did in dispatches:
                d = dispatches[did]
                d["returned_at"] = _ts(i)
                d["success"] = bool(p.get("success", True))
                d["wall_time"] = round(_ts(i) - d["dispatched_at"], 2)
                d["deliverable"] = str(p.get("deliverable", p.get("summary", "")))[:240]
            else:
                # orphan return — list it standalone
                key = f"orphan-{i.get('seq', 0)}"
                dispatches[key] = {
                    "dispatch_id": key,
                    "operator": str(p.get("operator", "unknown")),
                    "objective": "(no dispatch event)",
                    "dispatched_at": _ts(i),
                    "returned_at": _ts(i),
                    "success": bool(p.get("success", True)),
                    "wall_time": 0.0,
                    "deliverable": str(p.get("deliverable", ""))[:240],
                }
    rows = list(dispatches.values())
    rows.sort(key=lambda r: r["dispatched_at"])
    successes = [r for r in rows if r["success"] is True]
    wall_times = [r["wall_time"] for r in rows if r["wall_time"] is not None]
    return {
        "rows": rows,
        "count": len(rows),
        "success_rate": round(100.0 * len(successes) / max(1, len(rows)), 1),
        "mean_wall_time": round(sum(wall_times) / max(1, len(wall_times)), 2) if wall_times else 0.0,
    }


def source_grounding_ratio(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """SOURCE_GROUNDED vs SOURCE_UNGROUNDED counts + a sample evidence list."""
    grounded = [i for i in insights if _type(i) == T_SOURCE_GROUNDED]
    ungrounded = [i for i in insights if _type(i) == T_SOURCE_UNGROUNDED]
    g, u = len(grounded), len(ungrounded)
    total = g + u
    ratio = round(g / max(1, total), 3)
    samples = []
    for i in grounded[:6]:
        p = i.get("payload") or {}
        samples.append({
            "kind": "grounded",
            "claim": str(p.get("claim", p.get("statement", "")))[:160],
            "source": str(p.get("source", p.get("url", "")))[:160],
        })
    for i in ungrounded[:6]:
        p = i.get("payload") or {}
        samples.append({
            "kind": "ungrounded",
            "claim": str(p.get("claim", p.get("statement", "")))[:160],
            "source": "—",
        })
    return {
        "grounded": g,
        "ungrounded": u,
        "total": total,
        "ratio": ratio,
        "pct": round(ratio * 100, 1),
        "samples": samples,
    }


def entropy_spikes(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """ENTROPY_SPIKE rows: state at spike, chain depth, seq, timestamp."""
    rows = []
    for i in insights:
        if _type(i) != T_ENTROPY_SPIKE:
            continue
        p = i.get("payload") or {}
        rows.append({
            "seq": int(i.get("seq", 0)),
            "timestamp": _ts(i),
            "state": str(i.get("state", "") or p.get("state", "")),
            "chain_depth": int(p.get("chain_depth", 0)),
            "trigger": str(p.get("trigger", "")),
        })
    rows.sort(key=lambda r: r["seq"])
    return {"rows": rows, "count": len(rows)}


def contradictions(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """CONTRADICTION rows with payload."""
    rows = []
    for i in insights:
        if _type(i) != T_CONTRADICTION:
            continue
        p = i.get("payload") or {}
        rows.append({
            "seq": int(i.get("seq", 0)),
            "timestamp": _ts(i),
            "state": str(i.get("state", "") or ""),
            "a": str(p.get("a", p.get("claim_a", "")))[:240],
            "b": str(p.get("b", p.get("claim_b", "")))[:240],
            "note": str(p.get("note", p.get("resolution", "")))[:240],
        })
    rows.sort(key=lambda r: r["seq"])
    return {"rows": rows, "count": len(rows)}


def tool_ledger(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Every tool used, with count, success rate, mean latency.

    Reward-signal insights carry tool name, success flag and latency in payload
    (the q_table.update path emits these). Fall back to TOOL_FAILURE rows for
    error-only invocations and any tool present in the Q-table.
    """
    counts: Counter = Counter()
    successes: Counter = Counter()
    latencies: dict[str, list[float]] = defaultdict(list)
    seen_tools: set[str] = set()

    for i in insights:
        t = _type(i)
        p = i.get("payload") or {}
        if t == T_REWARD_SIGNAL:
            tool = str(p.get("tool", ""))
            if not tool:
                continue
            seen_tools.add(tool)
            counts[tool] += 1
            if bool(p.get("success", True)):
                successes[tool] += 1
            lat = p.get("latency_ms")
            if lat is not None:
                try:
                    latencies[tool].append(float(lat))
                except (TypeError, ValueError):
                    pass
        elif t == T_TOOL_FAILURE:
            tool = str(p.get("tool", ""))
            if not tool:
                continue
            seen_tools.add(tool)
            counts[tool] += 1
            lat = p.get("latency_ms")
            if lat is not None:
                try:
                    latencies[tool].append(float(lat))
                except (TypeError, ValueError):
                    pass

    # Tools known only via the Q-table (visited but no insight emitted this session).
    for row in q_table:
        tool = str(row.get("tool", ""))
        if tool and tool not in seen_tools:
            seen_tools.add(tool)

    rows = []
    for tool in sorted(seen_tools):
        c = counts[tool]
        s = successes[tool]
        lats = latencies.get(tool) or []
        rows.append({
            "tool": tool,
            "count": c,
            "successes": s,
            "success_rate": round(100.0 * s / c, 1) if c else 0.0,
            "mean_latency_ms": round(sum(lats) / len(lats), 1) if lats else 0.0,
        })
    rows.sort(key=lambda r: (r["count"], r["success_rate"]), reverse=True)
    return {"rows": rows, "tool_count": len(rows), "total_calls": sum(counts.values())}


def forward_actions(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    """Three forward actions tied to the actual insight stream.

    Heuristics — same ones the skill body used to ask the model to apply, but
    now deterministic:

    1. If drift_count > 0  → "reaffirm scope.md" at the drifting/blocked state.
    2. If entropy_spikes > 0  → "tighten verify cadence" at the executing state.
    3. If Q-best for current state differs from last_tool with value > 0.5 →
       "consider <tool>" at the current state.

    Fallbacks fill the slots if a primary heuristic doesn't fire.
    """
    state = str(session.get("state", "planning"))
    last_tool = session.get("last_tool")
    drift_count = sum(1 for i in insights if _type(i) == T_SCOPE_DRIFT)
    spike_count = sum(1 for i in insights if _type(i) == T_ENTROPY_SPIKE)
    contradiction_count = sum(1 for i in insights if _type(i) == T_CONTRADICTION)
    ungrounded_count = sum(1 for i in insights if _type(i) == T_SOURCE_UNGROUNDED)

    # Q-best for current state.
    q_best = None
    for row in q_table:
        if str(row.get("state", "")) != state:
            continue
        v = float(row.get("value", 0.0))
        if q_best is None or v > q_best[1]:
            q_best = (str(row.get("tool", "")), v, int(row.get("visits", 0)))

    actions: list[dict] = []

    if drift_count > 0:
        actions.append({
            "headline": "Reaffirm scope.md before the next write.",
            "state": "drifting",
            "rationale": (
                f"{drift_count} scope-drift event(s) tripped the sentinel this session. "
                "Re-read the project's scope.md, decide whether the deferred topic is "
                "now in-scope, and either update scope.md or re-route the conversation."
            ),
            "tied_to": f"{drift_count} SCOPE_DRIFT insight(s)",
        })

    if spike_count > 0:
        actions.append({
            "headline": "Tighten verify cadence — chain depth exceeded threshold.",
            "state": "executing",
            "rationale": (
                f"{spike_count} entropy spike(s) logged. Each is a window where the agent "
                "stayed in EXECUTING past the chain-depth threshold without a VERIFYING "
                "transition. Inject an explicit test/lint step before the next write."
            ),
            "tied_to": f"{spike_count} ENTROPY_SPIKE insight(s)",
        })

    if q_best and last_tool and q_best[0] != last_tool and q_best[1] > 0.5:
        actions.append({
            "headline": f"Consider routing through `{q_best[0]}` in {state.upper()}.",
            "state": state,
            "rationale": (
                f"Historical Q-best for {state} is `{q_best[0]}` "
                f"(value={q_best[1]:.2f}, visits={q_best[2]}). Last tool used was "
                f"`{last_tool}` — the Q-table has higher confidence in the alternative."
            ),
            "tied_to": f"Q-table delta vs last_tool",
        })

    if contradiction_count > 0 and len(actions) < 3:
        actions.append({
            "headline": "Resolve outstanding contradiction(s) before continuing.",
            "state": "reflecting",
            "rationale": (
                f"{contradiction_count} contradiction(s) logged. Each is two claims the "
                "session held simultaneously without reconciliation. Pin one as correct, "
                "or mark the question open."
            ),
            "tied_to": f"{contradiction_count} CONTRADICTION insight(s)",
        })

    if ungrounded_count > 2 and len(actions) < 3:
        actions.append({
            "headline": "Re-ground unsupported claims with a source pass.",
            "state": "exploring",
            "rationale": (
                f"{ungrounded_count} ungrounded statement(s) emitted vs the verified count. "
                "Run a quick Read/Grep/WebFetch pass to attach citations or weaken the claims."
            ),
            "tied_to": f"{ungrounded_count} SOURCE_UNGROUNDED insight(s)",
        })

    # Generic fallbacks if we still don't have three.
    fallbacks = [
        {
            "headline": "Snapshot to handoff.md before context compaction.",
            "state": "compacting",
            "rationale": (
                "The session is approaching context pressure. Write a fresh handoff snapshot "
                "so the next session can resume with FSA state + Q-best + recent insights."
            ),
            "tied_to": "preventive — no insight required",
        },
        {
            "headline": "Refresh the Q-table delta vs the global baseline.",
            "state": "reflecting",
            "rationale": (
                "Dump the per-state top-3 from the project-local table and compare to global. "
                "If they diverge, this project has a private routing policy worth keeping."
            ),
            "tied_to": "Q-table mathematics — Section 04",
        },
        {
            "headline": "Re-affirm the FSA's current state with an explicit prompt.",
            "state": state,
            "rationale": (
                f"Session ended in {state.upper()}. A single prompt that names the next move "
                "will pin the machine into PLANNING cleanly instead of letting it drift."
            ),
            "tied_to": "session.state at last_event_at",
        },
    ]
    for f in fallbacks:
        if len(actions) >= 3:
            break
        actions.append(f)

    return {"actions": actions[:3]}


# Convenience: the renderer can call this once to bundle everything.
def aggregate_all(insights: list[dict], q_table: list[dict], session: dict) -> dict[str, Any]:
    return {
        "state_time": state_time_histogram(insights, q_table, session),
        "transitions": transition_edges(insights, q_table, session),
        "drift": drift_events(insights, q_table, session),
        "rewards": reward_distribution(insights, q_table, session),
        "subagents": subagent_ledger(insights, q_table, session),
        "grounding": source_grounding_ratio(insights, q_table, session),
        "entropy": entropy_spikes(insights, q_table, session),
        "contradictions": contradictions(insights, q_table, session),
        "tools": tool_ledger(insights, q_table, session),
        "forward": forward_actions(insights, q_table, session),
    }
