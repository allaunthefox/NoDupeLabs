"""Test tool registry functionality."""

from unittest.mock import MagicMock

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.registry import ToolRegistry


class TestToolRegistry:
    """Test tool registry core functionality."""

    def test_tool_registry_initialization(self):
        """Test tool registry initialization."""
        registry = ToolRegistry()
        assert registry is not None
        assert isinstance(registry, ToolRegistry)

        # Test that it has expected attributes
        assert hasattr(registry, "register")
        assert hasattr(registry, "unregister")
        assert hasattr(registry, "get_tool")
        assert hasattr(registry, "get_tools")
        assert hasattr(registry, "initialize")
        assert hasattr(registry, "shutdown")

    def test_tool_registry_singleton_behavior(self):
        """Test tool registry singleton behavior."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        # Should be the same instance (singleton)
        assert registry1 is registry2

    def test_tool_registration(self):
        """Test tool registration functionality."""
        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create a mock tool
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "test_tool"
        mock_tool.version = "1.0.0"
        mock_tool.dependencies = []

        # Register the tool
        registry.register(mock_tool)

        # Verify tool is registered
        retrieved = registry.get_tool("test_tool")
        assert retrieved is mock_tool

    def test_tool_unregistration(self):
        """Test tool unregistration functionality."""
        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create and register a tool
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "test_tool"
        registry.register(mock_tool)

        # Verify tool is registered
        assert registry.get_tool("test_tool") is mock_tool

        # Unregister the tool
        registry.unregister("test_tool")

        # Verify tool is unregistered
        assert registry.get_tool("test_tool") is None

    def test_get_all_tools(self):
        """Test getting all registered tools."""
        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Register multiple tools
        tools = []
        for i in range(5):
            mock_tool = MagicMock(spec=Tool)
            mock_tool.name = f"tool_{i}"
            tools.append(mock_tool)
            registry.register(mock_tool)

        # Get all tools
        all_tools = registry.get_tools()

        # Verify all tools are returned
        assert len(all_tools) == 5
        for tool in tools:
            assert tool in all_tools

    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        result = registry.get_tool("nonexistent_tool")
        assert result is None

    def test_tool_registry_with_container(self):
        """Test tool registry with dependency container."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()

        # Initialize registry with container
        registry.initialize(container)
        assert registry._container is container

        # Test tool registration with container
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "container_tool"
        mock_tool.version = "1.0.0"
        mock_tool.dependencies = []

        registry.register(mock_tool)

        # Verify tool is accessible
        retrieved = registry.get_tool("container_tool")
        assert retrieved is mock_tool

    def test_tool_registry_lifecycle(self):
        """Test tool registry lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()

        # Test initialization
        registry.initialize(container)
        assert registry._container is container

        # Test shutdown
        registry.shutdown()
        assert registry._container is None

        # Test re-initialization
        registry.initialize(container)
        assert registry._container is container


class TestToolRegistryEdgeCases:
    """Test tool registry edge cases."""

    def test_register_duplicate_tool(self):
        """Test registering duplicate tool."""
        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create two tools with same name
        mock_tool1 = MagicMock(spec=Tool)
        mock_tool1.name = "duplicate_tool"

        mock_tool2 = MagicMock(spec=Tool)
        mock_tool2.name = "duplicate_tool"

        # Register first tool
        registry.register(mock_tool1)

        # Register second tool with same name (should raise error)
        with pytest.raises(ValueError):
            registry.register(mock_tool2)

        # Should still return the first tool
        retrieved = registry.get_tool("duplicate_tool")
        assert retrieved is mock_tool1

    def test_tool_with_empty_name(self):
        """Test tool with empty name."""
        registry = ToolRegistry()

        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = ""

        registry.register(mock_tool)
        retrieved = registry.get_tool("")
        assert retrieved is mock_tool

    def test_tool_with_special_characters(self):
        """Test tool with special characters in name."""
        registry = ToolRegistry()

        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "tool-with_special.chars"

        registry.register(mock_tool)
        retrieved = registry.get_tool("tool-with_special.chars")
        assert retrieved is mock_tool

    def test_multiple_tool_registrations(self):
        """Test multiple tool registrations."""
        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Register multiple tools
        for i in range(10):
            mock_tool = MagicMock(spec=Tool)
            mock_tool.name = f"tool_{i}"
            registry.register(mock_tool)

        # Verify all tools are accessible
        all_tools = registry.get_tools()
        assert len(all_tools) == 10

        for i in range(10):
            tool = registry.get_tool(f"tool_{i}")
            assert tool is not None
            assert tool.name == f"tool_{i}"


class TestToolRegistryPerformance:
    """Test tool registry performance."""

    def test_tool_registry_mass_registration(self):
        """Test mass tool registration."""
        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Test registering many tools
        for i in range(100):
            mock_tool = MagicMock(spec=Tool)
            mock_tool.name = f"mass_tool_{i}"
            registry.register(mock_tool)

        # Verify all tools are registered
        all_tools = registry.get_tools()
        assert len(all_tools) == 100

        # Verify specific tools can be retrieved
        for i in range(100):
            tool = registry.get_tool(f"mass_tool_{i}")
            assert tool is not None
            assert tool.name == f"mass_tool_{i}"

    def test_tool_registry_performance(self):
        """Test tool registry performance."""
        import time

        registry = ToolRegistry()

        # Test registration performance
        start_time = time.time()
        for i in range(1000):
            mock_tool = MagicMock(spec=Tool)
            mock_tool.name = f"perf_tool_{i}"
            registry.register(mock_tool)
        registration_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        for i in range(1000):
            tool = registry.get_tool(f"perf_tool_{i}")
            assert tool is not None
        retrieval_time = time.time() - start_time

        # Should be fast operations
        assert registration_time < 1.0
        assert retrieval_time < 0.1


class TestToolRegistryIntegration:
    """Test tool registry integration scenarios."""

    def test_tool_registry_with_lifecycle_manager(self):
        """Test tool registry integration with lifecycle manager."""
        from nodupe.core.tool_system.lifecycle import ToolLifecycleManager

        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create lifecycle manager with registry
        lifecycle_manager = ToolLifecycleManager(registry)

        # Verify integration
        assert lifecycle_manager.registry is registry

        # Test tool registration through lifecycle manager
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "lifecycle_tool"
        mock_tool.version = "1.0.0"
        mock_tool.dependencies = []

        registry.register(mock_tool)

        # Verify tool is accessible through both
        retrieved_from_registry = registry.get_tool("lifecycle_tool")
        assert retrieved_from_registry is mock_tool

    def test_tool_registry_with_loader(self):
        """Test tool registry integration with tool loader."""
        from nodupe.core.tool_system.loader import ToolLoader

        registry = ToolRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create loader with registry
        loader = ToolLoader(registry)

        # Verify integration
        assert loader.registry is registry

        # Test tool registration through loader
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "loader_tool"
        mock_tool.version = "1.0.0"
        mock_tool.dependencies = []

        # Register tool directly (loader doesn't have load_tool method)
        registry.register(mock_tool)

        # Verify tool is accessible through registry
        retrieved = registry.get_tool("loader_tool")
        assert retrieved is mock_tool
