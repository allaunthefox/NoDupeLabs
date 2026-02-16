"""Test tool registry functionality."""

import pytest
from unittest.mock import Mock
from nodupe.core.tool_system.registry import ToolRegistry
from nodupe.core.tool_system.base import Tool


class TestToolRegistryInitialization:
    """Test ToolRegistry initialization functionality."""

    def test_tool_registry_singleton(self):
        """Test ToolRegistry singleton pattern."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        assert registry1 is registry2
        assert registry1._instance is registry2._instance

    def test_tool_registry_initial_state(self):
        """Test ToolRegistry initial state."""
        registry = ToolRegistry()
        
        assert registry._tools == {}
        assert registry._initialized is False
        assert registry.container is None

    def test_tool_registry_initialize(self):
        """Test ToolRegistry initialization with container."""
        registry = ToolRegistry()
        container = Mock()
        
        registry.initialize(container)
        
        assert registry._container is container
        assert registry._initialized is True
        assert registry.container is container


class TestToolRegistryRegistration:
    """Test tool registration functionality."""

    def test_register_tool_success(self):
        """Test successful tool registration."""
        registry = ToolRegistry()
        
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock()
        
        registry.register(mock_tool)
        
        assert "TestTool" in registry._tools
        assert registry._tools["TestTool"] is mock_tool
        # initialize should not be called if no container
        mock_tool.initialize.assert_not_called()

    def test_register_tool_with_container(self):
        """Test tool registration with container."""
        registry = ToolRegistry()
        container = Mock()
        registry.initialize(container)
        
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.initialize = Mock()
        
        registry.register(mock_tool)
        
        assert "TestTool" in registry._tools
        assert registry._tools["TestTool"] is mock_tool
        mock_tool.initialize.assert_called_once_with(container)

    def test_register_duplicate_tool(self):
        """Test registering a duplicate tool."""
        registry = ToolRegistry()
        
        mock_tool1 = Mock()
        mock_tool1.name = "TestTool"
        
        mock_tool2 = Mock()
        mock_tool2.name = "TestTool"  # Same name
        
        registry.register(mock_tool1)
        
        with pytest.raises(ValueError) as exc_info:
            registry.register(mock_tool2)
        
        assert "already registered" in str(exc_info.value)

    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.shutdown = Mock()
        
        registry.register(mock_tool)
        
        # Verify tool is registered
        assert "TestTool" in registry._tools
        
        # Unregister the tool
        registry.unregister("TestTool")
        
        # Verify tool is unregistered
        assert "TestTool" not in registry._tools
        mock_tool.shutdown.assert_called_once()

    def test_unregister_nonexistent_tool(self):
        """Test unregistering a nonexistent tool."""
        registry = ToolRegistry()
        
        with pytest.raises(KeyError) as exc_info:
            registry.unregister("NonExistentTool")
        
        assert "not found" in str(exc_info.value)

    def test_get_tool(self):
        """Test getting a registered tool."""
        registry = ToolRegistry()
        
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        
        registry.register(mock_tool)
        
        result = registry.get_tool("TestTool")
        assert result is mock_tool

    def test_get_nonexistent_tool(self):
        """Test getting a nonexistent tool."""
        registry = ToolRegistry()
        
        result = registry.get_tool("NonExistentTool")
        assert result is None

    def test_get_tools(self):
        """Test getting all registered tools."""
        registry = ToolRegistry()
        
        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        
        registry.register(mock_tool1)
        registry.register(mock_tool2)
        
        result = registry.get_tools()
        
        # Should return a list of the tools
        assert len(result) == 2
        assert mock_tool1 in result
        assert mock_tool2 in result
        
        # Verify it returns a copy, not the original dict values
        assert result is not list(registry._tools.values())


class TestToolRegistryLifecycle:
    """Test tool registry lifecycle functionality."""

    def test_clear_all_tools(self):
        """Test clearing all tools."""
        registry = ToolRegistry()
        
        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        
        registry.register(mock_tool1)
        registry.register(mock_tool2)
        
        # Verify tools are registered
        assert len(registry._tools) == 2
        
        # Clear all tools
        registry.clear()
        
        # Verify tools are cleared
        assert len(registry._tools) == 0

    def test_shutdown_all_tools(self):
        """Test shutting down all tools."""
        registry = ToolRegistry()
        
        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.shutdown = Mock()
        
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.shutdown = Mock()
        
        registry.register(mock_tool1)
        registry.register(mock_tool2)
        
        # Shutdown all tools
        registry.shutdown()
        
        # Verify all tools were shut down
        mock_tool1.shutdown.assert_called_once()
        mock_tool2.shutdown.assert_called_once()
        
        # Verify tools were removed
        assert len(registry._tools) == 0
        
        # Verify internal state was reset
        assert registry._container is None
        assert registry._initialized is False

    def test_shutdown_all_tools_with_exception(self):
        """Test shutting down all tools with one throwing an exception."""
        registry = ToolRegistry()
        
        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.shutdown = Mock(side_effect=Exception("Shutdown failed"))
        
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.shutdown = Mock()
        
        registry.register(mock_tool1)
        registry.register(mock_tool2)
        
        # Shutdown all tools - should continue despite exception
        registry.shutdown()
        
        # Both tools should have been attempted to be shut down
        mock_tool1.shutdown.assert_called_once()
        mock_tool2.shutdown.assert_called_once()
        
        # Tools should still be removed despite exception
        assert len(registry._tools) == 0

    def test_reset_instance(self):
        """Test resetting the singleton instance."""
        registry1 = ToolRegistry()
        
        # Add a tool to verify it's gone after reset
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        registry1.register(mock_tool)
        
        assert len(registry1._tools) == 1
        
        # Reset the instance
        ToolRegistry._reset_instance()
        
        # Create a new instance
        registry2 = ToolRegistry()
        
        # Should be a fresh instance
        assert registry1 is not registry2
        assert len(registry2._tools) == 0


class TestToolRegistryContainer:
    """Test tool registry container functionality."""

    def test_container_property(self):
        """Test container property access."""
        registry = ToolRegistry()
        
        # Initially should be None
        assert registry.container is None
        
        # Set container
        container = Mock()
        registry._container = container
        
        # Should return the container
        assert registry.container is container

    def test_initialize_with_container(self):
        """Test initialization with container."""
        registry = ToolRegistry()
        container = Mock()
        
        registry.initialize(container)
        
        assert registry._container is container
        assert registry.container is container
        assert registry._initialized is True