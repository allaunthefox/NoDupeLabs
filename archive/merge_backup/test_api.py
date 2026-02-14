"""Test API module functionality."""

import pytest
from typing import Dict, Any, Callable
from nodupe.core.api import (
    API,
    APILevel,
    stable_api,
    beta_api,
    experimental_api,
    deprecated,
    api_endpoint,
    validate_args
)


class TestAPILevel:
    """Test APILevel enum."""

    def test_api_level_values(self):
        """Test APILevel enum values."""
        assert APILevel.STABLE.value == "stable"
        assert APILevel.BETA.value == "beta"
        assert APILevel.EXPERIMENTAL.value == "experimental"
        assert APILevel.DEPRECATED.value == "deprecated"


class TestAPIDecorators:
    """Test API stability decorators."""

    def test_stable_api_decorator(self):
        """Test stable_api decorator."""
        @stable_api
        def test_func():
            return "test"

        assert hasattr(test_func, '_stable_api')
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.STABLE
        assert test_func() == "test"

    def test_beta_api_decorator(self):
        """Test beta_api decorator."""
        @beta_api
        def test_func():
            return "test"

        assert hasattr(test_func, '_beta_api')
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.BETA
        assert test_func() == "test"

    def test_experimental_api_decorator(self):
        """Test experimental_api decorator."""
        @experimental_api
        def test_func():
            return "test"

        assert hasattr(test_func, '_experimental_api')
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.EXPERIMENTAL
        assert test_func() == "test"

    def test_deprecated_decorator(self):
        """Test deprecated decorator."""
        @deprecated
        def test_func():
            return "test"

        assert hasattr(test_func, '_deprecated')
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.DEPRECATED
        assert test_func() == "test"


class TestAPIClass:
    """Test API class functionality."""

    def test_register_and_get_endpoint(self):
        """Test registering and retrieving API endpoints."""
        def test_func():
            return "test"

        API.register_api("test_endpoint", test_func)
        endpoint = API.get_endpoint("test_endpoint")
        assert endpoint is test_func
        assert endpoint() == "test"

    def test_get_nonexistent_endpoint(self):
        """Test getting non-existent endpoint."""
        endpoint = API.get_endpoint("nonexistent")
        assert endpoint is None

    def test_list_endpoints(self):
        """Test listing all registered endpoints."""
        def func1():
            return "func1"

        def func2():
            return "func2"

        API.register_api("endpoint1", func1)
        API.register_api("endpoint2", func2)

        endpoints = API.list_endpoints()
        assert "endpoint1" in endpoints
        assert "endpoint2" in endpoints
        assert len(endpoints) >= 2

    def test_get_metadata(self):
        """Test getting endpoint metadata."""
        def test_func():
            return "test"

        metadata = {"version": "1.0", "description": "Test endpoint"}
        API.register_api("test_endpoint", test_func, metadata)

        retrieved_metadata = API.get_metadata("test_endpoint")
        assert retrieved_metadata == metadata

    def test_get_nonexistent_metadata(self):
        """Test getting metadata for non-existent endpoint."""
        metadata = API.get_metadata("nonexistent")
        assert metadata is None

    def test_validate_api_call_valid(self):
        """Test validating valid API call."""
        @validate_args(arg1=lambda x: x > 0)
        def test_func(arg1: int):
            return arg1 * 2

        API.register_api("validated_endpoint", test_func)

        assert API.validate_api_call("validated_endpoint", 5) is True
        assert API.validate_api_call("validated_endpoint", -1) is False

    def test_validate_api_call_nonexistent(self):
        """Test validating call to non-existent endpoint."""
        assert API.validate_api_call("nonexistent", 1, 2, 3) is False

    def test_call_endpoint_success(self):
        """Test calling endpoint successfully."""
        def test_func(arg1: int, arg2: str):
            return f"{arg1}:{arg2}"

        API.register_api("test_endpoint", test_func)
        result = API.call_endpoint("test_endpoint", 42, "hello")
        assert result == "42:hello"

    def test_call_endpoint_nonexistent(self):
        """Test calling non-existent endpoint."""
        with pytest.raises(ValueError, match="Endpoint 'nonexistent' not registered"):
            API.call_endpoint("nonexistent", 1, 2, 3)

    def test_call_endpoint_invalid_args(self):
        """Test calling endpoint with invalid arguments."""
        @validate_args(arg1=lambda x: x > 0)
        def test_func(arg1: int):
            return arg1 * 2

        API.register_api("validated_endpoint", test_func)

        with pytest.raises(ValueError, match="Invalid arguments for endpoint 'validated_endpoint'"):
            API.call_endpoint("validated_endpoint", -1)


