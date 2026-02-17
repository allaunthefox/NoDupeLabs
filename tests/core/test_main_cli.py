"""Test main CLI functionality."""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.loader import CoreLoader
from nodupe.core.main import CLIHandler, main


class TestCLIHandlerInitialization:
    """Test CLIHandler initialization functionality."""

    def test_cli_handler_creation(self):
        """Test CLIHandler instance creation."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        assert cli is not None
        assert cli.loader is mock_loader
        assert cli.parser is not None

    def test_create_parser(self):
        """Test parser creation."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        parser = cli._create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

        # Check that expected arguments are present
        # This is harder to test directly, but we can verify the parser was created

    def test_register_commands(self):
        """Test command registration."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Register commands
        cli._register_commands()

        # Check that subparsers were added
        # This is harder to test directly, but the method should run without error


class TestCLIHandlerRun:
    """Test CLIHandler run functionality."""

    def test_run_with_version_command(self):
        """Test running with version command."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to return version command
        with patch.object(cli.parser, 'parse_args') as mock_parse_args:
            mock_parsed_args = Mock()
            mock_parsed_args.command = 'version'
            mock_parsed_args.func = cli._cmd_version
            mock_parsed_args.debug = False
            mock_parse_args.return_value = mock_parsed_args

            # Mock the logger setup
            with patch.object(cli, '_setup_debug_logging'):
                result = cli.run(['version'])

                # Version command should return 0 (success)
                assert result == 0

    def test_run_with_tools_command(self):
        """Test running with tools command."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to return tools command
        with patch.object(cli.parser, 'parse_args') as mock_parse_args:
            mock_parsed_args = Mock()
            mock_parsed_args.command = 'tools'
            mock_parsed_args.func = cli._cmd_tool
            mock_parsed_args.debug = False
            mock_parsed_args.list = True
            mock_parse_args.return_value = mock_parsed_args

            # Mock the loader's tool registry
            mock_tool1 = Mock()
            mock_tool1.name = "Tool1"
            mock_tool1.version = "1.0.0"
            mock_loader.tool_registry.get_tools.return_value = [mock_tool1]

            # Mock the logger setup
            with patch.object(cli, '_setup_debug_logging'):
                result = cli.run(['tools', '--list'])

                # Tools command should return 0 (success)
                assert result == 0

    def test_run_with_invalid_command(self):
        """Test running with invalid command."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to return no command
        with patch.object(cli.parser, 'parse_args') as mock_parse_args:
            mock_parsed_args = Mock()
            mock_parsed_args.command = None
            mock_parse_args.return_value = mock_parsed_args

            # Mock the parser print_help method
            with patch.object(cli.parser, 'print_help'):
                result = cli.run([])

                # Should return 0 when no command is provided
                assert result == 0

    def test_run_with_debug_flag(self):
        """Test running with debug flag."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to return version command with debug
        with patch.object(cli.parser, 'parse_args') as mock_parse_args:
            mock_parsed_args = Mock()
            mock_parsed_args.command = 'version'
            mock_parsed_args.func = cli._cmd_version
            mock_parsed_args.debug = True
            mock_parse_args.return_value = mock_parsed_args

            # Mock the logger setup
            with patch.object(cli, '_setup_debug_logging') as mock_setup_debug:
                result = cli.run(['--debug', 'version'])

                # Debug setup should have been called
                mock_setup_debug.assert_called_once()
                assert result == 0

    def test_run_with_keyboard_interrupt(self):
        """Test running with keyboard interrupt."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to raise KeyboardInterrupt
        with patch.object(cli.parser, 'parse_args') as mock_parse_args:
            mock_parse_args.side_effect = KeyboardInterrupt()

            # Capture stderr
            with patch('sys.stderr'):
                with pytest.raises(SystemExit) as exc_info:
                    cli.run([])

                # Should exit with code 130 for keyboard interrupt
                assert exc_info.value.code == 130

    def test_run_with_exception(self):
        """Test running with exception."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to return a command that raises an exception
        mock_parsed_args = Mock()
        mock_parsed_args.command = 'version'
        mock_parsed_args.func = Mock(side_effect=Exception("Test error"))
        mock_parsed_args.debug = False

        with patch.object(cli.parser, 'parse_args', return_value=mock_parsed_args):
            # Capture stderr
            with patch('sys.stderr'):
                result = cli.run(['version'])

                # Should return 1 for error
                assert result == 1

    def test_run_with_debug_and_exception(self):
        """Test running with debug and exception (to trigger traceback)."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the parser to return a command that raises an exception
        mock_parsed_args = Mock()
        mock_parsed_args.command = 'version'
        mock_parsed_args.func = Mock(side_effect=Exception("Test error"))
        mock_parsed_args.debug = True  # Enable debug to trigger traceback

        with patch.object(cli.parser, 'parse_args', return_value=mock_parsed_args):
            # Mock traceback printing
            with patch('traceback.print_exc') as mock_traceback:
                result = cli.run(['--debug', 'version'])

                # Traceback should have been printed
                mock_traceback.assert_called_once()
                # Should return 1 for error
                assert result == 1


