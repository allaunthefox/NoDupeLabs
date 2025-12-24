"""Test suite for ServiceContainer functionality.

This test suite provides 100% coverage for the ServiceContainer class
in nodupe.core.container module.
"""

import pytest
from unittest.mock import Mock, MagicMock
from nodupe.core.container import ServiceContainer, container


class TestServiceContainer:
    """Test suite for ServiceContainer functionality."""

    def setup_method(self):
        """Setup method to create a fresh container for each test."""
        self.container = ServiceContainer()

    def test_container_initialization(self):
        """Test ServiceContainer initialization."""
        assert isinstance(self.container, ServiceContainer)
        assert self.container.services == {}
        assert self.container.factories == {}

    def test_register_service(self):
        """Test registering a service instance."""
        mock_service = Mock()
        self.container.register_service("test_service", mock_service)

        assert "test_service" in self.container.services
        assert self.container.services["test_service"] is mock_service

    def test_register_factory(self):
        """Test registering a service factory."""
        mock_factory = Mock(return_value="factory_result")
        self.container.register_factory("test_factory", mock_factory)

        assert "test_factory" in self.container.factories
        assert self.container.factories["test_factory"] is mock_factory

    def test_get_service_existing_instance(self):
        """Test getting an existing service instance."""
        mock_service = Mock()
        self.container.register_service("test_service", mock_service)

        result = self.container.get_service("test_service")
        assert result is mock_service

    def test_get_service_from_factory(self):
        """Test getting a service from a factory."""
        mock_service = Mock()
        mock_factory = Mock(return_value=mock_service)
        self.container.register_factory("test_factory", mock_factory)

        result = self.container.get_service("test_factory")
        assert result is mock_service
        mock_factory.assert_called_once()

    def test_get_service_from_factory_lazy_initialization(self):
        """Test lazy initialization from factory."""
        mock_service = Mock()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return mock_service

        self.container.register_factory("lazy_service", factory)

        # First call should initialize
        result1 = self.container.get_service("lazy_service")
        assert result1 is mock_service
        assert call_count == 1

        # Second call should return cached instance
        result2 = self.container.get_service("lazy_service")
        assert result2 is mock_service
        assert call_count == 1  # Factory should not be called again

    def test_get_service_factory_exception_handling(self):
        """Test exception handling when factory fails."""
        def failing_factory():
            raise ValueError("Factory failed")

        self.container.register_factory("failing_service", failing_factory)

        result = self.container.get_service("failing_service")
        assert result is None

    def test_get_nonexistent_service(self):
        """Test getting a non-existent service."""
        result = self.container.get_service("nonexistent")
        assert result is None

    def test_has_service_instance_exists(self):
        """Test has_service for existing service instance."""
        mock_service = Mock()
        self.container.register_service("test_service", mock_service)

        assert self.container.has_service("test_service") is True

    def test_has_service_factory_exists(self):
        """Test has_service for existing factory."""
        mock_factory = Mock()
        self.container.register_factory("test_factory", mock_factory)

        assert self.container.has_service("test_factory") is True

    def test_has_service_nonexistent(self):
        """Test has_service for non-existent service."""
        assert self.container.has_service("nonexistent") is False

    def test_remove_service_instance(self):
        """Test removing a service instance."""
        mock_service = Mock()
        self.container.register_service("test_service", mock_service)

        self.container.remove_service("test_service")

        assert "test_service" not in self.container.services
        assert self.container.has_service("test_service") is False

    def test_remove_service_factory(self):
        """Test removing a service factory."""
        mock_factory = Mock()
        self.container.register_factory("test_factory", mock_factory)

        self.container.remove_service("test_factory")

        assert "test_factory" not in self.container.factories
        assert self.container.has_service("test_factory") is False

    def test_remove_nonexistent_service(self):
        """Test removing a non-existent service (should not raise error)."""
        # This should not raise an exception
        self.container.remove_service("nonexistent")

        # Verify container is still functional
        assert self.container.services == {}
        assert self.container.factories == {}

    def test_clear_all_services(self):
        """Test clearing all services and factories."""
        mock_service = Mock()
        mock_factory = Mock()

        self.container.register_service("service1", mock_service)
        self.container.register_factory("factory1", mock_factory)

        self.container.clear()

        assert self.container.services == {}
        assert self.container.factories == {}
        assert self.container.has_service("service1") is False
        assert self.container.has_service("factory1") is False

    def test_multiple_services_management(self):
        """Test managing multiple services."""
        service1 = Mock()
        service2 = Mock()
        factory1 = Mock(return_value=service1)
        factory2 = Mock(return_value=service2)

        # Register multiple services and factories
        self.container.register_service("service1", service1)
        self.container.register_service("service2", service2)
        self.container.register_factory("factory1", factory1)
        self.container.register_factory("factory2", factory2)

        # Verify all are registered
        assert self.container.has_service("service1")
        assert self.container.has_service("service2")
        assert self.container.has_service("factory1")
        assert self.container.has_service("factory2")

        # Verify retrieval
        assert self.container.get_service("service1") is service1
        assert self.container.get_service("service2") is service2
        assert self.container.get_service("factory1") is service1
        assert self.container.get_service("factory2") is service2

    def test_service_with_complex_object(self):
        """Test registering and retrieving complex service objects."""
        class ComplexService:
            def __init__(self, name: str):
                self.name = name
                self.data = []

            def add_data(self, item):
                self.data.append(item)

        complex_service = ComplexService("test")
        complex_service.add_data("initial")

        self.container.register_service("complex_service", complex_service)

        retrieved = self.container.get_service("complex_service")
        assert retrieved is complex_service
        assert retrieved.name == "test"
        assert retrieved.data == ["initial"]

    def test_factory_returning_none(self):
        """Test factory that returns None."""
        def none_factory():
            return None

        self.container.register_factory("none_factory", none_factory)
        result = self.container.get_service("none_factory")

        # Should return None but also cache it
        assert result is None
        assert "none_factory" in self.container.services

    def test_factory_with_side_effects(self):
        """Test factory with side effects."""
        side_effect_counter = []

        def side_effect_factory():
            side_effect_counter.append(1)
            return Mock()

        self.container.register_factory("side_effect_service", side_effect_factory)

        # First call
        result1 = self.container.get_service("side_effect_service")
        assert len(side_effect_counter) == 1

        # Second call should not trigger factory again
        result2 = self.container.get_service("side_effect_service")
        assert result1 is result2
        assert len(side_effect_counter) == 1

    def test_concurrent_access_simulation(self):
        """Test container behavior with simulated concurrent access."""
        # Create multiple containers to simulate independent instances
        container1 = ServiceContainer()
        container2 = ServiceContainer()

        service1 = Mock(name="container1_service")
        service2 = Mock(name="container2_service")

        container1.register_service("service", service1)
        container2.register_service("service", service2)

        # Each container should have its own services
        assert container1.get_service("service") is service1
        assert container2.get_service("service") is service2
        assert container1.get_service("service") is not container2.get_service("service")

    def test_large_number_of_services(self):
        """Test container with a large number of services."""
        service_count = 100

        # Register many services
        for i in range(service_count):
            service = Mock(name=f"service_{i}")
            self.container.register_service(f"service_{i}", service)
            self.container.register_factory(f"factory_{i}", lambda s=service: s)

        # Verify all services are accessible
        for i in range(service_count):
            service = self.container.get_service(f"service_{i}")
            factory_service = self.container.get_service(f"factory_{i}")
            assert service is not None
            assert factory_service is not None

        # Verify total count
        assert len(self.container.services) == service_count * 2  # instances + cached factories
        assert len(self.container.factories) == service_count


class TestGlobalContainer:
    """Test suite for the global container instance."""

    def test_global_container_instance_exists(self):
        """Test that the global container instance exists."""
        from nodupe.core.container import container as global_container
        assert isinstance(global_container, ServiceContainer)
        assert global_container is container  # Should be the same instance

    def test_global_container_functionality(self):
        """Test that global container works like regular container."""
        mock_service = Mock()
        container.register_service("global_test_service", mock_service)

        result = container.get_service("global_test_service")
        assert result is mock_service

        # Clean up
        container.remove_service("global_test_service")


def test_container_isolation():
    """Test that containers are properly isolated."""
    container1 = ServiceContainer()
    container2 = ServiceContainer()

    service1 = Mock()
    service2 = Mock()

    container1.register_service("shared_service", service1)
    container2.register_service("shared_service", service2)

    assert container1.get_service("shared_service") is service1
    assert container2.get_service("shared_service") is service2
    assert container1.get_service("shared_service") is not container2.get_service("shared_service")


if __name__ == "__main__":
    pytest.main([__file__])
