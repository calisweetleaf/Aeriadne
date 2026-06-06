#!/usr/bin/env python3
"""Codex PreToolUse hook.

Runs before Codex invokes a tool (Bash, apply_patch, or any MCP tool). Three
jobs:
    1. Classify the tool into READ / WRITE / EXEC / AGENT for the FSA.
    2. Drift-check the tool input — a clean prompt can still hide a deferred
       file path inside the tool arguments.
    3. Hard guard: if the FSA is in DRIFTING, deny WRITE/EXEC tools via the
       canonical Codex deny path (exit 2 + stderr reason). READ and AGENT
       tools are always allowed so the model can investigate its way out.

Codex's docs spell out that PreToolUse runs against Bash, apply_patch, and
MCP tools — it is *not* a hard enforcement boundary because the model can
sometimes route around it. We still use it as the cheapest first defense.
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

    # 1. drift on tool input (flatten string fields)
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
                         "runtime": "codex"},
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
                "runtime": "codex",
            },
        ))
        ctx.save()
        deny_and_exit(
            "Mentat: state machine is in DRIFTING. The current request touches a "
            "deferred topic. Reaffirm scope (update .mentat/scope.md or note the "
            "exception in chat) before performing writes or shell side-effects."
        )

    # 3. step normally; emit a Q-route hint when the Q-best differs from
    #    the chosen tool by a non-trivial margin.
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
                    "runtime": "codex",
                },
            ))

    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("pre_tool_use", main))
