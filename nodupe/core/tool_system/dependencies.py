"""Tool Dependencies Module.

Tool dependency management using standard library only.

Key Features:
    - Tool dependency resolution and ordering
    - Circular dependency detection
    - Dependency validation and conflict resolution
    - Topological sorting for initialization order
    - Standard library only (no external dependencies)

Dependencies:
    - typing (standard library)
    - enum (standard library)
"""

from enum import Enum
from typing import Any, Optional

from .base import Tool


class DependencyError(Exception):
    """Tool dependency error"""


class ResolutionStatus(Enum):
    """Dependency resolution status."""
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    CIRCULAR = "circular"
    MISSING = "missing"
    CONFLICT = "conflict"


class DependencyResolver:
    """Handle tool dependency resolution and management.

    Resolves tool dependencies, detects circular dependencies,
    and provides ordering for initialization.
    """

    def __init__(self):
        """Initialize dependency resolver."""
        self._dependencies: dict[str, list[str]] = {}
        self._dependents: dict[str, list[str]] = {}
        self._resolutions: dict[str, ResolutionStatus] = {}
        self._resolved_order: list[str] = []

    def check_dependency_graph(self, tools: list[str]) -> bool:
        """Check if the dependency graph is valid (no circular dependencies).

        Args:
            tools: List of tool names to check

        Returns:
            True if graph is valid
        """
        return not self._has_circular_dependency(tools)

    def add_dependency(self, tool_name: str, dependency_name: str) -> None:
        """Add a dependency relationship.

        Args:
            tool_name: Name of tool that depends on another
            dependency_name: Name of tool that is depended upon
        """
        if tool_name not in self._dependencies:
            self._dependencies[tool_name] = []
        if dependency_name not in self._dependencies[tool_name]:
            self._dependencies[tool_name].append(dependency_name)

        # Update reverse dependencies
        if dependency_name not in self._dependents:
            self._dependents[dependency_name] = []
        if tool_name not in self._dependents[dependency_name]:
            self._dependents[dependency_name].append(tool_name)

        # Reset resolution status when dependencies change
        self._resolutions.clear()
        self._resolved_order.clear()

    def remove_dependency(self, tool_name: str, dependency_name: str) -> bool:
        """Remove a dependency relationship.

        Args:
            tool_name: Name of tool that had dependency
            dependency_name: Name of dependency to remove

        Returns:
            True if dependency was removed, False if not found
        """
        if (tool_name in self._dependencies and
                dependency_name in self._dependencies[tool_name]):
            self._dependencies[tool_name].remove(dependency_name)

            # Update reverse dependencies
            if (dependency_name in self._dependents and
                    tool_name in self._dependents[dependency_name]):
                self._dependents[dependency_name].remove(tool_name)

            # Reset resolution status
            self._resolutions.clear()
            self._resolved_order.clear()
            return True

        return False

    def get_dependencies(self, tool_name: str) -> list[str]:
        """Get dependencies for a tool.

        Args:
            tool_name: Name of tool

        Returns:
            List of dependency names
        """
        return self._dependencies.get(tool_name, [])

    def get_dependents(self, tool_name: str) -> list[str]:
        """Get tools that depend on this tool.

        Args:
            tool_name: Name of tool

        Returns:
            List of dependent tool names
        """
        return self._dependents.get(tool_name, [])

    def resolve_dependencies(self, tools: list[str]) -> tuple[ResolutionStatus, list[str]]:
        """Resolve dependencies for a list of tools.

        Args:
            tools: List of tool names to resolve

        Returns:
            Tuple of (resolution status, ordered list of tools)
        """
        try:
            # Check for missing dependencies
            all_deps = set()
            for tool in tools:
                deps = set(self._dependencies.get(tool, []))
                all_deps.update(deps)

            missing = all_deps - set(tools)
            if missing:
                return ResolutionStatus.MISSING, []

            # Check for circular dependencies
            if self._has_circular_dependency(tools):
                return ResolutionStatus.CIRCULAR, []

            # Perform topological sort
            ordered_tools = self._topological_sort(tools)

            if not ordered_tools:
                return ResolutionStatus.UNRESOLVED, []

            return ResolutionStatus.RESOLVED, ordered_tools

        except Exception as e:
            raise DependencyError(f"Dependency resolution failed: {e}") from e

    def _has_circular_dependency(self, tools: list[str]) -> bool:
        """Check if there are circular dependencies among tools.

        Args:
            tools: List of tool names to check

        Returns:
            True if circular dependency exists
        """
        # Build dependency graph for the specific tools
        graph = {}
        tool_set = set(tools)

        for tool in tools:
            deps = [dep for dep in self._dependencies.get(tool, []) if dep in tool_set]
            graph[tool] = deps

        # Use DFS to detect cycles
        visiting = set()
        visited = set()

        def dfs(node: str) -> bool:
            """TODO: Document dfs."""
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

        return any(dfs(tool) for tool in tools)

    def _topological_sort(self, tools: list[str]) -> list[str]:
        """Perform topological sort to get dependency order.

        Args:
            tools: List of tool names to sort

        Returns:
            Ordered list of tool names, or empty list if cycle exists
        """
        if self._has_circular_dependency(tools):
            return []  # Cannot sort with circular dependencies

        # Build dependency graph
        graph = {}
        tool_set = set(tools)

        for tool in tools:
            deps = [dep for dep in self._dependencies.get(tool, []) if dep in tool_set]
            graph[tool] = deps

        # Perform topological sort using DFS
        result = []
        visited = set()
        temp_visited = set()

        def visit(node: str) -> bool:
            """TODO: Document visit."""
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

        for tool in tools:
            if tool not in visited and not visit(tool):
                return []  # Cycle detected

        return result

    def get_initialization_order(self, tools: list[str]) -> list[str]:
        """Get the correct initialization order for tools.

        Args:
            tools: List of tool names

        Returns:
            List of tool names in initialization order
        """
        status, order = self.resolve_dependencies(tools)
        if status == ResolutionStatus.RESOLVED:
            return order
        return []

    def get_shutdown_order(self, tools: list[str]) -> list[str]:
        """Get the correct shutdown order for tools (reverse of initialization).

        Args:
            tools: List of tool names

        Returns:
            List of tool names in shutdown order
        """
        init_order = self.get_initialization_order(tools)
        return list(reversed(init_order))

    def validate_tool_compatibility(
        self,
        tool: Tool,
        available_tools: list[str]
    ) -> tuple[bool, list[str]]:
        """Validate that a tool is compatible with available tools.

        Args:
            tool: Tool instance to validate
            available_tools: List of available tool names

        Returns:
            Tuple of (is_compatible, list_of_missing_dependencies)
        """
        required_deps = getattr(tool, 'dependencies', [])
        missing_deps = [dep for dep in required_deps if dep not in available_tools]

        return len(missing_deps) == 0, missing_deps

    def get_dependency_tree(self, tool_name: str) -> dict[str, Any]:
        """Get the dependency tree for a tool.

        Args:
            tool_name: Name of tool

        Returns:
            Dictionary representing dependency tree
        """
        def build_tree(name: str, visited: Optional[set[str]] = None) -> dict[str, Any]:
            """TODO: Document build_tree."""
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

        return build_tree(tool_name)

    def get_all_dependencies(self, tool_name: str) -> set[str]:
        """Get all transitive dependencies for a tool.

        Args:
            tool_name: Name of tool

        Returns:
            Set of all dependency names (direct and indirect)
        """
        all_deps = set()
        to_process = [tool_name]
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

# Alias for backward compatibility
ToolDependencyManager = DependencyResolver
