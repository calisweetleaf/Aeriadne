"""Disler-compatible webhook envelope.

The disler/claude-code-hooks-multi-agent-observability dashboard accepts a
flat JSON shape per event:

    {
        "source_app":      str   # which app emitted it (we use "mentat")
        "session_id":      str   # opaque session id, stable across a session
        "hook_event_type": str   # discriminator — we map InsightType.value
        "payload":         dict  # event-specific body
        "chat":            list  # optional chat-history snippet (we leave null)
        "summary":         str   # optional one-liner (rendered as a card title)
        "timestamp":       int   # ms since epoch (disler convention)
    }

We add a couple of Mentat-only fields under payload (`state`, `seq`, `id`) so
the dashboard's "raw" view shows the FSA context — they're additive and the
disler UI ignores unknown keys. This keeps Mentat a drop-in replacement for
the disler observability hooks.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class DislerEnvelope:
    source_app: str
    session_id: str
    hook_event_type: str
    payload: dict
    timestamp: int  # ms since epoch
    chat: Optional[list] = None
    summary: Optional[str] = None

    def to_json(self) -> str:
        """Canonical JSON: sorted keys, no whitespace. HMAC is computed over
        exactly this byte sequence so the receiver can re-derive the same hash
        with `json.dumps(parsed, sort_keys=True, separators=(',', ':'))`."""
        d = asdict(self)
        # Strip None-valued optional keys so the wire format matches disler's
        # minimal shape when chat/summary aren't provided.
        if d.get("chat") is None:
            d.pop("chat", None)
        if d.get("summary") is None:
            d.pop("summary", None)
        return json.dumps(d, sort_keys=True, separators=(",", ":"))


def _summarize(insight_type: str, payload: dict, state: Optional[str]) -> str:
    """Best-effort one-line summary for the disler card view."""
    if insight_type == "state_transition":
        return f"{payload.get('prev', '?')} -> {payload.get('next', '?')}"
    if insight_type == "reward_signal":
        sign = "+" if payload.get("success") else "-"
        return f"{sign} {payload.get('tool', '?')} (Q={payload.get('value', 0):+.2f})"
    if insight_type == "scope_drift":
        return f"drift: {payload.get('topic', '?')}"
    if insight_type == "session_end":
        return f"session end (transitions={payload.get('transitions', 0)})"
    if insight_type == "note":
        text = payload.get("text") or payload.get("event") or ""
        return f"note: {text}"[:120]
    if insight_type == "entropy_spike":
        return f"entropy spike (chain={payload.get('chain_depth', 0)})"
    if state:
        return f"{insight_type} @ {state}"
    return insight_type


def build_envelope(insight: Any, session_id: str,
                   source_app: str = "mentat") -> DislerEnvelope:
    """Convert a state_machine.insights.Insight into the disler envelope.

    The Insight object is opaque here — we only touch its public attributes
    (.type, .payload, .state, .timestamp, .seq, .id) so we don't take a hard
    import dependency on the state_machine package. That keeps the webhook
    engine importable from anywhere without dragging in SQLite handles.
    """
    insight_type_value = (
        insight.type.value if hasattr(insight.type, "value") else str(insight.type)
    )
    state = getattr(insight, "state", None)
    base_payload: dict = dict(getattr(insight, "payload", {}) or {})
    # Surface FSA context inside payload so disler's raw view is useful.
    base_payload.setdefault("state", state)
    base_payload.setdefault("seq", getattr(insight, "seq", 0))
    base_payload.setdefault("insight_id", getattr(insight, "id", ""))

    ts_secs = float(getattr(insight, "timestamp", time.time()))
    return DislerEnvelope(
        source_app=source_app,
        session_id=session_id,
        hook_event_type=insight_type_value,
        payload=base_payload,
        timestamp=int(ts_secs * 1000),
        chat=None,
        summary=_summarize(insight_type_value, base_payload, state),
    )
