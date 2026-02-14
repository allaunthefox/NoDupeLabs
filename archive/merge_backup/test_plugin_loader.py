"""Test plugin loader functionality."""

import pytest
from unittest.mock import MagicMock, patch
from nodupe.core.plugin_system.loader import PluginLoader, PluginLoaderError
from nodupe.core.plugin_system.registry import PluginRegistry
from nodupe.core.plugin_system.base import Plugin


class TestPluginLoader:
    """Test plugin loader core functionality."""

    def test_plugin_loader_initialization(self):
        """Test plugin loader initialization."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        assert loader is not None
        assert isinstance(loader, PluginLoader)
        assert loader.registry is registry

        # Test that it has expected attributes
        assert hasattr(loader, 'load_plugin')
        assert hasattr(loader, 'unload_plugin')
        assert hasattr(loader, 'get_loaded_plugins')
        assert hasattr(loader, 'get_loaded_plugin')
        assert hasattr(loader, 'initialize')
        assert hasattr(loader, 'shutdown')

    def test_plugin_loader_with_container(self):
        """Test plugin loader with dependency container."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
        container = ServiceContainer()
        loader = PluginLoader(registry)

        # Initialize loader with container
        loader.initialize(container)
        assert loader.container is container

    def test_plugin_loader_lifecycle(self):
        """Test plugin loader lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
        container = ServiceContainer()
        loader = PluginLoader(registry)

        # Test initialization
        loader.initialize(container)
        assert loader.container is container

        # Test shutdown
        loader.shutdown()
        assert loader.container is None

        # Test re-initialization
        loader.initialize(container)
        assert loader.container is container


class TestPluginLoading:
    """Test plugin loading functionality."""

    def test_load_plugin(self):
        """Test loading a plugin."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a test plugin
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

        test_plugin = TestPlugin()

        # Test loading
        loaded_plugin = loader.load_plugin(test_plugin)
        assert loaded_plugin is test_plugin
        assert test_plugin.initialized is True

    def test_load_plugin_with_container(self):
        """Test loading a plugin with container."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
        container = ServiceContainer()
        loader = PluginLoader(registry)
        loader.initialize(container)

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
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

        test_plugin = TestPlugin()

        # Test loading with container
        loaded_plugin = loader.load_plugin(test_plugin)
        assert loaded_plugin is test_plugin
        assert test_plugin.initialized is True
        assert test_plugin.container is container

    def test_unload_plugin(self):
        """Test unloading a plugin."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a test plugin
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

        test_plugin = TestPlugin()

        # Load plugin
        loaded_plugin = loader.load_plugin(test_plugin)
        assert test_plugin.initialized is True

        # Unload plugin
        loader.unload_plugin(test_plugin)
        assert test_plugin.shutdown_called is True

    def test_get_loaded_plugin(self):
        """Test getting a loaded plugin."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()

        # Load plugin
        loader.load_plugin(test_plugin)

        # Get loaded plugin
        retrieved = loader.get_loaded_plugin("test_plugin")
        assert retrieved is test_plugin

    def test_get_nonexistent_loaded_plugin(self):
        """Test getting non-existent loaded plugin."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        result = loader.get_loaded_plugin("nonexistent_plugin")
        assert result is None

    def test_get_all_loaded_plugins(self):
        """Test getting all loaded plugins."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create and load multiple plugins
        plugins = []
        for i in range(5):
            class TestPlugin(Plugin):
                def __init__(self, plugin_id):
                    self.name = f"test_plugin_{plugin_id}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_plugin = TestPlugin(i)
            plugins.append(test_plugin)
            loader.load_plugin(test_plugin)

        # Get all loaded plugins
        all_plugins = loader.get_loaded_plugins()
        assert len(all_plugins) == 5

        for plugin in plugins:
            assert plugin in all_plugins.values()


class TestPluginLoadingEdgeCases:
    """Test plugin loading edge cases."""

    def test_load_plugin_without_name(self):
        """Test loading a plugin without a name."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a plugin without name
        class TestPlugin(Plugin):
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

        test_plugin = TestPlugin()

        # Should raise an error or handle gracefully
        with pytest.raises((PluginLoaderError, AttributeError)):
            loader.load_plugin(test_plugin)

    def test_load_plugin_with_invalid_name(self):
        """Test loading a plugin with invalid name."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a plugin with invalid name
        class TestPlugin(Plugin):
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

        test_plugin = TestPlugin()

        # Should handle gracefully
        loaded_plugin = loader.load_plugin(test_plugin)
        assert loaded_plugin is test_plugin

    def test_load_duplicate_plugin(self):
        """Test loading duplicate plugins."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create two plugins with same name
        class TestPlugin(Plugin):
            def __init__(self, plugin_id):
                self.name = "duplicate_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.plugin_id = plugin_id

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        plugin1 = TestPlugin(1)
        plugin2 = TestPlugin(2)

        # Load first plugin
        loaded1 = loader.load_plugin(plugin1)
        assert loaded1 is plugin1

        # Load second plugin with same name
        loaded2 = loader.load_plugin(plugin2)
        assert loaded2 is plugin2

        # Should return the second plugin
        retrieved = loader.get_loaded_plugin("duplicate_plugin")
        assert retrieved is plugin2

    def test_unload_nonexistent_plugin(self):
        """Test unloading non-existent plugin."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()

        # Try to unload plugin that wasn't loaded
        result = loader.unload_plugin(test_plugin)
        assert result is False


class TestPluginLoadingPerformance:
    """Test plugin loading performance."""

    def test_mass_plugin_loading(self):
        """Test mass plugin loading."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create and load many plugins
        plugins = []
        for i in range(100):
            class TestPlugin(Plugin):
                def __init__(self, plugin_id):
                    self.name = f"mass_plugin_{plugin_id}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_plugin = TestPlugin(i)
            plugins.append(test_plugin)
            loader.load_plugin(test_plugin)

        # Verify all plugins are loaded
        all_plugins = loader.get_loaded_plugins()
        assert len(all_plugins) == 100

        for plugin in plugins:
            assert plugin in all_plugins.values()

    def test_plugin_loading_performance(self):
        """Test plugin loading performance."""
        import time

        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Test loading performance
        start_time = time.time()
        for i in range(1000):
            class TestPlugin(Plugin):
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
                    return {"test": True}

            test_plugin = TestPlugin(i)
            loader.load_plugin(test_plugin)
        loading_time = time.time() - start_time

        # Test unloading performance
        start_time = time.time()
        for i in range(1000):
            loader.unload_plugin(loader.get_loaded_plugin(f"perf_plugin_{i}"))
        unloading_time = time.time() - start_time

        # Should be fast operations
        assert loading_time < 2.0
        assert unloading_time < 1.0


