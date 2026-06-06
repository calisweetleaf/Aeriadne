#!/usr/bin/env python3
"""Codex PermissionRequest hook.

Codex-specific event (no Claude Code analog). Fires when Codex is about to
ask the user for approval — shell escalation, managed-network approval, or
any tool the active policy gates.

Mentat doesn't decide the request (we let the normal approval prompt run);
we tag it as PERMISSION_REQUEST in the insight bus and, when the FSA is
DRIFTING + the request is a write/exec, we proactively emit a Q-route hint
suggesting safer alternatives the Q-table has historically rewarded.
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
    open_context,
    read_payload,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    ec = classify_tool(tool_name, tool_input)

    # Tag the request itself — useful for triage / debrief.
    ctx.bus.emit(Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        payload={
            "event": "permission_request",
            "tool": tool_name,
            "event_class": ec.value,
            "runtime": "codex",
        },
    ))

    # If we're DRIFTING and Codex is escalating, surface a Q-best hint
    # so the user sees that the FSA had a safer historical alternative.
    if ctx.session.state is State.DRIFTING and ec in (
        EventClass.WRITE_TOOL, EventClass.EXEC_TOOL,
    ):
        best = ctx.q_table.best(ctx.session.state)
        if best:
            tool, value = best
            ctx.bus.emit(Insight(
                type=InsightType.Q_ROUTE_HINT,
                state=ctx.session.state.value,
                payload={
                    "trigger": "permission_request_during_drift",
                    "requested_tool": tool_name,
                    "suggested_tool": tool,
                    "suggested_q": value,
                    "runtime": "codex",
                },
            ))

    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("permission_request", main))
