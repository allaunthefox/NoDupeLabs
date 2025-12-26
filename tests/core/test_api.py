"""
Test suite for nodupe.core.api module
"""
import pytest
from nodupe.core.api import API, APILevel, stable_api, beta_api, experimental_api, deprecated, api_endpoint, validate_args


class TestAPILevel:
    """Test cases for APILevel enum"""
    
    def test_api_level_values(self):
        """Test APILevel enum values"""
        assert APILevel.STABLE.value == "stable"
        assert APILevel.BETA.value == "beta"
        assert APILevel.EXPERIMENTAL.value == "experimental"
        assert APILevel.DEPRECATED.value == "deprecated"


class TestAPI:
    """Test cases for the API class"""
    
    def test_api_register_api_static_method(self):
        """Test API.register_api static method"""
        def test_func():
            return "test"
        
        API.register_api("test_endpoint", test_func, {"description": "Test endpoint"})
        
        # Verify the endpoint was registered
        registered_func = API.get_endpoint("test_endpoint")
        assert registered_func is test_func
        
        # Verify the metadata was stored
        metadata = API.get_metadata("test_endpoint")
        assert metadata == {"description": "Test endpoint"}
    
    def test_api_get_endpoint(self):
        """Test API.get_endpoint static method"""
        # Test with non-existent endpoint
        result = API.get_endpoint("non_existent")
        assert result is None
        
        # Test with registered endpoint
        def test_func():
            return "test"
        
        API.register_api("existent_endpoint", test_func)
        result = API.get_endpoint("existent_endpoint")
        assert result is test_func
    
    def test_api_list_endpoints(self):
        """Test API.list_endpoints static method"""
        # Clear any existing endpoints
        API._registered_endpoints.clear()
        API._api_metadata.clear()
        
        # Register a few endpoints
        def func1():
            return "func1"
        
        def func2():
            return "func2"
        
        API.register_api("endpoint1", func1)
        API.register_api("endpoint2", func2)
        
        endpoints = API.list_endpoints()
        assert "endpoint1" in endpoints
        assert "endpoint2" in endpoints
        assert len(endpoints) == 2
    
    def test_api_get_metadata(self):
        """Test API.get_metadata static method"""
        # Test with non-existent endpoint
        result = API.get_metadata("non_existent")
        assert result is None
        
        # Test with registered endpoint with metadata
        def test_func():
            return "test"
        
        API.register_api("metadata_endpoint", test_func, {"version": "1.0", "author": "test"})
        result = API.get_metadata("metadata_endpoint")
        assert result == {"version": "1.0", "author": "test"}
    
    def test_api_validate_api_call(self):
        """Test API.validate_api_call static method"""
        # Test with non-existent endpoint
        result = API.validate_api_call("non_existent")
        assert result is False
        
        # Test with valid endpoint
        def test_func():
            return "test"
        
        API.register_api("valid_endpoint", test_func)
        result = API.validate_api_call("valid_endpoint")
        assert result is True
    
    def test_api_call_endpoint_success(self):
        """Test API.call_endpoint static method with successful call"""
        def test_func(x, y):
            return x + y
        
        API.register_api("add_endpoint", test_func)
        
        result = API.call_endpoint("add_endpoint", 2, 3)
        assert result == 5
    
    def test_api_call_endpoint_not_registered(self):
        """Test API.call_endpoint static method with unregistered endpoint"""
        with pytest.raises(ValueError, match="Endpoint 'non_existent' not registered"):
            API.call_endpoint("non_existent")
    
    def test_api_call_endpoint_invalid_args(self):
        """Test API.call_endpoint static method with invalid arguments"""
        def test_func():
            return "test"
        
        API.register_api("test_endpoint", test_func)
        
        # Add a validator to the function that always fails
        def failing_validator(*args, **kwargs):
            return False
        
        test_func._validator = failing_validator
        
        with pytest.raises(ValueError, match="Invalid arguments for endpoint 'test_endpoint'"):
            API.call_endpoint("test_endpoint")


class TestAPIDecorators:
    """Test cases for API decorators"""
    
    def test_stable_api_decorator(self):
        """Test stable_api decorator"""
        @stable_api
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_stable_api')
        assert test_func._stable_api is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.STABLE
    
    def test_beta_api_decorator(self):
        """Test beta_api decorator"""
        @beta_api
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_beta_api')
        assert test_func._beta_api is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.BETA
    
    def test_experimental_api_decorator(self):
        """Test experimental_api decorator"""
        @experimental_api
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_experimental_api')
        assert test_func._experimental_api is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.EXPERIMENTAL
    
    def test_deprecated_decorator(self):
        """Test deprecated decorator"""
        @deprecated
        def test_func():
            return "test"
        
        assert hasattr(test_func, '_deprecated')
        assert test_func._deprecated is True
        assert hasattr(test_func, '_api_level')
        assert test_func._api_level == APILevel.DEPRECATED
    
    def test_api_endpoint_decorator(self):
        """Test api_endpoint decorator"""
        # Clear any existing endpoints
        API._registered_endpoints.clear()
        API._api_metadata.clear()
        
        @api_endpoint("test_decorator_endpoint", {"version": "1.0"})
        def test_func(x):
            return x * 2
        
        # Verify the endpoint was registered
        registered_func = API.get_endpoint("test_decorator_endpoint")
        assert registered_func is test_func
        
        # Verify the metadata was stored
        metadata = API.get_metadata("test_decorator_endpoint")
        assert metadata == {"version": "1.0"}
        
        # Test the function still works as expected
        result = test_func(5)
        assert result == 10
    
    def test_validate_args_decorator(self):
        """Test validate_args decorator"""
        @validate_args(x=lambda val: isinstance(val, int) and val > 0)
        def positive_int_func(x):
            return x * 2
        
        # Test with valid argument
        result = positive_int_func(5)
        assert result == 10
        
        # Test with invalid argument
        with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
            positive_int_func(-1)
        
        # Test with invalid argument type
        with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
            positive_int_func("not_an_int")
