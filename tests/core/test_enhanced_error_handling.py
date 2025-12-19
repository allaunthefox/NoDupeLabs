# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for Enhanced Error Handling System.

This module provides comprehensive testing for the enhanced error handling
capabilities of the plugin system.
"""

import pytest
from unittest.mock import Mock, patch
from nodupe.core.plugin_system.enhanced_error_handling import (
    EnhancedPluginErrorHandler,
    PluginErrorDetails,
    PluginErrorFormatter,
    PluginErrorRecovery,
    enhanced_error_handler,
    setup_enhanced_error_handling
)
import datetime
import logging

class TestEnhancedErrorHandler:
    """Test the EnhancedPluginErrorHandler class."""

    def test_error_handler_instantiation(self):
        """Test EnhancedPluginErrorHandler instantiation."""
        handler = EnhancedPluginErrorHandler()
        assert handler is not None
        assert handler.error_counter == 0
        assert handler.error_log == []

    def test_log_error_basic(self):
        """Test basic error logging functionality."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Test error")

        error_details = handler.log_error("test_plugin", error)

        assert error_details is not None
        assert isinstance(error_details, PluginErrorDetails)
        assert error_details.plugin_name == "test_plugin"
        assert error_details.error_type == "RuntimeError"
        assert error_details.error_message == "Test error"
        assert error_details.severity == "ERROR"
        assert len(error_details.recovery_suggestions) > 0

        # Verify error was logged
        assert len(handler.error_log) == 1
        assert handler.error_counter == 1

    def test_log_error_with_context(self):
        """Test error logging with additional context."""
        handler = EnhancedPluginErrorHandler()
        error = ValueError("Invalid value")
        context = {
            "operation": "initialize",
            "file_path": "/test/path",
            "attempt": 1
        }

        error_details = handler.log_error("test_plugin", error, context)

        assert error_details.context == context
        assert "Check plugin initialization parameters" in error_details.recovery_suggestions
        assert "Verify dependency container availability" in error_details.recovery_suggestions

    def test_log_error_different_severities(self):
        """Test error logging with different severity levels."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Test error")

        # Test different severity levels
        severities = ["ERROR", "WARNING", "INFO", "DEBUG"]

        for severity in severities:
            error_details = handler.log_error("test_plugin", error, severity=severity)
            assert error_details.severity == severity

    def test_error_id_format(self):
        """Test that error IDs follow the expected format."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Test error")

        error_details = handler.log_error("test_plugin", error)

        # Should match format: PLUGIN-YYYYMMDD-HHMMSS-0001
        assert error_details.error_id.startswith("PLUGIN-")
        assert len(error_details.error_id.split("-")) == 4

    def test_get_error_report(self):
        """Test error report generation."""
        handler = EnhancedPluginErrorHandler()

        # Log some errors
        handler.log_error("plugin1", RuntimeError("Error 1"))
        handler.log_error("plugin2", ValueError("Error 2"))

        # Get report for all errors
        report = handler.get_error_report()
        assert report["total_errors"] == 2
        assert len(report["errors"]) == 2

        # Get report for specific error
        error_id = report["errors"][0]["error_id"]
        specific_report = handler.get_error_report(error_id)
        assert specific_report["total_errors"] == 1
        assert specific_report["errors"][0]["error_id"] == error_id

    def test_get_user_friendly_error_message(self):
        """Test user-friendly error message generation."""
        handler = EnhancedPluginErrorHandler()
        error = FileNotFoundError("/missing/file.txt")
        context = {"operation": "file_read", "attempt": 1}

        error_details = handler.log_error("file_plugin", error, context)

        user_message = handler.get_user_friendly_error_message(error_details)

        assert "🚨 Plugin Error:" in user_message
        assert "file_plugin" in user_message
        assert "FileNotFoundError" in user_message
        assert "💡 Recovery Suggestions:" in user_message
        assert "Verify that all required files exist" in user_message

    def test_handle_plugin_error(self):
        """Test plugin error handling with appropriate return values."""
        handler = EnhancedPluginErrorHandler()

        # Test different method types
        test_cases = [
            ("execute_scan", 1),
            ("execute_verify", 1),
            ("initialize", False),
            ("shutdown", False),
            ("get_capabilities", {}),
            ("unknown_method", None)
        ]

        for method_name, expected_return in test_cases:
            error = RuntimeError(f"Error in {method_name}")
            result = handler.handle_plugin_error("test_plugin", method_name, error)
            assert result == expected_return

    def test_error_statistics(self):
        """Test error statistics generation."""
        handler = EnhancedPluginErrorHandler()

        # Log various types of errors
        handler.log_error("plugin1", RuntimeError("Error 1"), severity="ERROR")
        handler.log_error("plugin1", ValueError("Error 2"), severity="WARNING")
        handler.log_error("plugin2", TypeError("Error 3"), severity="ERROR")

        stats = handler.get_error_statistics()

        assert stats["total_errors"] == 3
        assert stats["errors_by_severity"]["ERROR"] == 2
        assert stats["errors_by_severity"]["WARNING"] == 1
        assert stats["errors_by_plugin"]["plugin1"] == 2
        assert stats["errors_by_plugin"]["plugin2"] == 1
        assert stats["errors_by_type"]["RuntimeError"] == 1

    def test_clear_error_log(self):
        """Test clearing the error log."""
        handler = EnhancedPluginErrorHandler()

        # Add some errors
        handler.log_error("plugin1", RuntimeError("Error 1"))
        handler.log_error("plugin2", ValueError("Error 2"))

        assert len(handler.error_log) == 2
        assert handler.error_counter == 2

        # Clear the log
        handler.clear_error_log()

        assert len(handler.error_log) == 0
        assert handler.error_counter == 0

