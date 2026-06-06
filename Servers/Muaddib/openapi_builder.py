#!/usr/bin/env python3
"""
OpenAPI Schema Builder — Sovereign MCP Server

Generates a complete OpenAPI 3.1 spec from the live mcp_server.tools dict.
This powers:
  - ChatGPT Custom GPT Actions (paste /openapi.json into GPT editor)
  - Claude Plugin discovery
  - Any OpenAPI-consuming client (Swagger UI, Postman, etc.)

Also generates:
  - /.well-known/ai-plugin.json (ChatGPT plugin manifest)
  - Claude Desktop mcpServers config block
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _sanitize_operation_id(tool_name: str) -> str:
    """
    Convert a bb7_ tool name to a valid OpenAPI operationId.
    ChatGPT Actions require operationIds matching ^[a-zA-Z0-9_-]+$
    """
    # Strip bb7_ prefix for cleaner operation IDs
    clean = tool_name.replace("bb7_", "", 1) if tool_name.startswith("bb7_") else tool_name
    # Replace any non-alphanumeric chars with underscore
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", clean)
    return clean or tool_name


def _extract_input_schema(tool_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract or build a JSON Schema from a tool's registration info.
    Handles both 'inputSchema' dict format and legacy 'parameters' list format.
    """
    # Preferred: inputSchema already present
    if isinstance(tool_info.get("inputSchema"), dict):
        schema = dict(tool_info["inputSchema"])
        schema.setdefault("type", "object")
        return schema

    # Legacy: parameters list → convert to JSON Schema
    params = tool_info.get("parameters", [])
    if isinstance(params, list) and params:
        properties = {}
        required = []
        for p in params:
            if isinstance(p, dict):
                name = p.get("name", "")
                if not name:
                    continue
                prop: Dict[str, Any] = {}
                prop["type"] = p.get("type", "string")
                if "description" in p:
                    prop["description"] = p["description"]
                if "default" in p:
                    prop["default"] = p["default"]
                if "enum" in p:
                    prop["enum"] = p["enum"]
                properties[name] = prop
                if p.get("required", False):
                    required.append(name)
        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    # Fallback: no-param tool
    return {"type": "object", "properties": {}}


