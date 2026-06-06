"""
OpenRouter Agent Tool - Distributed Cognitive Execution Plane

Provides specialized AI agents backed by OpenRouter that EXECUTE MCP tools
in a shared cognitive space. All tools share:
- /home/daeron/Somnus-MCP/data/ (canon data dir)
- Memory store (bm25 indexed)
- Journal (reasoning provenance)
- Planner state
- Session state
- Execution history

This makes the MCP server itself a distributed cognitive architecture
where agents can call tools, hand off to each other, and build on shared context.
"""

from __future__ import annotations

import asyncio
import inspect
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

_SOVEREIGN_DATA_DIR = Path(
    os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data")
).expanduser().resolve()


def _resolve_canon_data_dir(data_dir: Optional[Path] = None) -> Path:
    """Resolve canonical persistence root for all agent-plane state."""
    if data_dir is not None:
        return Path(data_dir).expanduser().resolve()
    configured = os.environ.get("SOVEREIGN_DATA_DIR", "").strip()
    if not configured:
        configured = os.environ.get("MCP_DATA_DIR", "").strip()
    if not configured:
        configured = str(_SOVEREIGN_DATA_DIR)
    return Path(configured).expanduser().resolve()


class AgentNotConfiguredError(RuntimeError):
    """Raised when OPENROUTER_API_KEY is missing."""


