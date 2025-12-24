"""Test suite for API module functionality.

This test suite provides 100% coverage for the API module
in nodupe.core.api module.
"""

import pytest
from unittest.mock import Mock, MagicMock
from nodupe.core.api import (
    APILevel,
    stable_api,
    beta_api,
    experimental_api,
    deprecated,
    API,
    api_endpoint,
    validate_args
)


class TestAPILevelEnum:
    """Test APILevel enumeration values."""

    def test_api_level_values(self):
        """Test that APILevel enum has correct values."""
        assert APILevel.STABLE.value == "stable"
        assert APILevel.BETA.value == "beta"
        assert APILevel.EXPERIMENTAL.value == "experimental"
        assert APILevel.DEPRECATED.value == "deprecated"

    def test_api_level_membership(self):
        """Test API level membership."""
        assert APILevel.STABLE in APILevel
        assert APILevel.BETA in APILevel
        assert APILevel.EXPERIMENTAL in APILevel
        assert APILevel.DEPRECATED in APILevel


class TestAPIDecorators:
    """Test API decorators functionality."""

    def test_stable_api_decorator(self):
        """Test stable_api decorator."""
        @stable_api
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_stable_api')
        assert test_func._stable_api is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.STABLE

    def test_beta_api_decorator(self):
        """Test beta_api decorator."""
        @beta_api
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_beta_api')
        assert test_func._beta_api is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.BETA

    def test_experimental_api_decorator(self):
        """Test experimental_api decorator."""
        @experimental_api
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_experimental_api')
        assert test_func._experimental_api is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.EXPERIMENTAL

    def test_deprecated_decorator(self):
        """Test deprecated decorator."""
        @deprecated
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_deprecated')
        assert test_func._deprecated is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.DEPRECATED


class TestAPIRegistry:
    """Test API registry functionality."""

    def setup_method(self):
        """Setup method to clear API registry before each test."""
        # Reset the static dictionaries to ensure clean state
        API._registered_endpoints.clear()
        API._api_metadata.clear()

    def test_register_api_endpoint(self):
        """Test registering an API endpoint."""
        def test_function():
            return "result"
        
        API.register_api("test_endpoint", test_function, {"description": "test"})
        
        assert "test_endpoint" in API._registered_endpoints
        assert API._registered_endpoints["test_endpoint"] is test_function
        assert API._api_metadata["test_endpoint"]["description"] == "test"

    def test_register_api_endpoint_no_metadata(self):
        """Test registering an API endpoint without metadata."""
        def test_function():
            return "result"
        
        API.register_api("test_endpoint_no_meta", test_function)
        
        assert "test_endpoint_no_meta" in API._registered_endpoints
        assert API._registered_endpoints["test_endpoint_no_meta"] is test_function
        assert API._api_metadata["test_endpoint_no_meta"] == {}

    def test_get_endpoint_existing(self):
        """Test getting an existing endpoint."""
        def test_function():
            return "result"
        
        API.register_api("existing_endpoint", test_function)
        
        result = API.get_endpoint("existing_endpoint")
        assert result is test_function

    def test_get_endpoint_nonexistent(self):
        """Test getting a non-existent endpoint."""
        result = API.get_endpoint("nonexistent_endpoint")
        assert result is None

    def test_list_endpoints(self):
        """Test listing all registered endpoints."""
        def func1(): return 1
        def func2(): return 2
        
        API.register_api("endpoint1", func1)
        API.register_api("endpoint2", func2)
        
        endpoints = API.list_endpoints()
        assert len(endpoints) == 2
        assert "endpoint1" in endpoints
        assert "endpoint2" in endpoints

    def test_get_metadata_existing(self):
        """Test getting metadata for existing endpoint."""
        def test_function():
            return "result"
        
        metadata = {"description": "test", "version": "1.0.0"}
        API.register_api("meta_endpoint", test_function, metadata)
        
        result = API.get_metadata("meta_endpoint")
        assert result == metadata

    def test_get_metadata_nonexistent(self):
        """Test getting metadata for non-existent endpoint."""
        result = API.get_metadata("nonexistent_meta")
        assert result is None

    def test_validate_api_call_valid(self):
        """Test validating a valid API call."""
        def test_function(x, y):
            return x + y
        
        API.register_api("valid_call", test_function)
        
        is_valid = API.validate_api_call("valid_call", 1, 2)
        assert is_valid is True

    def test_validate_api_call_nonexistent(self):
        """Test validating a call to non-existent endpoint."""
        is_valid = API.validate_api_call("nonexistent_call", 1, 2)
        assert is_valid is False

    def test_call_endpoint_success(self):
        """Test calling an endpoint successfully."""
        def test_function(x, y):
            return x + y
        
        API.register_api("success_endpoint", test_function)
        
        result = API.call_endpoint("success_endpoint", 1, 2)
        assert result == 3

    def test_call_endpoint_not_registered(self):
        """Test calling a non-registered endpoint."""
        with pytest.raises(ValueError, match="Endpoint 'missing_endpoint' not registered"):
            API.call_endpoint("missing_endpoint", 1, 2)

    def test_call_endpoint_with_validator(self):
        """Test calling endpoint with validation."""
        def test_function(x):
            return x * 2
        
        # Add a validator to the function
        def validator(*args, **kwargs):
            return len(args) > 0 and args[0] > 0
        
        test_function._validator = validator
        API.register_api("validated_endpoint", test_function)
        
        # This should work
        result = API.call_endpoint("validated_endpoint", 5)
        assert result == 10

    def test_call_endpoint_with_invalid_args(self):
        """Test calling endpoint with invalid arguments."""
        def test_function(x):
            if x <= 0:
                raise ValueError("x must be positive")
            return x * 2
        
        API.register_api("invalid_args_endpoint", test_function)
        
        with pytest.raises(ValueError):
            API.call_endpoint("invalid_args_endpoint", -1)


