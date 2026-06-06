#!/usr/bin/env python3
"""Gemini BeforeToolSelection hook.

Fires before the LLM picks a tool from the available set. Gemini supports
tool filtering at this stage; Mentat is advisory and only records a NOTE
so the debrief skill can correlate "the model selected tool X when the
Q-best for state Y was tool Z."

We do not filter the tool set — that's a policy concern outside Mentat's
charter. Hook is here for observability and for future Q-driven recommender
work in v0.3+.
"""
from __future__ import annotations

import sys

from _lib import (
    Insight,
    InsightType,
    open_context,
    read_payload,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    available = payload.get("available_tools") or payload.get("tools") or []

    best = ctx.q_table.best(ctx.session.state)
    suggested_tool, suggested_q = (best if best else (None, None))

    ctx.bus.emit(Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        payload={
            "event": "before_tool_selection",
            "available_count": len(available),
            "q_best_tool": suggested_tool,
            "q_best_value": suggested_q,
            "runtime": "gemini",
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("before_tool_selection", main))
