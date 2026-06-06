"""
Production Module: Sovereign OpenRouter BB7 Wrapper
Source: Somnus Sovereign Systems
Created: 2026-03-06
Status: Production Stable

Wrapper exposing SovereignOpenRouterClient as BB7 exoskeleton tools.
Follows OPSEC thin-wrapper pattern: translate interface, never rewrite logic.

Tools Exposed:
- or_complete       : Single completion call
- or_stream         : Streaming completion (returns full joined string)
- or_batch          : Parallel multi-model execution
- or_model_list     : Live model catalog from OpenRouter
- or_cost_report    : Session token and cost summary
- or_config_reload  : Hot-reload YAML config without restart
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_SOVEREIGN_OR_AVAILABLE = False
_SOVEREIGN_OR_IMPORT_ERROR: Optional[Exception] = None

try:
    from databus.sovereign_openrouter import (
        BatchRankBy,
        SovereignOpenRouterClient,
        load_config,
    )
    _SOVEREIGN_OR_AVAILABLE = True
except Exception as exc_primary:  # pragma: no cover - standalone fallback
    try:
        from sovereign_openrouter import (  # type: ignore[no-redef]
            BatchRankBy,
            SovereignOpenRouterClient,
            load_config,
        )
        _SOVEREIGN_OR_AVAILABLE = True
    except Exception as exc_fallback:
        _SOVEREIGN_OR_IMPORT_ERROR = exc_fallback or exc_primary
        BatchRankBy = None  # type: ignore[assignment,misc]
        SovereignOpenRouterClient = None  # type: ignore[assignment,misc]
        load_config = None  # type: ignore[assignment,misc]

logger = logging.getLogger("sovereign.openrouter.wrapper")
distill_logger = logging.getLogger("sovereign.openrouter.distillation")

_DEFAULT_CANON_DATA_DIR = Path(
    os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data")
).expanduser().resolve()


class OpenRouterDistillationLogger:
    """
    Always-on async distillation writer for OpenRouter tool planes.

    Writes schema v2 trajectory records to:
      - <data_dir>/distillation_dataset/trajectories_YYYY-MM-DD.jsonl
      - <data_dir>/distillation/trajectories_YYYY-MM-DD.jsonl (legacy compatibility)

    Also emits:
      - trajectory_index.jsonl
      - high_value/high_value_YYYY-MM-DD.jsonl
      - failures/failures_YYYY-MM-DD.jsonl
    """

    SCHEMA_VERSION = "2.0"
    ERROR_MARKERS = (
        "error:",
        "failed",
        "exception",
        "traceback",
        "timeout",
        "http error",
        "url error",
    )

    def __init__(self, data_dir: Optional[Path] = None, logger_: Optional[logging.Logger] = None) -> None:
        self.data_dir = Path(data_dir or _DEFAULT_CANON_DATA_DIR).expanduser().resolve()
        self.dataset_dir = self.data_dir / "distillation_dataset"
        self.legacy_dir = self.data_dir / "distillation"
        self.high_value_dir = self.dataset_dir / "high_value"
        self.failure_dir = self.dataset_dir / "failures"
        self.index_path = self.dataset_dir / "trajectory_index.jsonl"
        self.logger = logger_ or distill_logger

        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_dir.mkdir(parents=True, exist_ok=True)
        self.high_value_dir.mkdir(parents=True, exist_ok=True)
        self.failure_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._write_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name="sovereign-openrouter-distill-writer",
            daemon=True,
        )
        self._writer_thread.start()

    def log_trajectory(
        self,
        *,
        source_plane: str,
        session_id: str,
        trajectory: List[Dict[str, Any]],
        telemetry: Optional[Dict[str, Any]] = None,
        intent_provenance: Optional[Dict[str, Any]] = None,
        memory_context_at_start: Optional[Dict[str, Any]] = None,
        thought_journal_entries: Optional[List[Dict[str, Any]]] = None,
        parent_trajectory_id: Optional[str] = None,
        linked_trajectory_ids: Optional[List[str]] = None,
        environment_snapshot: Optional[Dict[str, Any]] = None,
        capture_mode: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        safe_trajectory = self._sanitize_trajectory(trajectory)
        safe_telemetry = dict(telemetry or {})
        safe_telemetry.setdefault("tool_call_count", self._count_tool_calls(safe_trajectory))
        safe_telemetry.setdefault("tool_error_count", self._count_tool_errors(safe_trajectory))

        heuristics, auto_tags = self._evaluate_quality(
            safe_trajectory,
            safe_telemetry,
            intent_provenance or {},
            memory_context_at_start or {},
        )
        trajectory_id = str(uuid.uuid4())
        entry = {
            "schema_version": self.SCHEMA_VERSION,
            "trajectory_id": trajectory_id,
            "parent_trajectory_id": parent_trajectory_id,
            "linked_trajectory_ids": list(linked_trajectory_ids or []),
            "timestamp": time.time(),
            "session_id": session_id,
            "source_plane": source_plane,
            "environment_snapshot": environment_snapshot or {},
            "intent_provenance": intent_provenance or {},
            "memory_context_at_start": memory_context_at_start or {},
            "quality_matrix": {
                "status": "unreviewed",
                "score": None,
                "heuristics": heuristics,
                "auto_tags": auto_tags,
                "human_labels": [],
            },
            "trajectory": safe_trajectory,
            "telemetry": safe_telemetry,
            "thought_journal_entries": list(thought_journal_entries or []),
            "context": context or {},
            "distill_meta": {
                "capture_mode": capture_mode or "openrouter_tool_plane",
                "stdio_transcript_ref": None,
                "write_latency_ms": None,
                "queue_depth_at_write": self._write_queue.qsize(),
            },
            "_write_started_at": time.time(),
        }
        self._enqueue(entry)
        return trajectory_id

    def log_tool_call(
        self,
        *,
        source_plane: str,
        session_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        latency_seconds: float,
        error: Optional[str] = None,
        environment_snapshot: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        safe_arguments = self._to_json_safe(arguments, limit=8000)
        safe_result = self._to_json_safe(result, limit=12000)
        tool_call_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"

        trajectory = [
            {
                "step": 0,
                "role": "assistant",
                "t_offset_ms": 0.0,
                "tool_calls": [{"id": tool_call_id, "name": tool_name, "arguments": safe_arguments}],
            },
            {
                "step": 1,
                "role": "tool",
                "tool_call_id": tool_call_id,
                "t_offset_ms": round(max(float(latency_seconds), 0.0) * 1000.0, 1),
                "latency_ms": round(max(float(latency_seconds), 0.0) * 1000.0, 2),
                "content": safe_result,
                "error": error,
            },
        ]
        telemetry = {
            "latency_seconds": round(max(float(latency_seconds), 0.0), 6),
            "is_stub": True,
            "tool_call_count": 1,
            "tool_error_count": 1 if error else 0,
        }
        return self.log_trajectory(
            source_plane=source_plane,
            session_id=session_id,
            trajectory=trajectory,
            telemetry=telemetry,
            environment_snapshot=environment_snapshot or {},
            context=context or {},
            capture_mode="rpc_stub",
        )

    def _enqueue(self, entry: Dict[str, Any]) -> None:
        depth = self._write_queue.qsize()
        if depth > 500:
            self.logger.warning("Distillation queue depth is high: %s", depth)
        self._write_queue.put(entry)

    def _writer_loop(self) -> None:
        while True:
            entry = self._write_queue.get()
            try:
                self._write_entry(entry)
            except Exception as exc:
                self.logger.error("CRITICAL distillation write failure: %s", exc)
            finally:
                self._write_queue.task_done()

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        write_started_at = float(entry.pop("_write_started_at", time.time()))
        entry.setdefault("distill_meta", {})
        entry["distill_meta"]["write_latency_ms"] = round(
            (time.time() - write_started_at) * 1000.0,
            3,
        )
        date_str = time.strftime("%Y-%m-%d")
        dataset_shard = self.dataset_dir / f"trajectories_{date_str}.jsonl"
        legacy_shard = self.legacy_dir / f"trajectories_{date_str}.jsonl"
        row = json.dumps(entry, ensure_ascii=False) + "\n"

        with self._lock:
            with open(dataset_shard, "a", encoding="utf-8") as handle:
                handle.write(row)
            with open(legacy_shard, "a", encoding="utf-8") as handle:
                handle.write(row)
            self._write_index(entry)
            self._bucket_entry(entry)

    def _write_index(self, entry: Dict[str, Any]) -> None:
        telemetry = entry.get("telemetry", {})
        quality = entry.get("quality_matrix", {})
        summary = {
            "trajectory_id": entry.get("trajectory_id"),
            "timestamp": entry.get("timestamp"),
            "session_id": entry.get("session_id"),
            "source_plane": entry.get("source_plane"),
            "heuristics": quality.get("heuristics", []),
            "auto_tags": quality.get("auto_tags", []),
            "tool_call_count": telemetry.get("tool_call_count", 0),
            "latency_seconds": telemetry.get("latency_seconds", 0),
            "memory_enriched": bool(
                (entry.get("memory_context_at_start") or {}).get("surfaces")
            ),
            "planner_mode": ((entry.get("intent_provenance") or {}).get("exo_route") or {}).get(
                "planner_used"
            ),
        }
        with open(self.index_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, ensure_ascii=False) + "\n")

    def _bucket_entry(self, entry: Dict[str, Any]) -> None:
        quality = entry.get("quality_matrix", {})
        auto_tags = set(quality.get("auto_tags", []) or [])
        heuristics = set(quality.get("heuristics", []) or [])
        row = json.dumps(entry, ensure_ascii=False) + "\n"
        date_str = time.strftime("%Y-%m-%d")

        is_high_value = (
            "deep_clean_chain" in auto_tags
            or ("memory_enriched" in auto_tags and "lisan_high_confidence" in auto_tags)
        )
        is_noisy_failure = "contains_tool_error" in heuristics and "deep_tool_chain" not in heuristics

        if is_high_value and not is_noisy_failure:
            with open(self.high_value_dir / f"high_value_{date_str}.jsonl", "a", encoding="utf-8") as handle:
                handle.write(row)

        if "contains_tool_error" in heuristics:
            with open(self.failure_dir / f"failures_{date_str}.jsonl", "a", encoding="utf-8") as handle:
                handle.write(row)

    def _evaluate_quality(
        self,
        trajectory: List[Dict[str, Any]],
        telemetry: Dict[str, Any],
        intent_provenance: Dict[str, Any],
        memory_context: Dict[str, Any],
    ) -> tuple[List[str], List[str]]:
        heuristics: List[str] = []
        auto_tags: List[str] = []

        tool_error_count = self._count_tool_errors(trajectory) + int(
            telemetry.get("tool_error_count", 0) or 0
        )
        tool_call_count = int(telemetry.get("tool_call_count", 0) or 0)
        if tool_call_count <= 0:
            tool_call_count = self._count_tool_calls(trajectory)

        if tool_error_count > 0:
            heuristics.append("contains_tool_error")
        if tool_call_count >= 3:
            heuristics.append("deep_tool_chain")
        if float(telemetry.get("latency_seconds", 0) or 0) > 30.0:
            heuristics.append("high_latency")
        if int(telemetry.get("iterations", 0) or 0) >= 5:
            heuristics.append("many_iterations")

        lisan_intent = intent_provenance.get("lisan_intent", {}) if isinstance(intent_provenance, dict) else {}
        if float(lisan_intent.get("confidence", 0) or 0) > 0.80:
            auto_tags.append("lisan_high_confidence")

        exo_route = intent_provenance.get("exo_route", {}) if isinstance(intent_provenance, dict) else {}
        planner_used = str(exo_route.get("planner_used", "") or "").lower()
        if planner_used == "mcts":
            auto_tags.append("mcts_planned")
        elif planner_used == "astar":
            auto_tags.append("astar_planned")
        elif planner_used:
            auto_tags.append(f"planner_{planner_used}")

        if (memory_context or {}).get("surfaces"):
            auto_tags.append("memory_enriched")
        if tool_call_count >= 5 and tool_error_count == 0:
            auto_tags.append("deep_clean_chain")
        if bool(exo_route.get("fallback_triggered", False)):
            auto_tags.append("planner_fallback")

        return heuristics, auto_tags

    def _count_tool_calls(self, trajectory: List[Dict[str, Any]]) -> int:
        count = 0
        for step in trajectory:
            tool_calls = step.get("tool_calls")
            if isinstance(tool_calls, list):
                count += len(tool_calls)
        return count

    def _count_tool_errors(self, trajectory: List[Dict[str, Any]]) -> int:
        count = 0
        for step in trajectory:
            if step.get("role") != "tool":
                continue
            if step.get("error"):
                count += 1
                continue
            text = str(step.get("content", "")).lower()
            if any(marker in text for marker in self.ERROR_MARKERS):
                count += 1
        return count

    def _sanitize_trajectory(self, trajectory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        safe: List[Dict[str, Any]] = []
        for idx, step in enumerate(trajectory):
            if not isinstance(step, dict):
                safe.append(
                    {
                        "step": idx,
                        "role": "unknown",
                        "content": self._truncate_text(str(step), 4000),
                        "t_offset_ms": None,
                    }
                )
                continue
            entry = dict(step)
            entry.setdefault("step", idx)
            if "content" in entry:
                entry["content"] = self._to_json_safe(entry["content"], limit=12000)
            if "reasoning" in entry:
                entry["reasoning"] = self._truncate_text(entry.get("reasoning", ""), 8000)
            if "tool_calls" in entry:
                entry["tool_calls"] = self._to_json_safe(entry["tool_calls"], limit=12000)
            safe.append(entry)
        return safe

    @staticmethod
    def _truncate_text(value: Any, limit: int) -> str:
        text = str(value or "")
        if len(text) <= limit:
            return text
        return text[:limit] + "... [truncated]"

    def _to_json_safe(self, value: Any, limit: int = 12000) -> Any:
        if value is None:
            return None
        try:
            json.dumps(value, ensure_ascii=False)
            if isinstance(value, str):
                return self._truncate_text(value, limit)
            return value
        except Exception:
            return self._truncate_text(value, limit)


_DISTILLATION_SINGLETONS: Dict[str, OpenRouterDistillationLogger] = {}
_DISTILLATION_SINGLETON_LOCK = threading.Lock()


def get_openrouter_distillation_logger(
    data_dir: Optional[Path] = None,
    logger_: Optional[logging.Logger] = None,
) -> OpenRouterDistillationLogger:
    resolved = Path(data_dir or _DEFAULT_CANON_DATA_DIR).expanduser().resolve()
    key = str(resolved)
    with _DISTILLATION_SINGLETON_LOCK:
        existing = _DISTILLATION_SINGLETONS.get(key)
        if existing is not None:
            return existing
        created = OpenRouterDistillationLogger(data_dir=resolved, logger_=logger_)
        _DISTILLATION_SINGLETONS[key] = created
        return created


class SovereignOpenRouterWrapper:
    """
    BB7-compatible wrapper for SovereignOpenRouterClient.

    Follows OPSEC wrapper pattern:
    - Imports production module (never modifies it)
    - Exposes capabilities via get_tools()
    - Thin adapters only — under 50 lines each
    - Output transformed to shell-friendly dicts
    """

    def __init__(self, yaml_path: str = "openrouter.yaml") -> None:
        self._yaml_path = Path(yaml_path)
        self._client: Optional[SovereignOpenRouterClient] = None
        self._distill = get_openrouter_distillation_logger(logger_=logger)

    async def initialize(self) -> None:
        """
        Async init — must be called before get_tools() is used.
        Separates construction from IO so wrapper is safe to instantiate sync.
        """
        if not _SOVEREIGN_OR_AVAILABLE or SovereignOpenRouterClient is None:
            raise RuntimeError(
                "SovereignOpenRouterClient unavailable. "
                f"Import error: {_SOVEREIGN_OR_IMPORT_ERROR}"
            )
        self._client = await SovereignOpenRouterClient.create(self._yaml_path)
        logger.info("[or_wrapper] Initialized against %s", self._yaml_path)

    async def shutdown(self) -> None:
        """Graceful shutdown. Call on exoskeleton teardown."""
        if self._client:
            await self._client.close()

    # ──────────────────────────────────────────
    # BB7 TOOL REGISTRY
    # ──────────────────────────────────────────

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return tool definitions for BB7 exoskeleton registration."""
        return {
            "or_complete": {
                "function": self._tool_complete,
                "description": (
                    "Single completion call via OpenRouter. "
                    "Supports model override, thinking mode, temperature, max_tokens. "
                    "Fallback chain engaged automatically on provider failure."
                ),
                "domain": "openrouter",
                "schema": {
                    "messages": "List[Dict] — OpenAI-format message list (required)",
                    "model": "str — OR model string, e.g. 'anthropic/claude-sonnet-4-5' (optional)",
                    "temperature": "float 0.0-2.0 (optional)",
                    "max_tokens": "int (optional)",
                    "thinking": "bool — enable extended thinking (optional)",
                    "system_prompt": "str — inline system prompt override (optional)",
                },
            },
            "or_stream": {
                "function": self._tool_stream,
                "description": (
                    "Streaming completion via OpenRouter. "
                    "Collects all chunks and returns joined string. "
                    "Use for long-form generation where latency-to-first-token matters."
                ),
                "domain": "openrouter",
                "schema": {
                    "messages": "List[Dict] — OpenAI-format message list (required)",
                    "model": "str (optional)",
                    "temperature": "float (optional)",
                    "max_tokens": "int (optional)",
                },
            },
            "or_batch": {
                "function": self._tool_batch,
                "description": (
                    "Fire identical prompt at multiple models in parallel. "
                    "Returns ranked results. Ideal for cross-model distillation, "
                    "RLHF data collection, and output diversity evaluation."
                ),
                "domain": "openrouter",
                "schema": {
                    "messages": "List[Dict] — OpenAI-format message list (required)",
                    "models": "List[str] — OR model strings (optional, defaults to fallback_chain)",
                    "rank_by": "str — 'quality' | 'latency' | 'cost' (optional, default: quality)",
                    "temperature": "float (optional)",
                    "max_tokens": "int (optional)",
                },
            },
            "or_model_list": {
                "function": self._tool_model_list,
                "description": (
                    "Fetch live model catalog from OpenRouter API. "
                    "Returns id, name, context_length, pricing per model."
                ),
                "domain": "openrouter",
                "schema": {
                    "filter_free": "bool — return only zero-cost models (optional, default: false)",
                },
            },
            "or_cost_report": {
                "function": self._tool_cost_report,
                "description": (
                    "Return accumulated token usage and cost for the current session. "
                    "Includes per-call breakdown and session totals."
                ),
                "domain": "openrouter",
                "schema": {},
            },
            "or_config_reload": {
                "function": self._tool_config_reload,
                "description": (
                    "Hot-reload openrouter.yaml without restarting the process. "
                    "Useful for swapping models, adjusting routing strategy, "
                    "or rotating API keys mid-session."
                ),
                "domain": "openrouter",
                "schema": {},
            },
        }

    # ──────────────────────────────────────────
    # THIN ADAPTERS
    # ──────────────────────────────────────────

    async def _tool_complete(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: Optional[bool] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._assert_ready()
        started_at = time.time()
        tool_args = {
            "messages_count": len(messages or []),
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking": thinking,
            "system_prompt": bool(system_prompt),
        }
        try:
            resp = await self._client.complete(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking=thinking,
                system_prompt_override=system_prompt,
            )
            payload = {
                "content": resp.content,
                "model": resp.model,
                "finish_reason": resp.finish_reason,
                "usage": resp.usage,
            }
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_complete",
                arguments=tool_args,
                result=payload,
                latency_seconds=time.time() - started_at,
                context={"yaml_path": str(self._yaml_path)},
            )
            return payload
        except Exception as exc:
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_complete",
                arguments=tool_args,
                result={"error": str(exc)},
                latency_seconds=time.time() - started_at,
                error=str(exc),
                context={"yaml_path": str(self._yaml_path)},
            )
            raise

    async def _tool_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._assert_ready()
        started_at = time.time()
        tool_args = {
            "messages_count": len(messages or []),
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            chunks = []
            async for chunk in self._client.stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                chunks.append(chunk)
            payload = {
                "content": "".join(chunks),
                "chunk_count": len(chunks),
            }
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_stream",
                arguments=tool_args,
                result=payload,
                latency_seconds=time.time() - started_at,
                context={"yaml_path": str(self._yaml_path)},
            )
            return payload
        except Exception as exc:
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_stream",
                arguments=tool_args,
                result={"error": str(exc)},
                latency_seconds=time.time() - started_at,
                error=str(exc),
                context={"yaml_path": str(self._yaml_path)},
            )
            raise

    async def _tool_batch(
        self,
        messages: List[Dict[str, Any]],
        models: Optional[List[str]] = None,
        rank_by: str = "quality",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._assert_ready()
        started_at = time.time()
        tool_args = {
            "messages_count": len(messages or []),
            "models": models,
            "rank_by": rank_by,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            rank_enum = BatchRankBy(rank_by) if rank_by in BatchRankBy._value2member_map_ else BatchRankBy.QUALITY
            results = await self._client.batch(
                messages=messages,
                models=models,
                rank_by=rank_enum,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            payload = {
                "results": [
                    {
                        "model": r.model,
                        "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                        "content_length": len(r.content),
                        "latency_ms": round(r.latency_ms, 1),
                        "usage": r.usage,
                        "error": r.error,
                    }
                    for r in results
                ],
                "model_count": len(results),
                "successful": sum(1 for r in results if r.error is None),
            }
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_batch",
                arguments=tool_args,
                result=payload,
                latency_seconds=time.time() - started_at,
                context={"yaml_path": str(self._yaml_path)},
            )
            return payload
        except Exception as exc:
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_batch",
                arguments=tool_args,
                result={"error": str(exc)},
                latency_seconds=time.time() - started_at,
                error=str(exc),
                context={"yaml_path": str(self._yaml_path)},
            )
            raise

    async def _tool_model_list(
        self,
        filter_free: bool = False,
    ) -> Dict[str, Any]:
        self._assert_ready()
        started_at = time.time()
        tool_args = {"filter_free": filter_free}
        try:
            models = await self._client.get_models(filter_free=filter_free)
            payload = {
                "models": [
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "context_length": m.get("context_length"),
                        "pricing": m.get("pricing"),
                    }
                    for m in models
                ],
                "count": len(models),
                "filter_free": filter_free,
            }
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_model_list",
                arguments=tool_args,
                result=payload,
                latency_seconds=time.time() - started_at,
                context={"yaml_path": str(self._yaml_path)},
            )
            return payload
        except Exception as exc:
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_model_list",
                arguments=tool_args,
                result={"error": str(exc)},
                latency_seconds=time.time() - started_at,
                error=str(exc),
                context={"yaml_path": str(self._yaml_path)},
            )
            raise

    async def _tool_cost_report(self) -> Dict[str, Any]:
        self._assert_ready()
        started_at = time.time()
        try:
            payload = self._client.cost_report()
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_cost_report",
                arguments={},
                result=payload,
                latency_seconds=time.time() - started_at,
                context={"yaml_path": str(self._yaml_path)},
            )
            return payload
        except Exception as exc:
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_cost_report",
                arguments={},
                result={"error": str(exc)},
                latency_seconds=time.time() - started_at,
                error=str(exc),
                context={"yaml_path": str(self._yaml_path)},
            )
            raise

    async def _tool_config_reload(self) -> Dict[str, Any]:
        self._assert_ready()
        started_at = time.time()
        try:
            await self._client.reload_config()
            cfg = self._client._config
            payload = {
                "status": "reloaded",
                "active_model": cfg.defaults.model,
                "routing_strategy": cfg.routing.strategy,
                "thinking_enabled": cfg.thinking.enabled,
            }
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_config_reload",
                arguments={},
                result=payload,
                latency_seconds=time.time() - started_at,
                context={"yaml_path": str(self._yaml_path)},
            )
            return payload
        except Exception as exc:
            self._distill.log_tool_call(
                source_plane="openrouter_wrapper",
                session_id="openrouter_wrapper",
                tool_name="or_config_reload",
                arguments={},
                result={"error": str(exc)},
                latency_seconds=time.time() - started_at,
                error=str(exc),
                context={"yaml_path": str(self._yaml_path)},
            )
            raise

    # ──────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────

    def _assert_ready(self) -> None:
        if self._client is None:
            raise RuntimeError(
                "SovereignOpenRouterWrapper not initialized. "
                "Call await wrapper.initialize() before using tools."
            )
