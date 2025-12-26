"""
Test suite for nodupe.core.main module
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
from nodupe.core.main import main, CLIHandler


class TestCLIHandler:
    """Test cases for the CLIHandler class"""
    
    def test_cli_handler_initialization(self):
        """Test CLIHandler initialization"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        assert cli_handler is not None
        assert hasattr(cli_handler, 'loader')
        assert hasattr(cli_handler, 'parser')
        assert cli_handler.loader == mock_loader
    
    def test_cli_handler_run_method_exists(self):
        """Test that CLIHandler has a run method"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        assert hasattr(cli_handler, 'run')
        assert callable(getattr(cli_handler, 'run'))
    
    def test_cli_handler__create_parser_method_exists(self):
        """Test that CLIHandler has a _create_parser method"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        assert hasattr(cli_handler, '_create_parser')
        assert callable(getattr(cli_handler, '_create_parser'))
    
    def test_cli_handler__register_commands_method_exists(self):
        """Test that CLIHandler has a _register_commands method"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        assert hasattr(cli_handler, '_register_commands')
        assert callable(getattr(cli_handler, '_register_commands'))
    
    def test_cli_handler__cmd_version_method_exists(self):
        """Test that CLIHandler has a _cmd_version method"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        assert hasattr(cli_handler, '_cmd_version')
        assert callable(getattr(cli_handler, '_cmd_version'))
    
    def test_cli_handler__cmd_plugin_method_exists(self):
        """Test that CLIHandler has a _cmd_plugin method"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        assert hasattr(cli_handler, '_cmd_plugin')
        assert callable(getattr(cli_handler, '_cmd_plugin'))
    
    def test_cli_handler_run_method_with_args(self):
        """Test CLIHandler run method with arguments"""
        mock_loader = MagicMock()
        cli_handler = CLIHandler(mock_loader)
        
        # Mock the parser and its methods
        mock_parser = MagicMock()
        mock_parsed_args = MagicMock()
        mock_parser.parse_args.return_value = mock_parsed_args
        cli_handler.parser = mock_parser
        
        # Set up the parsed args
        mock_parsed_args.debug = False
        mock_parsed_args.func = None
        
        result = cli_handler.run(['--help'])
        
        # Check that parse_args was called with the provided args
        mock_parser.parse_args.assert_called_once_with(['--help'])
        # Check that the result is an integer (exit code)
        assert isinstance(result, int)


@patch('nodupe.core.main.bootstrap')
def test_main_function_with_args(mock_bootstrap):
    """Test main function with command line arguments"""
    # Mock the loader returned by bootstrap
    mock_loader = MagicMock()
    mock_bootstrap.return_value = mock_loader
    
    # Mock CLIHandler and its run method
    with patch('nodupe.core.main.CLIHandler') as mock_cli_handler_class:
        mock_cli_instance = MagicMock()
        mock_cli_handler_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0
        
        # Test with some command line arguments
        test_args = ['nodupe', '--help']
        
        with patch.object(sys, 'argv', test_args):
            result = main(['--help'])
            
            # Verify bootstrap was called
            mock_bootstrap.assert_called_once()
            # Verify CLIHandler was instantiated with the loader
            mock_cli_handler_class.assert_called_once_with(mock_loader)
            # Verify the CLIHandler's run method was called
            mock_cli_instance.run.assert_called_once_with(['--help'])
            # Verify the result
            assert result == 0


@patch('nodupe.core.main.bootstrap')
def test_main_function_without_args(mock_bootstrap):
    """Test main function without additional command line arguments"""
    # Mock the loader returned by bootstrap
    mock_loader = MagicMock()
    mock_bootstrap.return_value = mock_loader
    
    # Mock CLIHandler and its run method
    with patch('nodupe.core.main.CLIHandler') as mock_cli_handler_class:
        mock_cli_instance = MagicMock()
        mock_cli_handler_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0
        
        # Test with no additional arguments
        result = main()
        
        # Verify bootstrap was called
        mock_bootstrap.assert_called_once()
        # Verify CLIHandler was instantiated with the loader
        mock_cli_handler_class.assert_called_once_with(mock_loader)
        # Verify the CLIHandler's run method was called with None (default)
        mock_cli_instance.run.assert_called_once_with(None)
        # Verify the result
        assert result == 0


def test_main_function_imports():
    """Test that main function can be imported and is callable"""
    from nodupe.core.main import main
    assert callable(main)


def test_main_function_type_annotations():
    """Test that main function has proper type annotations if present"""
    import inspect
    from nodupe.core.main import main
    sig = inspect.signature(main)
    # Check that the function signature is as expected
    # main(args: Optional[List[str]] = None) -> int
    assert len(sig.parameters) == 1
    param = list(sig.parameters.values())[0]
    assert param.name == 'args'
    assert sig.return_annotation.__name__ == 'int' if hasattr(sig.return_annotation, '__name__') else sig.return_annotation == int


def test_cli_handler_safe_get_plugins_with_mock():
    """Test the _safe_get_plugins method of CLIHandler with mock"""
    mock_loader = MagicMock()
    cli_handler = CLIHandler(mock_loader)
    
    # Test with no plugin registry
    cli_handler.loader.plugin_registry = None
    result = cli_handler._safe_get_plugins()
    assert result == []
    
    # Test with plugin registry that has get_plugins method
    mock_registry = MagicMock()
    mock_registry.get_plugins.return_value = ['plugin1', 'plugin2']
    cli_handler.loader.plugin_registry = mock_registry
    result = cli_handler._safe_get_plugins()
    assert result == ['plugin1', 'plugin2']
    mock_registry.get_plugins.assert_called_once()


def test_cli_handler_apply_overrides():
    """Test the _apply_overrides method of CLIHandler"""
    mock_loader = MagicMock()
    cli_handler = CLIHandler(mock_loader)
    
    # Mock the config object
    mock_config = MagicMock()
    mock_config.config = {}
    cli_handler.loader.config = mock_config
    
    # Create mock args with override values
    mock_args = MagicMock()
    mock_args.cores = 4
    mock_args.max_workers = 8
    mock_args.batch_size = 16
    
    cli_handler._apply_overrides(mock_args)
    
    # Check that the config was updated
    assert mock_config.config['cpu_cores'] == 4
    assert mock_config.config['max_workers'] == 8
    assert mock_config.config['batch_size'] == 16


def test_cli_handler_setup_debug_logging():
    """Test the _setup_debug_logging method of CLIHandler"""
    mock_loader = MagicMock()
    cli_handler = CLIHandler(mock_loader)
    
    # Mock logging
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        cli_handler._setup_debug_logging()
        
        mock_logger.setLevel.assert_called_once()
        # Verify that DEBUG level was set
        from logging import DEBUG
        mock_logger.setLevel.assert_called_with(DEBUG)
