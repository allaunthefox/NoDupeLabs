"""Test plugin hot reload functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from nodupe.core.plugin_system.hot_reload import PluginHotReload
from nodupe.core.plugin_system.registry import PluginRegistry


class TestPluginHotReload:
    """Test plugin hot reload core functionality."""

    def test_plugin_hot_reload_initialization(self):
        """Test plugin hot reload initialization."""
        hot_reload = PluginHotReload()
        assert hot_reload is not None
        assert isinstance(hot_reload, PluginHotReload)

        # Test that it has expected attributes
        assert hasattr(hot_reload, 'watch_plugin')
        assert hasattr(hot_reload, 'start')
        assert hasattr(hot_reload, 'stop')
        assert hasattr(hot_reload, 'initialize')
        assert hasattr(hot_reload, 'shutdown')

    def test_plugin_hot_reload_with_container(self):
        """Test plugin hot reload with dependency container."""
        from nodupe.core.container import ServiceContainer

        hot_reload = PluginHotReload()
        container = ServiceContainer()

        # Initialize hot reload with container
        hot_reload.initialize(container)
        assert hot_reload.container is container

    def test_plugin_hot_reload_lifecycle(self):
        """Test plugin hot reload lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        hot_reload = PluginHotReload()
        container = ServiceContainer()

        # Test initialization
        hot_reload.initialize(container)
        assert hot_reload.container is container

        # Test shutdown
        hot_reload.shutdown()
        assert hot_reload.container is None

        # Test re-initialization
        hot_reload.initialize(container)
        assert hot_reload.container is container


class TestPluginHotReloadOperations:
    """Test plugin hot reload operations."""

    def test_watch_plugin(self):
        """Test watching a plugin."""
        hot_reload = PluginHotReload()

        # Watch a plugin
        hot_reload.watch_plugin("test_plugin", Path("/test/plugin.py"))

        # Verify plugin is being watched
        assert "test_plugin" in hot_reload._watched_plugins
        assert hot_reload._watched_plugins["test_plugin"] == Path(
            "/test/plugin.py")

    def test_watch_multiple_plugins(self):
        """Test watching multiple plugins."""
        hot_reload = PluginHotReload()

        # Watch multiple plugins
        plugins = [
            ("plugin1", Path("/test/plugin1.py")),
            ("plugin2", Path("/test/plugin2.py")),
            ("plugin3", Path("/test/plugin3.py"))
        ]

        for name, path in plugins:
            hot_reload.watch_plugin(name, path)

        # Verify all plugins are being watched
        for name, path in plugins:
            assert name in hot_reload._watched_plugins
            assert hot_reload._watched_plugins[name] == path

    def test_start_hot_reload(self):
        """Test starting hot reload."""
        hot_reload = PluginHotReload()

        # Mock the poll loop
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()

            # Verify poll loop was started
            mock_poll_loop.assert_called_once()

    def test_stop_hot_reload(self):
        """Test stopping hot reload."""
        hot_reload = PluginHotReload()

        # Start hot reload
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()

            # Stop hot reload
            hot_reload.stop()

            # Verify running flag is set to False
            assert hot_reload._running is False

    def test_hot_reload_lifecycle(self):
        """Test hot reload lifecycle."""
        hot_reload = PluginHotReload()

        # Start hot reload
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()
            assert hot_reload._running is True

            # Stop hot reload
            hot_reload.stop()
            assert hot_reload._running is False


class TestPluginHotReloadEdgeCases:
    """Test plugin hot reload edge cases."""

    def test_watch_duplicate_plugin(self):
        """Test watching duplicate plugin."""
        hot_reload = PluginHotReload()

        # Watch a plugin
        hot_reload.watch_plugin("test_plugin", Path("/test/plugin.py"))

        # Watch the same plugin again (should overwrite)
        hot_reload.watch_plugin("test_plugin", Path("/test/plugin_new.py"))

        # Verify plugin path was updated
        assert hot_reload._watched_plugins["test_plugin"] == Path(
            "/test/plugin_new.py")

    def test_watch_plugin_with_nonexistent_path(self):
        """Test watching plugin with non-existent path."""
        hot_reload = PluginHotReload()

        # Watch a plugin with non-existent path
        hot_reload.watch_plugin("test_plugin", Path("/nonexistent/plugin.py"))

        # Should still be watched (validation happens during reload)
        assert "test_plugin" in hot_reload._watched_plugins

    def test_start_hot_reload_already_running(self):
        """Test starting hot reload when already running."""
        hot_reload = PluginHotReload()

        # Start hot reload
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()
            assert hot_reload._running is True

            # Try to start again
            hot_reload.start()

            # Should not start again
            assert mock_poll_loop.call_count == 1

    def test_stop_hot_reload_not_running(self):
        """Test stopping hot reload when not running."""
        hot_reload = PluginHotReload()

        # Stop hot reload when not running
        hot_reload.stop()

        # Should handle gracefully
        assert hot_reload._running is False


