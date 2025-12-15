"""Plugin Lifecycle Module.

Plugin lifecycle management using standard library only.

Key Features:
    - Plugin initialization and shutdown
    - Dependency resolution and ordering
    - Graceful error handling
    - Standard library only (no external dependencies)

Dependencies:
    - typing (standard library)
    - enum (standard library)
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from .base import Plugin
from .registry import PluginRegistry


class PluginLifecycleError(Exception):
    """Plugin lifecycle error"""


class PluginState(Enum):
    """Plugin lifecycle states."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class PluginLifecycleManager:
    """Handle plugin lifecycle management.

    Manages plugin initialization, shutdown, and dependency resolution.
    """

    def __init__(self, registry: PluginRegistry):
        """Initialize lifecycle manager.

        Args:
            registry: Plugin registry instance
        """
        self.registry = registry
        self._plugin_states: Dict[str, PluginState] = {}
        self._plugin_dependencies: Dict[str, List[str]] = {}
        self._plugin_containers: Dict[str, Any] = {}

    def initialize_plugin(
        self,
        plugin: Plugin,
        container: Any,
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """Initialize a plugin with dependency resolution.

        Args:
            plugin: Plugin instance to initialize
            container: Dependency injection container
            dependencies: Optional list of plugin dependencies

        Returns:
            True if initialization successful

        Raises:
            PluginLifecycleError: If initialization fails
        """
        try:
            plugin_name = plugin.name
            
            # Check if plugin is already initialized
            current_state = self._plugin_states.get(plugin_name, PluginState.UNLOADED)
            if current_state == PluginState.INITIALIZED:
                return True  # Already initialized
            
            # Set state to initializing
            self._plugin_states[plugin_name] = PluginState.INITIALIZING
            
            # Store dependencies if provided
            if dependencies is not None:
                self._plugin_dependencies[plugin_name] = dependencies
            
            # Check dependency availability
            if not self._check_dependencies(plugin_name):
                self._plugin_states[plugin_name] = PluginState.ERROR
                raise PluginLifecycleError(
                    f"Dependencies not satisfied for plugin {plugin_name}"
                )
            
            # Store container reference
            self._plugin_containers[plugin_name] = container
            
            # Initialize the plugin
            plugin.initialize(container)
            
            # Set state to initialized
            self._plugin_states[plugin_name] = PluginState.INITIALIZED
            
            return True

        except Exception as e:
            self._plugin_states[plugin_name] = PluginState.ERROR
            if isinstance(e, PluginLifecycleError):
                raise
            raise PluginLifecycleError(f"Failed to initialize plugin {plugin_name}: {e}") from e

    def shutdown_plugin(self, plugin_name: str) -> bool:
        """Shutdown a plugin.

        Args:
            plugin_name: Name of plugin to shutdown

        Returns:
            True if shutdown successful, False if plugin not found
        """
        try:
            # Check if plugin exists
            plugin = self.registry.get_plugin(plugin_name)
            if plugin is None:
                return False

            current_state = self._plugin_states.get(plugin_name, PluginState.UNLOADED)
            if current_state in [PluginState.SHUTDOWN, PluginState.UNLOADED]:
                return True  # Already shutdown

            # Set state to shutting down
            self._plugin_states[plugin_name] = PluginState.SHUTTING_DOWN

            # Shutdown the plugin
            try:
                plugin.shutdown()
            except Exception as e:
                # Log error but continue
                print(f"Warning: Error shutting down plugin {plugin_name}: {e}")

            # Clean up state
            self._plugin_states[plugin_name] = PluginState.SHUTDOWN
            self._plugin_containers.pop(plugin_name, None)

            return True

        except Exception as e:
            self._plugin_states[plugin_name] = PluginState.ERROR
            raise PluginLifecycleError(f"Failed to shutdown plugin {plugin_name}: {e}") from e

    def initialize_all_plugins(self, container: Any) -> bool:
        """Initialize all registered plugins with dependency resolution.

        Args:
            container: Dependency injection container

        Returns:
            True if all plugins initialized successfully

        Raises:
            PluginLifecycleError: If any plugin fails to initialize
        """
        try:
            # Get all plugins from registry
            plugins = self.registry.get_plugins()
            
            # Sort plugins by dependency order
            ordered_plugins = self._sort_plugins_by_dependencies(plugins)
            
            # Initialize each plugin
            for plugin in ordered_plugins:
                if not self.initialize_plugin(plugin, container):
                    raise PluginLifecycleError(f"Failed to initialize plugin {plugin.name}")
            
            return True

        except Exception as e:
            if isinstance(e, PluginLifecycleError):
                raise
            raise PluginLifecycleError(f"Failed to initialize all plugins: {e}") from e

    def shutdown_all_plugins(self) -> bool:
        """Shutdown all initialized plugins.

        Returns:
            True if all plugins shutdown successfully
        """
        try:
            # Get all plugins from registry
            plugins = self.registry.get_plugins()
            
            # Shutdown in reverse dependency order
            for plugin in reversed(plugins):
                try:
                    self.shutdown_plugin(plugin.name)
                except PluginLifecycleError:
                    # Continue shutting down other plugins even if one fails
                    continue
            
            return True

        except Exception as e:
            raise PluginLifecycleError(f"Failed to shutdown all plugins: {e}") from e

    def get_plugin_state(self, plugin_name: str) -> PluginState:
        """Get the current state of a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Current plugin state
        """
        return self._plugin_states.get(plugin_name, PluginState.UNLOADED)

    def is_plugin_initialized(self, plugin_name: str) -> bool:
        """Check if a plugin is initialized.

        Args:
            plugin_name: Name of plugin

        Returns:
            True if plugin is initialized
        """
        return self._plugin_states.get(plugin_name, PluginState.UNLOADED) == PluginState.INITIALIZED

    def is_plugin_active(self, plugin_name: str) -> bool:
        """Check if a plugin is active (loaded and initialized).

        Args:
            plugin_name: Name of plugin

        Returns:
            True if plugin is active
        """
        state = self._plugin_states.get(plugin_name, PluginState.UNLOADED)
        return state in [PluginState.INITIALIZED, PluginState.INITIALIZING]

    def get_active_plugins(self) -> List[str]:
        """Get list of active plugin names.

        Returns:
            List of active plugin names
        """
        return [
            name for name, state in self._plugin_states.items()
            if state in [PluginState.INITIALIZED, PluginState.INITIALIZING]
        ]

    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """Get dependencies for a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            List of dependency plugin names
        """
        return self._plugin_dependencies.get(plugin_name, [])

    def set_plugin_dependencies(self, plugin_name: str, dependencies: List[str]) -> None:
        """Set dependencies for a plugin.

        Args:
            plugin_name: Name of plugin
            dependencies: List of dependency plugin names
        """
        self._plugin_dependencies[plugin_name] = dependencies

    def _check_dependencies(self, plugin_name: str) -> bool:
        """Check if all dependencies for a plugin are satisfied.

        Args:
            plugin_name: Name of plugin

        Returns:
            True if all dependencies are satisfied
        """
        dependencies = self._plugin_dependencies.get(plugin_name, [])
        
        for dep_name in dependencies:
            dep_state = self._plugin_states.get(dep_name, PluginState.UNLOADED)
            if dep_state != PluginState.INITIALIZED:
                return False
        
        return True

    def _sort_plugins_by_dependencies(self, plugins: List[Plugin]) -> List[Plugin]:
        """Sort plugins by dependency order (topological sort).

        Args:
            plugins: List of plugins to sort

        Returns:
            List of plugins sorted by dependency order
        """
        # Build dependency graph
        graph = {}
        plugin_names = {plugin.name: plugin for plugin in plugins}
        
        for plugin in plugins:
            deps = self._plugin_dependencies.get(plugin.name, [])
            # Only include dependencies that are in our plugin list
            graph[plugin.name] = [dep for dep in deps if dep in plugin_names]
        
        # Topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(node):
            if node in temp_visited:
                raise PluginLifecycleError(f"Circular dependency detected: {node}")
            if node not in visited:
                temp_visited.add(node)
                for dep in graph.get(node, []):
                    visit(dep)
                temp_visited.remove(node)
                visited.add(node)
                result.append(plugin_names[node])
        
        for plugin in plugins:
            if plugin.name not in visited:
                visit(plugin.name)
        
        return result


def create_lifecycle_manager(registry: PluginRegistry) -> PluginLifecycleManager:
    """Create a plugin lifecycle manager instance.

    Args:
        registry: Plugin registry instance

    Returns:
        PluginLifecycleManager instance
    """
    return PluginLifecycleManager(registry)
