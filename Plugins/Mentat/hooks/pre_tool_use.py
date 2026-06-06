#!/usr/bin/env python3
"""PreToolUse hook.

Runs before every tool invocation. Three jobs:
    1. Pre-classify the tool into READ / WRITE / EXEC / AGENT for the FSA.
    2. Drift-check the tool input (in case the prompt was clean but the tool
       inputs reveal scope drift, e.g. an Edit on a deferred-topic file).
    3. State-machine guard: if state is DRIFTING, deny destructive tools
       until the user re-affirms scope. This is the only place the plugin
       can actually block work — exit 2 (or JSON deny) prevents the tool.

The guard is conservative — it only denies WRITE/EXEC tools while DRIFTING.
READ tools and AGENT dispatches are always allowed (so Claude can use
sub-agents to research a way out).
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
    detect_drift,
    open_context,
    parse_scope,
    read_payload,
    scope_path,
    write_decision,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    ec = classify_tool(tool_name, tool_input)
    event = Event(event_class=ec, tool_name=tool_name, payload=tool_input)

    # 1. drift on tool input (combine string fields)
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
                payload={"topic": hit.topic, "phrase": hit.matched_phrase},
            ))

    # 2. guard: deny write/exec while DRIFTING
    if ctx.session.state is State.DRIFTING and ec in (
        EventClass.WRITE_TOOL, EventClass.EXEC_TOOL,
    ):
        ctx.bus.emit(Insight(
            type=InsightType.NOTE,
            state=ctx.session.state.value,
            payload={
                "guard": "deny_write_in_drifting",
                "tool": tool_name,
            },
        ))
        ctx.save()
        write_decision(
            "deny",
            "Mentat: state machine is in DRIFTING. The current request touches a "
            "deferred topic. Reaffirm scope (update .mentat/scope.md or note the "
            "exception in chat) before performing writes or shell side-effects."
        )
        return 0

    # 3. step normally; emit a Q-route hint
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
                },
            ))

    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("pre_tool_use", main))
