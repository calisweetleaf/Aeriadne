"""SQLite-backed dead-letter queue for webhook envelopes.

When emitter exhausts its in-process retries (3 attempts with 1s/2s/4s
backoff), the envelope lands here. A separate `drain()` call (driven by the
`mentat-webhooks drain` CLI or a cron) re-emits eligible rows on a slower
schedule (10min / 1h / 6h / 24h) and gives up after 5 total attempts.

Schema:
    id INTEGER PRIMARY KEY
    idempotency_key TEXT UNIQUE      — sha256(session_id + seq + type)
    endpoint_url TEXT                — disler may have multiple endpoints
    envelope_json TEXT               — canonical JSON body (what got signed)
    error TEXT                       — last failure reason
    attempts INTEGER                 — total send attempts so far
    first_failed_at REAL             — epoch seconds
    last_failed_at REAL              — epoch seconds
    next_retry_at REAL               — epoch seconds; drain() respects this
    status TEXT                      — 'pending' | 'dead'
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional


MAX_ATTEMPTS = 5

# Backoff schedule for DLQ retries (applied *after* an attempt fails).
# Index = number of total attempts already made.
#   1 failed attempt   -> wait 10 minutes
#   2 failed attempts  -> wait 1 hour
#   3 failed attempts  -> wait 6 hours
#   4 failed attempts  -> wait 24 hours
#   5 failed attempts  -> dead (no more retries)
DLQ_BACKOFF_SECONDS = (
    10 * 60,
    60 * 60,
    6 * 60 * 60,
    24 * 60 * 60,
)


def _dlq_path() -> Path:
    root = Path(os.environ.get("MENTAT_HOME", Path.home() / ".mentat"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "webhook_dlq.sqlite"


def _conn(path: Optional[Path] = None) -> sqlite3.Connection:
    p = path or _dlq_path()
    c = sqlite3.connect(str(p), timeout=2.0)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dlq (
            id INTEGER PRIMARY KEY,
            idempotency_key TEXT UNIQUE,
            endpoint_url TEXT,
            envelope_json TEXT,
            error TEXT,
            attempts INTEGER NOT NULL DEFAULT 1,
            first_failed_at REAL,
            last_failed_at REAL,
            next_retry_at REAL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    c.commit()
    return c


def _next_retry_at(now: float, attempts: int) -> float:
    # attempts is the number of attempts already made (post-increment).
    # attempts=1 -> first DLQ wait (10min), attempts=4 -> last wait (24h).
    idx = max(0, min(len(DLQ_BACKOFF_SECONDS) - 1, attempts - 1))
    return now + DLQ_BACKOFF_SECONDS[idx]


def enqueue(envelope_json: str, idempotency_key: str, endpoint_url: str,
            error: str, db_path: Optional[Path] = None) -> None:
    """Insert (or bump attempts on) a failed envelope.

    Uniqueness is on idempotency_key — re-emitting the same logical event
    after a restart updates the same row rather than spamming the DLQ.
    """
    now = time.time()
    with _conn(db_path) as c:
        existing = c.execute(
            "SELECT id, attempts FROM dlq WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing is None:
            c.execute(
                """
                INSERT INTO dlq (idempotency_key, endpoint_url, envelope_json,
                                 error, attempts, first_failed_at,
                                 last_failed_at, next_retry_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (idempotency_key, endpoint_url, envelope_json, error, 1,
                 now, now, _next_retry_at(now, 1)),
            )
        else:
            row_id, attempts = existing
            new_attempts = attempts + 1
            status = "dead" if new_attempts >= MAX_ATTEMPTS else "pending"
            c.execute(
                """
                UPDATE dlq SET attempts = ?, error = ?, last_failed_at = ?,
                               next_retry_at = ?, status = ?
                WHERE id = ?
                """,
                (new_attempts, error, now,
                 _next_retry_at(now, new_attempts), status, row_id),
            )
        c.commit()


def depth(db_path: Optional[Path] = None) -> dict:
    with _conn(db_path) as c:
        rows = c.execute(
            "SELECT status, COUNT(*) FROM dlq GROUP BY status"
        ).fetchall()
    out = {"pending": 0, "dead": 0, "total": 0}
    for status, n in rows:
        out[status] = n
        out["total"] += n
    return out


def tail(n: int = 20, db_path: Optional[Path] = None) -> list[dict]:
    with _conn(db_path) as c:
        rows = c.execute(
            """
            SELECT idempotency_key, endpoint_url, envelope_json, error,
                   attempts, first_failed_at, last_failed_at, next_retry_at,
                   status
            FROM dlq
            ORDER BY last_failed_at DESC
            LIMIT ?
            """,
            (n,),
        ).fetchall()
    out: list[dict] = []
    for r in rows:
        try:
            env = json.loads(r[2])
        except Exception:
            env = {"_raw": r[2]}
        out.append({
            "idempotency_key": r[0],
            "endpoint_url": r[1],
            "envelope": env,
            "error": r[3],
            "attempts": r[4],
            "first_failed_at": r[5],
            "last_failed_at": r[6],
            "next_retry_at": r[7],
            "status": r[8],
        })
    return out


def drain(max_n: int = 50, db_path: Optional[Path] = None,
          send_fn=None) -> dict:
    """Re-emit eligible rows. `send_fn(envelope_json, idempotency_key,
    endpoint_url, secret)` returns (ok: bool, err: str|None).

    On success → DELETE the row. On failure → bump attempts and reschedule.
    """
    if send_fn is None:
        # Lazy import to avoid a circular dep at module import time.
        from . import emitter as _emitter

        def send_fn(envelope_json, idempotency_key, endpoint_url, secret):
            return _emitter.post_signed(
                envelope_json=envelope_json,
                endpoint_url=endpoint_url,
                idempotency_key=idempotency_key,
                secret=secret,
                timeout=3.0,
            )

    from .config import load_config

    cfg = load_config()
    secret_by_url: dict[str, str] = {e.url: e.secret() for e in cfg.endpoints}

    now = time.time()
    succeeded = 0
    retried = 0
    dead = 0
    with _conn(db_path) as c:
        rows = c.execute(
            """
            SELECT id, idempotency_key, endpoint_url, envelope_json, attempts
            FROM dlq
            WHERE status = 'pending' AND next_retry_at <= ?
            ORDER BY next_retry_at ASC
            LIMIT ?
            """,
            (now, max_n),
        ).fetchall()

        for row_id, key, url, env_json, attempts in rows:
            secret = secret_by_url.get(url, "")
            ok, err = send_fn(env_json, key, url, secret)
            if ok:
                c.execute("DELETE FROM dlq WHERE id = ?", (row_id,))
                succeeded += 1
            else:
                new_attempts = attempts + 1
                status = "dead" if new_attempts >= MAX_ATTEMPTS else "pending"
                if status == "dead":
                    dead += 1
                else:
                    retried += 1
                c.execute(
                    """
                    UPDATE dlq SET attempts = ?, error = ?, last_failed_at = ?,
                                   next_retry_at = ?, status = ?
                    WHERE id = ?
                    """,
                    (new_attempts, err or "unknown", time.time(),
                     _next_retry_at(time.time(), new_attempts), status, row_id),
                )
        c.commit()
    return {
        "examined": len(rows),
        "succeeded": succeeded,
        "retried": retried,
        "dead": dead,
    }
