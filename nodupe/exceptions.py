# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Custom exception hierarchy for NoDupeLabs.

Provides a structured exception hierarchy for better error handling
and more informative error messages.
"""
from pathlib import Path
from typing import Optional


class NoDupeError(Exception):
    """Base exception for all NoDupeLabs errors.

    All custom exceptions inherit from this to allow catching
    all nodupe-related errors with a single except clause.
    """

    def __init__(self, message: str, details: Optional[str] = None):
        """Initialize error.

        Args:
            message: Human-readable error message
            details: Optional additional details
        """
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """Return a human-friendly string for the error, including details if
        available.
        """
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


# Configuration Errors
class ConfigError(NoDupeError):
    """Errors raised when the application encounters invalid or missing
    configuration.

    This is the base class for configuration-related exceptions and is
    intended to be subclassed for specific error cases (eg. missing file,
    invalid value).
    """
    pass


class ConfigNotFoundError(ConfigError):
    """Raised when the requested configuration file cannot be found.

    Includes the path to the missing file in ``details`` for diagnostics.
    """

    def __init__(self, path: Path):
        """Construct a ConfigNotFoundError for a missing file path.

        Args:
            path: Path to the configuration file that was not found.
        """
        super().__init__(
            "Configuration file not found",
            details=str(path)
        )
        self.path = path


class InvalidConfigError(ConfigError):
    """Raised when a configuration key contains an invalid value.

    Carries the key, attempted value and a human-readable reason.
    """

    def __init__(self, key: str, value: str, reason: str):
        """Invalid configuration value error.

        Args:
            key: Configuration key name
            value: The invalid value
            reason: Explanation why value is invalid
        """
        super().__init__(
            f"Invalid configuration value for '{key}'",
            details=f"{value} - {reason}"
        )
        self.key = key
        self.value = value
        self.reason = reason


# Database Errors
class DatabaseError(NoDupeError):
    """Base class for errors interacting with the application's database.

    Use this as a generic catch-all for database layer problems; more
    specific subclasses exist for missing files or corruption.
    """
    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when the requested database file does not exist.

    The problematic path is included as ``details`` and on the
    exception instance as ``path``.
    """

    def __init__(self, path: Path):
        """Database file not found error.

        Args:
            path: Path to the database file that wasn't found.
        """
        super().__init__(
            "Database not found",
            details=str(path)
        )
        self.path = path


class DatabaseCorruptError(DatabaseError):
    """Raised when the database contents appear corrupted.

    The constructor accepts a `reason` describing the corruption.
    """

    def __init__(self, path: Path, reason: str):
        """Database corruption error with reason.

        Args:
            path: Path to the corrupted database
            reason: Short explanation for the corruption
        """
        super().__init__(
            "Database is corrupted",
            details=f"{path}: {reason}"
        )
        self.path = path
        self.reason = reason


# Scan Errors
class ScanError(NoDupeError):
    """Raised for problems discovered during directory scanning.

    Scan-related issues (path not found, permission denied, etc.) inherit
    from this class so they can be handled as a group when needed.
    """
    pass


class PathNotFoundError(ScanError):
    """Raised when a scan operation targets a path that does not exist.

    Includes the missing path in the exception details.
    """

    def __init__(self, path: Path):
        """Raised when a scan path is not found.

        Args:
            path: Path that could not be located during scanning
        """
        super().__init__(
            "Path not found",
            details=str(path)
        )
        self.path = path


class PermissionDeniedError(ScanError):
    """Raised when access to a scan path is denied by the OS.

    The exception instance holds the denied path for troubleshooting.
    """

    def __init__(self, path: Path):
        """Raised when permission to access `path` is denied.

        Args:
            path: Path where access was denied
        """
        super().__init__(
            "Permission denied",
            details=str(path)
        )
        self.path = path


# Apply Errors
class ApplyError(NoDupeError):
    """Errors that occur while applying a deduplication or file-move plan.

    This includes failures when moving files, writing checkpoints, or when
    rollback operations fail.
    """
    pass


class CheckpointError(ApplyError):
    """Errors related to checkpoint files used during apply/rollback.

    Carries optional path information for the affected checkpoint.
    """

    def __init__(self, message: str, path: Optional[Path] = None):
        """Raised for checkpoint-related errors during apply/rollback.

        Args:
            message: Human message describing the error
            path: Optional Path of the checkpoint file involved
        """
        super().__init__(message, details=str(path) if path else None)
        self.path = path


class RollbackError(ApplyError):
    """Raised when a rollback operation fails or completes only partially.

    The `partial_count` attribute indicates how many items were rolled
    back before the failure occurred.
    """

    def __init__(self, message: str, partial_count: int = 0):
        """Raised when a rollback operation fails or completes partially.

        Args:
            message: Human-readable message
            partial_count: Number of files that were rolled back before failure
        """
        super().__init__(message, details=f"rolled back {partial_count} files")
        self.partial_count = partial_count


# Similarity Errors
class SimilarityError(NoDupeError):
    """Problems encountered while building or querying similarity indices.

    Use this base class for general similarity/index related failures so
    callers can produce consistent error handling for all backends.
    """
    pass


class IndexNotFoundError(SimilarityError):
    """Raised when a requested similarity index file is not present.

    The exception carries the missing index file path as ``path``.
    """

    def __init__(self, path: Path):
        """Raised when a scan operation times out (stall or max idle time
        exceeded).
        """
        super().__init__(
            "Similarity index not found",
            details=str(path)
        )
        self.path = path


# AI Backend Errors
class AIBackendError(NoDupeError):
    """Errors produced by AI/ML backend integrations.

    Encapsulates backend-specific failures such as missing models, failed
    inference calls, or dependency issues.
    """
    pass


class ModelNotFoundError(AIBackendError):
    """Raised when the specified ML model file cannot be located.

    Contains the `model_name` and optionally a path where the loader
    expected to find the model.
    """

    def __init__(self, model_name: str, path: Optional[Path] = None):
        """Raised when the requested ML model file can't be found.

        Args:
            model_name: Logical name of the model
            path: Optional path where the model was expected
        """
        super().__init__(
            f"Model not found: {model_name}",
            details=str(path) if path else None
        )
        self.model_name = model_name
        self.path = path


class InferenceError(AIBackendError):
    """Raised when an AI backend inference call fails for runtime reasons.

    The `model` attribute provides an identifier of the model that failed
    to run.
    """

    def __init__(self, message: str, model: str = "unknown"):
        """Raised when an AI backend inference call fails.

        Args:
            message: Human-readable error message
            model: Optional model identifier where the error occurred
        """
        super().__init__(message, details=f"model={model}")
        self.model = model
