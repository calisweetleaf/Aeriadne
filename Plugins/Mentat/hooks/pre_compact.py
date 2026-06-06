#!/usr/bin/env python3
"""PreCompact hook.

The most important hook for context survival. Snapshots the state machine,
recent insights, and the Q-table best-actions into ~/.mentat/handoff/<sid>.md.
SessionStart on the post-compact turn reads this file back in and prepends
it as additionalContext so the model resumes with full state-machine memory.

This is the persistence-across-compaction layer — Mentat's answer to the
silent forgetting that wipes most of a session at compaction time.
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


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    ctx.step(Event(event_class=EventClass.PRE_COMPACT))

    recent = ctx.bus.tail(HANDOFF_TOP_INSIGHTS)
    drift_count = ctx.session.drift_count
    transitions = ctx.session.transition_count

    lines: list[str] = []
    lines.append(f"# Mentat Handoff — session {ctx.session_id}")
    lines.append("")
    lines.append(f"- State at compaction: **{ctx.session.state.value}**")
    lines.append(f"- Transitions so far: {transitions}")
    lines.append(f"- Chain depth: {ctx.session.chain_depth}")
    lines.append(f"- Last tool: {ctx.session.last_tool} "
                 f"(success={ctx.session.last_tool_success})")
    lines.append(f"- Drift events: {drift_count}")
    lines.append("")
    lines.append("## Q-table top-3 per state")
    lines.append("")
    for state_value in ("planning", "exploring", "executing", "verifying",
                        "reflecting", "blocked"):
        # Pull top three for this state from the table.
        rows = [r for r in ctx.q_table.dump() if r["state"] == state_value][:3]
        if rows:
            joined = ", ".join(f"{r['tool']} ({r['value']:.2f}, n={r['visits']})" for r in rows)
            lines.append(f"- **{state_value}**: {joined}")
    lines.append("")
    lines.append(f"## Recent {len(recent)} insights")
    lines.append("")
    for ins in recent:
        ts = ins.timestamp
        lines.append(
            f"- `{ins.type.value}` @ state={ins.state or '-'} "
            f"payload={ins.payload}"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for n in ctx.session.notes[-10:]:
        lines.append(f"- {n}")

    handoff_dir = home_root() / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f"{ctx.session_id}.md"
    handoff_path.write_text("\n".join(lines), encoding="utf-8")

    ctx.bus.emit(Insight(
        type=InsightType.HANDOFF_WRITE,
        state=ctx.session.state.value,
        payload={"path": str(handoff_path), "bytes": handoff_path.stat().st_size},
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("pre_compact", main))
