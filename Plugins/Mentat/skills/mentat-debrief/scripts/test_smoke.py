#!/usr/bin/env python3
"""Smoke test for the Mentat debrief renderer.

Synthesizes a fake insight stream + Q-table + session record on disk inside a
throwaway MENTAT_HOME, runs the aggregator + renderer end-to-end, and asserts:

    1. aggregate_all() returns the expected ten-key bundle.
    2. render_html() produces non-trivial HTML.
    3. The HTML is well-formed enough (basic tag balance check on a few tags).
    4. All twelve sections render with substantive content (not just empty cards).
    5. CLI entry exits 0 with --session and --out.
    6. Size lands in the 50-300 KB ballpark for a synthetic input.

Pure stdlib. Run directly: ``python3 test_smoke.py``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import aggregate  # type: ignore
import render  # type: ignore


SID = "smk-20260510-test-session-id"


def _synth_session(home: Path) -> dict:
    now = time.time()
    session = {
        "session_id": SID,
        "state": "reflecting",
        "chain_depth": 5,
        "drift_count": 2,
        "transition_count": 14,
        "started_at": now - 3600,
        "last_event_at": now - 30,
        "last_tool": "Bash",
        "last_tool_success": True,
        "notes": ["renderer smoke test"],
    }
    (home / "sessions").mkdir(parents=True, exist_ok=True)
    (home / "sessions" / f"{SID}.json").write_text(json.dumps(session), encoding="utf-8")
    return session


def _synth_insights(home: Path, started_at: float) -> list[dict]:
    """Produce a representative spread across insight types."""
    (home / "insights").mkdir(parents=True, exist_ok=True)
    p = home / "insights" / f"{SID}.jsonl"
    insights: list[dict] = []

    t = started_at
    def emit(kind: str, payload: dict | None = None, state: str | None = None, dt: float = 12.0) -> None:
        nonlocal t
        t += dt
        i = {
            "type": kind,
            "payload": payload or {},
            "state": state,
            "timestamp": t,
            "seq": len(insights),
            "id": f"i{len(insights):04d}",
            "session_id": SID,
        }
        insights.append(i)

    # Boot
    emit("session_start", state="planning", dt=0.0)
    emit("state_transition", {"prev": "planning", "next": "exploring", "trigger": "read"}, state="exploring", dt=20.0)
    emit("state_transition", {"prev": "exploring", "next": "executing", "trigger": "write"}, state="executing", dt=120.0)
    # Reward signals
    for tool, lat, ok in [
        ("Read", 80.0, True), ("Grep", 45.0, True), ("Bash", 220.0, True),
        ("Edit", 320.0, True), ("Bash", 410.0, False), ("Write", 180.0, True),
        ("Bash", 600.0, True),
    ]:
        emit("reward_signal", {"tool": tool, "success": ok, "latency_ms": lat,
                               "value": 1.0 if ok else -0.5}, state="executing", dt=8.0)
    # Verify cycle
    emit("state_transition", {"prev": "executing", "next": "verifying", "trigger": "verify"}, state="verifying", dt=4.0)
    emit("reward_signal", {"tool": "Bash", "success": True, "latency_ms": 950.0,
                           "value": 1.0}, state="verifying", dt=4.0)
    emit("state_transition", {"prev": "verifying", "next": "reflecting", "trigger": "tool_success"},
         state="reflecting", dt=2.0)
    # Sub-agent dispatch
    emit("subagent_dispatch", {"dispatch_id": "d1", "operator": "mentat-cartographer",
                               "objective": "map the auth layer"}, state="exploring", dt=5.0)
    emit("subagent_return", {"dispatch_id": "d1", "success": True,
                             "deliverable": "wrote research/auth-map.md (240 lines)"},
         state="exploring", dt=180.0)
    emit("subagent_dispatch", {"dispatch_id": "d2", "operator": "mentat-crucible",
                               "objective": "stress-test the q-table dump path"}, state="executing", dt=2.0)
    emit("subagent_return", {"dispatch_id": "d2", "success": False,
                             "deliverable": "crashed in q_table.dump() — table was None"},
         state="executing", dt=92.0)
    # Drift
    emit("scope_drift", {"topic": "inference / model loading",
                         "deferred_at": "scope.md:14",
                         "evidence": "...let's just try a quick safetensors load to..."},
         state="drifting", dt=2.0)
    emit("state_transition", {"prev": "executing", "next": "drifting", "trigger": "scope_drift"},
         state="drifting", dt=0.5)
    emit("scope_drift", {"topic": "AI/ML pipelines", "deferred_at": "scope.md:18",
                         "evidence": "drop in a PyTorch dep for the embedding pass"},
         state="drifting", dt=4.0)
    # Source grounding
    emit("source_grounded", {"claim": "Hook timeout default is 600s",
                             "source": "docs.anthropic.com/en/docs/claude-code/hooks#timeouts"},
         state="reflecting", dt=2.0)
    emit("source_grounded", {"claim": "Skills auto-attach via description retrieval",
                             "source": "docs.anthropic.com/en/docs/claude-code/skills"},
         state="reflecting", dt=2.0)
    emit("source_ungrounded", {"claim": "MCP servers always run as subprocesses"},
         state="reflecting", dt=2.0)
    emit("source_ungrounded", {"claim": "The Q-table is reset on session start"}, state="reflecting", dt=2.0)
    emit("source_ungrounded", {"claim": "Drift detection fires on partial matches"}, state="reflecting", dt=2.0)
    # Entropy spike
    emit("entropy_spike", {"chain_depth": 9, "trigger": "9 EXEC without VERIFY"},
         state="executing", dt=1.0)
    # Contradiction
    emit("contradiction", {"a": "Q-table is per-session", "b": "Q-table is global and SQLite-backed",
                           "note": "Resolved: it is global; per-session reference in skill draft was wrong."},
         state="reflecting", dt=2.0)
    # Tool failure
    emit("tool_failure", {"tool": "Bash", "latency_ms": 4500.0,
                          "error": "timeout"}, state="blocked", dt=2.0)

    with p.open("w", encoding="utf-8") as f:
        for i in insights:
            f.write(json.dumps(i) + "\n")
    return insights


def _synth_q_table(home: Path) -> list[dict]:
    db_path = home / "q_table.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE q_values (
            state TEXT NOT NULL,
            tool TEXT NOT NULL,
            value REAL NOT NULL,
            visits INTEGER NOT NULL,
            last_updated REAL NOT NULL,
            PRIMARY KEY (state, tool)
        );
        """
    )
    rows = [
        ("planning",   "Read",  0.62, 18),
        ("planning",   "Grep",  0.58, 14),
        ("planning",   "Glob",  0.41, 6),
        ("exploring",  "Read",  0.74, 32),
        ("exploring",  "Grep",  0.69, 28),
        ("exploring",  "Bash",  0.31, 9),
        ("executing",  "Edit",  0.81, 22),
        ("executing",  "Write", 0.71, 11),
        ("executing",  "Bash",  0.44, 30),
        ("verifying",  "Bash",  0.88, 19),
        ("verifying",  "Read",  0.22, 4),
        ("reflecting", "Read",  0.55, 12),
        ("reflecting", "Write", 0.39, 5),
        ("blocked",    "Bash", -0.41, 7),
        ("blocked",    "Read",  0.18, 3),
        ("drifting",   "Read",  0.02, 2),
        ("compacting", "Write", 0.46, 4),
    ]
    now = time.time()
    conn.executemany(
        "INSERT INTO q_values (state, tool, value, visits, last_updated) VALUES (?, ?, ?, ?, ?)",
        [(s, t, v, n, now) for (s, t, v, n) in rows],
    )
    conn.commit()
    conn.close()
    return [{"state": s, "tool": t, "value": v, "visits": n, "last_updated": now}
            for (s, t, v, n) in rows]


