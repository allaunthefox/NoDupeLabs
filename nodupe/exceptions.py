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
        """Return a human-friendly string for the error, including details if available."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


# Configuration Errors
class ConfigError(NoDupeError):
    """Configuration-related errors."""
    pass


class ConfigNotFoundError(ConfigError):
    """Configuration file not found."""

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
    """Invalid configuration value."""

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
    """Database-related errors."""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Database file not found."""

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
    """Database is corrupted."""

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
    """Scanning-related errors."""
    pass


class PathNotFoundError(ScanError):
    """Scan path not found."""

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
    """Permission denied when accessing path."""

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
    """Apply/move operation errors."""
    pass


class CheckpointError(ApplyError):
    """Checkpoint file error."""

    def __init__(self, message: str, path: Optional[Path] = None):
        """Raised for checkpoint-related errors during apply/rollback.

        Args:
            message: Human message describing the error
            path: Optional Path of the checkpoint file involved
        """
        super().__init__(message, details=str(path) if path else None)
        self.path = path


class RollbackError(ApplyError):
    """Rollback operation failed."""

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
    """Similarity search errors."""
    pass


class IndexNotFoundError(SimilarityError):
    """Similarity index not found."""

    def __init__(self, path: Path):
        """Raised when a similarity index file is not found.

        Args:
            path: Path to the expected index location
        """
        super().__init__(
            "Similarity index not found",
            details=str(path)
        )
        self.path = path


# AI Backend Errors
class AIBackendError(NoDupeError):
    """AI backend errors."""
    pass


class ModelNotFoundError(AIBackendError):
    """ML model file not found."""

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
    """Error during ML inference."""

    def __init__(self, message: str, model: str = "unknown"):
        """Raised when an AI backend inference call fails.

        Args:
            message: Human-readable error message
            model: Optional model identifier where the error occurred
        """
        super().__init__(message, details=f"model={model}")
        self.model = model
