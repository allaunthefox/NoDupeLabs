"""Test plugins module functionality."""

import pytest
from unittest.mock import patch, MagicMock
from nodupe.core.plugins import (
    PluginManager,
    plugin_manager
)
from nodupe.core.plugin_system.registry import PluginRegistry


class TestPluginsModule:
    """Test plugins module functionality."""

    def test_plugin_manager_instance(self):
        """Test plugin_manager instance."""
        assert isinstance(plugin_manager, PluginRegistry)
        assert plugin_manager is not None

    def test_plugin_manager_alias(self):
        """Test PluginManager alias."""
        assert PluginManager is PluginRegistry
        assert PluginManager.__name__ == "PluginRegistry"

    def test_module_exports(self):
        """Test module exports."""
        import nodupe.core.plugins as plugins_module

        assert hasattr(plugins_module, 'PluginManager')
        assert hasattr(plugins_module, 'plugin_manager')
        assert hasattr(plugins_module, '__all__')

        expected_exports = ['PluginManager', 'plugin_manager']
        assert plugins_module.__all__ == expected_exports


class TestPluginManagerFunctionality:
    """Test plugin manager functionality."""

    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        # The plugin_manager should already be initialized
        assert plugin_manager is not None
        assert isinstance(plugin_manager, PluginRegistry)

        # Test that it has expected attributes
        assert hasattr(plugin_manager, 'initialize')
        assert hasattr(plugin_manager, 'register')
        assert hasattr(plugin_manager, 'get_plugin')
        assert hasattr(plugin_manager, 'get_plugins')
        assert hasattr(plugin_manager, 'shutdown')

    def test_plugin_manager_operations(self):
        """Test plugin manager operations."""
        # Test basic operations
        plugins = plugin_manager.get_plugins()
        assert isinstance(plugins, list)

        # Test plugin registration
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"

        plugin_manager.register(mock_plugin)
        retrieved = plugin_manager.get_plugin("test_plugin")
        assert retrieved is mock_plugin

        # Test getting all plugins
        all_plugins = plugin_manager.get_plugins()
        assert len(all_plugins) == 1
        assert all_plugins[0] is mock_plugin


class TestPluginManagerIntegration:
    """Test plugin manager integration scenarios."""

    def test_plugin_manager_with_container(self):
        """Test plugin manager with dependency container."""
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()

        # Initialize plugin manager with container
        plugin_manager.initialize(container)

        # Verify container was set
        assert plugin_manager.container is container

        # Test plugin registration with container
        mock_plugin = MagicMock()
        mock_plugin.name = "container_plugin"

        plugin_manager.register(mock_plugin)

        # Verify plugin is accessible
        retrieved = plugin_manager.get_plugin("container_plugin")
        assert retrieved is mock_plugin

    def test_plugin_manager_lifecycle(self):
        """Test plugin manager lifecycle operations."""
        # Test initialization
        from nodupe.core.container import ServiceContainer
        container = ServiceContainer()

        plugin_manager.initialize(container)
        assert plugin_manager.container is container

        # Test shutdown
        plugin_manager.shutdown()
        assert plugin_manager.container is None

        # Test re-initialization
        plugin_manager.initialize(container)
        assert plugin_manager.container is container


