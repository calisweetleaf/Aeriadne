#!/usr/bin/env python3
"""Gemini BeforeTool hook.

Runs before a tool executes (write_file, replace, run_shell_command, MCP).
Three jobs, same as Codex's PreToolUse:
    1. Classify the tool into READ / WRITE / EXEC / AGENT.
    2. Drift-check the tool input (string values flattened against scope.md).
    3. Hard guard: deny WRITE/EXEC tools while DRIFTING via exit-2 + stderr
       (Gemini's canonical System Block path).

Per Gemini docs, the preferred clean block is exit 0 with
`{"decision": "deny"}` JSON — Mentat uses exit 2 for symmetry with Claude
Code and Codex (so the same deny reason is surfaced everywhere). Both work.
"""
from __future__ import annotations

import sys

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    State,
    classify_tool,
    deny_and_exit,
    detect_drift,
    open_context,
    parse_scope,
    read_payload,
    scope_path,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    ec = classify_tool(tool_name, tool_input)
    event = Event(event_class=ec, tool_name=tool_name, payload=tool_input)

    # 1. drift on tool input
    sp = scope_path()
    if sp and sp.exists():
        _, out_topics = parse_scope(sp)
        flat = " ".join(str(v) for v in tool_input.values() if isinstance(v, str))
        hit = detect_drift(flat, out_topics)
        if hit:
            ctx.bus.emit_drift(topic=hit.topic, deferred_at=str(sp),
                               evidence=hit.snippet)
            ctx.step(Event(
                event_class=EventClass.SCOPE_DRIFT_DETECTED,
                payload={"topic": hit.topic, "phrase": hit.matched_phrase,
                         "runtime": "gemini"},
            ))

    # 2. guard
    if ctx.session.state is State.DRIFTING and ec in (
        EventClass.WRITE_TOOL, EventClass.EXEC_TOOL,
    ):
        ctx.bus.emit(Insight(
            type=InsightType.NOTE,
            state=ctx.session.state.value,
            payload={
                "guard": "deny_write_in_drifting",
                "tool": tool_name,
                "runtime": "gemini",
            },
        ))
        ctx.save()
        deny_and_exit(
            "Mentat: state machine is in DRIFTING. The current request touches a "
            "deferred topic. Reaffirm scope (update .mentat/scope.md or note the "
            "exception in chat) before performing writes or shell side-effects."
        )

    # 3. step + Q-route hint
    prev, nxt, transitioned = ctx.step(event)
    best = ctx.q_table.best(ctx.session.state)
    if best:
        tool, value = best
        if tool != tool_name and value > 0.5:
            ctx.bus.emit(Insight(
                type=InsightType.Q_ROUTE_HINT,
                state=ctx.session.state.value,
                payload={
                    "current_tool": tool_name,
                    "suggested_tool": tool,
                    "suggested_q": value,
                    "runtime": "gemini",
                },
            ))

    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("before_tool", main))