class TestAPIEndpointDecorator:
    """Test api_endpoint decorator functionality."""

    def setup_method(self):
        """Setup method to clear API registry before each test."""
        API._registered_endpoints.clear()
        API._api_metadata.clear()

    def test_api_endpoint_decorator_registration(self):
        """Test that api_endpoint decorator registers functions."""
        @api_endpoint("decorated_endpoint", {"description": "decorated test"})
        def decorated_function(x):
            return x * 2
        
        # Verify function is registered
        assert "decorated_endpoint" in API._registered_endpoints
        assert API._registered_endpoints["decorated_endpoint"] is decorated_function
        assert API._api_metadata["decorated_endpoint"]["description"] == "decorated test"
        
        # Verify function still works normally
        result = decorated_function(5)
        assert result == 10

    def test_api_endpoint_decorator_no_metadata(self):
        """Test api_endpoint decorator without metadata."""
        @api_endpoint("simple_endpoint")
        def simple_function(x):
            return x + 1
        
        # Verify function is registered
        assert "simple_endpoint" in API._registered_endpoints
        assert API._api_metadata["simple_endpoint"] == {}
        
        # Verify function still works
        result = simple_function(5)
        assert result == 6


class TestValidateArgsDecorator:
    """Test validate_args decorator functionality."""

    def test_validate_args_success(self):
        """Test validate_args decorator with valid arguments."""
        @validate_args(x=lambda v: v > 0, y=lambda v: isinstance(v, int))
        def test_function(x, y):
            return x + y
        
        # Valid call should succeed
        result = test_function(5, 10)
        assert result == 15

    def test_validate_args_invalid_first_arg(self):
        """Test validate_args decorator with invalid first argument."""
        @validate_args(x=lambda v: v > 0, y=lambda v: isinstance(v, int))
        def test_function(x, y):
            return x + y
        
        # Invalid x should fail
        with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
            test_function(-1, 10)

    def test_validate_args_invalid_second_arg(self):
        """Test validate_args decorator with invalid second argument."""
        @validate_args(x=lambda v: v > 0, y=lambda v: isinstance(v, int))
        def test_function(x, y):
            return x + y
        
        # Invalid y should fail
        with pytest.raises(ValueError, match="Validation failed for argument 'y'"):
            test_function(5, "invalid")

    def test_validate_args_missing_validators(self):
        """Test validate_args decorator with arguments not in validators."""
        @validate_args(x=lambda v: v > 0)
        def test_function(x, z):
            return x + z
        
        # z is not validated, only x is
        result = test_function(5, 10)
        assert result == 15
        
        # Invalid x should still fail
        with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
            test_function(-1, 10)

    def test_validate_args_with_kwargs(self):
        """Test validate_args decorator with keyword arguments."""
        @validate_args(x=lambda v: v > 0, y=lambda v: isinstance(v, int))
        def test_function(x, y=0):
            return x + y
        
        # Valid call with kwargs
        result = test_function(5, y=10)
        assert result == 15
        
        # Invalid x with kwargs
        with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
            test_function(-1, y=10)

    def test_validate_args_preserves_function_attributes(self):
        """Test that validate_args decorator preserves function attributes."""
        @validate_args(x=lambda v: v > 0)
        def test_function(x):
            """Test function docstring."""
            return x * 2
        
        # Check that the wrapped function preserves name and docstring
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."


