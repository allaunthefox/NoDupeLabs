"""Test logging module functionality."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.logging_system import Logging, LoggingError, get_logger, setup_logging


class TestLoggingError:
    """Test LoggingError exception."""

    def test_logging_error(self):
        """Test LoggingError exception."""
        error = LoggingError("Test logging error")
        assert str(error) == "Test logging error"
        assert isinstance(error, Exception)


class TestLoggingSetup:
    """Test Logging setup functionality."""

    def test_setup_logging_defaults(self):
        """Test setup_logging with default parameters."""
        # Clear any existing configuration
        Logging._configured = False
        Logging._loggers.clear()

        # Test with defaults
        Logging.setup_logging()

        # Verify configuration
        assert Logging._configured is True
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1  # Console handler

    def test_setup_logging_with_file(self):
        """Test setup_logging with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            # Clear configuration
            Logging._configured = False
            Logging._loggers.clear()

            # Setup with file
            Logging.setup_logging(
                log_file=log_file,
                log_level="DEBUG",
                console_output=True
            )

            # Verify configuration
            assert Logging._configured is True
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
            assert len(root_logger.handlers) == 2  # Console + File

            # Verify file was created
            assert log_file.exists()

    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid log level."""
        with pytest.raises(LoggingError):
            Logging.setup_logging(log_level="INVALID")

    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format."""
        custom_format = "%(levelname)s: %(message)s"

        Logging._configured = False
        Logging._loggers.clear()

        Logging.setup_logging(log_format=custom_format)

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert handler.formatter._fmt == custom_format


class TestLoggingGetLogger:
    """Test Logging get_logger functionality."""

    def test_get_logger_auto_configure(self):
        """Test get_logger auto-configures when not configured."""
        # Clear configuration
        Logging._configured = False
        Logging._loggers.clear()

        logger = Logging.get_logger("test_module")

        # Should auto-configure
        assert Logging._configured is True
        assert logger.name == "test_module"

    def test_get_logger_caching(self):
        """Test get_logger caching."""
        # Clear configuration
        Logging._configured = False
        Logging._loggers.clear()

        # First call
        logger1 = Logging.get_logger("test_module")
        # Second call
        logger2 = Logging.get_logger("test_module")

        # Should return same instance
        assert logger1 is logger2
        assert len(Logging._loggers) == 1

    def test_get_logger_different_names(self):
        """Test get_logger with different names."""
        # Clear configuration
        Logging._configured = False
        Logging._loggers.clear()

        logger1 = Logging.get_logger("module1")
        logger2 = Logging.get_logger("module2")

        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert len(Logging._loggers) == 2


