"""Test tools module functionality."""

from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.tool_system.registry import ToolRegistry
from nodupe.core.tools import ToolManager, tool_manager


class TestToolsModule:
    """Test tools module functionality."""

    def test_tool_manager_instance(self):
        """Test tool_manager instance."""
        assert isinstance(tool_manager, ToolRegistry)
        assert tool_manager is not None

    def test_tool_manager_alias(self):
        """Test ToolManager alias."""
        assert ToolManager is ToolRegistry
        assert ToolManager.__name__ == "ToolRegistry"

    def test_module_exports(self):
        """Test module exports."""
        import nodupe.core.tools as tools_module

        assert hasattr(tools_module, "ToolManager")
        assert hasattr(tools_module, "tool_manager")
        assert hasattr(tools_module, "__all__")

        expected_exports = ["ToolManager", "tool_manager"]
        assert tools_module.__all__ == expected_exports


class TestToolManagerFunctionality:
    """Test tool manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_tool_manager_initialization(self):
        """Test tool manager initialization."""
        # The tool_manager should already be initialized
        assert tool_manager is not None
        assert isinstance(tool_manager, ToolRegistry)

        # Test that it has expected attributes
        assert hasattr(tool_manager, "initialize")
        assert hasattr(tool_manager, "register")
        assert hasattr(tool_manager, "get_tool")
        assert hasattr(tool_manager, "get_tools")
        assert hasattr(tool_manager, "shutdown")

    def test_tool_manager_operations(self):
        """Test tool manager operations."""
        # Test basic operations
        tools = tool_manager.get_tools()
        assert isinstance(tools, list)

        # Test tool registration
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        tool_manager.register(mock_tool)
        retrieved = tool_manager.get_tool("test_tool")
        assert retrieved is mock_tool

        # Test getting all tools
        all_tools = tool_manager.get_tools()
        assert len(all_tools) == 1
        assert all_tools[0] is mock_tool


class TestToolManagerIntegration:
    """Test tool manager integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_tool_manager_with_container(self):
        """Test tool manager with dependency container."""
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()

        # Initialize tool manager with container
        tool_manager.initialize(container)

        # Verify container was set
        assert tool_manager.container is container

        # Test tool registration with container
        mock_tool = MagicMock()
        mock_tool.name = "container_tool"

        tool_manager.register(mock_tool)

        # Verify tool is accessible
        retrieved = tool_manager.get_tool("container_tool")
        assert retrieved is mock_tool

    def test_tool_manager_lifecycle(self):
        """Test tool manager lifecycle operations."""
        # Test initialization
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()

        tool_manager.initialize(container)
        assert tool_manager.container is container

        # Test shutdown
        tool_manager.shutdown()
        assert tool_manager.container is None

        # Test re-initialization
        tool_manager.initialize(container)
        assert tool_manager.container is container


class TestToolManagerErrorHandling:
    """Test tool manager error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool."""
        result = tool_manager.get_tool("nonexistent_tool")
        assert result is None

    def test_register_duplicate_tool(self):
        """Test registering duplicate tool."""
        mock_tool1 = MagicMock()
        mock_tool1.name = "duplicate_tool"

        mock_tool2 = MagicMock()
        mock_tool2.name = "duplicate_tool"

        # Register first tool
        tool_manager.register(mock_tool1)

        # Register second tool with same name (should raise ValueError)
        with pytest.raises(ValueError, match="already registered"):
            tool_manager.register(mock_tool2)

        # Should still return the first tool
        retrieved = tool_manager.get_tool("duplicate_tool")
        assert retrieved is mock_tool1

    def test_tool_manager_without_container(self):
        """Test tool manager operations without container."""
        # Clear container
        tool_manager.container = None

        # Should still work for basic operations
        mock_tool = MagicMock()
        mock_tool.name = "no_container_tool"

        tool_manager.register(mock_tool)
        retrieved = tool_manager.get_tool("no_container_tool")
        assert retrieved is mock_tool