class TestAPIEndpointDecorator:
    """Test api_endpoint decorator."""

    def test_api_endpoint_decorator(self):
        """Test api_endpoint decorator functionality."""
        @api_endpoint("test_endpoint", {"version": "1.0"})
        def test_func():
            return "test"

        # Check that the function was registered
        endpoint = API.get_endpoint("test_endpoint")
        assert endpoint is test_func

        # Check metadata
        metadata = API.get_metadata("test_endpoint")
        assert metadata == {"version": "1.0"}

        # Check function still works
        assert test_func() == "test"


class TestValidateArgsDecorator:
    """Test validate_args decorator."""

    def test_validate_args_success(self):
        """Test validate_args with valid arguments."""
        @validate_args(arg1=lambda x: x > 0, arg2=lambda x: len(x) > 3)
        def test_func(arg1: int, arg2: str):
            return f"{arg1}:{arg2}"

        result = test_func(5, "hello")
        assert result == "5:hello"

    def test_validate_args_failure(self):
        """Test validate_args with invalid arguments."""
        @validate_args(arg1=lambda x: x > 0, arg2=lambda x: len(x) > 3)
        def test_func(arg1: int, arg2: str):
            return f"{arg1}:{arg2}"

        with pytest.raises(ValueError, match="Validation failed for argument 'arg1'"):
            test_func(-1, "hello")

        with pytest.raises(ValueError, match="Validation failed for argument 'arg2'"):
            test_func(5, "hi")

    def test_validate_args_partial_args(self):
        """Test validate_args with partial arguments."""
        @validate_args(arg1=lambda x: x > 0, arg2=lambda x: len(x) > 3)
        def test_func(arg1: int, arg2: str = "default"):
            return f"{arg1}:{arg2}"

        # Should work with valid arg1 and default arg2
        result = test_func(5)
        assert result == "5:default"

        # Should fail with invalid arg1
        with pytest.raises(ValueError, match="Validation failed for argument 'arg1'"):
            test_func(-1)


class TestAPIIntegration:
    """Test API integration scenarios."""

    def test_complete_api_workflow(self):
        """Test complete API workflow from registration to execution."""
        # Clear any existing endpoints for clean test
        API._registered_endpoints.clear()
        API._api_metadata.clear()

        # Create a function with validation - order matters: api_endpoint
        # first, then validate_args
        @api_endpoint("user_info", {"version": "1.0",
                      "description": "Get user information"})
        @validate_args(user_id=lambda x: x > 0, name=lambda x: len(x) > 2)
        def get_user_info(user_id: int, name: str):
            return {"id": user_id, "name": name}

        # Test registration
        assert "user_info" in API.list_endpoints()
        assert API.get_endpoint("user_info") is not None
        assert API.get_metadata("user_info") == {
            "version": "1.0", "description": "Get user information"}

        # Test validation - now with proper validator, it should validate
        # correctly
        assert API.validate_api_call(
            "user_info", 1, "John") is True   # Valid arguments
        assert API.validate_api_call(
            "user_info", -1, "John") is False  # Invalid user_id
        assert API.validate_api_call(
            "user_info", 1, "Jo") is False    # Invalid name

        # Test successful call
        result = API.call_endpoint("user_info", 1, "John")
        assert result == {"id": 1, "name": "John"}

        # Test invalid call
        with pytest.raises(ValueError, match="Invalid arguments for endpoint 'user_info'"):
            API.call_endpoint("user_info", -1, "John")

    def test_api_stability_decorators_with_endpoints(self):
        """Test API stability decorators combined with API endpoints."""
        @stable_api
        @api_endpoint("stable_func")
        def stable_function():
            return "stable"

        @beta_api
        @api_endpoint("beta_func")
        def beta_function():
            return "beta"

        @experimental_api
        @api_endpoint("experimental_func")
        def experimental_function():
            return "experimental"

        @deprecated
        @api_endpoint("deprecated_func")
        def deprecated_function():
            return "deprecated"

        # Test that all functions are registered
        assert API.get_endpoint("stable_func") is stable_function
        assert API.get_endpoint("beta_func") is beta_function
        assert API.get_endpoint("experimental_func") is experimental_function
        assert API.get_endpoint("deprecated_func") is deprecated_function

        # Test that stability markers are preserved
        assert stable_function._api_level == APILevel.STABLE
        assert beta_function._api_level == APILevel.BETA
        assert experimental_function._api_level == APILevel.EXPERIMENTAL
        assert deprecated_function._api_level == APILevel.DEPRECATED