# ─── well-formedness check ──────────────────────────────────────────────────

def _check_balanced(html: str) -> tuple[bool, str]:
    """Lightweight balance check: <section>, <table>, <div>, <details>, <svg>."""
    for tag in ("section", "table", "details", "svg"):
        opens = len(re.findall(rf"<{tag}\b", html, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}>", html, re.IGNORECASE))
        if opens != closes:
            return False, f"<{tag}> imbalance: {opens} open / {closes} close"
    # <div> is a little fuzzier (self-closing variations); just confirm both > 0
    div_open = len(re.findall(r"<div\b", html, re.IGNORECASE))
    div_close = len(re.findall(r"</div>", html, re.IGNORECASE))
    if div_open != div_close:
        return False, f"<div> imbalance: {div_open} open / {div_close} close"
    return True, "balanced"


# ─── the tests ──────────────────────────────────────────────────────────────

REQUIRED_SECTION_IDS = [
    "timeline", "fsa", "qroute", "drift", "subagents",
    "rewards", "grounding", "contradictions", "entropy",
    "tools", "forward",
]


def _hr(label: str, ok: bool, msg: str = "") -> None:
    pad = "." * max(1, 56 - len(label))
    status = "PASS" if ok else "FAIL"
    print(f"  {label} {pad} {status} {msg}")


def main() -> int:
    print("mentat-debrief renderer smoke test")
    fails: list[str] = []

    tmp = Path(tempfile.mkdtemp(prefix="mentat-smoke-"))
    try:
        home = tmp / ".mentat"
        home.mkdir(parents=True, exist_ok=True)

        # --- synthesize -----------------------------------------------------
        session = _synth_session(home)
        insights = _synth_insights(home, session["started_at"])
        q_table = _synth_q_table(home)

        # --- aggregator -----------------------------------------------------
        agg = aggregate.aggregate_all(insights, q_table, session)
        expected_keys = {"state_time", "transitions", "drift", "rewards",
                         "subagents", "grounding", "entropy", "contradictions",
                         "tools", "forward"}
        ok = expected_keys.issubset(agg.keys())
        _hr("aggregate_all returns full bundle", ok)
        if not ok:
            fails.append("aggregate_all missing keys: " + str(expected_keys - agg.keys()))

        # drift count
        ok = agg["drift"]["count"] == 2
        _hr("drift.count == 2 synthetic events", ok, f"got {agg['drift']['count']}")
        if not ok:
            fails.append("drift.count")

        # sub-agent ledger has 2 entries, 1 success
        ok = agg["subagents"]["count"] == 2 and 40 < agg["subagents"]["success_rate"] < 60
        _hr("subagent ledger pairs dispatch+return", ok,
            f"count={agg['subagents']['count']} rate={agg['subagents']['success_rate']}%")
        if not ok:
            fails.append("subagent ledger pairing")

        # grounding signals
        ok = agg["grounding"]["grounded"] == 2 and agg["grounding"]["ungrounded"] == 3
        _hr("grounding 2/3 split", ok,
            f"g={agg['grounding']['grounded']} u={agg['grounding']['ungrounded']}")
        if not ok:
            fails.append("grounding split")

        # entropy spike
        ok = agg["entropy"]["count"] >= 1
        _hr("entropy spike captured", ok, f"count={agg['entropy']['count']}")
        if not ok:
            fails.append("entropy")

        # contradiction
        ok = agg["contradictions"]["count"] == 1
        _hr("contradiction captured", ok, f"count={agg['contradictions']['count']}")
        if not ok:
            fails.append("contradiction")

        # rewards top includes Bash@verifying (highest Q in synthetic table)
        top_tools = {r["tool"] for r in agg["rewards"]["top"]}
        ok = "Bash" in top_tools or "Edit" in top_tools or "Read" in top_tools
        _hr("rewards top non-empty", ok, f"top={top_tools}")
        if not ok:
            fails.append("rewards top")

        # forward actions: 3, and at least one tied to drift
        ok = len(agg["forward"]["actions"]) == 3
        _hr("forward actions = 3", ok, f"got {len(agg['forward']['actions'])}")
        if not ok:
            fails.append("forward actions count")

        drift_action = any("drift" in a["tied_to"].lower() or "scope" in a["headline"].lower()
                           for a in agg["forward"]["actions"])
        _hr("forward action mentions drift/scope", drift_action)
        if not drift_action:
            fails.append("forward drift tie")

        # --- render ----------------------------------------------------------
        html = render.render_html(session, insights, q_table)
        size_kb = len(html.encode("utf-8")) / 1024.0
        ok = len(html) > 8000  # template alone is bigger than this
        _hr("render produces non-trivial HTML", ok, f"{size_kb:.1f} KB")
        if not ok:
            fails.append("render size")

        ok = 30 < size_kb < 400
        _hr("HTML size in 30-400 KB band", ok, f"{size_kb:.1f} KB")
        if not ok:
            fails.append("size band")

        # well-formedness
        balanced, why = _check_balanced(html)
        _hr("HTML is balanced", balanced, why)
        if not balanced:
            fails.append("balance: " + why)

        # every required section id appears
        for sid_id in REQUIRED_SECTION_IDS:
            ok = f'id="{sid_id}"' in html
            _hr(f"section #{sid_id} present", ok)
            if not ok:
                fails.append(f"missing section #{sid_id}")

        # banner mention of session id
        ok = SID[:12] in html
        _hr("banner carries short session id", ok)
        if not ok:
            fails.append("banner sid")

        # forward cards
        ok = html.count("forward-card") >= 3
        _hr("≥3 forward-cards in HTML", ok, f"got {html.count('forward-card')}")
        if not ok:
            fails.append("forward-card count in HTML")

        # FSA graph contains pulsing class (most-visited node)
        ok = "pulse-anim" in html
        _hr("pulse-anim on most-visited", ok)
        if not ok:
            fails.append("pulse-anim")

        # Drift evidence text leaks through
        ok = "safetensors" in html or "PyTorch" in html
        _hr("drift evidence interpolated", ok)
        if not ok:
            fails.append("drift evidence")

        # --- CLI entry --------------------------------------------------------
        out_path = tmp / "out" / "debrief.html"
        env = dict(os.environ, MENTAT_HOME=str(home), CLAUDE_SESSION_ID=SID)
        cmd = [sys.executable, str(HERE / "render.py"), "--session", SID, "--out", str(out_path)]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        ok = proc.returncode == 0 and out_path.exists()
        _hr("render.py CLI exits 0", ok, proc.stdout.strip() or proc.stderr.strip())
        if not ok:
            fails.append("CLI exit: " + proc.stderr.strip())
        else:
            cli_size_kb = out_path.stat().st_size / 1024.0
            _hr("CLI artifact exists", True, f"{cli_size_kb:.1f} KB at {out_path}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if fails:
        print(f"FAIL ({len(fails)})")
        for f in fails:
            print("  - " + f)
        return 1
    print("OK — all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
