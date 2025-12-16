# Error Test Utilities
# Helper functions for error condition simulation and testing

import contextlib
from typing import Dict, Any, List, Optional, Union, Callable, Type
from unittest.mock import MagicMock, patch
import random
import os
import tempfile
from pathlib import Path

def simulate_file_system_errors(
    error_type: str = "permission",
    operation: str = "read"
) -> Callable:
    """
    Create a context manager to simulate file system errors.

    Args:
        error_type: Type of error to simulate
        operation: File operation to fail

    Returns:
        Context manager for error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "permission": PermissionError("Operation not permitted"),
            "not_found": FileNotFoundError("File not found"),
            "disk_full": OSError("No space left on device"),
            "io_error": IOError("Input/output error"),
            "access_denied": PermissionError("Access denied")
        }

        error = error_map.get(error_type, IOError("File system error"))

        original_open = open
        original_path = Path

        class MockPath:
            def __init__(self, *args):
                self.path = original_path(*args)

            def __truediv__(self, other):
                return MockPath(str(self.path) + "/" + str(other))

            def __str__(self):
                return str(self.path)

            def read_text(self, *args, **kwargs):
                if operation == "read":
                    raise error
                return self.path.read_text(*args, **kwargs)

            def write_text(self, *args, **kwargs):
                if operation == "write":
                    raise error
                return self.path.write_text(*args, **kwargs)

            def exists(self):
                if operation == "exists":
                    raise error
                return self.path.exists()

            def unlink(self):
                if operation == "delete":
                    raise error
                return self.path.unlink()

        def mock_open(*args, **kwargs):
            if operation == "open":
                raise error
            return original_open(*args, **kwargs)

        with patch('builtins.open', side_effect=mock_open):
            with patch('pathlib.Path', side_effect=MockPath):
                yield

    return error_context

def create_error_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create error test scenarios.

    Returns:
        List of error test scenarios
    """
    return [
        {
            "name": "file_not_found",
            "error_type": "FileNotFoundError",
            "expected_behavior": "graceful_failure"
        },
        {
            "name": "permission_denied",
            "error_type": "PermissionError",
            "expected_behavior": "retry_or_fail"
        },
        {
            "name": "disk_full",
            "error_type": "OSError",
            "expected_behavior": "cleanup_and_fail"
        },
        {
            "name": "network_timeout",
            "error_type": "TimeoutError",
            "expected_behavior": "retry_with_backoff"
        },
        {
            "name": "invalid_input",
            "error_type": "ValueError",
            "expected_behavior": "validate_and_fail"
        }
    ]