class TestAPIIntegration:
    """Test API integration scenarios."""

    def setup_method(self):
        """Setup method to clear API registry before each test."""
        API._registered_endpoints.clear()
        API._api_metadata.clear()

    def test_complete_api_workflow(self):
        """Test complete API workflow with registration, validation, and calling."""
        # Register multiple endpoints
        @api_endpoint("add_numbers", {"operation": "addition", "version": "1.0.0"})
        @validate_args(a=lambda v: isinstance(v, (int, float)), b=lambda v: isinstance(v, (int, float)))
        def add_numbers(a, b):
            return a + b
        
        @api_endpoint("multiply_numbers", {"operation": "multiplication", "version": "1.0.0"})
        @validate_args(x=lambda v: isinstance(v, (int, float)), y=lambda v: isinstance(v, (int, float)))
        def multiply_numbers(x, y):
            return x * y
        
        # Verify registration
        assert len(API.list_endpoints()) == 2
        assert "add_numbers" in API.list_endpoints()
        assert "multiply_numbers" in API.list_endpoints()
        
        # Verify metadata
        add_meta = API.get_metadata("add_numbers")
        assert add_meta["operation"] == "addition"
        
        mult_meta = API.get_metadata("multiply_numbers")
        assert mult_meta["operation"] == "multiplication"
        
        # Test successful calls
        add_result = API.call_endpoint("add_numbers", 5, 3)
        assert add_result == 8
        
        mult_result = API.call_endpoint("multiply_numbers", 4, 6)
        assert mult_result == 24
        
        # Test invalid calls
        with pytest.raises(ValueError):
            API.call_endpoint("add_numbers", "invalid", 3)
        
        with pytest.raises(ValueError):
            API.call_endpoint("multiply_numbers", 4, None)

    def test_api_with_different_api_levels(self):
        """Test API with different stability levels."""
        @stable_api
        @api_endpoint("stable_feature")
        def stable_function():
            return "stable"
        
        @beta_api
        @api_endpoint("beta_feature")
        def beta_function():
            return "beta"
        
        @experimental_api
        @api_endpoint("exp_feature")
        def exp_function():
            return "experimental"
        
        @deprecated
        @api_endpoint("deprecated_feature")
        def deprecated_function():
            return "deprecated"
        
        # Verify all are registered
        endpoints = API.list_endpoints()
        assert "stable_feature" in endpoints
        assert "beta_feature" in endpoints
        assert "exp_feature" in endpoints
        assert "deprecated_feature" in endpoints
        
        # Verify API level decorations are preserved
        registered_stable = API.get_endpoint("stable_feature")
        assert hasattr(registered_stable, '_stable_api')
        assert hasattr(registered_stable, '_api_level')
        assert registered_stable._api_level == APILevel.STABLE


class TestAPIEdgeCases:
    """Test API edge cases and error conditions."""

    def setup_method(self):
        """Setup method to clear API registry before each test."""
        API._registered_endpoints.clear()
        API._api_metadata.clear()

    def test_register_same_endpoint_twice(self):
        """Test registering the same endpoint twice (should overwrite)."""
        def func1(): return 1
        def func2(): return 2
        
        API.register_api("duplicate_endpoint", func1)
        API.register_api("duplicate_endpoint", func2)
        
        # Second registration should overwrite first
        result = API.get_endpoint("duplicate_endpoint")
        assert result is func2

    def test_empty_endpoint_name(self):
        """Test registering with empty endpoint name."""
        def test_function(): return "test"
        
        API.register_api("", test_function)
        
        # Should be able to retrieve with empty string
        result = API.get_endpoint("")
        assert result is test_function

    def test_endpoint_with_special_characters(self):
        """Test endpoint names with special characters."""
        def test_function(): return "test"
        
        special_names = ["test-endpoint", "test_endpoint", "test.endpoint", "test endpoint", "test123"]
        
        for name in special_names:
            API.register_api(name, test_function)
            result = API.get_endpoint(name)
            assert result is test_function

    def test_large_metadata(self):
        """Test registering endpoint with large metadata."""
        def test_function(): return "test"
        
        large_metadata = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        API.register_api("large_meta_endpoint", test_function, large_metadata)
        
        retrieved = API.get_metadata("large_meta_endpoint")
        assert len(retrieved) == 1000
        assert retrieved["key_500"] == "value_500"

    def test_many_endpoints(self):
        """Test registering and retrieving many endpoints."""
        # Register 100 endpoints
        for i in range(100):
            def make_func(n):
                def func():
                    return n
                return func
            
            func = make_func(i)
            API.register_api(f"endpoint_{i}", func)
        
        # Verify all are registered
        endpoints = API.list_endpoints()
        assert len(endpoints) == 100
        
        # Verify specific endpoints can be retrieved
        for i in range(0, 100, 10):  # Check every 10th endpoint
            endpoint = API.get_endpoint(f"endpoint_{i}")
            assert endpoint is not None

    def test_reset_api_registry(self):
        """Test resetting the API registry."""
        def test_function(): return "test"
        
        API.register_api("reset_test", test_function)
        assert len(API.list_endpoints()) == 1
        
        # Clear the registry
        API._registered_endpoints.clear()
        API._api_metadata.clear()
        
        assert len(API.list_endpoints()) == 0
        assert API.get_endpoint("reset_test") is None


def test_api_module_level_functions():
    """Test API module-level functionality."""
    # Test that all expected functions are available
    assert stable_api is not None
    assert beta_api is not None
    assert experimental_api is not None
    assert deprecated is not None
    assert API is not None
    assert api_endpoint is not None
    assert validate_args is not None
    
    # Test that API class has expected static methods
    assert hasattr(API, 'register_api')
    assert hasattr(API, 'get_endpoint')
    assert hasattr(API, 'list_endpoints')
    assert hasattr(API, 'get_metadata')
    assert hasattr(API, 'validate_api_call')
    assert hasattr(API, 'call_endpoint')


if __name__ == "__main__":
    pytest.main([__file__])
