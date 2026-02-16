"""Test tool lifecycle functionality."""

from unittest.mock import Mock, patch

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.lifecycle import ToolLifecycleError, ToolLifecycleManager, ToolState
from nodupe.core.tool_system.registry import ToolRegistry


class TestToolState:
    """Test ToolState enum functionality."""

    def test_tool_state_values(self):
        """Test ToolState enum values."""
        assert ToolState.UNLOADED.value == "unloaded"
        assert ToolState.LOADED.value == "loaded"
        assert ToolState.INITIALIZING.value == "initializing"
        assert ToolState.INITIALIZED.value == "initialized"
        assert ToolState.SHUTTING_DOWN.value == "shutting_down"
        assert ToolState.SHUTDOWN.value == "shutdown"
        assert ToolState.ERROR.value == "error"


class TestToolLifecycleManagerInitialization:
    """Test ToolLifecycleManager initialization functionality."""

    def test_lifecycle_manager_creation(self):
        """Test ToolLifecycleManager instance creation."""
        manager = ToolLifecycleManager()

        assert manager is not None
        assert manager._tool_states == {}
        assert manager._tool_dependencies == {}
        assert manager._tool_containers == {}
        assert manager.container is None

    def test_lifecycle_manager_with_registry(self):
        """Test ToolLifecycleManager with registry."""
        mock_registry = Mock()
        manager = ToolLifecycleManager(mock_registry)

        assert manager.registry is mock_registry

    def test_lifecycle_manager_initialize(self):
        """Test ToolLifecycleManager initialization with container."""
        manager = ToolLifecycleManager()
        container = Mock()

        manager.initialize(container)

        assert manager.container is container


class TestToolLifecycleInitialization:
    """Test tool initialization functionality."""

    def test_initialize_tool_success(self):
        """Test successful tool initialization."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock()

        result = manager.initialize_tool(mock_tool, container)

        assert result is True
        mock_tool.initialize.assert_called_once_with(container)
        assert manager.get_tool_state("TestTool") == ToolState.INITIALIZED

    def test_initialize_tool_already_initialized(self):
        """Test initializing an already initialized tool."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock()

        # Set initial state to initialized
        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        result = manager.initialize_tool(mock_tool, container)

        # Should return True without calling initialize again
        assert result is True
        mock_tool.initialize.assert_not_called()
        assert manager.get_tool_state("TestTool") == ToolState.INITIALIZED

    def test_initialize_tool_dependencies_satisfied(self):
        """Test tool initialization with satisfied dependencies."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock()

        # Set up dependencies
        manager._tool_states["DependencyTool"] = ToolState.INITIALIZED
        dependencies = ["DependencyTool"]

        result = manager.initialize_tool(mock_tool, container, dependencies)

        assert result is True
        mock_tool.initialize.assert_called_once_with(container)
        assert manager.get_tool_state("TestTool") == ToolState.INITIALIZED

    def test_initialize_tool_dependencies_not_satisfied(self):
        """Test tool initialization with unsatisfied dependencies."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock()

        # Set up dependencies that are not satisfied
        dependencies = ["MissingDependency"]

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager.initialize_tool(mock_tool, container, dependencies)

        assert "Dependencies not satisfied" in str(exc_info.value)
        mock_tool.initialize.assert_not_called()
        assert manager.get_tool_state("TestTool") == ToolState.ERROR

    def test_initialize_tool_failure(self):
        """Test tool initialization failure."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock(side_effect=Exception("Init failed"))

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager.initialize_tool(mock_tool, container)

        assert "Failed to initialize tool" in str(exc_info.value)
        assert manager.get_tool_state("TestTool") == ToolState.ERROR

    def test_initialize_multiple_tools(self):
        """Test initializing multiple tools."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.initialize = Mock()

        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.initialize = Mock()

        tools = [mock_tool1, mock_tool2]
        manager.initialize_tools(tools)

        mock_tool1.initialize.assert_called_once_with(container)
        mock_tool2.initialize.assert_called_once_with(container)
        assert manager.get_tool_state("Tool1") == ToolState.INITIALIZED
        assert manager.get_tool_state("Tool2") == ToolState.INITIALIZED


