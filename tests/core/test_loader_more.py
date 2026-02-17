import pytest
from unittest.mock import Mock, MagicMock, patch

from nodupe.core.loader import CoreLoader


def test_load_single_tool_handles_missing_tool_class():
    loader = CoreLoader()

    # inject a mock tool_loader that returns None for load_tool_from_file
    loader.tool_loader = Mock()
    loader.tool_loader.load_tool_from_file.return_value = None
    loader.tool_loader.instantiate_tool.return_value = None
    loader.hot_reload = Mock()

    fake_tool_info = Mock()
    fake_tool_info.name = "no_tool"
    fake_tool_info.path = "/nonexistent/path.py"

    # Should not raise and should simply skip
    loader._load_single_tool(fake_tool_info)
    loader.tool_loader.load_tool_from_file.assert_called()


def test_load_single_tool_instantiation_failure_logged():
    loader = CoreLoader()

    # tool_loader.load_tool_from_file returns a class-like object
    loader.tool_loader = Mock()
    loader.tool_loader.load_tool_from_file.return_value = object
    # instantiate_tool raises
    loader.tool_loader.instantiate_tool.side_effect = Exception("boom")
    loader.hot_reload = Mock()

    fake_tool_info = Mock()
    fake_tool_info.name = "broken"
    fake_tool_info.path = "tools/broken.py"

    with patch.object(loader, "logger") as mock_logger:
        mock_logger.exception = MagicMock()
        # Should not propagate exception
        loader._load_single_tool(fake_tool_info)
        mock_logger.exception.assert_called()


def test_initialize_skips_database_when_get_connection_fails():
    loader = CoreLoader()

    with (
        patch("nodupe.core.loader.load_config") as mock_load_config,
        patch.object(loader, "_apply_platform_autoconfig") as mock_autoconfig,
        patch("nodupe.core.loader.ToolRegistry"),
        patch("nodupe.core.loader.create_tool_loader"),
        patch("nodupe.core.loader.create_tool_discovery"),
        patch("nodupe.core.loader.create_lifecycle_manager"),
        patch("nodupe.core.loader.ToolHotReload"),
        patch("nodupe.core.loader.get_connection") as mock_db,
        patch("nodupe.core.loader.logging") as mock_logging,
    ):
        mock_config = Mock()
        mock_config.config = {}
        mock_load_config.return_value = mock_config
        mock_autoconfig.return_value = {}

        # Simulate get_connection raising during initialization
        mock_db.side_effect = Exception("db fail")

        # Should not raise from initialize
        loader.initialize()

        # database attribute should remain None (initialization skipped)
        assert loader.database is None
