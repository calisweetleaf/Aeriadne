#!/usr/bin/env python3
"""Gemini AfterAgent hook.

Fires when the agent loop ends for a turn. Per Gemini docs, AfterAgent can
force a retry or halt — Mentat doesn't use either; we record the loop close
and let the natural flow continue. The hook is the cleanest place to tag a
TURN_END insight (distinct from SessionEnd which only fires on real exit).
"""
from __future__ import annotations

import sys

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    open_context,
    read_payload,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    success = bool(payload.get("success", True))

    ctx.bus.emit(Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        payload={
            "event": "after_agent",
            "success": success,
            "transitions_this_turn": ctx.session.transition_count,
            "runtime": "gemini",
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("after_agent", main))
