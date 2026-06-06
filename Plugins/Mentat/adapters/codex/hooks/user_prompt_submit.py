#!/usr/bin/env python3
"""Codex UserPromptSubmit hook.

Two responsibilities, same as the Claude Code equivalent:
    1. Drift detection — match the prompt against scope.md's "Out" list. If
       a deferred topic is mentioned, emit SCOPE_DRIFT and step the FSA into
       DRIFTING.
    2. State-aware context injection — when the FSA is in REFLECTING or
       BLOCKED, prepend a short retrospective with the Q-best tool for the
       current state.

Codex's UserPromptSubmit accepts the same JSON envelope Claude Code uses:
`hookSpecificOutput.additionalContext` becomes a system note attached to the
next model turn.
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

    # 1. drift detection against scope.md
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
                         "runtime": "codex"},
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

    # 2. state-aware Q-route hint when stalled
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
                 "runtime": "codex"},
    ))
    ctx.save()

    if drift_msg or state_msg:
        write_additional_context("\n".join(x for x in (drift_msg, state_msg) if x))

    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("user_prompt_submit", main))
