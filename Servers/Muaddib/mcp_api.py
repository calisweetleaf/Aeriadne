# mcp_api.py
import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict  # Import Any from typing
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
import sys
from pathlib import Path
import inspect
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Local MCP server (JSON-RPC dispatcher)
from mcp_server import MCPServer

# --- CONFIG ---
API_KEY = os.environ.get("MCP_API_KEY", "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8")  # set via env for security
MAX_EXECUTION_SECONDS = int(os.environ.get("MCP_MAX_EXEC_SECONDS", "30"))
# Disable timeouts entirely when MCP_DISABLE_TIMEOUTS is set to '1' (useful for local dev / power users)
MCP_DISABLE_TIMEOUTS = os.environ.get("MCP_DISABLE_TIMEOUTS", "0") == "1"
CERT_PATH = os.environ.get("MCP_CERT_PATH", "cert.pem")
KEY_PATH = os.environ.get("MCP_KEY_PATH", "key.pem")

# Add project root to path so we can import your tool modules
sys.path.append(str(Path(__file__).parent))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP API Server", version="1.0")

# Allow localhost only (you're not exposing to internet)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH MIDDLEWARE ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    # Support Authorization: Bearer <token> header as an alternative
    if not api_key:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            api_key = auth.split(" ", 1)[1].strip()

    if api_key != API_KEY:
        logger.warning(f"Unauthorized access attempt from {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    response = await call_next(request)
    return response

# --- LOAD YOUR TOOLS DYNAMICALLY ---
# Assuming your tools are in ./tools/ directory, each with a .py file and callable functions
# Example: tools/memory_tool.py has function bb7_memory_store()
# We'll auto-discover all tools matching pattern bb7_*

TOOLS_DIR = Path("./tools")
tool_registry = {}

if TOOLS_DIR.exists():
    for py_file in TOOLS_DIR.glob("*.py"):
        module_name = py_file.stem
        try:
            module = __import__(f"tools.{module_name}", fromlist=[""])
            # Look for any function starting with 'bb7_'
            for attr_name in dir(module):
                if attr_name.startswith("bb7_") and callable(getattr(module, attr_name)):
                    tool_registry[attr_name] = getattr(module, attr_name)
                    logger.info(f"Loaded tool: {attr_name} from {module_name}.py")
        except Exception as e:
            logger.error(f"Failed to load {py_file}: {e}")

logger.info(f"Total tools loaded: {len(tool_registry)}")
# Thread pool used to run blocking tools without blocking the event loop
EXECUTOR = ThreadPoolExecutor(max_workers=int(os.environ.get("MCP_EXECUTOR_WORKERS", "6")))

# Single in-process MCP JSON-RPC server instance (reuses full tool stack)
MCP_DEBUG = os.environ.get("MCP_DEBUG", "0") == "1"
mcp_server = MCPServer(debug=MCP_DEBUG)
rpc_lock = asyncio.Lock()

# SSE broadcaster for streaming events
from sse_broadcaster import SSEBroadcaster
from openapi_builder import build_openapi_spec, build_ai_plugin_manifest

sse_broadcaster = SSEBroadcaster(heartbeat_interval=30.0)

# MCP session tracking
_mcp_sessions: Dict[str, float] = {}

# --- REQUEST MODEL ---
class MCPRequest(BaseModel):
    tool_name: str
    args: dict = {}
    session_id: Optional[str] = None

# --- RESPONSE MODEL (FIXED) ---
class MCPResponse(BaseModel):
    success: bool
    result: Optional[Any] = None  # FIXED: Use Any (capital A) instead of any
    error: Optional[str] = None

# --- MAIN ENDPOINT ---
@app.post("/execute", response_model=MCPResponse)
async def execute_tool(request: MCPRequest):
    tool_name = request.tool_name
    args = request.args or {}

    if tool_name not in tool_registry:
        return MCPResponse(success=False, error=f"Tool '{tool_name}' not found.")

    func = tool_registry[tool_name]

    # Filter args to function signature to avoid unexpected kwargs
    try:
        sig = inspect.signature(func)
        filtered_args = {}
        for name, param in sig.parameters.items():
            if name in args:
                filtered_args[name] = args[name]
    except Exception:
        filtered_args = args

    try:
        # Execute without enforced timeout per user request
        if asyncio.iscoroutinefunction(func):
            result = await func(**filtered_args)
        else:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(EXECUTOR, lambda: func(**filtered_args))
        return MCPResponse(success=True, result=result)
    except Exception as e:
        logger.exception(f"Error executing {tool_name}")
        return MCPResponse(success=False, error=str(e))

# --- JSON-RPC BRIDGE ---
@app.post("/rpc")
async def rpc_gateway(request: Request):
    """
    JSON-RPC 2.0 over HTTPS endpoint that forwards to the in-process MCPServer.
    Supports single-request objects; batches return HTTP 400 to avoid partial ambiguity.
    """
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Enforce JSON-RPC object (no batch) for clarity with GPT clients
    if isinstance(payload, list):
        raise HTTPException(status_code=400, detail="Batch requests are not supported")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON-RPC request must be an object")

    async with rpc_lock:
        response = mcp_server.handle_request(payload)

    if response is None:
        raise HTTPException(status_code=400, detail="Malformed JSON-RPC request")
    
    # MCP Streamable HTTP: assign session ID
    import uuid as _uuid
    session_id = request.headers.get("Mcp-Session-Id") or f"mcp_{_uuid.uuid4().hex[:16]}"
    _mcp_sessions[session_id] = __import__('time').time()
    
    resp = JSONResponse(content=response)
    resp.headers["Mcp-Session-Id"] = session_id
    return resp

# --- HEALTH CHECK ---
@app.get("/health")
async def health():
    ssl_enabled = os.path.exists(CERT_PATH) and os.path.exists(KEY_PATH)
    return {
        "status": "ok",
        "tools_loaded": len(tool_registry),
        "api_key_set": bool(API_KEY),
        "ssl_enabled": ssl_enabled,
        "timeouts_enforced": False,
        "executor_workers": getattr(EXECUTOR, '_max_workers', None)
    }

# --- LIST TOOLS ---
@app.get("/tools")
async def list_tools():
    return {"tools": list(tool_registry.keys())}


# --- SSE EVENT STREAM ---
@app.get("/mcp/stream")
async def mcp_sse_stream(request: Request):
    """MCP Streamable HTTP — SSE event stream for server→client notifications."""
    client = sse_broadcaster.connect(
        event_filters=["tool_call", "neural_telemetry", "golden_path", "mcp_notification"]
    )

    async def event_generator():
        try:
            for msg in sse_broadcaster.stream_generator(client, timeout=1.0):
                if await request.is_disconnected():
                    break
                yield msg
        finally:
            sse_broadcaster.disconnect(client.client_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- DYNAMIC OPENAPI ---
@app.get("/openapi-live.json")
async def live_openapi():
    """Dynamic OpenAPI 3.1 spec built from the live tool catalog."""
    spec = build_openapi_spec(
        mcp_server.tools,
        server_url="https://localhost:8000",
        title="Sovereign MCP FastAPI Gateway",
    )
    return JSONResponse(content=spec)


# --- CHATGPT PLUGIN MANIFEST ---
@app.get("/.well-known/ai-plugin.json")
async def ai_plugin_manifest():
    """ChatGPT plugin discovery manifest."""
    manifest = build_ai_plugin_manifest(server_url="https://localhost:8000")
    return JSONResponse(content=manifest)


# --- RUN SERVER ---
if __name__ == "__main__":
    # Generate self-signed cert if needed for HTTPS (optional)
    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        logger.info("No SSL cert found. Running on HTTP for development.")
        uvicorn.run("mcp_api:app", host="127.0.0.1", port=8000, reload=False)
    else:
        logger.info("Running MCP API with HTTPS...")
        uvicorn.run(
            "mcp_api:app",
            host="127.0.0.1",
            port=8000,
            ssl_certfile=CERT_PATH,
            ssl_keyfile=KEY_PATH,
            reload=False
        )
