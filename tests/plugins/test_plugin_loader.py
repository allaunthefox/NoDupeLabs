"""Test tool loader functionality."""

from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError
from nodupe.core.tool_system.registry import ToolRegistry


class TestToolLoader:
    """Test tool loader core functionality."""

    def test_tool_loader_initialization(self):
        """Test tool loader initialization."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        assert loader is not None
        assert isinstance(loader, ToolLoader)
        assert loader.registry is registry

        # Test that it has expected attributes
        assert hasattr(loader, "load_tool")
        assert hasattr(loader, "unload_tool")
        assert hasattr(loader, "get_loaded_tools")
        assert hasattr(loader, "get_loaded_tool")
        assert hasattr(loader, "initialize")
        assert hasattr(loader, "shutdown")

    def test_tool_loader_with_container(self):
        """Test tool loader with dependency container."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()
        loader = ToolLoader(registry)

        # Initialize loader with container
        loader.initialize(container)
        assert loader.container is container

    def test_tool_loader_lifecycle(self):
        """Test tool loader lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()
        loader = ToolLoader(registry)

        # Test initialization
        loader.initialize(container)
        assert loader.container is container

        # Test shutdown
        loader.shutdown()
        assert loader.container is None

        # Test re-initialization
        loader.initialize(container)
        assert loader.container is container


class TestToolLoading:
    """Test tool loading functionality."""

    def test_load_tool(self):
        """Test loading a tool."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a test tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                self.shutdown_called = True

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Test loading
        loaded_tool = loader.load_tool(test_tool)
        assert loaded_tool is test_tool
        assert test_tool.initialized is True

    def test_load_tool_with_container(self):
        """Test loading a tool with container."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()
        loader = ToolLoader(registry)
        loader.initialize(container)

        # Create a test tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.container = None

            def initialize(self, container):
                self.initialized = True
                self.container = container

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Test loading with container
        loaded_tool = loader.load_tool(test_tool)
        assert loaded_tool is test_tool
        assert test_tool.initialized is True
        assert test_tool.container is container

    def test_unload_tool(self):
        """Test unloading a tool."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a test tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                self.shutdown_called = True

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Load tool
        loader.load_tool(test_tool)
        assert test_tool.initialized is True

        # Unload tool
        loader.unload_tool(test_tool)
        assert test_tool.shutdown_called is True

    def test_get_loaded_tool(self):
        """Test getting a loaded tool."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a test tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Load tool
        loader.load_tool(test_tool)

        # Get loaded tool
        retrieved = loader.get_loaded_tool("test_tool")
        assert retrieved is test_tool

    def test_get_nonexistent_loaded_tool(self):
        """Test getting non-existent loaded tool."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        result = loader.get_loaded_tool("nonexistent_tool")
        assert result is None

    def test_get_all_loaded_tools(self):
        """Test getting all loaded tools."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create and load multiple tools
        tools = []
        for i in range(5):

            class TestTool(Tool):
                def __init__(self, tool_id):
                    self.name = f"test_tool_{tool_id}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_tool = TestTool(i)
            tools.append(test_tool)
            loader.load_tool(test_tool)

        # Get all loaded tools
        all_tools = loader.get_loaded_tools()
        assert len(all_tools) == 5

        for tool in tools:
            assert tool in all_tools.values()


class TestToolLoadingEdgeCases:
    """Test tool loading edge cases."""

    def test_load_tool_without_name(self):
        """Test loading a tool without a name."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a tool without name
        class TestTool(Tool):
            def __init__(self):
                self.name = None
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Should raise an error or handle gracefully
        with pytest.raises((ToolLoaderError, AttributeError)):
            loader.load_tool(test_tool)

    def test_load_tool_with_invalid_name(self):
        """Test loading a tool with invalid name."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a tool with invalid name
        class TestTool(Tool):
            def __init__(self):
                self.name = ""  # Empty name
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Should handle gracefully
        loaded_tool = loader.load_tool(test_tool)
        assert loaded_tool is test_tool

    def test_load_duplicate_tool(self):
        """Test loading duplicate tools."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create two tools with same name
        class TestTool(Tool):
            def __init__(self, tool_id):
                self.name = "duplicate_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.tool_id = tool_id

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        tool1 = TestTool(1)
        tool2 = TestTool(2)

        # Load first tool
        loaded1 = loader.load_tool(tool1)
        assert loaded1 is tool1

        # Load second tool with same name
        loaded2 = loader.load_tool(tool2)
        assert loaded2 is tool2

        # Should return the second tool
        retrieved = loader.get_loaded_tool("duplicate_tool")
        assert retrieved is tool2

    def test_unload_nonexistent_tool(self):
        """Test unloading non-existent tool."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Try to unload tool that wasn't loaded
        result = loader.unload_tool(test_tool)
        assert result is False


class TestToolLoadingPerformance:
    """Test tool loading performance."""

    def test_mass_tool_loading(self):
        """Test mass tool loading."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create and load many tools
        tools = []
        for i in range(100):

            class TestTool(Tool):
                def __init__(self, tool_id):
                    self.name = f"mass_tool_{tool_id}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_tool = TestTool(i)
            tools.append(test_tool)
            loader.load_tool(test_tool)

        # Verify all tools are loaded
        all_tools = loader.get_loaded_tools()
        assert len(all_tools) == 100

        for tool in tools:
            assert tool in all_tools.values()

    def test_tool_loading_performance(self):
        """Test tool loading performance."""
        import time

        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Test loading performance
        start_time = time.time()
        for i in range(1000):

            class TestTool(Tool):
                def __init__(self, tool_id):
                    self.name = f"perf_tool_{tool_id}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_tool = TestTool(i)
            loader.load_tool(test_tool)
        loading_time = time.time() - start_time

        # Test unloading performance
        start_time = time.time()
        for i in range(1000):
            loader.unload_tool(loader.get_loaded_tool(f"perf_tool_{i}"))
        unloading_time = time.time() - start_time

        # Should be fast operations
        assert loading_time < 2.0
        assert unloading_time < 1.0


