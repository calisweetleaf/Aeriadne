#!/usr/bin/env python3
"""PostCompact hook.

Steps the FSA out of COMPACTING into REFLECTING, emits the resume marker, and
relies on the SessionStart hook on the next turn to actually inject the
handoff text via additionalContext (PostCompact does not get to write to
additionalContext on most clients — the next user-prompt-submit / session-start
is the canonical injection point).
"""
from __future__ import annotations

import sys

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    emit_safe,
    open_context,
    read_payload,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    ctx.step(Event(event_class=EventClass.POST_COMPACT))
    note = Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        session_id=ctx.session_id,
        payload={"event": "post_compact", "compacted_size": payload.get("compacted_size", 0)},
    )
    ctx.bus.emit(note)
    ctx.save()
    # Webhook emit (v0.2): mirror the NOTE to disler dashboards.
    emit_safe(note, session_id=ctx.session_id)
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("post_compact", main))