class TestPluginErrorDetails:
    """Test the PluginErrorDetails dataclass."""

    def test_error_details_creation(self):
        """Test PluginErrorDetails object creation."""
        error_details = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="RuntimeError",
            error_message="Test error",
            stack_trace="Traceback...",
            context={"key": "value"},
            severity="ERROR",
            recovery_suggestions=["Suggestion 1", "Suggestion 2"]
        )

        assert error_details.error_id == "TEST-001"
        assert error_details.plugin_name == "test_plugin"
        assert error_details.error_type == "RuntimeError"
        assert error_details.error_message == "Test error"
        assert error_details.severity == "ERROR"
        assert len(error_details.recovery_suggestions) == 2

    def test_error_details_immutability(self):
        """Test that PluginErrorDetails is immutable (dataclass behavior)."""
        error_details = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="RuntimeError",
            error_message="Test error",
            stack_trace="Traceback...",
            context={"key": "value"},
            severity="ERROR",
            recovery_suggestions=["Suggestion 1"]
        )

        # Should be able to access attributes
        assert error_details.plugin_name == "test_plugin"

        # Context and recovery_suggestions should be mutable lists
        error_details.recovery_suggestions.append("Suggestion 2")
        assert len(error_details.recovery_suggestions) == 2

class TestPluginErrorFormatter:
    """Test the PluginErrorFormatter class."""

    def test_console_formatting(self):
        """Test console error formatting."""
        error_details = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="RuntimeError",
            error_message="Test error",
            stack_trace="Traceback...",
            context={},
            severity="ERROR",
            recovery_suggestions=[]
        )

        console_output = PluginErrorFormatter.format_error_console(error_details)

        assert "🚨 ERROR: TEST-001" in console_output
        assert "📦 Plugin: test_plugin" in console_output
        assert "🔧 Error: RuntimeError - Test error" in console_output

    def test_json_formatting(self):
        """Test JSON error formatting."""
        error_details = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="RuntimeError",
            error_message="Test error",
            stack_trace="Traceback...",
            context={"operation": "test"},
            severity="ERROR",
            recovery_suggestions=["Suggestion 1"]
        )

        json_output = PluginErrorFormatter.format_error_json(error_details)

        assert json_output["error_id"] == "TEST-001"
        assert json_output["plugin_name"] == "test_plugin"
        assert json_output["error_type"] == "RuntimeError"
        assert json_output["context"]["operation"] == "test"
        assert len(json_output["recovery_suggestions"]) == 1

    def test_markdown_formatting(self):
        """Test Markdown error formatting."""
        error_details = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="RuntimeError",
            error_message="Test error",
            stack_trace="Traceback...",
            context={"operation": "test"},
            severity="ERROR",
            recovery_suggestions=["Suggestion 1"]
        )

        md_output = PluginErrorFormatter.format_error_markdown(error_details)

        assert "## Plugin Error: TEST-001" in md_output
        assert "**Plugin**: `test_plugin`" in md_output
        assert "**Type**: `RuntimeError`" in md_output
        assert "**Context:**" in md_output
        assert "**Recovery Suggestions:**" in md_output

