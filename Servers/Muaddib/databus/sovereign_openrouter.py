"""
Production Module: Sovereign OpenRouter Client
Source: Somnus Sovereign Systems
Created: 2026-03-06
Status: Production Hardened

Capabilities:
- YAML-driven sovereign config with env var interpolation
- Configurable identity headers and relative-path prompt resolution
- Truthful fallback routing with strategy-aware ordering
- Correct thinking mode semantics (auto / force / disabled)
- Retry engine for non-streaming requests and guarded retry for streaming
- Per-session token and cost tracking with request metadata
- Hot-reload config without process restart or dropping in-flight clients
- Structured observability with request/route summaries

API Surface:
- SovereignOpenRouterClient.complete()
- SovereignOpenRouterClient.stream()
- SovereignOpenRouterClient.batch()
- SovereignOpenRouterClient.get_models()
- SovereignOpenRouterClient.cost_report()
- SovereignOpenRouterClient.config_summary()
- SovereignOpenRouterClient.reload_config()

Dependencies:
- httpx (async HTTP)
- pyyaml
- pydantic
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Tuple

import httpx
import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger("sovereign.openrouter")
ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")
REQUEST_ID_HEADERS = (
    "x-openrouter-request-id",
    "x-request-id",
    "request-id",
)


class RoutingStrategy(str, Enum):
    COST = "cost"
    LATENCY = "latency"
    QUALITY = "quality"
    COST_LATENCY = "cost_latency"


class ThinkingMode(str, Enum):
    AUTO = "auto"
    FORCE = "force"
    DISABLED = "disabled"


class InjectMode(str, Enum):
    PREPEND = "prepend"
    APPEND = "append"
    REPLACE = "replace"


class BatchRankBy(str, Enum):
    QUALITY = "quality"
    LATENCY = "latency"
    COST = "cost"


class ConfigError(Exception):
    """Raised when YAML loading or config resolution fails."""


class RoutingError(Exception):
    """Raised when every provider in a route chain fails."""


class ThinkingError(Exception):
    """Raised when thinking mode is requested for an unsupported model."""


class StreamError(Exception):
    """Raised when streaming fails after partial output or invalid SSE data."""


class BatchError(Exception):
    """Raised when batch execution returns no usable results."""


class APIResponseError(Exception):
    """Raised when the upstream response shape is invalid or not JSON."""


class ModelProfile(BaseModel):
    cost_rank: int = Field(default=100, ge=1)
    latency_rank: int = Field(default=100, ge=1)
    quality_rank: int = Field(default=100, ge=1)
    thinking_supported: Optional[bool] = None


class ThinkingConfig(BaseModel):
    enabled: bool = False
    budget_tokens: int = Field(default=8000, ge=1000, le=32000)
    mode: ThinkingMode = ThinkingMode.AUTO
    supported_model_prefixes: List[str] = Field(
        default_factory=lambda: [
            "anthropic/claude",
            "deepseek/deepseek-r1",
            "openai/o",
        ]
    )


class RoutingConfig(BaseModel):
    strategy: RoutingStrategy = RoutingStrategy.COST_LATENCY
    fallback_chain: List[str] = Field(
        default_factory=lambda: [
            "google/gemini-2.0-flash",
            "deepseek/deepseek-r1",
            "anthropic/claude-sonnet-4-5",
        ]
    )
    max_fallback_attempts: int = Field(default=3, ge=1, le=10)
    allow_fallbacks_in_batch: bool = False
    model_profiles: Dict[str, ModelProfile] = Field(default_factory=dict)


class IdentityConfig(BaseModel):
    referer: Optional[str] = None
    title: str = "Sovereign OpenRouter"
    extra_headers: Dict[str, str] = Field(default_factory=dict)


class SystemPromptConfig(BaseModel):
    enabled: bool = False
    template: Optional[str] = None
    inject_mode: InjectMode = InjectMode.PREPEND


class CompatibilityConfig(BaseModel):
    complete_via_stream_models: List[str] = Field(default_factory=list)


class RetryConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_base: float = Field(default=2.0, ge=1.0)
    backoff_max: float = Field(default=30.0, ge=5.0)


class ObservabilityConfig(BaseModel):
    log_requests: bool = True
    log_responses: bool = False
    token_tracking: bool = True
    cost_tracking: bool = True
    session_id: Optional[str] = None


class DefaultsConfig(BaseModel):
    model: str = "google/gemini-2.0-flash"
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    timeout_seconds: int = Field(default=120, ge=5)


class SovereignOpenRouterConfig(BaseModel):
    """Root config model loaded from openrouter.yaml."""

    api_key: str
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    thinking: ThinkingConfig = Field(default_factory=ThinkingConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    identity: IdentityConfig = Field(default_factory=IdentityConfig)
    system_prompt: SystemPromptConfig = Field(default_factory=SystemPromptConfig)
    compatibility: CompatibilityConfig = Field(default_factory=CompatibilityConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_empty(cls, value: str) -> str:
        if not value or value.strip() == "":
            raise ValueError("api_key resolved to empty string - check env var")
        return value


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def absorb(self, usage_dict: Dict[str, int]) -> None:
        self.prompt_tokens += usage_dict.get("prompt_tokens", 0)
        self.completion_tokens += usage_dict.get("completion_tokens", 0)
        self.total_tokens += usage_dict.get("total_tokens", 0)


@dataclass
class CostEntry:
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    request_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RouteAttempt:
    model: str
    success: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class CompletionResponse:
    content: str
    model: str
    requested_model: str
    usage: Dict[str, int]
    finish_reason: str
    raw: Dict[str, Any]
    latency_ms: float
    route_attempts: List[RouteAttempt]
    request_id: Optional[str] = None


@dataclass
class BatchResult:
    model: str
    requested_model: str
    content: str
    usage: Dict[str, int]
    latency_ms: float
    fallback_used: bool = False
    error: Optional[str] = None


class CostTracker:
    """Per-session token and cost accumulator."""

    def __init__(self) -> None:
        self._entries: List[CostEntry] = []
        self._total_usage = TokenUsage()
        self._lock = Lock()

    def record(
        self,
        model: str,
        usage: Dict[str, int],
        headers: httpx.Headers,
        request_id: Optional[str],
        record_cost: bool,
        observed_cost_usd: Optional[float] = None,
    ) -> None:
        if record_cost:
            header_cost = _extract_cost_from_headers(headers)
            cost_usd = observed_cost_usd if observed_cost_usd is not None else header_cost
            if cost_usd == 0.0 and observed_cost_usd is None:
                cost_usd = header_cost
        else:
            cost_usd = 0.0
        entry = CostEntry(
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            cost_usd=cost_usd,
            request_id=request_id,
        )
        with self._lock:
            self._entries.append(entry)
            self._total_usage.absorb(usage)

    def report(self) -> Dict[str, Any]:
        with self._lock:
            entries = list(self._entries)
            totals = TokenUsage(
                prompt_tokens=self._total_usage.prompt_tokens,
                completion_tokens=self._total_usage.completion_tokens,
                total_tokens=self._total_usage.total_tokens,
            )

        return {
            "session_totals": {
                "prompt_tokens": totals.prompt_tokens,
                "completion_tokens": totals.completion_tokens,
                "total_tokens": totals.total_tokens,
                "total_cost_usd": round(sum(entry.cost_usd for entry in entries), 6),
            },
            "calls": len(entries),
            "breakdown": [
                {
                    "model": entry.model,
                    "tokens": entry.prompt_tokens + entry.completion_tokens,
                    "cost_usd": entry.cost_usd,
                    "request_id": entry.request_id,
                    "ts": entry.timestamp,
                }
                for entry in entries
            ],
        }

    def reset(self) -> None:
        with self._lock:
            self._entries.clear()
            self._total_usage = TokenUsage()


def _extract_cost_from_headers(headers: httpx.Headers) -> float:
    for key in ("x-openrouter-credits-used", "x-openrouter-cost", "x-openrouter-total-cost"):
        raw_value = headers.get(key)
        if raw_value is None:
            continue
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _interpolate_env(value: Any) -> Any:
    """Recursively resolve ${ENV_VAR} patterns inside a YAML-derived structure."""
    if isinstance(value, str):
        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            resolved = os.environ.get(var_name)
            if resolved is None:
                raise ConfigError(
                    f"Environment variable '{var_name}' is not set. Required by openrouter.yaml."
                )
            return resolved

        return ENV_VAR_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {key: _interpolate_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_interpolate_env(item) for item in value]
    return value


def load_config(yaml_path: str | Path) -> SovereignOpenRouterConfig:
    """Load and validate openrouter.yaml into SovereignOpenRouterConfig."""
    path = Path(yaml_path).expanduser()
    if not path.exists():
        raise ConfigError(f"Config file not found: {path.resolve()}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"YAML root in {path} must be a mapping")

    root = raw.get("sovereign_openrouter")
    if root is None:
        raise ConfigError(
            "YAML root key 'sovereign_openrouter' not found. Check openrouter.yaml structure."
        )
    if not isinstance(root, dict):
        raise ConfigError("'sovereign_openrouter' must be a mapping")

    try:
        interpolated = _interpolate_env(root)
        return SovereignOpenRouterConfig(**interpolated)
    except ConfigError:
        raise
    except ValidationError as exc:
        raise ConfigError(f"Config validation failed: {exc}") from exc


def _resolve_system_prompt(cfg: SystemPromptConfig, base_dir: Path) -> Optional[str]:
    """Resolve a prompt template path relative to the YAML file before treating it as inline text."""
    if not cfg.enabled or not cfg.template:
        return None

    candidate = Path(cfg.template)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    if candidate.exists():
        return candidate.read_text(encoding="utf-8").strip() or None
    return cfg.template.strip() or None


def _inject_system_prompt(
    messages: List[Dict[str, Any]],
    system_text: str,
    mode: InjectMode,
) -> List[Dict[str, Any]]:
    """Inject a system prompt into a copied message list."""
    system_msg = {"role": "system", "content": system_text}

    if mode == InjectMode.REPLACE:
        filtered = [message for message in messages if message.get("role") != "system"]
        return [system_msg] + filtered

    if mode == InjectMode.PREPEND:
        if messages and messages[0].get("role") == "system":
            first = dict(messages[0])
            first_content = first.get("content")
            if isinstance(first_content, str):
                first["content"] = system_text + "\n\n" + first_content
                return [first] + messages[1:]
        return [system_msg] + messages

    if mode == InjectMode.APPEND:
        return messages + [system_msg]

    return messages


async def _with_retry(
    coro_factory: Callable[[], Awaitable[Any]],
    max_attempts: int,
    backoff_base: float,
    backoff_max: float,
    label: str,
) -> Any:
    """Execute coro_factory() with retry semantics for timeout/network/429/5xx failures."""
    last_exc: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_factory()
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            wait_seconds = min(backoff_base ** attempt, backoff_max)
            logger.warning(
                "[sovereign.openrouter] %s attempt %d/%d failed (%s). Retrying in %.1fs.",
                label,
                attempt,
                max_attempts,
                type(exc).__name__,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code != 429 and status_code < 500:
                raise
            last_exc = exc
            if attempt == max_attempts:
                break
            wait_seconds = min(backoff_base ** attempt, backoff_max)
            logger.warning(
                "[sovereign.openrouter] %s HTTP %d on attempt %d/%d. Retrying in %.1fs.",
                label,
                status_code,
                attempt,
                max_attempts,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)

    raise RoutingError(
        f"All {max_attempts} retry attempts exhausted for {label}. Last error: {last_exc}"
    ) from last_exc


def _coerce_usage_dict(raw_usage: Any) -> Dict[str, int]:
    if not isinstance(raw_usage, dict):
        return {}

    usage: Dict[str, int] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        raw_value = raw_usage.get(key, 0)
        try:
            usage[key] = int(raw_value)
        except (TypeError, ValueError):
            usage[key] = 0

    if usage["total_tokens"] == 0:
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    return usage


def _extract_usage_cost(raw_usage: Any) -> Optional[float]:
    if not isinstance(raw_usage, dict):
        return None

    raw_cost = raw_usage.get("cost")
    try:
        return float(raw_cost) if raw_cost is not None else None
    except (TypeError, ValueError):
        return None


def _extract_request_id(headers: httpx.Headers, data: Optional[Dict[str, Any]] = None) -> Optional[str]:
    for header_name in REQUEST_ID_HEADERS:
        request_id = headers.get(header_name)
        if request_id:
            return request_id
    if isinstance(data, dict):
        raw_id = data.get("id")
        if isinstance(raw_id, str) and raw_id:
            return raw_id
    return None


def _should_retry_status(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def _extract_stream_text(chunk: Dict[str, Any]) -> str:
    choices = chunk.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    delta = choices[0].get("delta", {})
    if not isinstance(delta, dict):
        return ""
    content = delta.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type in {"text", "output_text"}:
                text = block.get("text") or block.get("content") or ""
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class SovereignOpenRouterClient:
    """Async-first sovereign OpenRouter client with hot-reload-safe HTTP swapping."""

    def __init__(self, config: SovereignOpenRouterConfig, yaml_path: Path) -> None:
        self._config = config
        self._yaml_path = yaml_path
        self._cost_tracker = CostTracker()
        self._http: Optional[httpx.AsyncClient] = None
        self._state_lock = asyncio.Lock()
        self._client_ref_counts: Dict[int, int] = {}
        self._client_idle_events: Dict[int, asyncio.Event] = {}

    @classmethod
    async def create(cls, yaml_path: str | Path) -> "SovereignOpenRouterClient":
        path = Path(yaml_path).expanduser()
        config = load_config(path)
        instance = cls(config, path)
        await instance._replace_http_client(config)
        logger.info(
            "[sovereign.openrouter] Client initialized. Default model: %s | Strategy: %s",
            config.defaults.model,
            config.routing.strategy,
        )
        return instance

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: Optional[bool] = None,
        system_prompt_override: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        allow_fallbacks: bool = True,
    ) -> CompletionResponse:
        cfg, http_client, client_key = await self._acquire_runtime()
        try:
            requested_model = model or cfg.defaults.model
            resolved_messages = self._prepare_messages(messages, system_prompt_override, cfg)
            provider_chain = self._build_provider_chain(
                primary_model=requested_model,
                routing_cfg=cfg.routing,
                allow_fallbacks=allow_fallbacks,
            )
            route_attempts: List[RouteAttempt] = []

            for provider_model in provider_chain:
                payload = self._build_payload(
                    messages=resolved_messages,
                    model=provider_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking=thinking,
                    stream=False,
                    extra_params=extra_params,
                    cfg=cfg,
                )
                label = f"complete:{provider_model}"
                started_at = time.monotonic()

                if self._should_complete_via_stream(provider_model, cfg):
                    response = await self._complete_via_stream_response(
                        http_client=http_client,
                        cfg=cfg,
                        payload=payload,
                        provider_model=provider_model,
                        requested_model=requested_model,
                        route_attempts=route_attempts,
                        started_at=started_at,
                        label=label,
                    )
                    return response

                try:
                    response = await _with_retry(
                        coro_factory=lambda p=payload: self._post(http_client, "/chat/completions", p),
                        max_attempts=cfg.retry.max_attempts,
                        backoff_base=cfg.retry.backoff_base,
                        backoff_max=cfg.retry.backoff_max,
                        label=label,
                    )
                except RoutingError as exc:
                    route_attempts.append(RouteAttempt(model=provider_model, success=False, error=str(exc)))
                    logger.warning(
                        "[sovereign.openrouter] Provider %s exhausted: %s. Trying next in chain.",
                        provider_model,
                        exc,
                    )
                    continue

                latency_ms = (time.monotonic() - started_at) * 1000
                data = self._parse_response_json(response, label)
                raw_usage = data.get("usage")
                usage = _coerce_usage_dict(raw_usage)
                observed_cost_usd = _extract_usage_cost(raw_usage)
                finish_reason = self._extract_finish_reason(data)
                content = self._extract_content(data)
                request_id = _extract_request_id(response.headers, data)
                self._record_usage(
                    provider_model,
                    usage,
                    response.headers,
                    request_id,
                    cfg,
                    observed_cost_usd=observed_cost_usd,
                )

                route_attempts.append(
                    RouteAttempt(
                        model=provider_model,
                        success=True,
                        latency_ms=latency_ms,
                        request_id=request_id,
                    )
                )

                if cfg.observability.log_responses:
                    logger.debug(
                        "[sovereign.openrouter] Response summary model=%s request_id=%s finish_reason=%s usage=%s",
                        provider_model,
                        request_id,
                        finish_reason,
                        usage,
                    )

                return CompletionResponse(
                    content=content,
                    model=provider_model,
                    requested_model=requested_model,
                    usage=usage,
                    finish_reason=finish_reason,
                    raw=data,
                    latency_ms=latency_ms,
                    route_attempts=route_attempts,
                    request_id=request_id,
                )

            raise RoutingError(
                f"All providers exhausted. Chain: {provider_chain}. Check network, API key, and model availability."
            )
        finally:
            await self._release_runtime(client_key)

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: Optional[bool] = None,
        system_prompt_override: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        allow_fallbacks: bool = True,
    ) -> AsyncIterator[str]:
        cfg, http_client, client_key = await self._acquire_runtime()
        try:
            requested_model = model or cfg.defaults.model
            resolved_messages = self._prepare_messages(messages, system_prompt_override, cfg)
            provider_chain = self._build_provider_chain(
                primary_model=requested_model,
                routing_cfg=cfg.routing,
                allow_fallbacks=allow_fallbacks,
            )

            for provider_model in provider_chain:
                payload = self._build_payload(
                    messages=resolved_messages,
                    model=provider_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking=thinking,
                    stream=True,
                    extra_params=extra_params,
                    cfg=cfg,
                )
                label = f"stream:{provider_model}"
                last_exc: Optional[Exception] = None

                for attempt in range(1, cfg.retry.max_attempts + 1):
                    yielded_any_output = False
                    usage: Dict[str, int] = {}
                    observed_cost_usd: Optional[float] = None
                    request_id: Optional[str] = None

                    try:
                        async with http_client.stream("POST", "/chat/completions", json=payload) as response:
                            response.raise_for_status()
                            request_id = _extract_request_id(response.headers)

                            async for line in response.aiter_lines():
                                if not line:
                                    continue
                                if line == "data: [DONE]":
                                    break
                                if not line.startswith("data: "):
                                    continue

                                raw_json = line[6:]
                                chunk = self._parse_stream_chunk(raw_json, provider_model)
                                raw_chunk_usage = chunk.get("usage")
                                chunk_usage = _coerce_usage_dict(raw_chunk_usage)
                                if chunk_usage:
                                    usage = chunk_usage
                                chunk_cost = _extract_usage_cost(raw_chunk_usage)
                                if chunk_cost is not None:
                                    observed_cost_usd = chunk_cost
                                text = _extract_stream_text(chunk)
                                if text:
                                    yielded_any_output = True
                                    yield text

                            self._record_usage(
                                provider_model,
                                usage,
                                response.headers,
                                request_id,
                                cfg,
                                observed_cost_usd=observed_cost_usd,
                            )
                            return
                    except httpx.HTTPStatusError as exc:
                        last_exc = exc
                        if yielded_any_output:
                            raise StreamError(
                                f"Streaming interrupted after partial output from {provider_model}: HTTP {exc.response.status_code}"
                            ) from exc
                        if not _should_retry_status(exc.response.status_code) or attempt == cfg.retry.max_attempts:
                            break
                    except (httpx.TimeoutException, httpx.NetworkError) as exc:
                        last_exc = exc
                        if yielded_any_output:
                            raise StreamError(
                                f"Streaming interrupted after partial output from {provider_model}: {type(exc).__name__}"
                            ) from exc
                        if attempt == cfg.retry.max_attempts:
                            break
                    except StreamError as exc:
                        last_exc = exc
                        if yielded_any_output:
                            raise
                        if attempt == cfg.retry.max_attempts:
                            break

                    wait_seconds = min(cfg.retry.backoff_base ** attempt, cfg.retry.backoff_max)
                    logger.warning(
                        "[sovereign.openrouter] %s attempt %d/%d failed (%s). Retrying in %.1fs.",
                        label,
                        attempt,
                        cfg.retry.max_attempts,
                        type(last_exc).__name__ if last_exc else "unknown",
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)

                logger.warning(
                    "[sovereign.openrouter] Provider %s exhausted for streaming: %s",
                    provider_model,
                    last_exc,
                )

            raise RoutingError(
                f"All providers exhausted for streaming. Chain: {provider_chain}. Check network, API key, and model availability."
            )
        finally:
            await self._release_runtime(client_key)

    async def batch(
        self,
        messages: List[Dict[str, Any]],
        models: Optional[List[str]] = None,
        rank_by: BatchRankBy = BatchRankBy.QUALITY,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        allow_fallbacks: Optional[bool] = None,
    ) -> List[BatchResult]:
        cfg_snapshot = self._config.model_copy(deep=True)
        target_models = models or self._default_batch_models(cfg_snapshot)
        if not target_models:
            raise BatchError("Batch requires at least one target model")

        resolved_allow_fallbacks = (
            cfg_snapshot.routing.allow_fallbacks_in_batch
            if allow_fallbacks is None
            else allow_fallbacks
        )

        async def _single(model_id: str) -> BatchResult:
            started_at = time.monotonic()
            try:
                response = await self.complete(
                    messages=messages,
                    model=model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    allow_fallbacks=resolved_allow_fallbacks,
                )
                latency_ms = (time.monotonic() - started_at) * 1000
                return BatchResult(
                    model=response.model,
                    requested_model=model_id,
                    content=response.content,
                    usage=response.usage,
                    latency_ms=latency_ms,
                    fallback_used=response.model != model_id,
                )
            except Exception as exc:
                latency_ms = (time.monotonic() - started_at) * 1000
                logger.warning(
                    "[sovereign.openrouter] Batch model %s failed: %s",
                    model_id,
                    exc,
                )
                return BatchResult(
                    model=model_id,
                    requested_model=model_id,
                    content="",
                    usage={},
                    latency_ms=latency_ms,
                    error=str(exc),
                )

        results = list(await asyncio.gather(*[_single(model_id) for model_id in target_models]))
        successful = [result for result in results if result.error is None]
        failed = [result for result in results if result.error is not None]

        if not successful and failed:
            return failed

        if rank_by == BatchRankBy.LATENCY:
            successful.sort(key=lambda result: result.latency_ms)
        elif rank_by == BatchRankBy.COST:
            successful.sort(
                key=lambda result: (
                    self._profile_rank(cfg_snapshot.routing.model_profiles, result.model, "cost_rank"),
                    result.usage.get("total_tokens", 0),
                )
            )
        elif rank_by == BatchRankBy.QUALITY:
            successful.sort(
                key=lambda result: (
                    self._profile_rank(cfg_snapshot.routing.model_profiles, result.model, "quality_rank"),
                    -len(result.content),
                )
            )

        return successful + failed

    async def get_models(self, filter_free: bool = False) -> List[Dict[str, Any]]:
        cfg, http_client, client_key = await self._acquire_runtime()
        try:
            response = await _with_retry(
                coro_factory=lambda: self._get(http_client, "/models"),
                max_attempts=cfg.retry.max_attempts,
                backoff_base=cfg.retry.backoff_base,
                backoff_max=cfg.retry.backoff_max,
                label="models",
            )
            data = self._parse_response_json(response, "models")
            models = data.get("data", [])
            if not isinstance(models, list):
                raise APIResponseError("OpenRouter model catalog response is missing a data list")

            if filter_free:
                models = [model for model in models if self._model_is_zero_cost(model)]
            return models
        finally:
            await self._release_runtime(client_key)

    def cost_report(self) -> Dict[str, Any]:
        report = self._cost_tracker.report()
        if self._config.observability.session_id:
            report["session_id"] = self._config.observability.session_id
        return report

    def config_summary(self) -> Dict[str, Any]:
        cfg = self._config
        return {
            "active_model": cfg.defaults.model,
            "routing_strategy": cfg.routing.strategy.value,
            "fallback_chain": list(cfg.routing.fallback_chain),
            "allow_fallbacks_in_batch": cfg.routing.allow_fallbacks_in_batch,
            "thinking_enabled": cfg.thinking.enabled,
            "thinking_mode": cfg.thinking.mode.value,
            "complete_via_stream_models": list(cfg.compatibility.complete_via_stream_models),
            "timeout_seconds": cfg.defaults.timeout_seconds,
            "session_id": cfg.observability.session_id,
        }

    async def reload_config(self) -> None:
        new_config = load_config(self._yaml_path)
        await self._replace_http_client(new_config)
        logger.info(
            "[sovereign.openrouter] Config reloaded. New model: %s | Strategy: %s",
            new_config.defaults.model,
            new_config.routing.strategy,
        )

    async def close(self) -> None:
        async with self._state_lock:
            old_http = self._http
            self._http = None
        if old_http is not None:
            await self._retire_http_client(old_http)

    def _prepare_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt_override: Optional[str],
        cfg: SovereignOpenRouterConfig,
    ) -> List[Dict[str, Any]]:
        copied_messages = deepcopy(messages)
        prompt_text = system_prompt_override
        if prompt_text is None:
            prompt_text = _resolve_system_prompt(cfg.system_prompt, self._yaml_path.parent)
        if prompt_text:
            return _inject_system_prompt(copied_messages, prompt_text, cfg.system_prompt.inject_mode)
        return copied_messages

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        thinking: Optional[bool],
        stream: bool,
        extra_params: Optional[Dict[str, Any]],
        cfg: SovereignOpenRouterConfig,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else cfg.defaults.temperature,
            "max_tokens": max_tokens if max_tokens is not None else cfg.defaults.max_tokens,
            "stream": stream,
        }

        if self._resolve_thinking_enabled(model, thinking, cfg):
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": cfg.thinking.budget_tokens,
            }

        if extra_params:
            payload.update(extra_params)

        if cfg.observability.log_requests:
            safe_payload = {
                **payload,
                "messages": f"[{len(messages)} messages]",
            }
            logger.debug("[sovereign.openrouter] Request payload: %s", json.dumps(safe_payload))

        return payload

    def _resolve_thinking_enabled(
        self,
        model: str,
        thinking: Optional[bool],
        cfg: SovereignOpenRouterConfig,
    ) -> bool:
        mode = cfg.thinking.mode
        if mode == ThinkingMode.DISABLED:
            return False
        if mode == ThinkingMode.FORCE:
            enabled = True
        elif thinking is not None:
            enabled = thinking
        else:
            enabled = cfg.thinking.enabled

        if enabled and not self._model_supports_thinking(model, cfg):
            raise ThinkingError(
                f"Thinking mode requested for model '{model}', but it is not marked as thinking-capable in config."
            )
        return enabled

    def _should_complete_via_stream(
        self,
        model: str,
        cfg: SovereignOpenRouterConfig,
    ) -> bool:
        configured_models = cfg.compatibility.complete_via_stream_models
        return model in configured_models

    def _model_supports_thinking(self, model: str, cfg: SovereignOpenRouterConfig) -> bool:
        profile = cfg.routing.model_profiles.get(model)
        if profile and profile.thinking_supported is not None:
            return profile.thinking_supported
        prefixes = cfg.thinking.supported_model_prefixes
        if not prefixes:
            return True
        return any(model.startswith(prefix) for prefix in prefixes)

    def _build_provider_chain(
        self,
        primary_model: str,
        routing_cfg: RoutingConfig,
        allow_fallbacks: bool,
    ) -> List[str]:
        if not allow_fallbacks:
            return [primary_model]

        chain = self._dedupe_models([primary_model, *routing_cfg.fallback_chain])
        if len(chain) <= 1:
            return chain[: routing_cfg.max_fallback_attempts]

        primary = chain[0]
        fallbacks = chain[1:]
        strategy = routing_cfg.strategy

        if strategy == RoutingStrategy.COST:
            fallbacks.sort(key=lambda model: self._profile_rank(routing_cfg.model_profiles, model, "cost_rank"))
        elif strategy == RoutingStrategy.LATENCY:
            fallbacks.sort(
                key=lambda model: self._profile_rank(routing_cfg.model_profiles, model, "latency_rank")
            )
        elif strategy == RoutingStrategy.QUALITY:
            fallbacks.sort(
                key=lambda model: self._profile_rank(routing_cfg.model_profiles, model, "quality_rank")
            )
        elif strategy == RoutingStrategy.COST_LATENCY:
            fallbacks.sort(
                key=lambda model: (
                    self._profile_rank(routing_cfg.model_profiles, model, "cost_rank"),
                    self._profile_rank(routing_cfg.model_profiles, model, "latency_rank"),
                )
            )

        limited_chain = [primary] + fallbacks
        return limited_chain[: routing_cfg.max_fallback_attempts]

    def _default_batch_models(self, cfg: SovereignOpenRouterConfig) -> List[str]:
        return self._build_provider_chain(
            primary_model=cfg.defaults.model,
            routing_cfg=cfg.routing,
            allow_fallbacks=True,
        )

    async def _complete_via_stream_response(
        self,
        http_client: httpx.AsyncClient,
        cfg: SovereignOpenRouterConfig,
        payload: Dict[str, Any],
        provider_model: str,
        requested_model: str,
        route_attempts: List[RouteAttempt],
        started_at: float,
        label: str,
    ) -> CompletionResponse:
        last_exc: Optional[Exception] = None
        stream_payload = dict(payload)
        stream_payload["stream"] = True

        for attempt in range(1, cfg.retry.max_attempts + 1):
            yielded_any_output = False
            usage: Dict[str, int] = {}
            observed_cost_usd: Optional[float] = None
            request_id: Optional[str] = None
            content_parts: List[str] = []
            finish_reason = "unknown"
            actual_model = provider_model
            raw_chunks: List[Dict[str, Any]] = []

            try:
                async with http_client.stream("POST", "/chat/completions", json=stream_payload) as response:
                    response.raise_for_status()
                    request_id = _extract_request_id(response.headers)

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line == "data: [DONE]":
                            break
                        if not line.startswith("data: "):
                            continue

                        raw_json = line[6:]
                        chunk = self._parse_stream_chunk(raw_json, provider_model)
                        raw_chunks.append(chunk)
                        actual_model = chunk.get("model", actual_model)
                        request_id = request_id or _extract_request_id(response.headers, chunk)

                        raw_chunk_usage = chunk.get("usage")
                        chunk_usage = _coerce_usage_dict(raw_chunk_usage)
                        if chunk_usage:
                            usage = chunk_usage
                        chunk_cost = _extract_usage_cost(raw_chunk_usage)
                        if chunk_cost is not None:
                            observed_cost_usd = chunk_cost

                        text = _extract_stream_text(chunk)
                        if text:
                            yielded_any_output = True
                            content_parts.append(text)

                        choices = chunk.get("choices")
                        if isinstance(choices, list) and choices:
                            choice0 = choices[0]
                            if isinstance(choice0, dict):
                                chunk_finish_reason = choice0.get("finish_reason")
                                if isinstance(chunk_finish_reason, str) and chunk_finish_reason:
                                    finish_reason = chunk_finish_reason

                    latency_ms = (time.monotonic() - started_at) * 1000
                    content = "".join(content_parts)
                    self._record_usage(
                        provider_model,
                        usage,
                        response.headers,
                        request_id,
                        cfg,
                        observed_cost_usd=observed_cost_usd,
                    )
                    route_attempts.append(
                        RouteAttempt(
                            model=provider_model,
                            success=True,
                            latency_ms=latency_ms,
                            request_id=request_id,
                        )
                    )
                    return CompletionResponse(
                        content=content,
                        model=actual_model,
                        requested_model=requested_model,
                        usage=usage,
                        finish_reason=finish_reason,
                        raw={"stream_chunks": raw_chunks},
                        latency_ms=latency_ms,
                        route_attempts=route_attempts,
                        request_id=request_id,
                    )
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if yielded_any_output:
                    raise StreamError(
                        f"Streaming completion recovery interrupted after partial output from {provider_model}: HTTP {exc.response.status_code}"
                    ) from exc
                if not _should_retry_status(exc.response.status_code) or attempt == cfg.retry.max_attempts:
                    break
            except (httpx.TimeoutException, httpx.NetworkError, StreamError) as exc:
                last_exc = exc
                if yielded_any_output:
                    raise StreamError(
                        f"Streaming completion recovery interrupted after partial output from {provider_model}: {type(exc).__name__}"
                    ) from exc
                if attempt == cfg.retry.max_attempts:
                    break

            wait_seconds = min(cfg.retry.backoff_base ** attempt, cfg.retry.backoff_max)
            logger.warning(
                "[sovereign.openrouter] %s compatibility-stream attempt %d/%d failed (%s). Retrying in %.1fs.",
                label,
                attempt,
                cfg.retry.max_attempts,
                type(last_exc).__name__ if last_exc else "unknown",
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)

        route_attempts.append(RouteAttempt(model=provider_model, success=False, error=str(last_exc)))
        raise RoutingError(
            f"All compatibility-stream attempts exhausted for {label}. Last error: {last_exc}"
        ) from last_exc

    @staticmethod
    def _dedupe_models(models: List[str]) -> List[str]:
        deduped: List[str] = []
        seen = set()
        for model in models:
            if not model or model in seen:
                continue
            seen.add(model)
            deduped.append(model)
        return deduped

    @staticmethod
    def _profile_rank(
        profiles: Dict[str, ModelProfile],
        model: str,
        field_name: str,
    ) -> int:
        profile = profiles.get(model)
        if profile is None:
            return 10_000
        return int(getattr(profile, field_name))

    async def _replace_http_client(self, config: SovereignOpenRouterConfig) -> None:
        new_http = self._build_http_client(config)

        async with self._state_lock:
            old_http = self._http
            self._http = new_http
            self._config = config
            new_key = id(new_http)
            idle_event = asyncio.Event()
            idle_event.set()
            self._client_ref_counts[new_key] = 0
            self._client_idle_events[new_key] = idle_event

        if old_http is not None:
            await self._retire_http_client(old_http)

    async def _acquire_runtime(self) -> Tuple[SovereignOpenRouterConfig, httpx.AsyncClient, int]:
        async with self._state_lock:
            if self._http is None:
                raise RuntimeError("SovereignOpenRouterClient is closed")

            http_client = self._http
            client_key = id(http_client)
            self._client_ref_counts[client_key] = self._client_ref_counts.get(client_key, 0) + 1
            idle_event = self._client_idle_events.setdefault(client_key, asyncio.Event())
            idle_event.clear()
            return self._config.model_copy(deep=True), http_client, client_key

    async def _release_runtime(self, client_key: int) -> None:
        async with self._state_lock:
            current_refs = self._client_ref_counts.get(client_key, 0)
            if current_refs <= 1:
                self._client_ref_counts[client_key] = 0
                self._client_idle_events.setdefault(client_key, asyncio.Event()).set()
            else:
                self._client_ref_counts[client_key] = current_refs - 1

    async def _retire_http_client(self, http_client: httpx.AsyncClient) -> None:
        client_key = id(http_client)
        idle_event = self._client_idle_events.setdefault(client_key, asyncio.Event())

        async with self._state_lock:
            if self._client_ref_counts.get(client_key, 0) == 0:
                idle_event.set()

        await idle_event.wait()
        await http_client.aclose()

        async with self._state_lock:
            self._client_ref_counts.pop(client_key, None)
            self._client_idle_events.pop(client_key, None)

    def _build_http_client(self, config: SovereignOpenRouterConfig) -> httpx.AsyncClient:
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-Title": config.identity.title,
        }
        if config.identity.referer:
            headers["HTTP-Referer"] = config.identity.referer
        headers.update(config.identity.extra_headers)

        return httpx.AsyncClient(
            base_url=OPENROUTER_BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(config.defaults.timeout_seconds),
        )

    async def _post(
        self,
        http_client: httpx.AsyncClient,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> httpx.Response:
        response = await http_client.post(endpoint, json=payload)
        response.raise_for_status()
        return response

    async def _get(self, http_client: httpx.AsyncClient, endpoint: str) -> httpx.Response:
        response = await http_client.get(endpoint)
        response.raise_for_status()
        return response

    def _parse_response_json(self, response: httpx.Response, label: str) -> Dict[str, Any]:
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise APIResponseError(f"{label} returned non-JSON response") from exc
        if not isinstance(data, dict):
            raise APIResponseError(f"{label} returned JSON that is not an object")
        return data

    def _parse_stream_chunk(self, raw_json: str, provider_model: str) -> Dict[str, Any]:
        try:
            chunk = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise StreamError(f"Invalid SSE JSON from {provider_model}") from exc
        if not isinstance(chunk, dict):
            raise StreamError(f"Invalid SSE payload type from {provider_model}")
        if "error" in chunk:
            raise StreamError(f"Upstream streaming error from {provider_model}: {chunk['error']}")
        return chunk

    def _record_usage(
        self,
        model: str,
        usage: Dict[str, int],
        headers: httpx.Headers,
        request_id: Optional[str],
        cfg: SovereignOpenRouterConfig,
        observed_cost_usd: Optional[float] = None,
    ) -> None:
        if not (cfg.observability.token_tracking or cfg.observability.cost_tracking):
            return
        self._cost_tracker.record(
            model=model,
            usage=usage,
            headers=headers,
            request_id=request_id,
            record_cost=cfg.observability.cost_tracking,
            observed_cost_usd=observed_cost_usd,
        )

    @staticmethod
    def _extract_finish_reason(data: Dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return "unknown"
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return "unknown"
        finish_reason = first_choice.get("finish_reason", "unknown")
        return finish_reason if isinstance(finish_reason, str) else "unknown"

    @staticmethod
    def _extract_content(data: Dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return ""

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return ""

        message = first_choice.get("message", {})
        if not isinstance(message, dict):
            return ""

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") in {"text", "output_text"}:
                    text = block.get("text") or block.get("content") or ""
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return ""

    @staticmethod
    def _model_is_zero_cost(model: Dict[str, Any]) -> bool:
        pricing = model.get("pricing", {})
        if not isinstance(pricing, dict):
            return False
        prompt_price = pricing.get("prompt")
        completion_price = pricing.get("completion")
        try:
            return float(prompt_price) == 0.0 and float(completion_price) == 0.0
        except (TypeError, ValueError):
            return False


class SovereignOpenRouter:
    """Async context manager wrapper for SovereignOpenRouterClient."""

    def __init__(self, yaml_path: str | Path) -> None:
        self._yaml_path = yaml_path
        self._client: Optional[SovereignOpenRouterClient] = None

    async def __aenter__(self) -> SovereignOpenRouterClient:
        self._client = await SovereignOpenRouterClient.create(self._yaml_path)
        return self._client

    async def __aexit__(self, *_) -> None:
        if self._client:
            await self._client.close()
