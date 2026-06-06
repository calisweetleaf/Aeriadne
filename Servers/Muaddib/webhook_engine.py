#!/usr/bin/env python3
"""
Webhook Dispatch Engine — Sovereign MCP gateway event egress.

This engine dispatches events emitted by the existing gateway/state-machine
path. It is not a second cognition plane and must not own Muad'Dib weights,
Q-table state, or tool registry state.

Production-grade outbound webhook system with:
  - HMAC-SHA256 payload signing
  - Exponential backoff retries (3 attempts: 1s → 4s → 16s)
  - Idempotency keys on every payload
  - Dead-letter queue persistence
  - Thread-safe registration/unregistration
  - Event filter subscriptions

Persistence: data/security/webhooks.json (registrations)
             data/security/webhook_dead_letters.jsonl (failed deliveries)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  WEBHOOK REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════


class WebhookRegistration:
    """A single webhook subscription."""

    __slots__ = (
        "webhook_id", "callback_url", "secret", "event_filters",
        "created_at", "last_delivery", "delivery_count",
        "failure_count", "active",
    )

    def __init__(
        self,
        callback_url: str,
        secret: str,
        event_filters: Optional[List[str]] = None,
        webhook_id: Optional[str] = None,
    ) -> None:
        self.webhook_id: str = webhook_id or f"wh_{uuid.uuid4().hex[:16]}"
        self.callback_url: str = callback_url
        self.secret: str = secret
        self.event_filters: List[str] = event_filters or ["*"]
        self.created_at: float = time.time()
        self.last_delivery: float = 0.0
        self.delivery_count: int = 0
        self.failure_count: int = 0
        self.active: bool = True

    def matches_event(self, event_type: str) -> bool:
        """Check if this webhook subscribes to the given event type."""
        if not self.active:
            return False
        if "*" in self.event_filters:
            return True
        return event_type in self.event_filters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "webhook_id": self.webhook_id,
            "callback_url": self.callback_url,
            "secret": self.secret,
            "event_filters": self.event_filters,
            "created_at": self.created_at,
            "last_delivery": self.last_delivery,
            "delivery_count": self.delivery_count,
            "failure_count": self.failure_count,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookRegistration":
        wh = cls(
            callback_url=data["callback_url"],
            secret=data["secret"],
            event_filters=data.get("event_filters", ["*"]),
            webhook_id=data.get("webhook_id"),
        )
        wh.created_at = data.get("created_at", time.time())
        wh.last_delivery = data.get("last_delivery", 0.0)
        wh.delivery_count = data.get("delivery_count", 0)
        wh.failure_count = data.get("failure_count", 0)
        wh.active = data.get("active", True)
        return wh


# ═══════════════════════════════════════════════════════════════════════════
#  WEBHOOK ENGINE
# ═══════════════════════════════════════════════════════════════════════════


class WebhookEngine:
    """
    Thread-safe webhook dispatch engine.

    Register callback URLs with HMAC secrets and event filters.
    Fire events and the engine delivers payloads asynchronously
    with retry + dead-letter on permanent failure.
    """

    RETRY_DELAYS = [1.0, 4.0, 16.0]  # exponential backoff
    DELIVERY_TIMEOUT = 10.0  # seconds per HTTP attempt

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = Path(data_dir or "data/security")
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._registry_file = self._data_dir / "webhooks.json"
        self._dead_letter_file = self._data_dir / "webhook_dead_letters.jsonl"

        self._lock = threading.Lock()
        self._webhooks: Dict[str, WebhookRegistration] = {}
        self._load_registry()

        # Background dispatch thread
        self._dispatch_queue: List[Dict[str, Any]] = []
        self._queue_lock = threading.Lock()
        self._dispatch_event = threading.Event()
        self._running = True
        self._dispatch_thread = threading.Thread(
            target=self._dispatch_loop,
            daemon=True,
            name="webhook-dispatch",
        )
        self._dispatch_thread.start()
        logger.info(
            "WebhookEngine initialized: %d registered webhook(s)",
            len(self._webhooks),
        )

    # ── Registration API ──────────────────────────────────────────────────

    def register(
        self,
        callback_url: str,
        secret: Optional[str] = None,
        event_filters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Register a new webhook. Returns registration details."""
        if not callback_url or not callback_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid callback URL: {callback_url!r}")

        generated_secret = secret or uuid.uuid4().hex
        wh = WebhookRegistration(
            callback_url=callback_url,
            secret=generated_secret,
            event_filters=event_filters,
        )

        with self._lock:
            self._webhooks[wh.webhook_id] = wh
            self._save_registry()

        logger.info(
            "Webhook registered: %s → %s (filters: %s)",
            wh.webhook_id, callback_url, wh.event_filters,
        )
        return {
            "ok": True,
            "webhook_id": wh.webhook_id,
            "secret": generated_secret,
            "event_filters": wh.event_filters,
        }

    def unregister(self, webhook_id: str) -> Dict[str, Any]:
        """Remove a webhook registration."""
        with self._lock:
            wh = self._webhooks.pop(webhook_id, None)
            if wh is None:
                return {"ok": False, "error": f"Webhook {webhook_id} not found"}
            self._save_registry()

        logger.info("Webhook unregistered: %s", webhook_id)
        return {"ok": True, "webhook_id": webhook_id, "removed": True}

    def list_webhooks(self) -> Dict[str, Any]:
        """List all registered webhooks (secrets redacted)."""
        with self._lock:
            hooks = []
            for wh in self._webhooks.values():
                entry = wh.to_dict()
                entry["secret"] = entry["secret"][:4] + "****"
                hooks.append(entry)
        return {"ok": True, "webhooks": hooks, "count": len(hooks)}

    # ── Dispatch API ──────────────────────────────────────────────────────

    def fire_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: str = "mcp_server",
    ) -> int:
        """
        Queue an event for delivery to all matching webhooks.
        Returns the number of webhooks that will receive the event.
        Non-blocking — actual HTTP delivery happens in background thread.
        """
        idempotency_key = f"evt_{uuid.uuid4().hex}"
        envelope = {
            "idempotency_key": idempotency_key,
            "event_type": event_type,
            "source": source,
            "timestamp": time.time(),
            "payload": payload,
        }

        matched = 0
        with self._lock:
            targets = [
                wh for wh in self._webhooks.values()
                if wh.matches_event(event_type)
            ]

        for wh in targets:
            with self._queue_lock:
                self._dispatch_queue.append({
                    "webhook": wh,
                    "envelope": envelope,
                    "attempt": 0,
                })
            matched += 1

        if matched > 0:
            self._dispatch_event.set()

        return matched

    # ── Background Dispatch Loop ──────────────────────────────────────────

    def _dispatch_loop(self) -> None:
        """Background thread: drain queue, deliver with retries."""
        while self._running:
            self._dispatch_event.wait(timeout=5.0)
            self._dispatch_event.clear()

            while True:
                with self._queue_lock:
                    if not self._dispatch_queue:
                        break
                    item = self._dispatch_queue.pop(0)

                wh: WebhookRegistration = item["webhook"]
                envelope: Dict[str, Any] = item["envelope"]
                attempt: int = item["attempt"]

                success = self._deliver(wh, envelope)
                if success:
                    with self._lock:
                        wh.delivery_count += 1
                        wh.last_delivery = time.time()
                        self._save_registry()
                else:
                    if attempt < len(self.RETRY_DELAYS):
                        delay = self.RETRY_DELAYS[attempt]
                        logger.warning(
                            "Webhook %s delivery failed (attempt %d), retry in %.0fs",
                            wh.webhook_id, attempt + 1, delay,
                        )
                        time.sleep(delay)
                        with self._queue_lock:
                            self._dispatch_queue.append({
                                "webhook": wh,
                                "envelope": envelope,
                                "attempt": attempt + 1,
                            })
                        self._dispatch_event.set()
                    else:
                        # Dead letter
                        with self._lock:
                            wh.failure_count += 1
                            self._save_registry()
                        self._write_dead_letter(wh, envelope)
                        logger.error(
                            "Webhook %s permanently failed after %d attempts → dead letter",
                            wh.webhook_id, len(self.RETRY_DELAYS),
                        )

    def _deliver(
        self, wh: WebhookRegistration, envelope: Dict[str, Any]
    ) -> bool:
        """Deliver a single webhook payload with HMAC signature."""
        body = json.dumps(envelope, ensure_ascii=False, default=str).encode("utf-8")

        # HMAC-SHA256 signature
        signature = hmac.new(
            wh.secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Id": wh.webhook_id,
            "X-Idempotency-Key": envelope.get("idempotency_key", ""),
            "User-Agent": "SovereignMCP-Webhook/1.0",
        }

        req = Request(
            wh.callback_url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.DELIVERY_TIMEOUT) as resp:
                status = resp.getcode()
                if 200 <= status < 300:
                    logger.debug(
                        "Webhook %s delivered: %s → %d",
                        wh.webhook_id, envelope["event_type"], status,
                    )
                    return True
                logger.warning(
                    "Webhook %s non-2xx response: %d", wh.webhook_id, status,
                )
                return False
        except HTTPError as exc:
            logger.warning(
                "Webhook %s HTTP error: %d %s",
                wh.webhook_id, exc.code, exc.reason,
            )
            return False
        except URLError as exc:
            logger.warning(
                "Webhook %s URL error: %s", wh.webhook_id, exc.reason,
            )
            return False
        except Exception as exc:
            logger.error(
                "Webhook %s delivery exception: %s", wh.webhook_id, exc,
            )
            return False

    # ── Persistence ───────────────────────────────────────────────────────

    def _save_registry(self) -> None:
        """Atomic save of webhook registrations."""
        data = {wid: wh.to_dict() for wid, wh in self._webhooks.items()}
        tmp = self._registry_file.with_suffix(".json.tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self._registry_file)
        except Exception as exc:
            logger.error("Webhook registry save failed: %s", exc)

    def _load_registry(self) -> None:
        """Load webhook registrations from disk."""
        if not self._registry_file.exists():
            return
        try:
            with open(self._registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for wid, wh_data in data.items():
                self._webhooks[wid] = WebhookRegistration.from_dict(wh_data)
            logger.info("Loaded %d webhook(s) from disk", len(self._webhooks))
        except Exception as exc:
            logger.error("Webhook registry load failed: %s", exc)

    def _write_dead_letter(
        self, wh: WebhookRegistration, envelope: Dict[str, Any]
    ) -> None:
        """Append a failed delivery to the dead-letter log."""
        entry = {
            "timestamp": time.time(),
            "webhook_id": wh.webhook_id,
            "callback_url": wh.callback_url,
            "event_type": envelope.get("event_type"),
            "idempotency_key": envelope.get("idempotency_key"),
            "payload_size": len(json.dumps(envelope, default=str)),
        }
        try:
            with open(self._dead_letter_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("Dead letter write failed: %s", exc)

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Graceful shutdown — drain remaining queue items."""
        self._running = False
        self._dispatch_event.set()
        self._dispatch_thread.join(timeout=5.0)
        logger.info("WebhookEngine shut down")