def simulate_network_errors(
    error_type: str = "timeout",
    failure_rate: float = 1.0
) -> Callable:
    """
    Create a context manager to simulate network errors.

    Args:
        error_type: Type of network error to simulate
        failure_rate: Probability of failure (0.0 to 1.0)

    Returns:
        Context manager for network error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "timeout": TimeoutError("Connection timed out"),
            "connection_refused": ConnectionRefusedError("Connection refused"),
            "dns_failure": OSError("Name or service not known"),
            "ssl_error": OSError("SSL handshake failed"),
            "network_unreachable": OSError("Network is unreachable")
        }

        error = error_map.get(error_type, OSError("Network error"))

        original_requests = __import__('requests')

        class MockRequests:
            @staticmethod
            def get(*args, **kwargs):
                if random.random() < failure_rate:
                    raise error
                return original_requests.get(*args, **kwargs)

            @staticmethod
            def post(*args, **kwargs):
                if random.random() < failure_rate:
                    raise error
                return original_requests.post(*args, **kwargs)

        with patch('requests', MockRequests):
            with patch('urllib.request.urlopen') as mock_urlopen:
                if random.random() < failure_rate:
                    mock_urlopen.side_effect = error
                yield

    return error_context

def create_exception_test_cases() -> List[Dict[str, Any]]:
    """
    Create exception test cases.

    Returns:
        List of exception test cases
    """
    return [
        {
            "name": "value_error",
            "exception": ValueError,
            "message": "Invalid value provided",
            "test_function": lambda: int("invalid")
        },
        {
            "name": "type_error",
            "exception": TypeError,
            "message": "Invalid type provided",
            "test_function": lambda: "string" + 123
        },
        {
            "name": "index_error",
            "exception": IndexError,
            "message": "Index out of range",
            "test_function": lambda: [1, 2, 3][10]
        },
        {
            "name": "key_error",
            "exception": KeyError,
            "message": "Key not found",
            "test_function": lambda: {"a": 1}["b"]
        },
        {
            "name": "attribute_error",
            "exception": AttributeError,
            "message": "Attribute not found",
            "test_function": lambda: "string".nonexistent_method()
        }
    ]

def simulate_memory_errors(
    error_type: str = "out_of_memory"
) -> Callable:
    """
    Create a context manager to simulate memory errors.

    Args:
        error_type: Type of memory error to simulate

    Returns:
        Context manager for memory error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "out_of_memory": MemoryError("Out of memory"),
            "memory_leak": MemoryError("Memory allocation failed"),
            "stack_overflow": RecursionError("Maximum recursion depth exceeded")
        }

        error = error_map.get(error_type, MemoryError("Memory error"))

        original_alloc = __import__('builtins').__dict__['object'].__new__

        def mock_alloc(cls, *args, **kwargs):
            if random.random() > 0.5:  # 50% chance of failure
                raise error
            return original_alloc(cls, *args, **kwargs)

        with patch('builtins.object.__new__', side_effect=mock_alloc):
            yield

    return error_context

def create_error_recovery_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create error recovery test scenarios.

    Returns:
        List of error recovery test scenarios
    """
    return [
        {
            "name": "automatic_retry",
            "error_type": "temporary_failure",
            "recovery_strategy": "retry",
            "max_retries": 3,
            "expected_result": "success"
        },
        {
            "name": "fallback_mechanism",
            "error_type": "permanent_failure",
            "recovery_strategy": "fallback",
            "expected_result": "degraded_functionality"
        },
        {
            "name": "graceful_degradation",
            "error_type": "resource_exhaustion",
            "recovery_strategy": "degrade",
            "expected_result": "reduced_performance"
        },
        {
            "name": "manual_intervention",
            "error_type": "critical_failure",
            "recovery_strategy": "alert",
            "expected_result": "admin_notification"
        }
    ]

def simulate_database_errors(
    error_type: str = "connection_failed"
) -> Callable:
    """
    Create a context manager to simulate database errors.

    Args:
        error_type: Type of database error to simulate

    Returns:
        Context manager for database error simulation
    """
    @contextlib.contextmanager
    def error_context():
        import sqlite3
        error_map = {
            "connection_failed": sqlite3.OperationalError("Unable to connect to database"),
            "query_failed": sqlite3.ProgrammingError("SQL syntax error"),
            "constraint_violation": sqlite3.IntegrityError("Constraint violation"),
            "timeout": sqlite3.OperationalError("Database locked"),
            "disk_full": sqlite3.OperationalError("Database or disk is full")
        }

        error = error_map.get(error_type, sqlite3.Error("Database error"))

        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            if error_type == "connection_failed":
                mock_connect.side_effect = error
            else:
                mock_conn.cursor.return_value = mock_cursor
                if error_type == "query_failed":
                    mock_cursor.execute.side_effect = error
                elif error_type == "constraint_violation":
                    mock_cursor.execute.side_effect = error
                elif error_type == "timeout":
                    mock_conn.commit.side_effect = error
                elif error_type == "disk_full":
                    mock_cursor.execute.side_effect = error

                mock_connect.return_value = mock_conn

            yield

    return error_context

def create_error_injection_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create error injection test scenarios.

    Returns:
        List of error injection test scenarios
    """
    return [
        {
            "name": "random_failures",
            "failure_rate": 0.1,
            "target_components": ["network", "database", "file_system"],
            "expected_behavior": "resilient_operation"
        },
        {
            "name": "cascading_failures",
            "failure_sequence": ["database", "cache", "api"],
            "expected_behavior": "failure_containment"
        },
        {
            "name": "intermittent_failures",
            "failure_pattern": "on_off",
            "expected_behavior": "automatic_recovery"
        }
    ]

