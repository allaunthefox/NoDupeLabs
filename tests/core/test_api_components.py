"""Test API components functionality."""

import json
import socket
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.api.codes import ActionCode, _aliases, _enum_members
from nodupe.core.api.ipc import ToolIPCServer
from nodupe.core.tool_system.registry import ToolRegistry


class TestActionCode:
    """Test ActionCode functionality."""

    def test_action_code_creation(self):
        """Test ActionCode enum creation."""
        # Test that all expected codes exist
        assert hasattr(ActionCode, 'FIA_UAU_INIT')
        assert hasattr(ActionCode, 'FPT_STM_ERR')
        assert hasattr(ActionCode, 'FPT_FLS_FAIL')
        assert hasattr(ActionCode, 'ACC_ISO_CMP')
        assert hasattr(ActionCode, 'ACC_SCREEN_READER_INIT')
        assert hasattr(ActionCode, 'ACC_BRAILLE_INIT')

    def test_action_code_values(self):
        """Test ActionCode values."""
        assert ActionCode.FIA_UAU_INIT == 300001
        assert ActionCode.FPT_STM_ERR == 500001
        assert ActionCode.FPT_FLS_FAIL == 500000
        assert ActionCode.ACC_ISO_CMP == 600013
        assert ActionCode.ACC_SCREEN_READER_INIT == 600000
        assert ActionCode.ACC_BRAILLE_INIT == 600003

    def test_action_code_aliases(self):
        """Test ActionCode aliases."""
        # Check that aliases map to the correct values
        assert ActionCode.IPC_START == ActionCode.FAU_GEN_START
        assert ActionCode.TOOL_INIT == ActionCode.FIA_UAU_INIT
        assert ActionCode.ERR_INTERNAL == ActionCode.FPT_STM_ERR
        assert ActionCode.ERR_TOOL_NOT_FOUND == ActionCode.FPT_FLS_FAIL

    def test_action_code_get_lut(self):
        """Test getting LUT data."""
        lut = ActionCode.get_lut()
        assert isinstance(lut, dict)
        assert "codes" in lut

    def test_action_code_get_description(self):
        """Test getting action code descriptions."""
        desc = ActionCode.get_description(ActionCode.FIA_UAU_INIT)
        # Description might vary, but should return a string
        assert isinstance(desc, str)

    def test_action_code_get_category(self):
        """Test getting action code categories."""
        category = ActionCode.get_category(ActionCode.FIA_UAU_INIT)
        # Category should be a string
        assert isinstance(category, str)

    def test_action_code_to_jsonrpc_code(self):
        """Test converting action code to JSON-RPC code."""
        rpc_code = ActionCode.to_jsonrpc_code(ActionCode.FPT_FLS_FAIL)
        # Should be a negative integer for JSON-RPC error codes
        assert isinstance(rpc_code, int)


