#!/usr/bin/env python3
"""
Registry-bound meta-intelligence facade for Somnus-MCP.

This module is deliberately not a second tool container.  It binds to the live
BB7 tool plane created by mcp_server.py and composes existing cognition surfaces
(memory substrate, session continuity, project context, analysis, Lisan) without
importing or instantiating sibling tools.
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


class IntelligentToolOrchestrator:
    """Coordinate live BB7 surfaces into higher-order cognition operations."""

    TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")

    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        repo_root = Path(__file__).resolve().parent.parent
        self.repo_root = repo_root
        configured_data_dir = (
            os.environ.get("SOVEREIGN_DATA_DIR")
            or os.environ.get("MCP_DATA_DIR")
            or str(repo_root / "data")
        )
        self.data_dir = Path(data_dir or configured_data_dir).expanduser().resolve()
        self.meta_dir = self.data_dir / "meta_intelligence"
        self.meta_dir.mkdir(parents=True, exist_ok=True)

        self.tools: Dict[str, Any] = {}
        self.tool_modules: Dict[str, Any] = {}
        self.active_workflows: Dict[str, Any] = {}
        self.tool_interaction_patterns: Dict[str, Any] = {}
        self.emergent_insights: List[Dict[str, Any]] = []

    def attach_tool_plane(self, tools: Dict[str, Any], tool_modules: Dict[str, Any]) -> Dict[str, Any]:
        """Bind this facade to the already-registered live server tool plane."""
        self.tools = tools if isinstance(tools, dict) else {}
        self.tool_modules = tool_modules if isinstance(tool_modules, dict) else {}
        return {
            "success": True,
            "attached_tools": len(self.tools),
            "attached_modules": sorted(self.tool_modules.keys()),
        }

    # ------------------------------------------------------------------
    # Invocation helpers
    # ------------------------------------------------------------------

    def _coerce_arguments(
        self, arguments: Optional[Dict[str, Any]] = None, kwargs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if isinstance(arguments, dict):
            payload.update(arguments)
        if isinstance(kwargs, dict):
            payload.update(kwargs)
        return payload

    def _tool_callable(self, tool_name: str) -> Tuple[Optional[Callable[..., Any]], Optional[Dict[str, Any]]]:
        tool_info = self.tools.get(tool_name)
        if isinstance(tool_info, dict):
            fn = tool_info.get("function")
            return (fn if callable(fn) else None), tool_info
        if callable(tool_info):
            return tool_info, None
        return None, None

    def _invoke_live_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke a live tool entry without creating any sibling tool instances."""
        fn, metadata = self._tool_callable(tool_name)
        if fn is None:
            return {"available": False, "tool": tool_name, "reason": "not_registered"}

        args = dict(arguments or {})
        prefer_kwargs = True
        if isinstance(metadata, dict):
            prefer_kwargs = not (
                isinstance(metadata.get("inputSchema"), dict) and "parameters" not in metadata
            )

        strategies: List[Tuple[str, Callable[[], Any]]] = []
        if not args:
            strategies.append(("no_args", lambda: fn()))
        if prefer_kwargs:
            strategies.extend([
                ("kwargs", lambda: fn(**args)),
                ("dict", lambda: fn(args)),
            ])
        else:
            strategies.extend([
                ("dict", lambda: fn(args)),
                ("kwargs", lambda: fn(**args)),
            ])

        last_type_error: Optional[TypeError] = None
        started = time.time()
        for strategy_name, strategy in strategies:
            try:
                result = strategy()
                if inspect.isawaitable(result):
                    return {
                        "available": True,
                        "tool": tool_name,
                        "success": False,
                        "error": "awaitable_live_tool_not_executed_sync",
                    }
                return {
                    "available": True,
                    "tool": tool_name,
                    "success": True,
                    "strategy": strategy_name,
                    "elapsed_ms": round((time.time() - started) * 1000, 3),
                    "result": self._compact_result(result),
                }
            except TypeError as exc:
                last_type_error = exc
                continue
            except Exception as exc:  # live substrate failures are surfaced, not hidden
                return {
                    "available": True,
                    "tool": tool_name,
                    "success": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }

        return {
            "available": True,
            "tool": tool_name,
            "success": False,
            "error": str(last_type_error) if last_type_error else "invocation_failed",
            "error_type": type(last_type_error).__name__ if last_type_error else "RuntimeError",
        }

    def _first_available_call(self, tool_names: List[str], arguments: Dict[str, Any]) -> Dict[str, Any]:
        for tool_name in tool_names:
            outcome = self._invoke_live_tool(tool_name, arguments)
            if outcome.get("available"):
                return outcome
        return {"available": False, "tool_candidates": tool_names, "reason": "none_registered"}

    def _compact_result(self, result: Any, max_chars: int = 6000) -> Any:
        if isinstance(result, (dict, list, int, float, bool)) or result is None:
            return result
        text = str(result)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + f"\n... [truncated {len(text) - max_chars} chars]"

    def _json(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, indent=2, default=str)

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except Exception:
            parsed = default
        return max(minimum, min(maximum, parsed))

    def _read_json_path(self, path: Path) -> Dict[str, Any]:
        try:
            if not path.exists():
                return {"available": False, "path": str(path), "reason": "missing"}
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "available": True,
                "path": str(path),
                "mtime": path.stat().st_mtime,
                "data": data,
            }
        except Exception as exc:
            return {
                "available": True,
                "path": str(path),
                "success": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }

    def _read_text_path(self, path: Path, max_chars: int = 5000) -> Dict[str, Any]:
        try:
            if not path.exists():
                return {"available": False, "path": str(path), "reason": "missing"}
            text = path.read_text(encoding="utf-8", errors="replace")
            truncated = len(text) > max_chars
            return {
                "available": True,
                "path": str(path),
                "mtime": path.stat().st_mtime,
                "truncated": truncated,
                "text": text[:max_chars],
                "omitted_chars": max(0, len(text) - max_chars),
            }
        except Exception as exc:
            return {
                "available": True,
                "path": str(path),
                "success": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }

    def _tail_jsonl_path(
        self,
        path: Path,
        max_lines: int = 10,
        max_line_chars: int = 2000,
    ) -> Dict[str, Any]:
        try:
            if not path.exists():
                return {"available": False, "path": str(path), "reason": "missing"}
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            selected = lines[-max_lines:]
            entries: List[Any] = []
            parse_errors: List[Dict[str, Any]] = []
            for line in selected:
                compact_line = line[:max_line_chars]
                try:
                    entries.append(json.loads(compact_line))
                except Exception as exc:
                    entries.append({"raw": compact_line})
                    parse_errors.append({
                        "error": str(exc),
                        "line_prefix": compact_line[:120],
                    })
            return {
                "available": True,
                "path": str(path),
                "mtime": path.stat().st_mtime,
                "line_count": len(lines),
                "returned": len(entries),
                "entries": entries,
                "parse_errors": parse_errors,
            }
        except Exception as exc:
            return {
                "available": True,
                "path": str(path),
                "success": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }

    # ------------------------------------------------------------------
    # Public BB7 compiled surfaces
    # ------------------------------------------------------------------

    def bb7_code_consciousness(
        self, arguments: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> str:
        """Architectural/context understanding through the live BB7 plane."""
        args = self._coerce_arguments(arguments, kwargs)
        operation = str(args.get("operation", "understand_intent"))
        if operation != "understand_intent":
            return self._json({
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "supported_operations": ["understand_intent"],
            })

        file_path = str(args.get("file_path") or args.get("path") or ".")
        query = str(args.get("query") or f"architectural intent and design role for {file_path}")
        max_depth = int(args.get("max_depth", 3))

        sources: Dict[str, Any] = {}
        candidate_path = Path(file_path).expanduser()
        if candidate_path.is_file() or file_path.endswith(".py"):
            sources["code_analysis"] = self._invoke_live_tool(
                "bb7_analyze_code_complete",
                {"file_path": file_path, "include_all": True},
            )
        else:
            sources["code_analysis"] = {
                "available": "bb7_analyze_code_complete" in self.tools,
                "skipped": True,
                "reason": "file_path_not_a_single_python_file",
            }

        sources["project_structure"] = self._invoke_live_tool(
            "bb7_analyze_project_structure",
            {"max_depth": max_depth, "include_hidden": bool(args.get("include_hidden", False))},
        )
        sources["memory_context"] = self._first_available_call(
            ["bb7_memory_intelligent_search", "bb7_memory_search"],
            {"query": query, "max_results": int(args.get("max_memories", 5))},
        )
        sources["lisan_recall"] = self._invoke_live_tool(
            "bb7_lisan_recall",
            {
                "context": query,
                "max_memories": int(args.get("max_memories", 5)),
                "include_plans": True,
                "include_activity": True,
                "include_decisions": True,
            },
        )

        return self._json({
            "success": True,
            "surface": "bb7_code_consciousness",
            "operation": operation,
            "file_path": file_path,
            "compiled_understanding": self._synthesize_architectural_intent(file_path, query, sources),
            "source_calls": sources,
        })

    def bb7_context_weaver(
        self, arguments: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> str:
        """Synthesize workspace, memory, session, and project context."""
        args = self._coerce_arguments(arguments, kwargs)
        operation = str(args.get("operation", "synthesize_context"))
        if operation != "synthesize_context":
            return self._json({
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "supported_operations": ["synthesize_context"],
            })

        context = str(args.get("context") or args.get("task") or "current workspace continuity")
        workspace_path = args.get("workspace_path")
        max_memories = int(args.get("max_memories", 7))

        workspace_args: Dict[str, Any] = {
            "include_recent_memories": True,
            "include_active_sessions": True,
        }
        if workspace_path:
            workspace_args["workspace_path"] = str(workspace_path)

        sources = {
            "workspace_context": self._invoke_live_tool("bb7_workspace_context_loader", workspace_args),
            "lisan_recall": self._invoke_live_tool(
                "bb7_lisan_recall",
                {
                    "context": context,
                    "max_memories": max_memories,
                    "include_plans": True,
                    "include_activity": True,
                    "include_decisions": True,
                },
            ),
            "session_resume": self._invoke_live_tool(
                "bb7_auto_session_resume",
                {"workspace_path": str(workspace_path)} if workspace_path else {},
            ),
            "memory_insights": self._first_available_call(
                ["bb7_memory_get_insights", "bb7_memory_surface_context"],
                {"query": context, "max_results": max_memories},
            ),
            "recent_changes": self._invoke_live_tool("bb7_get_recent_changes", {"days": int(args.get("days", 7))}),
        }

        return self._json({
            "success": True,
            "surface": "bb7_context_weaver",
            "operation": operation,
            "context": context,
            "synthesis": self._synthesize_context_state(context, sources),
            "source_calls": sources,
        })

    def bb7_creative_problem_solver(
        self, arguments: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> str:
        """Problem decomposition with Lisan/memory context when available."""
        args = self._coerce_arguments(arguments, kwargs)
        operation = str(args.get("operation", "decompose_challenge"))
        if operation != "decompose_challenge":
            return self._json({
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "supported_operations": ["decompose_challenge"],
            })

        problem = str(args.get("problem") or args.get("challenge") or args.get("prompt") or "").strip()
        if not problem:
            return self._json({
                "success": False,
                "error": "problem is required for decompose_challenge",
            })

        sources = {
            "intent_analysis": self._invoke_live_tool(
                "bb7_lisan_intend", {"user_message": problem, "verbosity": "normal"}
            ),
            "memory_context": self._first_available_call(
                ["bb7_memory_intelligent_search", "bb7_memory_search"],
                {"query": problem, "max_results": int(args.get("max_memories", 5))},
            ),
        }
        decomposition = self._decompose_problem(problem, args)

        return self._json({
            "success": True,
            "surface": "bb7_creative_problem_solver",
            "operation": operation,
            "problem": problem,
            "decomposition": decomposition,
            "source_calls": sources,
        })

    def bb7_muadib_mentat_bridge(
        self, arguments: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> str:
        """
        Compile a read-only one-plane snapshot across Muad'Dib, exoskeleton, and Mentat.

        This facade intentionally does not instantiate sibling tools, start a
        server, mutate checkpoints, or modify the MCP display adapter. It only
        calls already-registered BB7 surfaces and reads bounded Mentat sidecar
        artifacts. `mcp_server.py` is treated as the gateway/dispatcher into
        Muad'Dib + tools, not as the intelligence owner.
        """
        args = self._coerce_arguments(arguments, kwargs)
        operation = str(args.get("operation", "snapshot"))
        if operation != "snapshot":
            return self._json({
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "supported_operations": ["snapshot"],
            })

        workspace_path = Path(
            str(args.get("workspace_path") or self.repo_root)
        ).expanduser().resolve()
        max_insights = self._bounded_int(args.get("max_insights", 8), 8, 0, 50)
        max_handoff_chars = self._bounded_int(
            args.get("max_handoff_chars", 5000), 5000, 500, 20000
        )
        include_handoff = bool(args.get("include_handoff", True))
        include_insights = bool(args.get("include_insights", True))
        include_scope = bool(args.get("include_scope", True))
        include_live_calls = bool(args.get("include_live_calls", True))

        mentat_root = Path(
            str(args.get("mentat_root") or os.environ.get("MENTAT_HOME") or Path.home() / ".mentat")
        ).expanduser().resolve()
        requested_session = str(args.get("mentat_session_id") or "default")

        active_session = self._read_json_path(mentat_root / "active_session.json")
        latest_eval = self._read_json_path(mentat_root / "eval" / "latest.json")
        if requested_session == "latest":
            latest_data = latest_eval.get("data") if isinstance(latest_eval, dict) else {}
            requested_session = str(
                latest_data.get("session_id")
                if isinstance(latest_data, dict)
                else "default"
            )
        if not requested_session:
            requested_session = "default"

        mentat: Dict[str, Any] = {
            "root": str(mentat_root),
            "session_id": requested_session,
            "active_session": active_session,
            "latest_eval": latest_eval,
            "session_eval": self._read_json_path(
                mentat_root / "eval" / f"{requested_session}.eval.json"
            ),
            "q_table": {
                "available": (mentat_root / "q_table.sqlite").exists(),
                "path": str(mentat_root / "q_table.sqlite"),
                "bytes": (mentat_root / "q_table.sqlite").stat().st_size
                if (mentat_root / "q_table.sqlite").exists()
                else 0,
            },
        }
        if include_handoff:
            mentat["handoff"] = self._read_text_path(
                mentat_root / "handoff" / f"{requested_session}.md",
                max_chars=max_handoff_chars,
            )
        if include_insights:
            mentat["recent_insights"] = self._tail_jsonl_path(
                mentat_root / "insights" / f"{requested_session}.jsonl",
                max_lines=max_insights,
            )
        if include_scope:
            mentat["workspace_scope"] = self._read_text_path(
                workspace_path / ".mentat" / "scope.md",
                max_chars=4000,
            )
            mentat["workspace_active_session"] = self._read_json_path(
                workspace_path / ".mentat" / "active_session.json"
            )

        default_candidates = [
            "bb7_dt_checkpoint_status",
            "bb7_dt_self_play",
            "bb7_dt_self_play_lock",
            "bb7_dt_advanced_features",
            "bb7_exo_state",
            "bb7_exo_reflect",
            "bb7_lisan_recall",
            "bb7_context_weaver",
            "bb7_memory_store",
        ]
        candidates_arg = args.get("candidates") or default_candidates
        if isinstance(candidates_arg, str):
            candidates = [item.strip() for item in candidates_arg.split(",") if item.strip()]
        elif isinstance(candidates_arg, list):
            candidates = [str(item) for item in candidates_arg if str(item).strip()]
        else:
            candidates = default_candidates
        if not candidates:
            candidates = default_candidates

        source_calls: Dict[str, Any] = {}
        if include_live_calls:
            source_calls["muadib_checkpoint_status"] = self._invoke_live_tool(
                "bb7_dt_checkpoint_status", {}
            )
            source_calls["muadib_advanced_features"] = self._invoke_live_tool(
                "bb7_dt_advanced_features",
                {
                    "candidates": candidates,
                    "category": "meta_intelligence",
                    "session_id": f"mentat_bridge::{requested_session}",
                    "recent_tools": [
                        "bb7_lisan_recall",
                        "bb7_context_weaver",
                        "bb7_dt_checkpoint_status",
                    ],
                },
            )
            source_calls["exoskeleton_state"] = self._invoke_live_tool(
                "bb7_exo_state", {"limit": self._bounded_int(args.get("exo_limit", 5), 5, 1, 25)}
            )
            source_calls["tool_health"] = self._invoke_live_tool(
                "bb7_tool_health_report",
                {
                    "include_failed_loads": True,
                    "include_failed_calls": True,
                    "include_slow_tools": False,
                },
            )

        tool_health_result = source_calls.get("tool_health", {}).get("result")
        runtime_identity = (
            tool_health_result.get("runtime_identity")
            if isinstance(tool_health_result, dict)
            else None
        )

        return self._json({
            "success": True,
            "surface": "bb7_muadib_mentat_bridge",
            "operation": operation,
            "timestamp": time.time(),
            "workspace_path": str(workspace_path),
            "contract": {
                "runtime_plane": "Somnus-MCP/BB7/Lisan/MuadDib",
                "gateway_role": "mcp_server.py is the transport/registry/lifecycle gateway into Muad'Dib + tools",
                "cognition_plane_role": "muadib/ and tools/ own neural self-play, routing, reflection, memory synthesis, and answer compilation",
                "meta_facade_role": "registry_bound_read_model",
                "mentat_role": "observer_conductor_sidecar",
                "one_cognition_data_plane": True,
                "one_server_one_plane": True,
                "stdio_gateway_children_may_exist": True,
                "mcp_server_is_intelligence": False,
                "gateway_process_is_cognition_plane": False,
                "starts_server": False,
                "instantiates_sibling_tools": False,
                "mutates_muadib_weights": False,
                "mutates_qtable": False,
                "mutates_mcp_output_adapter": False,
                "raw_json_display_boundary": "unchanged",
            },
            "gateway": {
                "role": "gateway_dispatcher",
                "source": "bb7_tool_health_report.runtime_identity",
                "runtime_identity": runtime_identity,
                "identity_available": isinstance(runtime_identity, dict),
                "note": (
                    "Gateway identity identifies the answering transport/registry process; "
                    "it is not the Muad'Dib cognition plane itself."
                ),
            },
            "mentat": mentat,
            "source_calls": source_calls,
            "registered_bridge_candidates": {
                name: name in self.tools for name in candidates
            },
            "recommended_next": [
                "Use bb7_dt_checkpoint_status to inspect active Muad'Dib checkpoint/lock state.",
                "Use bb7_dt_self_play_lock when candidate self-play should continue but active/champion weights must stay pinned.",
                "Use Mentat notes, handoffs, and scope as conductor signals; do not route Muad'Dib weights or Q-table ownership through Mentat.",
                "Treat mcp_server.py as the gateway into Muad'Dib + tools, not as the intelligence layer itself.",
                "Do not edit mcp_server.py output formatting unless display-boundary truncation is proven in runtime output.",
            ],
        })

    # ------------------------------------------------------------------
    # Local synthesis helpers. These are intentionally deterministic and bounded.
    # ------------------------------------------------------------------

    def _synthesize_architectural_intent(
        self, file_path: str, query: str, sources: Dict[str, Any]
    ) -> Dict[str, Any]:
        path_text = file_path.lower()
        if "memory" in path_text or "session" in path_text:
            role = "continuity_substrate"
        elif "exo" in path_text or "lisan" in path_text or "muadib" in path_text:
            role = "routing_planning_substrate"
        elif "file" in path_text or "shell" in path_text or "web" in path_text:
            role = "capability_surface"
        elif "server" in path_text:
            role = "transport_and_orchestration_layer"
        else:
            role = "project_component"

        successful_sources = [k for k, v in sources.items() if isinstance(v, dict) and v.get("success")]
        unavailable_sources = [k for k, v in sources.items() if isinstance(v, dict) and v.get("available") is False]
        return {
            "inferred_role": role,
            "query": query,
            "evidence_sources": successful_sources,
            "unavailable_sources": unavailable_sources,
            "reading": (
                "Treat this module by its runtime role in the neural-symbolic server: "
                "continuity, routing, transport, or public capability surface."
            ),
        }

    def _synthesize_context_state(self, context: str, sources: Dict[str, Any]) -> Dict[str, Any]:
        active_sources = [k for k, v in sources.items() if isinstance(v, dict) and v.get("success")]
        missed_sources = [k for k, v in sources.items() if isinstance(v, dict) and not v.get("success")]
        return {
            "current_focus": context,
            "active_sources": active_sources,
            "missed_or_unavailable_sources": missed_sources,
            "continuity_doctrine": {
                "data_root": str(self.data_dir),
                "memory_session_are_substrate": True,
                "tool_plane": "live_registry_bound",
            },
            "next_move": "Use the returned Lisan/memory/session/workspace packets as a compiled context bundle before acting.",
        }

    def _decompose_problem(self, problem: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tokens = [t for t in self.TOKEN_RE.findall(problem) if len(t) > 2]
        sentences = [s.strip() for s in re.split(r"[.!?;\n]+", problem) if s.strip()]
        user_constraints = args.get("constraints") or []
        if isinstance(user_constraints, str):
            user_constraints = [user_constraints]
        goals = args.get("goals") or []
        if isinstance(goals, str):
            goals = [goals]

        inferred_constraints = []
        lowered = problem.lower()
        for marker, label in [
            ("without", "explicit exclusion"),
            ("must", "hard requirement"),
            ("never", "forbidden action"),
            ("always", "standing invariant"),
            ("only", "scope limiter"),
        ]:
            if marker in lowered:
                inferred_constraints.append(label)

        subproblems = []
        for idx, sentence in enumerate(sentences[:6], start=1):
            subproblems.append({
                "id": f"P{idx}",
                "statement": sentence,
                "recommended_lens": self._lens_for_sentence(sentence),
            })
        if not subproblems:
            subproblems.append({
                "id": "P1",
                "statement": problem,
                "recommended_lens": "clarify_target_state",
            })

        return {
            "core_terms": tokens[:20],
            "explicit_constraints": user_constraints,
            "explicit_goals": goals,
            "inferred_constraints": inferred_constraints,
            "subproblems": subproblems,
            "solution_lenses": [
                "preserve_runtime_invariants",
                "separate_source_truth_from_live_runtime_truth",
                "prefer_compatibility_aliases_before churn",
                "validate through mcp.venv and live BB7 plane",
            ],
            "next_steps": [
                "Lock invariants and forbidden actions.",
                "Patch the smallest source surfaces that carry the new capability.",
                "Validate source/schema truth without creating a second server plane.",
                "Ask the live BB7 plane for runtime health/parity after source validation.",
            ],
        }

    def _lens_for_sentence(self, sentence: str) -> str:
        text = sentence.lower()
        if any(word in text for word in ("memory", "session", "continuity")):
            return "continuity_substrate"
        if any(word in text for word in ("golden", "route", "lisan", "exo")):
            return "routing_oracle"
        if any(word in text for word in ("file", "schema", "manifest")):
            return "capability_contract"
        if any(word in text for word in ("validate", "test", "check")):
            return "verification"
        return "first_principles"

    # ------------------------------------------------------------------
    # MCP discovery surface
    # ------------------------------------------------------------------

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            "bb7_code_consciousness": {
                "function": self.bb7_code_consciousness,
                "description": (
                    "Registry-bound architectural consciousness: compiles code analysis, "
                    "project context, memory substrate, and Lisan recall without instantiating sibling tools."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["understand_intent"],
                            "default": "understand_intent",
                        },
                        "file_path": {"type": "string", "default": "."},
                        "query": {"type": "string"},
                        "max_depth": {"type": "integer", "default": 3},
                        "max_memories": {"type": "integer", "default": 5},
                        "include_hidden": {"type": "boolean", "default": False},
                    },
                    "required": [],
                },
            },
            "bb7_context_weaver": {
                "function": self.bb7_context_weaver,
                "description": (
                    "Registry-bound context synthesis across workspace, memory, session continuity, "
                    "recent changes, and Lisan context resurrection."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["synthesize_context"],
                            "default": "synthesize_context",
                        },
                        "context": {"type": "string"},
                        "task": {"type": "string"},
                        "workspace_path": {"type": "string"},
                        "max_memories": {"type": "integer", "default": 7},
                        "days": {"type": "integer", "default": 7},
                    },
                    "required": [],
                },
            },
            "bb7_creative_problem_solver": {
                "function": self.bb7_creative_problem_solver,
                "description": (
                    "Registry-bound problem decomposition that uses Lisan intent and memory context "
                    "when available, then emits bounded execution-ready subproblems."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["decompose_challenge"],
                            "default": "decompose_challenge",
                        },
                        "problem": {"type": "string"},
                        "challenge": {"type": "string"},
                        "prompt": {"type": "string"},
                        "constraints": {
                            "oneOf": [
                                {"type": "array", "items": {"type": "string"}},
                                {"type": "string"},
                            ]
                        },
                        "goals": {
                            "oneOf": [
                                {"type": "array", "items": {"type": "string"}},
                                {"type": "string"},
                            ]
                        },
                        "max_memories": {"type": "integer", "default": 5},
                    },
                    "required": ["problem"],
                },
            },
            "bb7_muadib_mentat_bridge": {
                "function": self.bb7_muadib_mentat_bridge,
                "description": (
                    "Read-only one-plane bridge snapshot across Muad'Dib checkpoint state, "
                    "exoskeleton health, and Mentat conductor artifacts. Uses the live registry "
                    "and bounded Mentat file reads; treats mcp_server.py as gateway into Muad'Dib/tools "
                    "and does not instantiate sibling tools or mutate weights, Q-table state, "
                    "server lifecycle, or output adapters."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["snapshot"],
                            "default": "snapshot",
                        },
                        "workspace_path": {"type": "string"},
                        "mentat_root": {"type": "string"},
                        "mentat_session_id": {
                            "type": "string",
                            "default": "default",
                            "description": "Mentat session id to inspect, or 'latest'.",
                        },
                        "max_insights": {"type": "integer", "default": 8},
                        "max_handoff_chars": {"type": "integer", "default": 5000},
                        "include_handoff": {"type": "boolean", "default": True},
                        "include_insights": {"type": "boolean", "default": True},
                        "include_scope": {"type": "boolean", "default": True},
                        "include_live_calls": {"type": "boolean", "default": True},
                        "exo_limit": {"type": "integer", "default": 5},
                        "candidates": {
                            "oneOf": [
                                {"type": "array", "items": {"type": "string"}},
                                {"type": "string"},
                            ]
                        },
                    },
                    "required": [],
                },
            },
        }
