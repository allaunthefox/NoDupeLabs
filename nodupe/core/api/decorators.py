# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""API Decorators Module.

Provides common API decorators for NoDupeLabs.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional


def api_endpoint(methods: Optional[List[str]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark a function as an API endpoint."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cors(origins: Optional[List[str]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add CORS headers to a response."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if isinstance(result, dict):
                result["_cors"] = {
                    "Access-Control-Allow-Origin": ", ".join(origins) if origins else "*",
                }
            return result
        return wrapper
    return decorator


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require authentication for an endpoint."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        auth_token = kwargs.get("auth_token") or kwargs.get("authorization")
        if not auth_token:
            raise PermissionError("Authentication required")
        return func(*args, **kwargs)
    return wrapper


def cache_response(ttl: int = 300) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache API responses."""
    _cache: Dict[str, tuple[Any, float]] = {}

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time
            cache_key = str(args) + str(sorted(kwargs.items()))
            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if time.time() - timestamp < ttl:
                    return result
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to retry failed operations."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time
            last_exception: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def deprecated(message: str = "This endpoint is deprecated") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark endpoints as deprecated."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import warnings
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator
