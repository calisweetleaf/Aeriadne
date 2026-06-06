#!/usr/bin/env python3
"""Gemini SessionEnd hook.

Gemini distinguishes SessionStart / SessionEnd cleanly (Codex bundles
end-of-turn into Stop and Claude Code has no canonical SessionEnd at all).
Mentat treats SessionEnd as the canonical session-close + handoff write
point on Gemini — same shape as Claude Code's pre_compact.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    home_root,
    open_context,
    read_payload,
)


HANDOFF_TOP_INSIGHTS = 30


def _write_handoff(ctx) -> Path:
    recent = ctx.bus.tail(HANDOFF_TOP_INSIGHTS)
    lines: list[str] = []
    lines.append(f"# Mentat Handoff — session {ctx.session_id} (gemini)")
    lines.append("")
    lines.append(f"- State at end: **{ctx.session.state.value}**")
    lines.append(f"- Transitions so far: {ctx.session.transition_count}")
    lines.append(f"- Chain depth: {ctx.session.chain_depth}")
    lines.append(f"- Last tool: {ctx.session.last_tool} "
                 f"(success={ctx.session.last_tool_success})")
    lines.append(f"- Drift events: {ctx.session.drift_count}")
    lines.append("")
    lines.append("## Q-table top-3 per state")
    lines.append("")
    for state_value in ("planning", "exploring", "executing", "verifying",
                        "reflecting", "blocked"):
        rows = [r for r in ctx.q_table.dump() if r["state"] == state_value][:3]
        if rows:
            joined = ", ".join(
                f"{r['tool']} ({r['value']:.2f}, n={r['visits']})" for r in rows
            )
            lines.append(f"- **{state_value}**: {joined}")
    lines.append("")
    lines.append(f"## Recent {len(recent)} insights")
    lines.append("")
    for ins in recent:
        lines.append(
            f"- `{ins.type.value}` @ state={ins.state or '-'} "
            f"payload={ins.payload}"
        )

    handoff_dir = home_root() / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f"{ctx.session_id}.md"
    handoff_path.write_text("\n".join(lines), encoding="utf-8")
    return handoff_path


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    matcher = payload.get("matcher") or payload.get("source") or "exit"
    ctx.step(Event(event_class=EventClass.STOP,
                   payload={"runtime": "gemini", "matcher": matcher}))
    ctx.bus.emit(Insight(
        type=InsightType.SESSION_END,
        state=ctx.session.state.value,
        payload={
            "transitions": ctx.session.transition_count,
            "drift_count": ctx.session.drift_count,
            "last_tool": ctx.session.last_tool,
            "matcher": matcher,
            "runtime": "gemini",
        },
    ))
    handoff_path = _write_handoff(ctx)
    ctx.bus.emit(Insight(
        type=InsightType.HANDOFF_WRITE,
        state=ctx.session.state.value,
        payload={"path": str(handoff_path),
                 "bytes": handoff_path.stat().st_size,
                 "runtime": "gemini"},
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("session_end", main))
