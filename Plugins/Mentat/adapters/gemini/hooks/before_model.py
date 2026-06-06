#!/usr/bin/env python3
"""Gemini BeforeModel hook.

Fires before each request to the model. Mentat records the model slug and
the current FSA state as a NOTE — useful for the debrief skill to correlate
"model x in state y took z transitions to verify."

We don't mutate or swap models here; the hook is advisory.
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
    model = payload.get("model", "")

    ctx.bus.emit(Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        payload={
            "event": "before_model",
            "model": model,
            "chain_depth": ctx.session.chain_depth,
            "runtime": "gemini",
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("before_model", main))
