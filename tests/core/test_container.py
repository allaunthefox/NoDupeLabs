"""Test container module functionality."""

import pytest

from nodupe.core.container import ServiceContainer, container


class TestServiceContainer:
    """Test ServiceContainer class functionality."""

    def test_initialization(self):
        """Test ServiceContainer initialization."""
        sc = ServiceContainer()
        assert hasattr(sc, "services")
        assert hasattr(sc, "factories")
        assert isinstance(sc.services, dict)
        assert isinstance(sc.factories, dict)
        assert len(sc.services) == 0
        assert len(sc.factories) == 0

    def test_register_service(self):
        """Test registering a service."""
        sc = ServiceContainer()
        service = {"name": "test_service"}

        sc.register_service("test", service)
        assert "test" in sc.services
        assert sc.services["test"] is service
        assert len(sc.services) == 1

    def test_register_factory(self):
        """Test registering a factory."""
        sc = ServiceContainer()

        def factory():
            return {"name": "factory_service"}

        sc.register_factory("factory_test", factory)
        assert "factory_test" in sc.factories
        assert sc.factories["factory_test"] is factory
        assert len(sc.factories) == 1

    def test_get_service_direct(self):
        """Test getting a directly registered service."""
        sc = ServiceContainer()
        service = {"name": "direct_service"}

        sc.register_service("direct", service)
        retrieved = sc.get_service("direct")
        assert retrieved is service
        assert retrieved["name"] == "direct_service"

    def test_get_service_lazy_initialization(self):
        """Test getting a service with lazy initialization."""
        sc = ServiceContainer()

        def factory():
            return {"name": "lazy_service"}

        sc.register_factory("lazy", factory)

        # Service should not be in services yet
        assert "lazy" not in sc.services

        # Getting service should trigger factory
        retrieved = sc.get_service("lazy")
        assert retrieved is not None
        assert retrieved["name"] == "lazy_service"

        # Service should now be in services
        assert "lazy" in sc.services
        assert sc.services["lazy"] is retrieved

    def test_get_nonexistent_service(self):
        """Test getting a non-existent service."""
        sc = ServiceContainer()
        result = sc.get_service("nonexistent")
        assert result is None

    def test_get_service_factory_exception(self):
        """Test getting service when factory raises exception."""
        sc = ServiceContainer()

        def failing_factory():
            raise Exception("Factory failed")

        sc.register_factory("failing", failing_factory)

        # Should handle exception gracefully and return None
        result = sc.get_service("failing")
        assert result is None

        # Service should not be registered
        assert "failing" not in sc.services

    def test_has_service(self):
        """Test has_service method."""
        sc = ServiceContainer()
        service = {"name": "test"}

        def factory():
            return {"name": "factory"}

        sc.register_service("direct", service)
        sc.register_factory("lazy", factory)

        assert sc.has_service("direct") is True
        assert sc.has_service("lazy") is True
        assert sc.has_service("nonexistent") is False

    def test_remove_service(self):
        """Test removing a service."""
        sc = ServiceContainer()
        service = {"name": "test"}

        def factory():
            return {"name": "factory"}

        sc.register_service("direct", service)
        sc.register_factory("lazy", factory)

        # Remove direct service
        sc.remove_service("direct")
        assert "direct" not in sc.services
        assert sc.has_service("direct") is False

        # Remove factory service
        sc.remove_service("lazy")
        assert "lazy" not in sc.factories
        assert sc.has_service("lazy") is False

    def test_clear(self):
        """Test clearing all services."""
        sc = ServiceContainer()
        service = {"name": "test"}

        def factory():
            return {"name": "factory"}

        sc.register_service("direct", service)
        sc.register_factory("lazy", factory)

        sc.clear()
        assert len(sc.services) == 0
        assert len(sc.factories) == 0
        assert sc.has_service("direct") is False
        assert sc.has_service("lazy") is False


class TestGlobalContainer:
    """Test global container instance."""

    def test_global_container_instance(self):
        """Test that global container is a ServiceContainer instance."""
        assert isinstance(container, ServiceContainer)
        assert hasattr(container, "services")
        assert hasattr(container, "factories")

    def test_global_container_isolation(self):
        """Test that global container maintains isolation."""
        # Clear global container for clean test
        container.clear()

        service1 = {"name": "service1"}
        service2 = {"name": "service2"}

        container.register_service("test1", service1)
        container.register_service("test2", service2)

        assert container.get_service("test1") is service1
        assert container.get_service("test2") is service2
        assert container.has_service("test1") is True
        assert container.has_service("test2") is True

        # Clean up
        container.clear()


class TestContainerIntegration:
    """Test container integration scenarios."""

    def test_container_workflow(self):
        """Test complete container workflow."""
        sc = ServiceContainer()

        # Register services
        config_service = {"config": "settings"}
        sc.register_service("config", config_service)

        # Register factory
        def create_database_service():
            return {"db": "connection"}

        sc.register_factory("database", create_database_service)

        # Test service availability
        assert sc.has_service("config") is True
        assert sc.has_service("database") is True

        # Test service retrieval
        config = sc.get_service("config")
        assert config is config_service

        # Test lazy initialization
        db = sc.get_service("database")
        assert db is not None
        assert db["db"] == "connection"

        # Test that factory service is now in services
        assert sc.has_service("database") is True
        assert "database" in sc.services

    def test_container_with_complex_objects(self):
        """Test container with complex objects."""
        sc = ServiceContainer()

        class TestService:
            def __init__(self, name):
                self.name = name

            def get_name(self):
                return self.name

        # Register complex service
        service_instance = TestService("test_service")
        sc.register_service("complex", service_instance)

        # Register factory for complex object
        def create_complex_service():
            return TestService("factory_service")

        sc.register_factory("complex_factory", create_complex_service)

        # Test direct service
        retrieved = sc.get_service("complex")
        assert isinstance(retrieved, TestService)
        assert retrieved.get_name() == "test_service"

        # Test factory service
        factory_service = sc.get_service("complex_factory")
        assert isinstance(factory_service, TestService)
        assert factory_service.get_name() == "factory_service"

    def test_container_graceful_degradation(self):
        """Test container graceful degradation with failing factories."""
        sc = ServiceContainer()

        def failing_factory():
            raise Exception("Critical failure")

        sc.register_factory("failing", failing_factory)

        # Should handle exception gracefully
        result = sc.get_service("failing")
        assert result is None

        # Container should still be functional
        sc.register_service("working", {"status": "ok"})
        working = sc.get_service("working")
        assert working is not None
        assert working["status"] == "ok"


class TestContainerEdgeCases:
    """Test container edge cases."""

    def test_register_same_service_twice(self):
        """Test registering the same service twice."""
        sc = ServiceContainer()
        service1 = {"name": "first"}
        service2 = {"name": "second"}

        sc.register_service("test", service1)
        sc.register_service("test", service2)

        # Second registration should overwrite first
        result = sc.get_service("test")
        assert result is service2
        assert result["name"] == "second"

    def test_register_service_and_factory_same_name(self):
        """Test registering service and factory with same name."""
        sc = ServiceContainer()
        service = {"name": "direct"}

        def factory():
            return {"name": "factory"}

        sc.register_service("test", service)
        sc.register_factory("test", factory)

        # Service should take precedence
        result = sc.get_service("test")
        assert result is service
        assert result["name"] == "direct"

    def test_get_service_after_removal(self):
        """Test getting service after removal."""
        sc = ServiceContainer()
        service = {"name": "test"}

        sc.register_service("test", service)
        assert sc.get_service("test") is service

        sc.remove_service("test")
        assert sc.get_service("test") is None
