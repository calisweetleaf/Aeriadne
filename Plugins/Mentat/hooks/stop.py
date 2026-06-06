#!/usr/bin/env python3
"""Stop hook.

Fires at the end of a Claude Code turn (model declared done). Emits SESSION_END,
writes a handoff snapshot, and — v0.3 — computes a structural self-play eval:
state path, tool accounting, Q-best recommendation. Writes eval to
~/.mentat/eval/{session_id}.eval.json and atomically updates latest.json.
Prints a compact diagnostic box to stderr (visible in terminal after the turn).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    emit_safe,
    home_root,
    open_context,
    read_payload,
)


def _compute_eval(ctx) -> dict:
    """Sync, in-memory: derive structural metrics from insight bus + Q-table.

    Reads the last 30 insights to build a state path and tool accounting.
    No I/O beyond the JSONL tail read and one Q-table query — always <10ms.
    """
    recent = ctx.bus.tail(30)

    # Build state path from STATE_TRANSITION insights
    states: list[str] = []
    for ins in recent:
        if ins.type.value == "state_transition":
            p = ins.payload or {}
            if not states and p.get("prev"):
                states.append(p["prev"])
            if p.get("next"):
                states.append(p["next"])
    if not states or states[-1] != ctx.session.state.value:
        states.append(ctx.session.state.value)
    # Deduplicate preserving order
    seen: set[str] = set()
    state_path: list[str] = []
    for s in states:
        if s not in seen:
            seen.add(s)
            state_path.append(s)

    # Tool accounting from REWARD_SIGNAL insights
    rewards = [i for i in recent if i.type.value == "reward_signal"]
    total = len(rewards)
    ok = sum(1 for r in rewards if (r.payload or {}).get("success", True))

    # Q-best for final state
    q_best = None
    try:
        best = ctx.q_table.best(ctx.session.state)
        if best:
            tool, val = best
            visits = ctx.q_table.get(ctx.session.state, tool)[1]
            q_best = {"tool": tool, "value": round(float(val), 3), "visits": int(visits)}
    except Exception:
        pass

    return {
        "session_id": ctx.session_id,
        "ts": time.time(),
        "state": ctx.session.state.value,
        "state_path": state_path,
        "transitions": ctx.session.transition_count,
        "chain_depth": ctx.session.chain_depth,
        "drift_count": ctx.session.drift_count,
        "last_tool": ctx.session.last_tool,
        "tool_ok": ok,
        "tool_err": total - ok,
        "q_best": q_best,
    }


def _write_eval(session_id: str, eval_data: dict) -> None:
    """Write per-session eval.json and atomically update latest.json.

    Uses tmp+rename for latest.json so session_start never reads a partial file.
    Prunes eval/ to the 50 most recent files.
    """
    try:
        eval_dir = home_root() / "eval"
        eval_dir.mkdir(parents=True, exist_ok=True)

        payload = json.dumps(eval_data, indent=2)
        (eval_dir / f"{session_id}.eval.json").write_text(payload, encoding="utf-8")

        tmp = eval_dir / "latest.tmp.json"
        tmp.write_text(payload, encoding="utf-8")
        tmp.rename(eval_dir / "latest.json")

        # Keep only the 50 most recent eval files
        evals = sorted(eval_dir.glob("*.eval.json"), key=lambda p: p.stat().st_mtime)
        for old in evals[:-50]:
            try:
                old.unlink()
            except Exception:
                pass
    except Exception:
        pass


def _print_eval_box(eval_data: dict) -> None:
    """Print compact self-play summary to stderr. Skipped if MENTAT_QUIET=1.

    Format: strictly structural, no prose, ~140 chars, always prints.
    Signal priority: drift > blocked-at-stop > Q-best > empty-table.
    """
    if os.environ.get("MENTAT_QUIET"):
        return
    try:
        state = eval_data.get("state", "?")
        tx = eval_data.get("transitions", 0)
        ok = eval_data.get("tool_ok", 0)
        err = eval_data.get("tool_err", 0)
        chain = eval_data.get("chain_depth", 0)
        drift = eval_data.get("drift_count", 0)
        q = eval_data.get("q_best") or {}

        if drift > 0:
            signal = f"drift:{drift} topic(s)"
        elif state == "blocked":
            signal = "BLOCKED at stop — check last error"
        elif q:
            signal = f"Q-best@{state}: {q['tool']} ({q['value']:.2f}, n={q['visits']})"
        else:
            signal = "Q-table empty for this state"

        lines = [
            "╔ mentat:eval ╗",
            f"state:{state}  tx:{tx}  tools:{ok + err} ({ok}ok/{err}err)  chain:{chain}",
            signal,
            "╚══════════════╝",
        ]
        print("\n".join(lines), file=sys.stderr)
    except Exception:
        pass


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    ctx.step(Event(event_class=EventClass.STOP))
    end = Insight(
        type=InsightType.SESSION_END,
        state=ctx.session.state.value,
        session_id=ctx.session_id,
        payload={
            "transitions": ctx.session.transition_count,
            "drift_count": ctx.session.drift_count,
            "last_tool": ctx.session.last_tool,
        },
    )
    ctx.bus.emit(end)
    ctx.save()

    # v0.3: self-play eval — always sync, always structural, <50ms total
    eval_data = _compute_eval(ctx)
    _write_eval(ctx.session_id, eval_data)
    _print_eval_box(eval_data)

    # v0.2: webhook mirror (best-effort, never blocks)
    emit_safe(end, session_id=ctx.session_id)
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("stop", main))
