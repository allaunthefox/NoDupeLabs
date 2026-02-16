"""Logging Module.

Structured logging utilities using standard library only.

Key Features:
    - Structured logging with configurable levels
    - File and console output
    - Log rotation support
    - Contextual logging
    - Standard library only (no external dependencies)

Dependencies:
    - logging (standard library)
    - logging.handlers (standard library)
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import sys


class LoggingError(Exception):
    """Logging configuration error"""


class Logging:
    """Handle structured logging.

    Provides a centralized logging system with file rotation,
    configurable log levels, and both file and console output.
    """

    _loggers: Dict[str, logging.Logger] = {}
    _configured: bool = False

    @classmethod
    def setup_logging(
        cls,
        log_file: Optional[Path] = None,
        log_level: str = "INFO",
        console_output: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_format: Optional[str] = None
    ) -> None:
        """Set up logging configuration.

        Args:
            log_file: Path to log file (None = no file logging)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console output
            max_file_size: Maximum log file size in bytes before rotation
            backup_count: Number of backup log files to keep
            log_format: Custom log format string

        Raises:
            LoggingError: If logging setup fails
        """
        try:
            # Validate log level
            numeric_level = getattr(logging, log_level.upper(), None)
            if not isinstance(numeric_level, int):
                raise LoggingError(f"Invalid log level: {log_level}")

            # Set default log format if not provided
            if log_format is None:
                log_format = (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(filename)s:%(lineno)d - %(message)s"
                )

            formatter = logging.Formatter(log_format)

            # Get root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(numeric_level)

            # Remove existing handlers
            root_logger.handlers.clear()

            # Add console handler if enabled
            if console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(numeric_level)
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)

            # Add file handler if log file specified
            if log_file is not None:
                # Convert to Path if string
                if isinstance(log_file, str):
                    log_file = Path(log_file)

                # Create log directory if it doesn't exist
                log_file.parent.mkdir(parents=True, exist_ok=True)

                # Create rotating file handler
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=str(log_file),
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(numeric_level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)

            cls._configured = True

        except Exception as e:
            raise LoggingError(f"Failed to setup logging: {e}") from e

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Logger name (typically __name__ of the module)

        Returns:
            Logger instance

        Raises:
            LoggingError: If logging not configured
        """
        # Auto-configure with defaults if not configured
        if not cls._configured:
            cls.setup_logging()

        # Return cached logger if exists
        if name in cls._loggers:
            return cls._loggers[name]

        # Create and cache new logger
        logger = logging.getLogger(name)
        cls._loggers[name] = logger
        return logger

    @staticmethod
    def log_exception(
        logger: logging.Logger,
        message: str,
        exc_info: bool = True
    ) -> None:
        """Log an exception with full traceback.

        Args:
            logger: Logger instance
            message: Error message
            exc_info: Include exception info in log
        """
        logger.error(message, exc_info=exc_info)

    @staticmethod
    def log_with_context(
        logger: logging.Logger,
        level: str,
        message: str,
        **context: Any
    ) -> None:
        """Log message with additional context.

        Args:
            logger: Logger instance
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **context: Additional context key-value pairs
        """
        # Format context
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        full_message = f"{message} | {context_str}" if context else message

        # Log at appropriate level
        log_method = getattr(logger, level.lower())
        log_method(full_message)

    @staticmethod
    def configure_module_logger(
        module_name: str,
        log_level: Optional[str] = None
    ) -> logging.Logger:
        """Configure logger for specific module.

        Args:
            module_name: Module name
            log_level: Override log level for this module

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(module_name)

        if log_level is not None:
            numeric_level = getattr(logging, log_level.upper(), logging.INFO)
            logger.setLevel(numeric_level)

        return logger

    @staticmethod
    def set_log_level(logger: logging.Logger, log_level: str) -> None:
        """Set log level for a logger.

        Args:
            logger: Logger instance
            log_level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Raises:
            LoggingError: If log level is invalid
        """
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise LoggingError(f"Invalid log level: {log_level}")

        logger.setLevel(numeric_level)

    @staticmethod
    def add_file_handler(
        logger: logging.Logger,
        log_file: Path,
        log_level: str = "INFO",
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ) -> None:
        """Add file handler to existing logger.

        Args:
            logger: Logger instance
            log_file: Path to log file
            log_level: Log level for this handler
            max_file_size: Maximum file size before rotation
            backup_count: Number of backup files to keep

        Raises:
            LoggingError: If handler cannot be added
        """
        try:
            # Convert to Path if string
            if isinstance(log_file, str):
                log_file = Path(log_file)

            # Create log directory
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Get numeric log level
            numeric_level = getattr(logging, log_level.upper(), logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )

            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)

            # Add handler to logger
            logger.addHandler(file_handler)

        except Exception as e:
            raise LoggingError(f"Failed to add file handler: {e}") from e


# Convenience functions for quick logging setup
def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return Logging.get_logger(name)


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    console_output: bool = True
) -> None:
    """Convenience function to setup logging.

    Args:
        log_file: Path to log file
        log_level: Logging level
        console_output: Enable console output
    """
    Logging.setup_logging(
        log_file=log_file,
        log_level=log_level,
        console_output=console_output
    )
