#!/usr/bin/env python3
"""Codex PostToolUse hook.

Runs after Codex's supported tools (Bash, apply_patch, MCP) produce output —
including Bash commands that exit non-zero. Updates the Q-table with the
reward signal and steps the FSA on success / error.

Also tags entropy spikes: long chains in EXECUTING without a VERIFY signal
are a proxy for "we're flailing without a checkpoint."
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


ENTROPY_SPIKE_THRESHOLD = 8  # > 8 EXECUTING tool uses without VERIFY → spike


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    tool_response = payload.get("tool_response", {}) or {}

    # Codex tool_response shape varies: some tools surface `error` directly,
    # others stash a non-zero `exit_code` (Bash). Treat any of those as failure.
    is_error = bool(
        tool_response.get("error")
        or payload.get("error")
        or (tool_response.get("exit_code", 0) not in (0, None))
    )
    duration_ms = float(payload.get("duration_ms", 0.0))

    success = not is_error
    ec = EventClass.TOOL_SUCCESS if success else EventClass.TOOL_ERROR
    event = Event(event_class=ec, tool_name=tool_name,
                  payload={"is_error": is_error, "duration_ms": duration_ms})

    ctx.update_chain(success=success)
    prev, nxt, transitioned = ctx.step(event)
    ctx.reward(tool=tool_name, success=success, latency_ms=duration_ms)

    cls = classify_tool(tool_name, tool_input)
    if cls is EventClass.AGENT_TOOL:
        ctx.bus.emit(Insight(
            type=InsightType.SUBAGENT_RETURN,
            state=ctx.session.state.value,
            payload={
                "tool": tool_name,
                "success": success,
                "duration_ms": duration_ms,
                "runtime": "codex",
            },
        ))

    if ctx.session.state is State.EXECUTING and ctx.session.chain_depth >= ENTROPY_SPIKE_THRESHOLD:
        ctx.bus.emit(Insight(
            type=InsightType.ENTROPY_SPIKE,
            state=ctx.session.state.value,
            payload={
                "chain_depth": ctx.session.chain_depth,
                "threshold": ENTROPY_SPIKE_THRESHOLD,
                "hint": "Run a verification step (tests/lints/typecheck) before continuing.",
                "runtime": "codex",
            },
        ))

    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("post_tool_use", main))
