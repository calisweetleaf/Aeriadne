#!/usr/bin/env python3
"""Gemini Notification hook.

Fires on system notifications (per Gemini docs: forward to desktop alerts,
logging). Mentat doesn't forward anywhere — we tag the notification with
its source / kind so the bus has a record. The debrief skill can correlate
notifications with state transitions ("got a rate-limit notice while
EXECUTING, dropped to BLOCKED for 12 minutes").
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

    ctx.bus.emit(Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        payload={
            "event": "notification",
            "kind": payload.get("kind") or payload.get("type", "unknown"),
            "title": payload.get("title", ""),
            "message": (payload.get("message", "") or "")[:200],
            "runtime": "gemini",
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("notification", main))
