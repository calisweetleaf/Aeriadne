#!/usr/bin/env python3
"""PostToolUse hook.

Updates Q-table with the reward signal and steps the FSA based on success/error.
Detects entropy spikes (long chains in EXECUTING without VERIFY signals — a
proxy for "we're flailing"). Detects deep success chains and bumps DEEP_CHAIN_BONUS.
"""
from __future__ import annotations

import sys
import time

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    State,
    classify_tool,
    emit_safe,
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
    is_error = bool(tool_response.get("error") or payload.get("error"))
    duration_ms = float(payload.get("duration_ms", 0.0))

    success = not is_error
    ec = EventClass.TOOL_SUCCESS if success else EventClass.TOOL_ERROR
    event = Event(event_class=ec, tool_name=tool_name,
                  payload={"is_error": is_error, "duration_ms": duration_ms})

    ctx.update_chain(success=success)
    prev, nxt, transitioned = ctx.step(event)
    ctx.reward(tool=tool_name, success=success, latency_ms=duration_ms)

    # If the tool was an Agent dispatch, ALSO emit SUBAGENT_DISPATCH (PreToolUse
    # only sees the call itself; we want a discrete return marker too).
    cls = classify_tool(tool_name, tool_input)
    if cls is EventClass.AGENT_TOOL:
        ctx.bus.emit(Insight(
            type=InsightType.SUBAGENT_RETURN,
            state=ctx.session.state.value,
            payload={
                "tool": tool_name,
                "success": success,
                "duration_ms": duration_ms,
            },
        ))

    # Entropy spike: too many EXECUTING tools without a VERIFY breakpoint.
    if ctx.session.state is State.EXECUTING and ctx.session.chain_depth >= ENTROPY_SPIKE_THRESHOLD:
        ctx.bus.emit(Insight(
            type=InsightType.ENTROPY_SPIKE,
            state=ctx.session.state.value,
            payload={
                "chain_depth": ctx.session.chain_depth,
                "threshold": ENTROPY_SPIKE_THRESHOLD,
                "hint": "Run a verification step (tests/lints/typecheck) before continuing.",
            },
        ))
        # Soft signal — don't transition. The model can choose to act on it.

    ctx.save()
    # Webhook emit (v0.2): forward the reward insight to the disler-compatible
    # dashboard. emit_safe never raises and never blocks.
    emit_safe(Insight(
        type=InsightType.REWARD_SIGNAL,
        state=ctx.session.state.value,
        session_id=ctx.session_id,
        payload={
            "tool": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "chain_depth": ctx.session.chain_depth,
        },
    ), session_id=ctx.session_id)
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("post_tool_use", main))