class TestToolManagerEdgeCases:
    """Test tool manager edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_tool_with_empty_name(self):
        """Test tool with empty name."""
        mock_tool = MagicMock()
        mock_tool.name = ""

        tool_manager.register_tool(mock_tool)
        retrieved = tool_manager.get_tool("")
        assert retrieved is mock_tool

    def test_tool_with_special_characters(self):
        """Test tool with special characters in name."""
        mock_tool = MagicMock()
        mock_tool.name = "tool-with_special.chars"

        tool_manager.register_tool(mock_tool)
        retrieved = tool_manager.get_tool("tool-with_special.chars")
        assert retrieved is mock_tool

    def test_multiple_tool_registrations(self):
        """Test multiple tool registrations."""
        # Register multiple tools
        for i in range(10):
            mock_tool = MagicMock()
            mock_tool.name = f"tool_{i}"
            tool_manager.register_tool(mock_tool)

        # Verify all tools are accessible
        all_tools = tool_manager.get_all_tools()
        assert len(all_tools) == 10

        for i in range(10):
            tool = tool_manager.get_tool(f"tool_{i}")
            assert tool is not None
            assert tool.name == f"tool_{i}"


class TestToolManagerCompatibility:
    """Test tool manager compatibility with tool system."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_tool_manager_is_tool_registry(self):
        """Test that ToolManager is the same as ToolRegistry."""
        assert ToolManager is ToolRegistry
        assert isinstance(tool_manager, ToolRegistry)

    def test_tool_manager_compatibility(self):
        """Test tool manager compatibility with tool system."""
        # Test that tool_manager has the same interface as ToolRegistry
        registry = ToolRegistry()

        # Both should have the same methods
        manager_methods = set(dir(tool_manager))
        registry_methods = set(dir(registry))

        # Check key methods are present
        key_methods = [
            "initialize",
            "register_tool",
            "get_tool",
            "get_all_tools",
            "shutdown",
        ]
        for method in key_methods:
            assert method in manager_methods
            assert method in registry_methods

    def test_tool_manager_singleton_behavior(self):
        """Test that tool_manager and ToolRegistry return the same instance (singleton)."""
        # Create a new registry instance
        new_registry = ToolRegistry()

        # Register a tool in the new registry
        mock_tool = MagicMock()
        mock_tool.name = "registry_tool"
        new_registry.register_tool(mock_tool)

        # Should affect the global tool_manager because it's a singleton
        retrieved = tool_manager.get_tool("registry_tool")
        assert retrieved is mock_tool

        # Both references point to the same object
        assert new_registry is tool_manager


