"""API Module.

API stability decorators and utilities.
"""

from typing import Callable, Any, TypeVar

T = TypeVar('T', bound=Callable[..., Any])

def stable_api(func: T) -> T:
    """Mark a function as stable API"""
    func._stable_api = True  # type: ignore
    return func

def deprecated(func: T) -> T:
    """Mark a function as deprecated"""
    func._deprecated = True  # type: ignore
    return func

class API:
    """Handle API management"""

    @staticmethod
    def register_api() -> None:
        """Register API endpoints"""
        raise NotImplementedError("API registration not implemented yet")
