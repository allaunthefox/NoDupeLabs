# Tool Test Utilities
# Helper functions for tool system testing

import contextlib
import importlib
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import MagicMock, Mock, patch


def create_mock_tool(
    name: str = "test_tool",
    functions: Optional[dict[str, Callable]] = None,
    metadata: Optional[dict[str, Any]] = None
) -> Mock:
    """
    Create a mock tool for testing.

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation

    Args:
        name: Tool name
        functions: Dictionary of tool functions
        metadata: Tool metadata

    Returns:
        Mock tool object
    """
    mock_tool = Mock()
    mock_tool.name = name

    # Set up tool metadata
    if metadata is None:
        metadata = {
            "name": name,
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Test tool for testing"
        }

    mock_tool.metadata = metadata

    # Set up tool functions
    if functions is None:
        functions = {
            "initialize": lambda: True,
            "execute": lambda *args, **kwargs: {"result": "success"},
            "cleanup": lambda: None
        }

    for func_name, func_impl in functions.items():
        setattr(mock_tool, func_name, func_impl)

    return mock_tool

def create_tool_directory_structure(
    base_path: Path,
    tools: list[dict[str, Any]]
) -> dict[str, Path]:
    """
    Create a tool directory structure for testing.

    Args:
        base_path: Base directory path
        tools: List of tool definitions

    Returns:
        Dictionary mapping tool names to their paths
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    tool_paths = {}

    for tool_def in tools:
        tool_name = tool_def["name"]
        tool_dir = base_path / tool_name

        if not tool_dir.exists():
            tool_dir.mkdir()

        # Create __init__.py
        init_file = tool_dir / "__init__.py"
        init_file.write_text(f"# {tool_name} tool\n")

        # Create main tool file
        tool_file = tool_dir / f"{tool_name}.py"
        tool_content = f"""
# {tool_name} Tool Implementation

def initialize():
    '''Initialize the tool'''
    return True

def execute(*args, **kwargs):
    '''Execute tool functionality'''
    return {{"tool": "{tool_name}", "status": "success"}}

def cleanup():
    '''Clean up tool resources'''
    pass

metadata = {{
    "name": "{tool_name}",
    "version": "{tool_def.get("version", "1.0.0")}",
    "author": "{tool_def.get("author", "Test Author")}",
    "description": "{tool_def.get("description", "Test tool")}"
}}
"""

        tool_file.write_text(tool_content.strip())

        tool_paths[tool_name] = tool_dir

    return tool_paths

def mock_tool_loader(
    tools: Optional[list[Mock]] = None
) -> MagicMock:
    """
    Create a mock tool loader for testing.

    Args:
        tools: List of mock tools to load

    Returns:
        Mock tool loader
    """
    mock_loader = MagicMock()

    if tools is None:
        tools = [
            create_mock_tool("tool1"),
            create_mock_tool("tool2")
        ]

    mock_loader.load_tools.return_value = tools
    mock_loader.get_tool_by_name.side_effect = lambda name: next(
        (p for p in tools if p.name == name), None
    )

    return mock_loader

def create_tool_test_scenarios() -> list[dict[str, Any]]:
    """
    Create test scenarios for tool testing.

    Returns:
        List of tool test scenarios
    """
    return [
        {
            "name": "successful_tool_loading",
            "tools": [
                {"name": "valid_tool1", "version": "1.0.0"},
                {"name": "valid_tool2", "version": "2.0.0"}
            ],
            "expected_result": "success"
        },
        {
            "name": "tool_loading_failure",
            "tools": [
                {"name": "invalid_tool", "version": "1.0.0", "has_error": True}
            ],
            "expected_result": "failure"
        },
        {
            "name": "tool_compatibility_issue",
            "tools": [
                {"name": "old_tool", "version": "0.5.0"},
                {"name": "new_tool", "version": "3.0.0"}
            ],
            "expected_result": "compatibility_warning"
        }
    ]

def simulate_tool_errors(
    error_type: str = "loading",
    tool_name: str = "test_tool"
) -> Callable:
    """
    Create a context manager to simulate tool errors.

    Args:
        error_type: Type of error to simulate
        tool_name: Name of tool to fail

    Returns:
        Context manager for error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "loading": ImportError(f"Cannot load tool {tool_name}"),
            "initialization": RuntimeError(f"Tool {tool_name} initialization failed"),
            "execution": ValueError(f"Tool {tool_name} execution error"),
            "compatibility": RuntimeError(f"Tool {tool_name} compatibility issue")
        }

        error = error_map.get(error_type, RuntimeError("Tool error"))

        with patch('importlib.import_module') as mock_import:
            if error_type == "loading":
                mock_import.side_effect = error
            else:
                mock_tool = create_mock_tool(tool_name)
                if error_type == "initialization":
                    mock_tool.initialize.side_effect = error
                elif error_type == "execution":
                    mock_tool.execute.side_effect = error

                mock_import.return_value = mock_tool

            yield

    return error_context

def verify_tool_functionality(
    tool: Union[Mock, ModuleType],
    test_cases: list[dict[str, Any]]
) -> dict[str, bool]:
    """
    Verify tool functionality against test cases.

    Args:
        tool: Tool to test
        test_cases: List of test cases

    Returns:
        Dictionary of test results
    """
    results = {}

    for test_case in test_cases:
        test_name = test_case["name"]
        try:
            # Call the appropriate tool function
            if test_case["function"] == "initialize":
                result = tool.initialize()
            elif test_case["function"] == "execute":
                result = tool.execute(*test_case.get("args", []), **test_case.get("kwargs", {}))
            elif test_case["function"] == "cleanup":
                result = tool.cleanup()
            else:
                results[test_name] = False
                continue

            # Verify result
            expected = test_case.get("expected", True)
            if result == expected:
                results[test_name] = True
            else:
                results[test_name] = False

        except Exception:
            results[test_name] = False

    return results

