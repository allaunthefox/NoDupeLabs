# pylint: disable=logging-fstring-interpolation
"""
Tool Loading Order Management

This module defines explicit tool loading order and dependency management
to prevent cascading failures and ensure proper initialization sequence.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ToolLoadOrder(Enum):
    """Explicit tool loading order levels."""

    # Core infrastructure - must load first
    CORE_INFRASTRUCTURE = 1

    # System utilities - depend on core infrastructure
    SYSTEM_UTILITIES = 2

    # Database and storage - depend on system utilities
    STORAGE_SERVICES = 3

    # Processing and analysis - depend on storage
    PROCESSING_SERVICES = 4

    # User interface and commands - depend on processing
    UI_COMMANDS = 5

    # Specialized tools - depend on UI/commands
    SPECIALIZED_TOOLS = 6


@dataclass
class ToolLoadInfo:
    """Information about tool loading requirements."""

    name: str
    load_order: ToolLoadOrder
    required_dependencies: list[str]
    optional_dependencies: list[str]
    critical: bool = False  # If True, failure prevents loading other tools
    description: str = ""
    load_priority: int = (
        0  # Higher priority loads first within same order level
    )


class ToolLoadingError(Exception):
    """Exception raised when tool loading fails."""

    pass


class ToolDependencyError(ToolLoadingError):
    """Exception raised when tool dependencies cannot be resolved."""

    pass


class ToolLoadingOrder:
    """Manages explicit tool loading order and dependencies."""

    def __init__(self):
        """Initialize the tool loading order manager."""
        self._tool_info: dict[str, ToolLoadInfo] = {}
        self._load_order_groups: dict[ToolLoadOrder, list[str]] = {
            order: [] for order in ToolLoadOrder
        }
        self._dependency_graph: dict[str, set[str]] = {}
        self._reverse_dependencies: dict[str, set[str]] = {}
        self._load_callbacks: dict[str, list[Callable]] = defaultdict(list)

        # Initialize known tool order
        self._initialize_known_tools()

    def _initialize_known_tools(self):
        """Initialize known tool loading order and dependencies."""

        # Core Infrastructure (must load first)
        core_tools = [
            ToolLoadInfo(
                name="core",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=[],
                optional_dependencies=[],
                critical=True,
                description="Core system infrastructure",
            ),
            ToolLoadInfo(
                name="deps",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=[],
                optional_dependencies=[],
                critical=True,
                description="Dependency management",
            ),
            ToolLoadInfo(
                name="container",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "deps"],
                optional_dependencies=[],
                critical=True,
                description="Dependency injection container",
            ),
            ToolLoadInfo(
                name="registry",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "container"],
                optional_dependencies=[],
                critical=True,
                description="Tool registry",
            ),
            ToolLoadInfo(
                name="discovery",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "registry"],
                optional_dependencies=[],
                critical=True,
                description="Tool discovery",
            ),
            ToolLoadInfo(
                name="loader",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "registry", "discovery"],
                optional_dependencies=[],
                critical=True,
                description="Tool loader",
            ),
            ToolLoadInfo(
                name="security",
                load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core"],
                optional_dependencies=[],
                critical=True,
                description="Security services",
            ),
        ]

        # System Utilities (depend on core infrastructure)
        utility_tools = [
            ToolLoadInfo(
                name="config",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "container"],
                optional_dependencies=["security"],
                critical=False,
                description="Configuration management",
            ),
            ToolLoadInfo(
                name="logging",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "config"],
                optional_dependencies=[],
                critical=False,
                description="Logging services",
            ),
            ToolLoadInfo(
                name="limits",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "config"],
                optional_dependencies=[],
                critical=False,
                description="System limits",
            ),
            ToolLoadInfo(
                name="parallel",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "limits"],
                optional_dependencies=[],
                critical=False,
                description="Parallel processing",
            ),
            ToolLoadInfo(
                name="pools",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "parallel"],
                optional_dependencies=[],
                critical=False,
                description="Resource pools",
            ),
            ToolLoadInfo(
                name="cache",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "pools"],
                optional_dependencies=[],
                critical=False,
                description="Caching services",
            ),
            ToolLoadInfo(
                name="time_sync",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "cache"],
                optional_dependencies=["security"],
                critical=False,
                description="Time synchronization",
            ),
            ToolLoadInfo(
                name="leap_year",
                load_order=ToolLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core"],
                optional_dependencies=[],
                critical=False,
                description="Leap year calculations",
            ),
        ]

        # Storage Services (depend on system utilities)
        storage_tools = [
            ToolLoadInfo(
                name="database",
                load_order=ToolLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "config", "security", "limits"],
                optional_dependencies=["cache", "time_sync"],
                critical=True,
                description="Database services",
            ),
            ToolLoadInfo(
                name="filesystem",
                load_order=ToolLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "limits"],
                optional_dependencies=["cache"],
                critical=False,
                description="File system operations",
            ),
            ToolLoadInfo(
                name="compression",
                load_order=ToolLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "filesystem"],
                optional_dependencies=[],
                critical=False,
                description="Compression utilities",
            ),
            ToolLoadInfo(
                name="mime_detection",
                load_order=ToolLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "filesystem"],
                optional_dependencies=[],
                critical=False,
                description="MIME type detection",
            ),
        ]

        # Processing Services (depend on storage)
        processing_tools = [
            ToolLoadInfo(
                name="scan",
                load_order=ToolLoadOrder.PROCESSING_SERVICES,
                required_dependencies=[
                    "core",
                    "filesystem",
                    "limits",
                    "parallel",
                ],
                optional_dependencies=["mime_detection", "compression"],
                critical=False,
                description="File scanning",
            ),
            ToolLoadInfo(
                name="incremental",
                load_order=ToolLoadOrder.PROCESSING_SERVICES,
                required_dependencies=["core", "database", "scan"],
                optional_dependencies=["time_sync"],
                critical=False,
                description="Incremental processing",
            ),
            ToolLoadInfo(
                name="hash_autotune",
                load_order=ToolLoadOrder.PROCESSING_SERVICES,
                required_dependencies=["core", "limits", "parallel"],
                optional_dependencies=[],
                critical=False,
                description="Hash autotuning",
            ),
        ]

        # UI/Commands (depend on processing)
        ui_tools = [
            ToolLoadInfo(
                name="cli",
                load_order=ToolLoadOrder.UI_COMMANDS,
                required_dependencies=["core", "config", "logging"],
                optional_dependencies=["database", "scan"],
                critical=False,
                description="Command line interface",
            ),
            ToolLoadInfo(
                name="commands",
                load_order=ToolLoadOrder.UI_COMMANDS,
                required_dependencies=["core", "cli", "database"],
                optional_dependencies=["scan", "incremental"],
                critical=False,
                description="Command implementations",
            ),
        ]

        # Specialized Tools (depend on UI/commands)
        specialized_tools = [
            ToolLoadInfo(
                name="similarity",
                load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan", "incremental"],
                critical=False,
                description="Similarity detection",
            ),
            ToolLoadInfo(
                name="apply",
                load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan"],
                critical=False,
                description="Apply operations",
            ),
            ToolLoadInfo(
                name="scan_command",
                load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
                required_dependencies=["core", "commands", "scan"],
                optional_dependencies=["database"],
                critical=False,
                description="Scan command",
            ),
            ToolLoadInfo(
                name="verify",
                load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan"],
                critical=False,
                description="Verification tools",
            ),
            ToolLoadInfo(
                name="plan",
                load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan"],
                critical=False,
                description="Plan operations",
            ),
        ]

        # Register all tools
        all_tools = (
            core_tools
            + utility_tools
            + storage_tools
            + processing_tools
            + ui_tools
            + specialized_tools
        )

        for tool_info in all_tools:
            self.register_tool(tool_info)

    def register_tool(self, tool_info: ToolLoadInfo) -> None:
        """Register a tool with its loading requirements.

        Args:
            tool_info: Tool loading information
        """
        self._tool_info[tool_info.name] = tool_info
        self._load_order_groups[tool_info.load_order].append(tool_info.name)

        # Build dependency graph
        self._dependency_graph[tool_info.name] = set(
            tool_info.required_dependencies
        )
        self._reverse_dependencies[tool_info.name] = set()

        # Update reverse dependencies
        for dep in tool_info.required_dependencies:
            if dep not in self._reverse_dependencies:
                self._reverse_dependencies[dep] = set()
            self._reverse_dependencies[dep].add(tool_info.name)

    def get_load_order(self) -> list[ToolLoadOrder]:
        """Get the tool loading order levels.

        Returns:
            List of load order levels in sequence
        """
        return list(ToolLoadOrder)

    def get_tools_for_order(self, order: ToolLoadOrder) -> list[str]:
        """Get tools that should be loaded at a specific order level.

        Args:
            order: Load order level

        Returns:
            List of tool names for this order level
        """
        return self._load_order_groups.get(order, [])

    def get_required_dependencies(self, tool_name: str) -> list[str]:
        """Get required dependencies for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of required dependency names
        """
        if tool_name not in self._tool_info:
            return []
        return self._tool_info[tool_name].required_dependencies

    def get_optional_dependencies(self, tool_name: str) -> list[str]:
        """Get optional dependencies for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of optional dependency names
        """
        if tool_name not in self._tool_info:
            return []
        return self._tool_info[tool_name].optional_dependencies

    def is_critical(self, tool_name: str) -> bool:
        """Check if a tool is critical (failure prevents other tools).

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is critical
        """
        if tool_name not in self._tool_info:
            return False
        return self._tool_info[tool_name].critical

    def get_tool_info(self, tool_name: str) -> Optional[ToolLoadInfo]:
        """Get tool loading information.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolLoadInfo if found, None otherwise
        """
        return self._tool_info.get(tool_name)

    def validate_dependencies(
        self, tool_name: str, available_tools: set[str]
    ) -> tuple[bool, list[str]]:
        """Validate that all required dependencies are available.

        Args:
            tool_name: Name of the tool to validate
            available_tools: Set of currently available tools

        Returns:
            Tuple of (is_valid, missing_dependencies)
        """
        if tool_name not in self._tool_info:
            return True, []

        required_deps = set(self._tool_info[tool_name].required_dependencies)
        missing = required_deps - available_tools

        return len(missing) == 0, list(missing)

    def get_load_sequence(self, tool_names: list[str]) -> list[str]:
        """Get the optimal loading sequence for a set of tools.

        Args:
            tool_names: List of tool names to load

        Returns:
            Ordered list of tool names for loading (includes dependencies)
        """
        # Build complete set including all dependencies
        all_required = set(tool_names)

        # Add all dependencies recursively
        for tool_name in tool_names:
            if tool_name in self._tool_info:
                deps = self.get_dependency_chain(tool_name)
                all_required.update(deps)

        # Build dependency graph for all required tools
        requested_set = all_required
        load_sequence = []
        visited = set()
        temp_mark = set()

        def visit(node: str) -> None:
            """TODO: Document visit."""
            if node in temp_mark:
                raise ValueError(
                    f"Circular dependency detected involving {node}"
                )

            if node not in visited:
                temp_mark.add(node)

                # Visit dependencies first
                if node in self._dependency_graph:
                    for dep in self._dependency_graph[node]:
                        if dep in requested_set:
                            visit(dep)

                temp_mark.remove(node)
                visited.add(node)
                load_sequence.append(node)

        # Sort tools by load order first, then process
        tools_by_order = {}
        for tool_name in requested_set:
            if tool_name in self._tool_info:
                order = self._tool_info[tool_name].load_order
                if order not in tools_by_order:
                    tools_by_order[order] = []
                tools_by_order[order].append(tool_name)

        # Process in load order
        for order in self.get_load_order():
            if order in tools_by_order:
                for tool_name in tools_by_order[order]:
                    visit(tool_name)

        return load_sequence

    def get_critical_tools(self) -> list[str]:
        """Get all critical tools that must load successfully.

        Returns:
            List of critical tool names
        """
        return [name for name, info in self._tool_info.items() if info.critical]

    def get_tool_description(self, tool_name: str) -> str:
        """Get tool description.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool description
        """
        if tool_name in self._tool_info:
            return self._tool_info[tool_name].description
        return "Unknown tool"

    def get_dependency_chain(self, tool_name: str) -> list[str]:
        """Get the full dependency chain for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of dependencies in loading order
        """
        chain = []
        visited = set()

        def add_deps(name: str) -> None:
            """TODO: Document add_deps."""
            if name in visited:
                return
            visited.add(name)

            if name in self._dependency_graph:
                for dep in self._dependency_graph[name]:
                    add_deps(dep)

            if name in self._tool_info:
                chain.append(name)

        add_deps(tool_name)
        return chain[:-1]  # Remove the tool itself, return only dependencies

    def validate_load_sequence(
        self, tool_names: list[str]
    ) -> tuple[bool, list[str], list[str]]:
        """Validate a complete tool load sequence for dependencies and conflicts.

        Args:
            tool_names: List of tool names to load

        Returns:
            Tuple of (is_valid, missing_dependencies, circular_dependencies)
        """
        missing_deps = []
        circular_deps = []

        # Check for circular dependencies
        try:
            self.get_load_sequence(tool_names)
        except ValueError as e:
            if "Circular dependency" in str(e):
                circular_deps.append(str(e))

        # Check all dependencies are available
        for tool_name in tool_names:
            if tool_name in self._tool_info:
                required_deps = self._tool_info[tool_name].required_dependencies
                for dep in required_deps:
                    if dep not in tool_names:
                        missing_deps.append(f"{tool_name} requires {dep}")

        return (
            len(missing_deps) == 0 and len(circular_deps) == 0,
            missing_deps,
            circular_deps,
        )

    def get_safe_load_sequence(
        self, tool_names: list[str]
    ) -> tuple[list[str], list[str]]:
        """Get a safe loading sequence that handles failures gracefully.

        Args:
            tool_names: List of tool names to load

        Returns:
            Tuple of (safe_sequence, excluded_tools_due_to_missing_deps)
        """
        # First, get the optimal sequence
        try:
            optimal_sequence = self.get_load_sequence(tool_names)
        except ValueError:
            # If there are circular dependencies, fall back to simple ordering
            optimal_sequence = self._fallback_load_sequence(tool_names)

        # Group by load order and criticality
        safe_sequence = []
        excluded = []

        # Process by load order levels
        for order in self.get_load_order():
            order_tools = [
                p
                for p in optimal_sequence
                if p in self._load_order_groups[order]
            ]

            # Separate critical and non-critical tools
            critical_tools = [p for p in order_tools if self.is_critical(p)]
            non_critical_tools = [
                p for p in order_tools if not self.is_critical(p)
            ]

            # Load critical tools first (they must succeed)
            safe_sequence.extend(critical_tools)

            # Load non-critical tools after critical ones
            safe_sequence.extend(non_critical_tools)

        # Check for missing dependencies and exclude tools that can't load
        available_for_validation = set(safe_sequence)
        for tool_name in list(safe_sequence):
            is_valid, missing = self.validate_dependencies(
                tool_name, available_for_validation - {tool_name}
            )
            if not is_valid:
                safe_sequence.remove(tool_name)
                excluded.append(f"{tool_name} (missing: {', '.join(missing)})")

        return safe_sequence, excluded

    def _fallback_load_sequence(self, tool_names: list[str]) -> list[str]:
        """Fallback sequence generator when optimal fails."""
        # Sort by load order, then by name for deterministic ordering
        sorted_tools = sorted(
            tool_names,
            key=lambda name: (
                self._tool_info.get(
                    name,
                    ToolLoadInfo(
                        name, ToolLoadOrder.CORE_INFRASTRUCTURE, [], []
                    ),
                ).load_order.value,
                name,
            ),
        )
        return sorted_tools

    def get_failure_impact_analysis(
        self, failed_tool: str, loaded_tools: list[str]
    ) -> dict[str, list[str]]:
        """Analyze the impact of a tool failure on other tools.

        Args:
            failed_tool: Name of the failed tool
            loaded_tools: List of tools that have been loaded

        Returns:
            Dict mapping tool names to lists of affected dependencies
        """
        impact = {}

        # Find tools that depend on the failed tool
        for tool_name in loaded_tools:
            if tool_name == failed_tool:
                continue

            if tool_name in self._tool_info:
                deps = self._tool_info[tool_name].required_dependencies
                if failed_tool in deps:
                    if failed_tool not in impact:
                        impact[failed_tool] = []
                    impact[failed_tool].append(tool_name)

        return impact

    def should_continue_loading(
        self, failed_tool: str, loaded_tools: list[str]
    ) -> tuple[bool, str]:
        """Determine if loading should continue after a tool failure.

        Args:
            failed_tool: Name of the failed tool
            loaded_tools: List of tools that have been loaded

        Returns:
            Tuple of (should_continue, reason)
        """
        if not self.is_critical(failed_tool):
            return True, f"Non-critical tool {failed_tool} failed, continuing"

        # Critical tool failed - always stop loading
        return (
            False,
            f"Critical tool {failed_tool} failed, stopping loading sequence",
        )

    def get_load_priorities(
        self, tool_names: list[str]
    ) -> list[tuple[str, int]]:
        """Get loading priorities for tools based on dependencies and criticality.

        Args:
            tool_names: List of tool names

        Returns:
            List of (tool_name, priority) tuples sorted by priority (higher = loads first)
        """
        priorities = []

        for tool_name in tool_names:
            if tool_name not in self._tool_info:
                continue

            info = self._tool_info[tool_name]

            # Base priority on load order (lower order = higher priority)
            base_priority = (6 - info.load_order.value) * 100

            # Add criticality bonus
            critical_bonus = 50 if info.critical else 0

            # Add dependency count bonus (tools with more dependents should load first)
            dependency_bonus = (
                len(self._reverse_dependencies.get(tool_name, set())) * 10
            )

            # Add configured priority
            configured_priority = info.load_priority

            total_priority = (
                base_priority
                + critical_bonus
                + dependency_bonus
                + configured_priority
            )
            priorities.append((tool_name, total_priority))

        # Sort by priority descending
        priorities.sort(key=lambda x: x[1], reverse=True)
        return priorities

    def register_load_callback(
        self, tool_name: str, callback: Callable
    ) -> None:
        """Register a callback to be called when a tool is loaded.

        Args:
            tool_name: Name of the tool
            callback: Function to call when tool loads
        """
        self._load_callbacks[tool_name].append(callback)

    def notify_tool_loaded(self, tool_name: str) -> None:
        """Notify all callbacks that a tool has been loaded.

        Args:
            tool_name: Name of the loaded tool
        """
        for callback in self._load_callbacks.get(tool_name, []):
            try:
                callback(tool_name)
            except Exception as e:
                logger.exception(f"Error in load callback for {tool_name}: {e}")

    def get_tool_statistics(self) -> dict[str, Any]:
        """Get statistics about the tool loading order configuration.

        Returns:
            Dict containing tool statistics
        """
        stats = {
            "total_tools": len(self._tool_info),
            "tools_by_order": {},
            "critical_tools": self.get_critical_tools(),
            "dependency_counts": {},
            "tools_with_optional_deps": [],
        }

        # Count tools by order
        for order in self.get_load_order():
            stats["tools_by_order"][order.name] = len(
                self.get_tools_for_order(order)
            )

        # Count dependencies
        for tool_name, deps in self._dependency_graph.items():
            stats["dependency_counts"][tool_name] = len(deps)

        # Find tools with optional dependencies
        for tool_name, info in self._tool_info.items():
            if info.optional_dependencies:
                stats["tools_with_optional_deps"].append(tool_name)

        return stats


# Global tool loading order instance
_global_loading_order = None


def get_tool_loading_order() -> ToolLoadingOrder:
    """Get the global tool loading order instance.

    Returns:
        ToolLoadingOrder instance
    """
    global _global_loading_order
    if _global_loading_order is None:
        _global_loading_order = ToolLoadingOrder()
    return _global_loading_order


def reset_tool_loading_order():
    """Reset the global tool loading order instance."""
    global _global_loading_order
    _global_loading_order = ToolLoadingOrder()
