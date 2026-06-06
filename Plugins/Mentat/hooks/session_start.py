#!/usr/bin/env python3
"""SessionStart hook.

Fires on every session boot (startup / resume / clear / compact-resume).
Loads or creates the session record, emits the SESSION_START insight, and
injects a structured boot context block so the model sees prior state on resume.

v0.3: richer boot injection —
    - <mentat:handoff>  compaction snapshot (existing)
    - <mentat:boot>     warm/cold signal from CTMv3 + prior structural eval
      Both blocks are composed into a single write_user_message() call.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from _lib import (
    Event,
    EventClass,
    Insight,
    InsightType,
    home_root,
    open_context,
    read_payload,
    write_user_message,
)


def _read_eval(session_id: str) -> dict:
    """Read prior session eval. Falls back to latest.json for cross-session boots."""
    eval_dir = home_root() / "eval"
    for p in (eval_dir / f"{session_id}.eval.json", eval_dir / "latest.json"):
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
    return {}


def _read_ctm_state() -> dict:
    """Read CTMv3 .sovereign/session_state.json for warm/cold boot signal.

    Returns {} on any failure — Mentat treats absence as cold start.
    Only trusted if schema field starts with 'ctmv3.session_state'.
    """
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if not proj:
        return {}
    p = Path(proj) / ".sovereign" / "session_state.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if str(data.get("schema", "")).startswith("ctmv3.session_state"):
            return data
    except Exception:
        pass
    return {}


def main() -> int:
    payload = read_payload()
    matcher = payload.get("matcher", "startup")
    ctx = open_context(payload)

    handoff = home_root() / "handoff" / f"{ctx.session_id}.md"
    handoff_text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""

    ctx.step(Event(event_class=EventClass.SESSION_START,
                   payload={"matcher": matcher}))
    ctx.bus.emit(Insight(
        type=InsightType.SESSION_START,
        state=ctx.session.state.value,
        payload={"matcher": matcher, "had_handoff": bool(handoff_text)},
    ))
    ctx.save()

    # Compose injection — only write_user_message once (2KB cap applies globally)
    parts: list[str] = []

    if handoff_text:
        ctx.bus.emit(Insight(
            type=InsightType.HANDOFF_READ,
            state=ctx.session.state.value,
            payload={"bytes": len(handoff_text)},
        ))
        parts.append(
            "<mentat:handoff>\n"
            "Mentat detected a prior session handoff (compaction or stop). "
            "Prior state machine and key insights:\n\n"
            f"{handoff_text}\n"
            "</mentat:handoff>"
        )

    # v0.3: prior eval + CTMv3 warm/cold
    prior = _read_eval(ctx.session_id)
    ctm = _read_ctm_state()

    if prior or ctm:
        boot_lines: list[str] = []

        warm = bool(ctm.get("state") or ctm.get("last_agent"))
        boot_tag = "warm" if warm else "cold"
        workspace = ctm.get("workspace", "")
        boot_lines.append(
            f"boot:{boot_tag}" + (f"  workspace:{workspace}" if workspace else "")
        )

        if prior:
            path_str = "→".join(prior.get("state_path", [prior.get("state", "?")]))
            ok = prior.get("tool_ok", 0)
            err = prior.get("tool_err", 0)
            boot_lines.append(
                f"prior:{path_str}  tools:{ok + err}({ok}ok/{err}err)"
                f"  drift:{prior.get('drift_count', 0)}"
            )
            q = prior.get("q_best") or {}
            if q:
                boot_lines.append(
                    f"q_best:{q['tool']} ({q['value']:.2f}, n={q['visits']})"
                )

        parts.append("<mentat:boot>\n" + "\n".join(boot_lines) + "\n</mentat:boot>")

    if parts:
        write_user_message("\n".join(parts))

    return 0


if __name__ == "__main__":
    from _lib import safe_main
    sys.exit(safe_main("session_start", main))