def create_tool_dependency_graph(
    tools: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """
    Create a tool dependency graph for testing.

    Args:
        tools: List of tool definitions with dependencies

    Returns:
        Dictionary representing dependency graph
    """
    graph = {}

    for tool in tools:
        tool_name = tool["name"]
        dependencies = tool.get("dependencies", [])

        graph[tool_name] = dependencies

    return graph

def test_tool_dependency_resolution(
    dependency_graph: dict[str, list[str]],
    resolution_order: list[str]
) -> bool:
    """
    Test tool dependency resolution.

    Args:
        dependency_graph: Tool dependency graph
        resolution_order: Proposed resolution order

    Returns:
        True if dependencies are satisfied, False otherwise
    """
    resolved = set()

    for tool in resolution_order:
        # Check if all dependencies are resolved
        dependencies = dependency_graph.get(tool, [])

        for dep in dependencies:
            if dep not in resolved:
                return False

        resolved.add(tool)

    return True

def create_tool_sandbox_environment() -> dict[str, Any]:
    """
    Create a sandbox environment for tool testing.

    Returns:
        Dictionary representing sandbox environment
    """
    return {
        "temp_dir": tempfile.mkdtemp(),
        "allowed_modules": ["os", "sys", "pathlib", "json"],
        "resource_limits": {
            "memory": 1024 * 1024,  # 1MB
            "cpu": 1.0,  # 1 CPU core
            "timeout": 30  # 30 seconds
        },
        "permissions": {
            "file_access": "read_only",
            "network_access": False,
            "process_creation": False
        }
    }

def mock_tool_registry(
    tools: Optional[list[Mock]] = None
) -> MagicMock:
    """
    Create a mock tool registry for testing.

    Args:
        tools: List of tools to register

    Returns:
        Mock tool registry
    """
    mock_registry = MagicMock()

    if tools is None:
        tools = [
            create_mock_tool("registered_tool1"),
            create_mock_tool("registered_tool2")
        ]

    # Mock registry methods
    mock_registry.get_all_tools.return_value = tools
    mock_registry.get_tool.return_value = tools[0] if tools else None
    mock_registry.register_tool.return_value = True
    mock_registry.unregister_tool.return_value = True

    return mock_registry

def create_tool_lifecycle_test_scenarios() -> list[dict[str, Any]]:
    """
    Create test scenarios for tool lifecycle testing.

    Returns:
        List of tool lifecycle test scenarios
    """
    return [
        {
            "name": "normal_lifecycle",
            "steps": [
                {"action": "load", "expected": "success"},
                {"action": "initialize", "expected": "success"},
                {"action": "execute", "expected": "success"},
                {"action": "cleanup", "expected": "success"},
                {"action": "unload", "expected": "success"}
            ]
        },
        {
            "name": "initialization_failure",
            "steps": [
                {"action": "load", "expected": "success"},
                {"action": "initialize", "expected": "failure"},
                {"action": "cleanup", "expected": "success"},
                {"action": "unload", "expected": "success"}
            ]
        },
        {
            "name": "execution_failure",
            "steps": [
                {"action": "load", "expected": "success"},
                {"action": "initialize", "expected": "success"},
                {"action": "execute", "expected": "failure"},
                {"action": "cleanup", "expected": "success"},
                {"action": "unload", "expected": "success"}
            ]
        }
    ]

def benchmark_tool_performance(
    tool: Union[Mock, ModuleType],
    test_data: list[dict[str, Any]],
    iterations: int = 100
) -> dict[str, float]:
    """
    Benchmark tool performance.

    Args:
        tool: Tool to benchmark
        test_data: List of test data inputs
        iterations: Number of iterations

    Returns:
        Dictionary of performance metrics
    """
    import time

    results = {
        "initialize": 0.0,
        "execute": 0.0,
        "cleanup": 0.0
    }

    # Benchmark initialize
    start_time = time.time()
    for _ in range(iterations):
        tool.initialize()
    end_time = time.time()
    results["initialize"] = (end_time - start_time) / iterations

    # Benchmark execute
    start_time = time.time()
    for _ in range(iterations):
        for data in test_data:
            tool.execute(**data)
    end_time = time.time()
    results["execute"] = (end_time - start_time) / (iterations * len(test_data))

    # Benchmark cleanup
    start_time = time.time()
    for _ in range(iterations):
        tool.cleanup()
    end_time = time.time()
    results["cleanup"] = (end_time - start_time) / iterations

    return results

def create_tool_security_test_scenarios() -> list[dict[str, Any]]:
    """
    Create test scenarios for tool security testing.

    Returns:
        List of tool security test scenarios
    """
    return [
        {
            "name": "safe_tool",
            "tool_code": """
def execute():
    return {"result": "success"}
""",
            "expected_result": "allowed"
        },
        {
            "name": "dangerous_tool",
            "tool_code": """
import os
def execute():
    os.system("rm -rf /")
    return {"result": "success"}
""",
            "expected_result": "blocked"
        },
        {
            "name": "resource_intensive_tool",
            "tool_code": """
def execute():
    while True:
        pass
    return {"result": "success"}
""",
            "expected_result": "timeout"
        }
    ]
