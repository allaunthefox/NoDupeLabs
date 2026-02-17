"""Test tool hot reload functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
        assert hasattr(hot_reload, "watch_tool")
        assert hasattr(hot_reload, "start")
        assert hasattr(hot_reload, "stop")
        assert hasattr(hot_reload, "initialize")

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

        # Reset container (ToolHotReload exposes initialize but no shutdown)
        hot_reload.initialize(None)
        assert hot_reload.container is None

        # Test re-initialization
        hot_reload.initialize(container)
        assert hot_reload.container is container


class TestToolHotReloadOperations:
    """Test tool hot reload operations."""

    def test_watch_tool(self, tmp_path):
        """Test watching a tool."""
        hot_reload = ToolHotReload()

        # Create a temporary file and watch it
        tmp = tmp_path / "tool.py"
        tmp.write_text("# test tool")
        hot_reload.watch_tool("test_tool", tmp)

        # Verify tool is being watched
        assert "test_tool" in hot_reload._watched_tools
        assert hot_reload._watched_tools["test_tool"]["path"] == tmp

    def test_watch_multiple_tools(self, tmp_path):
        """Test watching multiple tools."""
        hot_reload = ToolHotReload()

        # Create files and watch multiple tools
        tools = []
        for i in range(3):
            p = tmp_path / f"tool{i}.py"
            p.write_text("# tool")
            tools.append((f"tool{i}", p))

        for name, path in tools:
            hot_reload.watch_tool(name, path)

        # Verify all tools are being watched
        for name, path in tools:
            assert name in hot_reload._watched_tools
            assert hot_reload._watched_tools[name]["path"] == path

    def test_start_hot_reload(self):
        """Test starting hot reload."""
        hot_reload = ToolHotReload()

        # Mock the poll loop
        with patch.object(hot_reload, "_poll_loop") as mock_poll_loop:
            hot_reload.start()

            # Verify poll loop was started
            mock_poll_loop.assert_called_once()

    def test_stop_hot_reload(self):
        """Test stopping hot reload."""
        hot_reload = ToolHotReload()

        # Start hot reload
        with patch.object(hot_reload, "_poll_loop"):
            hot_reload.start()

            # Stop hot reload
            hot_reload.stop()

            # Verify thread was cleaned up
            assert hot_reload._thread is None

    def test_hot_reload_lifecycle(self):
        """Test hot reload lifecycle."""
        hot_reload = ToolHotReload()

        # Start hot reload
        with patch.object(hot_reload, "_poll_loop"):
            hot_reload.start()
            assert hot_reload._thread is not None

            # Stop hot reload
            hot_reload.stop()
            assert hot_reload._thread is None


class TestToolHotReloadEdgeCases:
    """Test tool hot reload edge cases."""

    def test_watch_duplicate_tool(self, tmp_path):
        """Test watching duplicate tool."""
        hot_reload = ToolHotReload()

        p1 = tmp_path / "tool.py"
        p1.write_text("# v1")
        hot_reload.watch_tool("test_tool", p1)

        # Watch the same tool again (should overwrite)
        p2 = tmp_path / "tool_new.py"
        p2.write_text("# v2")
        hot_reload.watch_tool("test_tool", p2)

        # Verify tool path was updated
        assert hot_reload._watched_tools["test_tool"]["path"] == p2

    def test_watch_tool_with_nonexistent_path(self):
        """Test watching tool with non-existent path."""
        hot_reload = ToolHotReload()

        # Watch a tool with non-existent path
        hot_reload.watch_tool("test_tool", Path("/nonexistent/tool.py"))

        # Should NOT be watched because path does not exist
        assert "test_tool" not in hot_reload._watched_tools

    def test_start_hot_reload_already_running(self):
        """Test starting hot reload when already running."""
        hot_reload = ToolHotReload()

        # Start hot reload
        with patch.object(hot_reload, "_poll_loop") as mock_poll_loop:
            hot_reload.start()
            assert hot_reload._thread is not None

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
        assert hot_reload._thread is None


class TestToolHotReloadPerformance:
    """Test tool hot reload performance."""

    def test_mass_tool_watching(self, tmp_path):
        """Test mass tool watching."""
        hot_reload = ToolHotReload()

        # Watch many tools
        for i in range(100):
            p = tmp_path / f"tool_{i}.py"
            p.write_text("# tool")
            hot_reload.watch_tool(f"tool_{i}", p)

        # Verify all tools are being watched
        assert len(hot_reload._watched_tools) == 100

        for i in range(100):
            assert f"tool_{i}" in hot_reload._watched_tools

    def test_hot_reload_performance(self, tmp_path):
        """Test hot reload performance."""
        import time

        hot_reload = ToolHotReload()

        # Test watching performance
        start_time = time.time()
        for i in range(1000):
            p = tmp_path / f"perf_tool_{i}.py"
            p.write_text("# tool")
            hot_reload.watch_tool(f"perf_tool_{i}", p)
        watch_time = time.time() - start_time

        # Should be fast operation
        assert watch_time < 0.5

        # Verify all tools are being watched
        assert len(hot_reload._watched_tools) == 1000


class TestToolHotReloadIntegration:
    """Test tool hot reload integration scenarios."""

    def test_hot_reload_with_registry(self, tmp_path):
        """Test hot reload integration with registry."""
        hot_reload = ToolHotReload()
        ToolRegistry()

        p = tmp_path / "tool.py"
        p.write_text("# tool")
        # Watch a tool
        hot_reload.watch_tool("test_tool", p)

        # Verify integration
        assert "test_tool" in hot_reload._watched_tools

    def test_hot_reload_with_loader(self, tmp_path):
        """Test hot reload integration with loader."""
        from nodupe.core.tool_system.loader import ToolLoader

        hot_reload = ToolHotReload()
        registry = ToolRegistry()
        ToolLoader(registry)

        p = tmp_path / "tool.py"
        p.write_text("# tool")
        # Watch a tool
        hot_reload.watch_tool("test_tool", p)

        # Verify integration
        assert "test_tool" in hot_reload._watched_tools


class TestToolHotReloadErrorHandling:
    """Test tool hot reload error handling."""

    def test_watch_tool_with_invalid_name(self, tmp_path):
        """Test watching tool with invalid name."""
        hot_reload = ToolHotReload()

        p = tmp_path / "tool.py"
        p.write_text("# tool")
        # Watch a tool with invalid name
        hot_reload.watch_tool("", p)

        # Should handle gracefully
        assert "" in hot_reload._watched_tools

    def test_watch_tool_with_invalid_path(self):
        """Test watching tool with invalid path."""
        hot_reload = ToolHotReload()

        # Passing None should raise a TypeError
        with pytest.raises(TypeError):
            hot_reload.watch_tool("test_tool", None)

    def test_start_hot_reload_with_exception(self):
        """Test starting hot reload when exception occurs."""
        hot_reload = ToolHotReload()

        # Mock poll loop to raise exception
        with patch.object(
            hot_reload, "_poll_loop", side_effect=Exception("Poll loop failed")
        ):
            # Should handle exception gracefully
            hot_reload.start()

            # Verify thread was started
            assert hot_reload._thread is not None
        hot_reload = ToolHotReload()

        # Watch multiple tools
        tools = [
            ("tool1", Path("/test/tool1.py")),
            ("tool2", Path("/test/tool2.py")),
            ("tool3", Path("/test/tool3.py")),
        ]

        for name, path in tools:
            hot_reload.watch_tool(name, path)

        # Verify all tools are being watched
        for name, path in tools:
            assert name in hot_reload._watched_tools
            assert hot_reload._watched_tools[name]["path"] == path

    def test_hot_reload_with_conditional_watching(self):
        """Test hot reload with conditional watching."""
        hot_reload = ToolHotReload()

        # Watch tools conditionally
        for i in range(10):
            if i % 2 == 0:  # Only watch even-numbered tools
                hot_reload.watch_tool(f"tool_{i}", Path(f"/test/tool_{i}.py"))

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
        initial_tools = [
            ("tool1", Path("/test/tool1.py")),
            ("tool2", Path("/test/tool2.py")),
        ]
        for name, path in initial_tools:
            hot_reload.watch_tool(name, path)

        # Verify initial tools are being watched
        assert len(hot_reload._watched_tools) == 2

        # Add more tools dynamically
        new_tools = [
            ("tool3", Path("/test/tool3.py")),
            ("tool4", Path("/test/tool4.py")),
        ]
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