class TestToolLoaderIntegration:
    """Test tool loader integration scenarios."""

    def test_tool_loader_with_registry(self):
        """Test tool loader integration with registry."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a test tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "integration_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Load tool
        loaded_tool = loader.load_tool(test_tool)

        # Verify tool is accessible through registry
        retrieved = registry.get_tool("integration_tool")
        assert retrieved is loaded_tool

    def test_tool_loader_with_lifecycle_manager(self):
        """Test tool loader integration with lifecycle manager."""
        from nodupe.core.tool_system.lifecycle import ToolLifecycleManager

        registry = ToolRegistry()
        loader = ToolLoader(registry)
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            def __init__(self):
                self.name = "lifecycle_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                self.shutdown_called = True

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Load tool
        loader.load_tool(test_tool)

        # Initialize through lifecycle manager
        lifecycle_manager.initialize_tool("lifecycle_tool")
        assert test_tool.initialized is True

        # Shutdown through lifecycle manager
        lifecycle_manager.shutdown_tool("lifecycle_tool")
        assert test_tool.shutdown_called is True


class TestToolLoaderErrorHandling:
    """Test tool loader error handling."""

    def test_load_invalid_tool(self):
        """Test loading an invalid tool."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create an invalid tool (not inheriting from Tool)
        class InvalidTool:
            def __init__(self):
                self.name = "invalid_tool"

        invalid_tool = InvalidTool()

        # Should raise an error
        with pytest.raises(ToolLoaderError):
            loader.load_tool(invalid_tool)

    def test_load_tool_with_missing_methods(self):
        """Test loading a tool with missing required methods."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a tool missing required methods
        class IncompleteTool(Tool):
            def __init__(self):
                self.name = "incomplete_tool"
                self.version = "1.0.0"
                self.dependencies = []
                # Missing initialize and shutdown methods

        incomplete_tool = IncompleteTool()

        # Should raise an error
        with pytest.raises(ToolLoaderError):
            loader.load_tool(incomplete_tool)

    def test_load_tool_with_exception_in_initialize(self):
        """Test loading a tool that throws exception in initialize."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a tool that throws exception in initialize
        class FailingTool(Tool):
            def __init__(self):
                self.name = "failing_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                raise Exception("Initialize failed")

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        failing_tool = FailingTool()

        # Should raise an error
        with pytest.raises(Exception):
            loader.load_tool(failing_tool)
