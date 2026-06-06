"""Sovereign hook helper — calls SovereignMCP bb7_ tools safely from Codex hooks.

Hook scripts must write only Codex hook JSON to stdout.  This helper therefore
captures SovereignMCP startup/log chatter while invoking tools directly through
the local MCPServer class.  It intentionally keeps persistence rooted at the
canonical SOVEREIGN_DATA_DIR (/home/daeron/Somnus-MCP/data by default).
"""
from __future__ import annotations
import atexit, contextlib, io, json, os, subprocess, sys, time
from pathlib import Path

SOVEREIGN_ROOT = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data")).parent
MCP_PYTHON = str(SOVEREIGN_ROOT / "mcp.venv/bin/python")
MCP_SERVER = str(SOVEREIGN_ROOT / "mcp_server.py")
_SERVER = None
_LAST_PAYLOAD: dict = {}

# Codex 0.136 validates hook stdout against per-event schemas.  Hook-specific
# output objects that include additionalContext must carry the matching
# hookEventName const; several events (for example PreCompact/Stop) do not allow
# hookSpecificOutput at all.  This table keeps helper output schema-safe.
ADDITIONAL_CONTEXT_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "SubagentStart",
}
SCRIPT_EVENT_BY_STEM = {
    "session_start": "SessionStart",
    "user_prompt_submit": "UserPromptSubmit",
    "pre_tool_use": "PreToolUse",
    "post_tool_use": "PostToolUse",
    "pre_compact": "PreCompact",
    "post_compact": "PostCompact",
    "subagent_start": "SubagentStart",
    "subagent_stop": "SubagentStop",
    "stop": "Stop",
}

def read_payload() -> dict:
    global _LAST_PAYLOAD
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    _LAST_PAYLOAD = payload
    return payload

def _infer_hook_event() -> str:
    if isinstance(_LAST_PAYLOAD, dict):
        for key in ("hook_event_name", "hookEventName"):
            value = _LAST_PAYLOAD.get(key)
            if isinstance(value, str) and value:
                return value
    return SCRIPT_EVENT_BY_STEM.get(Path(sys.argv[0]).stem, "")

def write_additional_context(msg: str, hook_event_name: str | None = None) -> None:
    """Emit Codex schema-valid additionalContext for events that support it.

    Codex's hook output schemas require hookSpecificOutput.hookEventName for
    UserPromptSubmit/SessionStart/SubagentStart/etc.  Unsupported events return
    no stdout rather than emitting JSON that Codex will reject.
    """
    if not msg:
        return
    event = hook_event_name or _infer_hook_event()
    if event not in ADDITIONAL_CONTEXT_EVENTS:
        return
    if len(msg) > 4096:
        msg = msg[:4000] + "\n…[sovereign: truncated]"
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": msg,
        }
    }))
    sys.stdout.flush()

def _unwrap_mcp_response(resp: dict) -> dict:
    if not isinstance(resp, dict) or resp.get("error"):
        return {}
    result = resp.get("result", {})
    if isinstance(result, dict) and isinstance(result.get("content"), list):
        blocks = result.get("content") or []
        if blocks and isinstance(blocks[0], dict):
            text = blocks[0].get("text", "")
            if isinstance(text, str) and text.strip():
                try:
                    parsed = json.loads(text)
                    return parsed if isinstance(parsed, dict) else {"value": parsed}
                except Exception:
                    return {"text": text}
    return result if isinstance(result, dict) else {"value": result}

def _get_server():
    global _SERVER
    if _SERVER is None:
        sys.path.insert(0, str(SOVEREIGN_ROOT))
        from mcp_server import MCPServer  # type: ignore[import]
        _SERVER = MCPServer(debug=False, transport="stdio")
    return _SERVER

def _shutdown_server() -> None:
    global _SERVER
    if _SERVER is not None:
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                _SERVER.shutdown()
        except Exception:
            pass
        _SERVER = None

atexit.register(_shutdown_server)

def call_bb7(tool: str, args: dict, timeout: float = 4.0) -> dict:
    """Call a bb7_ tool on SovereignMCP.

    Direct import is preferred because the MCP stdio protocol requires an
    initialize/list/call exchange; sending a lone tools/call frame commonly
    returns nothing.  The caller-provided timeout is still respected by the
    outer Codex hook timeout configured in hooks.json.
    """
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            server = _get_server()
            resp = server.handle_call_tool(1, {"name": tool, "arguments": args or {}})
        return _unwrap_mcp_response(resp)
    except Exception as e:
        log_error(f"call_bb7:{tool}:direct", e)

    # Best-effort fallback: still safe and quiet, but may return empty on old
    # MCPServer builds that require a full initialize handshake.
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args or {}}})
    try:
        r = subprocess.run(
            [MCP_PYTHON, MCP_SERVER],
            input=req, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        return _unwrap_mcp_response(json.loads(r.stdout)) if r.stdout.strip() else {}
    except Exception as e:
        log_error(f"call_bb7:{tool}:subprocess", e)
        return {}

def log_error(ctx: str, exc: BaseException) -> None:
    log_dir = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data")) / "hook_errors"
    log_dir.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [sovereign/{ctx}] {type(exc).__name__}: {exc}\n"
    try:
        with (log_dir / "errors.log").open("a") as f:
            f.write(line)
    except Exception:
        pass

def safe_main(ctx: str, fn):
    try:
        return fn()
    except SystemExit:
        raise
    except BaseException as e:
        log_error(ctx, e)
        return 0
