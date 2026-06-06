"""Mentat webhook engine — disler-compatible event emitter.

Public API (the only names hooks / CLI / tests should import):

    emit(insight, session_id=None, source_app="mentat")  -> dict
    emit_async(insight, session_id=None, source_app="mentat") -> dict
    configure(config=None) -> Config         # refresh in-process cache
    drain_dlq(max_n=50) -> dict              # retry DLQ rows

    DislerEnvelope, build_envelope          # for tests / advanced callers
    Config, Endpoint, load_config           # for the CLI

The engine is stdlib-only and sync. Webhook failures never block the
calling hook (the hook layer wraps emit() in try/except and the emitter
itself defends in depth by catching everything internally).
"""
from __future__ import annotations

from .config import Config, Endpoint, load_config
from .emitter import (
    compute_idempotency_key,
    compute_signature,
    configure,
    drain_dlq,
    emit,
    emit_async,
)
from .envelope import DislerEnvelope, build_envelope

__all__ = [
    "emit",
    "emit_async",
    "configure",
    "drain_dlq",
    "DislerEnvelope",
    "build_envelope",
    "Config",
    "Endpoint",
    "load_config",
    "compute_idempotency_key",
    "compute_signature",
]
