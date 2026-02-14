"""Test plugin lifecycle functionality."""

import pytest
from unittest.mock import MagicMock
from nodupe.core.plugin_system.lifecycle import PluginLifecycleManager, PluginLifecycleError, PluginState
from nodupe.core.plugin_system.registry import PluginRegistry
from nodupe.core.plugin_system.base import Plugin


class TestPluginLifecycleManager:
    """Test plugin lifecycle manager core functionality."""

    def test_plugin_lifecycle_manager_initialization(self):
        """Test plugin lifecycle manager initialization."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        assert lifecycle_manager is not None
        assert isinstance(lifecycle_manager, PluginLifecycleManager)
        assert lifecycle_manager.registry is registry

        # Test that it has expected attributes
        assert hasattr(lifecycle_manager, 'initialize_plugin')
        assert hasattr(lifecycle_manager, 'shutdown_plugin')
        assert hasattr(lifecycle_manager, 'initialize_all_plugins')
        assert hasattr(lifecycle_manager, 'shutdown_all_plugins')
        assert hasattr(lifecycle_manager, 'get_plugin_state')
        assert hasattr(lifecycle_manager, 'is_plugin_initialized')
        assert hasattr(lifecycle_manager, 'is_plugin_active')
        assert hasattr(lifecycle_manager, 'get_active_plugins')
        assert hasattr(lifecycle_manager, 'get_plugin_dependencies')
        assert hasattr(lifecycle_manager, 'set_plugin_dependencies')
        assert hasattr(lifecycle_manager, 'initialize')
        assert hasattr(lifecycle_manager, 'shutdown')

    def test_plugin_lifecycle_manager_with_container(self):
        """Test plugin lifecycle manager with dependency container."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
        container = ServiceContainer()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Initialize lifecycle manager with container
        lifecycle_manager.initialize(container)
        assert lifecycle_manager.container is container

    def test_plugin_lifecycle_manager_lifecycle(self):
        """Test plugin lifecycle manager lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        registry = PluginRegistry()
        container = ServiceContainer()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Test initialization
        lifecycle_manager.initialize(container)
        assert lifecycle_manager.container is container

        # Test shutdown
        lifecycle_manager.shutdown()
        assert lifecycle_manager.container is None

        # Test re-initialization
        lifecycle_manager.initialize(container)
        assert lifecycle_manager.container is container


class TestPluginState:
    """Test plugin state functionality."""

    def test_plugin_state_enum(self):
        """Test plugin state enum values."""
        # Test that all expected states are present
        assert hasattr(PluginState, 'UNINITIALIZED')
        assert hasattr(PluginState, 'INITIALIZED')
        assert hasattr(PluginState, 'ACTIVE')
        assert hasattr(PluginState, 'FAILED')

        # Test state values
        assert PluginState.UNINITIALIZED.value == 0
        assert PluginState.INITIALIZED.value == 1
        assert PluginState.ACTIVE.value == 2
        assert PluginState.FAILED.value == 3


class TestPluginLifecycleOperations:
    """Test plugin lifecycle operations."""

    def test_initialize_plugin(self):
        """Test initializing a plugin."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Initialize plugin
        result = lifecycle_manager.initialize_plugin("test_plugin")
        assert result is True
        assert test_plugin.initialized is True

        # Check plugin state
        state = lifecycle_manager.get_plugin_state("test_plugin")
        assert state == PluginState.INITIALIZED

    def test_shutdown_plugin(self):
        """Test shutting down a plugin."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Initialize plugin
        lifecycle_manager.initialize_plugin("test_plugin")
        assert test_plugin.initialized is True

        # Shutdown plugin
        result = lifecycle_manager.shutdown_plugin("test_plugin")
        assert result is True
        assert test_plugin.shutdown_called is True

        # Check plugin state
        state = lifecycle_manager.get_plugin_state("test_plugin")
        assert state == PluginState.UNINITIALIZED

    def test_initialize_all_plugins(self):
        """Test initializing all plugins."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create multiple test plugins
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
            registry.register(test_plugin)

        # Initialize all plugins
        result = lifecycle_manager.initialize_all_plugins(MagicMock())
        assert result is True

        # Verify all plugins are initialized
        for plugin in plugins:
            assert plugin.initialized is True
            state = lifecycle_manager.get_plugin_state(plugin.name)
            assert state == PluginState.INITIALIZED

    def test_shutdown_all_plugins(self):
        """Test shutting down all plugins."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create multiple test plugins
        plugins = []
        for i in range(5):
            class TestPlugin(Plugin):
                def __init__(self, plugin_id):
                    self.name = f"test_plugin_{plugin_id}"
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

            test_plugin = TestPlugin(i)
            plugins.append(test_plugin)
            registry.register(test_plugin)

        # Initialize all plugins
        lifecycle_manager.initialize_all_plugins(MagicMock())

        # Shutdown all plugins
        result = lifecycle_manager.shutdown_all_plugins()
        assert result is True

        # Verify all plugins are shutdown
        for plugin in plugins:
            assert plugin.shutdown_called is True
            state = lifecycle_manager.get_plugin_state(plugin.name)
            assert state == PluginState.UNINITIALIZED

    def test_get_plugin_state(self):
        """Test getting plugin state."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Check initial state
        state = lifecycle_manager.get_plugin_state("test_plugin")
        assert state == PluginState.UNINITIALIZED

        # Initialize plugin
        lifecycle_manager.initialize_plugin("test_plugin")

        # Check state after initialization
        state = lifecycle_manager.get_plugin_state("test_plugin")
        assert state == PluginState.INITIALIZED

    def test_is_plugin_initialized(self):
        """Test checking if plugin is initialized."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Check before initialization
        result = lifecycle_manager.is_plugin_initialized("test_plugin")
        assert result is False

        # Initialize plugin
        lifecycle_manager.initialize_plugin("test_plugin")

        # Check after initialization
        result = lifecycle_manager.is_plugin_initialized("test_plugin")
        assert result is True

    def test_is_plugin_active(self):
        """Test checking if plugin is active."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Check before initialization
        result = lifecycle_manager.is_plugin_active("test_plugin")
        assert result is False

        # Initialize plugin
        lifecycle_manager.initialize_plugin("test_plugin")

        # Check after initialization (should be active)
        result = lifecycle_manager.is_plugin_active("test_plugin")
        assert result is True

    def test_get_active_plugins(self):
        """Test getting active plugins."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create multiple test plugins
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
            registry.register(test_plugin)

        # Initialize some plugins
        lifecycle_manager.initialize_plugin("test_plugin_0")
        lifecycle_manager.initialize_plugin("test_plugin_2")
        lifecycle_manager.initialize_plugin("test_plugin_4")

        # Get active plugins
        active_plugins = lifecycle_manager.get_active_plugins()
        assert len(active_plugins) == 3
        assert "test_plugin_0" in active_plugins
        assert "test_plugin_2" in active_plugins
        assert "test_plugin_4" in active_plugins

    def test_get_plugin_dependencies(self):
        """Test getting plugin dependencies."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = ["dep1", "dep2"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()
        registry.register(test_plugin)

        # Get plugin dependencies
        dependencies = lifecycle_manager.get_plugin_dependencies("test_plugin")
        assert dependencies == ["dep1", "dep2"]

    def test_set_plugin_dependencies(self):
        """Test setting plugin dependencies."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Set plugin dependencies
        lifecycle_manager.set_plugin_dependencies(
            "test_plugin", ["new_dep1", "new_dep2"])

        # Get plugin dependencies
        dependencies = lifecycle_manager.get_plugin_dependencies("test_plugin")
        assert dependencies == ["new_dep1", "new_dep2"]


class TestPluginLifecycleEdgeCases:
    """Test plugin lifecycle edge cases."""

    def test_initialize_nonexistent_plugin(self):
        """Test initializing non-existent plugin."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Try to initialize non-existent plugin
        result = lifecycle_manager.initialize_plugin("nonexistent_plugin")
        assert result is False

    def test_shutdown_nonexistent_plugin(self):
        """Test shutting down non-existent plugin."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Try to shutdown non-existent plugin
        result = lifecycle_manager.shutdown_plugin("nonexistent_plugin")
        assert result is False

    def test_initialize_plugin_with_exception(self):
        """Test initializing plugin that throws exception."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create a test plugin that throws exception
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
        registry.register(failing_plugin)

        # Try to initialize plugin
        result = lifecycle_manager.initialize_plugin("failing_plugin")
        assert result is False

        # Check plugin state
        state = lifecycle_manager.get_plugin_state("failing_plugin")
        assert state == PluginState.FAILED

    def test_shutdown_plugin_with_exception(self):
        """Test shutting down plugin that throws exception."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create a test plugin that throws exception in shutdown
        class FailingPlugin(Plugin):
            def __init__(self):
                self.name = "failing_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                raise Exception("Shutdown failed")

            def get_capabilities(self):
                return {"test": True}

        failing_plugin = FailingPlugin()
        registry.register(failing_plugin)

        # Initialize plugin
        lifecycle_manager.initialize_plugin("failing_plugin")

        # Try to shutdown plugin
        result = lifecycle_manager.shutdown_plugin("failing_plugin")
        assert result is False

        # Check plugin state
        state = lifecycle_manager.get_plugin_state("failing_plugin")
        assert state == PluginState.FAILED

    def test_initialize_already_initialized_plugin(self):
        """Test initializing already initialized plugin."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Initialize plugin
        result1 = lifecycle_manager.initialize_plugin("test_plugin")
        assert result1 is True

        # Try to initialize again
        result2 = lifecycle_manager.initialize_plugin("test_plugin")
        assert result2 is False  # Should fail or return False

    def test_shutdown_already_shutdown_plugin(self):
        """Test shutting down already shutdown plugin."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Initialize and shutdown plugin
        lifecycle_manager.initialize_plugin("test_plugin")
        result1 = lifecycle_manager.shutdown_plugin("test_plugin")
        assert result1 is True

        # Try to shutdown again
        result2 = lifecycle_manager.shutdown_plugin("test_plugin")
        assert result2 is False  # Should fail or return False


class TestPluginLifecyclePerformance:
    """Test plugin lifecycle performance."""

    def test_mass_plugin_initialization(self):
        """Test mass plugin initialization."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create many test plugins
        plugins = []
        for i in range(100):
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
            registry.register(test_plugin)

        # Initialize all plugins
        result = lifecycle_manager.initialize_all_plugins(MagicMock())
        assert result is True

        # Verify all plugins are initialized
        for plugin in plugins:
            assert plugin.initialized is True

    def test_plugin_lifecycle_performance(self):
        """Test plugin lifecycle performance."""
        import time

        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create many test plugins
        plugins = []
        for i in range(1000):
            class TestPlugin(Plugin):
                def __init__(self, plugin_id):
                    self.name = f"perf_plugin_{plugin_id}"
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

            test_plugin = TestPlugin(i)
            plugins.append(test_plugin)
            registry.register(test_plugin)

        # Test initialization performance
        start_time = time.time()
        lifecycle_manager.initialize_all_plugins(MagicMock())
        init_time = time.time() - start_time

        # Test shutdown performance
        start_time = time.time()
        lifecycle_manager.shutdown_all_plugins()
        shutdown_time = time.time() - start_time

        # Should be fast operations
        assert init_time < 1.0
        assert shutdown_time < 0.5

        # Verify all plugins are initialized and shutdown
        for plugin in plugins:
            assert plugin.initialized is True
            assert plugin.shutdown_called is True