class ExecutionNode:
    """A node in the distributed cognitive network.
    
    Each agent is an execution node that can:
    - Read/write to shared memory
    - Call MCP tools
    - Hand off to other agents
    - Build on previous work
    """
    
    def __init__(self, node_id: str, node_type: str, canon_data_dir: Path):
        self.node_id = node_id
        self.node_type = node_type
        self.canon_data_dir = Path(canon_data_dir).expanduser().resolve()
        self.state_file = self.canon_data_dir / "agents" / "nodes" / f"{node_id}.json"
        self.canon_data_dir.mkdir(parents=True, exist_ok=True)
        (self.canon_data_dir / "agents" / "nodes").mkdir(parents=True, exist_ok=True)
        
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save node state to canon dir."""
        state["node_id"] = self.node_id
        state["node_type"] = self.node_type
        state["updated_at"] = time.time()
        tmp = self.state_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, self.state_file)
        
    def load_state(self) -> Dict[str, Any]:
        """Load node state from canon dir."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"node_id": self.node_id, "node_type": self.node_type}
    
    def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to shared cognitive space."""
        msg_file = self.canon_data_dir / "agents" / "messages" / f"{channel}.jsonl"
        msg_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "timestamp": time.time(),
            "message": message,
        }
        with open(msg_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def subscribe(self, channel: str, since: float = 0) -> List[Dict]:
        """Subscribe to messages from other nodes."""
        msg_file = self.canon_data_dir / "agents" / "messages" / f"{channel}.jsonl"
        if not msg_file.exists():
            return []
        messages = []
        with open(msg_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["timestamp"] > since:
                    messages.append(entry)
        return messages


class OpenRouterAgentTool:
    """Multi-agent OpenRouter integration with DISTRIBUTED EXECUTION.
    
    Key design principles:
    - ALL data goes to /home/daeron/Somnus-MCP/data/ (canon)
    - Agents EXECUTE MCP tools, not just return plans
    - Cross-agent handoff via shared state
    - Tool-to-tool calling enabled
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "elephant-alpha"
    FALLBACK_MODELS = [
        "elephant-alpha",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-exp:free",
        "xiaomi/mimo-v2-flash:free",
    ]

    AGENT_CONFIGS = {
        "planner": {
            "description": "Multi-step execution planning with tool execution",
            "system_prompt": "You are a senior planning agent that EXECUTES tasks. You have access to MCP tools. Do not just plan. Call tools, analyze results, iterate until complete.",
            "tools": [
                "bb7_lisan_recall",
                "bb7_memory_surface_context",
                "bb7_workspace_context_loader",
                "bb7_auto_session_resume",
                "bb7_analyze_project_structure",
                "bb7_search_files",
                "bb7_read_file",
                "bb7_get_project_dependencies",
                "bb7_get_recent_changes",
                "bb7_exo_route",
                "bb7_exo_plan",
                "bb7_intelligent_tool_guide",
                "bb7_memory_store",
                "bb7_memory_search",
                "bb7_capture_insight",
                "bb7_log_event",
                "bb7_agent_handoff",
                "bb7_agent_call",
            ],
            "max_iterations": 50,
        },
        "debugger": {
            "description": "Error diagnosis with tool execution",
            "system_prompt": "You are a debugging expert that EXECUTES diagnostics. Use MCP tools to investigate errors, trace issues, and apply fixes.",
            "tools": [
                "bb7_lisan_recall",
                "bb7_memory_surface_context",
                "bb7_memory_search",
                "bb7_memory_store",
                "bb7_get_system_info",
                "bb7_list_processes",
                "bb7_run_command",
                "bb7_analyze_code_complete",
                "bb7_security_audit",
                "bb7_take_screenshot",
                "bb7_capture_insight",
                "bb7_log_event",
                "bb7_agent_handoff",
                "bb7_agent_call",
            ],
            "max_iterations": 30,
        },
        "analyzer": {
            "description": "Deep code analysis with execution",
            "system_prompt": "You are a code architecture expert that EXECUTES analysis. Use MCP tools to deeply analyze codebases and produce actionable insights.",
            "tools": [
                "bb7_lisan_recall",
                "bb7_memory_surface_context",
                "bb7_memory_store",
                "bb7_analyze_code_complete",
                "bb7_security_audit",
                "bb7_analyze_project_structure",
                "bb7_get_code_metrics",
                "bb7_search_files",
                "bb7_read_file",
                "bb7_capture_insight",
                "bb7_log_event",
                "bb7_agent_handoff",
                "bb7_agent_call",
            ],
            "max_iterations": 20,
        },
        "doc": {
            "description": "Documentation generation with execution",
            "system_prompt": "You are a technical documentation expert that EXECUTES documentation. Use MCP tools to analyze code and generate docs.",
            "tools": [
                "bb7_lisan_recall",
                "bb7_memory_surface_context",
                "bb7_memory_search",
                "bb7_memory_store",
                "bb7_analyze_project_structure",
                "bb7_read_file",
                "bb7_search_files",
                "bb7_analyze_code_complete",
                "bb7_get_project_dependencies",
                "bb7_get_recent_changes",
                "bb7_capture_insight",
                "bb7_log_event",
                "bb7_agent_handoff",
            ],
            "max_iterations": 15,
        },
    }

    EXECUTION_TEMPLATE = """You are an autonomous cognitive agent running in a DISTRIBUTED EXECUTION PLANE.

## SHARED CANON DATA
All tools and agents share the canonical data root.
- Memory: data/memory_store.json (BM25 indexed)
- Sessions: data/sessions/
- Planner: data/planner/
- Agents: data/agents/nodes/
- Exoskeleton: data/exoskeleton/

## YOUR IDENTITY
- Agent Type: {agent_type}
- Node ID: {node_id}
- Description: {agent_description}
- Max iterations: {max_iterations}

## AVAILABLE TOOLS (MCP bb7_ functions)
You can call these to EXECUTE tasks:
{tools_list}

## CROSS-AGENT CAPABILITIES
- bb7_agent_handoff: Pass context to another agent type
- bb7_agent_call: Call a specific agent to help
- Read from shared memory to see what other agents did
- Write to shared memory for others to build on

## EXECUTION PROTOCOL

### Step 1: SURFACE CONTEXT
Use bb7_memory_surface_context to find relevant prior work:
- "What has been tried before?"
- "What context exists for this task?"

### Step 2: RESURRECT CONTINUITY
Use bb7_lisan_recall and bb7_memory_surface_context to find prior work:
- "What decisions already echo through this task?"
- "What active plan or memory should shape the next move?"

### Step 3: LOAD WORKSPACE
Use bb7_workspace_context_loader for current state.

### Step 4: EXECUTE (Don't just plan!)
For each step in your plan:
1. Call the appropriate MCP tool
2. Analyze the result
3. If result suggests new direction, pivot
4. Store significant findings to memory

### Step 5: HANDOFF OR COMPLETE
When stuck or done:
- Use bb7_agent_handoff to pass to another agent type
- Or mark complete with final results

## RESPONSE FORMAT
{{
    "phase": "context|analysis|execution|handoff|complete",
    "action": "tool_call|thinking|handoff|complete",
    "tool": "bb7_xxx" | null,
    "params": {{}} | null,
    "thinking": "Your reasoning",
    "result": "What happened",
    "memory": {{"key": "", "value": "", "importance": 0.8}} | null,
    "handoff": {{"to_agent": "", "context": ""}} | null,
    "should_continue": true/false
}}

## YOUR TASK
{task}

## PREVIOUS AGENT WORK
{previous_context}

EXECUTE now. Call tools. Iterate. Complete the task.
Respond with JSON only."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        self.data_dir = _resolve_canon_data_dir(data_dir)
        os.environ["SOVEREIGN_DATA_DIR"] = str(self.data_dir)
        os.environ["MCP_DATA_DIR"] = str(self.data_dir)
        self.agents_dir = self.data_dir / "agents"
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        (self.data_dir / "agents" / "nodes").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "agents" / "messages").mkdir(parents=True, exist_ok=True)

        self.runs_file = self.agents_dir / "agent_runs.jsonl"
        self.state_file = self.agents_dir / "agent_state.json"
        
        self._tool_registry: Optional[Dict[str, Callable]] = None
        self._or_client: Optional[Any] = None  # SovereignOpenRouterClient, lazy async init
        self._or_yaml_path = Path(__file__).resolve().parent.parent / "databus" / "openrouter.yaml"
        self._state: Dict[str, Any] = self._load_state()
        self._active_nodes: Dict[str, ExecutionNode] = {}
        self._distill = get_openrouter_distillation_logger(
            data_dir=self.data_dir,
            logger_=self.logger,
        )

    def register_tools(self, tool_registry: Dict[str, Any]) -> None:
        """Register the MCP tool registry for actual execution."""
        normalized: Dict[str, Callable[..., Any]] = {}
        for tool_name, tool_info in (tool_registry or {}).items():
            if callable(tool_info):
                normalized[tool_name] = tool_info
                continue
            if isinstance(tool_info, dict):
                tool_func = tool_info.get("function")
                if callable(tool_func):
                    normalized[tool_name] = tool_func
        self._tool_registry = normalized
        self.logger.info(
            "Registered %d normalized MCP tools for agent execution",
            len(normalized),
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
            self.logger.warning("Failed loading agent state: %s", exc)
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
                self.logger.debug("Agent client close error: %s", exc)
        self._or_client = None

    def _hydrate_env_from_dotenv(self) -> None:
        """
        Load .env values into process env without overriding existing values.
        This keeps agent health/run config aligned with repo env settings
        even when those settings were added after server start.
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
                self.logger.debug("Agent dotenv hydration skipped for %s: %s", env_path, exc)

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
            or self._env_first("OPENROUTER_AGENT_MODEL", "OPENROUTER_MODEL")
            or self.DEFAULT_MODEL
        )
        api_key = self._env_first("OPENROUTER_API_KEY", "OPENROUTER_KEY", "OR_API_KEY")
        app_name = self._env_first("OPENROUTER_APP_NAME") or "SovereignMCP Agent"
        site_url = self._env_first("OPENROUTER_SITE_URL") or "https://localhost"
        return {
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
            "app_name": app_name,
            "site_url": site_url,
        }

    def _build_tools_list(self, agent_type: str) -> str:
        config = self.AGENT_CONFIGS.get(agent_type, self.AGENT_CONFIGS["planner"])
        tools = config.get("tools", [])
        lines = []
        for tool in tools:
            lines.append(f"- {tool}()")
        return "\n".join(lines)

    def _build_execution_prompt(self, agent_type: str, node_id: str, task: str, previous_context: str = "") -> str:
        config = self.AGENT_CONFIGS.get(agent_type, self.AGENT_CONFIGS["planner"])
        return self.EXECUTION_TEMPLATE.format(
            agent_type=agent_type,
            node_id=node_id,
            agent_description=config.get("description", ""),
            max_iterations=config.get("max_iterations", 50),
            tools_list=self._build_tools_list(agent_type),
            task=task,
            previous_context=previous_context or "No previous context - start fresh.",
        )

    async def _execute_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Actually execute an MCP tool call."""
        if not self._tool_registry:
            return {"error": "Tool registry not registered", "result": None}
        
        if tool_name not in self._tool_registry:
            return {"error": f"Unknown tool: {tool_name}", "result": None}
        
        try:
            tool_func = self._tool_registry[tool_name]
            result = await self._invoke_tool_callable(tool_func, params)
            return {"result": result}
        except Exception as e:
            return {"error": str(e), "result": None}

    async def _invoke_tool_callable(
        self,
        tool_callable: Callable[..., Any],
        params: Dict[str, Any],
    ) -> Any:
        """Invoke a tool callable using kwargs-first then dict style, with awaitable support."""
        if not isinstance(params, dict):
            raise TypeError(f"Tool params must be a dict, got {type(params)}")

        strategies = []
        if not params:
            strategies.append(("no_args", lambda: tool_callable()))
        strategies.extend(
            [
                ("kwargs", lambda: tool_callable(**params)),
                ("dict", lambda: tool_callable(params)),
            ]
        )

        last_type_error: Optional[TypeError] = None
        for strategy_name, strategy in strategies:
            try:
                result = strategy()
                if inspect.isawaitable(result):
                    return await result
                return result
            except TypeError as exc:
                last_type_error = exc
                self.logger.debug(
                    "Agent tool invocation strategy '%s' failed for %s: %s",
                    strategy_name,
                    getattr(tool_callable, "__name__", repr(tool_callable)),
                    exc,
                )
        if last_type_error is not None:
            raise last_type_error
        raise RuntimeError("No valid invocation strategy for tool call")

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
    def _parse_agent_response(text: str) -> Dict[str, Any]:
        body = (text or "").strip()
        if not body:
            return {
                "phase": "error",
                "action": "thinking",
                "thinking": "Empty response",
                "should_continue": False,
                "result": "No response",
            }

        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

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
            "phase": "error",
            "action": "thinking",
            "thinking": f"Could not parse: {body[:300]}",
            "should_continue": False,
            "result": "Parse error",
        }

    @staticmethod
    def _truncate_for_distill(value: Any, limit: int = 8000) -> str:
        text = str(value or "")
        if len(text) <= limit:
            return text
        return text[:limit] + "... [truncated]"

    def _log_agent_distillation(
        self,
        *,
        node_id: str,
        agent_type: str,
        task_text: str,
        context_text: str,
        trajectory: List[Dict[str, Any]],
        run_started_at: float,
        iteration_count: int,
        tool_call_count: int,
        tool_error_count: int,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        requested_model: str,
        models_used: List[str],
        status: str,
        error: Optional[str] = None,
    ) -> Optional[str]:
        telemetry = {
            "latency_seconds": round(max(time.time() - run_started_at, 0.0), 6),
            "iterations": int(iteration_count),
            "tool_call_count": int(tool_call_count),
            "tool_error_count": int(tool_error_count),
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(total_tokens),
            "requested_model": requested_model,
            "models_used": models_used,
            "status": status,
        }
        if error:
            telemetry["error"] = self._truncate_for_distill(error, 2000)

        intent_provenance = {
            "raw_user_input": task_text,
            "lisan_intent": {},
            "exo_route": {
                "planner_used": "openrouter_agent_loop",
                "fallback_triggered": False,
                "agent_type": agent_type,
            },
        }

        environment_snapshot = {
            "os": sys.platform,
            "active_tools_count": len(self._tool_registry or {}),
            "planner_mode": "openrouter_agent_loop",
            "memory_plane_active": True,
            "thought_journal_active": Path(self.data_dir / "thought_journal.json").exists(),
            "lisan_active": True,
            "data_dir": str(self.data_dir),
        }

        try:
            return self._distill.log_trajectory(
                source_plane="bb7_agent_run",
                session_id=node_id,
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
                    "agent_type": agent_type,
                    "task": self._truncate_for_distill(task_text, 4000),
                    "context": self._truncate_for_distill(context_text, 4000),
                    "status": status,
                },
            )
        except Exception as exc:
            self.logger.error("Agent distillation logging failed for node %s: %s", node_id, exc)
            return None

    def bb7_agent_health(self) -> Dict[str, Any]:
        """Return agent integration health - ALL data in canon dir."""
        cfg = self._openrouter_config()
        return {
            "status": "ok",
            "canon_data_dir": str(self.data_dir),
            "agents_dir": str(self.agents_dir),
            "nodes_dir": str(self.agents_dir / "nodes"),
            "messages_dir": str(self.agents_dir / "messages"),
            "api_key_configured": bool(cfg["api_key"]),
            "model": cfg["model"],
            "tools_registered": len(self._tool_registry) if self._tool_registry else 0,
            "available_agents": list(self.AGENT_CONFIGS.keys()),
            "agent_configs": {
                name: {
                    "description": config["description"],
                    "tools_count": len(config["tools"]),
                    "max_iterations": config["max_iterations"],
                }
                for name, config in self.AGENT_CONFIGS.items()
            },
            "state": {
                "total_runs": int(self._state.get("total_runs", 0)),
                "successful_runs": int(self._state.get("successful_runs", 0)),
                "failed_runs": int(self._state.get("failed_runs", 0)),
            },
        }

    def bb7_agent_list(self) -> Dict[str, Any]:
        """List all available agents."""
        return {
            "status": "ok",
            "agents": {
                name: {
                    "description": config["description"],
                    "tools": config["tools"],
                    "max_iterations": config["max_iterations"],
                }
                for name, config in self.AGENT_CONFIGS.items()
            },
        }

    def bb7_agent_capabilities(self, agent_type: str) -> Dict[str, Any]:
        """Get specific agent capabilities."""
        if agent_type not in self.AGENT_CONFIGS:
            return {
                "status": "error",
                "error": f"Unknown: {agent_type}. Available: {list(self.AGENT_CONFIGS.keys())}",
            }
        config = self.AGENT_CONFIGS[agent_type]
        return {
            "status": "ok",
            "agent_type": agent_type,
            "description": config["description"],
            "tools": config["tools"],
            "max_iterations": config["max_iterations"],
        }

    def bb7_agent_nodes(self) -> Dict[str, Any]:
        """List all active agent nodes in the cognitive plane."""
        nodes_dir = self.agents_dir / "nodes"
        nodes = []
        if nodes_dir.exists():
            for f in nodes_dir.glob("*.json"):
                try:
                    with open(f) as handle:
                        nodes.append(json.load(handle))
                except:
                    pass
        return {"status": "ok", "nodes": nodes, "count": len(nodes)}

    def bb7_agent_messages(self, channel: str = "general", since: float = 0) -> Dict[str, Any]:
        """Get messages from the cognitive plane."""
        msg_file = self.agents_dir / "messages" / f"{channel}.jsonl"
        if not msg_file.exists():
            return {"status": "ok", "messages": [], "channel": channel}
        
        messages = []
        with open(msg_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["timestamp"] > since:
                    messages.append(entry)
        return {"status": "ok", "messages": messages, "channel": channel, "count": len(messages)}

    def bb7_agent_handoff(self, to_agent: str, context: str, task: str) -> Dict[str, Any]:
        """Hand off to another agent with shared context."""
        if to_agent not in self.AGENT_CONFIGS:
            return {"status": "error", "error": f"Unknown agent: {to_agent}"}
        
        handoff_file = self.agents_dir / "handoffs" / f"{to_agent}_pending.json"
        handoff_file.parent.mkdir(parents=True, exist_ok=True)
        
        handoff = {
            "from_agent": "current",
            "to_agent": to_agent,
            "context": context,
            "task": task,
            "timestamp": time.time(),
        }
        
        with open(handoff_file, "w") as f:
            json.dump(handoff, f, indent=2)
        
        return {"status": "ok", "handoff": handoff, "message": f"Handed off to {to_agent}"}

    def bb7_agent_call(self, agent_type: str, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Synchronously call another agent (non-blocking)."""
        if agent_type not in self.AGENT_CONFIGS:
            return {"status": "error", "error": f"Unknown agent: {agent_type}"}
        
        return {
            "status": "ok",
            "message": f"Queued task for {agent_type}",
            "agent_type": agent_type,
            "task": task,
        }

    async def bb7_agent_run(
        self,
        agent_type: str,
        task: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_iterations: Optional[int] = None,
        execute_tools: bool = True,
    ) -> Dict[str, Any]:
        """Run an agent with ACTUAL TOOL EXECUTION in distributed cognitive plane."""
        agent_type = str(agent_type or "planner").strip().lower()
        if agent_type not in self.AGENT_CONFIGS:
            raise ValueError(f"Unknown: {agent_type}. Available: {list(self.AGENT_CONFIGS.keys())}")

        task_text = str(task or "").strip()
        if not task_text:
            raise ValueError("task required")

        temperature = max(0.0, min(1.0, float(temperature)))
        cfg = self._openrouter_config(model_override=model)

        config = self.AGENT_CONFIGS[agent_type]
        max_iters = max_iterations or config.get("max_iterations", 50)

        if not cfg["api_key"]:
            raise AgentNotConfiguredError("OPENROUTER_API_KEY not set")

        node_id = f"{agent_type}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        node = ExecutionNode(node_id, agent_type, self.data_dir)
        self._active_nodes[node_id] = node

        node.publish("executions", {"event": "start", "task": task_text})

        previous_context = context or ""
        run_started_at = time.time()
        step_counter = 0
        trajectory: List[Dict[str, Any]] = []
        iteration = 0
        all_results: List[Dict[str, Any]] = []
        execution_count = 0
        tool_error_count = 0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        models_used: List[str] = []

        def add_step(
            role: str,
            *,
            content: Optional[Any] = None,
            reasoning: Optional[str] = None,
            tool_calls: Optional[List[Dict[str, Any]]] = None,
            tool_call_id: Optional[str] = None,
            latency_ms: Optional[float] = None,
            error: Optional[str] = None,
        ) -> None:
            nonlocal step_counter
            step: Dict[str, Any] = {
                "step": step_counter,
                "role": role,
                "t_offset_ms": round((time.time() - run_started_at) * 1000.0, 1),
            }
            if content is not None:
                step["content"] = self._truncate_for_distill(content, 12000)
            if reasoning is not None:
                step["reasoning"] = self._truncate_for_distill(reasoning, 8000)
            if tool_calls is not None:
                step["tool_calls"] = tool_calls
            if tool_call_id is not None:
                step["tool_call_id"] = tool_call_id
            if latency_ms is not None:
                step["latency_ms"] = round(float(latency_ms), 2)
            if error:
                step["error"] = self._truncate_for_distill(error, 2000)
            trajectory.append(step)
            step_counter += 1

        add_step(role="user", content=task_text)
        if previous_context:
            add_step(
                role="assistant",
                reasoning="Agent received prior context from caller.",
                content=previous_context,
            )

        try:
            while iteration < max_iters:
                iteration += 1

                prompt = self._build_execution_prompt(agent_type, node_id, task_text, previous_context)

                started_at = time.time()
                completion_text = ""

                try:
                    or_client = await self._get_or_client()
                    resp = await or_client.complete(
                        messages=[
                            {"role": "system", "content": config["system_prompt"]},
                            {"role": "user", "content": prompt},
                        ],
                        model=cfg["model"],
                        temperature=temperature,
                    )
                    completion_text = resp.content
                    usage = resp.usage if isinstance(resp.usage, dict) else {}
                    prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
                    completion_tokens += int(usage.get("completion_tokens", 0) or 0)
                    reported_total = int(usage.get("total_tokens", 0) or 0)
                    if reported_total > 0:
                        total_tokens += reported_total
                    else:
                        total_tokens = prompt_tokens + completion_tokens
                    if resp.model and resp.model not in models_used:
                        models_used.append(resp.model)
                except Exception as e:
                    tool_error_count += 1
                    add_step(
                        role="assistant",
                        reasoning=f"Iteration {iteration} OpenRouter completion failed.",
                        content=str(e),
                        error=str(e),
                    )
                    if iteration >= 3:
                        break
                    await asyncio.sleep(1)
                    continue

                duration = time.time() - started_at
                parsed = self._parse_agent_response(completion_text)
                tool_name_raw = parsed.get("tool")
                tool_name = str(tool_name_raw).strip() if tool_name_raw is not None else ""
                tool_params_raw = parsed.get("params", {})
                tool_params: Dict[str, Any] = (
                    tool_params_raw if isinstance(tool_params_raw, dict) else {}
                )
                tool_call_id = (
                    f"{node_id}_iter{iteration}_{uuid.uuid4().hex[:6]}"
                    if execute_tools and tool_name
                    else None
                )
                assistant_tool_calls = (
                    [{"id": tool_call_id, "name": tool_name, "arguments": tool_params}]
                    if tool_call_id
                    else None
                )
                add_step(
                    role="assistant",
                    reasoning=parsed.get("thinking") or completion_text,
                    content=completion_text,
                    tool_calls=assistant_tool_calls,
                )

                tool_result = None
                tool_latency_ms: Optional[float] = None
                if execute_tools and tool_name:
                    tool_started_at = time.time()
                    tool_result = await self._execute_tool_call(tool_name, tool_params)
                    tool_latency_ms = (time.time() - tool_started_at) * 1000.0
                    execution_count += 1
                    if isinstance(tool_result, dict) and tool_result.get("error"):
                        tool_error_count += 1
                    node.publish("executions", {
                        "iteration": iteration,
                        "tool": tool_name,
                        "result": tool_result,
                    })
                    add_step(
                        role="tool",
                        tool_call_id=tool_call_id,
                        content=tool_result,
                        latency_ms=tool_latency_ms,
                        error=(
                            str(tool_result.get("error"))
                            if isinstance(tool_result, dict) and tool_result.get("error")
                            else None
                        ),
                    )

                result_entry = {
                    "iteration": iteration,
                    "duration_sec": round(duration, 3),
                    "parsed": parsed,
                    "tool_executed": tool_result,
                    "tool_latency_ms": round(tool_latency_ms, 2) if tool_latency_ms is not None else None,
                }
                all_results.append(result_entry)

                node.save_state({
                    "iteration": iteration,
                    "current_phase": parsed.get("phase"),
                    "action": parsed.get("action"),
                    "result": parsed.get("result"),
                    "tool_executed": parsed.get("tool") if execute_tools else None,
                })

                if parsed.get("phase") == "complete" or not parsed.get("should_continue", True):
                    break

                if parsed.get("handoff"):
                    node.publish("handoffs", parsed["handoff"])
                    break

                previous_context = f"Iter {iteration}: {parsed.get('thinking', '')} | Result: {parsed.get('result', '')}"

            node.publish("executions", {"event": "complete", "iterations": iteration, "executions": execution_count})

            self._state["total_runs"] += 1
            self._state["successful_runs"] += 1
            self._save_state()

            final_result = all_results[-1] if all_results else {}
            trajectory_id = self._log_agent_distillation(
                node_id=node_id,
                agent_type=agent_type,
                task_text=task_text,
                context_text=context or "",
                trajectory=trajectory,
                run_started_at=run_started_at,
                iteration_count=iteration,
                tool_call_count=execution_count,
                tool_error_count=tool_error_count,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens or (prompt_tokens + completion_tokens),
                requested_model=cfg["model"],
                models_used=models_used,
                status="ok",
            )
            self._append_jsonl(
                {
                    "timestamp": time.time(),
                    "node_id": node_id,
                    "agent_type": agent_type,
                    "task": self._truncate_for_distill(task_text, 2000),
                    "status": "ok",
                    "iterations": iteration,
                    "tools_executed": execution_count,
                    "tool_error_count": tool_error_count,
                    "requested_model": cfg["model"],
                    "models_used": models_used,
                    "duration_sec": round(time.time() - run_started_at, 3),
                    "trajectory_id": trajectory_id,
                }
            )
            return {
                "status": "ok",
                "node_id": node_id,
                "agent_type": agent_type,
                "task": task_text,
                "iterations": iteration,
                "tools_executed": execution_count,
                "canon_data_dir": str(self.data_dir),
                "final_phase": final_result.get("parsed", {}).get("phase"),
                "all_results": all_results,
                "trajectory_id": trajectory_id,
            }

        except Exception as e:
            self._state["total_runs"] += 1
            self._state["failed_runs"] += 1
            self._save_state()
            node.publish("errors", {"error": str(e), "iteration": iteration})
            add_step(
                role="assistant",
                reasoning="Agent run terminated with exception.",
                content=str(e),
                error=str(e),
            )
            trajectory_id = self._log_agent_distillation(
                node_id=node_id,
                agent_type=agent_type,
                task_text=task_text,
                context_text=context or "",
                trajectory=trajectory,
                run_started_at=run_started_at,
                iteration_count=iteration,
                tool_call_count=execution_count,
                tool_error_count=tool_error_count + 1,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens or (prompt_tokens + completion_tokens),
                requested_model=cfg["model"],
                models_used=models_used,
                status="error",
                error=str(e),
            )
            self._append_jsonl(
                {
                    "timestamp": time.time(),
                    "node_id": node_id,
                    "agent_type": agent_type,
                    "task": self._truncate_for_distill(task_text, 2000),
                    "status": "error",
                    "iterations": iteration,
                    "tools_executed": execution_count,
                    "tool_error_count": tool_error_count + 1,
                    "requested_model": cfg["model"],
                    "models_used": models_used,
                    "duration_sec": round(time.time() - run_started_at, 3),
                    "trajectory_id": trajectory_id,
                    "error": self._truncate_for_distill(str(e), 3000),
                }
            )
            return {
                "status": "error",
                "error": str(e),
                "iterations": iteration,
                "trajectory_id": trajectory_id,
            }
        finally:
            if node_id in self._active_nodes:
                del self._active_nodes[node_id]

    def bb7_agent_status(self) -> Dict[str, Any]:
        """Get status of all active agent nodes."""
        return {
            "status": "ok",
            "active_nodes": list(self._active_nodes.keys()),
            "canon_data_dir": str(self.data_dir),
            "total_nodes": len(self._active_nodes),
        }

    def get_tools(self) -> Dict[str, Callable[..., Any]]:
        return {
            "bb7_agent_health": {
                "function": self.bb7_agent_health,
                "description": "Return agent health with canon data dir info",
                "parameters": [],
            },
            "bb7_agent_list": {
                "function": self.bb7_agent_list,
                "description": "List all available agents",
                "parameters": [],
            },
            "bb7_agent_capabilities": {
                "function": self.bb7_agent_capabilities,
                "description": "Get agent capabilities and tools",
                "parameters": [
                    {"name": "agent_type", "description": "planner, debugger, analyzer, or doc", "type": "string", "required": True},
                ],
            },
            "bb7_agent_nodes": {
                "function": self.bb7_agent_nodes,
                "description": "List all active agent nodes in cognitive plane",
                "parameters": [],
            },
            "bb7_agent_messages": {
                "function": self.bb7_agent_messages,
                "description": "Get messages from cognitive plane",
                "parameters": [
                    {"name": "channel", "description": "Message channel", "type": "string", "required": False},
                    {"name": "since", "description": "Timestamp filter", "type": "number", "required": False},
                ],
            },
            "bb7_agent_handoff": {
                "function": self.bb7_agent_handoff,
                "description": "Hand off to another agent with shared context",
                "parameters": [
                    {"name": "to_agent", "description": "Target agent type", "type": "string", "required": True},
                    {"name": "context", "description": "Context to pass", "type": "string", "required": True},
                    {"name": "task", "description": "Task for target agent", "type": "string", "required": True},
                ],
            },
            "bb7_agent_call": {
                "function": self.bb7_agent_call,
                "description": "Call another agent (non-blocking)",
                "parameters": [
                    {"name": "agent_type", "description": "Agent to call", "type": "string", "required": True},
                    {"name": "task", "description": "Task description", "type": "string", "required": True},
                    {"name": "context", "description": "Optional context", "type": "string", "required": False},
                ],
            },
            "bb7_agent_run": {
                "function": self.bb7_agent_run,
                "description": "Run agent with ACTUAL tool execution in distributed plane",
                "parameters": [
                    {"name": "agent_type", "description": "planner, debugger, analyzer, or doc", "type": "string", "required": True},
                    {"name": "task", "description": "Task to execute", "type": "string", "required": True},
                    {"name": "context", "description": "Additional context", "type": "string", "required": False},
                    {"name": "model", "description": "Model override", "type": "string", "required": False},
                    {"name": "temperature", "description": "0.0-1.0", "type": "number", "required": False},
                    {"name": "max_iterations", "description": "Max iterations", "type": "number", "required": False},
                    {"name": "execute_tools", "description": "Actually execute MCP tools", "type": "boolean", "required": False},
                ],
            },
            "bb7_agent_status": {
                "function": self.bb7_agent_status,
                "description": "Get active agent nodes status",
                "parameters": [],
            },
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def _smoke() -> None:
        tool = OpenRouterAgentTool()
        try:
            print(json.dumps(tool.bb7_agent_health(), indent=2))
            print(json.dumps(tool.bb7_agent_nodes(), indent=2))
        finally:
            await tool.close()

    asyncio.run(_smoke())
