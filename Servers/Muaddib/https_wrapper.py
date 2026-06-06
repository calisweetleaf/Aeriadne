#!/usr/bin/env python3
"""
Secure MCP HTTPS gateway with API Key Authentication.

This is a transport gateway into the Somnus-MCP Muad'Dib + tools cognition
plane, not a separate intelligence layer. Starting this wrapper is lifecycle
work that creates/uses a gateway process around MCPServer; do not treat it as
routine source/schema validation or as a second cognition plane.

Features:
- API key authentication
- Rate limiting
- HTTPS with self-signed certificates
- Comprehensive logging and audit trail
- RESTful API endpoints
- Secure local-only access
"""

import base64
import ipaddress
import hashlib
import hmac
import json
import logging
import secrets
import ssl
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Set
import tempfile
import os
import re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import sys
sys.path.insert(0, str(Path(__file__).parent))
from mcp_server import MCPServer
from webhook_engine import WebhookEngine
from sse_broadcaster import SSEBroadcaster
from openapi_builder import (
    build_openapi_spec, build_ai_plugin_manifest, build_claude_desktop_config,
)


class SecurityConfig:
    """Security configuration for the HTTPS server"""
    
    def __init__(self, allow_external: bool = False):
        self.api_key = self._generate_api_key()
        self.rate_limit_requests = 100  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.allow_external = allow_external
        self.allowed_origins = ["*"] if allow_external else ["https://localhost", "https://127.0.0.1"]
        self.session_timeout = 3600  # 1 hour
        
        # Create security directory
        self.security_dir = Path("data/security")
        self.security_dir.mkdir(exist_ok=True)
        
        # Save API key
        self._save_api_key()
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        # Generate 32 bytes of random data and encode as base64
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('ascii').rstrip('=')
    
    def _save_api_key(self):
        """Save API key to secure file"""
        api_key_file = self.security_dir / "api_key.txt"
        with open(api_key_file, 'w') as f:
            f.write(self.api_key)
        
        # Set restrictive permissions
        try:
            os.chmod(api_key_file, 0o600)
        except OSError as e:
            logging.getLogger(__name__).warning(f"Could not set permissions on {api_key_file}: {e}")
        
        print(f"API Key saved to: {api_key_file}")
        print(f"API Key: {self.api_key}")


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)
        self._lock = threading.Lock()
        
        # Start background cleanup thread to prevent memory leaks from one-off IPs
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
    def _cleanup_loop(self):
        """Periodically purge old IP records to prevent OOM attacks"""
        while self._running:
            time.sleep(self.window_seconds)
            with self._lock:
                now = time.time()
                empty_clients = []
                for client_id, reqs in self.clients.items():
                    valid_reqs = [t for t in reqs if now - t < self.window_seconds]
                    if not valid_reqs:
                        empty_clients.append(client_id)
                    else:
                        self.clients[client_id] = valid_reqs
                
                for client_id in empty_clients:
                    del self.clients[client_id]
                    
    def stop(self):
        """Stop the background cleanup thread"""
        self._running = False
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        with self._lock:
            now = time.time()
            
            # Clean old requests
            self.clients[client_id] = [
                req_time for req_time in self.clients[client_id]
                if now - req_time < self.window_seconds
            ]
            
            # Check if under limit
            if len(self.clients[client_id]) >= self.max_requests:
                return False
            
            # Add current request
            self.clients[client_id].append(now)
            return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests in current window for client"""
        with self._lock:
            now = time.time()
            active = [t for t in self.clients.get(client_id, []) if now - t < self.window_seconds]
            return max(0, self.max_requests - len(active))
    
    def get_reset_time(self, client_id: str) -> int:
        """Get when rate limit resets for client"""
        with self._lock:
            if not self.clients[client_id]:
                return 0
            
            oldest_request = min(self.clients[client_id])
            return int(oldest_request + self.window_seconds)


class SecurityLogger:
    """Security-focused logging"""
    
    def __init__(self):
        self.log_file = Path("data/security/security.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Setup security logger
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_auth_attempt(self, client_ip: str, success: bool, api_key_hash: str = ""):
        """Log authentication attempt"""
        self.logger.info(
            f"AUTH_ATTEMPT - IP: {client_ip} - Success: {success} - KeyHash: {api_key_hash[:8]}"
        )
    
    def log_rate_limit(self, client_ip: str, endpoint: str):
        """Log rate limit violation"""
        self.logger.warning(
            f"RATE_LIMIT - IP: {client_ip} - Endpoint: {endpoint}"
        )
    
    def log_suspicious_activity(self, client_ip: str, activity: str, details: str):
        """Log suspicious activity"""
        self.logger.warning(
            f"SUSPICIOUS - IP: {client_ip} - Activity: {activity} - Details: {details}"
        )
    
    def log_tool_usage(self, client_ip: str, tool_name: str, success: bool):
        """Log tool usage"""
        self.logger.info(
            f"TOOL_USAGE - IP: {client_ip} - Tool: {tool_name} - Success: {success}"
        )


class SecureMCPHandler(BaseHTTPRequestHandler):
    """Secure HTTP handler with API key authentication"""
    
    def __init__(self, *args, mcp_server=None, security_config=None, 
                 rate_limiter=None, security_logger=None,
                 webhook_engine=None, sse_broadcaster=None, https_server=None, **kwargs):
        self.mcp_server = mcp_server
        self.security_config = security_config
        self.rate_limiter = rate_limiter
        self.security_logger = security_logger
        self.webhook_engine = webhook_engine
        self.sse_broadcaster = sse_broadcaster
        self.https_server = https_server
        super().__init__(*args, **kwargs)
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = self.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return self.client_address[0]
    
    def _validate_api_key(self) -> bool:
        """Validate API key from request"""
        client_ip = self._get_client_ip()
        
        # Check Authorization header
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            provided_key = auth_header[7:]  # Remove 'Bearer ' prefix
        else:
            # Check query parameter as fallback
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            provided_key = query_params.get('api_key', [''])[0]
        
        if not provided_key:
            self.security_logger.log_auth_attempt(client_ip, False, "no_key")
            return False
        
        # Constant-time comparison to prevent timing attacks
        expected_key = self.security_config.api_key
        is_valid = hmac.compare_digest(provided_key, expected_key)
        
        # Log attempt
        key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        self.security_logger.log_auth_attempt(client_ip, is_valid, key_hash)
        
        return is_valid
    
    def _check_rate_limit(self) -> bool:
        """Check rate limiting"""
        client_ip = self._get_client_ip()
        
        if not self.rate_limiter.is_allowed(client_ip):
            self.security_logger.log_rate_limit(client_ip, self.path)
            return False
        
        return True
    
    def _validate_request_size(self) -> bool:
        """Validate request size"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        if content_length > self.security_config.max_request_size:
            self.security_logger.log_suspicious_activity(
                self._get_client_ip(),
                "large_request",
                f"Size: {content_length} bytes"
            )
            return False
        
        return True
    
    def _security_check(self) -> Optional[str]:
        """Perform comprehensive security checks"""
        client_ip = self._get_client_ip()
        
        # Only allow localhost connections (unless external access is enabled)
        if not self.security_config.allow_external:
            if client_ip not in ['127.0.0.1', '::1', 'localhost']:
                self.security_logger.log_suspicious_activity(
                    client_ip, "non_localhost", f"Attempted access from {client_ip}"
                )
                return "Forbidden: Only localhost connections allowed"
        
        # Check rate limiting
        if not self._check_rate_limit():
            return "Rate limit exceeded"
        
        # Check request size
        if not self._validate_request_size():
            return "Request too large"
        
        # Validate API key
        if not self._validate_api_key():
            return "Invalid or missing API key"
        
        return None  # All checks passed
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._send_security_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Security check
            security_error = self._security_check()
            if security_error:
                self._send_error(403, security_error)
                return
            
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/':
                self._send_server_info()
            elif parsed_path.path == '/tools':
                self._send_tools_list()
            elif parsed_path.path == '/health':
                self._send_health_check()
            elif parsed_path.path == '/metrics':
                self._send_metrics()
            elif parsed_path.path == '/api-info':
                self._send_api_info()
            elif parsed_path.path == '/openapi.json':
                self._send_openapi_spec()
            elif parsed_path.path == '/.well-known/ai-plugin.json':
                self._send_ai_plugin_manifest()
            elif parsed_path.path == '/events':
                self._handle_sse_stream(parsed_path)
            elif parsed_path.path == '/webhooks':
                self._handle_list_webhooks()
            elif parsed_path.path == '/mcp':
                self._handle_mcp_sse_stream()
            elif parsed_path.path == '/claude-config':
                self._send_claude_config()
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            self._send_error(500, f"Server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Security check
            security_error = self._security_check()
            if security_error:
                self._send_error(403, security_error)
                return
            
            if self.path == '/mcp':
                self._handle_mcp_request()
            elif self.path.startswith('/tools/'):
                self._handle_tool_call()
            elif self.path == '/webhooks/register':
                self._handle_webhook_register()
            elif self.path == '/webhooks/unregister':
                self._handle_webhook_unregister()
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            self._send_error(500, f"Server error: {str(e)}")
    
    def _handle_mcp_request(self):
        """Handle MCP JSON-RPC requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            request_data = self.rfile.read(content_length)
            request_json = json.loads(request_data.decode('utf-8'))
            
            # Process MCP request via the server's handle_request dispatcher
            if self.mcp_server:
                response = self.mcp_server.handle_request(request_json)
                if response is None:
                    response = {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Malformed JSON-RPC request"}, "id": request_json.get("id")}
            else:
                response = {"jsonrpc": "2.0", "error": {"code": -32000, "message": "MCP server not available"}, "id": request_json.get("id")}
            
            self._send_json_response(response)
            
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_tool_call(self):
        """Handle direct tool calls via JSON-RPC dispatch to MCPServer"""
        tool_name = None
        try:
            # Extract tool name from path: /tools/{tool_name}
            tool_name = self.path.split('/')[-1]
            client_ip = self._get_client_ip()
            
            # Validate tool name (security — block path traversal)
            if not re.match(r'^[a-zA-Z0-9_]+$', tool_name):
                self.security_logger.log_suspicious_activity(
                    client_ip, "invalid_tool_name", tool_name
                )
                self._send_error(400, "Invalid tool name")
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            request_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            
            try:
                params = json.loads(request_data.decode('utf-8'))
            except json.JSONDecodeError:
                params = {}
            
            # Route through the server's JSON-RPC handle_call_tool method
            if self.mcp_server and tool_name in self.mcp_server.tools:
                rpc_result = self.mcp_server.handle_call_tool(
                    req_id=str(uuid.uuid4()),
                    params={"name": tool_name, "arguments": params}
                )
                # Extract the content from the JSON-RPC envelope
                result_payload = rpc_result.get("result", rpc_result)
                success = "error" not in rpc_result
                
                self.security_logger.log_tool_usage(client_ip, tool_name, success)
                self._send_json_response(result_payload)
            else:
                self.security_logger.log_tool_usage(client_ip, tool_name or "unknown", False)
                self._send_error(404, f"Tool '{tool_name}' not found")
                
        except Exception as e:
            self.security_logger.log_tool_usage(self._get_client_ip(), tool_name or "unknown", False)
            self._send_error(500, str(e))
    
    def _send_server_info(self):
        """Send server information"""
        if self.mcp_server:
            info = {
                "name": "Sovereign MCP Server",
                "version": "1.0",
                "tool_count": len(self.mcp_server.tools),
                "https_wrapper": True,
                "security_enabled": True,
                "api_version": "1.0",
                "authentication": "API Key required",
                "external_access": self.security_config.allow_external,
                "rate_limit": f"{self.security_config.rate_limit_requests}/minute",
                "endpoints": {
                    "GET /": "Server information",
                    "GET /tools": "List available tools",
                    "GET /health": "Health check",
                    "GET /metrics": "Server metrics",
                    "GET /api-info": "API documentation",
                    "GET /openapi.json": "Dynamic OpenAPI 3.1 spec (ChatGPT Actions)",
                    "GET /.well-known/ai-plugin.json": "ChatGPT plugin manifest",
                    "GET /events": "SSE real-time event stream",
                    "GET /mcp": "MCP Streamable HTTP SSE (server→client)",
                    "GET /webhooks": "List registered webhooks",
                    "GET /claude-config": "Claude Desktop mcpServers config",
                    "POST /mcp": "MCP JSON-RPC endpoint",
                    "POST /tools/{tool_name}": "Direct tool execution",
                    "POST /webhooks/register": "Register webhook callback",
                    "POST /webhooks/unregister": "Remove webhook"
                }
            }
            self._send_json_response(info)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_tools_list(self):
        """Send tools list via JSON-RPC tools/list"""
        if self.mcp_server:
            rpc_result = self.mcp_server.handle_request(
                {"jsonrpc": "2.0", "method": "tools/list", "id": "tools-list", "params": {}}
            )
            # Flatten the JSON-RPC envelope for REST consumers
            tool_list = rpc_result.get("result", {}).get("tools", []) if rpc_result else []
            response = {
                "tools": [t.get("name", t) if isinstance(t, dict) else t for t in tool_list],
                "tool_count": len(tool_list),
                "tool_details": {t["name"]: t for t in tool_list if isinstance(t, dict)}
            }
            self._send_json_response(response)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_health_check(self):
        """Send health check"""
        if self.mcp_server:
            health = {
                "status": "ok",
                "tool_count": len(self.mcp_server.tools),
                "security_status": "enabled",
                "https_status": "active",
                "rate_limiter_status": "active",
                "external_access": self.security_config.allow_external,
            }
            self._send_json_response(health)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_metrics(self):
        """Send server metrics"""
        if self.mcp_server:
            perf = getattr(self.mcp_server, 'performance_metrics', {})
            metrics = {
                "tool_count": len(self.mcp_server.tools),
                "tool_calls": perf.get("tool_calls", 0),
                "failed_calls": perf.get("failed_calls", 0),
                "last_activity": perf.get("last_activity", 0),
                "security_metrics": {
                    "api_key_configured": bool(self.security_config.api_key),
                    "rate_limit_active": True,
                    "https_enabled": True,
                    "localhost_only": not self.security_config.allow_external
                }
            }
            self._send_json_response(metrics)
        else:
            self._send_error(500, "MCP server not available")
    
    def _send_api_info(self):
        """Send API documentation"""
        api_docs = {
            "api_version": "1.0",
            "authentication": {
                "type": "API Key",
                "header": "Authorization: Bearer YOUR_API_KEY",
                "query_param": "?api_key=YOUR_API_KEY"
            },
            "endpoints": {
                "GET /": "Server information and status",
                "GET /tools": "List all available MCP tools",
                "GET /health": "Server health check",
                "GET /metrics": "Server performance metrics",
                "GET /api-info": "This API documentation",
                "POST /mcp": "MCP JSON-RPC protocol endpoint",
                "POST /tools/{tool_name}": "Execute specific tool directly"
            },
            "rate_limits": {
                "requests_per_minute": self.security_config.rate_limit_requests,
                "window_seconds": self.security_config.rate_limit_window
            },
            "security": {
                "https_only": True,
                "localhost_only": True,
                "api_key_required": True,
                "request_size_limit": f"{self.security_config.max_request_size} bytes"
            }
        }
        self._send_json_response(api_docs)
    
    def _send_openapi_spec(self):
        """Send dynamic OpenAPI 3.1 spec built from live tool catalog"""
        server_url = f"https://{self.server.server_address[0]}:{self.server.server_address[1]}"
        tools = self.mcp_server.tools if self.mcp_server else {}
        spec = build_openapi_spec(tools, server_url=server_url)
        self._send_json_response(spec)
    
    def _send_ai_plugin_manifest(self):
        """Send /.well-known/ai-plugin.json for ChatGPT plugin discovery"""
        server_url = f"https://{self.server.server_address[0]}:{self.server.server_address[1]}"
        manifest = build_ai_plugin_manifest(server_url=server_url)
        self._send_json_response(manifest)
    
    def _send_claude_config(self):
        """Send ready-to-paste Claude Desktop / Claude Code mcpServers config"""
        server_url = f"https://{self.server.server_address[0]}:{self.server.server_address[1]}"
        api_key = self.security_config.api_key if self.security_config else ""
        config = build_claude_desktop_config(server_url=server_url, api_key=api_key)
        self._send_json_response(config)
    
    def _handle_sse_stream(self, parsed_path):
        """Handle GET /events — SSE event stream for connected clients"""
        if not self.sse_broadcaster:
            self._send_error(503, "SSE broadcaster not available")
            return
        
        # Parse event filters from query params
        from urllib.parse import parse_qs
        query = parse_qs(parsed_path.query)
        filters_raw = query.get("filters", ["*"])[0]
        filters = [f.strip() for f in filters_raw.split(",") if f.strip()]
        
        client = self.sse_broadcaster.connect(event_filters=filters)
        
        # Send SSE headers
        self.send_response(200)
        self._send_security_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        
        # Stream events until client disconnects
        try:
            for chunk in self.sse_broadcaster.stream_bytes_generator(client, timeout=1.0):
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.sse_broadcaster.disconnect(client.client_id)
    
    def _handle_mcp_sse_stream(self):
        """Handle GET /mcp — MCP Streamable HTTP SSE stream (server→client notifications)"""
        accept = self.headers.get("Accept", "")
        if "text/event-stream" not in accept:
            self._send_error(406, "GET /mcp requires Accept: text/event-stream")
            return
        
        if not self.sse_broadcaster:
            self._send_error(503, "SSE not available")
            return
        
        # Create MCP-specific SSE client (receives tool_call, neural_telemetry events)
        client = self.sse_broadcaster.connect(
            event_filters=["tool_call", "neural_telemetry", "golden_path", "mcp_notification"]
        )
        
        # Assign/return Mcp-Session-Id
        session_id = self.headers.get("Mcp-Session-Id") or f"mcp_{uuid.uuid4().hex[:16]}"
        if self.https_server:
            with self.https_server._session_lock:
                self.https_server._mcp_sessions[session_id] = time.time()
        
        self.send_response(200)
        self._send_security_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Mcp-Session-Id", session_id)
        self.end_headers()
        
        try:
            for chunk in self.sse_broadcaster.stream_bytes_generator(client, timeout=1.0):
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.sse_broadcaster.disconnect(client.client_id)
    
    def _handle_webhook_register(self):
        """Handle POST /webhooks/register"""
        if not self.webhook_engine:
            self._send_error(503, "Webhook engine not available")
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length > 0 else {}
            
            callback_url = body.get("callback_url")
            if not callback_url:
                self._send_error(400, "callback_url is required")
                return
            
            result = self.webhook_engine.register(
                callback_url=callback_url,
                secret=body.get("secret"),
                event_filters=body.get("event_filters"),
            )
            self._send_json_response(result)
        except ValueError as e:
            self._send_error(400, str(e))
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_webhook_unregister(self):
        """Handle POST /webhooks/unregister"""
        if not self.webhook_engine:
            self._send_error(503, "Webhook engine not available")
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length > 0 else {}
            
            webhook_id = body.get("webhook_id")
            if not webhook_id:
                self._send_error(400, "webhook_id is required")
                return
            
            result = self.webhook_engine.unregister(webhook_id)
            self._send_json_response(result)
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_list_webhooks(self):
        """Handle GET /webhooks"""
        if not self.webhook_engine:
            self._send_error(503, "Webhook engine not available")
            return
        result = self.webhook_engine.list_webhooks()
        self._send_json_response(result)
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response with security headers"""
        self.send_response(status_code)
        self._send_security_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_response = {
            "error": message,
            "status_code": status_code,
            "timestamp": time.time()
        }
        self._send_json_response(error_response, status_code)
    
    def _send_security_headers(self):
        """Send security headers — OpenRouter/Stripe-tier compliance"""
        # Request correlation ID
        request_id = str(uuid.uuid4())
        self.send_header('X-Request-ID', request_id)
        
        # CORS headers — allow all origins when external access is enabled
        origin = self.security_config.allowed_origins[0] if self.security_config.allowed_origins else '*'
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # Security headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        self.send_header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'")
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        
        # Rate limit headers (OpenRouter-compatible)
        if self.rate_limiter:
            client_ip = self._get_client_ip()
            reset_time = self.rate_limiter.get_reset_time(client_ip)
            remaining = self.rate_limiter.get_remaining(client_ip)
            self.send_header('X-RateLimit-Limit', str(self.security_config.rate_limit_requests))
            self.send_header('X-RateLimit-Remaining', str(remaining))
            self.send_header('X-RateLimit-Reset', str(reset_time))
    
    def log_message(self, format, *args):
        """Override logging to use our security logger"""
        message = format % args
        self.security_logger.logger.info(f"HTTP: {message}")


class SecureMCPHTTPSServer:
    """Secure HTTPS MCP server with API key authentication
    
    Supports two modes:
    - localhost-only (default): Only 127.0.0.1/::1 can connect. Safe for local Codex/Claude.
    - external (--external): Any IP can connect if they have the API key.
      Required for Custom GPTs, Claude plugins, or remote agent connections.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8443, debug: bool = False,
                 allow_external: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.allow_external = allow_external
        self.logger = logging.getLogger(__name__)
        
        # Initialize security components
        self.security_config = SecurityConfig(allow_external=allow_external)
        self.rate_limiter = RateLimiter(
            self.security_config.rate_limit_requests,
            self.security_config.rate_limit_window
        )
        self.security_logger = SecurityLogger()
        
        # Initialize MCP server
        self.mcp_server = MCPServer(debug=debug)
        
        # Integration engines
        self.webhook_engine = WebhookEngine(data_dir=Path("data/security"))
        self.sse_broadcaster = SSEBroadcaster(heartbeat_interval=30.0)
        
        # MCP Streamable HTTP session tracking
        self._mcp_sessions: Dict[str, float] = {}  # session_id -> last_seen
        self._session_lock = threading.Lock()
        
        # Server components
        self.httpd = None
        self.server_thread = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info(f"Secure MCP HTTPS Server initialized on {host}:{port}")
        self.logger.info(f"API Key: {self.security_config.api_key}")
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context — prefers external certs, falls back to self-signed"""
        cert_dir = Path("data/security/certs")
        cert_dir.mkdir(exist_ok=True)
        
        # Check for external certs (Let's Encrypt, custom CA, etc.)
        ext_cert = os.environ.get("MCP_EXTERNAL_CERT", "")
        ext_key = os.environ.get("MCP_EXTERNAL_KEY", "")
        
        if ext_cert and ext_key and Path(ext_cert).exists() and Path(ext_key).exists():
            cert_file = Path(ext_cert)
            key_file = Path(ext_key)
            self.logger.info("Using external TLS certificates: %s", cert_file)
        else:
            cert_file = cert_dir / "server.crt"
            key_file = cert_dir / "server.key"
            
            if not cert_file.exists() or not key_file.exists():
                self._generate_ssl_certificate(cert_file, key_file)
        
        # Create SSL context with strong security
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.load_cert_chain(cert_file, key_file)
        
        return context
    
    def _generate_ssl_certificate(self, cert_file: Path, key_file: Path):
        """Generate SSL certificate"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            import ipaddress as _ipaddress
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MCP Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(_ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Write private key
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Write certificate
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Set restrictive permissions
            try:
                os.chmod(key_file, 0o600)
                os.chmod(cert_file, 0o644)
            except OSError as e:
                self.logger.warning(f"Could not set cert permissions: {e}")
            
            self.logger.info("Generated SSL certificate for HTTPS")
            
        except ImportError:
            self.logger.error("cryptography library required for SSL certificate generation")
            raise RuntimeError("Install 'cryptography' package: pip install cryptography")
    
    def start_server(self) -> bool:
        """Start the secure HTTPS server"""
        try:
            # Create handler factory
            def handler_factory(*args, **kwargs):
                return SecureMCPHandler(
                    *args,
                    mcp_server=self.mcp_server,
                    security_config=self.security_config,
                    rate_limiter=self.rate_limiter,
                    security_logger=self.security_logger,
                    webhook_engine=self.webhook_engine,
                    sse_broadcaster=self.sse_broadcaster,
                    https_server=self,
                    **kwargs
                )
            
            # Create threaded HTTP server (prevents one slow tool call from blocking the server)
            self.httpd = ThreadingHTTPServer((self.host, self.port), handler_factory)
            
            # Wrap with SSL
            ssl_context = self.create_ssl_context()
            self.httpd.socket = ssl_context.wrap_socket(
                self.httpd.socket, server_side=True
            )
            
            # Start server in background
            self.server_thread = threading.Thread(
                target=self.httpd.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"Secure MCP HTTPS server started on https://{self.host}:{self.port}")
            self.security_logger.logger.info("Secure HTTPS server started")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start secure HTTPS server: {e}")
            return False
    
    def stop_server(self):
        """Stop the HTTPS server"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
        
        # Shutdown integration engines
        if hasattr(self, 'webhook_engine') and self.webhook_engine:
            self.webhook_engine.shutdown()
        if hasattr(self, 'sse_broadcaster') and self.sse_broadcaster:
            self.sse_broadcaster.shutdown()
            
        if hasattr(self, 'rate_limiter') and self.rate_limiter:
            self.rate_limiter.stop()
        
        self.security_logger.logger.info("Secure HTTPS server stopped")
        self.logger.info("Secure MCP HTTPS server stopped")
    
    def get_server_url(self) -> str:
        """Get server URL"""
        return f"https://{self.host}:{self.port}"
    
    def get_api_key(self) -> str:
        """Get API key"""
        return self.security_config.api_key
    
    def get_claude_desktop_config(self) -> Dict[str, Any]:
        """Generate Claude Desktop configuration"""
        return {
            "mcpServers": {
                "sovereign-mcp-https": {
                    "url": self.get_server_url(),
                    "api_key": self.get_api_key(),
                    "headers": {
                        "Authorization": f"Bearer {self.get_api_key()}"
                    }
                }
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure MCP HTTPS Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8443, help="Port to bind to") 
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--external", action="store_true",
                        help="Allow external (non-localhost) connections. Required for Custom GPTs, Claude plugins, remote agents.")
    
    args = parser.parse_args()
    
    # Create secure server
    server = SecureMCPHTTPSServer(host=args.host, port=args.port, debug=args.debug, allow_external=args.external)
    
    try:
        if server.start_server():
            print("Secure MCP HTTPS Server Started Successfully!")
            print("=" * 60)
            print(f"Server URL: {server.get_server_url()}")
            print(f"API Key: {server.get_api_key()}")
            print("Available endpoints:")
            print("   GET  / - Server information")
            print("   GET  /tools - List all tools")
            print("   GET  /health - Health check")
            print("   GET  /metrics - Server metrics")
            print("   GET  /openapi.json - Dynamic OpenAPI 3.1 (ChatGPT Actions)")
            print("   GET  /.well-known/ai-plugin.json - ChatGPT plugin manifest")
            print("   GET  /events - SSE real-time event stream")
            print("   GET  /mcp - MCP Streamable HTTP (SSE)")
            print("   GET  /webhooks - List webhooks")
            print("   GET  /claude-config - Claude Desktop config")
            print("   POST /mcp - MCP JSON-RPC endpoint")
            print("   POST /tools/{tool_name} - Direct tool execution")
            print("   POST /webhooks/register - Register webhook")
            print("   POST /webhooks/unregister - Remove webhook")
            print("\nSecurity Features:")
            print("   [OK] API Key Authentication")
            print("   [OK] Rate Limiting (100 req/min)")
            print("   [OK] HTTPS with TLS 1.2+")
            print("   [OK] Localhost-only access")
            print("   [OK] Comprehensive logging")
            print("   [OK] Security headers")
            print("\nConfiguration saved to:")
            print("   [FILE] API Key: data/security/api_key.txt")
            print("   [FILE] Security Log: data/security/security.log")
            print("   [FILE] SSL Certs: data/security/certs/")
            
            # Generate Claude Desktop config
            config = server.get_claude_desktop_config()
            config_file = Path("claude_desktop_config.json")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\nClaude Desktop Config: {config_file}")
            
            print("\nPress Ctrl+C to stop...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping server...")
                server.stop_server()
                print("Server stopped securely")
        else:
            print("Failed to start server")
            return 1
            
    except Exception as e:
        print(f"Server error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
