#!/usr/bin/env python3
"""Gemini SessionStart hook.

Fires on every Gemini session boot (startup / resume / clear — exact-string
matchers in Gemini's settings.json). Loads or creates the session record,
emits SESSION_START, and if a handoff.md exists from a prior compaction or
session end, prepends it via additionalContext so the model resumes with
substrate memory.
"""
from __future__ import annotations

import sys

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    home_root,
    open_context,
    read_payload,
    write_additional_context,
)


def main() -> int:
    payload = read_payload()
    matcher = payload.get("matcher") or payload.get("source") or "startup"
    ctx = open_context(payload)

    handoff = home_root() / "handoff" / f"{ctx.session_id}.md"
    handoff_text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""

    ctx.step(Event(event_class=EventClass.SESSION_START,
                   payload={"matcher": matcher, "runtime": "gemini"}))
    ctx.bus.emit(Insight(
        type=InsightType.SESSION_START,
        state=ctx.session.state.value,
        payload={"matcher": matcher, "runtime": "gemini",
                 "had_handoff": bool(handoff_text)},
    ))
    ctx.save()

    if handoff_text:
        ctx.bus.emit(Insight(
            type=InsightType.HANDOFF_READ,
            state=ctx.session.state.value,
            payload={"bytes": len(handoff_text), "runtime": "gemini"},
        ))
        msg = (
            "<mentat:handoff>\n"
            "Mentat detected a prior session handoff (compaction or stop). "
            "Prior state machine and key insights:\n\n"
            f"{handoff_text}\n"
            "</mentat:handoff>"
        )
        write_additional_context(msg)

    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("session_start", main))