class TestPluginHotReloadPerformance:
    """Test plugin hot reload performance."""

    def test_mass_plugin_watching(self):
        """Test mass plugin watching."""
        hot_reload = PluginHotReload()

        # Watch many plugins
        for i in range(100):
            hot_reload.watch_plugin(
                f"plugin_{i}", Path(
                    f"/test/plugin_{i}.py"))

        # Verify all plugins are being watched
        assert len(hot_reload._watched_plugins) == 100

        for i in range(100):
            assert f"plugin_{i}" in hot_reload._watched_plugins

    def test_hot_reload_performance(self):
        """Test hot reload performance."""
        import time

        hot_reload = PluginHotReload()

        # Test watching performance
        start_time = time.time()
        for i in range(1000):
            hot_reload.watch_plugin(
                f"perf_plugin_{i}", Path(
                    f"/test/plugin_{i}.py"))
        watch_time = time.time() - start_time

        # Should be fast operation
        assert watch_time < 0.1

        # Verify all plugins are being watched
        assert len(hot_reload._watched_plugins) == 1000


class TestPluginHotReloadIntegration:
    """Test plugin hot reload integration scenarios."""

    def test_hot_reload_with_registry(self):
        """Test hot reload integration with registry."""
        hot_reload = PluginHotReload()
        registry = PluginRegistry()

        # Watch a plugin
        hot_reload.watch_plugin("test_plugin", Path("/test/plugin.py"))

        # Verify integration
        assert "test_plugin" in hot_reload._watched_plugins

    def test_hot_reload_with_loader(self):
        """Test hot reload integration with loader."""
        from nodupe.core.plugin_system.loader import PluginLoader

        hot_reload = PluginHotReload()
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Watch a plugin
        hot_reload.watch_plugin("test_plugin", Path("/test/plugin.py"))

        # Verify integration
        assert "test_plugin" in hot_reload._watched_plugins


class TestPluginHotReloadErrorHandling:
    """Test plugin hot reload error handling."""

    def test_watch_plugin_with_invalid_name(self):
        """Test watching plugin with invalid name."""
        hot_reload = PluginHotReload()

        # Watch a plugin with invalid name
        hot_reload.watch_plugin("", Path("/test/plugin.py"))

        # Should handle gracefully
        assert "" in hot_reload._watched_plugins

    def test_watch_plugin_with_invalid_path(self):
        """Test watching plugin with invalid path."""
        hot_reload = PluginHotReload()

        # Watch a plugin with invalid path
        hot_reload.watch_plugin("test_plugin", None)

        # Should handle gracefully
        assert "test_plugin" in hot_reload._watched_plugins
        assert hot_reload._watched_plugins["test_plugin"] is None

    def test_start_hot_reload_with_exception(self):
        """Test starting hot reload when exception occurs."""
        hot_reload = PluginHotReload()

        # Mock poll loop to raise exception
        with patch.object(hot_reload, '_poll_loop', side_effect=Exception("Poll loop failed")):
            # Should handle exception gracefully
            hot_reload.start()

            # Verify running flag is still set appropriately
            assert hot_reload._running is True


class TestPluginHotReloadAdvanced:
    """Test advanced plugin hot reload functionality."""

    def test_hot_reload_with_plugin_lifecycle(self):
        """Test hot reload with plugin lifecycle."""
        hot_reload = PluginHotReload()

        # Watch multiple plugins
        plugins = [
            ("plugin1", Path("/test/plugin1.py")),
            ("plugin2", Path("/test/plugin2.py")),
            ("plugin3", Path("/test/plugin3.py"))
        ]

        for name, path in plugins:
            hot_reload.watch_plugin(name, path)

        # Verify all plugins are being watched
        for name, path in plugins:
            assert name in hot_reload._watched_plugins
            assert hot_reload._watched_plugins[name] == path

    def test_hot_reload_with_conditional_watching(self):
        """Test hot reload with conditional watching."""
        hot_reload = PluginHotReload()

        # Watch plugins conditionally
        for i in range(10):
            if i % 2 == 0:  # Only watch even-numbered plugins
                hot_reload.watch_plugin(
                    f"plugin_{i}", Path(
                        f"/test/plugin_{i}.py"))

        # Verify only even-numbered plugins are being watched
        assert len(hot_reload._watched_plugins) == 5

        for i in range(10):
            if i % 2 == 0:
                assert f"plugin_{i}" in hot_reload._watched_plugins
            else:
                assert f"plugin_{i}" not in hot_reload._watched_plugins

    def test_hot_reload_with_dynamic_plugin_management(self):
        """Test hot reload with dynamic plugin management."""
        hot_reload = PluginHotReload()

        # Watch initial set of plugins
        initial_plugins = [("plugin1", Path("/test/plugin1.py")),
                           ("plugin2", Path("/test/plugin2.py"))]
        for name, path in initial_plugins:
            hot_reload.watch_plugin(name, path)

        # Verify initial plugins are being watched
        assert len(hot_reload._watched_plugins) == 2

        # Add more plugins dynamically
        new_plugins = [("plugin3", Path("/test/plugin3.py")),
                       ("plugin4", Path("/test/plugin4.py"))]
        for name, path in new_plugins:
            hot_reload.watch_plugin(name, path)

        # Verify all plugins are being watched
        assert len(hot_reload._watched_plugins) == 4

        # Remove some plugins
        hot_reload._watched_plugins.pop("plugin1")
        hot_reload._watched_plugins.pop("plugin2")

        # Verify only new plugins remain
        assert len(hot_reload._watched_plugins) == 2
        assert "plugin3" in hot_reload._watched_plugins
        assert "plugin4" in hot_reload._watched_plugins
