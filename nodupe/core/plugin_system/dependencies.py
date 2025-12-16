"""Plugin Dependencies Module.

Plugin dependency management using standard library only.

Key Features:
    - Plugin dependency resolution and ordering
    - Circular dependency detection
    - Dependency validation and conflict resolution
    - Topological sorting for initialization order
    - Standard library only (no external dependencies)

Dependencies:
    - typing (standard library)
    - enum (standard library)
"""

from enum import Enum
from typing import Dict, List, Set, Any, Tuple
from .base import Plugin


class DependencyError(Exception):
    """Plugin dependency error"""


class ResolutionStatus(Enum):
    """Dependency resolution status."""
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    CIRCULAR = "circular"
    MISSING = "missing"
    CONFLICT = "conflict"


class DependencyResolver:
    """Handle plugin dependency resolution and management.

    Resolves plugin dependencies, detects circular dependencies,
    and provides ordering for initialization.
    """

    def __init__(self):
        """Initialize dependency resolver."""
        self._dependencies: Dict[str, List[str]] = {}
        self._dependents: Dict[str, List[str]] = {}
        self._resolutions: Dict[str, ResolutionStatus] = {}
        self._resolved_order: List[str] = []

    def add_dependency(self, plugin_name: str, dependency_name: str) -> None:
        """Add a dependency relationship.

        Args:
            plugin_name: Name of plugin that depends on another
            dependency_name: Name of plugin that is depended upon
        """
        if plugin_name not in self._dependencies:
            self._dependencies[plugin_name] = []
        if dependency_name not in self._dependencies[plugin_name]:
            self._dependencies[plugin_name].append(dependency_name)

        # Update reverse dependencies
        if dependency_name not in self._dependents:
            self._dependents[dependency_name] = []
        if plugin_name not in self._dependents[dependency_name]:
            self._dependents[dependency_name].append(plugin_name)

        # Reset resolution status when dependencies change
        self._resolutions.clear()
        self._resolved_order.clear()

    def remove_dependency(self, plugin_name: str, dependency_name: str) -> bool:
        """Remove a dependency relationship.

        Args:
            plugin_name: Name of plugin that had dependency
            dependency_name: Name of dependency to remove

        Returns:
            True if dependency was removed, False if not found
        """
        if (plugin_name in self._dependencies and
                dependency_name in self._dependencies[plugin_name]):
            self._dependencies[plugin_name].remove(dependency_name)

            # Update reverse dependencies
            if (dependency_name in self._dependents and
                    plugin_name in self._dependents[dependency_name]):
                self._dependents[dependency_name].remove(plugin_name)

            # Reset resolution status
            self._resolutions.clear()
            self._resolved_order.clear()
            return True

        return False

    def get_dependencies(self, plugin_name: str) -> List[str]:
        """Get dependencies for a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            List of dependency names
        """
        return self._dependencies.get(plugin_name, [])

    def get_dependents(self, plugin_name: str) -> List[str]:
        """Get plugins that depend on this plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            List of dependent plugin names
        """
        return self._dependents.get(plugin_name, [])

    def resolve_dependencies(self, plugins: List[str]) -> Tuple[ResolutionStatus, List[str]]:
        """Resolve dependencies for a list of plugins.

        Args:
            plugins: List of plugin names to resolve

        Returns:
            Tuple of (resolution status, ordered list of plugins)
        """
        try:
            # Check for missing dependencies
            all_deps = set()
            for plugin in plugins:
                deps = set(self._dependencies.get(plugin, []))
                all_deps.update(deps)

            missing = all_deps - set(plugins)
            if missing:
                return ResolutionStatus.MISSING, []

            # Check for circular dependencies
            if self._has_circular_dependency(plugins):
                return ResolutionStatus.CIRCULAR, []

            # Perform topological sort
            ordered_plugins = self._topological_sort(plugins)

            if not ordered_plugins:
                return ResolutionStatus.UNRESOLVED, []

            return ResolutionStatus.RESOLVED, ordered_plugins

        except Exception as e:
            raise DependencyError(f"Dependency resolution failed: {e}") from e

    def _has_circular_dependency(self, plugins: List[str]) -> bool:
        """Check if there are circular dependencies among plugins.

        Args:
            plugins: List of plugin names to check

        Returns:
            True if circular dependency exists
        """
        # Build dependency graph for the specific plugins
        graph = {}
        plugin_set = set(plugins)

        for plugin in plugins:
            deps = [dep for dep in self._dependencies.get(plugin, []) if dep in plugin_set]
            graph[plugin] = deps

        # Use DFS to detect cycles
        visiting = set()
        visited = set()

        def dfs(node: str) -> bool:
            if node in visited:
                return False
            if node in visiting:
                return True  # Cycle detected

            visiting.add(node)
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for plugin in plugins:
            if dfs(plugin):
                return True

        return False

    def _topological_sort(self, plugins: List[str]) -> List[str]:
        """Perform topological sort to get dependency order.

        Args:
            plugins: List of plugin names to sort

        Returns:
            Ordered list of plugin names, or empty list if cycle exists
        """
        if self._has_circular_dependency(plugins):
            return []  # Cannot sort with circular dependencies

        # Build dependency graph
        graph = {}
        plugin_set = set(plugins)

        for plugin in plugins:
            deps = [dep for dep in self._dependencies.get(plugin, []) if dep in plugin_set]
            graph[plugin] = deps

        # Perform topological sort using DFS
        result = []
        visited = set()
        temp_visited = set()

        def visit(node: str) -> bool:
            if node in temp_visited:
                return False  # Cycle detected (shouldn't happen if checked earlier)
            if node in visited:
                return True

            temp_visited.add(node)
            for dependency in graph.get(node, []):
                if not visit(dependency):
                    return False
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
            return True

        for plugin in plugins:
            if plugin not in visited:
                if not visit(plugin):
                    return []  # Cycle detected

        return result

    def get_initialization_order(self, plugins: List[str]) -> List[str]:
        """Get the correct initialization order for plugins.

        Args:
            plugins: List of plugin names

        Returns:
            List of plugin names in initialization order
        """
        status, order = self.resolve_dependencies(plugins)
        if status == ResolutionStatus.RESOLVED:
            return order
        return []

    def get_shutdown_order(self, plugins: List[str]) -> List[str]:
        """Get the correct shutdown order for plugins (reverse of initialization).

        Args:
            plugins: List of plugin names

        Returns:
            List of plugin names in shutdown order
        """
        init_order = self.get_initialization_order(plugins)
        return list(reversed(init_order))

    def validate_plugin_compatibility(
        self,
        plugin: Plugin,
        available_plugins: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate that a plugin is compatible with available plugins.

        Args:
            plugin: Plugin instance to validate
            available_plugins: List of available plugin names

        Returns:
            Tuple of (is_compatible, list_of_missing_dependencies)
        """
        required_deps = getattr(plugin, 'dependencies', [])
        missing_deps = [dep for dep in required_deps if dep not in available_plugins]

        return len(missing_deps) == 0, missing_deps

    def get_dependency_tree(self, plugin_name: str) -> Dict[str, Any]:
        """Get the dependency tree for a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Dictionary representing dependency tree
        """
        def build_tree(name: str, visited: Set[str] = None) -> Dict[str, Any]:
            if visited is None:
                visited = set()

            if name in visited:
                return {"name": name, "circular": True, "dependencies": {}}

            visited.add(name)

            deps = self._dependencies.get(name, [])
            tree = {
                "name": name,
                "dependencies": {}
            }

            for dep in deps:
                tree["dependencies"][dep] = build_tree(dep, visited.copy())

            return tree

        return build_tree(plugin_name)

    def get_all_dependencies(self, plugin_name: str) -> Set[str]:
        """Get all transitive dependencies for a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Set of all dependency names (direct and indirect)
        """
        all_deps = set()
        to_process = [plugin_name]
        processed = set()

        while to_process:
            current = to_process.pop(0)
            if current in processed:
                continue

            processed.add(current)
            deps = self._dependencies.get(current, [])

            for dep in deps:
                if dep not in all_deps:
                    all_deps.add(dep)
                    to_process.append(dep)

        return all_deps

    def clear_dependencies(self) -> None:
        """Clear all dependency information."""
        self._dependencies.clear()
        self._dependents.clear()
        self._resolutions.clear()
        self._resolved_order.clear()


def create_dependency_resolver() -> DependencyResolver:
    """Create a dependency resolver instance.

    Returns:
        DependencyResolver instance
    """
    return DependencyResolver()
