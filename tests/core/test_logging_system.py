import logging
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nodupe.core.logging_system import Logging, get_logger


@pytest.fixture(autouse=True)
def reset_logging_state():
    # Ensure Logging class state is reset between tests
    Logging._configured = False
    Logging._loggers.clear()
    # Preserve root handlers and restore after test
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    try:
        yield
    finally:
        root.handlers[:] = original_handlers
        Logging._configured = False
        Logging._loggers.clear()


def test_setup_logging_creates_console_handler_and_sets_level():
    root = logging.getLogger()
    # ensure no handlers initially for determinism
    root.handlers.clear()

    Logging.setup_logging(log_file=None, log_level="DEBUG", console_output=True)

    assert Logging._configured is True
    assert root.level == logging.DEBUG
    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)


def test_get_logger_auto_configures_and_caches():
    # Not configured initially
    assert Logging._configured is False

    logger = Logging.get_logger("nodupe.test.logger")
    assert isinstance(logger, logging.Logger)
    assert Logging._configured is True
    assert "nodupe.test.logger" in Logging._loggers

    # Subsequent call returns same instance
    same = Logging.get_logger("nodupe.test.logger")
    assert same is logger


def test_log_exception_calls_error_with_exc_info():
    mock_logger = MagicMock()
    Logging.log_exception(mock_logger, "something bad", exc_info=True)
    mock_logger.error.assert_called_once()
    called_msg, = mock_logger.error.call_args[0]
    assert "something bad" in called_msg
    # exc_info passed as kwarg
    assert mock_logger.error.call_args.kwargs.get("exc_info") is True


def test_log_with_context_formats_message_and_calls_level_method():
    mock_logger = MagicMock()
    Logging.log_with_context(mock_logger, "info", "hello", a=1, b="x")
    mock_logger.info.assert_called_once_with("hello | a=1 b=x")


def test_configure_module_logger_sets_level():
    logger = Logging.configure_module_logger("nodupe.core.test", log_level="ERROR")
    assert logger.level == logging.ERROR


def test_set_log_level_raises_on_invalid_level():
    logger = logging.getLogger("nodupe.level.test")
    with pytest.raises(Exception):
        # invalid level should raise LoggingError
        Logging.set_log_level(logger, "NOT_A_LEVEL")


def test_add_file_handler_creates_log_file_and_attaches_handler(tmp_path: Path):
    logger = logging.getLogger("nodupe.file.test")
    log_path = tmp_path / "logs" / "app.log"

    # Ensure parent dir does not exist
    assert not log_path.parent.exists()

    Logging.add_file_handler(logger, log_path, log_level="DEBUG", max_file_size=1024, backup_count=1)

    # Directory should have been created
    assert log_path.parent.exists()

    handlers = [h for h in logger.handlers if h.__class__.__name__ == "RotatingFileHandler"]
    assert handlers, "RotatingFileHandler was not attached to the logger"
    # verify handler filename matches
    assert any(getattr(h, "baseFilename", None) == str(log_path) for h in handlers)


def test_get_logger_convenience_function_returns_logger():
    lg = get_logger("nodupe.short.get")
    assert isinstance(lg, logging.Logger)


def test_setup_logging_raises_on_invalid_level():
    # invalid level should cause a LoggingError from setup_logging
    with pytest.raises(Exception):
        Logging.setup_logging(log_level="NOT_A_REAL_LEVEL")
