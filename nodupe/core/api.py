"""API Module.

API stability decorators and utilities.
"""

import functools
from typing import Callable, Any, TypeVar, Dict, List, Optional
from enum import Enum


T = TypeVar('T', bound=Callable[..., Any])


class APILevel(Enum):
    """API stability levels"""
    STABLE = "stable"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


def stable_api(func: T) -> T:
    """Mark a function as stable API"""
    func._stable_api = True  # type: ignore
    func._api_level = APILevel.STABLE  # type: ignore
    return func


def beta_api(func: T) -> T:
    """Mark a function as beta API"""
    func._beta_api = True  # type: ignore
    func._api_level = APILevel.BETA  # type: ignore
    return func


def experimental_api(func: T) -> T:
    """Mark a function as experimental API"""
    func._experimental_api = True  # type: ignore
    func._api_level = APILevel.EXPERIMENTAL  # type: ignore
    return func


def deprecated(func: T) -> T:
    """Mark a function as deprecated"""
    func._deprecated = True  # type: ignore
    func._api_level = APILevel.DEPRECATED  # type: ignore
    return func


class API:
    """Handle API management"""

    _registered_endpoints: Dict[str, Callable[..., Any]] = {}
    _api_metadata: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def register_api(
        endpoint_name: str,
        func: Callable[..., Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register API endpoint with metadata

        Args:
            endpoint_name: Name of the API endpoint
            func: Function to register
            metadata: Additional metadata about the endpoint
        """
        API._registered_endpoints[endpoint_name] = func
        API._api_metadata[endpoint_name] = metadata or {}

    @staticmethod
    def get_endpoint(endpoint_name: str) -> Optional[Callable[..., Any]]:
        """Get registered API endpoint

        Args:
            endpoint_name: Name of the endpoint to retrieve

        Returns:
            Registered function or None if not found
        """
        return API._registered_endpoints.get(endpoint_name)

    @staticmethod
    def list_endpoints() -> List[str]:
        """List all registered API endpoints

        Returns:
            List of endpoint names
        """
        return list(API._registered_endpoints.keys())

    @staticmethod
    def get_metadata(endpoint_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an API endpoint

        Args:
            endpoint_name: Name of the endpoint

        Returns:
            Metadata dictionary or None if endpoint not found
        """
        return API._api_metadata.get(endpoint_name)

    @staticmethod
    def validate_api_call(endpoint_name: str, *args: Any, **kwargs: Any) -> bool:
        """Validate API call before execution

        Args:
            endpoint_name: Name of the endpoint to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            True if call is valid, False otherwise
        """
        endpoint = API.get_endpoint(endpoint_name)
        if not endpoint:
            return False

        # Check if function has validation metadata
        if hasattr(endpoint, '_validator'):
            validator = getattr(endpoint, '_validator')
            return validator(*args, **kwargs)

        return True

    @staticmethod
    def call_endpoint(endpoint_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call registered API endpoint safely

        Args:
            endpoint_name: Name of the endpoint to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call
        """
        endpoint = API.get_endpoint(endpoint_name)
        if not endpoint:
            raise ValueError(f"Endpoint '{endpoint_name}' not registered")

        if not API.validate_api_call(endpoint_name, *args, **kwargs):
            raise ValueError(f"Invalid arguments for endpoint '{endpoint_name}'")

        return endpoint(*args, **kwargs)


def api_endpoint(
    endpoint_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a function as an API endpoint

    Args:
        endpoint_name: Name of the API endpoint
        metadata: Additional metadata about the endpoint
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        API.register_api(endpoint_name, func, metadata)
        return func
    return decorator


def validate_args(**validators: Callable[[Any], bool]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add argument validators to API functions

    Args:
        **validators: Dictionary of argument names to validator functions
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Validate arguments
            sig = func.__code__.co_varnames[:func.__code__.co_argcount]
            bound_args = dict(zip(sig, args))
            bound_args.update(kwargs)

            for arg_name, validator in validators.items():
                if arg_name in bound_args:
                    if not validator(bound_args[arg_name]):
                        raise ValueError(f"Validation failed for argument '{arg_name}'")

            return func(*args, **kwargs)

        # Add validator as an attribute to the wrapper function
        def validator_func(*a: Any, **kw: Any) -> bool:
            sig = func.__code__.co_varnames[:func.__code__.co_argcount]
            bound_args = dict(zip(sig, a))
            bound_args.update(kw)
            return all(
                validators[arg_name](val) for arg_name, val in bound_args.items()
                if arg_name in validators
            )
        setattr(wrapper, '_validator', validator_func)
        return wrapper
    return decorator
