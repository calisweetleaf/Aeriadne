"""Session state persistence.

Hooks are independent processes — there's no shared memory between firings, so
the state machine has to be reconstructed every time. This module centralizes
that load → mutate → save dance.

Layout under ${CLAUDE_PROJECT_DIR}/.mentat/ (per-project) and ~/.mentat/ (global):

    ~/.mentat/
        q_table.sqlite             # global TD-learning table, cross-session
        sessions/<session-id>.json # per-session state machine + counters
        insights/<session-id>.jsonl # per-session insight bus
        handoff/<session-id>.md    # latest pre-compact / pre-stop snapshot

    ${CLAUDE_PROJECT_DIR}/.mentat/
        active_session.json        # pointer to current session id
        local_q_table.sqlite       # project-local Q-table (overlays global)
        scope.md                   # current scope declaration (drift detector reads this)
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from .machine import State


def home_root() -> Path:
    root = Path(os.environ.get("MENTAT_HOME", Path.home() / ".mentat"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_root() -> Optional[Path]:
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if not proj:
        return None
    root = Path(proj) / ".mentat"
    root.mkdir(parents=True, exist_ok=True)
    return root


@dataclass
class Session:
    session_id: str
    state: State = State.PLANNING
    chain_depth: int = 0
    drift_count: int = 0
    transition_count: int = 0
    started_at: float = field(default_factory=time.time)
    last_event_at: float = field(default_factory=time.time)
    last_tool: Optional[str] = None
    last_tool_success: Optional[bool] = None
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        d = asdict(self)
        d["state"] = self.state.value
        return json.dumps(d, separators=(",", ":"))

    @classmethod
    def from_json(cls, raw: str) -> "Session":
        d = json.loads(raw)
        d["state"] = State(d["state"])
        return cls(**d)


def session_path(session_id: str) -> Path:
    return home_root() / "sessions" / f"{session_id}.json"


def load_session(session_id: str) -> Session:
    p = session_path(session_id)
    if p.exists():
        return Session.from_json(p.read_text(encoding="utf-8"))
    s = Session(session_id=session_id)
    save_session(s)
    return s


def save_session(s: Session) -> None:
    p = session_path(s.session_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s.to_json(), encoding="utf-8")


def active_session_id() -> Optional[str]:
    """Read the project-local active session pointer, falling back to env."""
    env = os.environ.get("CLAUDE_SESSION_ID")
    if env:
        return env
    proj = project_root()
    if proj:
        p = proj / "active_session.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("session_id")
            except Exception:
                return None
    return None


def set_active_session(session_id: str) -> None:
    proj = project_root()
    if proj is None:
        return
    p = proj / "active_session.json"
    p.write_text(json.dumps({"session_id": session_id, "set_at": time.time()}), encoding="utf-8")
