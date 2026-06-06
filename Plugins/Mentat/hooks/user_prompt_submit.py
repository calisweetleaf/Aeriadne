#!/usr/bin/env python3
"""UserPromptSubmit hook.

Two jobs:
    1. Drift detection — match the prompt against scope.md's "Out" list. If a
       deferred topic is mentioned, emit SCOPE_DRIFT and step the FSA into
       DRIFTING (caller can then choose to acknowledge or revise scope).
    2. State-aware context injection — when the FSA is in REFLECTING, BLOCKED,
       or DRIFTING, prepend a short retrospective note with a Q-route hint.

v0.3: PROMPT_SUBMIT fires unconditionally before drift detection — this is the
      DRIFTING→PLANNING escape. Without it, once in DRIFTING the FSA could
      never transition back via normal conversation flow (bug fix).
      Proactive Q-route hint added for PLANNING state (not just stuck states).
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
    write_user_message,
)


def main() -> int:
    payload = read_payload()
    ctx = open_context(payload)
    prompt = payload.get("prompt", "") or payload.get("user_prompt", "")

    # v0.3: always step PROMPT_SUBMIT first — this is the DRIFTING→PLANNING escape.
    # Fires before drift detection so a clean prompt escapes DRIFTING.
    # If drift is detected below, FSA steps to DRIFTING again (correct behaviour).
    ctx.step(Event(event_class=EventClass.PROMPT_SUBMIT))

    # 1. drift detection
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
                payload={"topic": hit.topic, "phrase": hit.matched_phrase},
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

    # 2. state-aware context — stuck states get retrospective Q-hint
    state_msg = ""
    current_state = ctx.session.state.value
    if current_state in ("blocked", "reflecting", "drifting") and ctx.session.last_tool:
        best = ctx.q_table.best(ctx.session.state)
        if best:
            tool, value = best
            state_msg = (
                "<mentat:route-hint>\n"
                f"Current state: {current_state}. "
                f"Last tool: {ctx.session.last_tool} "
                f"(success={ctx.session.last_tool_success}). "
                f"Historical Q-best for this state: {tool} (Q={value:.3f}).\n"
                "</mentat:route-hint>"
            )

    # v0.3: proactive Q-hint at PLANNING — surface best tool before first choice
    elif current_state == "planning" and not drift_msg:
        best = ctx.q_table.best(ctx.session.state)
        if best:
            tool, value = best
            visits = ctx.q_table.get(ctx.session.state, tool)[1]
            if visits > 3 and value > 0.3:
                state_msg = (
                    "<mentat:route-hint>\n"
                    f"Q-best at turn start: {tool} (Q={value:.3f}, {visits} visits).\n"
                    "</mentat:route-hint>"
                )

    ctx.bus.emit(Insight(
        type=InsightType.USER_PROMPT,
        state=ctx.session.state.value,
        payload={"chars": len(prompt), "drift": bool(drift_msg)},
    ))
    ctx.save()

    if drift_msg or state_msg:
        write_user_message("\n".join(x for x in (drift_msg, state_msg) if x))

    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("user_prompt_submit", main))
