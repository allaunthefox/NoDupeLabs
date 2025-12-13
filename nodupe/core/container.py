# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
# pylint: disable=broad-exception-caught

"""Dependency injection container with hard isolation.

This module provides a minimal dependency injection container that
maintains complete isolation from optional dependencies.

Key Features:
    - Service registration and retrieval
    - Lazy initialization
    - Graceful degradation
    - Error handling with resilience

Dependencies:
    - Standard library only
"""

from typing import Dict, Any, Optional, Callable

class ServiceContainer:
    """Minimal dependency injection container.

    Responsibilities:
    - Service registration and management
    - Lazy initialization
    - Graceful degradation
    """

    def __init__(self):
        """Initialize service container."""
        self.services: Dict[str, Any] = {}
        self.factories: Dict[str, Callable[[], Any]] = {}

    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance.

        Args:
            name: Service name
            service: Service instance
        """
        self.services[name] = service

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a service factory for lazy initialization.

        Args:
            name: Service name
            factory: Factory function that creates the service
        """
        self.factories[name] = factory

    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name, with lazy initialization if needed.

        Args:
            name: Service name

        Returns:
            Service instance or None if not found
        """
        # Check if service is already initialized
        if name in self.services:
            return self.services[name]

        # Try to initialize from factory
        if name in self.factories:
            try:
                service = self.factories[name]()
                self.services[name] = service
                return service
            except Exception as e:
                print(f"[WARN] Failed to initialize service {name}: {e}")
                return None

        return None

    def has_service(self, name: str) -> bool:
        """Check if a service is available.

        Args:
            name: Service name

        Returns:
            True if service is available, False otherwise
        """
        return name in self.services or name in self.factories

    def remove_service(self, name: str) -> None:
        """Remove a service from the container.

        Args:
            name: Service name
        """
        if name in self.services:
            del self.services[name]
        if name in self.factories:
            del self.factories[name]

    def clear(self) -> None:
        """Clear all services and factories."""
        self.services.clear()
        self.factories.clear()

# Global service container instance
container = ServiceContainer()