class TestPluginManagerErrorHandling:
    """Test plugin manager error handling."""

    def test_get_nonexistent_plugin(self):
        """Test getting non-existent plugin."""
        result = plugin_manager.get_plugin("nonexistent_plugin")
        assert result is None

    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin."""
        mock_plugin1 = MagicMock()
        mock_plugin1.name = "duplicate_plugin"

        mock_plugin2 = MagicMock()
        mock_plugin2.name = "duplicate_plugin"

        # Register first plugin
        plugin_manager.register(mock_plugin1)

        # Register second plugin with same name (should overwrite)
        plugin_manager.register(mock_plugin2)

        # Should return the second plugin
        retrieved = plugin_manager.get_plugin("duplicate_plugin")
        assert retrieved is mock_plugin2

    def test_plugin_manager_without_container(self):
        """Test plugin manager operations without container."""
        # Clear container
        plugin_manager.container = None

        # Should still work for basic operations
        mock_plugin = MagicMock()
        mock_plugin.name = "no_container_plugin"

        plugin_manager.register(mock_plugin)
        retrieved = plugin_manager.get_plugin("no_container_plugin")
        assert retrieved is mock_plugin


class TestPluginManagerEdgeCases:
    """Test plugin manager edge cases."""

    def test_plugin_with_empty_name(self):
        """Test plugin with empty name."""
        mock_plugin = MagicMock()
        mock_plugin.name = ""

        plugin_manager.register_plugin(mock_plugin)
        retrieved = plugin_manager.get_plugin("")
        assert retrieved is mock_plugin

    def test_plugin_with_special_characters(self):
        """Test plugin with special characters in name."""
        mock_plugin = MagicMock()
        mock_plugin.name = "plugin-with_special.chars"

        plugin_manager.register_plugin(mock_plugin)
        retrieved = plugin_manager.get_plugin("plugin-with_special.chars")
        assert retrieved is mock_plugin

    def test_multiple_plugin_registrations(self):
        """Test multiple plugin registrations."""
        # Register multiple plugins
        for i in range(10):
            mock_plugin = MagicMock()
            mock_plugin.name = f"plugin_{i}"
            plugin_manager.register_plugin(mock_plugin)

        # Verify all plugins are accessible
        all_plugins = plugin_manager.get_all_plugins()
        assert len(all_plugins) == 10

        for i in range(10):
            plugin = plugin_manager.get_plugin(f"plugin_{i}")
            assert plugin is not None
            assert plugin.name == f"plugin_{i}"


class TestPluginManagerCompatibility:
    """Test plugin manager compatibility with plugin system."""

    def test_plugin_manager_is_plugin_registry(self):
        """Test that PluginManager is the same as PluginRegistry."""
        assert PluginManager is PluginRegistry
        assert isinstance(plugin_manager, PluginRegistry)

    def test_plugin_manager_compatibility(self):
        """Test plugin manager compatibility with plugin system."""
        # Test that plugin_manager has the same interface as PluginRegistry
        registry = PluginRegistry()

        # Both should have the same methods
        manager_methods = set(dir(plugin_manager))
        registry_methods = set(dir(registry))

        # Check key methods are present
        key_methods = [
            'initialize',
            'register_plugin',
            'get_plugin',
            'get_all_plugins',
            'shutdown']
        for method in key_methods:
            assert method in manager_methods
            assert method in registry_methods

    def test_plugin_manager_independent_instances(self):
        """Test that plugin_manager and PluginRegistry create independent instances."""
        # Create a new registry instance
        new_registry = PluginRegistry()

        # Register a plugin in the new registry
        mock_plugin = MagicMock()
        mock_plugin.name = "registry_plugin"
        new_registry.register_plugin(mock_plugin)

        # Should not affect the global plugin_manager
        retrieved = plugin_manager.get_plugin("registry_plugin")
        assert retrieved is None

        # plugin_manager should have its own plugins
        assert len(plugin_manager.get_all_plugins()) == 0


class TestPluginManagerIntegrationWithCore:
    """Test plugin manager integration with core system."""

    def test_plugin_manager_in_core_loader(self):
        """Test plugin manager usage in core loader."""
        from unittest.mock import patch

        # Mock the core loader to test integration
        with patch('nodupe.core.loader.PluginRegistry') as mock_registry_class:
            # Create mock registry instance
            mock_registry_instance = MagicMock()
            mock_registry_class.return_value = mock_registry_instance

            # Import and test core loader
            from nodupepe.core.loader import CoreLoader

            loader = CoreLoader()

            # Mock initialization
            with patch('nodupe.core.loader.load_config') as mock_config, \
                    patch.object(loader, '_apply_platform_autoconfig') as mock_autoconfig, \
                    patch('nodupe.core.loader.create_plugin_loader') as mock_loader, \
                    patch('nodupe.core.loader.create_plugin_discovery') as mock_discovery, \
                    patch('nodupe.core.loader.create_lifecycle_manager') as mock_lifecycle, \
                    patch('nodupe.core.loader.PluginHotReload') as mock_hot_reload, \
                    patch('nodupe.core.loader.get_connection') as mock_db, \
                    patch('nodupe.core.loader.logging') as mock_logging:

                mock_config.return_value = MagicMock(config={})
                mock_autoconfig.return_value = {}
                mock_logging.info = MagicMock()

                # Initialize loader
                loader.initialize()

                # Verify plugin registry was initialized
                assert loader.plugin_registry is mock_registry_instance
                mock_registry_instance.initialize.assert_called_once()

    def test_plugin_manager_in_container(self):
        """Test plugin manager integration with dependency container."""
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()

        # Initialize plugin manager
        plugin_manager.initialize(container)

        # Register plugin manager in container
        container.register_service('plugin_manager', plugin_manager)

        # Verify it can be retrieved
        retrieved = container.get_service('plugin_manager')
        assert retrieved is plugin_manager

        # Test plugin operations through container
        mock_plugin = MagicMock()
        mock_plugin.name = "container_test_plugin"

        plugin_manager.register_plugin(mock_plugin)
        retrieved_plugin = plugin_manager.get_plugin("container_test_plugin")
        assert retrieved_plugin is mock_plugin


class TestPluginRegistryAdvanced:
    """Test advanced plugin registry functionality."""

    def test_plugin_registry_mass_registration(self):
        """Test mass plugin registration."""
        # Test registering many plugins
        for i in range(100):
            mock_plugin = MagicMock()
            mock_plugin.name = f"mass_plugin_{i}"
            plugin_manager.register_plugin(mock_plugin)

        # Verify all plugins are registered
        all_plugins = plugin_manager.get_all_plugins()
        assert len(all_plugins) == 100

        # Verify specific plugins can be retrieved
        for i in range(100):
            plugin = plugin_manager.get_plugin(f"mass_plugin_{i}")
            assert plugin is not None
            assert plugin.name == f"mass_plugin_{i}"

    def test_plugin_registry_performance(self):
        """Test plugin registry performance."""
        import time

        # Test registration performance
        start_time = time.time()
        for i in range(1000):
            mock_plugin = MagicMock()
            mock_plugin.name = f"perf_plugin_{i}"
            plugin_manager.register_plugin(mock_plugin)
        registration_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        for i in range(1000):
            plugin = plugin_manager.get_plugin(f"perf_plugin_{i}")
            assert plugin is not None
        retrieval_time = time.time() - start_time

        # Should be fast operations
        assert registration_time < 1.0
        assert retrieval_time < 0.1

    def test_plugin_registry_clear(self):
        """Test clearing plugin registry."""
        # Add some plugins
        for i in range(10):
            mock_plugin = MagicMock()
            mock_plugin.name = f"clear_plugin_{i}"
            plugin_manager.register_plugin(mock_plugin)

        # Verify plugins exist
        assert len(plugin_manager.get_all_plugins()) == 10

        # Clear registry (if supported)
        if hasattr(plugin_manager, 'clear'):
            plugin_manager.clear()
            assert len(plugin_manager.get_all_plugins()) == 0


class TestPluginLoader:
    """Test plugin loader functionality."""

    def test_plugin_loader_initialization(self):
        """Test plugin loader initialization."""
        from nodupe.core.plugin_system.loader import PluginLoader

        # Test basic initialization
        loader = PluginLoader()
        assert loader is not None

        # Test that it has expected attributes
        assert hasattr(loader, 'load_plugin')
        assert hasattr(loader, 'unload_plugin')
        assert hasattr(loader, 'get_loaded_plugins')

    def test_plugin_loader_with_container(self):
        """Test plugin loader with dependency container."""
        from nodupe.core.plugin_system.loader import PluginLoader
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()
        loader = PluginLoader()

        # Initialize loader with container
        loader.initialize(container)
        assert loader.container is container

    def test_plugin_loader_load_unload(self):
        """Test plugin loading and unloading."""
        from nodupe.core.plugin_system.loader import PluginLoader
        from nodupe.core.plugin_system.base import Plugin

        # Create a mock plugin class
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
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

        loader = PluginLoader()
        test_plugin = TestPlugin()

        # Test loading
        loaded_plugin = loader.load_plugin(test_plugin)
        assert loaded_plugin is test_plugin
        assert test_plugin.initialized is True

        # Test unloading
        loader.unload_plugin(test_plugin)
        assert test_plugin.shutdown_called is True


class TestPluginDiscovery:
    """Test plugin discovery functionality."""

    def test_plugin_discovery_initialization(self):
        """Test plugin discovery initialization."""
        from nodupe.core.plugin_system.discovery import PluginDiscovery

        discovery = PluginDiscovery()
        assert discovery is not None

        # Test that it has expected attributes
        assert hasattr(discovery, 'discover_plugins')
        assert hasattr(discovery, 'get_discovered_plugins')

    def test_plugin_discovery_with_container(self):
        """Test plugin discovery with dependency container."""
        from nodupe.core.plugin_system.discovery import PluginDiscovery
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()
        discovery = PluginDiscovery()

        # Initialize discovery with container
        discovery.initialize(container)
        assert discovery.container is container


class TestPluginLifecycle:
    """Test plugin lifecycle management."""

    def test_plugin_lifecycle_initialization(self):
        """Test plugin lifecycle manager initialization."""
        from nodupe.core.plugin_system.lifecycle import PluginLifecycleManager

        lifecycle = PluginLifecycleManager()
        assert lifecycle is not None

        # Test that it has expected attributes
        assert hasattr(lifecycle, 'initialize_plugins')
        assert hasattr(lifecycle, 'shutdown_plugins')
        assert hasattr(lifecycle, 'get_plugin_states')

    def test_plugin_lifecycle_with_container(self):
        """Test plugin lifecycle with dependency container."""
        from nodupe.core.plugin_system.lifecycle import PluginLifecycleManager
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()
        lifecycle = PluginLifecycleManager()

        # Initialize lifecycle with container
        lifecycle.initialize(container)
        assert lifecycle.container is container


class TestPluginHotReload:
    """Test plugin hot reload functionality."""

    def test_plugin_hot_reload_initialization(self):
        """Test plugin hot reload initialization."""
        from nodupe.core.plugin_system.hot_reload import PluginHotReload

        hot_reload = PluginHotReload()
        assert hot_reload is not None

        # Test that it has expected attributes
        assert hasattr(hot_reload, 'start_watching')
        assert hasattr(hot_reload, 'stop_watching')
        assert hasattr(hot_reload, 'reload_plugins')

    def test_plugin_hot_reload_with_container(self):
        """Test plugin hot reload with dependency container."""
        from nodupe.core.plugin_system.hot_reload import PluginHotReload
        from nodupe.core.container import ServiceContainer

        container = ServiceContainer()
        hot_reload = PluginHotReload()

        # Initialize hot reload with container
        hot_reload.initialize(container)
        assert hot_reload.container is container


class TestPluginCompatibility:
    """Test plugin compatibility functionality."""

    def test_plugin_compatibility_initialization(self):
        """Test plugin compatibility checker initialization."""
        from nodupe.core.plugin_system.compatibility import PluginCompatibility

        compatibility = PluginCompatibility()
        assert compatibility is not None

        # Test that it has expected attributes
        assert hasattr(compatibility, 'check_compatibility')
        assert hasattr(compatibility, 'get_compatibility_report')

    def test_plugin_compatibility_checking(self):
        """Test plugin compatibility checking."""
        from nodupe.core.plugin_system.compatibility import PluginCompatibility
        from nodupe.core.plugin_system.base import Plugin

        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        compatibility = PluginCompatibility()
        test_plugin = TestPlugin()

        # Test compatibility checking
        report = compatibility.check_compatibility(test_plugin)
        assert report is not None
        assert isinstance(report, dict)


class TestPluginDependencies:
    """Test plugin dependency management."""

    def test_plugin_dependency_initialization(self):
        """Test plugin dependency manager initialization."""
        from nodupe.core.plugin_system.dependencies import PluginDependencyManager

        dependency_manager = PluginDependencyManager()
        assert dependency_manager is not None

        # Test that it has expected attributes
        assert hasattr(dependency_manager, 'resolve_dependencies')
        assert hasattr(dependency_manager, 'check_dependency_graph')

    def test_plugin_dependency_resolution(self):
        """Test plugin dependency resolution."""
        from nodupe.core.plugin_system.dependencies import PluginDependencyManager
        from nodupe.core.plugin_system.base import Plugin

        class PluginA(Plugin):
            def __init__(self):
                self.name = "plugin_a"
                self.version = "1.0.0"
                self.dependencies = []

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        class PluginB(Plugin):
            def __init__(self):
                self.name = "plugin_b"
                self.version = "1.0.0"
                self.dependencies = ["plugin_a"]

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        dependency_manager = PluginDependencyManager()
        plugin_a = PluginA()
        plugin_b = PluginB()

        # Test dependency resolution
        plugins = [plugin_a, plugin_b]
        resolved = dependency_manager.resolve_dependencies(plugins)
        assert resolved is not None
        assert len(resolved) == 2


class TestPluginSecurity:
    """Test plugin security functionality."""

    def test_plugin_security_initialization(self):
        """Test plugin security manager initialization."""
        from nodupe.core.plugin_system.security import PluginSecurity

        security = PluginSecurity()
        assert security is not None

        # Test that it has expected attributes
        assert hasattr(security, 'validate_plugin')
        assert hasattr(security, 'check_plugin_permissions')

    def test_plugin_security_validation(self):
        """Test plugin security validation."""
        from nodupe.core.plugin_system.security import PluginSecurity
        from nodupe.core.plugin_system.base import Plugin

        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = []

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        security = PluginSecurity()
        test_plugin = TestPlugin()

        # Test security validation
        is_valid = security.validate_plugin(test_plugin)
        assert is_valid is not None


class TestPluginIntegration:
    """Test complete plugin system integration."""

    def test_complete_plugin_system_workflow(self):
        """Test complete plugin system workflow."""
        from nodupe.core.plugin_system.loader import PluginLoader
        from nodupe.core.plugin_system.discovery import PluginDiscovery
        from nodupe.core.plugin_system.lifecycle import PluginLifecycleManager
        from nodupe.core.plugin_system.registry import PluginRegistry
        from nodupe.core.plugin_system.base import Plugin
        from nodupe.core.container import ServiceContainer

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "integration_test_plugin"
                self.version = "1.0.0"
                self.dependencies = []
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

        # Initialize plugin components
        registry = PluginRegistry()
        loader = PluginLoader()
        discovery = PluginDiscovery()
        lifecycle = PluginLifecycleManager()

        # Initialize components with container
        registry.initialize(container)
        loader.initialize(container)
        discovery.initialize(container)
        lifecycle.initialize(container)

        # Create test plugin instance
        test_plugin = TestPlugin()

        # Test loading workflow
        loaded_plugin = loader.load_plugin(test_plugin)
        assert loaded_plugin is test_plugin
        assert test_plugin.initialized is True

        # Test registration
        registry.register_plugin(test_plugin)
        retrieved = registry.get_plugin("integration_test_plugin")
        assert retrieved is test_plugin

        # Test lifecycle management
        lifecycle.initialize_plugins([test_plugin])
        assert test_plugin.initialized is True

        # Test shutdown
        lifecycle.shutdown_plugins([test_plugin])
        assert test_plugin.shutdown_called is True

        # Test unloading
        loader.unload_plugin(test_plugin)
        assert test_plugin.shutdown_called is True

    def test_plugin_system_performance(self):
        """Test plugin system performance."""
        import time
        from nodupe.core.plugin_system.loader import PluginLoader
        from nodupe.core.plugin_system.registry import PluginRegistry
        from nodupe.core.plugin_system.base import Plugin

        # Create a simple test plugin class
        class SimplePlugin(Plugin):
            def __init__(self, plugin_id):
                self.name = f"perf_plugin_{plugin_id}"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

        registry = PluginRegistry()
        loader = PluginLoader()

        # Test mass plugin loading and registration
        start_time = time.time()
        plugins = []
        for i in range(100):
            plugin = SimplePlugin(i)
            plugins.append(plugin)
            loaded = loader.load_plugin(plugin)
            registry.register_plugin(loaded)
        load_time = time.time() - start_time

        # Test mass plugin retrieval
        start_time = time.time()
        for i in range(100):
            plugin = registry.get_plugin(f"perf_plugin_{i}")
            assert plugin is not None
        retrieval_time = time.time() - start_time

        # Should be fast operations
        assert load_time < 1.0
        assert retrieval_time < 0.1

        # Verify all plugins are loaded and registered
        all_plugins = registry.get_all_plugins()
        assert len(all_plugins) == 100

        # Test mass plugin unloading
        start_time = time.time()
        for plugin in plugins:
            loader.unload_plugin(plugin)
        unload_time = time.time() - start_time

        assert unload_time < 0.5
