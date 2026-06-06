#!/usr/bin/env python3
"""Drift watcher — background monitor for prolonged DRIFTING sessions.

When the scope-drift detector fires, the state machine moves the session into
DRIFTING. The only way out is an explicit PROMPT_SUBMIT — meaning the user
needs to acknowledge or re-scope. If the user walked away (or ignored the
banner) the session can sit in DRIFTING indefinitely, which silently degrades
every subsequent reflection because the FSA is wedged.

This monitor emits a single NOTE insight per session per hour reminding the
user that a session has been in DRIFTING for more than 30 minutes and asking
them to acknowledge or update scope.md.

Invoked by Claude Code's monitor system on a cadence — runs once and exits.
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


STUCK_AFTER_S = 30 * 60        # 30 minutes in DRIFTING qualifies as stuck
IDEMPOTENT_WINDOW_S = 3600     # at most one note per session per hour


def _seen_path() -> Path:
    root = home_root() / "monitors"
    root.mkdir(parents=True, exist_ok=True)
    return root / "drift_seen.json"


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
    root = home_root()
    seen = _load_seen()
    now = time.time()
    emitted = 0

    for session in _iter_sessions(root):
        if session.state is not State.DRIFTING:
            continue
        stuck_for = now - session.last_event_at
        if stuck_for < STUCK_AFTER_S:
            continue

        last_emit = seen.get(session.session_id, 0)
        if (now - last_emit) < IDEMPOTENT_WINDOW_S:
            continue

        bus = InsightBus(root, session.session_id)
        bus.emit(
            Insight(
                type=InsightType.NOTE,
                state=session.state.value,
                payload={
                    "tag": "drift-stuck",
                    "reason": "drifting_unacknowledged",
                    "stuck_seconds": round(stuck_for, 1),
                    "drift_count": session.drift_count,
                    "message": (
                        "Session has been DRIFTING for "
                        f"{int(stuck_for // 60)} minutes. Either acknowledge "
                        "the drift with a fresh prompt, or update "
                        ".mentat/scope.md to reopen the deferred topic."
                    ),
                    "threshold_stuck_seconds": STUCK_AFTER_S,
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
        print(f"drift_watcher: error {exc!r}", file=sys.stderr)
        return 1
    print(f"drift_watcher: emitted={emitted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