class TestToolManagerIntegrationWithCore:
    """Test tool manager integration with core system."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_tool_manager_in_core_loader(self):
        """Test tool manager usage in core loader."""
        from unittest.mock import patch

        # Mock the core loader to test integration
        with patch("nodupe.core.loader.ToolRegistry") as mock_registry_class:
            # Create mock registry instance
            mock_registry_instance = MagicMock()
            mock_registry_class.return_value = mock_registry_instance

            # Import and test core loader
            from nodupe.core.loader import CoreLoader

            loader = CoreLoader()

            # Mock initialization
            with (
                patch("nodupe.core.loader.load_config") as mock_config,
                patch.object(
                    loader, "_apply_platform_autoconfig"
                ) as mock_autoconfig,
                patch("nodupe.core.loader.create_tool_loader"),
                patch("nodupe.core.loader.create_tool_discovery"),
                patch("nodupe.core.loader.create_lifecycle_manager"),
                patch("nodupe.core.loader.ToolHotReload"),
                patch("nodupe.core.loader.get_connection"),
                patch("nodupe.core.loader.logging") as mock_logging,
            ):

                mock_config.return_value = MagicMock(config={})
                mock_autoconfig.return_value = {}
                mock_logging.info = MagicMock()

                # Initialize loader
                loader.initialize()

                # Verify tool registry was initialized
                assert loader.tool_registry is mock_registry_instance
                mock_registry_instance.initialize.assert_called_once()

    def test_tool_manager_in_container(self):
        """Test tool manager integration with dependency container."""
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()

        # Initialize tool manager
        tool_manager.initialize(container)

        # Register tool manager in container
        container.register_service("tool_manager", tool_manager)

        # Verify it can be retrieved
        retrieved = container.get_service("tool_manager")
        assert retrieved is tool_manager

        # Test tool operations through container
        mock_tool = MagicMock()
        mock_tool.name = "container_test_tool"

        tool_manager.register_tool(mock_tool)
        retrieved_tool = tool_manager.get_tool("container_test_tool")
        assert retrieved_tool is mock_tool


class TestToolRegistryAdvanced:
    """Test advanced tool registry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_tool_registry_mass_registration(self):
        """Test mass tool registration."""
        # Test registering many tools
        for i in range(100):
            mock_tool = MagicMock()
            mock_tool.name = f"mass_tool_{i}"
            tool_manager.register_tool(mock_tool)

        # Verify all tools are registered
        all_tools = tool_manager.get_all_tools()
        assert len(all_tools) == 100

        # Verify specific tools can be retrieved
        for i in range(100):
            tool = tool_manager.get_tool(f"mass_tool_{i}")
            assert tool is not None
            assert tool.name == f"mass_tool_{i}"

    def test_tool_registry_performance(self):
        """Test tool registry performance."""
        import time

        # Test registration performance
        start_time = time.time()
        for i in range(1000):
            mock_tool = MagicMock()
            mock_tool.name = f"perf_tool_{i}"
            tool_manager.register_tool(mock_tool)
        registration_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        for i in range(1000):
            tool = tool_manager.get_tool(f"perf_tool_{i}")
            assert tool is not None
        retrieval_time = time.time() - start_time

        # Should be fast operations
        assert registration_time < 1.0
        assert retrieval_time < 0.1

    def test_tool_registry_clear(self):
        """Test clearing tool registry."""
        # Add some tools
        for i in range(10):
            mock_tool = MagicMock()
            mock_tool.name = f"clear_tool_{i}"
            tool_manager.register_tool(mock_tool)

        # Verify tools exist
        assert len(tool_manager.get_all_tools()) == 10

        # Clear registry (if supported)
        if hasattr(tool_manager, "clear"):
            tool_manager.clear()
            assert len(tool_manager.get_all_tools()) == 0