class TestToolLifecycleShutdown:
    """Test tool shutdown functionality."""

    def test_shutdown_tool_success(self):
        """Test successful tool shutdown."""
        manager = ToolLifecycleManager()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.shutdown = Mock()

        # Set initial state to initialized
        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        result = manager.shutdown_tool("TestTool")

        assert result is True
        mock_tool.shutdown.assert_called_once()
        assert manager.get_tool_state("TestTool") == ToolState.SHUTDOWN

    def test_shutdown_tool_not_found(self):
        """Test shutting down a non-existent tool."""
        manager = ToolLifecycleManager()

        result = manager.shutdown_tool("NonExistentTool")

        assert result is False

    def test_shutdown_tool_already_shutdown(self):
        """Test shutting down an already shutdown tool."""
        manager = ToolLifecycleManager()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.shutdown = Mock()

        # Set initial state to shutdown
        manager._tool_states["TestTool"] = ToolState.SHUTDOWN

        result = manager.shutdown_tool("TestTool")

        assert result is True  # Should return True even if already shutdown
        mock_tool.shutdown.assert_not_called()
        assert manager.get_tool_state("TestTool") == ToolState.SHUTDOWN

    def test_shutdown_tool_with_error(self):
        """Test tool shutdown with error during shutdown."""
        manager = ToolLifecycleManager()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.shutdown = Mock(side_effect=Exception("Shutdown failed"))

        # Set initial state to initialized
        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        # Should not raise exception, just log warning
        result = manager.shutdown_tool("TestTool")

        assert result is True
        mock_tool.shutdown.assert_called_once()
        # State should still transition to SHUTDOWN despite error
        assert manager.get_tool_state("TestTool") == ToolState.SHUTDOWN

    def test_shutdown_multiple_tools(self):
        """Test shutting down multiple tools."""
        manager = ToolLifecycleManager()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.shutdown = Mock()

        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.shutdown = Mock()

        # Set initial states
        manager._tool_states["Tool1"] = ToolState.INITIALIZED
        manager._tool_states["Tool2"] = ToolState.INITIALIZED

        tools = [mock_tool1, mock_tool2]
        manager.shutdown_tools(tools)

        mock_tool1.shutdown.assert_called_once()
        mock_tool2.shutdown.assert_called_once()
        assert manager.get_tool_state("Tool1") == ToolState.SHUTDOWN
        assert manager.get_tool_state("Tool2") == ToolState.SHUTDOWN

    def test_shutdown_all_tools(self):
        """Test shutting down all tools."""
        manager = ToolLifecycleManager()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.shutdown = Mock()

        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.shutdown = Mock()

        # Set up registry to return tools
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool1, mock_tool2]
        manager.registry = mock_registry

        # Set initial states
        manager._tool_states["Tool1"] = ToolState.INITIALIZED
        manager._tool_states["Tool2"] = ToolState.INITIALIZED

        result = manager.shutdown_all_tools()

        assert result is True
        mock_tool1.shutdown.assert_called_once()
        mock_tool2.shutdown.assert_called_once()
        assert manager.get_tool_state("Tool1") == ToolState.SHUTDOWN
        assert manager.get_tool_state("Tool2") == ToolState.SHUTDOWN


class TestToolLifecycleStateManagement:
    """Test tool lifecycle state management functionality."""

    def test_get_tool_states(self):
        """Test getting all tool states."""
        manager = ToolLifecycleManager()

        # Set up some states
        manager._tool_states = {
            "Tool1": ToolState.INITIALIZED,
            "Tool2": ToolState.SHUTDOWN,
            "Tool3": ToolState.ERROR
        }

        result = manager.get_tool_states()

        assert result == {
            "Tool1": ToolState.INITIALIZED,
            "Tool2": ToolState.SHUTDOWN,
            "Tool3": ToolState.ERROR
        }
        # Should return a copy, not the original dict
        assert result is not manager._tool_states

    def test_get_tool_state(self):
        """Test getting a specific tool state."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        result = manager.get_tool_state("TestTool")
        assert result == ToolState.INITIALIZED

        # Test for non-existent tool
        result = manager.get_tool_state("NonExistentTool")
        assert result == ToolState.UNLOADED

    def test_is_tool_initialized(self):
        """Test checking if a tool is initialized."""
        manager = ToolLifecycleManager()

        # Test initialized tool
        manager._tool_states["InitializedTool"] = ToolState.INITIALIZED
        assert manager.is_tool_initialized("InitializedTool") is True

        # Test non-initialized tool
        manager._tool_states["NonInitializedTool"] = ToolState.UNLOADED
        assert manager.is_tool_initialized("NonInitializedTool") is False

        # Test non-existent tool
        assert manager.is_tool_initialized("NonExistentTool") is False

    def test_is_tool_active(self):
        """Test checking if a tool is active."""
        manager = ToolLifecycleManager()

        # Test initialized tool
        manager._tool_states["InitializedTool"] = ToolState.INITIALIZED
        assert manager.is_tool_active("InitializedTool") is True

        # Test initializing tool
        manager._tool_states["InitializingTool"] = ToolState.INITIALIZING
        assert manager.is_tool_active("InitializingTool") is True

        # Test shutdown tool
        manager._tool_states["ShutdownTool"] = ToolState.SHUTDOWN
        assert manager.is_tool_active("ShutdownTool") is False

        # Test non-existent tool
        assert manager.is_tool_active("NonExistentTool") is False

    def test_get_active_tools(self):
        """Test getting active tools."""
        manager = ToolLifecycleManager()

        # Set up various states
        manager._tool_states = {
            "ActiveTool1": ToolState.INITIALIZED,
            "ActiveTool2": ToolState.INITIALIZING,
            "InactiveTool": ToolState.SHUTDOWN,
            "UnloadedTool": ToolState.UNLOADED
        }

        result = manager.get_active_tools()

        assert "ActiveTool1" in result
        assert "ActiveTool2" in result
        assert "InactiveTool" not in result
        assert "UnloadedTool" not in result
        assert len(result) == 2


class TestToolLifecycleDependencies:
    """Test tool lifecycle dependency management functionality."""

    def test_get_set_tool_dependencies(self):
        """Test getting and setting tool dependencies."""
        manager = ToolLifecycleManager()

        # Set dependencies
        dependencies = ["Dep1", "Dep2", "Dep3"]
        manager.set_tool_dependencies("TestTool", dependencies)

        # Get dependencies
        result = manager.get_tool_dependencies("TestTool")

        assert result == dependencies

    def test_get_tool_dependencies_default(self):
        """Test getting dependencies for tool with no dependencies."""
        manager = ToolLifecycleManager()

        result = manager.get_tool_dependencies("NonExistentTool")

        assert result == []

    def test_check_dependencies_satisfied(self):
        """Test checking if dependencies are satisfied."""
        manager = ToolLifecycleManager()

        # Set up satisfied dependencies
        manager._tool_states["Dep1"] = ToolState.INITIALIZED
        manager._tool_dependencies["TestTool"] = ["Dep1"]

        result = manager._check_dependencies("TestTool")
        assert result is True

    def test_check_dependencies_not_satisfied(self):
        """Test checking if dependencies are not satisfied."""
        manager = ToolLifecycleManager()

        # Set up unsatisfied dependencies
        manager._tool_states["Dep1"] = ToolState.UNLOADED  # Not initialized
        manager._tool_dependencies["TestTool"] = ["Dep1"]

        result = manager._check_dependencies("TestTool")
        assert result is False

    def test_check_dependencies_missing(self):
        """Test checking dependencies that don't exist."""
        manager = ToolLifecycleManager()

        # Set up dependency that doesn't exist in states
        manager._tool_dependencies["TestTool"] = ["MissingDep"]

        result = manager._check_dependencies("TestTool")
        assert result is False

    def test_check_dependencies_empty(self):
        """Test checking empty dependencies."""
        manager = ToolLifecycleManager()

        # No dependencies set
        result = manager._check_dependencies("TestTool")
        assert result is True


