#!/usr/bin/env python3
"""SubagentStart hook.

Tags the dispatch with sub-agent name + model + initial prompt length. Goes into
the insight bus so the debrief skill can later show "in this session you spawned
6 sub-agents, of which 4 succeeded, costing 1m20s of wall time, with these
specialty distributions."
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
        type=InsightType.SUBAGENT_DISPATCH,
        state=ctx.session.state.value,
        payload={
            "subagent_type": payload.get("subagent_type", "default"),
            "subagent_name": payload.get("name", payload.get("description", "")),
            "model": payload.get("model", "inherit"),
            "prompt_len": len(payload.get("prompt", "") or ""),
        },
    ))
    ctx.save()
    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("subagent_start", main))
