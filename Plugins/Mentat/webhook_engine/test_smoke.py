#!/usr/bin/env python3
"""Webhook engine smoke test.

Covers:
    * envelope build from a duck-typed Insight
    * canonical JSON stability (HMAC depends on it)
    * idempotency-key determinism
    * HMAC signature reproducibility
    * DLQ enqueue + drain (with a mock send_fn)
    * DLQ backoff schedule (10m / 1h / 6h / 24h, cap at 5)
    * Endpoint event filter

Pure stdlib. Run directly:

    python3 webhook_engine/test_smoke.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Make the plugin importable when this script is run directly.
_HERE = Path(__file__).resolve().parent
_PLUGIN_ROOT = _HERE.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


# --- minimal duck-typed Insight so the test has no state_machine dep -------

@dataclass
class _StubType:
    value: str


@dataclass
class _StubInsight:
    type: _StubType
    payload: dict = field(default_factory=dict)
    state: Optional[str] = "EXECUTING"
    timestamp: float = 1_700_000_000.0
    seq: int = 7
    id: str = "abcdef123456"
    session_id: Optional[str] = "sess-xyz"


def _insight(type_value: str = "reward_signal", **kw) -> _StubInsight:
    return _StubInsight(type=_StubType(type_value), **kw)


# --- test helpers -----------------------------------------------------------

failures: list[str] = []


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  OK:   {msg}")


# --- tests ------------------------------------------------------------------

def test_envelope_build() -> None:
    print("[1] envelope.build_envelope")
    from webhook_engine.envelope import build_envelope

    env = build_envelope(_insight(payload={"tool": "Edit", "value": 0.7, "success": True}),
                          session_id="sess-xyz")
    _assert(env.source_app == "mentat", "source_app defaults to 'mentat'")
    _assert(env.session_id == "sess-xyz", "session_id propagates")
    _assert(env.hook_event_type == "reward_signal", "hook_event_type = InsightType.value")
    _assert(env.timestamp == 1_700_000_000_000, "timestamp in ms")
    _assert("state" in env.payload, "payload retains FSA state")
    _assert(env.payload["seq"] == 7, "payload retains seq")
    _assert(env.payload["insight_id"] == "abcdef123456", "payload retains insight id")
    _assert(env.summary is not None and "Edit" in env.summary, "summary surfaces the tool")


def test_canonical_json_stability() -> None:
    print("[2] canonical JSON stability")
    from webhook_engine.envelope import build_envelope

    env_a = build_envelope(_insight(payload={"b": 2, "a": 1}), session_id="s")
    env_b = build_envelope(_insight(payload={"a": 1, "b": 2}), session_id="s")
    _assert(env_a.to_json() == env_b.to_json(),
            "key order in source dict does NOT affect canonical output (sort_keys)")
    # Canonical form uses (',', ':') separators -> no whitespace between
    # structural tokens. (Values may contain spaces — that's legitimate.)
    raw = env_a.to_json()
    _assert(", " not in raw and ": " not in raw,
            "canonical JSON uses tight separators (',', ':')")


def test_idempotency_key_determinism() -> None:
    print("[3] idempotency key determinism")
    from webhook_engine import compute_idempotency_key

    k1 = compute_idempotency_key("sess-a", 5, "reward_signal")
    k2 = compute_idempotency_key("sess-a", 5, "reward_signal")
    k3 = compute_idempotency_key("sess-a", 5, "state_transition")
    _assert(k1 == k2, "same (sid, seq, type) -> same key")
    _assert(k1 != k3, "different type -> different key")
    _assert(len(k1) == 64, "sha256 hex digest is 64 chars")


def test_hmac_signature_stability() -> None:
    print("[4] HMAC signature stability")
    from webhook_engine import compute_signature

    body = b'{"a":1,"b":2}'
    s1 = compute_signature("topsecret", body)
    s2 = compute_signature("topsecret", body)
    s3 = compute_signature("different", body)
    _assert(s1 == s2, "same secret + body -> same hex")
    _assert(s1 != s3, "different secret -> different hex")
    _assert(len(s1) == 64, "sha256 hex digest is 64 chars")
    # Known-good vector: HMAC-SHA256("k", "msg")
    import hashlib
    import hmac
    expected = hmac.new(b"k", b"msg", hashlib.sha256).hexdigest()
    _assert(compute_signature("k", b"msg") == expected,
            "matches stdlib hmac reference")


def test_dlq_enqueue_drain() -> None:
    print("[5] DLQ enqueue + drain")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["MENTAT_HOME"] = tmp
        # Re-import to pick up the temp MENTAT_HOME for the dlq path helper.
        import importlib
        import sqlite3
        import webhook_engine.dlq as dlq
        importlib.reload(dlq)

        dlq.enqueue(envelope_json='{"hook_event_type":"reward_signal","payload":{}}',
                    idempotency_key="key-1",
                    endpoint_url="http://example.invalid/hooks",
                    error="urlerror:test")
        d = dlq.depth()
        _assert(d["pending"] == 1 and d["dead"] == 0,
                "after one enqueue: 1 pending")

        # The freshly-enqueued row's next_retry_at is now+600s (10min). Force
        # it to 0 so the immediate drain considers it eligible.
        with sqlite3.connect(str(dlq._dlq_path())) as c:
            c.execute("UPDATE dlq SET next_retry_at = 0")
            c.commit()

        # Drain with a mock send_fn that succeeds.
        result = dlq.drain(max_n=10, send_fn=lambda *a, **kw: (True, None))
        _assert(result["succeeded"] == 1, "successful drain removes row")
        _assert(dlq.depth()["total"] == 0, "DLQ empty after success")

        # Enqueue again, then fail through to "dead".
        for i in range(5):
            dlq.enqueue(envelope_json='{"x":1}',
                        idempotency_key="key-dead",
                        endpoint_url="http://example.invalid/hooks",
                        error=f"attempt-{i}")
        d = dlq.depth()
        _assert(d["dead"] == 1, "5 enqueues reach MAX_ATTEMPTS -> dead")


def test_dlq_backoff_math() -> None:
    print("[6] DLQ backoff schedule")
    from webhook_engine.dlq import DLQ_BACKOFF_SECONDS, _next_retry_at

    _assert(DLQ_BACKOFF_SECONDS == (600, 3600, 21600, 86400),
            "backoff schedule is 10min / 1h / 6h / 24h")
    now = 1_000_000.0
    _assert(_next_retry_at(now, 1) - now == 600, "1 attempt -> +10min")
    _assert(_next_retry_at(now, 2) - now == 3600, "2 attempts -> +1h")
    _assert(_next_retry_at(now, 3) - now == 21600, "3 attempts -> +6h")
    _assert(_next_retry_at(now, 4) - now == 86400, "4 attempts -> +24h")
    # 5th attempt would be capped at the last bucket (24h) — but at that
    # point status is 'dead' anyway.
    _assert(_next_retry_at(now, 5) - now == 86400, "5 attempts -> capped at 24h")


def test_endpoint_filter() -> None:
    print("[7] endpoint event filter")
    from webhook_engine.config import Endpoint

    e1 = Endpoint(url="http://a", events_filter=[])
    e2 = Endpoint(url="http://b", events_filter=["reward_signal", "scope_drift"])
    _assert(e1.accepts("anything"), "empty filter passes everything")
    _assert(e2.accepts("reward_signal"), "whitelisted event passes")
    _assert(not e2.accepts("session_end"), "non-whitelisted event blocked")


def test_emit_no_endpoint_is_skip() -> None:
    print("[8] emit() with no active endpoints reports skipped")
    from webhook_engine import configure, emit
    from webhook_engine.config import Config

    configure(Config(enabled=False, endpoints=[]))
    result = emit(_insight(type_value="note", payload={"text": "hi"}),
                  session_id="sess-skip")
    _assert(result["delivered"] == 0, "delivered=0 when disabled")
    _assert(result["skipped"] == 1, "skipped=1 when disabled")
    _assert(result["dlq"] == 0, "no DLQ when disabled (we don't even try)")


def test_emit_routes_to_dlq_on_failure() -> None:
    print("[9] emit() routes a failed POST to the DLQ")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["MENTAT_HOME"] = tmp
        # Reload dlq so it points at the temp dir.
        import importlib
        import webhook_engine.dlq as dlq
        importlib.reload(dlq)

        from webhook_engine import configure, emit
        from webhook_engine.config import Config, Endpoint

        # Point at an unreachable URL with very short backoff via monkey-patch.
        import webhook_engine.emitter as emitter
        importlib.reload(emitter)
        emitter.RETRY_BACKOFFS = (0.0, 0.0, 0.0)
        emitter.DEFAULT_TIMEOUT = 0.2
        emitter.EMIT_BUDGET_SECONDS = 1.0
        # Force the in-process config.
        emitter.configure(Config(
            enabled=True,
            endpoints=[Endpoint(url="http://127.0.0.1:1/never-listens", events_filter=[])],
        ))
        # Patch the dlq module emitter uses.
        emitter.dlq = dlq  # noqa: SLF001
        result = emitter.emit(_insight(type_value="note", payload={"text": "x"}),
                              session_id="sess-fail")
        _assert(result["delivered"] == 0, "no successful delivery (network refused)")
        _assert(result["dlq"] >= 1, "envelope was enqueued to DLQ")
        _assert(dlq.depth()["pending"] >= 1, "DLQ has at least one pending row")


# --- runner -----------------------------------------------------------------

def main() -> int:
    tests = [
        test_envelope_build,
        test_canonical_json_stability,
        test_idempotency_key_determinism,
        test_hmac_signature_stability,
        test_dlq_enqueue_drain,
        test_dlq_backoff_math,
        test_endpoint_filter,
        test_emit_no_endpoint_is_skip,
        test_emit_routes_to_dlq_on_failure,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:  # pylint: disable=broad-except
            failures.append(f"{t.__name__} raised {type(e).__name__}: {e}")
            print(f"  CRASH: {t.__name__}: {e}")
    print()
    if failures:
        print(f"FAILED ({len(failures)} failure(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASSED — webhook_engine smoke green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