class TestPluginLoaderIntegration:
    """Test plugin loader integration scenarios."""

    def test_plugin_loader_with_registry(self):
        """Test plugin loader integration with registry."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "integration_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()

        # Load plugin
        loaded_plugin = loader.load_plugin(test_plugin)

        # Verify plugin is accessible through registry
        retrieved = registry.get_plugin("integration_plugin")
        assert retrieved is loaded_plugin

    def test_plugin_loader_with_lifecycle_manager(self):
        """Test plugin loader integration with lifecycle manager."""
        from nodupe.core.plugin_system.lifecycle import PluginLifecycleManager

        registry = PluginRegistry()
        loader = PluginLoader(registry)
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "lifecycle_plugin"
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

        test_plugin = TestPlugin()

        # Load plugin
        loaded_plugin = loader.load_plugin(test_plugin)

        # Initialize through lifecycle manager
        lifecycle_manager.initialize_plugin("lifecycle_plugin")
        assert test_plugin.initialized is True

        # Shutdown through lifecycle manager
        lifecycle_manager.shutdown_plugin("lifecycle_plugin")
        assert test_plugin.shutdown_called is True


class TestPluginLoaderErrorHandling:
    """Test plugin loader error handling."""

    def test_load_invalid_plugin(self):
        """Test loading an invalid plugin."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create an invalid plugin (not inheriting from Plugin)
        class InvalidPlugin:
            def __init__(self):
                self.name = "invalid_plugin"

        invalid_plugin = InvalidPlugin()

        # Should raise an error
        with pytest.raises(PluginLoaderError):
            loader.load_plugin(invalid_plugin)

    def test_load_plugin_with_missing_methods(self):
        """Test loading a plugin with missing required methods."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a plugin missing required methods
        class IncompletePlugin(Plugin):
            def __init__(self):
                self.name = "incomplete_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                # Missing initialize and shutdown methods

        incomplete_plugin = IncompletePlugin()

        # Should raise an error
        with pytest.raises(PluginLoaderError):
            loader.load_plugin(incomplete_plugin)

    def test_load_plugin_with_exception_in_initialize(self):
        """Test loading a plugin that throws exception in initialize."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a plugin that throws exception in initialize
        class FailingPlugin(Plugin):
            def __init__(self):
                self.name = "failing_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                raise Exception("Initialize failed")

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        failing_plugin = FailingPlugin()

        # Should raise an error
        with pytest.raises(Exception):
            loader.load_plugin(failing_plugin)