def simulate_plugin_errors(
    error_type: str = "loading_failed"
) -> Callable:
    """
    Create a context manager to simulate plugin errors.

    Args:
        error_type: Type of plugin error to simulate

    Returns:
        Context manager for plugin error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "loading_failed": ImportError("Cannot load plugin"),
            "initialization_failed": RuntimeError("Plugin initialization failed"),
            "execution_failed": ValueError("Plugin execution error"),
            "compatibility_error": RuntimeError("Plugin compatibility issue"),
            "security_violation": RuntimeError("Plugin security violation")
        }

        error = error_map.get(error_type, RuntimeError("Plugin error"))

        with patch('importlib.import_module') as mock_import:
            if error_type == "loading_failed":
                mock_import.side_effect = error
            else:
                mock_plugin = MagicMock()
                if error_type == "initialization_failed":
                    mock_plugin.initialize.side_effect = error
                elif error_type == "execution_failed":
                    mock_plugin.execute.side_effect = error
                elif error_type == "compatibility_error":
                    mock_plugin.metadata = {"version": "incompatible"}
                elif error_type == "security_violation":
                    mock_plugin.execute.side_effect = error

                mock_import.return_value = mock_plugin

            yield

    return error_context

def create_error_handling_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create error handling test scenarios.

    Returns:
        List of error handling test scenarios
    """
    return [
        {
            "name": "exception_handling",
            "error_type": "ValueError",
            "handling_strategy": "catch_and_log",
            "expected_result": "logged_error"
        },
        {
            "name": "resource_cleanup",
            "error_type": "IOError",
            "handling_strategy": "cleanup_and_rethrow",
            "expected_result": "cleaned_up_resources"
        },
        {
            "name": "fallback_operation",
            "error_type": "TimeoutError",
            "handling_strategy": "use_fallback",
            "expected_result": "fallback_used"
        },
        {
            "name": "retry_operation",
            "error_type": "TemporaryError",
            "handling_strategy": "retry_with_backoff",
            "expected_result": "operation_retry"
        }
    ]

def simulate_concurrency_errors(
    error_type: str = "race_condition"
) -> Callable:
    """
    Create a context manager to simulate concurrency errors.

    Args:
        error_type: Type of concurrency error to simulate

    Returns:
        Context manager for concurrency error simulation
    """
    @contextlib.contextmanager
    def error_context():
        import threading

        error_map = {
            "race_condition": RuntimeError("Race condition detected"),
            "deadlock": RuntimeError("Deadlock detected"),
            "thread_failure": RuntimeError("Thread execution failed"),
            "resource_contention": RuntimeError("Resource contention detected")
        }

        error = error_map.get(error_type, RuntimeError("Concurrency error"))

        original_thread = threading.Thread

        class MockThread(threading.Thread):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._error = error if random.random() > 0.7 else None

            def run(self):
                if self._error:
                    raise self._error
                super().run()

        with patch('threading.Thread', MockThread):
            yield

    return error_context

