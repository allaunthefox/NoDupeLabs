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
        """Access configuration as a plain dict (lazy loaded).

        The configuration is read once from the path provided by
        `config_path` and cached on the container instance. Use
        :meth:`override` in tests to inject a custom configuration.

        Returns:
            A dictionary containing the merged configuration values.
        """
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
        """Clear all service overrides and reset created services.

        Useful during tests to restore the container to a clean state so
        overrides do not leak between test cases.
        """
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

    def get_logger(self) -> Any:
        """Return the structured JSONL logger used by the application.

        Returns:
            JsonlLogger: Logger instance which writes JSONL events to
            the configured log directory.
        """
        if 'logger' in self._overrides:
            return self._overrides['logger']
        if 'logger' not in self._services:
            from .logger import JsonlLogger
            log_dir = self.config.get('log_dir', 'logs')
            self._services['logger'] = JsonlLogger(Path(log_dir))
        return self._services['logger']

    def get_metrics(self) -> Any:
        """Return the global Metrics collector instance.

        Returns:
            Metrics: Metrics instance used for recording application metrics
            and optionally persisting them to disk.
        """
        if 'metrics' in self._overrides:
            return self._overrides['metrics']
        if 'metrics' not in self._services:
            from .metrics import Metrics
            metrics_path = self.config.get('metrics_path', 'metrics.json')
            self._services['metrics'] = Metrics(Path(metrics_path))
        return self._services['metrics']

    def get_backend(self) -> Any:
        """Return a chosen AI backend instance (or ``None`` when unavailable).

        The backend is created lazily, cached and only created once; use
        :py:meth:`override` to inject a test double for unit tests.

        Returns:
            A backend instance or ``None`` if no backend could be chosen.
        """
        if 'backend' in self._overrides:
            return self._overrides['backend']
        if 'backend' not in self._services:
            from .ai.backends import choose_backend
            model_hint = self.config.get('ai', {}).get('model_path')
            try:
                self._services['backend'] = choose_backend(model_hint)
            except Exception:
                self._services['backend'] = None
        return self._services['backend']

    def get_telemetry(self) -> Any:
        """Return a Telemetry instance configured from container settings.

        Returns:
            Telemetry: Instance used for structured logging, metrics and
            telemetry exports.
        """
        if 'telemetry' in self._overrides:
            return self._overrides['telemetry']
        if 'telemetry' not in self._services:
            from .telemetry import Telemetry
            log_dir = Path(self.config.get('log_dir', 'logs'))
            metrics_path = Path(self.config.get(
                'metrics_path', 'metrics.json'))
            self._services['telemetry'] = Telemetry(
                log_dir=log_dir,
                metrics_path=metrics_path
            )
        return self._services['telemetry']

    def get_scanner(self) -> Any:
        """Get scanner orchestrator.

        Returns:
            ScanOrchestrator instance (or facade)
        """
        if 'scanner' in self._overrides:
            return self._overrides['scanner']

        if 'scanner' not in self._services:
            try:
                from .scan import ScanOrchestrator
                self._services['scanner'] = ScanOrchestrator(
                    db=self.get_db(),
                    telemetry=self.get_telemetry(),
                    backend=self.get_backend(),
                    plugin_manager=self.get_plugin_manager()
                )
            except ImportError:
                # Fallback to legacy scanner facade if orchestrator unavailable
                # (This path is mostly for partial environments or tests)
                from .scanner import threaded_hash
                self._services['scanner'] = threaded_hash

        return self._services['scanner']


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
