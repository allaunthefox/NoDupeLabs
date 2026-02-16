"""Test tool hot reload functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from nodupe.core.tool_system.hot_reload import ToolHotReload
from nodupe.core.tool_system.registry import ToolRegistry


class TestToolHotReload:
    """Test tool hot reload core functionality."""

    def test_tool_hot_reload_initialization(self):
        """Test tool hot reload initialization."""
        hot_reload = ToolHotReload()
        assert hot_reload is not None
        assert isinstance(hot_reload, ToolHotReload)

        # Test that it has expected attributes
        assert hasattr(hot_reload, 'watch_tool')
        assert hasattr(hot_reload, 'start')
        assert hasattr(hot_reload, 'stop')
        assert hasattr(hot_reload, 'initialize')
        assert hasattr(hot_reload, 'shutdown')

    def test_tool_hot_reload_with_container(self):
        """Test tool hot reload with dependency container."""
        from nodupe.core.container import ServiceContainer

        hot_reload = ToolHotReload()
        container = ServiceContainer()

        # Initialize hot reload with container
        hot_reload.initialize(container)
        assert hot_reload.container is container

    def test_tool_hot_reload_lifecycle(self):
        """Test tool hot reload lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        hot_reload = ToolHotReload()
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


class TestToolHotReloadOperations:
    """Test tool hot reload operations."""

    def test_watch_tool(self):
        """Test watching a tool."""
        hot_reload = ToolHotReload()

        # Watch a tool
        hot_reload.watch_tool("test_tool", Path("/test/tool.py"))

        # Verify tool is being watched
        assert "test_tool" in hot_reload._watched_tools
        assert hot_reload._watched_tools["test_tool"] == Path(
            "/test/tool.py")

    def test_watch_multiple_tools(self):
        """Test watching multiple tools."""
        hot_reload = ToolHotReload()

        # Watch multiple tools
        tools = [
            ("tool1", Path("/test/tool1.py")),
            ("tool2", Path("/test/tool2.py")),
            ("tool3", Path("/test/tool3.py"))
        ]

        for name, path in tools:
            hot_reload.watch_tool(name, path)

        # Verify all tools are being watched
        for name, path in tools:
            assert name in hot_reload._watched_tools
            assert hot_reload._watched_tools[name] == path

    def test_start_hot_reload(self):
        """Test starting hot reload."""
        hot_reload = ToolHotReload()

        # Mock the poll loop
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()

            # Verify poll loop was started
            mock_poll_loop.assert_called_once()

    def test_stop_hot_reload(self):
        """Test stopping hot reload."""
        hot_reload = ToolHotReload()

        # Start hot reload
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()

            # Stop hot reload
            hot_reload.stop()

            # Verify running flag is set to False
            assert hot_reload._running is False

    def test_hot_reload_lifecycle(self):
        """Test hot reload lifecycle."""
        hot_reload = ToolHotReload()

        # Start hot reload
        with patch.object(hot_reload, '_poll_loop') as mock_poll_loop:
            hot_reload.start()
            assert hot_reload._running is True

            # Stop hot reload
            hot_reload.stop()
            assert hot_reload._running is False


class TestToolHotReloadEdgeCases:
    """Test tool hot reload edge cases."""

    def test_watch_duplicate_tool(self):
        """Test watching duplicate tool."""
        hot_reload = ToolHotReload()

        # Watch a tool
        hot_reload.watch_tool("test_tool", Path("/test/tool.py"))

        # Watch the same tool again (should overwrite)
        hot_reload.watch_tool("test_tool", Path("/test/tool_new.py"))

        # Verify tool path was updated
        assert hot_reload._watched_tools["test_tool"] == Path(
            "/test/tool_new.py")

    def test_watch_tool_with_nonexistent_path(self):
        """Test watching tool with non-existent path."""
        hot_reload = ToolHotReload()

        # Watch a tool with non-existent path
        hot_reload.watch_tool("test_tool", Path("/nonexistent/tool.py"))

        # Should still be watched (validation happens during reload)
        assert "test_tool" in hot_reload._watched_tools

    def test_start_hot_reload_already_running(self):
        """Test starting hot reload when already running."""
        hot_reload = ToolHotReload()

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
        hot_reload = ToolHotReload()

        # Stop hot reload when not running
        hot_reload.stop()

        # Should handle gracefully
        assert hot_reload._running is False


class TestToolHotReloadPerformance:
    """Test tool hot reload performance."""

    def test_mass_tool_watching(self):
        """Test mass tool watching."""
        hot_reload = ToolHotReload()

        # Watch many tools
        for i in range(100):
            hot_reload.watch_tool(
                f"tool_{i}", Path(
                    f"/test/tool_{i}.py"))

        # Verify all tools are being watched
        assert len(hot_reload._watched_tools) == 100

        for i in range(100):
            assert f"tool_{i}" in hot_reload._watched_tools

    def test_hot_reload_performance(self):
        """Test hot reload performance."""
        import time

        hot_reload = ToolHotReload()

        # Test watching performance
        start_time = time.time()
        for i in range(1000):
            hot_reload.watch_tool(
                f"perf_tool_{i}", Path(
                    f"/test/tool_{i}.py"))
        watch_time = time.time() - start_time

        # Should be fast operation
        assert watch_time < 0.1

        # Verify all tools are being watched
        assert len(hot_reload._watched_tools) == 1000