def create_error_validation_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create error validation test scenarios.

    Returns:
        List of error validation test scenarios
    """
    return [
        {
            "name": "input_validation",
            "test_cases": [
                {"input": None, "expected_error": "ValueError"},
                {"input": -1, "expected_error": "ValueError"},
                {"input": "invalid", "expected_error": "TypeError"}
            ]
        },
        {
            "name": "state_validation",
            "test_cases": [
                {"state": "invalid_state", "expected_error": "RuntimeError"},
                {"state": "corrupted_data", "expected_error": "DataError"}
            ]
        },
        {
            "name": "security_validation",
            "test_cases": [
                {"permission": "denied", "expected_error": "PermissionError"},
                {"access": "unauthorized", "expected_error": "SecurityError"}
            ]
        }
    ]

def simulate_resource_exhaustion_errors(
    resource_type: str = "memory"
) -> Callable:
    """
    Create a context manager to simulate resource exhaustion errors.

    Args:
        resource_type: Type of resource to exhaust

    Returns:
        Context manager for resource exhaustion simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "memory": MemoryError("Out of memory"),
            "cpu": RuntimeError("CPU resources exhausted"),
            "disk": OSError("No space left on device"),
            "handles": OSError("Too many open files"),
            "threads": RuntimeError("Too many threads")
        }

        error = error_map.get(resource_type, RuntimeError("Resource exhausted"))

        if resource_type == "memory":
            original_alloc = __import__('builtins').__dict__['object'].__new__

            def mock_alloc(cls, *args, **kwargs):
                if random.random() > 0.3:  # 70% chance of failure
                    raise error
                return original_alloc(cls, *args, **kwargs)

            with patch('builtins.object.__new__', side_effect=mock_alloc):
                yield

        elif resource_type == "disk":
            def mock_write(*args, **kwargs):
                if random.random() > 0.5:  # 50% chance of failure
                    raise error
                original_write(*args, **kwargs)

            original_write = open
            with patch('builtins.open', side_effect=mock_write):
                yield

        else:
            # For other resource types, use a simpler approach
            def resource_check():
                if random.random() > 0.7:  # 30% chance of failure
                    raise error

            with patch('resource.getrlimit', side_effect=resource_check):
                yield

    return error_context

def create_error_monitoring_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create error monitoring test scenarios.

    Returns:
        List of error monitoring test scenarios
    """
    return [
        {
            "name": "error_logging",
            "monitoring_type": "logging",
            "expected_behavior": "error_logged",
            "verification": "check_log_files"
        },
        {
            "name": "error_metrics",
            "monitoring_type": "metrics",
            "expected_behavior": "metrics_updated",
            "verification": "check_metrics_endpoint"
        },
        {
            "name": "error_alerting",
            "monitoring_type": "alerting",
            "expected_behavior": "alert_sent",
            "verification": "check_alert_system"
        },
        {
            "name": "error_tracing",
            "monitoring_type": "tracing",
            "expected_behavior": "trace_recorded",
            "verification": "check_tracing_system"
        }
    ]

def simulate_timeout_errors(
    timeout_type: str = "operation_timeout"
) -> Callable:
    """
    Create a context manager to simulate timeout errors.

    Args:
        timeout_type: Type of timeout error to simulate

    Returns:
        Context manager for timeout error simulation
    """
    @contextlib.contextmanager
    def error_context():
        import time

        error_map = {
            "operation_timeout": TimeoutError("Operation timed out"),
            "connection_timeout": TimeoutError("Connection timed out"),
            "read_timeout": TimeoutError("Read operation timed out"),
            "write_timeout": TimeoutError("Write operation timed out")
        }

        error = error_map.get(timeout_type, TimeoutError("Timeout error"))

        original_time = time.time
        original_sleep = time.sleep

        start_time = original_time()

        def slow_time():
            elapsed = original_time() - start_time
            if elapsed > 1.0:  # After 1 second, start causing timeouts
                raise error
            return original_time()

        def slow_sleep(seconds):
            if seconds > 0.1:  # Long sleeps cause timeouts
                raise error
            original_sleep(seconds)

        with patch('time.time', side_effect=slow_time):
            with patch('time.sleep', side_effect=slow_sleep):
                yield

    return error_context

def create_error_recovery_validation_scenarios() -> List[Dict[str, Any]]:
    """
    Create error recovery validation scenarios.

    Returns:
        List of error recovery validation scenarios
    """
    return [
        {
            "name": "data_consistency_after_error",
            "error_type": "database_error",
            "recovery_method": "transaction_rollback",
            "validation": "verify_data_integrity"
        },
        {
            "name": "resource_cleanup_after_error",
            "error_type": "file_error",
            "recovery_method": "resource_release",
            "validation": "verify_no_resource_leaks"
        },
        {
            "name": "state_consistency_after_error",
            "error_type": "state_error",
            "recovery_method": "state_reset",
            "validation": "verify_consistent_state"
        }
    ]
