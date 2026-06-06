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

def read_payload() -> dict:
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}

def write_additional_context(msg: str) -> None:
    if len(msg) > 4096:
        msg = msg[:4000] + "\n…[sovereign: truncated]"
    sys.stdout.write(json.dumps({"hookSpecificOutput": {"additionalContext": msg}}))
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
