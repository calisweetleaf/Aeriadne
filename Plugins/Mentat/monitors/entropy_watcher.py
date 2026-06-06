#!/usr/bin/env python3
"""Entropy watcher — background monitor for stale EXECUTING sessions.

Mentat's PostToolUse hook bumps chain_depth and updates last_event_at on every
tool call. A session that has been in EXECUTING with chain_depth >= 8 and zero
events for more than five minutes is almost certainly stuck — the model is
spinning on something it can't finish, or the user walked away. Either way
the insight bus should reflect it so the next reflect/debrief surfaces the
moment.

This script is invoked on a cadence by Claude Code's monitor system (see
monitors.json). It does NOT loop internally — it scans once and exits.

Idempotency: each session can only emit a single stale-spike insight per hour.
The idempotency record lives at ~/.mentat/monitors/entropy_seen.json so the
state survives across monitor invocations.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Make the plugin's state_machine package importable.
_HERE = Path(__file__).resolve().parent
_PLUGIN_ROOT = _HERE.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine import Insight, InsightBus, InsightType, State  # noqa: E402
from state_machine.session import Session, home_root  # noqa: E402


STALE_AFTER_S = 5 * 60         # idle threshold inside EXECUTING
CHAIN_DEPTH_THRESHOLD = 8      # depth that qualifies as "deep" / risky
IDEMPOTENT_WINDOW_S = 3600     # at most one spike per session per hour


def _seen_path() -> Path:
    root = home_root() / "monitors"
    root.mkdir(parents=True, exist_ok=True)
    return root / "entropy_seen.json"


def _load_seen() -> dict:
    p = _seen_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_seen(seen: dict) -> None:
    _seen_path().write_text(json.dumps(seen, separators=(",", ":")), encoding="utf-8")


def _iter_sessions(root: Path):
    sdir = root / "sessions"
    if not sdir.exists():
        return
    for f in sdir.glob("*.json"):
        try:
            session = Session.from_json(f.read_text(encoding="utf-8"))
            yield session
        except Exception:
            continue


def scan_once() -> int:
    """Return the number of stale-spike insights emitted on this pass."""
    root = home_root()
    seen = _load_seen()
    now = time.time()
    emitted = 0

    for session in _iter_sessions(root):
        if session.state is not State.EXECUTING:
            continue
        if session.chain_depth < CHAIN_DEPTH_THRESHOLD:
            continue
        idle_s = now - session.last_event_at
        if idle_s < STALE_AFTER_S:
            continue

        last_emit = seen.get(session.session_id, 0)
        if (now - last_emit) < IDEMPOTENT_WINDOW_S:
            continue

        bus = InsightBus(root, session.session_id)
        bus.emit(
            Insight(
                type=InsightType.ENTROPY_SPIKE,
                state=session.state.value,
                payload={
                    "tag": "stale",
                    "reason": "executing_idle",
                    "chain_depth": session.chain_depth,
                    "idle_seconds": round(idle_s, 1),
                    "last_tool": session.last_tool,
                    "threshold_chain_depth": CHAIN_DEPTH_THRESHOLD,
                    "threshold_idle_seconds": STALE_AFTER_S,
                },
            )
        )
        seen[session.session_id] = now
        emitted += 1

    _save_seen(seen)
    return emitted


def main() -> int:
    try:
        emitted = scan_once()
    except Exception as exc:
        print(f"entropy_watcher: error {exc!r}", file=sys.stderr)
        return 1
    print(f"entropy_watcher: emitted={emitted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
