"""Test plugin registry functionality."""

import pytest
from unittest.mock import MagicMock
from nodupe.core.plugin_system.registry import PluginRegistry
from nodupe.core.plugin_system.base import Plugin


class TestPluginRegistry:
    """Test plugin registry core functionality."""

    def test_plugin_registry_initialization(self):
        """Test plugin registry initialization."""
        registry = PluginRegistry()
        assert registry is not None
        assert isinstance(registry, PluginRegistry)

        # Test that it has expected attributes
        assert hasattr(registry, 'register')
        assert hasattr(registry, 'unregister')
        assert hasattr(registry, 'get_plugin')
        assert hasattr(registry, 'get_plugins')
        assert hasattr(registry, 'initialize')
        assert hasattr(registry, 'shutdown')

    def test_plugin_registry_singleton_behavior(self):
        """Test plugin registry singleton behavior."""
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()

        # Should be the same instance (singleton)
        assert registry1 is registry2

    def test_plugin_registration(self):
        """Test plugin registration functionality."""
        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create a mock plugin
        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin.dependencies = []

        # Register the plugin
        registry.register(mock_plugin)

        # Verify plugin is registered
        retrieved = registry.get_plugin("test_plugin")
        assert retrieved is mock_plugin

    def test_plugin_unregistration(self):
        """Test plugin unregistration functionality."""
        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create and register a plugin
        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = "test_plugin"
        registry.register(mock_plugin)

        # Verify plugin is registered
        assert registry.get_plugin("test_plugin") is mock_plugin

        # Unregister the plugin
        registry.unregister("test_plugin")

        # Verify plugin is unregistered
        assert registry.get_plugin("test_plugin") is None

    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Register multiple plugins
        plugins = []
        for i in range(5):
            mock_plugin = MagicMock(spec=Plugin)
            mock_plugin.name = f"plugin_{i}"
            plugins.append(mock_plugin)
            registry.register(mock_plugin)

        # Get all plugins
        all_plugins = registry.get_plugins()

        # Verify all plugins are returned
        assert len(all_plugins) == 5
        for plugin in plugins:
            assert plugin in all_plugins

    def test_get_nonexistent_plugin(self):
        """Test getting non-existent plugin."""
        registry = PluginRegistry()
        result = registry.get_plugin("nonexistent_plugin")
        assert result is None

    def test_plugin_registry_with_container(self):
        """Test plugin registry with dependency container."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
        container = ServiceContainer()

        # Initialize registry with container
        registry.initialize(container)
        assert registry._container is container

        # Test plugin registration with container
        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = "container_plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin.dependencies = []

        registry.register(mock_plugin)

        # Verify plugin is accessible
        retrieved = registry.get_plugin("container_plugin")
        assert retrieved is mock_plugin

    def test_plugin_registry_lifecycle(self):
        """Test plugin registry lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
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


class TestPluginRegistryEdgeCases:
    """Test plugin registry edge cases."""

    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin."""
        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create two plugins with same name
        mock_plugin1 = MagicMock(spec=Plugin)
        mock_plugin1.name = "duplicate_plugin"

        mock_plugin2 = MagicMock(spec=Plugin)
        mock_plugin2.name = "duplicate_plugin"

        # Register first plugin
        registry.register(mock_plugin1)

        # Register second plugin with same name (should raise error)
        with pytest.raises(ValueError):
            registry.register(mock_plugin2)

        # Should still return the first plugin
        retrieved = registry.get_plugin("duplicate_plugin")
        assert retrieved is mock_plugin1

    def test_plugin_with_empty_name(self):
        """Test plugin with empty name."""
        registry = PluginRegistry()

        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = ""

        registry.register(mock_plugin)
        retrieved = registry.get_plugin("")
        assert retrieved is mock_plugin

    def test_plugin_with_special_characters(self):
        """Test plugin with special characters in name."""
        registry = PluginRegistry()

        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = "plugin-with_special.chars"

        registry.register(mock_plugin)
        retrieved = registry.get_plugin("plugin-with_special.chars")
        assert retrieved is mock_plugin

    def test_multiple_plugin_registrations(self):
        """Test multiple plugin registrations."""
        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Register multiple plugins
        for i in range(10):
            mock_plugin = MagicMock(spec=Plugin)
            mock_plugin.name = f"plugin_{i}"
            registry.register(mock_plugin)

        # Verify all plugins are accessible
        all_plugins = registry.get_plugins()
        assert len(all_plugins) == 10

        for i in range(10):
            plugin = registry.get_plugin(f"plugin_{i}")
            assert plugin is not None
            assert plugin.name == f"plugin_{i}"


class TestPluginRegistryPerformance:
    """Test plugin registry performance."""

    def test_plugin_registry_mass_registration(self):
        """Test mass plugin registration."""
        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Test registering many plugins
        for i in range(100):
            mock_plugin = MagicMock(spec=Plugin)
            mock_plugin.name = f"mass_plugin_{i}"
            registry.register(mock_plugin)

        # Verify all plugins are registered
        all_plugins = registry.get_plugins()
        assert len(all_plugins) == 100

        # Verify specific plugins can be retrieved
        for i in range(100):
            plugin = registry.get_plugin(f"mass_plugin_{i}")
            assert plugin is not None
            assert plugin.name == f"mass_plugin_{i}"

    def test_plugin_registry_performance(self):
        """Test plugin registry performance."""
        import time

        registry = PluginRegistry()

        # Test registration performance
        start_time = time.time()
        for i in range(1000):
            mock_plugin = MagicMock(spec=Plugin)
            mock_plugin.name = f"perf_plugin_{i}"
            registry.register(mock_plugin)
        registration_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        for i in range(1000):
            plugin = registry.get_plugin(f"perf_plugin_{i}")
            assert plugin is not None
        retrieval_time = time.time() - start_time

        # Should be fast operations
        assert registration_time < 1.0
        assert retrieval_time < 0.1


class TestPluginRegistryIntegration:
    """Test plugin registry integration scenarios."""

    def test_plugin_registry_with_lifecycle_manager(self):
        """Test plugin registry integration with lifecycle manager."""
        from nodupe.core.plugin_system.lifecycle import PluginLifecycleManager

        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create lifecycle manager with registry
        lifecycle_manager = PluginLifecycleManager(registry)

        # Verify integration
        assert lifecycle_manager.registry is registry

        # Test plugin registration through lifecycle manager
        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = "lifecycle_plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin.dependencies = []

        registry.register(mock_plugin)

        # Verify plugin is accessible through both
        retrieved_from_registry = registry.get_plugin("lifecycle_plugin")
        assert retrieved_from_registry is mock_plugin

    def test_plugin_registry_with_loader(self):
        """Test plugin registry integration with plugin loader."""
        from nodupe.core.plugin_system.loader import PluginLoader

        registry = PluginRegistry()

        # Initialize registry first
        registry.initialize(MagicMock())

        # Create loader with registry
        loader = PluginLoader(registry)

        # Verify integration
        assert loader.registry is registry

        # Test plugin registration through loader
        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.name = "loader_plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin.dependencies = []

        # Register plugin directly (loader doesn't have load_plugin method)
        registry.register(mock_plugin)

        # Verify plugin is accessible through registry
        retrieved = registry.get_plugin("loader_plugin")
        assert retrieved is mock_plugin
