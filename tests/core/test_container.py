"""
Test suite for nodupe.core.container module
"""
import pytest
from unittest.mock import MagicMock
from nodupe.core.container import ServiceContainer, container


class TestServiceContainer:
    """Test cases for the ServiceContainer class"""
    
    def test_service_container_initialization(self):
        """Test ServiceContainer initialization"""
        service_container = ServiceContainer()
        assert service_container is not None
        assert service_container.services == {}
        assert service_container.factories == {}
    
    def test_service_container_register_service(self):
        """Test ServiceContainer.register_service method"""
        service_container = ServiceContainer()
        
        # Create a mock service
        mock_service = MagicMock()
        
        # Register the service
        service_container.register_service("test_service", mock_service)
        
        # Verify the service was registered
        assert "test_service" in service_container.services
        assert service_container.services["test_service"] is mock_service
    
    def test_service_container_register_factory(self):
        """Test ServiceContainer.register_factory method"""
        service_container = ServiceContainer()
        
        # Create a factory function
        def factory_func():
            return "created_service"
        
        # Register the factory
        service_container.register_factory("test_factory", factory_func)
        
        # Verify the factory was registered
        assert "test_factory" in service_container.factories
        assert service_container.factories["test_factory"] is factory_func
    
    def test_service_container_get_service_existing(self):
        """Test ServiceContainer.get_service method with existing service"""
        service_container = ServiceContainer()
        
        # Register a service
        mock_service = MagicMock()
        service_container.register_service("test_service", mock_service)
        
        # Get the service
        retrieved_service = service_container.get_service("test_service")
        
        # Verify the service was retrieved correctly
        assert retrieved_service is mock_service
    
    def test_service_container_get_service_from_factory(self):
        """Test ServiceContainer.get_service method with factory"""
        service_container = ServiceContainer()
        
        # Create a factory function
        def factory_func():
            return "created_service"
        
        # Register the factory
        service_container.register_factory("test_factory", factory_func)
        
        # Get the service (should create it from factory)
        retrieved_service = service_container.get_service("test_factory")
        
        # Verify the service was created and retrieved correctly
        assert retrieved_service == "created_service"
        # Verify it's now in the services dict
        assert "test_factory" in service_container.services
    
    def test_service_container_get_service_nonexistent(self):
        """Test ServiceContainer.get_service method with nonexistent service"""
        service_container = ServiceContainer()
        
        # Try to get a nonexistent service
        retrieved_service = service_container.get_service("nonexistent_service")
        
        # Verify None is returned
        assert retrieved_service is None
    
    def test_service_container_get_service_factory_failure(self):
        """Test ServiceContainer.get_service method when factory fails"""
        service_container = ServiceContainer()
        
        # Create a factory function that raises an exception
        def failing_factory():
            raise Exception("Factory failed")
        
        # Register the failing factory
        service_container.register_factory("failing_factory", failing_factory)
        
        # Try to get the service (should handle the exception gracefully)
        retrieved_service = service_container.get_service("failing_factory")
        
        # Verify None is returned
        assert retrieved_service is None
    
    def test_service_container_has_service(self):
        """Test ServiceContainer.has_service method"""
        service_container = ServiceContainer()
        
        # Create and register a service
        mock_service = MagicMock()
        service_container.register_service("test_service", mock_service)
        
        # Test with existing service
        assert service_container.has_service("test_service") is True
        
        # Test with nonexistent service
        assert service_container.has_service("nonexistent_service") is False
        
        # Test with factory
        def factory_func():
            return "created_service"
        service_container.register_factory("test_factory", factory_func)
        assert service_container.has_service("test_factory") is True
    
    def test_service_container_remove_service(self):
        """Test ServiceContainer.remove_service method"""
        service_container = ServiceContainer()
        
        # Register a service and a factory
        mock_service = MagicMock()
        service_container.register_service("test_service", mock_service)
        
        def factory_func():
            return "created_service"
        service_container.register_factory("test_factory", factory_func)
        
        # Verify they're there
        assert service_container.has_service("test_service") is True
        assert service_container.has_service("test_factory") is True
        
        # Remove the service
        service_container.remove_service("test_service")
        
        # Verify the service is removed
        assert service_container.has_service("test_service") is False
        
        # Remove the factory
        service_container.remove_service("test_factory")
        
        # Verify the factory is removed
        assert service_container.has_service("test_factory") is False
    
    def test_service_container_clear(self):
        """Test ServiceContainer.clear method"""
        service_container = ServiceContainer()
        
        # Register some services and factories
        mock_service = MagicMock()
        service_container.register_service("test_service", mock_service)
        
        def factory_func():
            return "created_service"
        service_container.register_factory("test_factory", factory_func)
        
        # Verify they're there
        assert len(service_container.services) > 0
        assert len(service_container.factories) > 0
        
        # Clear the container
        service_container.clear()
        
        # Verify everything is cleared
        assert len(service_container.services) == 0
        assert len(service_container.factories) == 0


class TestGlobalContainer:
    """Test cases for the global container instance"""
    
    def test_global_container_exists(self):
        """Test that the global container instance exists"""
        assert container is not None
        assert isinstance(container, ServiceContainer)
    
    def test_global_container_functionality(self):
        """Test that the global container works as expected"""
        # Save original state
        original_services = dict(container.services)
        original_factories = dict(container.factories)
        
        try:
            # Test registering and retrieving a service
            test_service = "global_test_service"
            container.register_service("global_test", test_service)
            
            retrieved = container.get_service("global_test")
            assert retrieved == test_service
        finally:
            # Restore original state
            container.services = original_services
            container.factories = original_factories
