#!/usr/bin/env python3
"""Gemini BeforeAgent hook.

Fires after the user submits a prompt but before agent planning. Gemini's
closest analog to Claude Code's UserPromptSubmit. Two jobs:
    1. Drift detection — scope.md "Out" list vs. prompt text.
    2. State-aware context — when the FSA is in REFLECTING or BLOCKED,
       inject a short retrospective with the Q-best tool.

Per Gemini docs, BeforeAgent is the "Block Turn / Context" surface — same
JSON envelope works for context injection. We never block the turn here
(drift trips the FSA into DRIFTING but lets the turn run so the agent can
acknowledge); the hard block lives in before_tool.py.
"""
from __future__ import annotations

import sys

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    detect_drift,
    open_context,
    parse_scope,
    read_payload,
    scope_path,
    write_additional_context,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    prompt = payload.get("prompt", "") or payload.get("user_prompt", "")

    drift_msg = ""
    sp = scope_path()
    if sp and sp.exists() and prompt:
        _, out_topics = parse_scope(sp)
        hit = detect_drift(prompt, out_topics)
        if hit:
            ctx.bus.emit_drift(topic=hit.topic, deferred_at=str(sp),
                               evidence=hit.snippet)
            ctx.step(Event(
                event_class=EventClass.SCOPE_DRIFT_DETECTED,
                payload={"topic": hit.topic, "phrase": hit.matched_phrase,
                         "runtime": "gemini"},
            ))
            ctx.session.drift_count += 1
            drift_msg = (
                "<mentat:scope-drift>\n"
                f"Mentat detected a deferred-topic mention. Topic: {hit.topic}\n"
                f"Matched phrase: {hit.matched_phrase!r}\n"
                f"Snippet: {hit.snippet!r}\n"
                "Acknowledge before proceeding, or update .mentat/scope.md if "
                "the user explicitly reopened this topic.\n"
                "</mentat:scope-drift>"
            )

    state_msg = ""
    if ctx.session.state.value in ("blocked", "reflecting") and ctx.session.last_tool:
        best = ctx.q_table.best(ctx.session.state)
        if best:
            tool, value = best
            state_msg = (
                "<mentat:route-hint>\n"
                f"Current state: {ctx.session.state.value}. "
                f"Last tool: {ctx.session.last_tool} "
                f"(success={ctx.session.last_tool_success}). "
                f"Historical Q-best for this state: {tool} (Q={value:.3f}).\n"
                "</mentat:route-hint>"
            )

    ctx.bus.emit(Insight(
        type=InsightType.USER_PROMPT,
        state=ctx.session.state.value,
        payload={"chars": len(prompt), "drift": bool(drift_msg),
                 "runtime": "gemini"},
    ))
    ctx.save()

    if drift_msg or state_msg:
        write_additional_context("\n".join(x for x in (drift_msg, state_msg) if x))

    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("before_agent", main))