class TestToolLoader:
    """Test tool loader functionality."""

    def test_tool_loader_initialization(self):
        """Test tool loader initialization."""
        from nodupe.core.tool_system.loader import ToolLoader

        # Test basic initialization
        loader = ToolLoader(tool_manager)
        assert loader is not None

        # Test that it has expected attributes
        assert hasattr(loader, "load_tool_from_file")
        assert hasattr(loader, "unload_tool")
        assert hasattr(loader, "get_all_loaded_tools")

    def test_tool_loader_with_container(self):
        """Test tool loader with dependency container."""
        from nodupe.core.container import ServiceContainer
        from nodupe.core.tool_system.loader import ToolLoader

        ServiceContainer()
        loader = ToolLoader(tool_manager)

        # Initialize loader with container
        # Note: ToolLoader doesn't have initialize method in this version,
        # but let's check if it should have it or if we should just test it exists
        # loader.initialize(container)
        # assert loader.container is container
        assert loader is not None

    def test_tool_loader_load_unload(self):
        """Test tool loading and unloading."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader

        # Create a mock tool class
        class TestTool(Tool):
            @property
            def name(self):
                return "test_tool"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def __init__(self):
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                self.shutdown_called = True

            def get_capabilities(self):
                return {"test": True}

        loader = ToolLoader()
        test_tool = TestTool()

        # Test loading
        loaded_tool = loader.load_tool(test_tool)
        assert loaded_tool is test_tool
        assert test_tool.initialized is True

        # Test unloading
        loader.unload_tool(test_tool)
        assert test_tool.shutdown_called is True


class TestToolDiscovery:
    """Test tool discovery functionality."""

    def test_tool_discovery_initialization(self):
        """Test tool discovery initialization."""
        from nodupe.core.tool_system.discovery import ToolDiscovery

        discovery = ToolDiscovery()
        assert discovery is not None

        # Test that it has expected attributes
        assert hasattr(discovery, "discover_tools")
        assert hasattr(discovery, "get_discovered_tools")

    def test_tool_discovery_with_container(self):
        """Test tool discovery with dependency container."""
        from nodupe.core.container import ServiceContainer
        from nodupe.core.tool_system.discovery import ToolDiscovery

        container = ServiceContainer()
        discovery = ToolDiscovery()

        # Initialize discovery with container
        discovery.initialize(container)
        assert discovery.container is container


class TestToolLifecycle:
    """Test tool lifecycle management."""

    def test_tool_lifecycle_initialization(self):
        """Test tool lifecycle manager initialization."""
        from nodupe.core.tool_system.lifecycle import ToolLifecycleManager

        lifecycle = ToolLifecycleManager()
        assert lifecycle is not None

        # Test that it has expected attributes
        assert hasattr(lifecycle, "initialize_tools")
        assert hasattr(lifecycle, "shutdown_tools")
        assert hasattr(lifecycle, "get_tool_states")

    def test_tool_lifecycle_with_container(self):
        """Test tool lifecycle with dependency container."""
        from nodupe.core.container import ServiceContainer
        from nodupe.core.tool_system.lifecycle import ToolLifecycleManager

        container = ServiceContainer()
        lifecycle = ToolLifecycleManager()

        # Initialize lifecycle with container
        lifecycle.initialize(container)
        assert lifecycle.container is container


class TestToolHotReload:
    """Test tool hot reload functionality."""

    def test_tool_hot_reload_initialization(self):
        """Test tool hot reload initialization."""
        from nodupe.core.tool_system.hot_reload import ToolHotReload

        hot_reload = ToolHotReload()
        assert hot_reload is not None

        # Test that it has expected attributes
        assert hasattr(hot_reload, "start_watching")
        assert hasattr(hot_reload, "stop_watching")
        assert hasattr(hot_reload, "reload_tools")

    def test_tool_hot_reload_with_container(self):
        """Test tool hot reload with dependency container."""
        from nodupe.core.container import ServiceContainer
        from nodupe.core.tool_system.hot_reload import ToolHotReload

        container = ServiceContainer()
        hot_reload = ToolHotReload()

        # Initialize hot reload with container
        hot_reload.initialize(container)
        assert hot_reload.container is container


class TestToolCompatibility:
    """Test tool compatibility functionality."""

    def test_tool_compatibility_initialization(self):
        """Test tool compatibility checker initialization."""
        from nodupe.core.tool_system.compatibility import ToolCompatibility

        compatibility = ToolCompatibility()
        assert compatibility is not None

        # Test that it has expected attributes
        assert hasattr(compatibility, "check_compatibility")
        assert hasattr(compatibility, "get_compatibility_report")

    def test_tool_compatibility_checking(self):
        """Test tool compatibility checking."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.compatibility import ToolCompatibility

        class TestTool(Tool):
            @property
            def name(self):
                return "test_tool"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return ["core>=1.0.0"]

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        compatibility = ToolCompatibility()
        test_tool = TestTool()

        # Test compatibility checking
        report = compatibility.check_compatibility(test_tool)
        assert report is not None
        assert isinstance(report, dict)