class TestPluginLifecycleIntegration:
    """Test plugin lifecycle integration scenarios."""

    def test_plugin_lifecycle_with_registry(self):
        """Test plugin lifecycle integration with registry."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Initialize plugin through lifecycle manager
        lifecycle_manager.initialize_plugin("test_plugin")

        # Verify plugin is accessible through registry
        retrieved = registry.get_plugin("test_plugin")
        assert retrieved is test_plugin
        assert retrieved.initialized is True

    def test_plugin_lifecycle_with_loader(self):
        """Test plugin lifecycle integration with loader."""
        from nodupe.core.plugin_system.loader import PluginLoader

        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)
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

        # Initialize through lifecycle manager
        lifecycle_manager.initialize_plugin("test_plugin")
        assert test_plugin.initialized is True

        # Shutdown through lifecycle manager
        lifecycle_manager.shutdown_plugin("test_plugin")
        assert test_plugin.shutdown_called is True


class TestPluginLifecycleErrorHandling:
    """Test plugin lifecycle error handling."""

    def test_initialize_plugin_with_missing_methods(self):
        """Test initializing plugin with missing required methods."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create a plugin missing required methods
        class IncompletePlugin(Plugin):
            def __init__(self):
                self.name = "incomplete_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                # Missing initialize and shutdown methods

        incomplete_plugin = IncompletePlugin()
        registry.register(incomplete_plugin)

        # Try to initialize plugin
        with pytest.raises(PluginLifecycleError):
            lifecycle_manager.initialize_plugin("incomplete_plugin")

    def test_initialize_plugin_with_invalid_state(self):
        """Test initializing plugin in invalid state."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Initialize plugin
        lifecycle_manager.initialize_plugin("test_plugin")

        # Manually set invalid state
        lifecycle_manager._plugin_states["test_plugin"] = "invalid_state"

        # Try to initialize again
        with pytest.raises(PluginLifecycleError):
            lifecycle_manager.initialize_plugin("test_plugin")

    def test_shutdown_plugin_with_invalid_state(self):
        """Test shutting down plugin in invalid state."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

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
        registry.register(test_plugin)

        # Manually set invalid state
        lifecycle_manager._plugin_states["test_plugin"] = "invalid_state"

        # Try to shutdown
        with pytest.raises(PluginLifecycleError):
            lifecycle_manager.shutdown_plugin("test_plugin")


