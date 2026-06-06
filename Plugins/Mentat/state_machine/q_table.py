"""TD-learning Q-table over (state, tool_name) → expected_value.

Mirrors the Muad'Dib reward constants exactly:
    REWARD_SUCCESS    = +1.0
    REWARD_ERROR      = -0.5
    DEEP_CHAIN_BONUS  = +0.3   (≥ 4 successful tool uses in a row)
    LOW_LATENCY_BONUS = +0.1   (tool returned in < 500 ms)

Update rule (TD(0) with α=0.2, γ=0.8):
    Q(s, a) ← Q(s, a) + α · (r + γ · max_a' Q(s', a') − Q(s, a))

Persisted in ~/.mentat/q_table.sqlite so the table improves across sessions —
a long-horizon learning signal that complements Claude Code's per-session memory.
"""
from __future__ import annotations

import math
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .machine import State

ALPHA = 0.2
GAMMA = 0.8
REWARD_SUCCESS = 1.0
REWARD_ERROR = -0.5
DEEP_CHAIN_BONUS = 0.3
LOW_LATENCY_BONUS = 0.1
DEEP_CHAIN_THRESHOLD = 4
LOW_LATENCY_MS = 500.0


@dataclass
class Reward:
    success: bool
    latency_ms: float = 0.0
    chain_depth: int = 0

    @property
    def value(self) -> float:
        r = REWARD_SUCCESS if self.success else REWARD_ERROR
        if self.success and self.chain_depth >= DEEP_CHAIN_THRESHOLD:
            r += DEEP_CHAIN_BONUS
        if self.success and self.latency_ms > 0 and self.latency_ms < LOW_LATENCY_MS:
            r += LOW_LATENCY_BONUS
        return r


class QTable:
    """SQLite-backed Q-table. Cheap to read/write from a hook process."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS q_values (
                state TEXT NOT NULL,
                tool TEXT NOT NULL,
                value REAL NOT NULL DEFAULT 0.0,
                visits INTEGER NOT NULL DEFAULT 0,
                last_updated REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (state, tool)
            );
            CREATE INDEX IF NOT EXISTS idx_q_state ON q_values(state);
            """
        )
        self._conn.commit()

    def get(self, state: State, tool: str) -> tuple[float, int]:
        cur = self._conn.execute(
            "SELECT value, visits FROM q_values WHERE state = ? AND tool = ?",
            (state.value, tool),
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else (0.0, 0)

    def best(self, state: State, tools: Optional[list[str]] = None) -> Optional[tuple[str, float]]:
        if tools:
            placeholders = ",".join("?" * len(tools))
            cur = self._conn.execute(
                f"SELECT tool, value FROM q_values WHERE state = ? AND tool IN ({placeholders}) "
                f"ORDER BY value DESC LIMIT 1",
                (state.value, *tools),
            )
        else:
            cur = self._conn.execute(
                "SELECT tool, value FROM q_values WHERE state = ? ORDER BY value DESC LIMIT 1",
                (state.value,),
            )
        row = cur.fetchone()
        return (row[0], row[1]) if row else None

    def max_value(self, state: State) -> float:
        cur = self._conn.execute(
            "SELECT MAX(value) FROM q_values WHERE state = ?", (state.value,)
        )
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0

    def update(self, state: State, tool: str, reward: Reward, next_state: State) -> float:
        """TD(0) update. Returns new Q-value."""
        q_old, visits = self.get(state, tool)
        q_next = self.max_value(next_state)
        target = reward.value + GAMMA * q_next
        q_new = q_old + ALPHA * (target - q_old)
        self._conn.execute(
            """
            INSERT INTO q_values (state, tool, value, visits, last_updated)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(state, tool) DO UPDATE SET
                value = excluded.value,
                visits = q_values.visits + 1,
                last_updated = excluded.last_updated
            """,
            (state.value, tool, q_new, time.time()),
        )
        self._conn.commit()
        return q_new

    def thompson_recommend(self, state: State, tools: list[str]) -> Optional[str]:
        """Thompson sampling over Q-values: variance shrinks with visit count.

        Each candidate's score is sampled from Normal(value, 1/sqrt(visits+1)).
        High-value tools with few visits still get exploration weight.
        """
        import random
        candidates: list[tuple[str, float]] = []
        for t in tools:
            v, visits = self.get(state, t)
            sigma = 1.0 / math.sqrt(visits + 1)
            sample = random.gauss(v, sigma)
            candidates.append((t, sample))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def dump(self) -> list[dict]:
        cur = self._conn.execute(
            "SELECT state, tool, value, visits, last_updated FROM q_values "
            "ORDER BY state, value DESC"
        )
        return [
            {"state": r[0], "tool": r[1], "value": r[2], "visits": r[3], "last_updated": r[4]}
            for r in cur.fetchall()
        ]

    def close(self) -> None:
        self._conn.close()