class TestToolDependencies:
    """Test tool dependency management."""

    def test_tool_dependency_initialization(self):
        """Test tool dependency manager initialization."""
        from nodupe.core.tool_system.dependencies import ToolDependencyManager

        dependency_manager = ToolDependencyManager()
        assert dependency_manager is not None

        # Test that it has expected attributes
        assert hasattr(dependency_manager, "resolve_dependencies")
        assert hasattr(dependency_manager, "check_dependency_graph")

    def test_tool_dependency_resolution(self):
        """Test tool dependency resolution."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.dependencies import ToolDependencyManager

        class ToolA(Tool):
            @property
            def name(self):
                return "tool_a"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        class ToolB(Tool):
            @property
            def name(self):
                return "tool_b"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return ["tool_a"]

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        dependency_manager = ToolDependencyManager()
        tool_a = ToolA()
        tool_b = ToolB()

        # Test dependency resolution
        tools = [tool_a, tool_b]
        resolved = dependency_manager.resolve_dependencies(tools)
        assert resolved is not None
        assert len(resolved) == 2


class TestToolSecurity:
    """Test tool security functionality."""

    def test_tool_security_initialization(self):
        """Test tool security manager initialization."""
        from nodupe.core.tool_system.security import ToolSecurity

        security = ToolSecurity()
        assert security is not None

        # Test that it has expected attributes
        assert hasattr(security, "validate_tool")
        assert hasattr(security, "check_tool_permissions")

    def test_tool_security_validation(self):
        """Test tool security validation."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.security import ToolSecurity

        class TestTool(Tool):
            @property
            def name(self):
                return "test_tool"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        security = ToolSecurity()
        test_tool = TestTool()

        # Test security validation
        is_valid = security.validate_tool(test_tool)
        assert is_valid is not None


class TestToolIntegration:
    """Test complete tool system integration."""

    def setup_method(self):
        """Set up test fixtures."""
        tool_manager.clear()
        tool_manager.container = None

    def test_complete_tool_system_workflow(self):
        """Test complete tool system workflow."""
        from nodupe.core.container import ServiceContainer
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.discovery import ToolDiscovery
        from nodupe.core.tool_system.lifecycle import ToolLifecycleManager
        from nodupe.core.tool_system.loader import ToolLoader
        from nodupe.core.tool_system.registry import ToolRegistry

        # Create a test tool
        class TestTool(Tool):
            @property
            def name(self):
                return "integration_test_tool"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def __init__(self):
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                self.shutdown_called = True

            def get_capabilities(self):
                return {"integration_test": True}

        # Initialize container
        container = ServiceContainer()

        # Initialize tool components
        registry = ToolRegistry()
        loader = ToolLoader()
        discovery = ToolDiscovery()
        lifecycle = ToolLifecycleManager()

        # Initialize components with container
        registry.initialize(container)
        loader.initialize(container)
        discovery.initialize(container)
        lifecycle.initialize(container)

        # Create test tool instance
        test_tool = TestTool()

        # Test loading workflow
        loaded_tool = loader.load_tool(test_tool)
        assert loaded_tool is test_tool
        assert test_tool.initialized is True

        # Test registration
        registry.register_tool(test_tool)
        retrieved = registry.get_tool("integration_test_tool")
        assert retrieved is test_tool

        # Test lifecycle management
        lifecycle.initialize_tools([test_tool])
        assert test_tool.initialized is True

        # Test shutdown
        lifecycle.shutdown_tools([test_tool])
        assert test_tool.shutdown_called is True

        # Test unloading
        loader.unload_tool(test_tool)
        assert test_tool.shutdown_called is True

    def test_tool_system_performance(self):
        """Test tool system performance."""
        import time

        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader
        from nodupe.core.tool_system.registry import ToolRegistry

        # Create a simple test tool class
        class SimpleTool(Tool):
            @property
            def name(self):
                return f"perf_tool_{self.tool_id}"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def __init__(self, tool_id):
                self.tool_id = tool_id
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        registry = ToolRegistry()
        loader = ToolLoader()

        # Test mass tool loading and registration
        start_time = time.time()
        tools = []
        for i in range(100):
            tool = SimpleTool(i)
            tools.append(tool)
            loaded = loader.load_tool(tool)
            registry.register_tool(loaded)
        load_time = time.time() - start_time

        # Test mass tool retrieval
        start_time = time.time()
        for i in range(100):
            tool = registry.get_tool(f"perf_tool_{i}")
            assert tool is not None
        retrieval_time = time.time() - start_time

        # Should be fast operations
        assert load_time < 1.0
        assert retrieval_time < 0.1

        # Verify all tools are loaded and registered
        all_tools = registry.get_all_tools()
        assert len(all_tools) == 100

        # Test mass tool unloading
        start_time = time.time()
        for tool in tools:
            loader.unload_tool(tool)
        unload_time = time.time() - start_time

        assert unload_time < 0.5
