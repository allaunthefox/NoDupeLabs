# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Service container for dependency injection.

Provides centralized dependency management for NoDupeLabs components.
Enables testable, loosely-coupled architecture.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .config import load_config


@dataclass
class ServiceContainer:
    """Centralized container for service dependencies.

    Provides lazy initialization of services and allows
    overriding services for testing.

    Example:
        >>> container = ServiceContainer()
        >>> db = container.get_db()
        >>> classifier = container.get_classifier()

    For testing:
        >>> container = ServiceContainer()
        >>> container.override('db', mock_db)
        >>> db = container.get_db()  # Returns mock_db
    """

    config_path: str = "nodupe.yml"
    _config: Optional[Dict[str, Any]] = field(default=None, repr=False)
    _services: Dict[str, Any] = field(default_factory=dict, repr=False)
    _overrides: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def config(self) -> Dict[str, Any]:
        """Get configuration (lazy loaded)."""
        if self._config is None:
            self._config = load_config(self.config_path)
        return self._config

    def override(self, name: str, service: Any) -> None:
        """Override a service for testing.

        Args:
            name: Service name
            service: Service instance to use
        """
        self._overrides[name] = service

    def clear_overrides(self) -> None:
        """Clear all service overrides."""
        self._overrides.clear()
        self._services.clear()

    def get_db(self) -> Any:
        """Get database facade.

        Returns:
            DB instance
        """
        if 'db' in self._overrides:
            return self._overrides['db']

        if 'db' not in self._services:
            from .db import DB
            db_path = self.config.get('db_path', 'output/index.db')
            self._services['db'] = DB(Path(db_path))

        return self._services['db']

    def get_classifier(self, threshold: int = 2) -> Any:
        """Get NSFW classifier.

        Args:
            threshold: Classification threshold

        Returns:
            NSFWClassifier instance
        """
        if 'classifier' in self._overrides:
            return self._overrides['classifier']

        if 'classifier' not in self._services:
            from .nsfw_classifier import NSFWClassifier
            backend = self._overrides.get('ai_backend')
            self._services['classifier'] = NSFWClassifier(
                threshold=threshold,
                backend=backend
            )

        return self._services['classifier']

    def get_file_writer(self) -> Any:
        """Get file writer.

        Returns:
            FileWriter instance
        """
        if 'file_writer' in self._overrides:
            return self._overrides['file_writer']

        if 'file_writer' not in self._services:
            from .io import RealFileWriter
            self._services['file_writer'] = RealFileWriter()

        return self._services['file_writer']

    def get_plugin_manager(self) -> Any:
        """Get plugin manager.

        Returns:
            PluginManager instance
        """
        if 'plugin_manager' in self._overrides:
            return self._overrides['plugin_manager']

        if 'plugin_manager' not in self._services:
            from .plugins import pm
            self._services['plugin_manager'] = pm

        return self._services['plugin_manager']


# Global container instance (can be replaced for testing)
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container.

    Returns:
        ServiceContainer instance
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def set_container(container: ServiceContainer) -> None:
    """Set the global service container.

    Primarily used for testing.

    Args:
        container: Container to use
    """
    global _container
    _container = container


def reset_container() -> None:
    """Reset the global container to None.

    Primarily used for testing cleanup.
    """
    global _container
    _container = None