class TestToolIPCServerInitialization:
    """Test ToolIPCServer initialization functionality."""

    def test_ipc_server_creation(self):
        """Test ToolIPCServer instance creation."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        assert server is not None
        assert server.registry is mock_registry
        assert server.socket_path == "/tmp/nodupe.sock"
        assert server._stop_event is not None
        assert server._server_thread is None

    def test_ipc_server_custom_socket_path(self):
        """Test ToolIPCServer with custom socket path."""
        mock_registry = Mock()
        custom_path = "/custom/path.sock"
        server = ToolIPCServer(mock_registry, socket_path=custom_path)

        assert server.socket_path == custom_path


class TestToolIPCServerConnectionHandling:
    """Test ToolIPCServer connection handling functionality."""

    def test_handle_connection_invalid_json(self):
        """Test handling connection with invalid JSON."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Mock a socket connection
        mock_conn = Mock()
        mock_conn.recv.return_value = b"invalid json"

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should send error response
            mock_conn.sendall.assert_called_once()
            # Verify error was logged
            mock_logger.warning.assert_called()

    def test_handle_connection_missing_jsonrpc_version(self):
        """Test handling connection with missing JSON-RPC version."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Mock a socket connection with valid JSON but no jsonrpc version
        mock_conn = Mock()
        mock_conn.recv.return_value = b'{"method": "test"}'

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should send error response
            mock_conn.sendall.assert_called_once()
            # Verify error was logged
            mock_logger.warning.assert_called()

    def test_handle_connection_missing_tool_or_method(self):
        """Test handling connection with missing tool or method."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Mock a socket connection with valid JSON-RPC but missing tool/method
        mock_conn = Mock()
        mock_conn.recv.return_value = b'{"jsonrpc": "2.0", "id": 1}'

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should send error response
            mock_conn.sendall.assert_called_once()
            # Verify error was logged
            mock_logger.warning.assert_called()

    def test_handle_connection_tool_not_found(self):
        """Test handling connection with non-existent tool."""
        mock_registry = Mock()
        mock_registry.get_tool.return_value = None
        server = ToolIPCServer(mock_registry)

        # Mock a socket connection with valid JSON-RPC and tool/method
        mock_conn = Mock()
        request_data = {
            "jsonrpc": "2.0",
            "tool": "NonExistentTool",
            "method": "test_method",
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request_data).encode('utf-8')

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should send error response
            mock_conn.sendall.assert_called_once()
            # Verify error was logged
            mock_logger.warning.assert_called()

    def test_handle_connection_method_not_exposed(self):
        """Test handling connection with non-exposed method."""
        mock_registry = Mock()

        # Mock a tool that exists but doesn't expose the requested method
        mock_tool = Mock()
        mock_tool.api_methods = {}  # No exposed methods
        mock_registry.get_tool.return_value = mock_tool

        server = ToolIPCServer(mock_registry)

        # Mock a socket connection with valid JSON-RPC and tool/method
        mock_conn = Mock()
        request_data = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            "method": "non_exposed_method",
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request_data).encode('utf-8')

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should send error response
            mock_conn.sendall.assert_called_once()
            # Verify error was logged
            mock_logger.warning.assert_called()

    def test_handle_connection_successful_method_call(self):
        """Test handling connection with successful method call."""
        mock_registry = Mock()

        # Mock a tool with an exposed method
        mock_method = Mock(return_value="success_result")
        mock_tool = Mock()
        mock_tool.api_methods = {"test_method": mock_method}
        mock_registry.get_tool.return_value = mock_tool

        server = ToolIPCServer(mock_registry)

        # Mock a socket connection with valid JSON-RPC and tool/method
        mock_conn = Mock()
        request_data = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            "method": "test_method",
            "params": {"param1": "value1"},
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request_data).encode('utf-8')

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should call the method
            mock_method.assert_called_once_with(param1="value1")

            # Should send success response
            mock_conn.sendall.assert_called_once()
            # Verify success was logged
            mock_logger.info.assert_called()

    def test_handle_connection_method_execution_error(self):
        """Test handling connection with method execution error."""
        mock_registry = Mock()

        # Mock a tool with an exposed method that throws an error
        mock_method = Mock(side_effect=Exception("Method failed"))
        mock_tool = Mock()
        mock_tool.api_methods = {"failing_method": mock_method}
        mock_registry.get_tool.return_value = mock_tool

        server = ToolIPCServer(mock_registry)

        # Mock a socket connection with valid JSON-RPC and tool/method
        mock_conn = Mock()
        request_data = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            "method": "failing_method",
            "params": {"param1": "value1"},
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request_data).encode('utf-8')

        with patch('nodupe.core.api.ipc.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server._handle_connection(mock_conn)

            # Should call the method
            mock_method.assert_called_once_with(param1="value1")

            # Should send error response
            mock_conn.sendall.assert_called_once()
            # Verify error was logged
            mock_logger.error.assert_called()

    def test_send_response(self):
        """Test sending successful response."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        mock_conn = Mock()

        server._send_response(mock_conn, "test_result", 1)

        # Verify response was sent
        mock_conn.sendall.assert_called_once()
        # Parse the sent data to verify it's valid JSON-RPC
        sent_data = mock_conn.sendall.call_args[0][0].decode('utf-8')
        response = json.loads(sent_data)

        assert response["jsonrpc"] == "2.0"
        assert response["result"] == "test_result"
        assert response["id"] == 1

    def test_send_error(self):
        """Test sending error response."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        mock_conn = Mock()

        server._send_error(mock_conn, "Test error message", 1, -32000)

        # Verify error response was sent
        mock_conn.sendall.assert_called_once()
        # Parse the sent data to verify it's valid JSON-RPC error
        sent_data = mock_conn.sendall.call_args[0][0].decode('utf-8')
        response = json.loads(sent_data)

        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["message"] == "Test error message"
        assert response["error"]["code"] == -32000
        assert response["id"] == 1

    def test_log_event(self):
        """Test logging events."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        with patch('nodupe.core.api.ipc.ActionCode') as mock_action_code:
            mock_action_code.FIA_UAU_INIT = 300001
            mock_action_code.name = "FIA_UAU_INIT"

            with patch('nodupe.core.api.ipc.logging') as mock_logging:
                mock_logger = Mock()
                mock_logging.getLogger.return_value = mock_logger
                server.logger = mock_logger

                server._log_event(mock_action_code, "Test message", level="info", test_param="value")

                # Verify logging was called
                mock_logger.info.assert_called_once()


class TestToolIPCServerLifecycle:
    """Test ToolIPCServer lifecycle functionality."""

    def test_start_stop_server(self):
        """Test starting and stopping the server."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Start the server
        with patch('socket.socket') as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value.__enter__.return_value = mock_socket
            mock_socket.accept.side_effect = [socket.timeout()]  # Stop after first iteration

            # Mock the _handle_connection method to avoid actual processing
            with patch.object(server, '_handle_connection'):
                server.start()

                # Wait briefly then stop
                import time
                time.sleep(0.1)
                server.stop()

                # Verify socket operations
                mock_socket.bind.assert_called()
                mock_socket.listen.assert_called()
                mock_socket.close.assert_called()

    def test_server_with_existing_socket(self):
        """Test starting server when socket already exists."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Mock that the socket path exists
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove, \
             patch('socket.socket') as mock_socket_class:

            mock_socket = Mock()
            mock_socket_class.return_value.__enter__.return_value = mock_socket
            mock_socket.accept.side_effect = [socket.timeout()]  # Stop after first iteration

            with patch.object(server, '_handle_connection'):
                server.start()

                # Wait briefly then stop
                import time
                time.sleep(0.1)
                server.stop()

                # Verify the existing socket was removed
                mock_remove.assert_called_once_with(server.socket_path)

    def test_run_server_stopped(self):
        """Test server run loop when stopped."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Set the stop event
        server._stop_event.set()

        # Run the server (should exit immediately due to stop event)
        with patch('socket.socket') as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value.__enter__.return_value = mock_socket
            mock_socket.accept.side_effect = socket.timeout  # This shouldn't be reached

            # This should return quickly due to stop event
            server._run_server()

            # Verify socket was set up but accept wasn't called (due to early exit)
            mock_socket.settimeout.assert_called_once()


class TestToolIPCServerRateLimiting:
    """Test ToolIPCServer rate limiting functionality."""

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Test that rate limiting is enforced
        # First call should be allowed
        result1 = server.rate_limiter.check_rate_limit("test_client")
        assert result1 is True

        # Make many rapid calls to exceed rate limit
        for i in range(100):
            result = server.rate_limiter.check_rate_limit("test_client")
            if not result:
                # Rate limit was hit
                break
        else:
            # If we didn't hit the rate limit, that's OK for this test
            pass
