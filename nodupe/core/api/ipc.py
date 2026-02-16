# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""IPC Module for Tool Programmatic Access.

Provides a Unix Domain Socket server that allows external programs to call
tool methods via JSON-RPC.
"""

import os
import json
import socket
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from ..tool_system.registry import ToolRegistry
from .codes import ActionCode, SENSITIVE_METHODS, RISK_LEVELS
from .ratelimit import RateLimiter

class ToolIPCServer:
    """Unix Domain Socket server for programmatic tool access."""

    def __init__(self, registry: ToolRegistry, socket_path: str = "/tmp/nodupe.sock"):
        """Initialize IPC server.

        Args:
            registry: Tool registry to look up tools
            socket_path: Path to the Unix Domain Socket
        """
        self.registry = registry
        self.socket_path = socket_path
        self._stop_event = threading.Event()
        self._server_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        
        # Enforce Log Policy: 1000 messages / 30 seconds
        # The RateLimiter uses a 60s window by default, so we'll adjust
        self.rate_limiter = RateLimiter(requests_per_minute=2000) # 2000/60s = 1000/30s

    def start(self) -> None:
        """Start the IPC server in a background thread."""
        if self._server_thread is not None:
            return

        # Clean up existing socket if any
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        self._stop_event.clear()
        self._server_thread = threading.Thread(
            target=self._run_server,
            name="ToolIPCServerThread",
            daemon=True
        )
        self._server_thread.start()
        self._log_event(ActionCode.FAU_GEN_START, f"Tool IPC Server started at {self.socket_path}")

    def stop(self) -> None:
        """Stop the IPC server."""
        if self._server_thread is None:
            return

        self._stop_event.set()
        # Connect to self to break the accept() loop
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(self.socket_path)
        except:
            pass

        self._server_thread.join(timeout=2.0)
        self._server_thread = None
        
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        self._log_event(ActionCode.FAU_GEN_STOP, "Tool IPC Server stopped")

    def _run_server(self) -> None:
        """Main server loop."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(self.socket_path)
            server.listen(5)
            server.settimeout(1.0)

            while not self._stop_event.is_set():
                try:
                    conn, _ = server.accept()
                    with conn:
                        self._handle_connection(conn)
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self._stop_event.is_set():
                        self._log_event(ActionCode.ERR_INTERNAL, f"IPC Server accept error: {e}", level="error")

    def _handle_connection(self, conn: socket.socket) -> None:
        """Handle a single client connection."""
        try:
            # Enforce Rate Limiting (Log Policy Compliance)
            if not self.rate_limiter.check_rate_limit("ipc_client"):
                self._log_event(ActionCode.RATE_LIMIT_HIT, "Rate limit exceeded for IPC client", level="warning")
                self._send_error(conn, "Rate limit exceeded", None, code=ActionCode.RATE_LIMIT_HIT)
                return

            data = conn.recv(4096)
            if not data:
                return

            try:
                request = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                self._log_event(ActionCode.ERR_INVALID_JSON, "Invalid JSON received", level="warning")
                self._send_error(conn, "Parse error", None, code=ActionCode.ERR_INVALID_JSON)
                return

            if request.get("jsonrpc") != "2.0":
                self._log_event(ActionCode.ERR_INVALID_REQUEST, "Missing or invalid jsonrpc version", level="warning")
                self._send_error(conn, "Invalid Request: Missing jsonrpc version", request.get("id"), code=ActionCode.ERR_INVALID_REQUEST)
                return

            tool_name = request.get("tool")
            method_name = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if not tool_name or not method_name:
                self._log_event(ActionCode.ERR_INVALID_REQUEST, "Missing tool or method", level="warning")
                self._send_error(conn, "Missing tool or method", request_id, code=ActionCode.ERR_INVALID_REQUEST)
                return

            self._log_event(ActionCode.FAU_SAR_REQ, f"Request: {tool_name}.{method_name}", tool=tool_name, method=method_name)

            # Security Risk Flagging
            action_code = SENSITIVE_METHODS.get(method_name, ActionCode.FAU_SAR_REQ)
            if action_code in RISK_LEVELS:
                risk = RISK_LEVELS[action_code]
                self._log_event(ActionCode.SECURITY_RISK_FLAGGED, 
                               f"Sensitive method '{method_name}' called on tool '{tool_name}'",
                               risk_level=risk, tool=tool_name, method=method_name)

            # Look up tool
            tool = self.registry.get_tool(tool_name)
            if not tool:
                self._log_event(ActionCode.ERR_TOOL_NOT_FOUND, f"Tool '{tool_name}' not found", level="warning")
                self._send_error(conn, f"Tool '{tool_name}' not found", request_id, code=ActionCode.ERR_TOOL_NOT_FOUND)
                return

            # Check if method is exposed via api_methods
            exposed_methods = getattr(tool, 'api_methods', {})
            if method_name not in exposed_methods:
                self._log_event(ActionCode.ERR_METHOD_NOT_FOUND, f"Method '{method_name}' not exposed", level="warning")
                self._send_error(conn, f"Method '{method_name}' not exposed by tool '{tool_name}'", request_id, code=ActionCode.ERR_METHOD_NOT_FOUND)
                return

            # Call method
            try:
                method = exposed_methods[method_name]
                result = method(**params)
                self._log_event(ActionCode.FAU_SAR_RES, f"Success: {tool_name}.{method_name}")
                self._send_response(conn, result, request_id)
            except Exception as e:
                self._log_event(ActionCode.ERR_EXEC_FAILED, f"Execution failed: {str(e)}", level="error")
                self._send_error(conn, f"Method execution failed: {str(e)}", request_id, code=ActionCode.ERR_EXEC_FAILED)

        except Exception as e:
            self._log_event(ActionCode.ERR_INTERNAL, f"IPC Connection error: {e}", level="error")

    def _log_event(self, code: ActionCode, message: str, level: str = "info", **kwargs) -> None:
        """Log structured event with Action Code and context."""
        context = {
            "action_code": int(code),
            "action_name": code.name,
            **kwargs
        }
        # Format for persistent logging
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        log_msg = f"[{code}] {message} | {context_str}"
        
        log_method = getattr(self.logger, level.lower())
        log_method(log_msg)

    def _send_response(self, conn: socket.socket, result: Any, request_id: Any) -> None:
        """Send successful JSON-RPC 2.0 response."""
        response = {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
        conn.sendall(json.dumps(response).encode('utf-8'))

    def _send_error(self, conn: socket.socket, message: str, request_id: Any, code: int = -32000) -> None:
        """Send standard JSON-RPC 2.0 error response."""
        # Convert internal ActionCode to standard JSON-RPC code if applicable
        rpc_code = ActionCode.to_jsonrpc_code(code) if code >= 100000 else code
        
        response = {
            "jsonrpc": "2.0",
            "error": {
                "code": rpc_code,
                "message": message,
                "data": {"action_code": code} # Preserve 6-digit internal code for LUT lookup
            },
            "id": request_id
        }
        conn.sendall(json.dumps(response).encode('utf-8'))