class TestToolLifecycleAllTools:
    """Test lifecycle management for all tools."""

    def test_initialize_all_tools_success(self):
        """Test successful initialization of all tools."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.initialize = Mock()

        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.initialize = Mock()

        # Set up registry to return tools
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool1, mock_tool2]
        manager.registry = mock_registry

        result = manager.initialize_all_tools(container)

        assert result is True
        mock_tool1.initialize.assert_called_once_with(container)
        mock_tool2.initialize.assert_called_once_with(container)
        assert manager.get_tool_state("Tool1") == ToolState.INITIALIZED
        assert manager.get_tool_state("Tool2") == ToolState.INITIALIZED

    def test_initialize_all_tools_failure(self):
        """Test initialization failure of one tool."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.initialize = Mock()

        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.initialize = Mock(side_effect=Exception("Init failed"))

        # Set up registry to return tools
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool1, mock_tool2]
        manager.registry = mock_registry

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager.initialize_all_tools(container)

        assert "Failed to initialize tool" in str(exc_info.value)
        # First tool should be initialized, second should fail
        mock_tool1.initialize.assert_called_once_with(container)
        mock_tool2.initialize.assert_called_once_with(container)
        assert manager.get_tool_state("Tool1") == ToolState.INITIALIZED
        assert manager.get_tool_state("Tool2") == ToolState.ERROR

    def test_sort_tools_by_dependencies(self):
        """Test sorting tools by dependencies."""
        manager = ToolLifecycleManager()

        mock_tool_a = Mock()
        mock_tool_a.name = "ToolA"

        mock_tool_b = Mock()
        mock_tool_b.name = "ToolB"

        mock_tool_c = Mock()
        mock_tool_c.name = "ToolC"

        tools = [mock_tool_a, mock_tool_b, mock_tool_c]

        # Set up dependencies: ToolC depends on ToolB, ToolB depends on ToolA
        manager.set_tool_dependencies("ToolB", ["ToolA"])
        manager.set_tool_dependencies("ToolC", ["ToolB"])
        # ToolA has no dependencies

        result = manager._sort_tools_by_dependencies(tools)

        # Should be sorted as: ToolA, ToolB, ToolC (dependencies first)
        assert result[0].name == "ToolA"
        assert result[1].name == "ToolB"
        assert result[2].name == "ToolC"

    def test_sort_tools_by_dependencies_circular(self):
        """Test sorting tools with circular dependencies."""
        manager = ToolLifecycleManager()

        mock_tool_a = Mock()
        mock_tool_a.name = "ToolA"

        mock_tool_b = Mock()
        mock_tool_b.name = "ToolB"

        tools = [mock_tool_a, mock_tool_b]

        # Set up circular dependencies: A depends on B, B depends on A
        manager.set_tool_dependencies("ToolA", ["ToolB"])
        manager.set_tool_dependencies("ToolB", ["ToolA"])

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager._sort_tools_by_dependencies(tools)

        assert "Circular dependency detected" in str(exc_info.value)
