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
        super().__init__(
            "Configuration file not found",
            details=str(path)
        )
        self.path = path


class InvalidConfigError(ConfigError):
    """Invalid configuration value."""

    def __init__(self, key: str, value: str, reason: str):
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
        super().__init__(
            "Database not found",
            details=str(path)
        )
        self.path = path


class DatabaseCorruptError(DatabaseError):
    """Database is corrupted."""

    def __init__(self, path: Path, reason: str):
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
        super().__init__(
            "Path not found",
            details=str(path)
        )
        self.path = path


class PermissionDeniedError(ScanError):
    """Permission denied when accessing path."""

    def __init__(self, path: Path):
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
        super().__init__(message, details=str(path) if path else None)
        self.path = path


class RollbackError(ApplyError):
    """Rollback operation failed."""

    def __init__(self, message: str, partial_count: int = 0):
        super().__init__(message, details=f"rolled back {partial_count} files")
        self.partial_count = partial_count


# Similarity Errors
class SimilarityError(NoDupeError):
    """Similarity search errors."""
    pass


class IndexNotFoundError(SimilarityError):
    """Similarity index not found."""

    def __init__(self, path: Path):
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
        super().__init__(
            f"Model not found: {model_name}",
            details=str(path) if path else None
        )
        self.model_name = model_name
        self.path = path


class InferenceError(AIBackendError):
    """Error during ML inference."""

    def __init__(self, message: str, model: str = "unknown"):
        super().__init__(message, details=f"model={model}")
        self.model = model
