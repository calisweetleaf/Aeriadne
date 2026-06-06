#!/usr/bin/env python3
"""
SSE Event Broadcaster — Sovereign MCP Server

Thread-safe Server-Sent Events broadcaster for:
  - Real-time tool call events
  - Neural substrate telemetry (Muad'Dib Q-table updates)
  - Golden path discoveries
  - Webhook delivery status
  - MCP Streamable HTTP server→client notifications

Each connected SSE client gets its own queue.
Disconnected clients are reaped automatically.
Heartbeat keeps connections alive through proxies.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Set

logger = logging.getLogger(__name__)


class SSEClient:
    """Represents a single connected SSE consumer."""

    __slots__ = ("client_id", "queue", "connected_at", "event_filters", "alive")

    def __init__(
        self,
        event_filters: Optional[List[str]] = None,
        client_id: Optional[str] = None,
    ) -> None:
        self.client_id: str = client_id or f"sse_{uuid.uuid4().hex[:12]}"
        self.queue: queue.Queue[Optional[str]] = queue.Queue(maxsize=256)
        self.connected_at: float = time.time()
        self.event_filters: Set[str] = set(event_filters or ["*"])
        self.alive: bool = True

    def accepts(self, event_type: str) -> bool:
        """Check if this client subscribes to the event type."""
        if not self.alive:
            return False
        if "*" in self.event_filters:
            return True
        return event_type in self.event_filters

    def push(self, data: str) -> bool:
        """Push an SSE-formatted string to this client's queue. Returns False if full."""
        if not self.alive:
            return False
        try:
            self.queue.put_nowait(data)
            return True
        except queue.Full:
            logger.warning("SSE client %s queue full — dropping event", self.client_id)
            return False

    def disconnect(self) -> None:
        """Signal this client is disconnected."""
        self.alive = False
        # Push sentinel to unblock any waiting generator
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass


class SSEBroadcaster:
    """
    Thread-safe SSE event broadcaster.

    Usage (stdlib HTTPServer):
        broadcaster = SSEBroadcaster()
        client = broadcaster.connect(event_filters=["tool_call", "neural_telemetry"])
        # In handler: stream client.queue items as text/event-stream

    Usage (FastAPI):
        @app.get("/events")
        async def events():
            client = broadcaster.connect()
            return StreamingResponse(broadcaster.stream_generator(client), ...)
    """

    def __init__(self, heartbeat_interval: float = 30.0) -> None:
        self._clients: Dict[str, SSEClient] = {}
        self._lock = threading.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._running = True
        self._event_count = 0

        # Heartbeat thread keeps connections alive through proxies/LBs
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="sse-heartbeat",
        )
        self._heartbeat_thread.start()

        # Reaper thread cleans up dead clients
        self._reaper_thread = threading.Thread(
            target=self._reaper_loop,
            daemon=True,
            name="sse-reaper",
        )
        self._reaper_thread.start()

        logger.info("SSEBroadcaster initialized (heartbeat: %.0fs)", heartbeat_interval)

    # ── Client Management ─────────────────────────────────────────────────

    def connect(
        self,
        event_filters: Optional[List[str]] = None,
        client_id: Optional[str] = None,
    ) -> SSEClient:
        """Register a new SSE client. Returns the client for streaming."""
        client = SSEClient(event_filters=event_filters, client_id=client_id)
        with self._lock:
            self._clients[client.client_id] = client
        logger.info(
            "SSE client connected: %s (filters: %s, total: %d)",
            client.client_id, client.event_filters, len(self._clients),
        )
        return client

    def disconnect(self, client_id: str) -> None:
        """Disconnect and remove a client."""
        with self._lock:
            client = self._clients.pop(client_id, None)
        if client:
            client.disconnect()
            logger.info("SSE client disconnected: %s", client_id)

    @property
    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    # ── Broadcast API ─────────────────────────────────────────────────────

    def broadcast(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast an event to all connected clients that match the event type.
        Returns the number of clients that received the event.
        """
        eid = event_id or f"e_{uuid.uuid4().hex[:12]}"
        self._event_count += 1

        # Format as SSE wire protocol
        payload = json.dumps(data, ensure_ascii=False, default=str)
        sse_message = f"id: {eid}\nevent: {event_type}\ndata: {payload}\n\n"

        delivered = 0
        with self._lock:
            targets = [c for c in self._clients.values() if c.accepts(event_type)]

        for client in targets:
            if client.push(sse_message):
                delivered += 1

        return delivered

    # ── Streaming Generators ──────────────────────────────────────────────

    def stream_generator(
        self, client: SSEClient, timeout: float = 1.0
    ) -> Generator[str, None, None]:
        """
        Generator that yields SSE-formatted strings for a connected client.
        Use with FastAPI StreamingResponse or any WSGI/ASGI framework.

        Yields SSE messages until the client disconnects.
        """
        try:
            while client.alive:
                try:
                    message = client.queue.get(timeout=timeout)
                    if message is None:
                        # Sentinel — client disconnected
                        break
                    yield message
                except queue.Empty:
                    continue
        finally:
            self.disconnect(client.client_id)

    def stream_bytes_generator(
        self, client: SSEClient, timeout: float = 1.0
    ) -> Generator[bytes, None, None]:
        """Same as stream_generator but yields bytes (for stdlib wfile.write)."""
        for msg in self.stream_generator(client, timeout=timeout):
            yield msg.encode("utf-8")

    # ── Background Threads ────────────────────────────────────────────────

    def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat comments to all connected clients."""
        while self._running:
            time.sleep(self._heartbeat_interval)
            heartbeat = f": heartbeat {int(time.time())}\n\n"
            with self._lock:
                alive_clients = list(self._clients.values())
            for client in alive_clients:
                if client.alive:
                    client.push(heartbeat)

    def _reaper_loop(self) -> None:
        """Periodically remove dead clients."""
        while self._running:
            time.sleep(60.0)
            with self._lock:
                dead = [cid for cid, c in self._clients.items() if not c.alive]
                for cid in dead:
                    del self._clients[cid]
            if dead:
                logger.info("SSE reaper cleaned %d dead client(s)", len(dead))

    # ── Stats / Health ────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return broadcaster statistics."""
        with self._lock:
            clients = [
                {
                    "client_id": c.client_id,
                    "connected_at": c.connected_at,
                    "filters": list(c.event_filters),
                    "queue_size": c.queue.qsize(),
                    "alive": c.alive,
                }
                for c in self._clients.values()
            ]
        return {
            "connected_clients": len(clients),
            "total_events_broadcast": self._event_count,
            "heartbeat_interval": self._heartbeat_interval,
            "clients": clients,
        }

    def shutdown(self) -> None:
        """Graceful shutdown — disconnect all clients."""
        self._running = False
        with self._lock:
            for client in self._clients.values():
                client.disconnect()
            self._clients.clear()
        logger.info("SSEBroadcaster shut down")
