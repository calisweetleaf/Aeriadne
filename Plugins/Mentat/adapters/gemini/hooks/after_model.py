#!/usr/bin/env python3
"""Gemini AfterModel hook.

Fires after the model returns. Gemini supports response filter / redact via
this hook; Mentat is advisory and only tags an insight with the response
shape (token-ish length, finish reason if surfaced) so the bus has a
record of model turns interleaved with tool turns.
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
    response = payload.get("response", {}) or {}
    model = payload.get("model", "")
    text = ""
    if isinstance(response, dict):
        text = response.get("text", "") or response.get("content", "")
    elif isinstance(response, str):
        text = response

    ctx.bus.emit(Insight(
        type=InsightType.NOTE,
        state=ctx.session.state.value,
        payload={
            "event": "after_model",
            "model": model,
            "response_chars": len(text or ""),
            "finish_reason": response.get("finish_reason") if isinstance(response, dict) else None,
            "runtime": "gemini",
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("after_model", main))
