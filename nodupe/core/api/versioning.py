# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""API Versioning Module.

Provides API versioning functionality with support for multiple API versions
and version-aware request handling.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class VersionedFunction:
    """Wrapper for a versioned function."""
    func: Callable[..., Any]
    version: str
    deprecated: bool = False
    deprecation_message: Optional[str] = None


class APIVersion:
    """API Version Manager.
    
    Manages API versions and provides version-aware routing for endpoints.
    Supports multiple API versions with deprecation warnings.
    """
    
    def __init__(self, default_version: str = "v1") -> None:
        """Initialize API version manager."""
        self.current_version: str = default_version
        self.supported_versions: Set[str] = {default_version}
        self.versioned_functions: Dict[str, Dict[str, VersionedFunction]] = {}
        self._deprecated_versions: Dict[str, str] = {}
    
    def register_version(self, version: str) -> None:
        """Register a new API version."""
        self.supported_versions.add(version)
    
    def set_current_version(self, version: str) -> None:
        """Set the current/default API version."""
        if version not in self.supported_versions:
            raise ValueError(f"Version {version} not registered.")
        self.current_version = version
    
    def deprecate_version(self, version: str, deprecated_by: Optional[str] = None) -> None:
        """Mark an API version as deprecated."""
        if version in self.supported_versions:
            self._deprecated_versions[version] = deprecated_by or "future"
    
    def is_version_supported(self, version: str) -> bool:
        """Check if a version is supported."""
        return version in self.supported_versions
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        return version in self._deprecated_versions
    
    def get_deprecation_message(self, version: str) -> str:
        """Get deprecation message for a version."""
        replacement = self._deprecated_versions.get(version, "future")
        return f"API version {version} is deprecated. Please use {replacement}."


def versioned(version: str, deprecated: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark a function with a specific API version."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._api_version = version
        func._api_deprecated = deprecated
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if deprecated:
                import warnings
                warnings.warn(f"API version {version} is deprecated", DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        wrapper._api_version = version
        wrapper._api_deprecated = deprecated
        return wrapper
    
    return decorator


def get_api_version(func: Callable[..., Any]) -> Optional[str]:
    """Get the API version for a function."""
    return getattr(func, '_api_version', None)


def is_api_deprecated(func: Callable[..., Any]) -> bool:
    """Check if a function is marked as deprecated."""
    return getattr(func, '_api_deprecated', False)
