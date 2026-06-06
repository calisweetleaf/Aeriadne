#!/usr/bin/env python3
"""StopFailure hook.

Fires when Claude Code aborts a turn for an out-of-band reason (rate limit,
authentication failure, content policy, etc.). The matcher payload tells us
which kind. This is the right place to log a TOOL_FAILURE-class insight tagged
with the reason so debrief / triage can correlate.
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
    reason = payload.get("matcher", "unknown")
    ctx.step(Event(event_class=EventClass.STOP_FAILURE,
                   payload={"reason": reason}))
    ctx.bus.emit(Insight(
        type=InsightType.TOOL_FAILURE,
        state=ctx.session.state.value,
        payload={"reason": reason, "scope": "stop_failure"},
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("stop_failure", main))