class TestToolHotReloadIntegration:
    """Test tool hot reload integration scenarios."""

    def test_hot_reload_with_registry(self):
        """Test hot reload integration with registry."""
        hot_reload = ToolHotReload()
        registry = ToolRegistry()

        # Watch a tool
        hot_reload.watch_tool("test_tool", Path("/test/tool.py"))

        # Verify integration
        assert "test_tool" in hot_reload._watched_tools

    def test_hot_reload_with_loader(self):
        """Test hot reload integration with loader."""
        from nodupe.core.tool_system.loader import ToolLoader

        hot_reload = ToolHotReload()
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Watch a tool
        hot_reload.watch_tool("test_tool", Path("/test/tool.py"))

        # Verify integration
        assert "test_tool" in hot_reload._watched_tools


class TestToolHotReloadErrorHandling:
    """Test tool hot reload error handling."""

    def test_watch_tool_with_invalid_name(self):
        """Test watching tool with invalid name."""
        hot_reload = ToolHotReload()

        # Watch a tool with invalid name
        hot_reload.watch_tool("", Path("/test/tool.py"))

        # Should handle gracefully
        assert "" in hot_reload._watched_tools

    def test_watch_tool_with_invalid_path(self):
        """Test watching tool with invalid path."""
        hot_reload = ToolHotReload()

        # Watch a tool with invalid path
        hot_reload.watch_tool("test_tool", None)

        # Should handle gracefully
        assert "test_tool" in hot_reload._watched_tools
        assert hot_reload._watched_tools["test_tool"] is None

    def test_start_hot_reload_with_exception(self):
        """Test starting hot reload when exception occurs."""
        hot_reload = ToolHotReload()

        # Mock poll loop to raise exception
        with patch.object(hot_reload, '_poll_loop', side_effect=Exception("Poll loop failed")):
            # Should handle exception gracefully
            hot_reload.start()

            # Verify running flag is still set appropriately
            assert hot_reload._running is True


class TestToolHotReloadAdvanced:
    """Test advanced tool hot reload functionality."""

    def test_hot_reload_with_tool_lifecycle(self):
        """Test hot reload with tool lifecycle."""
        hot_reload = ToolHotReload()

        # Watch multiple tools
        tools = [
            ("tool1", Path("/test/tool1.py")),
            ("tool2", Path("/test/tool2.py")),
            ("tool3", Path("/test/tool3.py"))
        ]

        for name, path in tools:
            hot_reload.watch_tool(name, path)

        # Verify all tools are being watched
        for name, path in tools:
            assert name in hot_reload._watched_tools
            assert hot_reload._watched_tools[name] == path

    def test_hot_reload_with_conditional_watching(self):
        """Test hot reload with conditional watching."""
        hot_reload = ToolHotReload()

        # Watch tools conditionally
        for i in range(10):
            if i % 2 == 0:  # Only watch even-numbered tools
                hot_reload.watch_tool(
                    f"tool_{i}", Path(
                        f"/test/tool_{i}.py"))

        # Verify only even-numbered tools are being watched
        assert len(hot_reload._watched_tools) == 5

        for i in range(10):
            if i % 2 == 0:
                assert f"tool_{i}" in hot_reload._watched_tools
            else:
                assert f"tool_{i}" not in hot_reload._watched_tools

    def test_hot_reload_with_dynamic_tool_management(self):
        """Test hot reload with dynamic tool management."""
        hot_reload = ToolHotReload()

        # Watch initial set of tools
        initial_tools = [("tool1", Path("/test/tool1.py")),
                           ("tool2", Path("/test/tool2.py"))]
        for name, path in initial_tools:
            hot_reload.watch_tool(name, path)

        # Verify initial tools are being watched
        assert len(hot_reload._watched_tools) == 2

        # Add more tools dynamically
        new_tools = [("tool3", Path("/test/tool3.py")),
                       ("tool4", Path("/test/tool4.py"))]
        for name, path in new_tools:
            hot_reload.watch_tool(name, path)

        # Verify all tools are being watched
        assert len(hot_reload._watched_tools) == 4

        # Remove some tools
        hot_reload._watched_tools.pop("tool1")
        hot_reload._watched_tools.pop("tool2")

        # Verify only new tools remain
        assert len(hot_reload._watched_tools) == 2
        assert "tool3" in hot_reload._watched_tools
        assert "tool4" in hot_reload._watched_tools
