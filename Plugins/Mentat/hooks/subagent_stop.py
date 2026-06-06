#!/usr/bin/env python3
"""SubagentStop hook.

Tags the return — we already emit SUBAGENT_RETURN from PostToolUse for Agent
calls, but SubagentStop fires even for sub-agents launched via skill frontmatter
or other indirect paths, so it's the most reliable surface.
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
    ctx.step(Event(event_class=EventClass.SUBAGENT_RETURN,
                   payload={"success": success}))
    ctx.bus.emit(Insight(
        type=InsightType.SUBAGENT_RETURN,
        state=ctx.session.state.value,
        payload={
            "subagent_name": payload.get("name", ""),
            "success": success,
            "duration_ms": payload.get("duration_ms", 0),
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("subagent_stop", main))
