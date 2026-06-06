"""Sync HTTP emitter with HMAC-SHA256 signing and exponential retry.

Stdlib only (urllib + hmac + hashlib + json + time). The function shape is:

    post_signed(envelope_json, endpoint_url, idempotency_key, secret, timeout)
        -> (ok: bool, err: str|None)

The retry wrapper (`_post_with_retry`) does 3 attempts with 1s/2s/4s backoff
before giving up. The whole emit() call has a soft budget of 5 seconds —
hooks.json wires every Mentat hook with timeout: 5, so a stuck webhook
must not be allowed to wedge the session. Per-request timeout is 3 seconds.

Idempotency keys are sha256(session_id + ":" + seq + ":" + hook_event_type)
so duplicate emits across restarts produce the same key and the receiver
can dedupe.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from typing import Optional

from .config import Config, Endpoint, load_config
from .envelope import DislerEnvelope, build_envelope

RETRY_BACKOFFS = (1.0, 2.0, 4.0)
DEFAULT_TIMEOUT = 3.0
EMIT_BUDGET_SECONDS = 5.0


_cached_config: Optional[Config] = None


def configure(config: Optional[Config] = None) -> Config:
    """Override or refresh the in-process config cache.

    Tests and the CLI call this with an explicit Config; hooks call it with
    no argument to force a re-read from disk on next emit().
    """
    global _cached_config
    if config is not None:
        _cached_config = config
    else:
        _cached_config = load_config()
    return _cached_config


def _get_config() -> Config:
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


def compute_idempotency_key(session_id: str, seq: int, hook_event_type: str) -> str:
    raw = f"{session_id}:{seq}:{hook_event_type}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def compute_signature(secret: str, canonical_body: bytes) -> str:
    """HMAC-SHA256 over the exact bytes that will be sent. Receivers verify by
    hashing the raw request body with the same secret."""
    return hmac.new(
        secret.encode("utf-8"),
        canonical_body,
        hashlib.sha256,
    ).hexdigest()


def post_signed(envelope_json: str, endpoint_url: str, idempotency_key: str,
                secret: str, timeout: float = DEFAULT_TIMEOUT) -> tuple[bool, Optional[str]]:
    """One HTTP POST, no retry. Returns (ok, error_reason)."""
    body = envelope_json.encode("utf-8")
    sig = compute_signature(secret, body)
    req = urllib.request.Request(
        url=endpoint_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Mentat-Signature": f"sha256={sig}",
            "X-Idempotency-Key": idempotency_key,
            "User-Agent": "mentat-webhooks/0.2",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode() or 0
            if 200 <= code < 300:
                return True, None
            return False, f"http_{code}"
    except urllib.error.HTTPError as e:
        return False, f"http_{e.code}"
    except urllib.error.URLError as e:
        return False, f"urlerror:{e.reason}"
    except TimeoutError as e:  # urlopen can raise this on timeout
        return False, f"timeout:{e}"
    except Exception as e:  # pylint: disable=broad-except
        return False, f"{type(e).__name__}:{e}"


def _post_with_retry(envelope_json: str, endpoint_url: str,
                     idempotency_key: str, secret: str,
                     deadline: float) -> tuple[bool, Optional[str]]:
    last_err: Optional[str] = None
    for i, backoff in enumerate(RETRY_BACKOFFS):
        remaining = deadline - time.time()
        if remaining <= 0:
            return False, last_err or "budget_exhausted"
        # Per-request timeout is min(default, remaining) so we never spend the
        # whole budget on a single in-flight call.
        per_req_timeout = min(DEFAULT_TIMEOUT, max(0.1, remaining))
        ok, err = post_signed(envelope_json, endpoint_url, idempotency_key,
                              secret, timeout=per_req_timeout)
        if ok:
            return True, None
        last_err = err
        # Don't sleep after the last attempt; just return.
        if i == len(RETRY_BACKOFFS) - 1:
            break
        # Honor the budget when sleeping.
        sleep_for = min(backoff, max(0.0, deadline - time.time() - 0.05))
        if sleep_for > 0:
            time.sleep(sleep_for)
    return False, last_err or "exhausted"


def emit(insight, session_id: Optional[str] = None,
         source_app: str = "mentat") -> dict:
    """Public sync entry point. Build envelope, sign, POST to every active
    endpoint that whitelists this event type, and DLQ any final failures.

    Returns a small report dict that tests + the CLI can use; hooks ignore it.
    NEVER raises — the hook layer wraps this with try/except, but defense in
    depth is cheap.
    """
    try:
        cfg = _get_config()
        sid = session_id or getattr(insight, "session_id", None) or "default"
        envelope = build_envelope(insight, session_id=sid, source_app=source_app)
        return _emit_envelope(envelope, cfg)
    except Exception as e:  # pylint: disable=broad-except
        return {
            "delivered": 0,
            "dlq": 0,
            "skipped": 0,
            "error": f"{type(e).__name__}:{e}",
        }


def emit_async(insight, session_id: Optional[str] = None,
               source_app: str = "mentat") -> dict:
    """Alias for emit(). v0.1 invariant is sync-only; this exists so callers
    can switch to a true background-thread implementation later without
    touching the call sites. For now it just calls emit()."""
    return emit(insight, session_id=session_id, source_app=source_app)


def _emit_envelope(envelope: DislerEnvelope, cfg: Config) -> dict:
    from . import dlq  # local import to avoid cycle at module load

    body = envelope.to_json()
    # Enforce max_payload_bytes (truncates large payloads loudly via marker).
    if len(body) > cfg.max_payload_bytes:
        # Truncate the payload dict and re-serialize so the wire body stays
        # under cap. Most disler ingestors choke on >64KB bodies.
        envelope.payload = {
            "_truncated": True,
            "_original_bytes": len(body),
            "hint": "Mentat dropped payload to honor max_payload_bytes.",
            "state": envelope.payload.get("state"),
            "seq": envelope.payload.get("seq"),
            "insight_id": envelope.payload.get("insight_id"),
        }
        body = envelope.to_json()

    targets = cfg.active_endpoints(envelope.hook_event_type)
    if not targets:
        return {"delivered": 0, "dlq": 0, "skipped": 1, "error": None}

    key = compute_idempotency_key(
        envelope.session_id,
        int(envelope.payload.get("seq", 0)),
        envelope.hook_event_type,
    )

    deadline = time.time() + EMIT_BUDGET_SECONDS
    delivered = 0
    dlq_count = 0
    for ep in targets:
        ok, err = _post_with_retry(
            envelope_json=body,
            endpoint_url=ep.url,
            idempotency_key=key,
            secret=ep.secret(),
            deadline=deadline,
        )
        if ok:
            delivered += 1
        else:
            try:
                dlq.enqueue(
                    envelope_json=body,
                    idempotency_key=key,
                    endpoint_url=ep.url,
                    error=err or "unknown",
                )
                dlq_count += 1
            except Exception:  # pylint: disable=broad-except
                # If the DLQ itself fails (disk full, locked db) we drop the
                # event rather than blowing up the hook. Hooks live in the
                # critical path.
                pass
    return {
        "delivered": delivered,
        "dlq": dlq_count,
        "skipped": 0,
        "error": None,
    }


def drain_dlq(max_n: int = 50) -> dict:
    """Trigger a DLQ drain. Thin wrapper kept here so callers have one
    import (`from webhook_engine import drain_dlq`)."""
    from . import dlq  # local import to avoid cycle at module load
    return dlq.drain(max_n=max_n)
