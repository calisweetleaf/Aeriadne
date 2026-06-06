"""stdio MCP server for Mentat. Speaks JSON-RPC 2.0 over stdin/stdout.

Implements MCP protocol version 2025-06-18. Minimal: tools/list, tools/call,
initialize, initialized notification. No resources / prompts / sampling /
elicitation in this first cut — they're easy adds once the surface is
proven.

Run as:
    python3 -m mcp_server         # from plugin root
    python3 ${CLAUDE_PLUGIN_ROOT}/mcp_server/__main__.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Make the plugin's state_machine package importable.
_HERE = Path(__file__).resolve().parent
_PLUGIN_ROOT = _HERE.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine import (  # noqa: E402
    Insight,
    InsightBus,
    InsightType,
    QTable,
    State,
)
from state_machine.session import home_root, load_session, save_session, active_session_id  # noqa: E402
from state_machine.drift import detect_drift, parse_scope  # noqa: E402


PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "mentat"
SERVER_VERSION = "0.1.0"


# ---- tool definitions ---------------------------------------------------

TOOLS: list[dict] = [
    {
        "name": "mentat_state_get",
        "description": (
            "Get the current Mentat state machine snapshot for the active "
            "session. Returns state, transitions, chain_depth, last_tool, "
            "drift_count, and the active scope.md path if present."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "mentat_state_set",
        "description": (
            "Force the state machine into a specific state. Use sparingly — "
            "the FSA normally transitions automatically based on tool events. "
            "Useful for declaring REFLECTING explicitly before a debrief."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": [s.value for s in State],
                    "description": "Target state",
                },
                "reason": {"type": "string", "description": "Why the manual transition"},
            },
            "required": ["state"],
            "additionalProperties": False,
        },
    },
    {
        "name": "mentat_insight_emit",
        "description": (
            "Push a structured insight to the bus. Common types: DECISION "
            "(architectural choice), CONTRADICTION (claim vs claim), "
            "SOURCE_GROUNDED (claim tied to file/line), NOTE (free-form)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [t.value for t in InsightType],
                },
                "payload": {"type": "object"},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
    },
    {
        "name": "mentat_insight_query",
        "description": "Filter the insight bus by type and/or state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "state": {"type": "string"},
                "limit": {"type": "integer", "default": 50},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "mentat_insight_tail",
        "description": "Get the most recent N insights from the bus.",
        "inputSchema": {
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 30}},
            "additionalProperties": False,
        },
    },
    {
        "name": "mentat_q_route",
        "description": (
            "Recommend a tool for the current state via Thompson sampling over "
            "the persistent Q-table. Returns the recommended tool name and the "
            "expected Q-value, plus the top-3 alternatives by visit-weighted score."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "candidate_tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Restrict the recommendation to these tools",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "mentat_q_table",
        "description": "Dump the full Q-table (state × tool × value × visits).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "mentat_handoff_read",
        "description": "Read the latest pre-compact handoff snapshot, if any.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "mentat_handoff_write",
        "description": "Manually snapshot session state to handoff.md (normally pre_compact does this automatically).",
        "inputSchema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "mentat_drift_check",
        "description": "Run scope-drift detection against arbitrary text. Returns a hit object or null.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
    },
]


# ---- handlers -----------------------------------------------------------

def _ctx() -> tuple[str, Any, Any, Any]:
    sid = active_session_id() or "default"
    session = load_session(sid)
    qt = QTable(home_root() / "q_table.sqlite")
    bus = InsightBus(home_root(), sid)
    return sid, session, qt, bus


def call_tool(name: str, args: dict) -> dict:
    sid, session, qt, bus = _ctx()
    if name == "mentat_state_get":
        scope_path = ""
        proj = os.environ.get("CLAUDE_PROJECT_DIR")
        if proj:
            sp = Path(proj) / ".mentat" / "scope.md"
            if sp.exists():
                scope_path = str(sp)
        return {
            "session_id": sid,
            "state": session.state.value,
            "transitions": session.transition_count,
            "chain_depth": session.chain_depth,
            "drift_count": session.drift_count,
            "last_tool": session.last_tool,
            "last_tool_success": session.last_tool_success,
            "scope_path": scope_path,
        }

    if name == "mentat_state_set":
        target = State(args["state"])
        prev = session.state
        session.state = target
        save_session(session)
        bus.emit_state_transition(prev.value, target.value,
                                  trigger=f"manual:{args.get('reason', '-')}")
        return {"prev": prev.value, "current": target.value}

    if name == "mentat_insight_emit":
        ins = Insight(
            type=InsightType(args["type"]),
            payload=args.get("payload", {}),
            state=session.state.value,
        )
        bus.emit(ins)
        return {"id": ins.id, "seq": ins.seq}

    if name == "mentat_insight_query":
        type_arg = args.get("type")
        state_arg = args.get("state")
        limit = int(args.get("limit", 50))
        results = bus.query(
            type=InsightType(type_arg) if type_arg else None,
            state=state_arg,
            limit=limit,
        )
        return {"count": len(results), "insights": [json.loads(r.to_json()) for r in results]}

    if name == "mentat_insight_tail":
        n = int(args.get("n", 30))
        results = bus.tail(n)
        return {"count": len(results), "insights": [json.loads(r.to_json()) for r in results]}

    if name == "mentat_q_route":
        candidates = args.get("candidate_tools") or []
        recommendation = qt.thompson_recommend(session.state, candidates) if candidates else None
        if not recommendation:
            best = qt.best(session.state)
            recommendation = best[0] if best else None
        rows = [r for r in qt.dump() if r["state"] == session.state.value][:3]
        return {
            "state": session.state.value,
            "recommendation": recommendation,
            "top_3": rows,
        }

    if name == "mentat_q_table":
        return {"rows": qt.dump()}

    if name == "mentat_handoff_read":
        path = home_root() / "handoff" / f"{sid}.md"
        if not path.exists():
            return {"exists": False, "content": ""}
        return {"exists": True, "content": path.read_text(encoding="utf-8")}

    if name == "mentat_handoff_write":
        path = home_root() / "handoff" / f"{sid}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            f"# Manual handoff — {sid}\n\n"
            f"- State: {session.state.value}\n"
            f"- Reason: {args.get('reason', '-')}\n"
            f"- At: {time.time()}\n"
        )
        path.write_text(content, encoding="utf-8")
        bus.emit(Insight(type=InsightType.HANDOFF_WRITE,
                         state=session.state.value,
                         payload={"manual": True, "reason": args.get("reason", "")}))
        return {"path": str(path)}

    if name == "mentat_drift_check":
        proj = os.environ.get("CLAUDE_PROJECT_DIR")
        if not proj:
            return {"error": "no CLAUDE_PROJECT_DIR set"}
        sp = Path(proj) / ".mentat" / "scope.md"
        if not sp.exists():
            return {"error": "no scope.md in project"}
        _, out = parse_scope(sp)
        hit = detect_drift(args["text"], out)
        if not hit:
            return {"hit": None}
        return {"hit": {
            "topic": hit.topic, "phrase": hit.matched_phrase, "snippet": hit.snippet,
        }}

    raise ValueError(f"unknown tool: {name}")


# ---- JSON-RPC framing ---------------------------------------------------

def write_message(msg: dict) -> None:
    sys.stdout.write(json.dumps(msg, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def read_message() -> dict | None:
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def handle(req: dict) -> dict | None:
    method = req.get("method")
    rid = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        try:
            result = call_tool(name, args)
            return {
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "content": [{"type": "text", "text": str(e)}],
                    "isError": True,
                },
            }
    if rid is not None:
        return {
            "jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    return None


def main() -> int:
    while True:
        msg = read_message()
        if msg is None:
            return 0
        resp = handle(msg)
        if resp is not None:
            write_message(resp)


if __name__ == "__main__":
    sys.exit(main())