class TestPluginLifecycleAdvanced:
    """Test advanced plugin lifecycle functionality."""

    def test_plugin_lifecycle_with_dependencies(self):
        """Test plugin lifecycle with dependencies."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create test plugins with dependencies
        class PluginA(Plugin):
            def __init__(self):
                self.name = "plugin_a"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"feature_a": True}

        class PluginB(Plugin):
            def __init__(self):
                self.name = "plugin_b"
                self.version = "1.0.0"
                self.dependencies = ["plugin_a"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"feature_b": True}

        plugin_a = PluginA()
        plugin_b = PluginB()
        registry.register(plugin_a)
        registry.register(plugin_b)

        # Set dependencies
        lifecycle_manager.set_plugin_dependencies("plugin_b", ["plugin_a"])

        # Initialize plugins (should handle dependencies)
        lifecycle_manager.initialize_plugin("plugin_a")
        lifecycle_manager.initialize_plugin("plugin_b")

        # Verify both plugins are initialized
        assert plugin_a.initialized is True
        assert plugin_b.initialized is True

    def test_plugin_lifecycle_with_circular_dependencies(self):
        """Test plugin lifecycle with circular dependencies."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create test plugins with circular dependencies
        class PluginA(Plugin):
            def __init__(self):
                self.name = "plugin_a"
                self.version = "1.0.0"
                self.dependencies = ["plugin_b"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"feature_a": True}

        class PluginB(Plugin):
            def __init__(self):
                self.name = "plugin_b"
                self.version = "1.0.0"
                self.dependencies = ["plugin_a"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"feature_b": True}

        plugin_a = PluginA()
        plugin_b = PluginB()
        registry.register(plugin_a)
        registry.register(plugin_b)

        # Set circular dependencies
        lifecycle_manager.set_plugin_dependencies("plugin_a", ["plugin_b"])
        lifecycle_manager.set_plugin_dependencies("plugin_b", ["plugin_a"])

        # Try to initialize (should handle gracefully)
        result = lifecycle_manager.initialize_plugin("plugin_a")
        assert result is False  # Should fail due to circular dependency

    def test_plugin_lifecycle_with_conditional_initialization(self):
        """Test plugin lifecycle with conditional initialization."""
        registry = PluginRegistry()
        lifecycle_manager = PluginLifecycleManager(registry)

        # Create test plugins with conditional initialization
        class PluginA(Plugin):
            def __init__(self):
                self.name = "plugin_a"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.initialization_attempts = 0

            def initialize(self, container):
                self.initialization_attempts += 1
                if self.initialization_attempts == 1:
                    raise Exception("First attempt failed")
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"feature_a": True}

        plugin_a = PluginA()
        registry.register(plugin_a)

        # First initialization attempt should fail
        result1 = lifecycle_manager.initialize_plugin("plugin_a")
        assert result1 is False

        # Second initialization attempt should succeed
        result2 = lifecycle_manager.initialize_plugin("plugin_a")
        assert result2 is True
        assert plugin_a.initialized is True
