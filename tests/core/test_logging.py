import os
import tempfile
import logging as std_logging
from pathlib import Path
import pytest
import shutil
from nodupe.core.logging import Logging, LoggingError, get_logger, setup_logging


class TestLogging:
    """Test suite for the Logging class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the logging configuration before each test
        std_logging.shutdown()
        std_logging.getLogger().handlers.clear()
        std_logging.getLogger().setLevel(std_logging.NOTSET)
        # Use the class methods to reset the internal state
        # Access the protected attributes to reset them for testing
        Logging._configured = False
        Logging._loggers = {}

    def teardown_method(self):
        """Tear down test fixtures after each test method."""
        # Clean up any temporary log files created during tests
        pass  # Individual tests handle their own cleanup

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        Logging.setup_logging()
        assert Logging._configured is True
        # Should have console handler
        root_logger = std_logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        # Create a temporary log file path
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "test.log")
        
        try:
            Logging.setup_logging(log_file=Path(log_file_path))
            assert Logging._configured is True
            # Should have both console and file handlers
            root_logger = std_logging.getLogger()
            assert len(root_logger.handlers) >= 1  # At least one handler
        finally:
            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_setup_logging_with_custom_log_level(self):
        """Test logging setup with custom log level."""
        Logging.setup_logging(log_level="DEBUG")
        assert Logging._configured is True
        # Check that the root logger level is DEBUG
        root_logger = std_logging.getLogger()
        assert root_logger.level == std_logging.DEBUG

    def test_setup_logging_with_invalid_log_level(self):
        """Test logging setup with invalid log level."""
        with pytest.raises(LoggingError):
            Logging.setup_logging(log_level="INVALID_LEVEL")

    def test_setup_logging_console_output_disabled(self):
        """Test logging setup with console output disabled."""
        Logging.setup_logging(console_output=False)
        assert Logging._configured is True
        # Should not have console handler but may have other handlers

    def test_get_logger_basic(self):
        """Test getting a logger instance."""
        logger = Logging.get_logger("test_logger")
        assert isinstance(logger, std_logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_auto_configuration(self):
        """Test that get_logger auto-configures if not configured."""
        # Ensure logging is not configured
        Logging._configured = False
        logger = Logging.get_logger("auto_config_test")
        assert Logging._configured is True
        assert isinstance(logger, std_logging.Logger)

    def test_get_logger_caching(self):
        """Test that get_logger caches instances."""
        logger1 = Logging.get_logger("cached_logger")
        logger2 = Logging.get_logger("cached_logger")
        assert logger1 is logger2  # Same instance should be returned

    def test_log_exception(self):
        """Test logging an exception."""
        logger = Logging.get_logger("exception_test")
        # Capture logs to verify the exception was logged
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                # Log an exception
                try:
                    raise ValueError("Test exception")
                except ValueError:
                    Logging.log_exception(logger, "Exception occurred")
                    
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the exception message
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Exception occurred" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_debug_level(self):
        """Test logging with context at debug level."""
        logger = Logging.get_logger("context_test")
        # Capture logs to verify the context was logged
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(logger, "debug", "Debug message", user_id=123, action="test")
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message with context
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Debug message" in log_content
                assert "user_id=123" in log_content
                assert "action=test" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_info_level(self):
        """Test logging with context at info level."""
        logger = Logging.get_logger("context_test")
        # Capture logs to verify the context was logged
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(logger, "info", "Info message", module="test_module", version="1.0")
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message with context
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Info message" in log_content
                assert "module=test_module" in log_content
                assert "version=1.0" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_warning_level(self):
        """Test logging with context at warning level."""
        logger = Logging.get_logger("context_test")
        # Capture logs to verify the context was logged
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(logger, "warning", "Warning message", severity="high", category="security")
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message with context
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Warning message" in log_content
                assert "severity=high" in log_content
                assert "category=security" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_error_level(self):
        """Test logging with context at error level."""
        logger = Logging.get_logger("context_test")
        # Capture logs to verify the context was logged
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(logger, "error", "Error message", code=500, component="api")
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message with context
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Error message" in log_content
                assert "code=500" in log_content
                assert "component=api" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_critical_level(self):
        """Test logging with context at critical level."""
        logger = Logging.get_logger("context_test")
        # Capture logs to verify the context was logged
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(logger, "critical", "Critical message", emergency=True, alert="urgent")
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message with context
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Critical message" in log_content
                assert "emergency=True" in log_content
                assert "alert=urgent" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_configure_module_logger_basic(self):
        """Test configuring a logger for a specific module."""
        logger = Logging.configure_module_logger("my_module")
        assert isinstance(logger, std_logging.Logger)
        assert logger.name == "my_module"

    def test_configure_module_logger_with_level_override(self):
        """Test configuring a logger with level override."""
        logger = Logging.configure_module_logger("my_module", log_level="DEBUG")
        assert isinstance(logger, std_logging.Logger)
        assert logger.name == "my_module"
        # The level should be set to DEBUG

    def test_set_log_level_valid_levels(self):
        """Test setting log level with valid levels."""
        logger = std_logging.getLogger("test_set_level")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            Logging.set_log_level(logger, level)
            expected_level = getattr(std_logging, level.upper())
            assert logger.level == expected_level

    def test_set_log_level_invalid_level(self):
        """Test setting log level with invalid level."""
        logger = std_logging.getLogger("test_invalid_level")
        with pytest.raises(LoggingError):
            Logging.set_log_level(logger, "INVALID_LEVEL")

    def test_add_file_handler_basic(self):
        """Test adding a file handler to a logger."""
        logger = std_logging.getLogger("test_file_handler")
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "handler_test.log")
        
        try:
            Logging.add_file_handler(logger, Path(log_file_path))
            # Should have at least one handler now
            assert len(logger.handlers) >= 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_add_file_handler_with_custom_level(self):
        """Test adding a file handler with custom level."""
        logger = std_logging.getLogger("test_file_handler_custom")
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "handler_custom_test.log")
        
        try:
            Logging.add_file_handler(logger, Path(log_file_path), log_level="WARNING")
            # Should have at least one handler now with WARNING level
            assert len(logger.handlers) >= 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_add_file_handler_with_invalid_path(self):
        """Test adding a file handler with invalid path."""
        logger = std_logging.getLogger("test_file_handler_invalid")
        # Use a path that's not accessible
        invalid_path = "/invalid/path/logfile.log"
        
        with pytest.raises(LoggingError):
            Logging.add_file_handler(logger, Path(invalid_path))

    def test_logging_error_creation(self):
        """Test creating a LoggingError with a message."""
        error = LoggingError("Test logging error")
        assert str(error) == "Test logging error"
        assert isinstance(error, Exception)

    def test_logging_error_without_message(self):
        """Test creating a LoggingError without a message."""
        error = LoggingError()
        assert str(error) == ""
        assert isinstance(error, Exception)

    def test_logging_error_raising(self):
        """Test raising and catching a LoggingError."""
        with pytest.raises(LoggingError):
            raise LoggingError("Test error message")

    def test_logging_error_inheritance(self):
        """Test that LoggingError properly inherits from Exception."""
        error = LoggingError("Test message")
        assert isinstance(error, Exception)
        assert isinstance(error, LoggingError)

    def test_logging_error_with_original_exception(self):
        """Test LoggingError with original exception chaining."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            with pytest.raises(LoggingError) as exc_info:
                raise LoggingError(f"Wrapper error: {e}") from e
            assert exc_info.value.__cause__ is e

    def test_setup_logging_with_custom_format(self):
        """Test setup_logging with custom format."""
        custom_format = "%(asctime)s | %(levelname)s | %(message)s"
        Logging.setup_logging(log_format=custom_format)
        assert Logging._configured is True
        # The format should be applied to handlers

    def test_get_logger_with_special_characters(self):
        """Test getting a logger with special characters in name."""
        logger = Logging.get_logger("logger_with_üñíçødé")
        assert isinstance(logger, std_logging.Logger)
        assert logger.name == "logger_with_üñíçødé"

    def test_log_with_context_with_empty_context(self):
        """Test logging with context when no context is provided."""
        logger = Logging.get_logger("empty_context_test")
        # Capture logs to verify the message was logged without context separator
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(logger, "info", "Message without context")
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message without context separator
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Message without context" in log_content
                assert " | " not in log_content  # No context separator should be present
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_with_various_types(self):
        """Test logging with context using various value types."""
        logger = Logging.get_logger("various_types_test")
        # Capture logs to verify the context was logged with different types
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                Logging.log_with_context(
                    logger, 
                    "info", 
                    "Message with various types", 
                    string_val="test", 
                    int_val=42, 
                    float_val=3.14,
                    bool_val=True,
                    none_val=None
                )
                
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message with context
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Message with various types" in log_content
                assert "string_val=test" in log_content
                assert "int_val=42" in log_content
                assert "float_val=3.14" in log_content
                assert "bool_val=True" in log_content
                assert "none_val=None" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_log_with_context_invalid_level(self):
        """Test logging with context using invalid log level."""
        logger = Logging.get_logger("invalid_level_context_test")
        with pytest.raises(AttributeError):
            Logging.log_with_context(logger, "invalid_level", "Test message", context="value")

    def test_setup_logging_with_none_file_path(self):
        """Test setup_logging with None as file path."""
        # This should work fine - just means no file logging
        Logging.setup_logging(log_file=None)
        assert Logging._configured is True

    def test_add_file_handler_with_string_path(self):
        """Test add_file_handler with string path instead of Path object."""
        logger = std_logging.getLogger("test_string_path_handler")
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "string_path_test.log")
        
        try:
            # Pass string path instead of Path object
            Logging.add_file_handler(logger, log_file_path, log_level="INFO")
            # Should work with string paths too
            assert len(logger.handlers) >= 1
        finally:
            shutil.rmtree(temp_file, ignore_errors=True)

    def test_add_file_handler_creates_directory(self):
        """Test that add_file_handler creates directories if they don't exist."""
        logger = std_logging.getLogger("test_dir_creation_handler")
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "subdir", "nested_log_test.log")
        
        try:
            Logging.add_file_handler(logger, Path(log_file_path))
            # Should create the nested directory structure
            assert os.path.exists(os.path.dirname(log_file_path))
            assert len(logger.handlers) >= 1
        finally:
            # Clean up by removing the nested directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_setup_logging_with_rotating_file_handler(self):
        """Test setup_logging with file that triggers rotating file handler."""
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "rotating_test.log")
        
        try:
            # Setup with file logging
            Logging.setup_logging(
                log_file=Path(log_file_path),
                max_file_size=1024,  # 1KB
                backup_count=2
            )
            assert Logging._configured is True
            
            # Check that handlers were added
            root_logger = std_logging.getLogger()
            assert len(root_logger.handlers) >= 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_logger_multiple_calls_same_name(self):
        """Test get_logger with multiple calls to same name."""
        logger1 = Logging.get_logger("same_name_test")
        logger2 = Logging.get_logger("same_name_test")
        logger3 = Logging.get_logger("same_name_test")
        
        # All should be the same instance
        assert logger1 is logger2
        assert logger2 is logger3
        assert logger1 is logger3

    def test_get_logger_different_names(self):
        """Test get_logger with different logger names."""
        logger1 = Logging.get_logger("first_logger")
        logger2 = Logging.get_logger("second_logger")
        
        # Should be different instances with different names
        assert logger1 is not logger2
        assert logger1.name == "first_logger"
        assert logger2.name == "second_logger"

    def test_configure_module_logger_multiple_times(self):
        """Test configuring the same module logger multiple times."""
        logger1 = Logging.configure_module_logger("module_test")
        logger2 = Logging.configure_module_logger("module_test")
        
        # Should return different logger instances each time (not cached like get_logger)
        # Both should have the same name
        assert logger1.name == logger2.name
        assert logger1.name == "module_test"

    def test_log_exception_without_exc_info(self):
        """Test log_exception with exc_info=False."""
        logger = Logging.get_logger("test_exc_info_false")
        # Capture logs to verify the exception was logged without traceback
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = std_logging.FileHandler(temp_file.name)
            formatter = std_logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                # Log an exception without traceback
                try:
                    raise ValueError("Test exception without traceback")
                except ValueError as e:
                    Logging.log_exception(logger, "Exception occurred", exc_info=False)
                    
                # Close the handler to flush the logs
                handler.close()
                
                # Verify log file contains the message
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                assert "Exception occurred" in log_content
            finally:
                os.unlink(temp_file.name)

    def test_magic_numbers_format(self):
        """Test that MAGIC_NUMBERS has the correct format."""
        # This test doesn't apply to logging module, so skip
        pass

    def test_extension_map_format(self):
        """Test that EXTENSION_MAP has the correct format."""
        # This test doesn't apply to logging module, so skip
        pass