class TestLoggingMethods:
    """Test Logging utility methods."""

    def test_log_exception(self):
        """Test log_exception method."""
        # Setup logging
        Logging.setup_logging()

        logger = Logging.get_logger("test")
        raise ValueError("Test exception")

        # This should not raise
        Logging.log_exception(logger, "Test error", exc_info=True)

    def test_log_with_context(self):
        """Test log_with_context method."""
        # Setup logging
        Logging.setup_logging()

        logger = Logging.get_logger("test")

        # This should not raise
        Logging.log_with_context(
            logger,
            "info",
            "Test message",
            user_id=123,
            action="test"
        )

    def test_configure_module_logger(self):
        """Test configure_module_logger method."""
        # Setup logging
        Logging.setup_logging()

        logger = Logging.configure_module_logger("test_module", "DEBUG")

        assert logger.name == "test_module"
        assert logger.level == logging.DEBUG

    def test_set_log_level(self):
        """Test set_log_level method."""
        # Setup logging
        Logging.setup_logging()

        logger = Logging.get_logger("test")

        # Set different levels
        Logging.set_log_level(logger, "DEBUG")
        assert logger.level == logging.DEBUG

        Logging.set_log_level(logger, "WARNING")
        assert logger.level == logging.WARNING

    def test_set_log_level_invalid(self):
        """Test set_log_level with invalid level."""
        logger = Logging.get_logger("test")

        with pytest.raises(LoggingError):
            Logging.set_log_level(logger, "INVALID")

    def test_add_file_handler(self):
        """Test add_file_handler method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "handler_test.log"

            logger = Logging.get_logger("test")

            # Add file handler
            Logging.add_file_handler(
                logger,
                log_file,
                log_level="DEBUG",
                max_file_size=1024,
                backup_count=2
            )

            # Verify handler was added
            assert len(logger.handlers) == 1
            handler = logger.handlers[0]
            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert handler.level == logging.DEBUG

            # Verify file was created
            assert log_file.exists()


class TestLoggingConvenienceFunctions:
    """Test convenience functions."""

    def test_get_logger_convenience(self):
        """Test get_logger convenience function."""
        # Clear configuration
        Logging._configured = False
        Logging._loggers.clear()

        logger = get_logger("test_module")

        assert logger.name == "test_module"
        assert Logging._configured is True

    def test_setup_logging_convenience(self):
        """Test setup_logging convenience function."""
        # Clear configuration
        Logging._configured = False
        Logging._loggers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "convenience.log"

            setup_logging(
                log_file=log_file,
                log_level="DEBUG",
                console_output=False
            )

            assert Logging._configured is True
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
            assert len(root_logger.handlers) == 1  # Only file handler


class TestLoggingEdgeCases:
    """Test logging edge cases."""

    def test_setup_logging_twice(self):
        """Test setup_logging called twice."""
        # First setup
        Logging.setup_logging(log_level="INFO")

        # Second setup should clear existing handlers
        Logging.setup_logging(log_level="DEBUG")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1  # Only one handler

    def test_log_with_empty_context(self):
        """Test log_with_context with empty context."""
        Logging.setup_logging()
        logger = Logging.get_logger("test")

        # Should not raise
        Logging.log_with_context(logger, "info", "Test message")

    def test_add_file_handler_invalid_path(self):
        """Test add_file_handler with invalid path."""
        logger = Logging.get_logger("test")

        # This should raise an exception
        with pytest.raises(LoggingError):
            Logging.add_file_handler(logger, "/invalid/path/test.log")


class TestLoggingIntegration:
    """Test logging integration scenarios."""

    def test_complete_logging_workflow(self):
        """Test complete logging workflow."""
        # Clear any existing configuration
        Logging._configured = False
        Logging._loggers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "workflow.log"

            # Setup logging
            Logging.setup_logging(
                log_file=log_file,
                log_level="DEBUG",
                console_output=True,
                max_file_size=1024,
                backup_count=3
            )

            # Get logger
            logger = Logging.get_logger("workflow_test")

            # Test different log levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            # Test exception logging
            try:
                raise ValueError("Test exception")
            except ValueError:
                Logging.log_exception(logger, "Exception occurred")

            # Test context logging
            Logging.log_with_context(
                logger,
                "info",
                "User action",
                user_id=123,
                action="login",
                status="success"
            )

            # Test module-specific logger
            module_logger = Logging.configure_module_logger(
                "special_module", "WARNING")
            module_logger.warning("Module warning")

            # Verify file was created and has content
            assert log_file.exists()
            with open(log_file) as f:
                content = f.read()
                assert "Debug message" in content
                assert "Info message" in content
                assert "Warning message" in content
                assert "Error message" in content
                assert "Critical message" in content
                assert "Exception occurred" in content
                assert "User action" in content
                assert "Module warning" in content

    def test_logging_with_rotation(self):
        """Test logging with file rotation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "rotation_test.log"

            # Setup with small file size to trigger rotation
            Logging.setup_logging(
                log_file=log_file,
                log_level="INFO",
                console_output=False,
                max_file_size=100,  # Very small to trigger rotation
                backup_count=2
            )

            logger = Logging.get_logger("rotation_test")

            # Write enough log messages to trigger rotation
            for i in range(100):
                logger.info(f"Log message {i}: " + "x" * 50)  # Large message

            # Verify rotation files were created
            rotation_files = list(Path(temp_dir).glob("rotation_test.log.*"))
            assert len(rotation_files) > 0

            # Verify main log file still exists
            assert log_file.exists()

    def test_logging_performance(self):
        """Test logging performance with many messages."""
        import time

        Logging.setup_logging(console_output=False)

        logger = Logging.get_logger("performance_test")

        # Time 1000 log messages
        start_time = time.time()
        for i in range(1000):
            logger.info(f"Performance test message {i}")
        end_time = time.time()

        # Should complete in reasonable time
        duration = end_time - start_time
        assert duration < 1.0  # Less than 1 second for 1000 messages