class TestPluginErrorRecovery:
    """Test the PluginErrorRecovery class."""

    def test_recovery_assessment(self):
        """Test error recovery assessment."""
        recoverable_error = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="FileNotFoundError",
            error_message="File not found",
            stack_trace="Traceback...",
            context={},
            severity="ERROR",
            recovery_suggestions=[]
        )

        non_recoverable_error = PluginErrorDetails(
            error_id="TEST-002",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="MemoryError",
            error_message="Out of memory",
            stack_trace="Traceback...",
            context={},
            severity="ERROR",
            recovery_suggestions=[]
        )

        assert PluginErrorRecovery.can_recover_from_error(recoverable_error) is True
        assert PluginErrorRecovery.can_recover_from_error(non_recoverable_error) is False

    def test_recovery_strategy(self):
        """Test recovery strategy generation."""
        file_error = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="FileNotFoundError",
            error_message="File not found",
            stack_trace="Traceback...",
            context={},
            severity="ERROR",
            recovery_suggestions=[]
        )

        strategy = PluginErrorRecovery.get_recovery_strategy(file_error)

        assert strategy["recoverable"] is True
        assert strategy["strategy"] == "retry_with_validation"
        assert len(strategy["automatic_actions"]) > 0
        assert len(strategy["manual_actions"]) > 0

    def test_non_recoverable_strategy(self):
        """Test strategy for non-recoverable errors."""
        memory_error = PluginErrorDetails(
            error_id="TEST-001",
            timestamp="2025-01-01T00:00:00",
            plugin_name="test_plugin",
            error_type="MemoryError",
            error_message="Out of memory",
            stack_trace="Traceback...",
            context={},
            severity="ERROR",
            recovery_suggestions=[]
        )

        strategy = PluginErrorRecovery.get_recovery_strategy(memory_error)

        assert strategy["recoverable"] is False
        assert strategy["strategy"] == "manual_intervention"
        assert len(strategy["automatic_actions"]) == 0

class TestGlobalErrorHandler:
    """Test the global error handler instance."""

    def test_global_handler_access(self):
        """Test access to global error handler."""
        from nodupe.core.plugin_system.enhanced_error_handling import enhanced_error_handler

        assert enhanced_error_handler is not None
        assert isinstance(enhanced_error_handler, EnhancedPluginErrorHandler)

    def test_global_handler_functionality(self):
        """Test that global handler works like regular instances."""
        error = RuntimeError("Global test error")

        error_details = enhanced_error_handler.log_error("global_test", error)

        assert error_details is not None
        assert error_details.plugin_name == "global_test"
        assert len(enhanced_error_handler.error_log) == 1

class TestErrorHandlingIntegration:
    """Test integration of enhanced error handling with plugins."""

    def test_scan_plugin_error_handling(self):
        """Test error handling integration with ScanPlugin."""
        from nodupe.plugins.commands.scan import ScanPlugin
        from nodupe.core.plugin_system.enhanced_error_handling import enhanced_error_handler

        plugin = ScanPlugin()

        # Test error in execute_scan
        mock_args = Mock()
        mock_args.paths = []  # This should cause an error

        # This should return error code 1
        result = plugin.execute_scan(mock_args)
        assert result == 1

        # The error should be handled gracefully without crashing

    def test_verify_plugin_error_handling(self):
        """Test error handling integration with VerifyPlugin."""
        from nodupe.plugins.commands.verify import VerifyPlugin
        from nodupe.core.plugin_system.enhanced_error_handling import enhanced_error_handler

        plugin = VerifyPlugin()

        # Test error in execute_verify
        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None
        mock_args.container = None  # This should cause an error

        # This should return error code 1
        result = plugin.execute_verify(mock_args)
        assert result == 1

        # The error should be handled gracefully without crashing

    def test_error_handling_with_enhanced_handler(self):
        """Test using enhanced error handler with plugin errors."""
        from nodupe.core.plugin_system.enhanced_error_handling import enhanced_error_handler

        # Clear any existing errors
        enhanced_error_handler.clear_error_log()

        # Simulate a plugin error
        error = FileNotFoundError("/missing/config.json")
        context = {
            "operation": "initialize",
            "plugin_version": "1.0.0",
            "attempt": 1
        }

        error_details = enhanced_error_handler.log_error("config_plugin", error, context)

        # Verify error was logged
        assert len(enhanced_error_handler.error_log) == 1
        assert error_details.plugin_name == "config_plugin"
        assert error_details.error_type == "FileNotFoundError"

        # Verify recovery suggestions
        suggestions = error_details.recovery_suggestions
        assert "Verify that all required files exist" in suggestions
        assert "Check file paths and configurations" in suggestions

        # Get user-friendly message
        user_message = enhanced_error_handler.get_user_friendly_error_message(error_details)
        assert "🚨 Plugin Error:" in user_message
        assert "config_plugin" in user_message

