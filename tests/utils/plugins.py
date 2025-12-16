# Plugin Test Utilities
# Helper functions for plugin system testing

import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from unittest.mock import MagicMock, patch, Mock
import importlib
import sys
from types import ModuleType
import contextlib

def create_mock_plugin(
    name: str = "test_plugin",
    functions: Optional[Dict[str, Callable]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Mock:
    """
    Create a mock plugin for testing.

    Args:
        name: Plugin name
        functions: Dictionary of plugin functions
        metadata: Plugin metadata

    Returns:
        Mock plugin object
    """
    mock_plugin = Mock()
    mock_plugin.name = name

    # Set up plugin metadata
    if metadata is None:
        metadata = {
            "name": name,
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Test plugin for testing"
        }

    mock_plugin.metadata = metadata

    # Set up plugin functions
    if functions is None:
        functions = {
            "initialize": lambda: True,
            "execute": lambda *args, **kwargs: {"result": "success"},
            "cleanup": lambda: None
        }

    for func_name, func_impl in functions.items():
        setattr(mock_plugin, func_name, func_impl)

    return mock_plugin

def create_plugin_directory_structure(
    base_path: Path,
    plugins: List[Dict[str, Any]]
) -> Dict[str, Path]:
    """
    Create a plugin directory structure for testing.

    Args:
        base_path: Base directory path
        plugins: List of plugin definitions

    Returns:
        Dictionary mapping plugin names to their paths
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    plugin_paths = {}

    for plugin_def in plugins:
        plugin_name = plugin_def["name"]
        plugin_dir = base_path / plugin_name

        if not plugin_dir.exists():
            plugin_dir.mkdir()

        # Create __init__.py
        init_file = plugin_dir / "__init__.py"
        init_file.write_text(f"# {plugin_name} plugin\n")

        # Create main plugin file
        plugin_file = plugin_dir / f"{plugin_name}.py"
        plugin_content = f"""
# {plugin_name} Plugin Implementation

def initialize():
    '''Initialize the plugin'''
    return True

def execute(*args, **kwargs):
    '''Execute plugin functionality'''
    return {{"plugin": "{plugin_name}", "status": "success"}}

def cleanup():
    '''Clean up plugin resources'''
    pass

metadata = {{
    "name": "{plugin_name}",
    "version": "{plugin_def.get("version", "1.0.0")}",
    "author": "{plugin_def.get("author", "Test Author")}",
    "description": "{plugin_def.get("description", "Test plugin")}"
}}
"""

        plugin_file.write_text(plugin_content.strip())

        plugin_paths[plugin_name] = plugin_dir

    return plugin_paths

def mock_plugin_loader(
    plugins: Optional[List[Mock]] = None
) -> MagicMock:
    """
    Create a mock plugin loader for testing.

    Args:
        plugins: List of mock plugins to load

    Returns:
        Mock plugin loader
    """
    mock_loader = MagicMock()

    if plugins is None:
        plugins = [
            create_mock_plugin("plugin1"),
            create_mock_plugin("plugin2")
        ]

    mock_loader.load_plugins.return_value = plugins
    mock_loader.get_plugin_by_name.side_effect = lambda name: next(
        (p for p in plugins if p.name == name), None
    )

    return mock_loader

def create_plugin_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create test scenarios for plugin testing.

    Returns:
        List of plugin test scenarios
    """
    return [
        {
            "name": "successful_plugin_loading",
            "plugins": [
                {"name": "valid_plugin1", "version": "1.0.0"},
                {"name": "valid_plugin2", "version": "2.0.0"}
            ],
            "expected_result": "success"
        },
        {
            "name": "plugin_loading_failure",
            "plugins": [
                {"name": "invalid_plugin", "version": "1.0.0", "has_error": True}
            ],
            "expected_result": "failure"
        },
        {
            "name": "plugin_compatibility_issue",
            "plugins": [
                {"name": "old_plugin", "version": "0.5.0"},
                {"name": "new_plugin", "version": "3.0.0"}
            ],
            "expected_result": "compatibility_warning"
        }
    ]

def simulate_plugin_errors(
    error_type: str = "loading",
    plugin_name: str = "test_plugin"
) -> Callable:
    """
    Create a context manager to simulate plugin errors.

    Args:
        error_type: Type of error to simulate
        plugin_name: Name of plugin to fail

    Returns:
        Context manager for error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "loading": ImportError(f"Cannot load plugin {plugin_name}"),
            "initialization": RuntimeError(f"Plugin {plugin_name} initialization failed"),
            "execution": ValueError(f"Plugin {plugin_name} execution error"),
            "compatibility": RuntimeError(f"Plugin {plugin_name} compatibility issue")
        }

        error = error_map.get(error_type, RuntimeError("Plugin error"))

        with patch('importlib.import_module') as mock_import:
            if error_type == "loading":
                mock_import.side_effect = error
            else:
                mock_plugin = create_mock_plugin(plugin_name)
                if error_type == "initialization":
                    mock_plugin.initialize.side_effect = error
                elif error_type == "execution":
                    mock_plugin.execute.side_effect = error

                mock_import.return_value = mock_plugin

            yield

    return error_context

def verify_plugin_functionality(
    plugin: Union[Mock, ModuleType],
    test_cases: List[Dict[str, Any]]
) -> Dict[str, bool]:
    """
    Verify plugin functionality against test cases.

    Args:
        plugin: Plugin to test
        test_cases: List of test cases

    Returns:
        Dictionary of test results
    """
    results = {}

    for test_case in test_cases:
        test_name = test_case["name"]
        try:
            # Call the appropriate plugin function
            if test_case["function"] == "initialize":
                result = plugin.initialize()
            elif test_case["function"] == "execute":
                result = plugin.execute(*test_case.get("args", []), **test_case.get("kwargs", {}))
            elif test_case["function"] == "cleanup":
                result = plugin.cleanup()
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

def create_plugin_dependency_graph(
    plugins: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """
    Create a plugin dependency graph for testing.

    Args:
        plugins: List of plugin definitions with dependencies

    Returns:
        Dictionary representing dependency graph
    """
    graph = {}

    for plugin in plugins:
        plugin_name = plugin["name"]
        dependencies = plugin.get("dependencies", [])

        graph[plugin_name] = dependencies

    return graph

def test_plugin_dependency_resolution(
    dependency_graph: Dict[str, List[str]],
    resolution_order: List[str]
) -> bool:
    """
    Test plugin dependency resolution.

    Args:
        dependency_graph: Plugin dependency graph
        resolution_order: Proposed resolution order

    Returns:
        True if dependencies are satisfied, False otherwise
    """
    resolved = set()

    for plugin in resolution_order:
        # Check if all dependencies are resolved
        dependencies = dependency_graph.get(plugin, [])

        for dep in dependencies:
            if dep not in resolved:
                return False

        resolved.add(plugin)

    return True

def create_plugin_sandbox_environment() -> Dict[str, Any]:
    """
    Create a sandbox environment for plugin testing.

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

def mock_plugin_registry(
    plugins: Optional[List[Mock]] = None
) -> MagicMock:
    """
    Create a mock plugin registry for testing.

    Args:
        plugins: List of plugins to register

    Returns:
        Mock plugin registry
    """
    mock_registry = MagicMock()

    if plugins is None:
        plugins = [
            create_mock_plugin("registered_plugin1"),
            create_mock_plugin("registered_plugin2")
        ]

    # Mock registry methods
    mock_registry.get_all_plugins.return_value = plugins
    mock_registry.get_plugin.return_value = plugins[0] if plugins else None
    mock_registry.register_plugin.return_value = True
    mock_registry.unregister_plugin.return_value = True

    return mock_registry

def create_plugin_lifecycle_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create test scenarios for plugin lifecycle testing.

    Returns:
        List of plugin lifecycle test scenarios
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

def benchmark_plugin_performance(
    plugin: Union[Mock, ModuleType],
    test_data: List[Dict[str, Any]],
    iterations: int = 100
) -> Dict[str, float]:
    """
    Benchmark plugin performance.

    Args:
        plugin: Plugin to benchmark
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
        plugin.initialize()
    end_time = time.time()
    results["initialize"] = (end_time - start_time) / iterations

    # Benchmark execute
    start_time = time.time()
    for _ in range(iterations):
        for data in test_data:
            plugin.execute(**data)
    end_time = time.time()
    results["execute"] = (end_time - start_time) / (iterations * len(test_data))

    # Benchmark cleanup
    start_time = time.time()
    for _ in range(iterations):
        plugin.cleanup()
    end_time = time.time()
    results["cleanup"] = (end_time - start_time) / iterations

    return results

def create_plugin_security_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create test scenarios for plugin security testing.

    Returns:
        List of plugin security test scenarios
    """
    return [
        {
            "name": "safe_plugin",
            "plugin_code": """
def execute():
    return {"result": "success"}
""",
            "expected_result": "allowed"
        },
        {
            "name": "dangerous_plugin",
            "plugin_code": """
import os
def execute():
    os.system("rm -rf /")
    return {"result": "success"}
""",
            "expected_result": "blocked"
        },
        {
            "name": "resource_intensive_plugin",
            "plugin_code": """
def execute():
    while True:
        pass
    return {"result": "success"}
""",
            "expected_result": "timeout"
        }
    ]
