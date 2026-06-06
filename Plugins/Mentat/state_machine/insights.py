"""Structured insight bus.

Every hook firing emits zero or more insights to a session-scoped JSONL file
under ~/.mentat/insights/<session-id>.jsonl. The format is line-delimited JSON,
append-only, indexed by sequence number. Consumers (the CLI inspector, the
debrief skill, the MCP shim) tail the file or query it via SQLite mirror.

Insight types are coarse and additive — adding a new type never breaks
existing consumers. Drop the unknown type silently if a reader doesn't know it.
"""
from __future__ import annotations

import enum
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


class InsightType(str, enum.Enum):
    STATE_TRANSITION = "state_transition"
    DECISION = "decision"
    CONTRADICTION = "contradiction"
    SCOPE_DRIFT = "scope_drift"
    SOURCE_GROUNDED = "source_grounded"
    SOURCE_UNGROUNDED = "source_ungrounded"
    REWARD_SIGNAL = "reward_signal"
    SUBAGENT_DISPATCH = "subagent_dispatch"
    SUBAGENT_RETURN = "subagent_return"
    TOOL_FAILURE = "tool_failure"
    ENTROPY_SPIKE = "entropy_spike"
    Q_ROUTE_HINT = "q_route_hint"
    HANDOFF_WRITE = "handoff_write"
    HANDOFF_READ = "handoff_read"
    USER_PROMPT = "user_prompt"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    NOTE = "note"


@dataclass
class Insight:
    type: InsightType
    payload: dict = field(default_factory=dict)
    state: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    seq: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: Optional[str] = None

    def to_json(self) -> str:
        d = asdict(self)
        d["type"] = self.type.value
        return json.dumps(d, separators=(",", ":"))


class InsightBus:
    """Append-only JSONL insight log + a small SQLite mirror for fast queries."""

    def __init__(self, root: Path, session_id: str):
        self.root = root
        self.session_id = session_id
        self.jsonl_path = root / "insights" / f"{session_id}.jsonl"
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, insight: Insight) -> Insight:
        if insight.session_id is None:
            insight.session_id = self.session_id
        # Sequence comes from line count — cheap and append-safe.
        insight.seq = self._next_seq()
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(insight.to_json() + "\n")
        return insight

    def emit_state_transition(self, prev: str, nxt: str, trigger: str) -> Insight:
        return self.emit(
            Insight(
                type=InsightType.STATE_TRANSITION,
                state=nxt,
                payload={"prev": prev, "next": nxt, "trigger": trigger},
            )
        )

    def emit_reward(self, state: str, tool: str, value: float, success: bool) -> Insight:
        return self.emit(
            Insight(
                type=InsightType.REWARD_SIGNAL,
                state=state,
                payload={"tool": tool, "value": value, "success": success},
            )
        )

    def emit_drift(self, topic: str, deferred_at: Optional[str], evidence: str) -> Insight:
        return self.emit(
            Insight(
                type=InsightType.SCOPE_DRIFT,
                payload={"topic": topic, "deferred_at": deferred_at, "evidence": evidence},
            )
        )

    def tail(self, n: int = 50) -> list[Insight]:
        if not self.jsonl_path.exists():
            return []
        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        out: list[Insight] = []
        for raw in lines[-n:]:
            try:
                d = json.loads(raw)
                d["type"] = InsightType(d["type"])
                out.append(Insight(**d))
            except Exception:
                continue
        return out

    def query(self, type: Optional[InsightType] = None, state: Optional[str] = None,
              limit: int = 100) -> list[Insight]:
        if not self.jsonl_path.exists():
            return []
        out: list[Insight] = []
        for raw in self.jsonl_path.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(raw)
                if type is not None and d.get("type") != type.value:
                    continue
                if state is not None and d.get("state") != state:
                    continue
                d["type"] = InsightType(d["type"])
                out.append(Insight(**d))
                if len(out) >= limit:
                    break
            except Exception:
                continue
        return out

    def _next_seq(self) -> int:
        if not self.jsonl_path.exists():
            return 0
        # Rough: count lines. A SQLite mirror would be O(1) but this keeps the dep
        # surface tiny (stdlib only) and is fine for plugin hook latency budgets.
        with self.jsonl_path.open("rb") as f:
            return sum(1 for _ in f)