def build_openapi_spec(
    tools: Dict[str, Any],
    server_url: str = "https://localhost:8443",
    title: str = "Sovereign MCP HTTPS API",
    version: str = "2.0.0",
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a complete OpenAPI 3.1 spec from the live tools dict.

    Each tool gets a POST /tools/{tool_name} path with:
      - Unique operationId (ChatGPT requirement)
      - Full input schema from tool registration
      - Description from tool metadata
      - Bearer auth requirement

    Also includes the /mcp JSON-RPC gateway, /health, /events SSE endpoint.
    """
    tool_count = len(tools)
    desc = description or (
        f"Sovereign MCP neural tool server exposing {tool_count} AI orchestration tools "
        f"via authenticated HTTPS. Supports JSON-RPC 2.0 (POST /mcp), "
        f"direct REST tool invocation (POST /tools/{{name}}), SSE events (GET /events), "
        f"and webhook subscriptions (POST /webhooks/register)."
    )

    paths: Dict[str, Any] = {}

    # ── Static endpoints ──────────────────────────────────────────────────

    paths["/health"] = {
        "get": {
            "operationId": "healthCheck",
            "summary": "Server health check",
            "description": "Returns server status, tool count, and security state.",
            "responses": {
                "200": {
                    "description": "Server is healthy",
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "tool_count": {"type": "integer"},
                        },
                    }}},
                },
            },
        },
    }

    paths["/tools"] = {
        "get": {
            "operationId": "listAllTools",
            "summary": "List all available MCP tools",
            "description": "Returns the full tool catalog with names and descriptions.",
            "responses": {
                "200": {
                    "description": "Tool catalog",
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "tools": {"type": "array", "items": {"type": "string"}},
                            "tool_count": {"type": "integer"},
                        },
                    }}},
                },
            },
        },
    }

    paths["/mcp"] = {
        "post": {
            "operationId": "mcpJsonRpc",
            "summary": "MCP JSON-RPC 2.0 gateway",
            "description": "Send any JSON-RPC 2.0 request (initialize, tools/list, tools/call).",
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {
                    "type": "object",
                    "properties": {
                        "jsonrpc": {"type": "string", "const": "2.0"},
                        "method": {"type": "string", "description": "JSON-RPC method"},
                        "id": {"description": "Request ID (string or integer)"},
                        "params": {"type": "object", "description": "Method parameters"},
                    },
                    "required": ["jsonrpc", "method"],
                }}},
            },
            "responses": {
                "200": {"description": "JSON-RPC response"},
            },
        },
        "get": {
            "operationId": "mcpStreamableHTTP",
            "summary": "MCP Streamable HTTP — SSE stream for server notifications",
            "description": "Establish an SSE connection for real-time server→client messages.",
            "responses": {
                "200": {
                    "description": "SSE event stream",
                    "content": {"text/event-stream": {}},
                },
            },
        },
    }

    paths["/events"] = {
        "get": {
            "operationId": "sseEventStream",
            "summary": "Real-time SSE event stream",
            "description": "Stream tool calls, neural telemetry, and webhook events in real-time.",
            "parameters": [
                {
                    "name": "filters",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "description": "Comma-separated event type filters (default: all)",
                },
            ],
            "responses": {
                "200": {
                    "description": "SSE event stream",
                    "content": {"text/event-stream": {}},
                },
            },
        },
    }

    # Webhook endpoints
    paths["/webhooks/register"] = {
        "post": {
            "operationId": "registerWebhook",
            "summary": "Register a webhook callback",
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {
                    "type": "object",
                    "properties": {
                        "callback_url": {"type": "string", "format": "uri"},
                        "secret": {"type": "string", "description": "HMAC signing secret (auto-generated if omitted)"},
                        "event_filters": {"type": "array", "items": {"type": "string"}, "description": "Event types to subscribe to (default: all)"},
                    },
                    "required": ["callback_url"],
                }}},
            },
            "responses": {"200": {"description": "Webhook registered"}},
        },
    }

    paths["/webhooks/unregister"] = {
        "post": {
            "operationId": "unregisterWebhook",
            "summary": "Remove a webhook registration",
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {
                    "type": "object",
                    "properties": {"webhook_id": {"type": "string"}},
                    "required": ["webhook_id"],
                }}},
            },
            "responses": {"200": {"description": "Webhook removed"}},
        },
    }

    paths["/webhooks"] = {
        "get": {
            "operationId": "listWebhooks",
            "summary": "List all registered webhooks",
            "responses": {"200": {"description": "Webhook list"}},
        },
    }

    # ── Per-tool endpoints ────────────────────────────────────────────────

    for tool_name, tool_info in sorted(tools.items()):
        if not isinstance(tool_info, dict):
            continue

        op_id = _sanitize_operation_id(tool_name)
        description = tool_info.get("description", f"Execute {tool_name}")
        input_schema = _extract_input_schema(tool_info)

        paths[f"/tools/{tool_name}"] = {
            "post": {
                "operationId": op_id,
                "summary": f"Execute {tool_name}",
                "description": description[:500],
                "requestBody": {
                    "required": False,
                    "content": {"application/json": {"schema": input_schema}},
                },
                "responses": {
                    "200": {"description": "Tool execution result"},
                    "404": {"description": "Tool not found"},
                    "403": {"description": "Authentication failed"},
                    "429": {"description": "Rate limit exceeded"},
                },
            },
        }

    # ── Assemble spec ─────────────────────────────────────────────────────

    spec: Dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "description": desc,
            "version": version,
            "contact": {"name": "Sovereign MCP"},
        },
        "servers": [{"url": server_url, "description": "Sovereign MCP HTTPS Gateway"}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API key via Authorization: Bearer header",
                },
            },
        },
        "security": [{"BearerAuth": []}],
    }

    logger.info(
        "OpenAPI spec built: %d paths (%d tool endpoints)",
        len(paths), tool_count,
    )
    return spec


def build_ai_plugin_manifest(
    server_url: str = "https://localhost:8443",
    plugin_name: str = "Sovereign MCP",
    plugin_description: str = "Neural MCP tool server with 100+ AI orchestration tools",
    contact_email: str = "admin@sovereign-mcp.local",
    legal_info_url: str = "",
) -> Dict[str, Any]:
    """
    Generate the /.well-known/ai-plugin.json manifest for ChatGPT plugin discovery.

    See: https://platform.openai.com/docs/plugins/getting-started
    """
    return {
        "schema_version": "v1",
        "name_for_human": plugin_name,
        "name_for_model": "sovereign_mcp",
        "description_for_human": plugin_description,
        "description_for_model": (
            "A neural MCP tool server that provides AI orchestration tools including "
            "memory management, file operations, shell execution, web tools, "
            "session management, code analysis, and autonomous learning. "
            "Use the listAllTools operation first to discover available tools."
        ),
        "auth": {
            "type": "service_http",
            "authorization_type": "bearer",
            "verification_tokens": {},
        },
        "api": {
            "type": "openapi",
            "url": f"{server_url}/openapi.json",
        },
        "logo_url": f"{server_url}/logo.png",
        "contact_email": contact_email,
        "legal_info_url": legal_info_url or f"{server_url}/legal",
    }


def build_claude_desktop_config(
    server_url: str = "https://localhost:8443",
    api_key: str = "",
    server_name: str = "sovereign-mcp",
) -> Dict[str, Any]:
    """
    Generate the mcpServers config block for Claude Desktop / Claude Code.

    Paste this into ~/.config/claude/settings.json (or equivalent).
    """
    return {
        "mcpServers": {
            server_name: {
                "type": "http",
                "url": f"{server_url}/mcp",
                "headers": {
                    "Authorization": f"Bearer {api_key}",
                },
            },
        },
    }
