#!/usr/bin/env python3
"""
MCP Server - Model Context Protocol Server Implementation
Complete implementation with 55+ tools for advanced AI-human collaboration

Features:
- Persistent memory across sessions
- File operations with comprehensive support
- Shell & system tools with secure execution
- Web tools for content fetching and search
- Session management with cognitive tracking
- Visual automation and screen interaction
- Enhanced code analysis with CFA, DFA, type inference
- Secure Python execution with sandboxing
- Real-time tool registration and management

Architecture:
- Modular tool system with dynamic loading
- Cross-platform compatibility (Windows, Linux, macOS)
- Resource monitoring and security controls
- Comprehensive audit logging
- MCP standard compliance
"""

import argparse
import asyncio
import hashlib
import inspect
import json
import logging
import os
import queue
import re
import shutil
import sqlite3
import sys
import time
import traceback
import threading
import importlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Tuple


class MCPServer:
    """Model Context Protocol Server with comprehensive tool ecosystem"""

    DEFAULT_SOVEREIGN_DATA_DIR = str(
        (Path(__file__).resolve().parent / "data").resolve()
    )
    LEGACY_WINDOWS_DATA_DIR = "C:/Users/treyr/mcp/data"

    def __init__(self, debug: bool = False, transport: str = "stdio"):
        self.debug = debug
        self._transport = transport
        self._load_env_file()
        self.workspace_root = Path(__file__).resolve().parent
        self.data_dir = self._resolve_data_dir()
        self._enforce_canonical_data_env()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.session_id = f"ses_{uuid.uuid4().hex[:12]}"
        self._turn_counter = 0
        self._telemetry_lock = threading.Lock()
        self._internal_failure_lock = threading.Lock()
        self._codex_ingest_lock = threading.Lock()
        self.events_file = self.data_dir / "events.jsonl"
        self.internal_failures_file = self.data_dir / "internal_failures.jsonl"
        self._instance_lock_path = self.data_dir / "mcp_server.lock"
        self.codex_ingest_state_file = self.data_dir / "codex_ingest_state.json"
        self._codex_state_db_path = Path.home() / ".codex" / "state_5.sqlite"
        self._codex_history_path = Path.home() / ".codex" / "history.jsonl"
        self._latest_codex_thread_id: Optional[str] = None
        self.logger.info("MCP data directory: %s", self.data_dir)
        self._acquire_singleton_lock()
        self._migrate_legacy_data_dir_if_needed()
        self._cleanup_stray_temp_files()

        # Shared async execution loop for coroutine-based tools.
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_loop_thread: Optional[threading.Thread] = None
        self._async_loop_ready = threading.Event()
        self._async_loop_lock = threading.Lock()
        self._exo_sync_lock = threading.Lock()
        self._last_exo_sync_time = 0.0
        self._last_exo_sync_tool_count = -1

        # Server state
        self.tools = {}
        self.tool_modules = {}
        self.tool_origins: Dict[str, str] = {}
        self._tool_registry_lock = threading.RLock()
        self._proactive_memory_injected = False
        self._ambient_memory_exchange_enabled = (
            str(os.environ.get("SOVEREIGN_AMBIENT_MEMORY_EXCHANGE", "1")).strip().lower()
            not in {"0", "false", "no"}
        )

        # Tool health monitoring - track silent failures and health issues
        self.tool_health = {
            "failed_tools": {},  # tool_name -> {"count": int, "last_error": str, "last_failure": float}
            "slow_tools": {},  # tool_name -> {"count": int, "avg_time": float}
            "loaded_tools": set(),  # Track which tools loaded successfully
            "failed_loads": {},  # module_name -> {"error": str, "timestamp": float}
            "unused_tools": {},  # tools loaded but never called in session
            "internal_failures": [],  # explicit internal control-plane failures
        }

        # Distillation engine — initialized late after register_tools() via _late_init_distillation().
        # Set SOVEREIGN_DISTILLATION_ENABLED=1 to activate trajectory capture.
        self._distillation_engine = None

        self.server_info = {
            "name": "Advanced MCP Server",
            "version": "2.1.0",
            "description": "Comprehensive AI-Human Collaboration Platform",
            "capabilities": [
                "memory",
                "files",
                "shell",
                "web",
                "sessions",
                "visual",
                "terminal",
                "auto",
                "code_analysis",
                "exoskeleton",
            ],
            "total_tools": 0,
            "startup_time": time.time(),
        }

        # Performance monitoring
        self.performance_metrics = {
            "tool_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_response_time": 0,
            "last_activity": time.time(),
        }

        # Session conversation history for RLHF distillation
        self.conversation_history: List[Dict[str, Any]] = []

        # ReAct Trajectory Buffer (Distillation Phase 3)
        self._trajectory_buffer: List[Dict[str, Any]] = []
        self._trajectory_buffer_lock = threading.Lock()
        self._trajectory_session_start = time.time()

        # SQLite3 distillation database for persistent logging
        self._init_distillation_db()

        # Comprehensive Tool Registry for AI Guidance
        self.tool_registry = {
            "auto_activation": [
                {
                    "name": "bb7_workspace_context_loader",
                    "description": " ALWAYS RUN FIRST: Automatically loads relevant project context, active sessions, recent memories, and current workspace state. Essential for understanding where we left off and maintaining seamless continuity across coding sessions.",
                    "category": "auto_activation",
                    "priority": "critical",
                    "when_to_use": [
                        "session_start",
                        "context_needed",
                        "resuming_work",
                        "conversation_start",
                    ],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "include_recent_memories": {
                                "type": "boolean",
                                "default": True,
                                "description": "Load recent memory entries related to current workspace",
                            },
                            "include_active_sessions": {
                                "type": "boolean",
                                "default": True,
                                "description": "Check for and resume active development sessions",
                            },
                        },
                        "required": [],
                    },
                }
            ]
        }

        # Add built-in ping tool for health checks
        self.tools["ping_server"] = {
            "description": "Checks if the Sovereign MCP server is alive and reachable",
            "parameters": [],
            "function": self._ping_server_impl,
        }
        self.logger.info("Added built-in ping_server tool")

        # Add tool health reporting tool
        self.tools["bb7_tool_health_report"] = {
            "description": "Reports on tool health including failed loads, failed tool calls, and slow tools",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "include_failed_loads": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include modules that failed to load",
                    },
                    "include_failed_calls": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include tools that have failed during execution",
                    },
                    "include_slow_tools": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include tools with slow execution times",
                    },
                },
            },
            "function": self._tool_health_report_impl,
        }
        self.logger.info("Added bb7_tool_health_report tool")

        # Add guarded registry-bound facade refresh tool. This is intentionally
        # narrow: it hot-refreshes safe facade modules in the existing process
        # without rerunning register_tools() boot side effects or touching the
        # JSON-RPC/display output adapter.
        self.tools["bb7_tool_refresh_module"] = {
            "description": (
                "Refresh an allowlisted registry-bound tool module in-place. "
                "Currently intended for meta_intelligence_engine parity after source edits; "
                "does not start a second server or rerun boot lifecycle loops."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "default": "meta_intelligence_engine",
                        "description": "Allowlisted module to refresh.",
                    },
                    "force_reload": {
                        "type": "boolean",
                        "default": True,
                        "description": "Reload the Python module before rebuilding the facade instance.",
                    },
                },
                "required": [],
            },
            "function": self._tool_refresh_module_impl,
        }
        self.tool_origins["bb7_tool_refresh_module"] = "mcp_server_builtin"
        self.logger.info("Added bb7_tool_refresh_module tool")

        # Register all tools from modules
        self.register_tools()
        self._init_dispatcher()
        self._append_event(
            event_type="session_start",
            source="mcp_server",
            payload={
                "pid": os.getpid(),
                "tool_count": len(self.tools),
                "data_dir": str(self.data_dir),
            },
            importance_hint=0.8,
        )

        self.logger.info(f"MCP Server initialized with {len(self.tools)} tools")

    def _ping_server_impl(self, **params) -> Dict[str, Any]:
        """Implementation for ping_server tool - looks up tool count at call time."""
        return {
            "status": "alive",
            "server": "SovereignMCP",
            "tool_count": len(self.tools),
            "runtime_identity": self._runtime_identity(),
            "timestamp": time.time(),
        }

    def _runtime_identity(self) -> Dict[str, Any]:
        """
        Return process/source identity for source-live parity audits.

        This is intentionally observational. It does not reload modules, start
        transports, or mutate the output adapter; it only describes the current
        in-process server that is answering this tool call.
        """
        source_path = Path(__file__).resolve()
        manifest_path = self.workspace_root / "tool_manifest.json"
        identity: Dict[str, Any] = {
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "session_id": self.session_id,
            "transport": getattr(self, "_transport", "unknown"),
            "data_dir": str(self.data_dir),
            "workspace_root": str(self.workspace_root),
            "python_executable": sys.executable,
            "source_file": str(source_path),
            "source_mtime": source_path.stat().st_mtime if source_path.exists() else None,
            "source_sha256_16": self._short_file_sha256(source_path),
            "tool_manifest_mtime": (
                manifest_path.stat().st_mtime if manifest_path.exists() else None
            ),
            "tool_manifest_sha256_16": self._short_file_sha256(manifest_path),
            "startup_time": self.server_info.get("startup_time"),
        }
        return identity

    @staticmethod
    def _short_file_sha256(path: Path) -> Optional[str]:
        """Return a short sha256 digest for a local source/control file."""
        try:
            if not path.exists() or not path.is_file():
                return None
            digest = hashlib.sha256()
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()[:16]
        except Exception as exc:
            return f"error:{type(exc).__name__}"

    def _tool_health_report_impl(self, **params) -> Dict[str, Any]:
        """Implementation for bb7_tool_health_report - reports on tool health."""
        include_failed_loads = params.get("include_failed_loads", True)
        include_failed_calls = params.get("include_failed_calls", True)
        include_slow_tools = params.get("include_slow_tools", True)

        report = {
            "status": "healthy",
            "total_tools": len(self.tools),
            "registered_tools": sorted(self.tools.keys()),
            "loaded_modules": list(self.tool_health["loaded_tools"]),
            "runtime_identity": self._runtime_identity(),
            "timestamp": time.time(),
        }

        # Failed module loads
        if include_failed_loads and self.tool_health["failed_loads"]:
            report["failed_module_loads"] = {
                module: {"error": data["error"], "timestamp": data["timestamp"]}
                for module, data in self.tool_health["failed_loads"].items()
            }
            report["status"] = "degraded"

        # Failed tool calls
        if include_failed_calls and self.tool_health["failed_tools"]:
            report["failed_tool_calls"] = {
                tool: {
                    "count": data["count"],
                    "last_error": data["last_error"],
                    "last_failure": data["last_failure"],
                }
                for tool, data in self.tool_health["failed_tools"].items()
            }
            report["status"] = "degraded"

        if self.tool_health.get("internal_failures"):
            report["internal_failures"] = self.tool_health["internal_failures"][-25:]
            report["status"] = "degraded"

        # Slow tools
        if include_slow_tools and self.tool_health["slow_tools"]:
            report["slow_tools"] = {
                tool: {
                    "count": data["count"],
                    "avg_time_seconds": round(data["avg_time"], 2),
                }
                for tool, data in self.tool_health["slow_tools"].items()
            }

        # Unused tools (loaded but never called)
        if self.tool_health.get("unused_tools"):
            report["unused_tools"] = list(self.tool_health["unused_tools"].keys())

        # Proactive memory context injection status
        if (
            hasattr(self, "_proactive_memory_injected")
            and self._proactive_memory_injected
        ):
            report["proactive_memory_injected"] = True

        return report

    REGISTRY_BOUND_REFRESH_ALLOWLIST = {"meta_intelligence_engine"}

    def _attach_registry_bound_facades(self) -> Dict[str, Any]:
        """
        Attach facade modules to the existing live registry.

        This is the one-plane binding hook for modules such as
        meta_intelligence_engine.py. It passes references to the current
        in-process registry and module map; it does not instantiate sibling
        tools or fork persistence.
        """
        attached: Dict[str, Any] = {}
        for module_name, tool_instance in list(self.tool_modules.items()):
            attach = getattr(tool_instance, "attach_tool_plane", None)
            if not callable(attach):
                continue
            try:
                attached[module_name] = attach(self.tools, self.tool_modules)
            except Exception as exc:
                attached[module_name] = {
                    "success": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
                self._record_internal_failure(
                    component="mcp_server",
                    operation="attach_registry_bound_facade",
                    error=exc,
                    context={"module_name": module_name},
                    severity="error",
                )
        return attached

    def _reattach_registry_dependents(self) -> Dict[str, Any]:
        """Reattach registry consumers after an in-place module refresh."""
        status: Dict[str, Any] = {
            "registry_bound_facades": self._attach_registry_bound_facades()
        }

        exo = self.tool_modules.get("exoskeleton_tool")
        if exo and hasattr(exo, "attach_live_tools_provider"):
            try:
                exo.attach_live_tools_provider(lambda: self.tools)
                status["exoskeleton_live_provider"] = True
            except Exception as exc:
                status["exoskeleton_live_provider"] = {
                    "success": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
                self._record_internal_failure(
                    component="mcp_server",
                    operation="reattach_exoskeleton_live_provider",
                    error=exc,
                    context={},
                    severity="error",
                )

        agent_tool = self.tool_modules.get("openrouter_agent_tool")
        if agent_tool and hasattr(agent_tool, "register_tools"):
            try:
                agent_tool.register_tools(self.tools)
                status["agent_tool_registry"] = True
            except Exception as exc:
                status["agent_tool_registry"] = {
                    "success": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
                self._record_internal_failure(
                    component="mcp_server",
                    operation="reattach_agent_tool_registry",
                    error=exc,
                    context={},
                    severity="error",
                )

        try:
            self._sync_exoskeleton_catalog(force=True)
            status["exoskeleton_catalog_synced"] = True
        except Exception as exc:
            status["exoskeleton_catalog_synced"] = {
                "success": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
            self._record_internal_failure(
                component="mcp_server",
                operation="refresh_module_sync_exoskeleton_catalog",
                error=exc,
                context={},
                severity="error",
            )

        return status

    def _tool_refresh_module_impl(self, **params) -> Dict[str, Any]:
        """
        Guarded in-place refresh for registry-bound facade modules.

        This is not a server restart and not a full register_tools() rerun. It
        avoids boot side effects such as starting another autonomous cycle.
        """
        module_name = str(params.get("module_name") or "meta_intelligence_engine").strip()
        force_reload = bool(params.get("force_reload", True))
        if module_name not in self.REGISTRY_BOUND_REFRESH_ALLOWLIST:
            return {
                "ok": False,
                "reason": "module_not_allowlisted_for_hot_refresh",
                "module_name": module_name,
                "allowlist": sorted(self.REGISTRY_BOUND_REFRESH_ALLOWLIST),
            }

        discovered = dict(self._discover_tool_module_specs())
        if module_name not in discovered:
            return {
                "ok": False,
                "reason": "module_not_discovered",
                "module_name": module_name,
                "discovered_count": len(discovered),
            }

        _source_dir, import_prefix = self._resolve_tools_import_surface()
        import_name = f"{import_prefix}.{module_name}" if import_prefix else module_name

        with self._tool_registry_lock:
            before_tools = set(self.tools.keys())
            previous_tools = {
                tool_name: tool_def
                for tool_name, tool_def in self.tools.items()
                if self.tool_origins.get(tool_name) == module_name
            }
            previous_instance = self.tool_modules.get(module_name)
            try:
                module = importlib.import_module(import_name)
                if force_reload:
                    module = importlib.reload(module)
                tool_class = self._discover_tool_class(module_name, module)
                if tool_class is None:
                    raise RuntimeError(
                        f"{module_name}: no get_tools-bearing class discovered"
                    )
                tool_instance = self._build_tool_instance(module_name, tool_class)
                module_tools = tool_instance.get_tools()
                if not isinstance(module_tools, dict):
                    raise RuntimeError(
                        f"{module_name}.get_tools() returned "
                        f"{type(module_tools).__name__}, expected dict"
                    )

                for tool_name in list(previous_tools.keys()):
                    self.tools.pop(tool_name, None)
                    self.tool_origins.pop(tool_name, None)
                    self.tool_health.get("unused_tools", {}).pop(tool_name, None)

                for tool_name, tool_definition in module_tools.items():
                    self.tools[tool_name] = tool_definition
                    self.tool_origins[tool_name] = module_name
                    self.tool_health["unused_tools"][tool_name] = True

                self.tool_modules[module_name] = tool_instance
                self.tool_health["loaded_tools"].add(module_name)
                self.tool_health["failed_loads"].pop(module_name, None)
                self.server_info["total_tools"] = len(self.tools)
                reattach_status = self._reattach_registry_dependents()

                after_tools = set(self.tools.keys())
                result = {
                    "ok": True,
                    "surface": "bb7_tool_refresh_module",
                    "module_name": module_name,
                    "import_name": import_name,
                    "force_reload": force_reload,
                    "tool_count_before": len(before_tools),
                    "tool_count_after": len(after_tools),
                    "removed_tools": sorted(before_tools - after_tools),
                    "added_tools": sorted(after_tools - before_tools),
                    "module_tools": sorted(module_tools.keys()),
                    "reattach_status": reattach_status,
                    "one_plane": True,
                    "started_server": False,
                    "reran_register_tools": False,
                    "output_adapter_touched": False,
                }
                self._append_event(
                    event_type="tool_module_refresh",
                    source="mcp_server",
                    payload=result,
                    importance_hint=0.7,
                )
                return result
            except Exception as exc:
                if previous_instance is not None:
                    self.tool_modules[module_name] = previous_instance
                for tool_name in list(self.tools.keys()):
                    if self.tool_origins.get(tool_name) == module_name:
                        self.tools.pop(tool_name, None)
                        self.tool_origins.pop(tool_name, None)
                for tool_name, tool_definition in previous_tools.items():
                    self.tools[tool_name] = tool_definition
                    self.tool_origins[tool_name] = module_name
                self.server_info["total_tools"] = len(self.tools)
                self.tool_health["failed_loads"][module_name] = {
                    "error": str(exc),
                    "timestamp": time.time(),
                }
                self._record_internal_failure(
                    component="mcp_server",
                    operation="tool_refresh_module",
                    error=exc,
                    context={"module_name": module_name, "import_name": import_name},
                    severity="error",
                )
                return {
                    "ok": False,
                    "surface": "bb7_tool_refresh_module",
                    "module_name": module_name,
                    "import_name": import_name,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "rolled_back": True,
                    "tool_count": len(self.tools),
                }

    def _write_jsonl_row(
        self,
        path: Path,
        row: Dict[str, Any],
        lock: Optional[threading.Lock] = None,
    ) -> None:
        """Append one JSON line to disk with optional serialization lock."""
        payload = json.dumps(self._to_jsonable(row), ensure_ascii=False) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if lock is None:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(payload)
            return

        with lock:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(payload)

    def _record_internal_failure(
        self,
        component: str,
        operation: str,
        error: Union[Exception, str],
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
        turn_id: Optional[str] = None,
    ) -> str:
        """
        Persist an internal control-plane failure outside the normal event stream.
        This path must never be silent, even when the main telemetry stream breaks.
        """
        failure_id = f"if_{uuid.uuid4().hex}"
        message = str(error)
        row = {
            "failure_id": failure_id,
            "ts": time.time(),
            "session_id": getattr(self, "session_id", ""),
            "turn_id": turn_id or "",
            "component": component,
            "operation": operation,
            "severity": severity,
            "error_type": type(error).__name__
            if isinstance(error, Exception)
            else "RuntimeError",
            "error": message,
            "context": self._to_jsonable(context or {}),
        }

        tool_health = getattr(self, "tool_health", None)
        if isinstance(tool_health, dict):
            cache = tool_health.setdefault("internal_failures", [])
            cache.append(
                {
                    "failure_id": failure_id,
                    "ts": row["ts"],
                    "component": component,
                    "operation": operation,
                    "severity": severity,
                    "error": message[:300],
                }
            )
            if len(cache) > 200:
                del cache[:-200]

        logger = getattr(self, "logger", None)
        if logger is not None:
            log_method = {
                "critical": logger.critical,
                "warning": logger.warning,
                "error": logger.error,
            }.get(severity, logger.error)
            log_method(
                "Internal failure [%s.%s] %s: %s",
                component,
                operation,
                failure_id,
                message,
            )
        else:
            sys.stderr.write(
                f"[mcp_server] Internal failure [{component}.{operation}] {failure_id}: {message}\n"
            )
            sys.stderr.flush()

        try:
            if hasattr(self, "internal_failures_file"):
                self._write_jsonl_row(
                    self.internal_failures_file,
                    row,
                    lock=getattr(self, "_internal_failure_lock", None),
                )
        except Exception as write_exc:
            sys.stderr.write(
                "[mcp_server] INTERNAL FAILURE LOGGING BROKEN "
                f"for {component}.{operation}: {write_exc}\n"
            )
            sys.stderr.write(json.dumps(row, ensure_ascii=False) + "\n")
            sys.stderr.flush()

        return failure_id

    def _init_distillation_db(self) -> None:
        """Initialize SQLite3 distillation database for persistent RLHF logging."""
        try:
            self._distillation_db_path = self.data_dir / "distillation.db"
            self._distillation_conn = sqlite3.connect(
                str(self._distillation_db_path), check_same_thread=False
            )
            self._distillation_conn.execute("""
                CREATE TABLE IF NOT EXISTS trajectories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trajectory_id TEXT UNIQUE NOT NULL,
                    timestamp REAL NOT NULL,
                    session_id TEXT,
                    source_plane TEXT,
                    environment_state TEXT,
                    quality_status TEXT DEFAULT 'unreviewed',
                    quality_score REAL,
                    quality_heuristics TEXT,
                    human_labels TEXT,
                    trajectory_data TEXT NOT NULL,
                    telemetry_data TEXT
                )
            """)
            self._distillation_conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    tool_name TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    latency_seconds REAL,
                    error_message TEXT,
                    session_id TEXT,
                    arguments TEXT
                )
            """)
            self._distillation_conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT,
                    tool_calls TEXT,
                    tool_call_id TEXT
                )
            """)
            self._distillation_conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON trajectories(timestamp)"
            )
            self._distillation_conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session ON trajectories(session_id)"
            )
            self._distillation_conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_usage(tool_name)"
            )
            self._distillation_conn.commit()
            self.logger.info(
                "SQLite3 distillation database initialized at %s",
                self._distillation_db_path,
            )
        except Exception as e:
            self._record_internal_failure(
                component="mcp_server",
                operation="init_distillation_db",
                error=e,
                context={"db_path": str(self.data_dir / "distillation.db")},
                severity="error",
            )
            self._distillation_db_path = None
            self._distillation_conn = None

    def flush_trajectory_to_distillation(self, reason: str = "session_end") -> Optional[str]:
        """
        Flush the in-memory trajectory buffer to distillation storage.
        Called at: session end, agent run completion, explicit bb7_lisan_distill call.
        Returns trajectory_id or None if nothing to flush.
        """
        if not self._trajectory_buffer or self._distillation_engine is None:
            return None

        with self._trajectory_buffer_lock:
            trajectory = list(self._trajectory_buffer)
            self._trajectory_buffer.clear()

        telemetry = {
            "total_tool_calls": len(trajectory),
            "latency_seconds": time.time() - self._trajectory_session_start,
            "flush_reason": reason,
            "session_id": getattr(self, "session_id", ""),
        }

        trajectory_id = self._distillation_engine.log_full_trajectory(
            source_plane="sovereign_mcp_session",
            session_id=getattr(self, "session_id", ""),
            trajectory=trajectory,
            telemetry=telemetry,
            environment_state={
                "os": sys.platform,
                "active_tools_count": len(self.tools),
                "workspace_root": str(self.workspace_root),
            },
        )

        self.logger.info(
            "Trajectory flushed to distillation: %s (%d tool calls, reason=%s)",
            trajectory_id, len(trajectory), reason,
        )
        return trajectory_id

    def _late_init_distillation(self) -> None:
        """
        Late-initialize distillation AFTER the full tool plane is stable.
        Gate: SOVEREIGN_DISTILLATION_ENABLED=1 env var (default off).
        Non-fatal: failure here must never affect tool execution.
        """
        if os.environ.get("SOVEREIGN_DISTILLATION_ENABLED", "0").strip() != "1":
            self.logger.info(
                "Distillation disabled (set SOVEREIGN_DISTILLATION_ENABLED=1 to enable)"
            )
            return
        try:
            from tools.lisan_al_gaib import DistillationSubsystem
            self._distillation_engine = DistillationSubsystem(
                data_dir=self.data_dir, logger=self.logger
            )
            self.logger.info("Distillation engine initialized (opt-in mode)")
        except Exception as e:
            self.logger.warning("Distillation init failed (non-fatal): %s", e)
            self._distillation_engine = None

    # ── Autonomous Exo Cycle ─────────────────────────────────────────────────
    # The server is a 24/7 state machine. This cycle runs INDEPENDENT of model
    # calls. Tool calls are events in the process — not the process itself.
    _EXO_CYCLE_INTERVAL_S: int = 45  # seconds between autonomous ticks

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        """Parse boolean environment flags without risking import/startup failure."""
        raw = os.environ.get(name)
        if raw is None:
            return default
        return str(raw).strip().lower() not in {"0", "false", "no", "off"}

    @staticmethod
    def _env_int(
        name: str,
        default: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> int:
        """Parse bounded integer environment settings with safe fallback."""
        raw = os.environ.get(name)
        if raw is None or str(raw).strip() == "":
            value = int(default)
        else:
            try:
                value = int(str(raw).strip())
            except ValueError:
                value = int(default)
        if min_value is not None:
            value = max(int(min_value), value)
        if max_value is not None:
            value = min(int(max_value), value)
        return value

    def _wire_journal_lisan_bridge(self) -> None:
        """
        Bridge all signal-generating tool modules → lisan CognitiveJournalSubsystem.

        Injects cognitive_journal into:
          - ThoughtJournalTool: bb7_journal_capture_decision writes routing signals
          - IntelligentOptimizationTool: pattern insights feed back to lisan routing

        This closes the bidirectional cascade:
          lisan surface_relevant → autonomous_routing_context.json → auto_tool reads
          auto_tool discovers patterns → record_decision → lisan routes on them next tick
        """
        exo = self.tool_modules.get("exoskeleton_tool")
        if exo is None:
            return
        cognitive_journal = getattr(exo, "_cognitive_journal", None)
        if cognitive_journal is None:
            self.logger.info("Lisan bridge: cognitive_journal not initialized (lisan offline?)")
            return

        # Wire ThoughtJournalTool
        journal_tool = self.tool_modules.get("thought_journal_tool")
        if journal_tool is not None:
            try:
                journal_tool.set_cognitive_journal(cognitive_journal)
                self.logger.info("Bridge wired: ThoughtJournalTool → CognitiveJournalSubsystem")
            except AttributeError:
                pass

        # Wire IntelligentOptimizationTool (auto_tool_module)
        auto_tool = self.tool_modules.get("auto_tool_module")
        if auto_tool is not None:
            try:
                auto_tool.set_cognitive_journal(cognitive_journal)
                self.logger.info("Bridge wired: IntelligentOptimizationTool → CognitiveJournalSubsystem")
            except AttributeError:
                pass

    def _start_autonomous_cycle(self) -> None:
        """Spawn the perpetual autonomous exo cycle as a daemon thread."""
        t = threading.Thread(
            target=self._autonomous_exo_cycle_loop,
            daemon=True,
            name="sovereign-exo-cycle",
        )
        t.start()
        self.logger.info(
            "Autonomous exo cycle started (interval: %ds)", self._EXO_CYCLE_INTERVAL_S
        )

    def _autonomous_exo_cycle_loop(self) -> None:
        """
        Perpetual server-side autonomous cycle. NEVER stops.

        The model joins an already-running system. It does not start it.

        Actions per tick (direct Python calls — zero JSON-RPC overhead):
          1. Sync exo live tool catalog priors
          2. Rebuild spectral IDF if catalog grew
          3. Mine execution_history.jsonl for new golden path candidates
          4. Surface proactive actions from auto_tool_module
          5. Append cycle telemetry event (feeds distillation when enabled)
        """
        # Wait for full tool plane boot (up to 30s)
        boot_deadline = time.time() + 30.0
        while time.time() < boot_deadline:
            if "exoskeleton_tool" in self.tool_modules:
                break
            time.sleep(1.0)
        else:
            self.logger.warning(
                "Autonomous cycle: exoskeleton_tool not loaded within 30s — cycle degraded"
            )

        cycle_n = 0
        while True:
            cycle_n += 1
            try:
                exo = self.tool_modules.get("exoskeleton_tool")
                if exo is not None:
                    # 1. Sync live catalog — keeps tool priors current
                    try:
                        exo._maybe_sync_live_tools(force=False)
                    except Exception as sync_exc:
                        self.logger.debug("Cycle %d: Sync live tools failed: %s", cycle_n, sync_exc)

                    # 2. Rebuild spectral IDF if decomposer is alive
                    try:
                        sd = getattr(exo, "_spectral_decomposer", None)
                        if sd is not None and hasattr(sd, "rebuild_idf"):
                            sd.rebuild_idf(exo.tool_catalog)
                    except Exception as idf_exc:
                        self.logger.debug("Cycle %d: Rebuild IDF failed: %s", cycle_n, idf_exc)

                    # 3. Mine execution history for new golden path candidates
                    try:
                        oracle = getattr(exo, "_golden_oracle", None)
                        history_file = getattr(exo, "history_file", None)
                        if oracle is not None and history_file is not None and history_file.exists():
                            history: List[Dict[str, Any]] = []
                            with open(history_file, "r", encoding="utf-8") as _hf:
                                for _line in _hf:
                                    try:
                                        row = json.loads(_line.strip())
                                        if row:
                                            history.append(row)
                                    except Exception as json_exc:
                                        self.logger.debug("Cycle %d: Load history row failed: %s", cycle_n, json_exc)
                            if len(history) >= 4:
                                try:
                                    from tools.lisan_al_gaib import _MetaLearningEngine
                                    meta = _MetaLearningEngine(
                                        golden_path_min_occurrences=3,
                                        golden_path_min_success_rate=0.8,
                                    )
                                    candidates = meta.discover_golden_paths(history[-200:])
                                    if candidates:
                                        self.logger.info(
                                            "Cycle %d: %d golden path candidate(s) discovered",
                                            cycle_n,
                                            len(candidates),
                                        )
                                        self._append_event(
                                            event_type="autonomous_golden_path_discovery",
                                            source="sovereign_exo_cycle",
                                            payload={
                                                "cycle": cycle_n,
                                                "candidates": len(candidates),
                                                "top_chain": candidates[0].get("chain", [])
                                                if candidates
                                                else [],
                                            },
                                            importance_hint=0.8,
                                        )
                                        # Auto-promote high-confidence candidates
                                        # (>= 0.9 success_rate) into golden_paths.json
                                        promoted = 0
                                        for _cand in candidates:
                                            if float(_cand.get("success_rate", 0)) >= 0.9:
                                                try:
                                                    did_promote = oracle.promote_candidate(
                                                        _cand, confidence_threshold=0.9
                                                    )
                                                    if did_promote:
                                                        promoted += 1
                                                except Exception as promote_exc:
                                                    self.logger.warning(
                                                        "Cycle %d: Oracle promote candidate failed: %s",
                                                        cycle_n,
                                                        promote_exc,
                                                    )
                                        if promoted:
                                            self.logger.info(
                                                "Cycle %d: %d candidate(s) auto-promoted to golden_paths.json",
                                                cycle_n,
                                                promoted,
                                            )
                                except Exception as _meta_err:
                                    self.logger.debug(
                                        "Cycle %d meta-learning: %s", cycle_n, _meta_err
                                    )
                    except Exception as mine_exc:
                        self.logger.warning("Cycle %d: Mining execution history failed: %s", cycle_n, mine_exc)

                # 4. Surface relevant journal decisions into routing context file
                # — so the next model turn has pre-computed decision history with zero latency
                try:
                    cognitive_journal = getattr(exo, "_cognitive_journal", None) if exo else None
                    if cognitive_journal is not None and hasattr(cognitive_journal, "surface_relevant"):
                        # Build recent context from last catalog tool names + cycle count
                        _recent_ctx = f"cycle {cycle_n} autonomous routing context"
                        if exo is not None and hasattr(exo, "tool_catalog"):
                            _recent_ctx += " " + " ".join(
                                list(exo.tool_catalog.keys())[-10:]
                            )
                        relevant = cognitive_journal.surface_relevant(_recent_ctx, max_results=5)
                        if relevant:
                            _ctx_path = self.data_dir / "autonomous_routing_context.json"
                            try:
                                _tmp = _ctx_path.with_suffix(".json.tmp")
                                with open(_tmp, "w", encoding="utf-8") as _cf:
                                    json.dump(
                                        {
                                            "cycle": cycle_n,
                                            "timestamp": time.time(),
                                            "surfaced_decisions": relevant,
                                        },
                                        _cf,
                                        indent=2,
                                    )
                                _tmp.replace(_ctx_path)
                            except Exception:
                                pass
                except Exception:
                    pass

                # 5. Proactive actions from auto_tool_module
                auto_tool = self.tool_modules.get("auto_tool_module")
                if auto_tool is not None and hasattr(auto_tool, "_generate_proactive_actions"):
                    try:
                        proactive = auto_tool._generate_proactive_actions()
                        if proactive:
                            self._append_event(
                                event_type="autonomous_proactive_actions",
                                source="sovereign_exo_cycle",
                                payload={"cycle": cycle_n, "actions": proactive[:3]},
                                importance_hint=0.4,
                            )
                    except Exception:
                        pass

                # 6. Narrative synthesis every 8 cycles (~6 minutes)
                # — Pre-computes a session briefing so bb7_exo_briefing has zero cold-start latency.
                # Calls exo.bb7_exo_briefing() directly (it handles routing + narrative internally).
                if cycle_n % 8 == 0 and exo is not None:
                    try:
                        briefing_result = exo.bb7_exo_briefing(
                            intent="autonomous session summary: current tool catalog state and routing priors",
                            max_recommendations=5,
                        )
                        if briefing_result:
                            _brief_path = self.data_dir / "precomputed_briefing.json"
                            try:
                                _tmp = _brief_path.with_suffix(".json.tmp")
                                with open(_tmp, "w", encoding="utf-8") as _bf:
                                    json.dump(
                                        {
                                            "cycle": cycle_n,
                                            "timestamp": time.time(),
                                            "briefing": briefing_result,
                                        },
                                        _bf,
                                        indent=2,
                                    )
                                _tmp.replace(_brief_path)
                                self.logger.debug(
                                    "Cycle %d: session briefing pre-computed",
                                    cycle_n,
                                )
                            except Exception:
                                pass
                    except Exception:
                        pass

                # 7. Muad'Dib Neural Telemetry & Save (Phase 5)
                # Logs substrate status every 4 cycles, auto-saves checkpoint every 16
                if exo is not None:
                    twin = getattr(exo, "_digital_twin", None)
                    if twin is not None:
                        try:
                            # Telemetry every 4 cycles
                            if cycle_n % 4 == 0 and hasattr(twin, "bb7_dt_status"):
                                status = twin.bb7_dt_status()
                                self.logger.info(
                                    "Muad'Dib status (cycle %d): obs=%d, states=%d, q_entries=%d, vocab=%d/%d, initialized=%s",
                                    cycle_n,
                                    status.get("observations", 0),
                                    status.get("states_learned", 0),
                                    status.get("q_entries", 0),
                                    status.get("vocab_size_used", 0),
                                    status.get("vocab_size_max", 4096),
                                    status.get("tokenizer_initialized", False)
                                )

                            # Save every 16 cycles
                            if cycle_n % 16 == 0 and hasattr(twin, "bb7_dt_save"):
                                twin.bb7_dt_save()
                                self.logger.debug("Cycle %d: Muad'Dib checkpoint saved", cycle_n)

                            # Bounded continuous self-play. This trains an
                            # isolated candidate policy/value head and writes
                            # real tensor weights as safetensors; JSON remains
                            # metadata/ledger only. Synthetic self-play does
                            # not update the real Q-table unless explicitly
                            # enabled by MUADIB_SELF_PLAY_UPDATE_QTABLE=1.
                            # Promotion is opt-in: by default the cadence
                            # archives candidate safetensors without advancing
                            # the active/champion head. Set
                            # MUADIB_SELF_PLAY_PROMOTE=1 only for deliberate
                            # live weight evolution; set
                            # MUADIB_SELF_PLAY_LOCK_ACTIVE=1 to keep training
                            # candidates while pinning the active champion
                            # head/pointer even if promotion is requested.
                            self_play_enabled = self._env_bool(
                                "MUADIB_SELF_PLAY_ENABLED", True
                            )
                            self_play_interval = self._env_int(
                                "MUADIB_SELF_PLAY_INTERVAL_CYCLES",
                                32,
                                min_value=4,
                                max_value=10_000,
                            )
                            if (
                                self_play_enabled
                                and cycle_n % self_play_interval == 0
                                and hasattr(exo, "bb7_dt_self_play")
                            ):
                                sp_episodes = self._env_int(
                                    "MUADIB_SELF_PLAY_EPISODES",
                                    4,
                                    min_value=1,
                                    max_value=64,
                                )
                                sp_max_steps = self._env_int(
                                    "MUADIB_SELF_PLAY_MAX_STEPS",
                                    3,
                                    min_value=2,
                                    max_value=8,
                                )
                                sp_promote = self._env_bool(
                                    "MUADIB_SELF_PLAY_PROMOTE", False
                                )
                                sp_update_qtable = self._env_bool(
                                    "MUADIB_SELF_PLAY_UPDATE_QTABLE", False
                                )
                                sp_result = exo.bb7_dt_self_play(
                                    episodes=sp_episodes,
                                    max_steps=sp_max_steps,
                                    promote=sp_promote,
                                    update_qtable=sp_update_qtable,
                                    session_id=f"autonomous_self_play_cycle_{cycle_n}",
                                )
                                if not isinstance(sp_result, dict) or not sp_result.get("ok"):
                                    raise RuntimeError(
                                        f"Muad'Dib self-play failed: {sp_result}"
                                    )
                                checkpoint = sp_result.get("checkpoint", {})
                                metrics = sp_result.get("metrics", {})
                                self._append_event(
                                    event_type="muadib_self_play_checkpoint",
                                    source="sovereign_exo_cycle",
                                    payload={
                                        "cycle": cycle_n,
                                        "interval_cycles": self_play_interval,
                                        "checkpoint": checkpoint.get("checkpoint"),
                                        "weights_format": sp_result.get("weights_format"),
                                        "promotion_requested": sp_result.get(
                                            "promotion_requested"
                                        ),
                                        "promoted": sp_result.get("promoted"),
                                        "active_locked": sp_result.get("active_locked"),
                                        "lock_source": sp_result.get("lock_source"),
                                        "episodes": metrics.get("episodes"),
                                        "max_steps": metrics.get("max_steps"),
                                        "avg_reward": metrics.get("avg_reward"),
                                        "avg_loss": metrics.get("avg_loss"),
                                        "qtable_updated": sp_result.get("qtable_updated"),
                                    },
                                    importance_hint=0.75,
                                )
                                self.logger.info(
                                    "Cycle %d: Muad'Dib self-play checkpoint=%s format=%s promoted=%s avg_reward=%.4f avg_loss=%.4f qtable_updated=%s",
                                    cycle_n,
                                    checkpoint.get("checkpoint"),
                                    sp_result.get("weights_format"),
                                    sp_result.get("promoted"),
                                    float(metrics.get("avg_reward", 0.0) or 0.0),
                                    float(metrics.get("avg_loss", 0.0) or 0.0),
                                    sp_result.get("qtable_updated"),
                                )
                        except Exception as _twin_err:
                            self.logger.warning(
                                "Cycle %d Muad'Dib telemetry/self-play fail: %s",
                                cycle_n,
                                _twin_err,
                            )

                self.logger.debug("Autonomous exo cycle %d complete", cycle_n)

            except Exception as outer_err:
                self.logger.warning(
                    "Autonomous exo cycle %d outer error: %s", cycle_n, outer_err
                )

            time.sleep(self._EXO_CYCLE_INTERVAL_S)

    @staticmethod
    def _pid_is_alive(pid: int) -> bool:
        """Best-effort process liveness check for singleton lock enforcement."""
        if not isinstance(pid, int) or pid <= 0:
            return False
        if pid == os.getpid():
            return True
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _acquire_singleton_lock(self) -> None:
        """
        Enforce one active MCP server process per canonical data directory.
        Only enforced in SSE transport mode (one persistent server per port).
        In stdio mode each client spawns its own process — shared SQLite handles
        concurrent state, no singleton needed.
        Can also be bypassed by setting MCP_ALLOW_MULTI_INSTANCE=1.
        """
        if getattr(self, "_transport", "stdio") == "stdio":
            return

        if str(os.environ.get("MCP_ALLOW_MULTI_INSTANCE", "")).strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            self.logger.warning(
                "Multi-instance mode enabled via MCP_ALLOW_MULTI_INSTANCE; "
                "singleton lock is bypassed"
            )
            return

        lock_path = self._instance_lock_path
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        for _attempt in range(2):
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(
                        {
                            "pid": os.getpid(),
                            "session_id": self.session_id,
                            "created_at": time.time(),
                            "data_dir": str(self.data_dir),
                        },
                        handle,
                    )
                return
            except FileExistsError:
                holder_pid: Optional[int] = None
                try:
                    with open(lock_path, "r", encoding="utf-8") as handle:
                        lock_payload = json.load(handle)
                    raw_pid = lock_payload.get("pid")
                    if isinstance(raw_pid, int):
                        holder_pid = raw_pid
                except Exception:
                    holder_pid = None

                if holder_pid is not None and self._pid_is_alive(holder_pid):
                    raise RuntimeError(
                        "Another MCP server instance is already active for "
                        f"data dir '{self.data_dir}' (pid={holder_pid})."
                    )

                try:
                    lock_path.unlink(missing_ok=True)
                except OSError as exc:
                    raise RuntimeError(
                        "Found stale MCP lock file but could not remove it: "
                        f"{lock_path} ({exc})"
                    ) from exc
            except OSError as exc:
                raise RuntimeError(
                    "Failed to create MCP singleton lock at "
                    f"{lock_path}: {exc}"
                ) from exc

        raise RuntimeError(
            f"Failed to acquire MCP singleton lock for data dir '{self.data_dir}'."
        )

    def _release_singleton_lock(self) -> None:
        """Release singleton lock on shutdown when owned by this process."""
        lock_path = self._instance_lock_path
        try:
            if not lock_path.exists():
                return
            owner_pid: Optional[int] = None
            try:
                with open(lock_path, "r", encoding="utf-8") as handle:
                    lock_payload = json.load(handle)
                raw_pid = lock_payload.get("pid")
                if isinstance(raw_pid, int):
                    owner_pid = raw_pid
            except Exception:
                owner_pid = None

            if owner_pid is not None and owner_pid != os.getpid():
                return
            lock_path.unlink(missing_ok=True)
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="release_singleton_lock",
                error=exc,
                context={"lock_path": str(lock_path)},
                severity="warning",
            )

    @staticmethod
    def _to_jsonable(value: Any) -> Any:
        """Convert arbitrary objects into JSON-safe structures."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(k): MCPServer._to_jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [MCPServer._to_jsonable(v) for v in value]
        return str(value)

    @staticmethod
    def _summarize_value(value: Any, max_chars: int = 500) -> str:
        """Create a short textual summary of a payload for telemetry rows."""
        if isinstance(value, str):
            text = value
        else:
            try:
                text = json.dumps(MCPServer._to_jsonable(value), ensure_ascii=False)
            except Exception:
                text = str(value)
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    @staticmethod
    def _parse_external_timestamp(value: Any) -> float:
        """Parse unix or ISO-8601 timestamps into epoch seconds."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.strip():
            text = value.strip()
            try:
                return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
            except ValueError:
                try:
                    return float(text)
                except ValueError:
                    return time.time()
        return time.time()

    @staticmethod
    def _extract_codex_content_text(content: Any) -> str:
        """Flatten Codex message content blocks into plain text."""
        if isinstance(content, str):
            return content.strip()
        if not isinstance(content, list):
            return ""

        blocks: List[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                blocks.append(text.strip())
        return "\n".join(blocks).strip()

    def _load_codex_ingest_state(self) -> Dict[str, Any]:
        """Load persisted Codex ingest offsets from canonical data root."""
        default_state = {"history_jsonl": {}, "rollouts": {}, "last_sync_ts": 0.0}
        if not self.codex_ingest_state_file.exists():
            return default_state

        try:
            with open(self.codex_ingest_state_file, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise RuntimeError("codex ingest state must be a JSON object")
            loaded.setdefault("history_jsonl", {})
            loaded.setdefault("rollouts", {})
            loaded.setdefault("last_sync_ts", 0.0)
            return loaded
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="load_codex_ingest_state",
                error=exc,
                context={"path": str(self.codex_ingest_state_file)},
                severity="error",
            )
            return default_state

    def _save_codex_ingest_state(self, state: Dict[str, Any]) -> None:
        """Atomically persist Codex ingest offsets."""
        tmp_path = self.codex_ingest_state_file.with_name(
            f"{self.codex_ingest_state_file.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        )
        try:
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(self._to_jsonable(state), handle, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.codex_ingest_state_file)
        except Exception as exc:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            self._record_internal_failure(
                component="mcp_server",
                operation="save_codex_ingest_state",
                error=exc,
                context={"path": str(self.codex_ingest_state_file)},
                severity="error",
            )
            raise

    def _select_codex_rollout(self) -> Optional[Dict[str, Any]]:
        """Pick the most recent Codex rollout for this workspace from the global state DB."""
        if not self._codex_state_db_path.exists():
            return None

        target_workspace = str(self.workspace_root.resolve())
        try:
            conn = sqlite3.connect(str(self._codex_state_db_path))
            try:
                rows = conn.execute(
                    """
                    SELECT id, rollout_path, updated_at, cwd
                    FROM threads
                    WHERE archived = 0
                    ORDER BY updated_at DESC
                    LIMIT 50
                    """
                ).fetchall()
            finally:
                conn.close()
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="query_codex_state_db",
                error=exc,
                context={"db_path": str(self._codex_state_db_path)},
                severity="error",
            )
            return None

        selected: Optional[Tuple[str, str, Any, str]] = None
        for row in rows:
            if len(row) != 4:
                continue
            thread_id, rollout_path, updated_at, cwd = row
            if not isinstance(rollout_path, str) or not rollout_path:
                continue
            rollout_file = Path(rollout_path)
            if not rollout_file.exists():
                continue
            if isinstance(cwd, str) and cwd:
                try:
                    if str(Path(cwd).expanduser().resolve()) == target_workspace:
                        selected = (thread_id, rollout_path, updated_at, cwd)
                        break
                except OSError:
                    pass
            if selected is None:
                selected = (thread_id, rollout_path, updated_at, cwd)

        if selected is None:
            return None

        thread_id, rollout_path, updated_at, cwd = selected
        return {
            "thread_id": str(thread_id),
            "rollout_path": str(rollout_path),
            "updated_at": float(updated_at or 0.0),
            "cwd": str(cwd or ""),
        }

    def _stream_jsonl_delta(
        self,
        path: Path,
        offset: int,
        source_label: str,
        turn_id: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Read new JSONL records from a file starting at the persisted offset."""
        if not path.exists():
            return [], 0

        current_size = path.stat().st_size
        safe_offset = max(0, min(int(offset), current_size))
        if offset != safe_offset:
            self._record_internal_failure(
                component="mcp_server",
                operation="codex_offset_reset",
                error=RuntimeError(
                    f"{source_label} offset {offset} invalid for size {current_size}"
                ),
                context={"path": str(path), "source_label": source_label},
                severity="warning",
                turn_id=turn_id,
            )

        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as handle:
            if safe_offset > 0:
                handle.seek(max(0, safe_offset - 1))
                previous_char = handle.read(1)
                if previous_char != "\n":
                    skipped_fragment = handle.readline()
                    realigned_offset = handle.tell()
                    self._record_internal_failure(
                        component="mcp_server",
                        operation="codex_offset_realigned",
                        error=RuntimeError(
                            f"Offset {safe_offset} did not start on a line boundary"
                        ),
                        context={
                            "path": str(path),
                            "source_label": source_label,
                            "realigned_offset": realigned_offset,
                            "skipped_fragment_preview": skipped_fragment[:160],
                        },
                        severity="warning",
                        turn_id=turn_id,
                    )
                else:
                    handle.seek(safe_offset)
            else:
                handle.seek(0)
            while True:
                line_start = handle.tell()
                raw_line = handle.readline()
                if not raw_line:
                    break
                if not raw_line.strip():
                    continue
                try:
                    parsed = json.loads(raw_line)
                except Exception as exc:
                    self._record_internal_failure(
                        component="mcp_server",
                        operation="codex_jsonl_parse",
                        error=exc,
                        context={
                            "path": str(path),
                            "source_label": source_label,
                            "line_offset": line_start,
                            "line_preview": raw_line[:240],
                        },
                        severity="error",
                        turn_id=turn_id,
                    )
                    continue
                records.append(parsed)
            next_offset = handle.tell()

        return records, next_offset

    @staticmethod
    def _decode_tool_arguments(raw_arguments: Any) -> Dict[str, Any]:
        """Decode Codex serialized function-call arguments into a dict when possible."""
        if isinstance(raw_arguments, dict):
            return raw_arguments
        if isinstance(raw_arguments, str) and raw_arguments.strip():
            try:
                decoded = json.loads(raw_arguments)
                return decoded if isinstance(decoded, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _make_codex_memory_key(
        prefix: str,
        session_id: str,
        role: str,
        timestamp_value: float,
        content: str,
    ) -> str:
        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{session_id}_{int(timestamp_value)}_{role}_{digest}"

    def _bulk_promote_memories(
        self,
        entries: List[Dict[str, Any]],
        turn_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Promote derived chat/context records into the memory plane in bounded chunks."""
        if not entries:
            return {"stored": 0, "chunks": 0}

        memory_tool = self.tool_modules.get("memory_tool")
        if memory_tool is None or not hasattr(memory_tool, "bulk_store"):
            self._record_internal_failure(
                component="mcp_server",
                operation="bulk_promote_memories",
                error=RuntimeError("memory_tool bulk_store unavailable"),
                context={"entry_count": len(entries)},
                severity="error",
                turn_id=turn_id,
            )
            return {"stored": 0, "chunks": 0}

        deduped: Dict[str, Dict[str, Any]] = {}
        for entry in entries:
            key = entry.get("key")
            if isinstance(key, str) and key:
                deduped[key] = entry

        stored = 0
        chunks = 0
        pending = list(deduped.values())
        for start in range(0, len(pending), 100):
            chunk = pending[start : start + 100]
            chunks += 1
            try:
                result = memory_tool.bulk_store(json.dumps(chunk, ensure_ascii=False))
            except Exception as exc:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="bulk_promote_memories",
                    error=exc,
                    context={"chunk_index": chunks, "chunk_size": len(chunk)},
                    severity="error",
                    turn_id=turn_id,
                )
                continue

            result_text = str(result)
            if result_text.startswith("Error") or result_text.startswith("Validation errors"):
                self._record_internal_failure(
                    component="mcp_server",
                    operation="bulk_promote_memories",
                    error=RuntimeError(result_text),
                    context={"chunk_index": chunks, "chunk_size": len(chunk)},
                    severity="error",
                    turn_id=turn_id,
                )
                continue

            stored += len(chunk)

        return {"stored": stored, "chunks": chunks}

    def _process_codex_rollout_records(
        self,
        thread_id: str,
        records: List[Dict[str, Any]],
        turn_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize current-thread Codex rollout records into DB logs, telemetry, and memory."""
        summary = {
            "records": len(records),
            "messages": 0,
            "tool_calls": 0,
            "tool_outputs": 0,
            "reasoning_items": 0,
        }
        memory_entries: List[Dict[str, Any]] = []

        _last_fc_tool: str = ""  # Track function_call tool name for output pairing
        for record in records:
            record_type = record.get("type")
            payload = record.get("payload", {})
            timestamp_value = self._parse_external_timestamp(record.get("timestamp"))

            if record_type == "event_msg" and isinstance(payload, dict):
                payload_type = payload.get("type")
                if payload_type == "user_message":
                    message = payload.get("message", "")
                    if isinstance(message, str) and message.strip():
                        self._log_conversation_message(
                            thread_id,
                            "user",
                            message,
                            timestamp=timestamp_value,
                        )
                        memory_entries.append(
                            {
                                "key": self._make_codex_memory_key(
                                    "codex_rollout",
                                    thread_id,
                                    "user",
                                    timestamp_value,
                                    message,
                                ),
                                "value": (
                                    f"[source=codex_rollout role=user thread={thread_id} "
                                    f"ts={timestamp_value}] {message}"
                                ),
                                "category": "context",
                                "importance": 0.68,
                                "tags": ["codex", "chat", "user", f"thread:{thread_id}"],
                            }
                        )
                        summary["messages"] += 1
                elif payload_type == "mcp_tool_call_end":
                    invocation = payload.get("invocation", {})
                    duration = payload.get("duration", {})
                    codex_tool_name = str(invocation.get("tool", ""))
                    self._append_event(
                        event_type="codex_tool_call_end",
                        source="codex_rollout",
                        turn_id=turn_id,
                        payload={
                            "thread_id": thread_id,
                            "tool_name": codex_tool_name,
                            "server": invocation.get("server", ""),
                            "arguments": invocation.get("arguments", {}),
                            "duration": duration,
                        },
                        importance_hint=0.3,
                    )
                    # ── Codex → Muad'Dib overlay ─────────────────────────
                    # Feed codex tool-call outcomes directly into the digital
                    # twin Q-table.  This is the overlay path: every tool call
                    # codex executes trains the neural substrate in real time.
                    if codex_tool_name:
                        self._feed_codex_tool_to_twin(
                            tool_name=codex_tool_name,
                            duration=duration,
                            thread_id=thread_id,
                        )
                    summary["tool_outputs"] += 1
                continue

            if record_type != "response_item" or not isinstance(payload, dict):
                continue

            payload_type = payload.get("type")
            if payload_type == "message":
                role = str(payload.get("role", "unknown"))
                text = self._extract_codex_content_text(payload.get("content"))
                if not text:
                    continue
                self._log_conversation_message(
                    thread_id,
                    role,
                    text,
                    timestamp=timestamp_value,
                )
                if role in {"user", "assistant"}:
                    memory_entries.append(
                        {
                            "key": self._make_codex_memory_key(
                                "codex_rollout",
                                thread_id,
                                role,
                                timestamp_value,
                                text,
                            ),
                            "value": (
                                f"[source=codex_rollout role={role} thread={thread_id} "
                                f"ts={timestamp_value}] {text}"
                            ),
                            "category": "context",
                            "importance": 0.62 if role == "assistant" else 0.68,
                            "tags": ["codex", "chat", role, f"thread:{thread_id}"],
                        }
                    )
                summary["messages"] += 1
            elif payload_type == "function_call":
                tool_name = str(payload.get("name", "unknown"))
                call_id = str(payload.get("call_id", ""))
                decoded_arguments = self._decode_tool_arguments(payload.get("arguments"))
                self._log_conversation_message(
                    thread_id,
                    "assistant",
                    f"[tool_call] {tool_name}",
                    tool_calls=[
                        {
                            "id": call_id,
                            "name": tool_name,
                            "arguments": decoded_arguments,
                        }
                    ],
                    tool_call_id=call_id,
                    timestamp=timestamp_value,
                )
                summary["tool_calls"] += 1
                _last_fc_tool = tool_name
            elif payload_type == "function_call_output":
                output = payload.get("output", "")
                self._append_event(
                    event_type="codex_function_call_output",
                    source="codex_rollout",
                    turn_id=turn_id,
                    payload={
                        "thread_id": thread_id,
                        "call_id": payload.get("call_id", ""),
                        "output_summary": self._summarize_value(output),
                    },
                    importance_hint=0.25,
                )
                # ── Codex output → Muad'Dib overlay (error detection) ──
                # If the output looks like an error, feed a negative signal
                # to the twin for the most recent function_call tool.
                if _last_fc_tool:
                    output_str = str(output)
                    is_error = (
                        output_str.startswith("Error:")
                        or output_str.startswith("error:")
                        or "Traceback" in output_str
                        or "Exception" in output_str
                    )
                    if is_error:
                        self._feed_codex_tool_to_twin(
                            tool_name=_last_fc_tool,
                            duration={},
                            thread_id=thread_id,
                            error=output_str[:300],
                        )
                    _last_fc_tool = ""
                summary["tool_outputs"] += 1
            elif payload_type == "reasoning":
                self._append_event(
                    event_type="codex_reasoning_observed",
                    source="codex_rollout",
                    turn_id=turn_id,
                    payload={
                        "thread_id": thread_id,
                        "summary_count": len(payload.get("summary", []))
                        if isinstance(payload.get("summary"), list)
                        else 0,
                        "has_plaintext_content": bool(payload.get("content")),
                        "has_encrypted_content": bool(payload.get("encrypted_content")),
                    },
                    importance_hint=0.2,
                )
                summary["reasoning_items"] += 1

        promotion = self._bulk_promote_memories(memory_entries, turn_id=turn_id)
        summary["memory_entries_stored"] = promotion["stored"]
        return summary

    def _feed_codex_tool_to_twin(
        self,
        tool_name: str,
        duration: Any,
        thread_id: str,
        error: Optional[str] = None,
    ) -> None:
        """
        Feed a codex tool-call outcome into the Muad'Dib digital twin Q-table.

        This is the overlay path that closes the data gap between codex
        history and the neural substrate.  Every tool call that codex
        executes against any MCP server now trains the Q-table in real
        time, accelerating convergence dramatically because codex generates
        a massive volume of tool calls across all sessions.

        Non-fatal: failures here must never affect codex ingestion.
        """
        try:
            exo = self.tool_modules.get("exoskeleton_tool")
            if exo is None:
                return
            twin = getattr(exo, "_digital_twin", None)
            if twin is None:
                return

            # Resolve category from exoskeleton catalog if available
            catalog = getattr(exo, "tool_catalog", {})
            category = catalog.get(tool_name, {}).get("category", "misc")

            # Extract latency from codex duration dict
            latency_ms = 0.0
            if isinstance(duration, dict):
                # Codex duration may have seconds or ms fields
                if "ms" in duration:
                    latency_ms = float(duration["ms"])
                elif "seconds" in duration:
                    latency_ms = float(duration["seconds"]) * 1000.0
                elif "secs" in duration:
                    latency_ms = float(duration["secs"]) * 1000.0
                elif "nanos" in duration:
                    latency_ms = float(duration.get("secs", 0)) * 1000.0 + float(duration["nanos"]) / 1_000_000.0
            elif isinstance(duration, (int, float)):
                latency_ms = float(duration) * 1000.0

            # Infer success: if an error was passed, or the tool name is empty, mark as failure
            success = bool(tool_name) and error is None

            twin.bb7_dt_observe(
                tool_name=tool_name,
                category=category,
                success=success,
                latency_ms=latency_ms,
                chain_length=1,  # codex calls are single-shot from our perspective
                session_id=f"codex_{thread_id}",
                error=error,
            )
            self.logger.debug(
                "Codex→Twin overlay: %s (cat=%s, success=%s, latency=%.1fms, thread=%s)",
                tool_name, category, success, latency_ms, thread_id,
            )
        except Exception as exc:
            # Non-fatal: log and continue. Never break codex ingestion.
            self.logger.debug(
                "Codex→Twin overlay failed for %s (non-fatal): %s",
                tool_name, exc,
            )

    def _process_codex_history_records(
        self,
        records: List[Dict[str, Any]],
        turn_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest global Codex history entries into conversation history."""
        count = 0
        for record in records:
            session_id = str(record.get("session_id", "unknown"))
            text = record.get("text", "")
            if not isinstance(text, str) or not text.strip():
                continue
            timestamp_value = self._parse_external_timestamp(record.get("ts"))
            self._log_conversation_message(
                session_id,
                "user",
                text,
                timestamp=timestamp_value,
            )
            count += 1

        if count:
            self._append_event(
                event_type="codex_history_ingested",
                source="codex_history",
                turn_id=turn_id,
                payload={"records_ingested": count, "path": str(self._codex_history_path)},
                importance_hint=0.25,
            )
        return {"records": count}

    def _query_conversation_context(
        self,
        context_text: str,
        max_results: int = 3,
    ) -> str:
        """Surface recent conversation snippets relevant to the current turn context."""
        if self._distillation_conn is None or not context_text.strip():
            return ""

        context_tokens = set(re.findall(r"[a-z0-9_]+", context_text.lower()))
        if not context_tokens:
            return ""

        try:
            if self._latest_codex_thread_id:
                rows = self._distillation_conn.execute(
                    """
                    SELECT timestamp, session_id, role, content
                    FROM conversation_history
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 400
                    """,
                    (self._latest_codex_thread_id,),
                ).fetchall()
            else:
                rows = self._distillation_conn.execute(
                    """
                    SELECT timestamp, session_id, role, content
                    FROM conversation_history
                    ORDER BY timestamp DESC
                    LIMIT 400
                    """
                ).fetchall()
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="query_conversation_context",
                error=exc,
                context={"latest_thread_id": self._latest_codex_thread_id or ""},
                severity="error",
            )
            return ""

        now = time.time()
        scored: List[Tuple[float, float, str, str, str]] = []
        for ts, session_id, role, content in rows:
            if not isinstance(content, str) or not content.strip():
                continue
            tokens = set(re.findall(r"[a-z0-9_]+", content.lower()))
            overlap = len(context_tokens & tokens)
            if overlap == 0:
                continue
            recency_days = max(0.0, (now - float(ts or now)) / 86400.0)
            recency_boost = 1.0 / (1.0 + recency_days)
            session_boost = (
                1.25
                if self._latest_codex_thread_id
                and session_id == self._latest_codex_thread_id
                else 1.0
            )
            score = overlap * session_boost + recency_boost
            scored.append((score, float(ts or now), str(session_id), str(role), content))

        if not scored:
            return ""

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        lines = ["Relevant conversation context:"]
        for _, ts, session_id, role, content in scored[: max(1, max_results)]:
            preview = content[:180] + ("..." if len(content) > 180 else "")
            ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            lines.append(f"- [{ts_str}] ({role}/{session_id}) {preview}")
        return "\n".join(lines)

    def _ingest_codex_context(self, turn_id: Optional[str] = None) -> Dict[str, Any]:
        """Ingest fresh Codex rollout/history records into the canonical MCP data plane."""
        with self._codex_ingest_lock:
            state = self._load_codex_ingest_state()
            summary: Dict[str, Any] = {
                "history_records": 0,
                "rollout_records": 0,
                "thread_id": "",
            }

            if self._codex_history_path.exists():
                history_state = state.setdefault("history_jsonl", {})
                history_records, next_offset = self._stream_jsonl_delta(
                    self._codex_history_path,
                    int(history_state.get("offset", 0) or 0),
                    "codex_history",
                    turn_id=turn_id,
                )
                if history_records:
                    history_summary = self._process_codex_history_records(
                        history_records,
                        turn_id=turn_id,
                    )
                    summary["history_records"] = history_summary["records"]
                history_state["offset"] = next_offset
                history_state["path"] = str(self._codex_history_path)

            rollout_info = self._select_codex_rollout()
            if rollout_info:
                thread_id = rollout_info["thread_id"]
                rollout_path = Path(rollout_info["rollout_path"])
                self._latest_codex_thread_id = thread_id
                summary["thread_id"] = thread_id
                rollout_state = state.setdefault("rollouts", {}).setdefault(
                    str(rollout_path),
                    {"offset": 0, "thread_id": thread_id},
                )
                rollout_records, next_offset = self._stream_jsonl_delta(
                    rollout_path,
                    int(rollout_state.get("offset", 0) or 0),
                    "codex_rollout",
                    turn_id=turn_id,
                )
                if rollout_records:
                    rollout_summary = self._process_codex_rollout_records(
                        thread_id,
                        rollout_records,
                        turn_id=turn_id,
                    )
                    summary.update(
                        {
                            "rollout_records": rollout_summary["records"],
                            "rollout_messages": rollout_summary["messages"],
                            "rollout_tool_calls": rollout_summary["tool_calls"],
                            "rollout_tool_outputs": rollout_summary["tool_outputs"],
                            "rollout_reasoning_items": rollout_summary["reasoning_items"],
                            "memory_entries_stored": rollout_summary[
                                "memory_entries_stored"
                            ],
                        }
                    )
                    self._append_event(
                        event_type="codex_rollout_ingested",
                        source="codex_rollout",
                        turn_id=turn_id,
                        payload={
                            "thread_id": thread_id,
                            "path": str(rollout_path),
                            "summary": summary,
                        },
                        importance_hint=0.35,
                    )
                rollout_state["offset"] = next_offset
                rollout_state["thread_id"] = thread_id
                rollout_state["updated_at"] = rollout_info["updated_at"]

            state["last_sync_ts"] = time.time()
            self._save_codex_ingest_state(state)
            return summary

    @staticmethod
    def _extract_artifacts(arguments: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Extract useful artifact references from tool args/results."""
        artifact_keys = (
            "path",
            "file_path",
            "directory",
            "filename",
            "url",
            "workspace_path",
            "session_id",
            "memory_key",
            "plan_id",
        )
        artifacts: Dict[str, Any] = {}
        for key in artifact_keys:
            if key in arguments:
                artifacts[key] = MCPServer._to_jsonable(arguments.get(key))

        if isinstance(result, dict):
            for key in artifact_keys:
                if key in result and key not in artifacts:
                    artifacts[key] = MCPServer._to_jsonable(result.get(key))

        return artifacts

    def _next_turn_id(self) -> str:
        """Allocate a monotonically increasing turn id inside this MCP session."""
        with self._telemetry_lock:
            self._turn_counter += 1
            return f"{self.session_id}:turn_{self._turn_counter:06d}"

    def _append_event(
        self,
        event_type: str,
        source: str,
        payload: Dict[str, Any],
        turn_id: Optional[str] = None,
        importance_hint: float = 0.0,
    ) -> Optional[str]:
        """
        Append one telemetry event row into events.jsonl.
        This is the passive continuity spine for distill and routing context.
        """
        event_id = f"evt_{uuid.uuid4().hex}"
        row = {
            "event_id": event_id,
            "ts": time.time(),
            "session_id": self.session_id,
            "turn_id": turn_id or "",
            "event_type": event_type,
            "source": source,
            "payload_json": self._to_jsonable(payload),
            "importance_hint": round(float(importance_hint), 4),
        }

        try:
            self._write_jsonl_row(self.events_file, row, lock=self._telemetry_lock)
            return event_id
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="append_event",
                error=exc,
                context={
                    "event_type": event_type,
                    "source": source,
                    "turn_id": turn_id or "",
                },
                severity="critical",
                turn_id=turn_id,
            )
            raise RuntimeError(
                f"Telemetry append failed for event '{event_type}' from '{source}': {exc}"
            ) from exc

    def _inject_proactive_memory_context(
        self, context_text: str = "session_start"
    ) -> Dict[str, Any]:
        """Proactively inject relevant memories at session start without explicit tool call.

        This runs automatically at session initialization to surface relevant context
        from the memory system without requiring an explicit bb7_memory_surface_context call.
        """
        if (
            not hasattr(self, "_proactive_memory_injected")
            or self._proactive_memory_injected
        ):
            return {"status": "skipped", "reason": "already_injected"}

        last_error: Optional[Exception] = None
        try:
            memory_tool = self.tool_modules.get("memory_tool")
            if memory_tool and hasattr(memory_tool, "surface_context"):
                result = memory_tool.surface_context(context_text, max_results=5)
                self._proactive_memory_injected = True
                self.logger.info(
                    "Proactive memory context injected: %d memories surfaced",
                    len(result.get("memories", [])) if isinstance(result, dict) else 0,
                )
                self._append_event(
                    event_type="memory_context_injected",
                    source="mcp_server",
                    payload={"context_text": context_text, "status": "success"},
                    importance_hint=0.7,
                )
                return {"status": "success", "injected": True, "context": result}
            elif memory_tool and hasattr(memory_tool, "memory_surface_context"):
                result = memory_tool.memory_surface_context(
                    context_text=context_text, max_results=5
                )
                self._proactive_memory_injected = True
                self._append_event(
                    event_type="memory_context_injected",
                    source="mcp_server",
                    payload={"context_text": context_text, "status": "success"},
                    importance_hint=0.7,
                )
                return {"status": "success", "injected": True, "context": result}
        except Exception as e:
            last_error = e
            self._record_internal_failure(
                component="mcp_server",
                operation="inject_proactive_memory_context",
                error=e,
                context={"context_text": context_text},
                severity="error",
            )

        reason = str(last_error) if last_error is not None else "memory_tool_unavailable"
        self._append_event(
            event_type="memory_context_injected",
            source="mcp_server",
            payload={
                "context_text": context_text,
                "status": "unavailable",
                "reason": reason,
            },
            importance_hint=0.4,
        )
        return {"status": "unavailable", "reason": reason}

    def _surface_turn_memory_context(
        self,
        turn_id: str,
        method: Optional[str],
        params: Any,
    ) -> Dict[str, Any]:
        """
        Surface weighted memory context for the current turn without changing tool APIs.
        Uses input-side context (method/tool/argument keys + short string values).
        """
        memory_tool = self.tool_modules.get("memory_tool")
        if not memory_tool:
            return {"status": "unavailable", "reason": "memory_tool_unavailable"}

        context_chunks: List[str] = [f"method={method or 'unknown'}"]
        tool_name: Optional[str] = None

        if isinstance(params, dict):
            tool_name = params.get("name") if isinstance(params.get("name"), str) else None
            if tool_name:
                context_chunks.append(f"tool={tool_name}")
            arguments = params.get("arguments")
            if isinstance(arguments, dict):
                arg_keys = sorted([k for k in arguments.keys() if isinstance(k, str)])
                if arg_keys:
                    context_chunks.append(f"arg_keys={','.join(arg_keys[:25])}")
                for key in arg_keys[:10]:
                    value = arguments.get(key)
                    if isinstance(value, str):
                        compact = value.strip().replace("\n", " ")
                        if compact:
                            context_chunks.append(f"{key}={compact[:120]}")

        context_text = " | ".join(context_chunks)[:1500]
        try:
            memory_result: Any = None
            if hasattr(memory_tool, "surface_context"):
                memory_result = memory_tool.surface_context(context_text, max_results=3)
            elif hasattr(memory_tool, "memory_surface_context"):
                memory_result = memory_tool.memory_surface_context(
                    context_text=context_text, max_results=3
                )
            else:
                return {"status": "unavailable", "reason": "surface_method_missing"}

            conversation_context = self._query_conversation_context(
                context_text=context_text,
                max_results=3,
            )
            combined = {
                "memory_context": memory_result,
                "conversation_context": conversation_context,
            }
            summary = self._summarize_value(combined)
            self._append_event(
                event_type="memory_context_surfaced",
                source="mcp_server",
                turn_id=turn_id,
                payload={
                    "method": method,
                    "tool_name": tool_name,
                    "context_text": context_text,
                    "result_summary": summary,
                    "conversation_context_present": bool(conversation_context),
                    "status": "success",
                },
                importance_hint=0.45,
            )
            return {
                "status": "success",
                "context_summary": summary,
                "memory_context": memory_result,
                "conversation_context": conversation_context,
            }
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="surface_turn_memory_context",
                error=exc,
                context={
                    "method": method,
                    "tool_name": tool_name,
                    "context_text": context_text,
                },
                severity="error",
                turn_id=turn_id,
            )
            self._append_event(
                event_type="memory_context_surfaced",
                source="mcp_server",
                turn_id=turn_id,
                payload={
                    "method": method,
                    "tool_name": tool_name,
                    "context_text": context_text,
                    "status": "failed",
                    "reason": str(exc),
                },
                importance_hint=0.35,
            )
            return {"status": "failed", "reason": str(exc)}

    def _persist_tool_exchange_memory(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result_payload: Any,
        success: bool,
        latency_seconds: float,
        turn_id: Optional[str] = None,
        request_id: Optional[Any] = None,
        memory_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Persist one MCP tool exchange as durable memory.
        Designed as a non-blocking continuity substrate for every tool call.
        """
        if not self._ambient_memory_exchange_enabled:
            return {"status": "disabled", "reason": "ambient_memory_exchange_off"}

        memory_tool = self.tool_modules.get("memory_tool")
        if memory_tool is None or not hasattr(memory_tool, "store"):
            return {"status": "unavailable", "reason": "memory_store_unavailable"}

        now = time.time()
        normalized_tool = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(tool_name or "unknown"))
        memory_key = (
            f"mcp_exchange::{self.session_id}::{int(now * 1000)}::{normalized_tool[:80]}"
        )
        memory_context_summary = ""
        if isinstance(memory_context, dict):
            memory_context_summary = str(memory_context.get("context_summary", ""))[:500]

        exchange_record = {
            "ts": now,
            "session_id": self.session_id,
            "turn_id": turn_id or "",
            "request_id": request_id,
            "tool_name": str(tool_name or ""),
            "success": bool(success),
            "latency_ms": round(max(0.0, float(latency_seconds)) * 1000.0, 3),
            "codex_thread_id": self._latest_codex_thread_id or "",
            "arguments_summary": self._summarize_value(arguments, max_chars=1200),
            "result_summary": self._summarize_value(result_payload, max_chars=2000),
            "memory_context_summary": memory_context_summary,
            "artifacts": self._extract_artifacts(
                arguments if isinstance(arguments, dict) else {},
                result_payload if isinstance(result_payload, dict) else {},
            ),
        }
        memory_value = json.dumps(exchange_record, ensure_ascii=False)
        importance = 0.82 if not success else 0.58
        tags = [
            "auto",
            "mcp_exchange",
            f"tool:{normalized_tool[:64]}",
            "status:error" if not success else "status:success",
        ]

        store_response = memory_tool.store(
            key=memory_key,
            value=memory_value,
            category="context",
            importance=importance,
            tags=tags,
        )

        analyzed = False
        memory_interconnect = self.tool_modules.get("memory_interconnect")
        if memory_interconnect is not None and hasattr(
            memory_interconnect, "analyze_memory_entry"
        ):
            try:
                memory_interconnect.analyze_memory_entry(
                    key=memory_key,
                    value=memory_value,
                    source="mcp_exchange",
                )
                analyzed = True
            except Exception as analyze_exc:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="persist_tool_exchange_memory_analyze",
                    error=analyze_exc,
                    context={"tool_name": str(tool_name or ""), "memory_key": memory_key},
                    severity="warning",
                    turn_id=turn_id,
                )

        linked = False
        session_tool = self.tool_modules.get("session_manager_tool")
        if session_tool is not None and hasattr(session_tool, "bb7_link_memory_to_session"):
            try:
                link_result = session_tool.bb7_link_memory_to_session(memory_key=memory_key)
                if isinstance(link_result, str) and "Linked memory key" in link_result:
                    linked = True
            except Exception as link_exc:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="persist_tool_exchange_memory_link",
                    error=link_exc,
                    context={"tool_name": str(tool_name or ""), "memory_key": memory_key},
                    severity="warning",
                    turn_id=turn_id,
                )

        self._append_event(
            event_type="memory_exchange_persisted",
            source="mcp_server",
            turn_id=turn_id,
            payload={
                "tool_name": str(tool_name or ""),
                "memory_key": memory_key,
                "success": bool(success),
                "latency_ms": exchange_record["latency_ms"],
                "analyzed": analyzed,
                "linked_to_session": linked,
                "store_response_summary": self._summarize_value(store_response, max_chars=300),
            },
            importance_hint=0.62,
        )
        return {
            "status": "ok",
            "memory_key": memory_key,
            "analyzed": analyzed,
            "linked_to_session": linked,
        }

    def _schedule_tool_exchange_memory_persist(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result_payload: Any,
        success: bool,
        latency_seconds: float,
        turn_id: Optional[str] = None,
        request_id: Optional[Any] = None,
        memory_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Schedule asynchronous persistence of one tool exchange into memory."""
        if not self._ambient_memory_exchange_enabled:
            return

        def _worker() -> None:
            try:
                self._persist_tool_exchange_memory(
                    tool_name=tool_name,
                    arguments=arguments if isinstance(arguments, dict) else {},
                    result_payload=result_payload,
                    success=success,
                    latency_seconds=latency_seconds,
                    turn_id=turn_id,
                    request_id=request_id,
                    memory_context=memory_context,
                )
            except Exception as persist_exc:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="schedule_tool_exchange_memory_persist",
                    error=persist_exc,
                    context={"tool_name": str(tool_name or "")},
                    severity="error",
                    turn_id=turn_id,
                )

        threading.Thread(target=_worker, daemon=True).start()

    def _compose_lisan_context_message(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        result_payload: Any = None,
    ) -> str:
        """Build a compact intent/context string for lisan-aware augmentation."""
        parts: List[str] = [f"tool={str(tool_name or '').strip()}"]
        if isinstance(arguments, dict):
            for key in sorted(arguments.keys()):
                value = arguments.get(key)
                if isinstance(value, (str, int, float, bool)):
                    parts.append(f"{key}={value}")
                elif isinstance(value, (list, dict)):
                    parts.append(f"{key}={self._summarize_value(value, max_chars=160)}")
        if result_payload is not None:
            parts.append(f"result={self._summarize_value(result_payload, max_chars=400)}")
        return " | ".join(part for part in parts if part)[:1600]

    def _build_sovereign_meta(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result_payload: Any,
        turn_memory_context: Optional[Dict[str, Any]] = None,
        turn_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Augment non-control-plane tool responses with lisan/exo continuity context."""
        if not isinstance(tool_name, str) or tool_name.startswith(("bb7_exo_", "bb7_lisan_")):
            return {}

        exo = self.tool_modules.get("exoskeleton_tool")
        if exo is None:
            return {}

        context_message = self._compose_lisan_context_message(
            tool_name=tool_name,
            arguments=arguments if isinstance(arguments, dict) else {},
            result_payload=result_payload,
        )
        sovereign_meta: Dict[str, Any] = {
            "current_context": {
                "tool_name": tool_name,
                "turn_id": turn_id or "",
                "session_id": self.session_id,
                "argument_keys": sorted(arguments.keys()) if isinstance(arguments, dict) else [],
            }
        }

        if isinstance(turn_memory_context, dict) and turn_memory_context:
            sovereign_meta["memory_context"] = {
                "status": turn_memory_context.get("status", ""),
                "summary": turn_memory_context.get("context_summary", ""),
            }

        if hasattr(exo, "bb7_lisan_intend"):
            try:
                sovereign_meta["lisan_intent"] = exo.bb7_lisan_intend(
                    user_message=context_message,
                    verbosity="normal",
                )
            except Exception as exc:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="build_sovereign_meta_lisan_intend",
                    error=exc,
                    context={"tool_name": tool_name},
                    severity="warning",
                    turn_id=turn_id,
                )

        if hasattr(exo, "bb7_exo_suggest_next"):
            try:
                sovereign_meta["suggested_next"] = exo.bb7_exo_suggest_next(
                    current_tool=tool_name,
                    intent=context_message,
                )
            except Exception as exc:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="build_sovereign_meta_suggest_next",
                    error=exc,
                    context={"tool_name": tool_name},
                    severity="warning",
                    turn_id=turn_id,
                )

        return sovereign_meta

    def _auto_reflect_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        success: bool,
        turn_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update exoskeleton priors even when the client skips explicit bb7_exo_reflect."""
        if not isinstance(tool_name, str) or tool_name.startswith(("bb7_exo_", "bb7_lisan_")):
            return
        exo = self.tool_modules.get("exoskeleton_tool")
        if exo is None or not hasattr(exo, "bb7_exo_reflect"):
            return

        ambient_plan_id = f"ambient::{turn_id or int(time.time() * 1000)}"
        intent_blob = self._compose_lisan_context_message(
            tool_name=tool_name,
            arguments=arguments if isinstance(arguments, dict) else {},
        )
        try:
            exo.bb7_exo_reflect(
                plan_id=ambient_plan_id,
                tools_used=[tool_name],
                success=bool(success),
                error=error,
                intent=intent_blob,
                recovery_strategy=None if success else "inspect_suggested_next",
            )
        except Exception as exc:
            self._record_internal_failure(
                component="mcp_server",
                operation="auto_reflect_tool_call",
                error=exc,
                context={"tool_name": tool_name, "success": bool(success)},
                severity="warning",
                turn_id=turn_id,
            )

    def _log_to_distillation_db(
        self,
        trajectory_id: str,
        session_id: str,
        source_plane: str,
        trajectory: List[Dict],
        telemetry: Dict,
    ) -> None:
        """Log trajectory to SQLite3 distillation database."""
        if self._distillation_conn is None:
            return

        import json

        try:
            self._distillation_conn.execute(
                """
                INSERT INTO trajectories (trajectory_id, timestamp, session_id, source_plane, 
                    trajectory_data, telemetry_data, quality_status)
                VALUES (?, ?, ?, ?, ?, ?, 'unreviewed')
            """,
                (
                    trajectory_id,
                    time.time(),
                    session_id,
                    source_plane,
                    json.dumps(trajectory),
                    json.dumps(telemetry),
                ),
            )
            self._distillation_conn.commit()
        except Exception as e:
            self._record_internal_failure(
                component="mcp_server",
                operation="log_to_distillation_db",
                error=e,
                context={
                    "trajectory_id": trajectory_id,
                    "source_plane": source_plane,
                    "session_id": session_id,
                },
                severity="error",
            )

    def _log_tool_usage(
        self,
        tool_name: str,
        success: bool,
        latency: float,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
        arguments: Optional[Dict] = None,
    ) -> None:
        """Log individual tool usage to SQLite3 for RLHF training."""
        if self._distillation_conn is None:
            return

        import json

        try:
            self._distillation_conn.execute(
                """
                INSERT INTO tool_usage (timestamp, tool_name, success, latency_seconds, 
                    error_message, session_id, arguments)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    time.time(),
                    tool_name,
                    1 if success else 0,
                    latency,
                    error,
                    session_id,
                    json.dumps(arguments) if arguments else None,
                ),
            )
            self._distillation_conn.commit()

            # Track unused tools - remove from unused if called
            if tool_name in self.tool_health.get("unused_tools", {}):
                del self.tool_health["unused_tools"][tool_name]

        except Exception as e:
            self._record_internal_failure(
                component="mcp_server",
                operation="log_tool_usage",
                error=e,
                context={"tool_name": tool_name, "session_id": session_id or ""},
                severity="error",
            )

    def _log_conversation_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List] = None,
        tool_call_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Log conversation message for RLHF distillation."""
        if self._distillation_conn is None:
            return

        import json

        try:
            self._distillation_conn.execute(
                """
                INSERT INTO conversation_history (timestamp, session_id, role, content, 
                    tool_calls, tool_call_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    float(timestamp if timestamp is not None else time.time()),
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    tool_call_id,
                ),
            )
            self._distillation_conn.commit()
            self.conversation_history.append(
                {
                    "timestamp": float(timestamp if timestamp is not None else time.time()),
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "tool_calls": tool_calls,
                    "tool_call_id": tool_call_id,
                }
            )
        except Exception as e:
            self._record_internal_failure(
                component="mcp_server",
                operation="log_conversation_message",
                error=e,
                context={"session_id": session_id, "role": role},
                severity="error",
            )

    def _init_dispatcher(self):
        """Initialize the JSON-RPC dispatcher"""
        self.dispatcher = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_list_tools,
            "tools/call": self.handle_call_tool,
            "logging/setLevel": self.handle_set_log_level,
        }

    @staticmethod
    def _normalize_id(req_id: Any) -> Union[str, int]:
        """
        Normalize inbound JSON-RPC ids to values accepted by strict clients.
        Falls back to 0 when missing/invalid to avoid null ids that some clients reject.
        """
        if isinstance(req_id, (str, int)):
            return req_id
        return 0

    def _display_projection_enabled(self) -> bool:
        """Return whether human-facing display projection is enabled.

        This is intentionally a display-layer flag only. It does not alter raw
        tool results before telemetry, memory exchange, Q-table observation,
        or distillation/RFT capture paths.
        """
        raw_value = str(os.environ.get("SOVEREIGN_DISPLAY_PROJECTION", "1")).strip().lower()
        return raw_value not in {"0", "false", "no", "off", "raw"}

    def _display_projection_max_chars(self) -> int:
        try:
            return max(
                1200,
                min(
                    20000,
                    int(os.environ.get("SOVEREIGN_DISPLAY_PROJECTION_MAX_CHARS", "5000")),
                ),
            )
        except (TypeError, ValueError):
            return 5000

    def _display_raw_fingerprint(self, payload: Any) -> Dict[str, Any]:
        try:
            raw_text = json.dumps(payload, sort_keys=True, default=str)
        except TypeError:
            raw_text = str(payload)
        return {
            "raw_kind": type(payload).__name__,
            "raw_size_chars": len(raw_text),
            "raw_sha256_16": hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:16],
        }

    def _stringify_display_scalar(self, value: Any, max_chars: int = 180) -> str:
        if isinstance(value, float):
            rendered = f"{value:.6g}"
        elif isinstance(value, (dict, list, tuple, set)):
            rendered = self._summarize_value(value, max_chars=max_chars)
        else:
            rendered = str(value)
        rendered = rendered.replace("\n", " ").strip()
        return rendered[: max_chars - 1] + "…" if len(rendered) > max_chars else rendered

    def _append_display_fact(
        self, facts: List[str], label: str, value: Any, *, max_chars: int = 180
    ) -> None:
        if value is None:
            return
        facts.append(f"{label}={self._stringify_display_scalar(value, max_chars=max_chars)}")

    def _project_bootstrap_display(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        warnings: List[str] = []
        next_actions: List[str] = []
        self._append_display_fact(facts, "indexed_tools", payload.get("indexed_tools"))
        self._append_display_fact(facts, "category_count", payload.get("category_count"))
        self._append_display_fact(facts, "exo_tools_registered", payload.get("exo_tools_registered"))
        self._append_display_fact(facts, "live_provider_attached", payload.get("live_provider_attached"))
        manifest_refresh = payload.get("manifest_refresh")
        if isinstance(manifest_refresh, dict):
            self._append_display_fact(facts, "manifest_reloaded", manifest_refresh.get("reloaded"))
            self._append_display_fact(facts, "manifest_tools", manifest_refresh.get("indexed_tools"))
        catalog_sync = payload.get("catalog_sync")
        if isinstance(catalog_sync, dict):
            facts.append(
                "catalog_sync="
                f"+{catalog_sync.get('added', 0)} "
                f"~{catalog_sync.get('updated', 0)} "
                f"-{catalog_sync.get('removed', 0)}"
            )
        failed_health = payload.get("healthcheck_failures") or payload.get("failed")
        if failed_health:
            warnings.append(f"health warnings present: {self._stringify_display_scalar(failed_health)}")
        next_actions.append("Skip repeated bootstrap unless manifest/runtime drift is suspected.")
        next_actions.append("Proceed with route/plan/execute/reflect for the actual task.")
        return facts, warnings, next_actions

    def _project_lisan_recall_display(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        warnings: List[str] = []
        next_actions: List[str] = []
        self._append_display_fact(facts, "session_id", payload.get("session_id"))
        memories = payload.get("memories")
        if isinstance(memories, list):
            self._append_display_fact(facts, "memory_blocks", len(memories))
        active_plans = payload.get("active_plans")
        if isinstance(active_plans, list):
            self._append_display_fact(facts, "active_plans", len(active_plans))
        activity = payload.get("cross_ai_activity")
        if isinstance(activity, list):
            self._append_display_fact(facts, "recent_activity_items", len(activity))

        context_blob = str(payload.get("context_blob", ""))
        top_memories: List[str] = []
        for line in context_blob.splitlines():
            stripped = line.strip()
            if re.match(r"^\d+\.\s+\[", stripped):
                top_memories.append(stripped)
            if len(top_memories) >= 5:
                break
        for idx, memory_line in enumerate(top_memories, start=1):
            facts.append(f"memory_{idx}={memory_line[:220]}")
        if context_blob and not top_memories:
            facts.append(f"context_blob_summary={self._summarize_value(context_blob, max_chars=300)}")
        next_actions.append("Use surfaced memories as routing evidence; inspect current repo state before edits.")
        next_actions.append("Ask for raw recall only if exact memory text is needed.")
        return facts, warnings, next_actions

    def _project_exo_briefing_display(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        warnings: List[str] = []
        next_actions: List[str] = []
        narrative = str(payload.get("narrative", ""))
        for line in narrative.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                facts.append(f"section={stripped[3:180]}")
            elif stripped.startswith("> "):
                facts.append(f"intent={stripped[2:220]}")
            elif stripped.startswith("- ") and len(next_actions) < 5:
                next_actions.append(stripped[2:220])
            if len(facts) >= 6 and len(next_actions) >= 3:
                break
        if not facts and narrative:
            facts.append(f"narrative_summary={self._summarize_value(narrative, max_chars=500)}")
        next_actions.append("Treat briefing as routing guidance, not raw execution evidence.")
        return facts, warnings, next_actions

    def _project_tool_health_display(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        warnings: List[str] = []
        next_actions: List[str] = []
        self._append_display_fact(facts, "total_tools", payload.get("total_tools"))
        registered_tools = payload.get("registered_tools")
        if isinstance(registered_tools, list):
            self._append_display_fact(facts, "registered_tools", len(registered_tools))
            facts.append(
                "required_surfaces="
                f"bridge:{'bb7_muadib_mentat_bridge' in registered_tools} "
                f"refresh:{'bb7_tool_refresh_module' in registered_tools}"
            )
        loaded_modules = payload.get("loaded_modules")
        if isinstance(loaded_modules, list):
            self._append_display_fact(facts, "loaded_modules", len(loaded_modules))
            facts.append(f"meta_loaded={'meta_intelligence_engine' in loaded_modules}")
        runtime_identity = payload.get("runtime_identity")
        if isinstance(runtime_identity, dict):
            for label, key in (
                ("pid", "pid"),
                ("session_id", "session_id"),
                ("transport", "transport"),
                ("data_dir", "data_dir"),
                ("source_sha256_16", "source_sha256_16"),
            ):
                self._append_display_fact(facts, label, runtime_identity.get(key))
        else:
            warnings.append("runtime_identity missing; live source parity is not proven.")
        if payload.get("status") != "healthy":
            warnings.append(f"health status is {payload.get('status')!r}")
        next_actions.append("Use registered_tools + runtime_identity for live/source parity decisions.")
        return facts, warnings, next_actions

    def _project_muadib_bridge_display(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        warnings: List[str] = []
        next_actions: List[str] = []
        contract = payload.get("contract")
        if isinstance(contract, dict):
            for key in (
                "one_cognition_data_plane",
                "one_server_one_plane",
                "mcp_server_is_intelligence",
                "gateway_process_is_cognition_plane",
                "mutates_mcp_output_adapter",
            ):
                self._append_display_fact(facts, key, contract.get(key))
        gateway = payload.get("gateway")
        if isinstance(gateway, dict):
            identity = gateway.get("runtime_identity")
            if isinstance(identity, dict):
                self._append_display_fact(facts, "gateway_pid", identity.get("pid"))
                self._append_display_fact(facts, "gateway_session", identity.get("session_id"))
                self._append_display_fact(facts, "source_sha256_16", identity.get("source_sha256_16"))
        source_calls = payload.get("source_calls")
        if isinstance(source_calls, dict):
            checkpoint = (
                source_calls.get("muadib_checkpoint_status", {})
                .get("result", {})
                .get("tokenizer", {})
                .get("meta", {})
            )
            if isinstance(checkpoint, dict):
                self._append_display_fact(facts, "active_checkpoint", checkpoint.get("active_checkpoint"))
                self._append_display_fact(facts, "checkpoint_format", checkpoint.get("format"))
                self._append_display_fact(facts, "checkpoint_bytes", checkpoint.get("bytes"))
            exo = source_calls.get("exoskeleton_state", {}).get("result", {})
            if isinstance(exo, dict):
                self._append_display_fact(facts, "exoskeleton_indexed_tools", exo.get("indexed_tools"))
            advanced = (
                source_calls.get("muadib_advanced_features", {})
                .get("result", {})
                .get("bridge_health", {})
            )
            if isinstance(advanced, dict):
                self._append_display_fact(facts, "advanced_bridge_active", advanced.get("active"))
        recommended = payload.get("recommended_next")
        if isinstance(recommended, list):
            next_actions.extend(str(item)[:220] for item in recommended[:5])
        if not next_actions:
            next_actions.append("Use this as a read-only one-plane snapshot, not a mutation surface.")
        return facts, warnings, next_actions

    def _project_generic_display(
        self, payload: Any
    ) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        warnings: List[str] = []
        next_actions: List[str] = []
        if isinstance(payload, dict):
            for key in ("status", "success", "ok", "mode", "operation", "timestamp"):
                if key in payload:
                    self._append_display_fact(facts, key, payload.get(key))
            facts.append("top_level_keys=" + ", ".join(str(key) for key in list(payload.keys())[:12]))
            if len(payload) > 12:
                facts.append(f"omitted_top_level_keys={len(payload) - 12}")
            for key in ("error", "warning", "warnings", "failed", "failures"):
                if payload.get(key):
                    warnings.append(f"{key}={self._stringify_display_scalar(payload.get(key), max_chars=240)}")
            for key in ("recommended_next", "suggested_next", "next_actions"):
                value = payload.get(key)
                if isinstance(value, list):
                    next_actions.extend(str(item)[:220] for item in value[:5])
                elif value:
                    next_actions.append(self._stringify_display_scalar(value, max_chars=240))
        elif isinstance(payload, list):
            facts.append(f"list_items={len(payload)}")
            for idx, item in enumerate(payload[:5], start=1):
                facts.append(f"item_{idx}={self._summarize_value(item, max_chars=220)}")
            if len(payload) > 5:
                facts.append(f"omitted_items={len(payload) - 5}")
        else:
            facts.append(self._stringify_display_scalar(payload, max_chars=500))
        return facts, warnings, next_actions

    def _project_tool_result_for_display(
        self, payload: Any, *, tool_name: str = "", is_error: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        fingerprint = self._display_raw_fingerprint(payload)
        status = "ERROR" if is_error else "OK"
        if isinstance(payload, dict):
            for key in ("status", "success", "ok"):
                if key in payload:
                    value = payload.get(key)
                    if isinstance(value, bool):
                        status = "OK" if value else "FAIL"
                    else:
                        status = self._stringify_display_scalar(value, max_chars=40).upper()
                    break

        if tool_name == "bb7_exo_bootstrap" and isinstance(payload, dict):
            facts, warnings, next_actions = self._project_bootstrap_display(payload)
        elif tool_name == "bb7_lisan_recall" and isinstance(payload, dict):
            facts, warnings, next_actions = self._project_lisan_recall_display(payload)
        elif tool_name == "bb7_exo_briefing" and isinstance(payload, dict):
            facts, warnings, next_actions = self._project_exo_briefing_display(payload)
        elif tool_name == "bb7_tool_health_report" and isinstance(payload, dict):
            facts, warnings, next_actions = self._project_tool_health_display(payload)
        elif tool_name == "bb7_muadib_mentat_bridge" and isinstance(payload, dict):
            facts, warnings, next_actions = self._project_muadib_bridge_display(payload)
        else:
            facts, warnings, next_actions = self._project_generic_display(payload)

        title = tool_name or "tool_result"
        lines = [
            f"### {title}: {status}",
            "",
            "Key facts:",
        ]
        lines.extend(f"- {fact}" for fact in (facts or ["no structured key facts extracted"]))
        if warnings:
            lines.extend(["", "Warnings:"])
            lines.extend(f"- {warning}" for warning in warnings)
        if next_actions:
            lines.extend(["", "Next:"])
            lines.extend(f"- {action}" for action in next_actions[:8])
        lines.extend(
            [
                "",
                "Raw:",
                "- hidden from display",
                "- preserved before projection for telemetry, memory exchange, Q-play, and RFT/distillation",
                f"- raw_kind={fingerprint['raw_kind']} raw_size_chars={fingerprint['raw_size_chars']} raw_sha256_16={fingerprint['raw_sha256_16']}",
                "- set SOVEREIGN_DISPLAY_PROJECTION=raw to display canonical raw JSON text",
            ]
        )
        text = "\n".join(lines)
        max_chars = self._display_projection_max_chars()
        truncated = False
        if len(text) > max_chars:
            truncated = True
            text = (
                text[: max_chars - 180].rstrip()
                + "\n\n… display projection truncated; raw payload remains preserved in substrate."
            )
        projection_meta: Dict[str, Any] = {
            "display_projection": {
                "enabled": True,
                "tool_name": tool_name,
                "truncated": truncated,
                "projection_for_display_only": True,
                "raw_payload_in_content": False,
                "raw_preserved_before_projection": True,
                "not_for_qtable": True,
                "not_for_observations": True,
                "not_for_distillation": True,
                "not_for_rft": True,
                **fingerprint,
            }
        }
        return text, projection_meta

    def _file_surface_tool_names(self) -> set[str]:
        return {
            "bb7_read_file",
            "bb7_write_file",
            "bb7_append_file",
            "bb7_copy_file",
            "bb7_move_file",
            "bb7_delete_file",
        }

    def _file_surface_inline_max_chars(self) -> int:
        try:
            return max(
                1200,
                min(
                    50000,
                    int(os.environ.get("SOVEREIGN_FILE_SURFACE_INLINE_MAX_CHARS", "24000")),
                ),
            )
        except (TypeError, ValueError):
            return 24000

    def _extract_file_surface_path(self, tool_name: str, arguments: Optional[Dict[str, Any]]) -> str:
        arguments = arguments if isinstance(arguments, dict) else {}
        if tool_name in {"bb7_copy_file", "bb7_move_file"}:
            source = arguments.get("source", "")
            destination = arguments.get("destination", "")
            return f"{source} -> {destination}" if source or destination else "unknown"
        return str(arguments.get("path") or arguments.get("file_path") or "unknown")

    def _render_argument_delta_preview(
        self, arguments: Optional[Dict[str, Any]], *, mode: str
    ) -> List[str]:
        arguments = arguments if isinstance(arguments, dict) else {}
        content = arguments.get("content")
        if content is None:
            return ["delta_preview=not_available"]
        lines = str(content).splitlines()
        if not lines:
            return ["delta_preview=empty_content"]
        label = "appended_lines" if mode == "append" else "written_lines"
        preview_lines = lines[:3]
        if len(lines) > 6:
            preview_lines += ["…"]
            preview_lines += lines[-3:]
        elif len(lines) > 3:
            preview_lines += lines[3:]
        preview = "\n".join(preview_lines)
        return [
            f"{label}={len(lines):,}",
            "",
            "Delta preview:",
            "```text",
            preview,
            "```",
        ]

    def _project_file_surface_string_for_display(
        self,
        payload: str,
        *,
        tool_name: str = "",
        arguments: Optional[Dict[str, Any]] = None,
        is_error: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        fingerprint = self._display_raw_fingerprint(payload)
        target = self._extract_file_surface_path(tool_name, arguments)
        status = "ERROR" if is_error else "OK"
        raw_chars = len(payload)

        if tool_name == "bb7_read_file":
            if (
                raw_chars <= self._file_surface_inline_max_chars()
                or payload.startswith("### [TOOL VERIFICATION]:")
            ):
                text = payload
                suppressed = False
            else:
                line_count = payload.count("\n") + (1 if payload else 0)
                text = "\n".join(
                    [
                        "### [TOOL VERIFICATION]: FILE_READ_ISOLATED",
                        f"* **Target:** `{target}`",
                        f"* **Returned Raw Chars:** {raw_chars:,}",
                        f"* **Returned Raw Lines:** {line_count:,}",
                        "* **Governor:** raw file echo suppressed at MCP display seam.",
                        "* **Recovery:** request `start_line`/`end_line`, `semantic_target`, or set `allow_large_raw=True` for an explicit full read.",
                    ]
                )
                suppressed = True
        else:
            if payload.startswith("### [TOOL VERIFICATION]:"):
                text = payload
                suppressed = False
                projection_meta: Dict[str, Any] = {
                    "display_projection": {
                        "enabled": True,
                        "tool_name": tool_name,
                        "file_surface_token_isolation": True,
                        "verification_manifest_passthrough": True,
                        "raw_payload_in_content": True,
                        "raw_preserved_before_projection": True,
                        "projection_for_display_only": True,
                        "not_for_qtable": True,
                        "not_for_observations": True,
                        "not_for_distillation": True,
                        "not_for_rft": True,
                        **fingerprint,
                    }
                }
                return text, projection_meta
            operation = tool_name.replace("bb7_", "").replace("_", " ").upper() or "FILE OPERATION"
            success_tag = (
                "FILE_PATCH_SUCCESS"
                if tool_name in {"bb7_write_file", "bb7_append_file"}
                else "FILE_OPERATION_SUCCESS"
            )
            lines = [
                f"### [TOOL VERIFICATION]: {success_tag if not is_error else 'FILE_OPERATION_ERROR'}",
                f"* **Operation:** {operation}",
                f"* **Target:** `{target}`",
                f"* **Status:** {status}",
                f"* **Raw Tool Message Chars:** {raw_chars:,}",
                "* **Liveness Check:** not_run_by_tool; run py_compile/pytest/target smoke validation when code behavior matters.",
            ]
            if tool_name == "bb7_write_file":
                lines.extend(self._render_argument_delta_preview(arguments, mode="write"))
            elif tool_name == "bb7_append_file":
                lines.extend(self._render_argument_delta_preview(arguments, mode="append"))
            text = "\n".join(lines)
            suppressed = True

        projection_meta: Dict[str, Any] = {
            "display_projection": {
                "enabled": True,
                "tool_name": tool_name,
                "file_surface_token_isolation": True,
                "raw_payload_in_content": not suppressed,
                "raw_preserved_before_projection": True,
                "projection_for_display_only": True,
                "not_for_qtable": True,
                "not_for_observations": True,
                "not_for_distillation": True,
                "not_for_rft": True,
                **fingerprint,
            }
        }
        return text, projection_meta

    def _format_tool_result(
        self,
        payload: Any,
        is_error: bool = False,
        tool_name: str = "",
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Adapt arbitrary tool return values into MCP-compliant CallToolResult shape:
        { "content": [ { "type": "text", "text": "<data>" } ], "isError": bool }
        """
        content_blocks: List[Dict[str, Any]] = []
        meta: Dict[str, Any] = {}

        # If payload already contains MCP-style content, honor it.
        if (
            isinstance(payload, dict)
            and "content" in payload
            and isinstance(payload["content"], list)
        ):
            content_blocks = payload["content"]
            if "meta" in payload and isinstance(payload["meta"], dict):
                meta = payload["meta"]
            is_error = is_error or bool(payload.get("isError"))
        else:
            # Fallback: serialize payload to text for client display.
            if isinstance(payload, (dict, list)):
                if self._display_projection_enabled():
                    try:
                        text, projection_meta = self._project_tool_result_for_display(
                            payload,
                            tool_name=tool_name,
                            is_error=is_error,
                        )
                        meta.update(projection_meta)
                    except Exception as projection_error:
                        self._record_internal_failure(
                            component="mcp_server",
                            operation="display_projection",
                            error=projection_error,
                            context={"tool_name": tool_name},
                            severity="error",
                        )
                        text = (
                            "### display_projection: FAILED\n\n"
                            f"- tool_name={tool_name or 'unknown'}\n"
                            f"- error={projection_error}\n"
                            "- fail_loud=true\n"
                            "- raw JSON fallback follows; substrate raw payload was already preserved before display formatting.\n\n"
                            + json.dumps(payload, indent=2)
                        )
                        meta.setdefault("display_projection", {})[
                            "projection_failed"
                        ] = True
                else:
                    text = json.dumps(payload, indent=2)
            elif (
                isinstance(payload, str)
                and tool_name in self._file_surface_tool_names()
                and self._display_projection_enabled()
            ):
                try:
                    text, projection_meta = self._project_file_surface_string_for_display(
                        payload,
                        tool_name=tool_name,
                        arguments=arguments,
                        is_error=is_error,
                    )
                    meta.update(projection_meta)
                except Exception as projection_error:
                    self._record_internal_failure(
                        component="mcp_server",
                        operation="file_surface_display_projection",
                        error=projection_error,
                        context={"tool_name": tool_name},
                        severity="error",
                    )
                    text = (
                        "### file_surface_display_projection: FAILED\n\n"
                        f"- tool_name={tool_name or 'unknown'}\n"
                        f"- error={projection_error}\n"
                        "- fail_loud=true\n"
                        "- raw string fallback follows; substrate raw payload was already preserved before display formatting.\n\n"
                        + payload
                    )
                    meta.setdefault("display_projection", {})["projection_failed"] = True
            else:
                text = str(payload)
            content_blocks = [{"type": "text", "text": text}]

        result: Dict[str, Any] = {"content": content_blocks}
        if meta:
            result["meta"] = meta
        if is_error:
            result["isError"] = True
        return result

    def _async_loop_worker(self) -> None:
        """Background thread target that hosts the shared async event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._async_loop = loop
        self._async_loop_ready.set()

        try:
            loop.run_forever()
        finally:
            try:
                pending = asyncio.all_tasks(loop=loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                loop.run_until_complete(loop.shutdown_asyncgens())
                if hasattr(loop, "shutdown_default_executor"):
                    loop.run_until_complete(loop.shutdown_default_executor())
            except Exception as loop_shutdown_error:
                self.logger.debug(
                    "Async loop shutdown cleanup error: %s", loop_shutdown_error
                )
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    def _ensure_async_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure a long-lived background event loop is available for coroutine execution."""
        with self._async_loop_lock:
            loop_is_usable = (
                self._async_loop is not None
                and not self._async_loop.is_closed()
                and self._async_loop_thread is not None
                and self._async_loop_thread.is_alive()
            )
            if loop_is_usable:
                return self._async_loop  # type: ignore[return-value]

            self._async_loop_ready.clear()
            self._async_loop = None
            self._async_loop_thread = threading.Thread(
                target=self._async_loop_worker,
                name="MCPServerAsyncLoop",
                daemon=True,
            )
            self._async_loop_thread.start()

        if not self._async_loop_ready.wait(timeout=5):
            raise RuntimeError("Failed to start MCP async execution loop")
        if self._async_loop is None or self._async_loop.is_closed():
            raise RuntimeError("MCP async execution loop is unavailable")
        return self._async_loop

    def _stop_async_loop(self) -> None:
        """Stop the shared background async event loop."""
        with self._async_loop_lock:
            loop = self._async_loop
            loop_thread = self._async_loop_thread
            if loop is None or loop_thread is None:
                return
            if not loop.is_closed():
                loop.call_soon_threadsafe(loop.stop)

        loop_thread.join(timeout=5)
        if loop_thread.is_alive():
            self.logger.warning("Async loop thread did not stop cleanly within timeout")

        with self._async_loop_lock:
            self._async_loop = None
            self._async_loop_thread = None
            self._async_loop_ready.clear()

    def _run_coroutine_sync(self, coroutine_obj: Any) -> Any:
        """
        Execute a coroutine from sync code using the shared async loop thread.
        This avoids per-call event-loop churn that can invalidate cached async resources.
        """
        if not inspect.isawaitable(coroutine_obj):
            return coroutine_obj

        loop = self._ensure_async_loop()
        if (
            self._async_loop_thread
            and threading.current_thread() is self._async_loop_thread
        ):
            raise RuntimeError(
                "Cannot synchronously wait for coroutine from async loop thread"
            )

        future = asyncio.run_coroutine_threadsafe(coroutine_obj, loop)
        return future.result()

    def _invoke_tool_callable(
        self,
        tool_callable: Callable[..., Any],
        arguments: Dict[str, Any],
        prefer_kwargs: bool = True,
    ) -> Any:
        """
        Invoke a tool callable with compatibility for both invocation styles:
        - kwargs style: fn(**arguments)
        - dict style:   fn(arguments)
        Also supports no-arg callables and awaitable return values.
        """
        if not isinstance(arguments, dict):
            raise TypeError(
                f"Tool arguments must be an object/dict, got: {type(arguments)}"
            )

        call_strategies: List[Tuple[str, Callable[[], Any]]] = []
        if not arguments:
            call_strategies.append(("no_args", lambda: tool_callable()))

        if prefer_kwargs:
            call_strategies.extend(
                [
                    ("kwargs", lambda: tool_callable(**arguments)),
                    ("dict", lambda: tool_callable(arguments)),
                ]
            )
        else:
            call_strategies.extend(
                [
                    ("dict", lambda: tool_callable(arguments)),
                    ("kwargs", lambda: tool_callable(**arguments)),
                ]
            )

        last_type_error: Optional[TypeError] = None

        for strategy_name, strategy in call_strategies:
            try:
                result = strategy()
                if inspect.isawaitable(result):
                    return self._run_coroutine_sync(result)
                return result
            except TypeError as exc:
                last_type_error = exc
                self.logger.debug(
                    "Tool invocation strategy '%s' failed for %s: %s",
                    strategy_name,
                    getattr(tool_callable, "__name__", repr(tool_callable)),
                    exc,
                )

        if last_type_error:
            raise last_type_error
        raise RuntimeError("Tool invocation failed with no callable strategy available")

    def _resolve_data_dir(self) -> Path:
        """
        Resolve the canonical persistence directory for all MCP state.
        This server is hard-anchored to repo-local ./data to prevent split planes.
        """
        repo_data_dir = Path(self.DEFAULT_SOVEREIGN_DATA_DIR).resolve()
        configured = os.environ.get("SOVEREIGN_DATA_DIR", "").strip()
        if configured:
            try:
                requested = Path(configured).expanduser().resolve()
                if requested != repo_data_dir:
                    print(
                        "[mcp_server] Ignoring external SOVEREIGN_DATA_DIR "
                        f"('{requested}') and enforcing '{repo_data_dir}'.",
                        file=sys.stderr,
                    )
            except Exception:
                pass
        return repo_data_dir

    def _enforce_canonical_data_env(self) -> None:
        """
        Force all tool modules to see a single canonical data root at import/runtime.
        This prevents split persistence planes caused by inherited shell environment.
        """
        canonical = str(self.data_dir)
        prior_sovereign = os.environ.get("SOVEREIGN_DATA_DIR", "").strip()
        prior_mcp = os.environ.get("MCP_DATA_DIR", "").strip()
        os.environ["SOVEREIGN_DATA_DIR"] = canonical
        os.environ["MCP_DATA_DIR"] = canonical

        def _normalized(path_value: str) -> Optional[Path]:
            if not path_value:
                return None
            try:
                return Path(path_value).expanduser().resolve()
            except Exception:
                return None

        canonical_path = _normalized(canonical)
        prior_sovereign_path = _normalized(prior_sovereign)
        prior_mcp_path = _normalized(prior_mcp)

        if (
            prior_sovereign_path
            and canonical_path
            and prior_sovereign_path != canonical_path
        ):
            print(
                "[mcp_server] Overriding process SOVEREIGN_DATA_DIR "
                f"('{prior_sovereign_path}') -> '{canonical_path}'.",
                file=sys.stderr,
            )
        if prior_mcp_path and canonical_path and prior_mcp_path != canonical_path:
            print(
                "[mcp_server] Overriding process MCP_DATA_DIR "
                f"('{prior_mcp_path}') -> '{canonical_path}'.",
                file=sys.stderr,
            )

    def _legacy_data_candidates(self) -> List[Path]:
        """
        Return legacy data-dir locations that can accidentally appear on Linux.
        We avoid migrating from the current target itself.
        """
        candidates = [
            (Path.cwd() / self.LEGACY_WINDOWS_DATA_DIR).resolve(),
            (Path(__file__).resolve().parent / self.LEGACY_WINDOWS_DATA_DIR).resolve(),
        ]
        uniq: List[Path] = []
        for candidate in candidates:
            if candidate == self.data_dir:
                continue
            if candidate not in uniq:
                uniq.append(candidate)
        return uniq

    @staticmethod
    def _path_has_seed_state(path: Path) -> bool:
        """Detect whether a path has meaningful persisted MCP state."""
        if not path.exists() or not path.is_dir():
            return False
        key_entries = [
            "memory_store.json",
            "thought_journal.json",
            "journal_index.json",
            "sessions",
            "exoskeleton",
            "planner",
            "agents",
        ]
        for entry in key_entries:
            if (path / entry).exists():
                return True
        try:
            return any(path.iterdir())
        except OSError:
            return False

    def _copy_tree_if_missing(self, source: Path, destination: Path) -> int:
        """Copy source items into destination without overwriting existing entries."""
        copied = 0
        destination.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            target = destination / item.name
            if target.exists():
                continue
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
            copied += 1
        return copied

    def _migrate_legacy_data_dir_if_needed(self) -> None:
        """
        Migrate accidental Linux-localized Windows legacy data dir into the
        canonical target if the target doesn't already contain seeded state.
        """
        if self._path_has_seed_state(self.data_dir):
            return

        for candidate in self._legacy_data_candidates():
            if not self._path_has_seed_state(candidate):
                continue
            try:
                copied = self._copy_tree_if_missing(candidate, self.data_dir)
                self.logger.info(
                    "Migrated legacy MCP data from %s to %s (items copied: %d)",
                    candidate,
                    self.data_dir,
                    copied,
                )
                return
            except Exception as exc:
                self.logger.warning(
                    "Failed legacy data migration from %s to %s: %s",
                    candidate,
                    self.data_dir,
                    exc,
                )

    def _cleanup_stray_temp_files(self) -> None:
        """Scan self.data_dir for leftover *.tmp files and unlink them to prevent leaks."""
        try:
            cleaned = 0
            for tmp_file in self.data_dir.glob("*.tmp"):
                try:
                    if tmp_file.is_file():
                        tmp_file.unlink()
                        cleaned += 1
                except Exception as unlink_exc:
                    self.logger.warning(
                        "Failed to delete stray temp file %s: %s", tmp_file, unlink_exc
                    )
            if cleaned > 0:
                self.logger.info("Cleaned up %d leftover temp files from data directory", cleaned)
        except Exception as exc:
            self.logger.warning("Error scanning data directory for temp files: %s", exc)

    def _load_env_file(self) -> None:
        """
        Load key-value pairs from local .env files into process environment.
        Existing environment variables are preserved.
        """
        candidate_paths = [
            Path.cwd() / ".env",
            Path(__file__).resolve().parent / ".env",
        ]

        for env_path in candidate_paths:
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
                self._record_internal_failure(
                    component="mcp_server",
                    operation="load_env_file",
                    error=exc,
                    context={"env_path": str(env_path)},
                    severity="warning",
                )

    def setup_logging(self):
        """Configure comprehensive logging"""
        log_file = self.data_dir / "mcp_server.log"
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.DEBUG if self.debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stderr),
            ],
        )

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

    def _build_tool_instance(self, module_name: str, tool_class: Any) -> Any:
        """Instantiate tool classes with centralized persistence paths when supported."""
        kwargs: Dict[str, Any] = {}
        try:
            signature = inspect.signature(tool_class.__init__)
            params = signature.parameters
        except (TypeError, ValueError):
            return tool_class()

        if "data_dir" in params:
            kwargs["data_dir"] = self.data_dir
        if "storage_file" in params:
            kwargs["storage_file"] = str(self.data_dir / "memory_store.json")

        try:
            return tool_class(**kwargs)
        except TypeError:
            return tool_class()

    TOOL_DISCOVERY_PRIORITY: Dict[str, int] = {
        "memory_tool": 10,
        "memory_interconnect": 20,
        "file_tool": 30,
        "shell_tool": 40,
        "thought_journal_tool": 45,
        "enhanced_web_tool": 60,
        "openrouter_planner_tool": 70,
        "openrouter_agent_tool": 80,
        "session_manager_tool": 90,
        "visual_tool": 100,
        "project_context_tool": 110,
        "auto_tool_module": 120,
        "enhanced_code_analysis_tool": 130,
        "exoskeleton_tool": 140,
    }
    TOOL_DISCOVERY_SKIP = {"__init__", "mcp_server", "lisan_al_gaib", "web_tool"}

    def _resolve_tools_import_surface(self) -> Tuple[Path, str]:
        """Return the preferred tool source directory and import prefix."""
        tools_dir = self.workspace_root / "tools"
        if tools_dir.is_dir():
            return tools_dir, "tools"
        self.logger.warning(
            "tools/ directory not found at %s; falling back to workspace root imports",
            tools_dir,
        )
        return self.workspace_root, ""

    def _discover_tool_module_specs(self) -> List[Tuple[str, str]]:
        """Discover tool modules dynamically from the tools surface."""
        source_dir, _import_prefix = self._resolve_tools_import_surface()
        discovered: List[Tuple[str, str]] = []
        for module_path in sorted(source_dir.glob("*.py")):
            module_name = module_path.stem
            if module_name in self.TOOL_DISCOVERY_SKIP or module_name.startswith("__"):
                continue
            discovered.append((module_name, str(module_path)))
        discovered.sort(
            key=lambda item: (
                self.TOOL_DISCOVERY_PRIORITY.get(item[0], 1000),
                item[0],
            )
        )
        return discovered

    def _discover_tool_class(self, module_name: str, module: Any) -> Optional[Any]:
        """Find the canonical get_tools-bearing class exposed by a module."""
        class_priority = {
            "ExoskeletonTool": 0,
            "OpenRouterAgentTool": 1,
            "OpenRouterPlannerTool": 2,
            "EnhancedSessionTool": 3,
            "IntelligentOptimizationTool": 4,
            "CodeAnalysisTool": 5,
            "ProjectContextTool": 6,
            "FileTool": 7,
            "ShellTool": 8,
            "WebTool": 9,
            "VisualTool": 10,
            "EnhancedMemoryTool": 11,
            "MemoryInterconnectionEngine": 12,
        }
        candidates = []
        for _name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            if hasattr(cls, "get_tools") and callable(getattr(cls, "get_tools")):
                candidates.append(cls)
        if not candidates:
            return None
        candidates.sort(key=lambda cls: (class_priority.get(cls.__name__, 999), cls.__name__))
        return candidates[0]

    def register_tools(self):
        """Register all available MCP tools discovered from the tools directory."""
        try:
            self.logger.info("Starting dynamic tool registration...")
            discovered_modules = self._discover_tool_module_specs()
            source_dir, import_prefix = self._resolve_tools_import_surface()
            self.logger.info(
                "Discovered %d candidate tool modules from %s",
                len(discovered_modules),
                source_dir,
            )

            for module_name, module_path in discovered_modules:
                try:
                    self.logger.debug("Loading %s from %s...", module_name, module_path)
                    import_name = f"{import_prefix}.{module_name}" if import_prefix else module_name
                    module = importlib.import_module(import_name)
                    tool_class = self._discover_tool_class(module_name, module)
                    if tool_class is None:
                        self.logger.debug(
                            "Skipping %s: no get_tools-bearing class discovered",
                            module_name,
                        )
                        continue
                    tool_instance = self._build_tool_instance(module_name, tool_class)

                    if hasattr(tool_instance, "get_tools"):
                        module_tools = tool_instance.get_tools()
                        if not isinstance(module_tools, dict):
                            raise RuntimeError(
                                f"{module_name}.get_tools() returned {type(module_tools).__name__}, expected dict"
                            )
                        for tool_name, tool_definition in module_tools.items():
                            previous_module = self.tool_origins.get(tool_name)
                            if previous_module and previous_module != module_name:
                                self.logger.info(
                                    "Tool '%s' overridden: %s -> %s",
                                    tool_name,
                                    previous_module,
                                    module_name,
                                )
                            self.tools[tool_name] = tool_definition
                            self.tool_origins[tool_name] = module_name
                        self.tool_modules[module_name] = tool_instance
                        self.tool_health["loaded_tools"].add(module_name)
                        self.logger.info(
                            "Loaded %d tools from %s (%s)",
                            len(module_tools),
                            module_name,
                            tool_class.__name__,
                        )
                    else:
                        self._record_internal_failure(
                            component="mcp_server",
                            operation="register_tools_missing_get_tools",
                            error=RuntimeError(
                                f"{module_name} does not have get_tools() method"
                            ),
                            context={"module_name": module_name},
                            severity="warning",
                        )

                except ImportError as e:
                    self.logger.error(f"Failed to import {module_name}: {e}")
                    self.tool_health["failed_loads"][module_name] = {
                        "error": str(e),
                        "timestamp": time.time(),
                    }
                except Exception as e:
                    self.logger.error(f"Failed to load {module_name}: {e}")
                    self.tool_health["failed_loads"][module_name] = {
                        "error": str(e),
                        "timestamp": time.time(),
                    }

            self.server_info["total_tools"] = len(self.tools)
            self.logger.info(
                f"Tool registration complete! {len(self.tools)} tools available"
            )
            self.log_tool_summary()

            exo = self.tool_modules.get("exoskeleton_tool")
            if exo and hasattr(exo, "attach_live_tools_provider"):
                try:
                    exo.attach_live_tools_provider(lambda: self.tools)
                except Exception as attach_err:
                    self._record_internal_failure(
                        component="mcp_server",
                        operation="attach_exoskeleton_live_provider",
                        error=attach_err,
                        context={"module_name": "exoskeleton_tool"},
                        severity="error",
                    )

            agent_tool = self.tool_modules.get("openrouter_agent_tool")
            if agent_tool and hasattr(agent_tool, "register_tools"):
                try:
                    agent_tool.register_tools(self.tools)
                    self.logger.info("Agent tool registered with MCP tool registry")
                except Exception as attach_err:
                    self._record_internal_failure(
                        component="mcp_server",
                        operation="attach_agent_tool_registry",
                        error=attach_err,
                        context={"module_name": "openrouter_agent_tool"},
                        severity="error",
                    )

            self._attach_registry_bound_facades()
            self._sync_exoskeleton_catalog(force=True)

            for tool_name in self.tools.keys():
                self.tool_health["unused_tools"][tool_name] = True

            self._inject_proactive_memory_context("session_start")

            # ── Explicit prescient layer warm-up ─────────────────────────────────────
            self._warm_up_prescient_layer()

            # Late-init distillation AFTER tool plane is fully stable (opt-in)
            self._late_init_distillation()

            # Wire thought_journal → lisan cognitive journal bridge
            self._wire_journal_lisan_bridge()

            # Start the perpetual autonomous exo cycle (never stops)
            self._start_autonomous_cycle()

        except Exception as e:
            self.logger.error(f"Critical error during tool registration: %s", e)
            self.logger.error(traceback.format_exc())

    def _warm_up_prescient_layer(self) -> None:
        """
        Explicitly initialize lisan's prescient subsystems through the ExoskeletonTool.
        This ensures GoldenPathOracle has loaded golden_paths.json priors,
        NarrativeEngine has its tool catalog, and momentum manifold is active
        BEFORE the first Codex tool call arrives.
        """
        exo = self.tool_modules.get("exoskeleton_tool")
        if exo is None:
            self.logger.warning("ExoskeletonTool not loaded — prescient layer inactive")
            return

        # Trigger the lisan subsystem init explicitly
        if hasattr(exo, "_ensure_lisan_subsystems"):
            try:
                exo._ensure_lisan_subsystems()
                self.logger.info("Prescient layer (lisan subsystems) warmed up")
            except Exception as e:
                self._record_internal_failure(
                    component="mcp_server",
                    operation="prescient_layer_warmup",
                    error=e,
                    severity="warning",
                )

        # Fire boot briefing into events.jsonl so it's available for session context
        if hasattr(exo, "generate_boot_briefing"):
            try:
                briefing = exo.generate_boot_briefing()
                self._append_event(
                    event_type="prescient_boot_briefing",
                    source="exoskeleton",
                    payload={"briefing": briefing, "tool_count": len(self.tools)},
                    importance_hint=1.0,
                )
            except Exception as e:
                self.logger.debug("Boot briefing generation failed (non-fatal): %s", e)

    def _normalize_live_tool_for_exoskeleton(
        self, tool_name: str, tool_info: Any
    ) -> Optional[Dict[str, Any]]:
        """Normalize live tool entries so exoskeleton sync receives dict metadata."""
        if isinstance(tool_info, dict):
            normalized = dict(tool_info)
            if "inputSchema" not in normalized and isinstance(
                normalized.get("input_schema"), dict
            ):
                normalized["inputSchema"] = normalized["input_schema"]
            return normalized
        if callable(tool_info):
            description = (
                getattr(tool_info, "__doc__", "") or f"Callable tool: {tool_name}"
            )
            return {
                "description": str(description).strip(),
                "parameters": [],
                "function": tool_info,
            }
        self.logger.debug(
            "Skipping live tool '%s' during exoskeleton sync: unsupported type %s",
            tool_name,
            type(tool_info).__name__,
        )
        return None

    def _sync_exoskeleton_catalog(self, force: bool = False) -> None:
        """Synchronize the exoskeleton catalog from the live server registry."""
        exo = self.tool_modules.get("exoskeleton_tool")
        if not exo or not hasattr(exo, "sync_from_live_tools"):
            return

        tool_count = len(self.tools)
        now = time.time()
        with self._exo_sync_lock:
            if (
                not force
                and self._last_exo_sync_tool_count == tool_count
                and (now - self._last_exo_sync_time) < 10.0
            ):
                return

        normalized_tools: Dict[str, Dict[str, Any]] = {}
        for tool_name, tool_info in self.tools.items():
            normalized = self._normalize_live_tool_for_exoskeleton(tool_name, tool_info)
            if normalized is None:
                continue
            normalized_tools[tool_name] = normalized
        try:
            exo.sync_from_live_tools(normalized_tools)
            with self._exo_sync_lock:
                self._last_exo_sync_time = now
                self._last_exo_sync_tool_count = tool_count
        except Exception as sync_err:
            self._record_internal_failure(
                component="mcp_server",
                operation="sync_exoskeleton_catalog",
                error=sync_err,
                context={"tool_count": tool_count, "force": force},
                severity="error",
            )

    def log_tool_summary(self):
        """Log detailed summary of registered tools"""
        self.logger.info("=" * 80)
        self.logger.info("MCP SERVER TOOL INVENTORY")
        self.logger.info("=" * 80)

        categories = {}
        for tool_name in self.tools.keys():
            if tool_name.startswith("bb7_"):
                category = tool_name.split("_")[1] if "_" in tool_name else "misc"
            else:
                category = "legacy"

            if category not in categories:
                categories[category] = []
            categories[category].append(tool_name)

        for category, tools in categories.items():
            self.logger.info(f"{category.upper()}: {len(tools)} tools")
            for tool in sorted(tools):
                self.logger.info(f"   - {tool}")

        self.logger.info("=" * 80)
        self.logger.info(f"TOTAL TOOLS REGISTERED: {len(self.tools)}")
        self.logger.info("=" * 80)

    def update_average_response_time(self, execution_time: float):
        """Update rolling average response time"""
        current_avg = self.performance_metrics["average_response_time"]
        total_calls = self.performance_metrics["successful_calls"]

        if total_calls == 1:
            self.performance_metrics["average_response_time"] = execution_time
        else:
            self.performance_metrics["average_response_time"] = (
                current_avg * (total_calls - 1) + execution_time
            ) / total_calls

    def run_stdio(self):
        """Run the MCP server using stdio for JSON-RPC communication"""
        self.logger.info("Starting MCP server in stdio mode")

        try:
            while True:
                # Read message from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line.strip())
                    self.logger.debug(f"Received request: {request}")

                    # Process the request
                    response = self.handle_request(request)

                    if response:
                        # Send response to stdout
                        response_json = json.dumps(response, separators=(",", ":"))
                        sys.stdout.write(f"{response_json}\n")
                        sys.stdout.flush()
                        self.logger.debug(f"Sent response: {response}")

                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                    error_id = self._normalize_id(None)
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"},
                        "id": error_id,
                    }
                    sys.stdout.write(f"{json.dumps(error_response)}\n")
                    sys.stdout.flush()

                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    error_id = self._normalize_id(None)
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": "Internal error"},
                        "id": error_id,
                    }
                    sys.stdout.write(f"{json.dumps(error_response)}\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Unexpected error in stdio loop: {e}")

        self.logger.info("MCP server stdio loop ended")

    def run_sse(self, port: int = 8765) -> None:
        """
        Run the MCP server as a persistent HTTP+SSE server.
        Follows the MCP SSE transport spec:
          - GET  /sse          → opens SSE stream, emits endpoint event
          - POST /message      → receives JSON-RPC, routes via session
          - All responses sent back over the client's SSE stream
        Multiple agents connect simultaneously; all share one process and data plane.
        """
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import urlparse, parse_qs

        server_ref = self
        _sessions: Dict[str, queue.Queue] = {}
        _sessions_lock = threading.Lock()

        class MCPSSEHandler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):  # suppress default stderr noise
                server_ref.logger.debug("SSE HTTP: " + fmt, *args)

            def _cors(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def do_OPTIONS(self):
                self.send_response(200)
                self._cors()
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path != "/sse":
                    self.send_error(404)
                    return

                session_id = uuid.uuid4().hex
                q: queue.Queue = queue.Queue()
                with _sessions_lock:
                    _sessions[session_id] = q

                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self._cors()
                self.end_headers()

                try:
                    # Advertise the POST endpoint for this session
                    endpoint = f"/message?sessionId={session_id}"
                    self.wfile.write(
                        f"event: endpoint\ndata: {endpoint}\n\n".encode()
                    )
                    self.wfile.flush()
                    server_ref.logger.info(
                        "SSE session opened: %s", session_id
                    )

                    while True:
                        try:
                            msg = q.get(timeout=25)
                            if msg is None:
                                break
                            data = json.dumps(msg, separators=(",", ":"))
                            self.wfile.write(
                                f"event: message\ndata: {data}\n\n".encode()
                            )
                            self.wfile.flush()
                        except queue.Empty:
                            # keepalive ping
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    with _sessions_lock:
                        _sessions.pop(session_id, None)
                    server_ref.logger.info("SSE session closed: %s", session_id)

            def do_POST(self):
                parsed = urlparse(self.path)
                if parsed.path != "/message":
                    self.send_error(404)
                    return

                params = parse_qs(parsed.query)
                sid_list = params.get("sessionId", [])
                if not sid_list:
                    self.send_error(400, "Missing sessionId")
                    return

                session_id = sid_list[0]
                with _sessions_lock:
                    q = _sessions.get(session_id)
                if q is None:
                    self.send_error(404, "Unknown session")
                    return

                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    request = json.loads(body)
                except json.JSONDecodeError:
                    self.send_error(400, "Invalid JSON")
                    return

                # Acknowledge immediately; response arrives over SSE stream
                self.send_response(202)
                self._cors()
                self.send_header("Content-Length", "0")
                self.end_headers()

                def _dispatch():
                    try:
                        response = server_ref.handle_request(request)
                        if response is not None:
                            q.put(response)
                    except Exception as exc:
                        server_ref.logger.error(
                            "SSE dispatch error: %s", exc
                        )
                        q.put({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                            },
                            "id": request.get("id"),
                        })

                threading.Thread(target=_dispatch, daemon=True).start()

        localhost_only = str(
            os.environ.get("MCP_SSE_LOCALHOST_ONLY", "1")
        ).strip().lower() in {"1", "true", "yes"}
        host = "127.0.0.1" if localhost_only else "0.0.0.0"

        httpd = ThreadingHTTPServer((host, port), MCPSSEHandler)
        self.logger.info(
            "MCP SSE server listening on %s:%d  (all agents share this process)",
            host, port,
        )

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("SSE server interrupted")
        finally:
            httpd.shutdown()

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a JSON-RPC request"""
        if not isinstance(request, dict):
            self._record_internal_failure(
                component="mcp_server",
                operation="handle_request_invalid_request",
                error=RuntimeError("JSON-RPC request must be an object"),
                context={"request_type": type(request).__name__},
                severity="error",
            )
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request"},
                "id": self._normalize_id(None),
            }

        # Extract request components
        jsonrpc = request.get("jsonrpc", "2.0")
        method = request.get("method")
        params = request.get("params", {})
        req_id = self._normalize_id(request.get("id"))
        turn_id = self._next_turn_id()

        self.logger.info(f"MCP SERVER RECEIVED METHOD: '{method}'")
        codex_ingest_summary = self._ingest_codex_context(turn_id=turn_id)
        self._append_event(
            event_type="request_received",
            source="mcp_server",
            turn_id=turn_id,
            payload={
                "request_id": req_id,
                "method": method,
                "params_keys": sorted(list(params.keys()))
                if isinstance(params, dict)
                else [],
                "codex_ingest_summary": codex_ingest_summary,
            },
            importance_hint=0.25,
        )
        turn_memory_context: Optional[Dict[str, Any]] = None
        if method == "tools/call":
            surfaced = self._surface_turn_memory_context(
                turn_id=turn_id, method=method, params=params
            )
            if isinstance(surfaced, dict):
                turn_memory_context = surfaced

        if method == "initialize":
            response = self.handle_initialize(req_id)
        elif method == "tools/list":
            response = self.handle_list_tools(req_id)
        elif method == "tools/call":
            call_params = dict(params) if isinstance(params, dict) else {}
            call_params["__turn_id"] = turn_id
            call_params["__turn_memory_context"] = turn_memory_context or {}
            response = self.handle_call_tool(req_id, call_params)
        elif method == "setLogLevel":
            # Handle VS Code's log level setting request
            response = self.handle_set_log_level(req_id, params)
        else:
            # Method not found
            response = {
                "jsonrpc": jsonrpc,
                "error": {"code": -32601, "message": "Method not found"},
                "id": req_id,
            }

        self._append_event(
            event_type="request_completed",
            source="mcp_server",
            turn_id=turn_id,
            payload={
                "request_id": req_id,
                "method": method,
                "status": "error" if isinstance(response, dict) and "error" in response else "success",
            },
            importance_hint=0.2,
        )
        return response

    def handle_initialize(self, req_id: Union[str, int]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "logging": {}},
                "serverInfo": {
                    "name": self.server_info["name"],
                    "version": self.server_info["version"],
                },
            },
            "id": req_id,
        }

    def handle_list_tools(self, req_id: Union[str, int]) -> Dict[str, Any]:
        """Handle tools/list request - supports both 'parameters' list and 'inputSchema' dict formats"""
        self._sync_exoskeleton_catalog()
        tool_list = []
        for name, tool_info in self.tools.items():
            try:
                # Debug: Check what type tool_info is
                self.logger.debug(f"Processing tool {name}, type: {type(tool_info)}")

                # Handle case where tool_info might be a function directly
                if callable(tool_info):
                    self.logger.warning(
                        f"Tool '{name}' is stored as a function, wrapping as no-params tool"
                    )
                    tool_list.append(
                        {
                            "name": name,
                            "description": getattr(
                                tool_info, "__doc__", "No description available."
                            ),
                            "inputSchema": {"type": "object", "properties": {}},
                        }
                    )
                    continue

                # Ensure tool_info is a dictionary
                if not isinstance(tool_info, dict):
                    self.logger.warning(
                        f"Tool '{name}' has invalid structure: {type(tool_info)}, skipping"
                    )
                    continue

                # Check for inputSchema format (newer tools)
                input_schema = tool_info.get("inputSchema")
                if input_schema and isinstance(input_schema, dict):
                    # Tool already has inputSchema, use it directly
                    tool_list.append(
                        {
                            "name": name,
                            "description": tool_info.get(
                                "description", "No description available."
                            ),
                            "inputSchema": input_schema,
                        }
                    )
                    continue

                # Check for parameters format (legacy tools)
                parameters = tool_info.get("parameters", [])
                if isinstance(parameters, list):
                    properties = {}
                    required = []
                    for param in parameters:
                        if not isinstance(param, dict) or "name" not in param:
                            continue
                        param_name = param["name"]
                        param_type = param.get("type", "string")
                        property_schema: Dict[str, Any] = {
                            "type": param_type,
                            "description": param.get("description", ""),
                        }

                        # Preserve richer schema hints from legacy parameter metadata.
                        if isinstance(param.get("enum"), list):
                            property_schema["enum"] = param["enum"]
                        if "default" in param:
                            property_schema["default"] = param.get("default")

                        # Strict JSON schema validators require array.item schemas.
                        if param_type == "array":
                            items = param.get("items")
                            property_schema["items"] = (
                                items if isinstance(items, dict) else {"type": "string"}
                            )
                        elif param_type == "object":
                            if isinstance(param.get("properties"), dict):
                                property_schema["properties"] = param["properties"]
                                req_props = param.get("required")
                                if isinstance(req_props, list):
                                    property_schema["required"] = req_props
                            elif isinstance(
                                param.get("additionalProperties"), (dict, bool)
                            ):
                                property_schema["additionalProperties"] = param[
                                    "additionalProperties"
                                ]

                        properties[param_name] = property_schema
                        if param.get("required", False):
                            required.append(param_name)

                    tool_list.append(
                        {
                            "name": name,
                            "description": tool_info.get(
                                "description", "No description available."
                            ),
                            "inputSchema": {
                                "type": "object",
                                "properties": properties,
                                "required": required,
                            },
                        }
                    )
                    continue

                # Fallback: tool with no parameters
                tool_list.append(
                    {
                        "name": name,
                        "description": tool_info.get(
                            "description", "No description available."
                        ),
                        "inputSchema": {"type": "object", "properties": {}},
                    }
                )

            except Exception as e:
                self.logger.error(f"Error processing tool '{name}': {e}")
                self._record_internal_failure(
                    component="mcp_server",
                    operation="handle_list_tools",
                    error=e,
                    context={"tool_name": name},
                    severity="error",
                )
                continue

        return {"jsonrpc": "2.0", "result": {"tools": tool_list}, "id": req_id}

    def handle_call_tool(
        self, req_id: Union[str, int], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tools/call request"""
        start_time = time.time()
        self.performance_metrics["tool_calls"] += 1
        self.performance_metrics["last_activity"] = start_time

        if isinstance(params, dict):
            turn_id_raw = params.get("__turn_id")
            turn_memory_context = params.get("__turn_memory_context")
            call_params = dict(params)
            call_params.pop("__turn_id", None)
            call_params.pop("__turn_memory_context", None)
        else:
            turn_id_raw = None
            turn_memory_context = None
            call_params = {}
        turn_id = turn_id_raw if isinstance(turn_id_raw, str) else None

        name = call_params.get("name")
        arguments = call_params.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            self.performance_metrics["failed_calls"] += 1
            self._append_event(
                event_type="tool_execution_end",
                source="mcp_server",
                turn_id=turn_id,
                payload={
                    "tool_name": name,
                    "status": "failed",
                    "error": "Tool arguments must be an object",
                },
                importance_hint=0.45,
            )
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Tool arguments must be an object",
                },
                "id": req_id,
            }

        if not name or name not in self.tools:
            self.performance_metrics["failed_calls"] += 1
            self._append_event(
                event_type="tool_execution_end",
                source="mcp_server",
                turn_id=turn_id,
                payload={
                    "tool_name": name,
                    "status": "failed",
                    "error": f"Tool not found: {name}",
                },
                importance_hint=0.5,
            )
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Tool not found: {name}"},
                "id": req_id,
            }

        self._append_event(
            event_type="tool_execution_start",
            source="mcp_server",
            turn_id=turn_id,
            payload={
                "tool_name": name,
                "intent_guess": name,
                "arguments": arguments,
            },
            importance_hint=0.5,
        )

        try:
            if isinstance(name, str) and name.startswith("bb7_exo_"):
                self._sync_exoskeleton_catalog()
            tool_definition = self.tools[name]

            # Debug: Check what type tool_definition is
            self.logger.debug(f"Calling tool {name}, type: {type(tool_definition)}")

            # Handle case where tool_definition might be a function directly
            if callable(tool_definition):
                self.logger.warning(
                    f"Tool '{name}' is stored as a function, calling directly"
                )
                result = self._invoke_tool_callable(
                    tool_definition, arguments, prefer_kwargs=True
                )
            elif isinstance(tool_definition, dict):
                tool_function = tool_definition.get("function")
                if not tool_function:
                    self._append_event(
                        event_type="tool_execution_end",
                        source="mcp_server",
                        turn_id=turn_id,
                        payload={
                            "tool_name": name,
                            "status": "failed",
                            "error": f"Tool '{name}' has no function defined",
                        },
                        importance_hint=0.6,
                    )
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Tool '{name}' has no function defined",
                        },
                        "id": req_id,
                    }

                # Validate arguments
                required_params: List[str] = []
                has_legacy_parameters = "parameters" in tool_definition
                parameters = tool_definition.get("parameters", [])
                if has_legacy_parameters and isinstance(parameters, list):
                    required_params = [
                        p["name"]
                        for p in parameters
                        if isinstance(p, dict) and p.get("required", False)
                    ]
                elif isinstance(tool_definition.get("inputSchema"), dict):
                    required_from_schema = tool_definition["inputSchema"].get(
                        "required", []
                    )
                    if isinstance(required_from_schema, list):
                        required_params = [
                            p for p in required_from_schema if isinstance(p, str)
                        ]

                for param in required_params:
                    if param not in arguments:
                        self._append_event(
                            event_type="tool_execution_end",
                            source="mcp_server",
                            turn_id=turn_id,
                            payload={
                                "tool_name": name,
                                "status": "failed",
                                "error": (
                                    f"Missing required parameter '{param}' "
                                    f"for tool '{name}'"
                                ),
                            },
                            importance_hint=0.5,
                        )
                        return {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32602,
                                "message": f"Missing required parameter '{param}' for tool '{name}'",
                            },
                            "id": req_id,
                        }

                prefer_kwargs = not (
                    isinstance(tool_definition.get("inputSchema"), dict)
                    and "parameters" not in tool_definition
                )
                result = self._invoke_tool_callable(
                    tool_function, arguments, prefer_kwargs=prefer_kwargs
                )
            else:
                self._append_event(
                    event_type="tool_execution_end",
                    source="mcp_server",
                    turn_id=turn_id,
                    payload={
                        "tool_name": name,
                        "status": "failed",
                        "error": f"Tool '{name}' has invalid structure",
                    },
                    importance_hint=0.6,
                )
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Tool '{name}' has invalid structure",
                    },
                    "id": req_id,
                }

            # ── Trajectory telemetry: only fire if distillation enabled AND agent context ──
            if (
                self._distillation_engine is not None 
                and getattr(self, "_latest_codex_thread_id", None)  # Only capture within a known Codex thread
            ):
                # Append to in-memory trajectory buffer, not per-call JSONL writes
                with self._trajectory_buffer_lock:
                    self._trajectory_buffer.append({
                        "role": "tool_result",
                        "tool_name": name,
                        "arguments": arguments,
                        "result_summary": self._summarize_value(result, max_chars=200),
                        "latency_ms": round((time.time() - start_time) * 1000, 1),
                        "turn_id": turn_id,
                        "ts": time.time(),
                    })

            execution_time = time.time() - start_time
            self.performance_metrics["successful_calls"] += 1
            self.update_average_response_time(execution_time)

            # Log tool usage to SQLite3 distillation database
            self._log_tool_usage(
                name, True, execution_time, session_id="current", arguments=arguments
            )

            # Track slow tools for health monitoring
            if execution_time >= 5.0:
                self.logger.warning(
                    "Slow tool call detected: %s took %.2fs",
                    name,
                    execution_time,
                )
                if name not in self.tool_health["slow_tools"]:
                    self.tool_health["slow_tools"][name] = {
                        "count": 0,
                        "total_time": 0.0,
                        "avg_time": 0.0,
                    }
                slow_data = self.tool_health["slow_tools"][name]
                slow_data["count"] += 1
                slow_data["total_time"] += execution_time
                slow_data["avg_time"] = slow_data["total_time"] / slow_data["count"]

            # Normalize tool output into MCP-compliant content blocks
            payload = result
            if isinstance(result, str):
                try:
                    payload = json.loads(result)
                except json.JSONDecodeError:
                    payload = result

            # If tool returned only an "output" field, flatten it for display
            if (
                isinstance(payload, dict)
                and "content" not in payload
                and set(payload.keys()) == {"output"}
            ):
                payload = payload.get("output")

            self._append_event(
                event_type="tool_execution_end",
                source="mcp_server",
                turn_id=turn_id,
                payload={
                    "tool_name": name,
                    "status": "success",
                    "latency_ms": round(execution_time * 1000.0, 3),
                    "result_summary": self._summarize_value(payload),
                    "artifacts": self._extract_artifacts(arguments, result),
                },
                importance_hint=0.7,
            )

            self._schedule_tool_exchange_memory_persist(
                tool_name=str(name or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
                result_payload=payload,
                success=True,
                latency_seconds=execution_time,
                turn_id=turn_id,
                request_id=req_id,
                memory_context=(
                    turn_memory_context if isinstance(turn_memory_context, dict) else {}
                ),
            )

            sovereign_meta = self._build_sovereign_meta(
                tool_name=str(name or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
                result_payload=payload,
                turn_memory_context=(
                    turn_memory_context if isinstance(turn_memory_context, dict) else {}
                ),
                turn_id=turn_id,
            )
            self._auto_reflect_tool_call(
                tool_name=str(name or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
                success=True,
                turn_id=turn_id,
            )
            formatted = self._format_tool_result(
                payload,
                is_error=False,
                tool_name=str(name or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
            )
            if sovereign_meta:
                formatted.setdefault("meta", {})["sovereign_context"] = sovereign_meta

            return {"jsonrpc": "2.0", "result": formatted, "id": req_id}

        except Exception as e:
            self.logger.error(f"Error calling tool {name}: {e}")
            self.logger.error(traceback.format_exc())
            self.performance_metrics["failed_calls"] += 1
            execution_time = time.time() - start_time

            # Track failed tool calls for health monitoring
            if name not in self.tool_health["failed_tools"]:
                self.tool_health["failed_tools"][name] = {
                    "count": 0,
                    "last_error": "",
                    "last_failure": 0.0,
                }
            fail_data = self.tool_health["failed_tools"][name]
            fail_data["count"] += 1
            fail_data["last_error"] = str(e)[:200]  # Truncate long errors
            fail_data["last_failure"] = time.time()

            self.logger.warning(
                f"Tool health updated: {name} has failed {fail_data['count']} time(s). Last error: {fail_data['last_error'][:50]}..."
            )

            # Log failed tool usage to SQLite3
            self._log_tool_usage(
                name,
                False,
                execution_time,
                error=str(e)[:500],
                session_id="current",
                arguments=arguments,
            )

            if self._distillation_engine is not None:
                _snap_memory_context = (
                    turn_memory_context if isinstance(turn_memory_context, dict) else {}
                )
                _snap_error = {
                    "error": str(e)[:500],
                    "traceback": traceback.format_exc()[:4000],
                }
                _snap_artifacts = self._extract_artifacts(arguments, {})
                _engine = self._distillation_engine

                def _fire_failure_telemetry(
                    _n=name,
                    _a=arguments,
                    _r=_snap_error,
                    _l=execution_time,
                    _req_id=req_id,
                    _artifacts=_snap_artifacts,
                    _memory_context=_snap_memory_context,
                    _e=_engine,
                ):
                    try:
                        _e.log_mcp_rpc_stub(
                            _n,
                            _a,
                            _r,
                            _l,
                            session_id=self.session_id,
                            source_plane="mcp_server_rpc",
                            turn_id=turn_id,
                            request_id=_req_id,
                            tool_error_count=1,
                            environment_state={
                                "os": sys.platform,
                                "active_tools_count": len(self.tools),
                                "workspace_root": str(self.workspace_root),
                            },
                            context={
                                "codex_thread_id": self._latest_codex_thread_id or "",
                                "artifacts": _artifacts,
                                "memory_context_status": _memory_context.get("status", ""),
                                "memory_context_summary": _memory_context.get(
                                    "context_summary", ""
                                ),
                            },
                        )
                    except Exception as telemetry_exc:
                        self._record_internal_failure(
                            component="mcp_server",
                            operation="distillation_thread_failure",
                            error=telemetry_exc,
                            context={"tool_name": _n},
                            severity="error",
                            turn_id=turn_id,
                        )

                threading.Thread(target=_fire_failure_telemetry, daemon=True).start()

            self._append_event(
                event_type="tool_execution_end",
                source="mcp_server",
                turn_id=turn_id,
                payload={
                    "tool_name": name,
                    "status": "failed",
                    "latency_ms": round(execution_time * 1000.0, 3),
                    "error": str(e)[:500],
                    "artifacts": self._extract_artifacts(arguments, {}),
                },
                importance_hint=0.8,
            )

            self._schedule_tool_exchange_memory_persist(
                tool_name=str(name or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
                result_payload={
                    "error": str(e)[:500],
                    "traceback": traceback.format_exc()[:2000],
                },
                success=False,
                latency_seconds=execution_time,
                turn_id=turn_id,
                request_id=req_id,
                memory_context=(
                    turn_memory_context if isinstance(turn_memory_context, dict) else {}
                ),
            )
            self._auto_reflect_tool_call(
                tool_name=str(name or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
                success=False,
                turn_id=turn_id,
                error=str(e)[:500],
            )

            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}",
                },
                "id": req_id,
            }

    def handle_set_log_level(
        self, req_id: Union[str, int], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle setLogLevel request from VS Code"""
        try:
            level = params.get("level", "info")
            # Map VS Code log levels to Python logging levels
            level_map = {
                "trace": logging.DEBUG,
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "warn": logging.WARNING,
                "warning": logging.WARNING,
                "error": logging.ERROR,
                "fatal": logging.CRITICAL,
                "critical": logging.CRITICAL,
            }

            python_level = level_map.get(level.lower(), logging.INFO)

            # Update logger level
            self.logger.setLevel(python_level)
            logging.getLogger().setLevel(python_level)

            self.logger.info(
                f"Log level set to: {level} (Python level: {python_level})"
            )

            return {"jsonrpc": "2.0", "result": {"success": True}, "id": req_id}
        except Exception as e:
            self.logger.error(f"Error setting log level: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Failed to set log level: {str(e)}",
                },
                "id": req_id,
            }

    def shutdown(self):
        """Graceful server shutdown"""
        self.logger.info("Initiating MCP Server shutdown...")

        try:
            # Close tool resources (e.g., aiohttp sessions) before final metrics snapshot.
            for module_name, tool_instance in self.tool_modules.items():
                close_method = getattr(tool_instance, "close", None)
                if callable(close_method):
                    try:
                        close_result = close_method()
                        if inspect.isawaitable(close_result):
                            self._run_coroutine_sync(close_result)
                    except Exception as close_error:
                        self.logger.warning(
                            "Error while closing tool module '%s': %s",
                            module_name,
                            close_error,
                        )

            # Stop shared async loop after async tool resources are closed.
            self._stop_async_loop()

            shutdown_info = {
                "shutdown_time": time.time(),
                "final_metrics": self.performance_metrics.copy(),
                "total_uptime": time.time() - self.server_info["startup_time"],
                "total_tools": len(self.tools),
            }

            shutdown_file = self.data_dir / "shutdown_status.json"
            with open(shutdown_file, "w", encoding="utf-8") as f:
                json.dump(shutdown_info, f, indent=2)

            self._append_event(
                event_type="session_end",
                source="mcp_server",
                payload={
                    "pid": os.getpid(),
                    "uptime_seconds": shutdown_info["total_uptime"],
                    "final_tool_calls": self.performance_metrics.get("tool_calls", 0),
                    "status_file": str(shutdown_file),
                },
                importance_hint=0.9,
            )
            if getattr(self, "_distillation_conn", None) is not None:
                try:
                    self._distillation_conn.close()
                    self.logger.info("SQLite3 distillation database connection closed")
                except Exception as db_exc:
                    self.logger.warning("Error closing distillation database: %s", db_exc)

            self.logger.info("MCP Server shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            self._release_singleton_lock()


def main():
    """Main entry point for MCP Server"""
    parser = argparse.ArgumentParser(
        description="MCP Server - Advanced AI Collaboration Platform"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport mode: 'stdio' (one process per client) or 'sse' "
             "(persistent HTTP server, all clients share one process). "
             "Default: stdio (or MCP_TRANSPORT env var).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_SSE_PORT", "8765")),
        help="Port for SSE transport (default: 8765 or MCP_SSE_PORT env var).",
    )
    args = parser.parse_args()

    server = MCPServer(debug=args.debug, transport=args.transport)

    try:
        if args.transport == "sse":
            server.run_sse(port=args.port)
        else:
            server.run_stdio()
    except Exception as e:
        server.logger.error(f"Server error: {e}")
        server.logger.error(traceback.format_exc())
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