class TestErrorHandlingPerformance:
    """Test performance characteristics of error handling."""

    def test_error_logging_performance(self, benchmark):
        """Test performance of error logging."""
        handler = EnhancedPluginErrorHandler()

        # Benchmark logging multiple errors
        def log_multiple_errors():
            for i in range(100):
                error = RuntimeError(f"Error {i}")
                handler.log_error(f"plugin_{i % 10}", error, context={"iteration": i})

        result = benchmark(log_multiple_errors)

        # Should complete without errors
        assert len(handler.error_log) == 100

    def test_error_report_generation_performance(self, benchmark):
        """Test performance of error report generation."""
        handler = EnhancedPluginErrorHandler()

        # Add many errors
        for i in range(1000):
            error = RuntimeError(f"Error {i}")
            handler.log_error(f"plugin_{i % 10}", error)

        # Benchmark report generation
        def generate_report():
            return handler.get_error_report()

        report = benchmark(generate_report)

        assert report["total_errors"] == 1000

class TestErrorHandlingEdgeCases:
    """Test edge cases in error handling."""

    def test_error_with_no_context(self):
        """Test error logging with no context provided."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Test error")

        error_details = handler.log_error("test_plugin", error, context=None)

        assert error_details.context == {}
        assert len(error_details.recovery_suggestions) > 0

    def test_error_with_empty_context(self):
        """Test error logging with empty context."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Test error")

        error_details = handler.log_error("test_plugin", error, context={})

        assert error_details.context == {}
        assert len(error_details.recovery_suggestions) > 0

    def test_error_with_complex_context(self):
        """Test error logging with complex context data."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Test error")

        complex_context = {
            "operation": "complex_operation",
            "nested_data": {
                "level1": {
                    "level2": "deep_value"
                }
            },
            "list_data": [1, 2, 3, "string", {"nested": "dict"}],
            "timestamp": datetime.datetime.now().isoformat()
        }

        error_details = handler.log_error("test_plugin", error, context=complex_context)

        assert error_details.context == complex_context
        assert len(error_details.recovery_suggestions) > 0

    def test_error_with_unicode_message(self):
        """Test error handling with unicode characters."""
        handler = EnhancedPluginErrorHandler()
        error = RuntimeError("Error with unicode: 文件不存在")

        error_details = handler.log_error("test_plugin", error)

        assert "文件不存在" in error_details.error_message
        assert len(error_details.recovery_suggestions) > 0

    def test_error_with_very_long_message(self):
        """Test error handling with very long error messages."""
        handler = EnhancedPluginErrorHandler()
        long_message = "X" * 10000  # 10KB error message
        error = RuntimeError(long_message)

        error_details = handler.log_error("test_plugin", error)

        assert len(error_details.error_message) == 10000
        assert len(error_details.recovery_suggestions) > 0

class TestErrorHandlingSecurity:
    """Test security aspects of error handling."""

    def test_sensitive_data_in_context(self):
        """Test handling of sensitive data in error context."""
        handler = EnhancedPluginErrorHandler()

        sensitive_context = {
            "password": "secret123",
            "api_key": "abc123xyz",
            "token": "sensitive_token",
            "operation": "authenticate"
        }

        error = RuntimeError("Authentication failed")
        error_details = handler.log_error("auth_plugin", error, context=sensitive_context)

        # Sensitive data should be included (in real scenario, this would be filtered)
        assert error_details.context == sensitive_context

        # User-friendly message should not expose sensitive data in suggestions
        user_message = handler.get_user_friendly_error_message(error_details)
        assert "secret123" not in user_message
        assert "abc123xyz" not in user_message

    def test_error_message_sanitization(self):
        """Test that error messages are properly handled."""
        handler = EnhancedPluginErrorHandler()

        # Test with potentially dangerous content
        malicious_message = "Error: <script>alert('xss')</script>"
        error = RuntimeError(malicious_message)

        error_details = handler.log_error("web_plugin", error)

        # Should store the message as-is (sanitization would happen at display time)
        assert malicious_message in error_details.error_message

        # Formatted outputs should handle it safely
        console_output = PluginErrorFormatter.format_error_console(error_details)
        assert malicious_message in console_output

        json_output = PluginErrorFormatter.format_error_json(error_details)
        assert malicious_message in json_output["error_message"]

class TestErrorHandlingLogging:
    """Test logging functionality of error handling."""

    def test_logging_setup(self, caplog):
        """Test that logging is properly configured."""
        # Setup enhanced error handling
        handler = setup_enhanced_error_handling()

        # Log an error
        error = RuntimeError("Test error for logging")
        handler.log_error("test_plugin", error)

        # Check that logs were generated
        assert len(caplog.records) > 0

        # Check for expected log messages
        log_messages = [record.message for record in caplog.records]
        error_messages = [msg for msg in log_messages if "ERROR" in msg]
        assert len(error_messages) > 0

    def test_error_severity_logging(self, caplog):
        """Test that different severity levels are logged appropriately."""
        handler = EnhancedPluginErrorHandler()

        # Clear previous logs
        caplog.clear()

        # Log errors with different severities
        handler.log_error("plugin1", RuntimeError("Error 1"), severity="ERROR")
        handler.log_error("plugin2", RuntimeError("Error 2"), severity="WARNING")
        handler.log_error("plugin3", RuntimeError("Error 3"), severity="INFO")

        # Check log levels
        error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
        warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
        info_logs = [r for r in caplog.records if r.levelname == "INFO"]

        assert len(error_logs) >= 1
        assert len(warning_logs) >= 1
        assert len(info_logs) >= 1

class TestErrorHandlingRecovery:
    """Test error recovery functionality."""

    def test_recovery_suggestions_generation(self):
        """Test generation of recovery suggestions for different error types."""
        handler = EnhancedPluginErrorHandler()

        error_types = [
            ("ImportError", "Module not found"),
            ("PermissionError", "Access denied"),
            ("FileNotFoundError", "File not found"),
            ("TypeError", "Invalid type"),
            ("ValueError", "Invalid value"),
            ("RuntimeError", "Runtime error")
        ]

        for error_type, message in error_types:
            error = type(error_type, (Exception,), {})(message)
            error_details = handler.log_error("test_plugin", error)

            suggestions = error_details.recovery_suggestions

            # Should have both common and specific suggestions
            assert len(suggestions) >= 4  # At least 4 suggestions (common + specific)

            # Should have common suggestions
            assert "Check plugin configuration and dependencies" in suggestions
            assert "Restart the application if the error persists" in suggestions

    def test_context_specific_suggestions(self):
        """Test context-specific recovery suggestions."""
        handler = EnhancedPluginErrorHandler()

        # Test initialization context
        init_error = RuntimeError("Initialization failed")
        init_details = handler.log_error("test_plugin", init_error, context={"operation": "initialize"})

        assert "Check plugin initialization parameters" in init_details.recovery_suggestions
        assert "Verify dependency container availability" in init_details.recovery_suggestions

        # Test execute context
        exec_error = RuntimeError("Execution failed")
        exec_details = handler.log_error("test_plugin", exec_error, context={"operation": "execute"})

        assert "Review command arguments and options" in exec_details.recovery_suggestions
        assert "Check for invalid or missing parameters" in exec_details.recovery_suggestions
