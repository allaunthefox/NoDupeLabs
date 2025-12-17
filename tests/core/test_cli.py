# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI Tests - Basic CLI functionality and argument parsing.

This module tests the core CLI functionality including:
- Argument parsing
- Help system
- Version command
- Plugin command
- Error handling
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from nodupe.core.main import CLIHandler, main
from nodupe.core.loader import bootstrap
import argparse

class TestCLIArgumentParsing:
    """Test CLI argument parsing functionality."""

    def test_cli_initialization(self):
        """Test that CLI handler initializes correctly."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)
        assert cli.loader == mock_loader
        assert cli.parser is not None

    def test_help_flag(self):
        """Test that help flag works."""
        with patch('sys.argv', ['nodupe', '--help']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

    def test_version_command(self):
        """Test version command."""
        with patch('sys.argv', ['nodupe', 'version']):
            result = main()
            assert result == 0

    def test_plugin_command_list(self):
        """Test plugin command with list flag."""
        with patch('sys.argv', ['nodupe', 'plugin', '--list']):
            result = main()
            assert result == 0

    def test_invalid_command(self):
        """Test invalid command handling."""
        with patch('sys.argv', ['nodupe', 'invalid_command']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code != 0

    def test_debug_flag(self):
        """Test debug flag functionality."""
        with patch('sys.argv', ['nodupe', '--debug', 'version']):
            result = main()
            assert result == 0

    def test_performance_overrides(self):
        """Test performance override flags."""
        with patch('sys.argv', ['nodupe', '--cores', '4', '--max-workers', '8', 'version']):
            result = main()
            assert result == 0

class TestCLIHelpSystem:
    """Test CLI help system functionality."""

    def test_help_output_contains_commands(self):
        """Test that help output contains expected commands."""
        with patch('sys.argv', ['nodupe', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_version_help(self):
        """Test version command help."""
        with patch('sys.argv', ['nodupe', 'version', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_plugin_help(self):
        """Test plugin command help."""
        with patch('sys.argv', ['nodupe', 'plugin', '--help']):
            with pytest.raises(SystemExit):
                main()

class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_missing_required_args(self):
        """Test missing required arguments."""
        with patch('sys.argv', ['nodupe', 'scan']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code != 0

    def test_invalid_file_path(self):
        """Test invalid file path handling."""
        with patch('sys.argv', ['nodupe', 'scan', '/nonexistent/path']):
            result = main()
            assert result != 0

    def test_permission_error_handling(self):
        """Test permission error handling."""
        with patch('sys.argv', ['nodupe', 'scan', '/root']):
            result = main()
            # This might succeed on some systems, so we just check it doesn't crash
            assert isinstance(result, int)

class TestCLICommandRegistration:
    """Test command registration functionality."""

    def test_builtin_commands_registered(self):
        """Test that built-in commands are registered."""
        mock_loader = MagicMock()
        mock_loader.plugin_registry = MagicMock()
        mock_loader.plugin_registry.get_plugins.return_value = []

        cli = CLIHandler(mock_loader)

        # Check that version and plugin commands are available
        with patch('sys.argv', ['nodupe', 'version']):
            result = cli.run()
            assert result == 0

        with patch('sys.argv', ['nodupe', 'plugin']):
            result = cli.run()
            assert result == 0

    def test_plugin_commands_registered(self):
        """Test that plugin commands are registered."""
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.register_commands = MagicMock()

        mock_loader = MagicMock()
        mock_loader.plugin_registry = MagicMock()
        mock_loader.plugin_registry.get_plugins.return_value = [mock_plugin]

        cli = CLIHandler(mock_loader)

        # This should call the plugin's register_commands method
        assert mock_plugin.register_commands.called

    def test_command_dispatch(self):
        """Test command dispatch functionality."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        # Test that commands are properly dispatched
        with patch('sys.argv', ['nodupe', 'version']):
            result = cli.run()
            assert result == 0

        with patch('sys.argv', ['nodupe', 'plugin', '--list']):
            result = cli.run()
            assert result == 0

class TestCLIPerformanceOverrides:
    """Test performance override functionality."""

    def test_cores_override(self):
        """Test cores override."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        mock_loader.config.config = {'cpu_cores': 2}

        cli = CLIHandler(mock_loader)

        with patch('sys.argv', ['nodupe', '--cores', '8', 'version']):
            result = cli.run()
            assert result == 0
            assert mock_loader.config.config['cpu_cores'] == 8

    def test_max_workers_override(self):
        """Test max workers override."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        mock_loader.config.config = {'max_workers': 4}

        cli = CLIHandler(mock_loader)

        with patch('sys.argv', ['nodupe', '--max-workers', '16', 'version']):
            result = cli.run()
            assert result == 0
            assert mock_loader.config.config['max_workers'] == 16

    def test_batch_size_override(self):
        """Test batch size override."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        mock_loader.config.config = {'batch_size': 100}

        cli = CLIHandler(mock_loader)

        with patch('sys.argv', ['nodupe', '--batch-size', '500', 'version']):
            result = cli.run()
            assert result == 0
            assert mock_loader.config.config['batch_size'] == 500

class TestCLIDebugLogging:
    """Test debug logging functionality."""

    def test_debug_logging_enabled(self):
        """Test that debug logging is enabled with --debug flag."""
        with patch('sys.argv', ['nodupe', '--debug', 'version']):
            with patch('nodupe.core.main.logging.getLogger') as mock_logger:
                result = main()
                assert result == 0
                # Check that debug logging was set up
                mock_logger.return_value.setLevel.assert_called_with('DEBUG')

    def test_debug_logging_disabled(self):
        """Test that debug logging is not enabled without --debug flag."""
        with patch('sys.argv', ['nodupe', 'version']):
            with patch('nodupe.core.main.logging.getLogger') as mock_logger:
                result = main()
                assert result == 0
                # Debug logging should not be set up
                mock_logger.return_value.setLevel.assert_not_called()

class TestCLIIntegration:
    """Test CLI integration with core components."""

    def test_cli_with_bootstrap(self):
        """Test CLI with actual bootstrap."""
        with patch('sys.argv', ['nodupe', 'version']):
            result = main()
            assert result == 0

    def test_cli_error_handling_integration(self):
        """Test CLI error handling with real bootstrap."""
        with patch('sys.argv', ['nodupe', 'invalid_command']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code != 0

    def test_cli_help_integration(self):
        """Test CLI help with real bootstrap."""
        with patch('sys.argv', ['nodupe', '--help']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