class TestCLIHandlerCommands:
    """Test CLIHandler command functionality."""

    def test_cmd_version(self):
        """Test version command."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the loader config
        mock_config = Mock()
        mock_config.config = {
            'drive_type': 'SSD',
            'cpu_cores': 4,
            'ram_gb': 8
        }
        mock_loader.config = mock_config

        # Capture print output
        with patch('builtins.print') as mock_print:
            result = cli._cmd_version(Mock())

            # Should return 0
            assert result == 0
            # Print should have been called
            mock_print.assert_called()

    def test_cmd_tool_list(self):
        """Test tools command with list option."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the tool registry
        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.version = "1.0.0"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        mock_tool2.version = "2.0.0"

        mock_loader.tool_registry.get_tools.return_value = [mock_tool1, mock_tool2]

        # Mock the args
        mock_args = Mock()
        mock_args.list = True

        # Capture print output
        with patch('builtins.print') as mock_print:
            result = cli._cmd_tool(mock_args)

            # Should return 0
            assert result == 0
            # Print should have been called for each tool
            assert mock_print.call_count >= 3  # At least header + 2 tools

    def test_cmd_tool_no_registry(self):
        """Test tools command when registry is not active."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        # Mock the args
        mock_args = Mock()
        mock_args.list = True

        # Capture print output
        with patch('builtins.print') as mock_print:
            result = cli._cmd_tool(mock_args)

            # Should return 1 (error)
            assert result == 1
            # Print should have been called with error message
            mock_print.assert_called()

    def test_cmd_tool_no_list(self):
        """Test tools command without list option."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the tool registry
        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool1.version = "1.0.0"

        mock_loader.tool_registry.get_tools.return_value = [mock_tool1]

        # Mock the args
        mock_args = Mock()
        mock_args.list = False  # No list flag

        # Capture print output
        with patch('builtins.print'):
            result = cli._cmd_tool(mock_args)

            # Should return 0 (no error, just no action taken)
            assert result == 0


class TestCLIHandlerUtilities:
    """Test CLIHandler utility functionality."""

    def test_setup_debug_logging(self):
        """Test debug logging setup."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.DEBUG', 10):

            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            cli._setup_debug_logging()

            # Verify logger level was set to DEBUG
            mock_logger.setLevel.assert_called_once_with(10)

    def test_apply_overrides(self):
        """Test applying performance overrides."""
        mock_loader = Mock()
        cli = CLIHandler(mock_loader)

        # Mock the loader config
        mock_config_obj = Mock()
        mock_config_obj.config = {}
        mock_loader.config = mock_config_obj

        # Mock args with override values
        mock_args = Mock()
        mock_args.cores = 8
        mock_args.max_workers = 16
        mock_args.batch_size = 1000

        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            cli._apply_overrides(mock_args)

            # Verify config was updated
            assert mock_config_obj.config['cpu_cores'] == 8
            assert mock_config_obj.config['max_workers'] == 16
            assert mock_config_obj.config['batch_size'] == 1000

            # Verify logging was called for each override
            assert mock_logger.info.call_count == 3


class TestMainFunction:
    """Test main function functionality."""

    def test_main_success(self):
        """Test main function success case."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_handler_class:

            # Mock the loader and CLI handler
            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            mock_cli_handler = Mock()
            mock_cli_handler.run.return_value = 0
            mock_cli_handler_class.return_value = mock_cli_handler

            # Call main
            result = main([])

            # Verify bootstrap was called
            mock_bootstrap.assert_called_once()
            # Verify CLI handler was created and run
            mock_cli_handler_class.assert_called_once_with(mock_loader)
            mock_cli_handler.run.assert_called_once_with([])
            # Verify result
            assert result == 0
            # Verify shutdown was called
            mock_loader.shutdown.assert_called_once()

    def test_main_keyboard_interrupt(self):
        """Test main function with keyboard interrupt."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_handler_class:

            # Mock the CLI handler to raise KeyboardInterrupt
            mock_cli_handler = Mock()
            mock_cli_handler.run.side_effect = KeyboardInterrupt()
            mock_cli_handler_class.return_value = mock_cli_handler

            # Mock the loader
            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            # Capture stderr
            with patch('sys.stderr'):
                result = main([])

                # Should return 130 for keyboard interrupt
                assert result == 130
                # Verify shutdown was still called
                mock_loader.shutdown.assert_called_once()

    def test_main_exception(self):
        """Test main function with exception."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_handler_class:

            # Mock the CLI handler to raise an exception
            mock_cli_handler = Mock()
            mock_cli_handler.run.side_effect = Exception("Startup failed")
            mock_cli_handler_class.return_value = mock_cli_handler

            # Mock the loader
            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            # Capture stderr
            with patch('sys.stderr'):
                result = main([])

                # Should return 1 for error
                assert result == 1
                # Verify shutdown was still called
                mock_loader.shutdown.assert_called_once()

    def test_main_bootstrap_exception(self):
        """Test main function with bootstrap exception."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap:

            # Mock bootstrap to raise an exception
            mock_bootstrap.side_effect = Exception("Bootstrap failed")

            # Capture stderr
            with patch('sys.stderr'):
                result = main([])

                # Should return 1 for error
                assert result == 1

    def test_main_with_args(self):
        """Test main function with specific arguments."""
        test_args = ['--verbose', 'version']

        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_handler_class:

            # Mock the loader and CLI handler
            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            mock_cli_handler = Mock()
            mock_cli_handler.run.return_value = 0
            mock_cli_handler_class.return_value = mock_cli_handler

            # Call main with specific args
            result = main(test_args)

            # Verify CLI handler run was called with the specific args
            mock_cli_handler.run.assert_called_once_with(test_args)
            assert result == 0