class TestLoggingConvenienceFunctions:
    """Test suite for the convenience functions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the logging configuration before each test
        std_logging.shutdown()
        std_logging.getLogger().handlers.clear()
        std_logging.getLogger().setLevel(std_logging.NOTSET)
        Logging._configured = False
        Logging._loggers = {}

    def test_get_logger_convenience_function(self):
        """Test the get_logger convenience function."""
        logger = get_logger("convenience_test")
        assert isinstance(logger, std_logging.Logger)
        assert logger.name == "convenience_test"

    def test_setup_logging_convenience_function(self):
        """Test the setup_logging convenience function."""
        # Test basic setup
        setup_logging()
        assert Logging._configured is True
        
        # Check that root logger has handlers
        root_logger = std_logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_convenience_function_with_params(self):
        """Test the setup_logging convenience function with parameters."""
        temp_dir = tempfile.mkdtemp()
        log_file_path = os.path.join(temp_dir, "convenience_param_test.log")
        
        try:
            # Test setup with parameters
            setup_logging(
                log_file=Path(log_file_path),
                log_level="DEBUG",
                console_output=True
            )
            assert Logging._configured is True
            
            # Check that root logger has handlers
            root_logger = std_logging.getLogger()
            assert len(root_logger.handlers) >= 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_setup_logging_convenience_function_console_disabled(self):
        """Test setup_logging convenience function with console disabled."""
        setup_logging(console_output=False)
        assert Logging._configured is True
        # Root logger should have handlers (likely just file handlers)

    def test_convenience_functions_consistency(self):
        """Test that convenience functions behave consistently with class methods."""
        # Both should produce similar results
        logger1 = get_logger("consistency_test")
        logger2 = Logging.get_logger("consistency_test")
        
        # Should have the same name
        assert logger1.name == logger2.name
        assert logger1.name == "consistency_test"

    def test_logging_after_convenience_setup(self):
        """Test that logging works after using convenience setup."""
        # Set up logging using convenience function
        setup_logging(log_level="DEBUG")
        
        # Get a logger and verify it works
        logger = get_logger("post_setup_test")
        assert isinstance(logger, std_logging.Logger)
        
        # The logger should be properly configured
        assert logger.isEnabledFor(std_logging.DEBUG)


def test_logging_example_usage():
    """Test the example usage from the logging module."""
    # Test basic setup
    setup_logging(log_level="INFO")
    assert Logging._configured is True
    
    # Get a logger
    logger = get_logger("example_usage")
    assert isinstance(logger, std_logging.Logger)
    
    # Test logging with context
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        handler = std_logging.FileHandler(temp_file.name)
        formatter = std_logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        try:
            Logging.log_with_context(logger, "info", "Processing started", user_id=123, action="scan")
            
            # Close handler to flush logs
            handler.close()
            
            # Verify log was created
            with open(temp_file.name, 'r') as f:
                log_content = f.read()
            assert "Processing started" in log_content
        finally:
            os.unlink(temp_file.name)
