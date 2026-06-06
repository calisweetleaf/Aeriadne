"""Webhook engine configuration loader.

Reads /agent/workspace/mentat/plugin/webhooks.json into a small dataclass.
The file is OPTIONAL — if absent the engine returns a disabled stub config
and emit() becomes a no-op. That keeps Mentat v0.1 invariants intact:
installing v0.2 over v0.1 does not start emitting webhooks unless the user
explicitly opts in by editing webhooks.json.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_MAX_PAYLOAD_BYTES = 16384


@dataclass
class Endpoint:
    url: str
    secret_env: str = "MENTAT_WEBHOOK_SECRET"
    events_filter: list[str] = field(default_factory=list)  # empty = pass everything

    def accepts(self, hook_event_type: str) -> bool:
        if not self.events_filter:
            return True
        return hook_event_type in self.events_filter

    def secret(self) -> str:
        """Resolve the shared secret from env. Empty string if unset.

        Empty secret is intentionally permitted (disler dev mode) — the
        emitter still computes an HMAC over an empty key so signatures stay
        deterministic; the receiver chooses whether to enforce.
        """
        return os.environ.get(self.secret_env, "")


@dataclass
class Config:
    enabled: bool = False
    endpoints: list[Endpoint] = field(default_factory=list)
    max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES

    def active_endpoints(self, hook_event_type: str) -> list[Endpoint]:
        if not self.enabled:
            return []
        return [e for e in self.endpoints if e.accepts(hook_event_type)]


def _config_path() -> Path:
    # Path is relative to the plugin install directory. Honoring
    # ${CLAUDE_PLUGIN_ROOT} mirrors the hooks/_lib.py convention.
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        return Path(root) / "webhooks.json"
    return Path(__file__).resolve().parent.parent / "webhooks.json"


def load_config(path: Optional[Path] = None) -> Config:
    p = path or _config_path()
    if not p.exists():
        return Config()
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return Config()
    # Tolerate the "_doc" key (inline schema docs) and any other unknowns.
    endpoints_raw = raw.get("endpoints", []) or []
    endpoints: list[Endpoint] = []
    for e in endpoints_raw:
        if not isinstance(e, dict) or "url" not in e:
            continue
        endpoints.append(Endpoint(
            url=str(e["url"]),
            secret_env=str(e.get("secret_env", "MENTAT_WEBHOOK_SECRET")),
            events_filter=list(e.get("events_filter", []) or []),
        ))
    return Config(
        enabled=bool(raw.get("enabled", False)),
        endpoints=endpoints,
        max_payload_bytes=int(raw.get("max_payload_bytes", DEFAULT_MAX_PAYLOAD_BYTES)),
    )
