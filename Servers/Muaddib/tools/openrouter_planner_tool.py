"""
OpenRouter Planner Tool

Provides planner-oriented BB7 tools backed by OpenRouter chat completions.
Designed for global persistence under the canonical MCP data root.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from databus.sovereign_openrouter import SovereignOpenRouterClient
    _SOVEREIGN_OR_AVAILABLE = True
except ImportError:
    _SOVEREIGN_OR_AVAILABLE = False
    SovereignOpenRouterClient = None  # type: ignore[assignment,misc]

from databus.openrouter_wrapper import get_openrouter_distillation_logger


class PlannerNotConfiguredError(RuntimeError):
    """Raised when OPENROUTER_API_KEY is missing or malformed.

    This is a hard gate — no mock plans will be generated.
    Set the key via: $env:OPENROUTER_API_KEY='sk-or-v1-...'
    """


class PlannerModelExhaustedError(RuntimeError):
    """Raised when all models in the fallback chain have failed."""


class OpenRouterPlannerTool:
    """Planner-focused OpenRouter integration with persistent run telemetry."""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "elephant-alpha"
    FALLBACK_MODELS = [
        "elephant-alpha",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-exp:free",
        "xiaomi/mimo-v2-flash:free",
    ]

    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        configured_data_dir = os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data").strip()
        if not configured_data_dir:
            configured_data_dir = "/home/daeron/Somnus-MCP/data"

        self.data_dir = Path(data_dir or configured_data_dir).expanduser().resolve()
        os.environ["SOVEREIGN_DATA_DIR"] = str(self.data_dir)
        os.environ["MCP_DATA_DIR"] = str(self.data_dir)
        self.planner_dir = self.data_dir / "planner"
        self.planner_dir.mkdir(parents=True, exist_ok=True)

        self.runs_file = self.planner_dir / "planner_runs.jsonl"
        self.state_file = self.planner_dir / "planner_state.json"

        self._or_client: Optional[Any] = None  # SovereignOpenRouterClient, lazy async init
        self._or_yaml_path = Path(__file__).resolve().parent.parent / "databus" / "openrouter.yaml"
        self._state: Dict[str, Any] = self._load_state()
        self._distill = get_openrouter_distillation_logger(
            data_dir=self.data_dir,
            logger_=self.logger,
        )

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {
                "version": 1,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_updated": time.time(),
            }
        try:
            with open(self.state_file, "r", encoding="utf-8") as handle:
                state = json.load(handle)
            if isinstance(state, dict):
                return state
        except Exception as exc:
            self.logger.warning("Failed loading planner state: %s", exc)
        return {
            "version": 1,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_updated": time.time(),
        }

    def _save_state(self) -> None:
        self._state["last_updated"] = time.time()
        payload = json.dumps(self._state, indent=2, ensure_ascii=False)
        tmp_path = self.state_file.with_suffix(".json.tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, self.state_file)
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass

    def _append_jsonl(self, payload: Dict[str, Any]) -> None:
        row = json.dumps(payload, ensure_ascii=False) + "\n"
        self.runs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.runs_file, "a", encoding="utf-8") as handle:
            handle.write(row)

    async def _get_or_client(self):
        """Lazy-initialize SovereignOpenRouterClient from databus/openrouter.yaml."""
        if not _SOVEREIGN_OR_AVAILABLE:
            raise RuntimeError(
                "SovereignOpenRouterClient unavailable — ensure databus/sovereign_openrouter.py is importable."
            )
        if self._or_client is None:
            self._or_client = await SovereignOpenRouterClient.create(self._or_yaml_path)
        return self._or_client

    async def close(self) -> None:
        if self._or_client is not None:
            try:
                await self._or_client.close()
            except Exception as exc:
                self.logger.debug("Planner client close error: %s", exc)
        self._or_client = None

    def _hydrate_env_from_dotenv(self) -> None:
        """
        Load .env values into process env without overriding existing values.
        This allows planner health/config calls to see newly-added env vars
        even if the server process was started before .env was updated.
        """
        candidates = [
            Path.cwd() / ".env",
            Path(__file__).resolve().parent.parent / ".env",
        ]
        for env_path in candidates:
            if not env_path.exists() or not env_path.is_file():
                continue
            try:
                with open(env_path, "r", encoding="utf-8") as handle:
                    for raw_line in handle:
                        line = raw_line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = value
            except Exception as exc:
                self.logger.debug("Planner dotenv hydration skipped for %s: %s", env_path, exc)

    def _env_first(self, *names: str) -> str:
        for name in names:
            value = os.environ.get(name, "").strip()
            if value:
                return value
        return ""

    def _openrouter_config(self, model_override: Optional[str] = None) -> Dict[str, str]:
        self._hydrate_env_from_dotenv()
        base_url = self._env_first("OPENROUTER_BASE_URL") or self.DEFAULT_BASE_URL
        model = (
            (model_override or "").strip()
            or self._env_first("OPENROUTER_PLANNER_MODEL", "OPENROUTER_MODEL")
            or self.DEFAULT_MODEL
        )
        api_key = self._env_first("OPENROUTER_API_KEY", "OPENROUTER_KEY", "OR_API_KEY")
        app_name = self._env_first("OPENROUTER_APP_NAME") or "SovereignMCP Planner"
        site_url = self._env_first("OPENROUTER_SITE_URL") or "https://localhost"
        return {
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
            "app_name": app_name,
            "site_url": site_url,
        }

    def _default_plan_template(self, intent: str, context: str, max_steps: int) -> str:
        return (
            "Return a concise execution plan in JSON with this exact shape:\n"
            "{\n"
            "  \"summary\": \"string\",\n"
            "  \"steps\": [\n"
            "    {\"id\": 1, \"title\": \"string\", \"why\": \"string\", \"actions\": [\"string\"], \"acceptance\": \"string\", \"risk\": \"string\"}\n"
            "  ],\n"
            "  \"handoff_template\": \"string\"\n"
            "}\n"
            f"Constraints: maximum {max_steps} steps; prioritize safe, reversible actions; include concrete verification criteria.\n"
            f"Intent: {intent}\n"
            f"Context: {context or 'N/A'}"
        )

    @staticmethod
    def _extract_text_from_response(payload: Dict[str, Any]) -> str:
        try:
            choices = payload.get("choices", [])
            if not choices:
                return ""
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                chunks: List[str] = []
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        chunks.append(item["text"])
                return "\n".join(chunks)
        except Exception:
            return ""
        return ""

    @staticmethod
    def _parse_json_or_fallback(text: str) -> Dict[str, Any]:
        body = (text or "").strip()
        if not body:
            return {
                "summary": "Planner response was empty.",
                "steps": [],
                "handoff_template": "Please provide more context and retry.",
            }

        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        fenced = body
        if "```" in body:
            parts = body.split("```")
            for part in parts:
                snippet = part.strip()
                if snippet.startswith("json"):
                    snippet = snippet[4:].strip()
                try:
                    parsed = json.loads(snippet)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue

        return {
            "summary": "Planner returned non-JSON output; preserved as text.",
            "steps": [],
            "handoff_template": body[:2000],
        }

    @staticmethod
    def _truncate_for_distill(value: Any, limit: int = 8000) -> str:
        text = str(value or "")
        if len(text) <= limit:
            return text
        return text[:limit] + "... [truncated]"

    def _log_planner_distillation(
        self,
        *,
        request_id: str,
        intent: str,
        context: str,
        constraints: str,
        trajectory: List[Dict[str, Any]],
        run_started_at: float,
        success: bool,
        model: str,
        retries: int,
        usage: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        safe_usage = usage if isinstance(usage, dict) else {}
        prompt_tokens = int(safe_usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(safe_usage.get("completion_tokens", 0) or 0)
        total_tokens = int(safe_usage.get("total_tokens", 0) or 0)
        if total_tokens <= 0:
            total_tokens = prompt_tokens + completion_tokens

        telemetry = {
            "latency_seconds": round(max(time.time() - run_started_at, 0.0), 6),
            "tool_call_count": 1,
            "tool_error_count": 0 if success else 1,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "retries": retries,
            "status": "dry_run" if dry_run else ("ok" if success else "error"),
            "request_id": request_id,
            "model": model,
        }
        if error:
            telemetry["error"] = self._truncate_for_distill(error, 2000)

        intent_provenance = {
            "raw_user_input": intent,
            "lisan_intent": {},
            "exo_route": {
                "planner_used": "openrouter_planner",
                "fallback_triggered": retries > 0,
            },
        }
        environment_snapshot = {
            "os": sys.platform,
            "planner_mode": "openrouter",
            "memory_plane_active": True,
            "thought_journal_active": Path(self.data_dir / "thought_journal.json").exists(),
            "lisan_active": True,
            "data_dir": str(self.data_dir),
        }

        try:
            return self._distill.log_trajectory(
                source_plane="bb7_planner_plan",
                session_id=request_id,
                trajectory=trajectory,
                telemetry=telemetry,
                intent_provenance=intent_provenance,
                memory_context_at_start={
                    "surfaces": [],
                    "signals_active": [],
                    "injection_boost": 0,
                },
                thought_journal_entries=[],
                environment_snapshot=environment_snapshot,
                capture_mode="lossless_harness",
                context={
                    "intent": self._truncate_for_distill(intent, 3000),
                    "context": self._truncate_for_distill(context, 3000),
                    "constraints": self._truncate_for_distill(constraints, 3000),
                    "dry_run": bool(dry_run),
                },
            )
        except Exception as exc:
            self.logger.error("Planner distillation logging failed for %s: %s", request_id, exc)
            return None

    def bb7_planner_health(self) -> Dict[str, Any]:
        """Return planner integration and persistence health details."""
        cfg = self._openrouter_config()
        return {
            "status": "ok",
            "planner_dir": str(self.planner_dir),
            "runs_file": str(self.runs_file),
            "state_file": str(self.state_file),
            "api_key_configured": bool(cfg["api_key"]),
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "state": {
                "total_runs": int(self._state.get("total_runs", 0)),
                "successful_runs": int(self._state.get("successful_runs", 0)),
                "failed_runs": int(self._state.get("failed_runs", 0)),
                "last_updated": float(self._state.get("last_updated", time.time())),
            },
        }

    def bb7_planner_template(
        self,
        intent: str,
        context: Optional[str] = None,
        max_steps: int = 8,
    ) -> Dict[str, Any]:
        """Generate a reusable planner prompt template for a given intent."""
        intent = str(intent or "").strip()
        if not intent:
            raise ValueError("intent parameter is required")

        max_steps = max(1, min(20, int(max_steps)))
        template = self._default_plan_template(intent=intent, context=str(context or ""), max_steps=max_steps)
        return {
            "status": "ok",
            "intent": intent,
            "max_steps": max_steps,
            "template": template,
        }

    async def bb7_planner_plan(
        self,
        intent: str,
        context: Optional[str] = None,
        constraints: Optional[str] = None,
        max_steps: int = 8,
        model: Optional[str] = None,
        temperature: float = 0.2,
        retries: int = 2,
        timeout: int = 45,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Generate a structured execution plan using OpenRouter."""
        intent = str(intent or "").strip()
        if not intent:
            raise ValueError("intent parameter is required")

        max_steps = max(1, min(20, int(max_steps)))
        temperature = max(0.0, min(1.0, float(temperature)))
        retries = max(0, min(5, int(retries)))
        timeout = max(5, min(180, int(timeout)))

        cfg = self._openrouter_config(model_override=model)
        request_id = f"planner_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        planner_prompt = self._default_plan_template(intent, str(context or ""), max_steps)
        if constraints:
            planner_prompt += f"\nAdditional constraints: {constraints.strip()}"

        request_payload = {
            "model": cfg["model"],
            "temperature": temperature,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a senior planning model. Return valid JSON only, no markdown wrapper, "
                        "with practical, verifiable execution steps."
                    ),
                },
                {
                    "role": "user",
                    "content": planner_prompt,
                },
            ],
        }

        run_started_at = time.time()
        step_counter = 0
        context_text = str(context or "")
        constraints_text = str(constraints or "")
        tool_call_id = f"{request_id}_openrouter_complete"
        trajectory: List[Dict[str, Any]] = []

        def add_step(
            role: str,
            *,
            content: Optional[Any] = None,
            reasoning: Optional[str] = None,
            tool_calls: Optional[List[Dict[str, Any]]] = None,
            tool_call_id_ref: Optional[str] = None,
            latency_ms: Optional[float] = None,
            error: Optional[str] = None,
        ) -> None:
            nonlocal step_counter
            entry: Dict[str, Any] = {
                "step": step_counter,
                "role": role,
                "t_offset_ms": round((time.time() - run_started_at) * 1000.0, 1),
            }
            if content is not None:
                entry["content"] = self._truncate_for_distill(content, 12000)
            if reasoning is not None:
                entry["reasoning"] = self._truncate_for_distill(reasoning, 8000)
            if tool_calls is not None:
                entry["tool_calls"] = tool_calls
            if tool_call_id_ref is not None:
                entry["tool_call_id"] = tool_call_id_ref
            if latency_ms is not None:
                entry["latency_ms"] = round(float(latency_ms), 2)
            if error:
                entry["error"] = self._truncate_for_distill(error, 2000)
            trajectory.append(entry)
            step_counter += 1

        add_step(
            role="user",
            content={
                "intent": intent,
                "context": context_text,
                "constraints": constraints_text,
                "max_steps": max_steps,
            },
        )
        add_step(
            role="assistant",
            reasoning="Generating a structured JSON plan with OpenRouter.",
            content=planner_prompt,
            tool_calls=[
                {
                    "id": tool_call_id,
                    "name": "openrouter.complete",
                    "arguments": {
                        "model": cfg["model"],
                        "temperature": temperature,
                        "max_tokens": 4096,
                        "retries": retries,
                    },
                }
            ],
        )

        if dry_run:
            add_step(
                role="tool",
                tool_call_id_ref=tool_call_id,
                content=request_payload,
                latency_ms=0.0,
            )
            trajectory_id = self._log_planner_distillation(
                request_id=request_id,
                intent=intent,
                context=context_text,
                constraints=constraints_text,
                trajectory=trajectory,
                run_started_at=run_started_at,
                success=True,
                model=cfg["model"],
                retries=0,
                usage={},
                error=None,
                dry_run=True,
            )
            self._append_jsonl(
                {
                    "timestamp": time.time(),
                    "request_id": request_id,
                    "intent": intent,
                    "model": cfg["model"],
                    "success": True,
                    "dry_run": True,
                    "duration_sec": round(time.time() - run_started_at, 3),
                    "error": "",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "trajectory_id": trajectory_id,
                }
            )
            return {
                "status": "dry_run",
                "request_id": request_id,
                "model": cfg["model"],
                "base_url": cfg["base_url"],
                "payload_preview": request_payload,
                "trajectory_id": trajectory_id,
            }

        if not cfg["api_key"]:
            error_text = (
                "OPENROUTER_API_KEY is not set or empty. "
                "Set it via: $env:OPENROUTER_API_KEY='sk-or-v1-...' "
                "or export OPENROUTER_API_KEY='sk-or-v1-...'. "
                "No mock plans will be generated — this is a hard gate."
            )
            add_step(
                role="tool",
                tool_call_id_ref=tool_call_id,
                content=error_text,
                error=error_text,
            )
            self._log_planner_distillation(
                request_id=request_id,
                intent=intent,
                context=context_text,
                constraints=constraints_text,
                trajectory=trajectory,
                run_started_at=run_started_at,
                success=False,
                model=cfg["model"],
                retries=0,
                usage={},
                error=error_text,
                dry_run=False,
            )
            raise PlannerNotConfiguredError(error_text)

        started_at = time.time()
        last_error = ""
        response_payload: Dict[str, Any] = {}
        active_model = cfg["model"]
        attempts_made = 0

        # SovereignOpenRouterClient handles fallback chain internally via openrouter.yaml routing config.
        for attempt in range(retries + 1):
            attempts_made = attempt + 1
            try:
                or_client = await self._get_or_client()
                resp = await or_client.complete(
                    messages=request_payload["messages"],
                    model=cfg["model"],
                    temperature=temperature,
                    max_tokens=4096,
                )
                active_model = resp.model
                usage = resp.usage or {}
                response_payload = {
                    "choices": [{"message": {"content": resp.content}}],
                    "usage": usage,
                }
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt >= retries:
                    break
                await asyncio.sleep(0.75 * (attempt + 1))

        duration = time.time() - started_at
        success = bool(response_payload)

        usage = response_payload.get("usage", {}) if isinstance(response_payload, dict) else {}
        completion_text = self._extract_text_from_response(response_payload) if success else ""
        parsed_plan = self._parse_json_or_fallback(completion_text) if success else {}
        retries_used = max(0, attempts_made - 1)

        add_step(
            role="tool",
            tool_call_id_ref=tool_call_id,
            content=completion_text if success else (last_error or "OpenRouter request failed"),
            latency_ms=duration * 1000.0,
            error=None if success else (last_error or "OpenRouter request failed"),
        )
        if success:
            add_step(
                role="assistant",
                reasoning="Parsed planner JSON response.",
                content=parsed_plan,
            )

        self._state["total_runs"] = int(self._state.get("total_runs", 0)) + 1
        if success:
            self._state["successful_runs"] = int(self._state.get("successful_runs", 0)) + 1
        else:
            self._state["failed_runs"] = int(self._state.get("failed_runs", 0)) + 1
        self._save_state()

        trajectory_id = self._log_planner_distillation(
            request_id=request_id,
            intent=intent,
            context=context_text,
            constraints=constraints_text,
            trajectory=trajectory,
            run_started_at=run_started_at,
            success=success,
            model=cfg["model"],
            retries=retries_used,
            usage=usage if isinstance(usage, dict) else {},
            error=last_error if not success else None,
            dry_run=False,
        )

        self._append_jsonl(
            {
                "timestamp": time.time(),
                "request_id": request_id,
                "intent": intent,
                "model": cfg["model"],
                "active_model": active_model,
                "success": success,
                "dry_run": False,
                "duration_sec": round(duration, 3),
                "error": last_error,
                "retries_used": retries_used,
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "trajectory_id": trajectory_id,
            }
        )

        if not success:
            return {
                "status": "error",
                "request_id": request_id,
                "error": last_error or "OpenRouter request failed",
                "model": cfg["model"],
                "duration_sec": round(duration, 3),
                "trajectory_id": trajectory_id,
            }

        return {
            "status": "ok",
            "request_id": request_id,
            "model": cfg["model"],
            "active_model": active_model,
            "duration_sec": round(duration, 3),
            "usage": usage,
            "plan": parsed_plan,
            "raw_text": completion_text,
            "trajectory_id": trajectory_id,
        }

    def get_tools(self) -> Dict[str, Callable[..., Any]]:
        return {
            "bb7_planner_health": {
                "function": self.bb7_planner_health,
                "description": "Return OpenRouter planner configuration and persistence health.",
                "parameters": [],
            },
            "bb7_planner_template": {
                "function": self.bb7_planner_template,
                "description": "Generate a planner prompt template for a target intent.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "Target intent to plan for.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "context",
                        "description": "Optional context to include in the template.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "max_steps",
                        "description": "Maximum number of plan steps.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_planner_plan": {
                "function": self.bb7_planner_plan,
                "description": "Generate a structured execution plan using OpenRouter.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "What should be planned.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "context",
                        "description": "Additional planning context.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "constraints",
                        "description": "Optional constraints for the plan.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "max_steps",
                        "description": "Maximum steps allowed in returned plan.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "model",
                        "description": "Optional OpenRouter model override.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "temperature",
                        "description": "Model temperature between 0 and 1.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "retries",
                        "description": "Retry count for transient request failures.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "timeout",
                        "description": "Request timeout in seconds.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "dry_run",
                        "description": "If true, do not call API and return payload preview only.",
                        "type": "boolean",
                        "required": False,
                    },
                ],
            },
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def _smoke() -> None:
        tool = OpenRouterPlannerTool()
        try:
            print(json.dumps(tool.bb7_planner_health(), indent=2))
            print(json.dumps(tool.bb7_planner_template("Design rollout plan"), indent=2))
            print(
                json.dumps(
                    await tool.bb7_planner_plan(
                        intent="Design rollout plan",
                        context="First pass check",
                        dry_run=True,
                    ),
                    indent=2,
                )
            )
        finally:
            await tool.close()

    asyncio.run(_smoke())
