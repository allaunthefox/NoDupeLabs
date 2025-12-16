"""Plugin Registry
Singleton registry for managing plugins
"""

from typing import List, Optional, Any
from .base import Plugin


class PluginRegistry:
    """Singleton registry for managing plugins"""

    _instance: Optional['PluginRegistry'] = None
    _plugins: dict[str, Plugin]
    _initialized: bool
    _container: Any

    def __new__(cls) -> 'PluginRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # type: ignore
            cls._instance._plugins = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, plugin: Plugin) -> None:
        """Register a plugin"""
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin {plugin.name} already registered")

        self._plugins[plugin.name] = plugin
        plugin.initialize(self._container)

    def unregister(self, name: str) -> None:
        """Unregister a plugin"""
        if name not in self._plugins:
            raise KeyError(f"Plugin {name} not found")

        plugin = self._plugins[name]
        plugin.shutdown()
        del self._plugins[name]

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name"""
        return self._plugins.get(name)

    def get_plugins(self) -> List[Plugin]:
        """Get all registered plugins"""
        return list(self._plugins.values())

    def shutdown(self) -> None:
        """Shutdown all plugins"""
        for plugin in self._plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                print(f"Error shutting down plugin {plugin.name}: {e}")

        self._plugins.clear()
        self._initialized = False

    def initialize(self, container: Any) -> None:
        """Initialize the registry with a dependency container"""
        self._container = container
        self._initialized = True
