# pylint: disable=logging-fstring-interpolation
"""Tool Lifecycle Module.

Tool lifecycle management using standard library only.

Key Features:
    - Tool initialization and shutdown
    - Dependency resolution and ordering
    - Graceful error handling
    - Standard library only (no external dependencies)

Dependencies:
    - typing (standard library)
    - enum (standard library)
"""

import logging
from enum import Enum
from typing import Any, Optional

from ..api.codes import ActionCode
from .base import Tool
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolLifecycleError(Exception):
    """Tool lifecycle error"""


class ToolState(Enum):
    """Tool lifecycle states."""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class ToolLifecycleManager:
    """Handle tool lifecycle management.

    Manages tool initialization, shutdown, and dependency resolution.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        """Initialize lifecycle manager.

        Args:
            registry: Tool registry instance
        """
        self.registry = registry or ToolRegistry()
        self._tool_states: dict[str, ToolState] = {}
        self._tool_dependencies: dict[str, list[str]] = {}
        self._tool_containers: dict[str, Any] = {}
        self.container = None

    def initialize(self, container: Any) -> None:
        """Initialize lifecycle manager with container.

        Args:
            container: Dependency container instance
        """
        self.container = container

    def initialize_tools(self, tools: list[Tool]) -> None:
        """Initialize multiple tools.

        Args:
            tools: List of tool instances to initialize
        """
        for tool in tools:
            self.initialize_tool(tool, self.container)

    def initialize_tool(
        self,
        tool: Tool,
        container: Any,
        dependencies: Optional[list[str]] = None,
    ) -> bool:
        """Initialize a tool with dependency resolution.

        Args:
            tool: Tool instance to initialize
            container: Dependency injection container
            dependencies: Optional list of tool dependencies

        Returns:
            True if initialization successful

        Raises:
            ToolLifecycleError: If initialization fails
        """
        try:
            tool_name = tool.name

            # Check if tool is already initialized
            current_state = self._tool_states.get(tool_name, ToolState.UNLOADED)
            if current_state == ToolState.INITIALIZED:
                return True  # Already initialized

            # Set state to initializing
            self._tool_states[tool_name] = ToolState.INITIALIZING
            logger.info(
                f"[{ActionCode.FIA_UAU_INIT}] Initializing tool: {tool_name}"
            )

            # Store dependencies if provided
            if dependencies is not None:
                self._tool_dependencies[tool_name] = dependencies

            # Check dependency availability
            if not self._check_dependencies(tool_name):
                self._tool_states[tool_name] = ToolState.ERROR
                raise ToolLifecycleError(
                    f"Dependencies not satisfied for tool {tool_name}"
                )

            # Store container reference
            self._tool_containers[tool_name] = container

            # Check for accessibility compliance before initialization
            from .base import AccessibleTool

            if isinstance(tool, AccessibleTool):
                logger.info(
                    f"[{ActionCode.ACC_ISO_CMP}] Initializing ISO accessibility compliant tool: {tool_name}"
                )
            else:
                logger.info(
                    f"[{ActionCode.ACC_FEATURE_DISABLED}] Initializing tool without accessibility features: {tool_name}"
                )

            # Initialize the tool
            tool.initialize(container)

            # Set state to initialized
            self._tool_states[tool_name] = ToolState.INITIALIZED
            logger.info(
                f"[{ActionCode.FIA_UAU_INIT}] Tool initialized successfully: {tool_name}"
            )

            return True

        except Exception as e:
            self._tool_states[tool_name] = ToolState.ERROR
            logger.exception(
                f"[{ActionCode.FPT_STM_ERR}] Failed to initialize tool {tool_name}: {e}"
            )
            if isinstance(e, ToolLifecycleError):
                raise
            raise ToolLifecycleError(
                f"Failed to initialize tool {tool_name}: {e}"
            ) from e

    def shutdown_tools(self, tools: list[Tool]) -> None:
        """Shutdown multiple tools.

        Args:
            tools: List of tool instances to shutdown
        """
        for tool in tools:
            self.shutdown_tool(tool.name)

    def shutdown_tool(self, tool_name: str) -> bool:
        """Shutdown a tool.

        Args:
            tool_name: Name of tool to shutdown

        Returns:
            True if shutdown successful, False if tool not found
        """
        try:
            # Check if tool exists
            tool = self.registry.get_tool(tool_name)
            if tool is None:
                return False

            current_state = self._tool_states.get(tool_name, ToolState.UNLOADED)
            if current_state in [ToolState.SHUTDOWN, ToolState.UNLOADED]:
                return True  # Already shutdown

            # Set state to shutting down
            self._tool_states[tool_name] = ToolState.SHUTTING_DOWN
            logger.info(
                f"[{ActionCode.FIA_UAU_SHUTDOWN}] Shutting down tool: {tool_name}"
            )

            # Check for accessibility compliance during shutdown
            from .base import AccessibleTool

            if isinstance(tool, AccessibleTool):
                logger.info(
                    f"[{ActionCode.ACC_ISO_CMP}] Shutting down ISO accessibility compliant tool: {tool_name}"
                )
            else:
                logger.info(
                    f"[{ActionCode.ACC_FEATURE_DISABLED}] Shutting down tool without accessibility features: {tool_name}"
                )

            # Shutdown the tool
            try:
                tool.shutdown()
            except Exception as e:
                # Log error but continue
                logger.warning(
                    f"[{ActionCode.ERR_INTERNAL}] Error shutting down tool {tool_name}: {e}"
                )

            # Clean up state
            self._tool_states[tool_name] = ToolState.SHUTDOWN
            self._tool_containers.pop(tool_name, None)
            logger.info(
                f"[{ActionCode.FIA_UAU_SHUTDOWN}] Tool shutdown complete: {tool_name}"
            )

            return True

        except Exception as e:
            self._tool_states[tool_name] = ToolState.ERROR
            logger.exception(
                f"[{ActionCode.FPT_STM_ERR}] Failed to shutdown tool {tool_name}: {e}"
            )
            raise ToolLifecycleError(
                f"Failed to shutdown tool {tool_name}: {e}"
            ) from e

    def initialize_all_tools(self, container: Any) -> bool:
        """Initialize all registered tools with dependency resolution.

        Args:
            container: Dependency injection container

        Returns:
            True if all tools initialized successfully

        Raises:
            ToolLifecycleError: If any tool fails to initialize
        """
        try:
            # Get all tools from registry
            tools = self.registry.get_tools()

            # Sort tools by dependency order
            ordered_tools = self._sort_tools_by_dependencies(tools)

            # Initialize each tool
            for tool in ordered_tools:
                if not self.initialize_tool(tool, container):
                    raise ToolLifecycleError(
                        f"Failed to initialize tool {tool.name}"
                    )

            return True

        except Exception as e:
            if isinstance(e, ToolLifecycleError):
                raise
            raise ToolLifecycleError(
                f"Failed to initialize all tools: {e}"
            ) from e

    def shutdown_all_tools(self) -> bool:
        """Shutdown all initialized tools.

        Returns:
            True if all tools shutdown successfully
        """
        try:
            # Get all tools from registry
            tools = self.registry.get_tools()

            # Shutdown in reverse dependency order
            for tool in reversed(tools):
                try:
                    self.shutdown_tool(tool.name)
                except ToolLifecycleError:
                    # Continue shutting down other tools even if one fails
                    continue

            return True

        except Exception as e:
            raise ToolLifecycleError(
                f"Failed to shutdown all tools: {e}"
            ) from e

    def get_tool_states(self) -> dict[str, ToolState]:
        """Get all tool states.

        Returns:
            Dictionary of tool name to state
        """
        return self._tool_states.copy()

    def get_tool_state(self, tool_name: str) -> ToolState:
        """Get the current state of a tool.

        Args:
            tool_name: Name of tool

        Returns:
            Current tool state
        """
        return self._tool_states.get(tool_name, ToolState.UNLOADED)

    def is_tool_initialized(self, tool_name: str) -> bool:
        """Check if a tool is initialized.

        Args:
            tool_name: Name of tool

        Returns:
            True if tool is initialized
        """
        return (
            self._tool_states.get(tool_name, ToolState.UNLOADED)
            == ToolState.INITIALIZED
        )

    def is_tool_active(self, tool_name: str) -> bool:
        """Check if a tool is active (loaded and initialized).

        Args:
            tool_name: Name of tool

        Returns:
            True if tool is active
        """
        state = self._tool_states.get(tool_name, ToolState.UNLOADED)
        return state in [ToolState.INITIALIZED, ToolState.INITIALIZING]

    def get_active_tools(self) -> list[str]:
        """Get list of active tool names.

        Returns:
            List of active tool names
        """
        return [
            name
            for name, state in self._tool_states.items()
            if state in [ToolState.INITIALIZED, ToolState.INITIALIZING]
        ]

    def get_tool_dependencies(self, tool_name: str) -> list[str]:
        """Get dependencies for a tool.

        Args:
            tool_name: Name of tool

        Returns:
            List of dependency tool names
        """
        return self._tool_dependencies.get(tool_name, [])

    def set_tool_dependencies(
        self, tool_name: str, dependencies: list[str]
    ) -> None:
        """Set dependencies for a tool.

        Args:
            tool_name: Name of tool
            dependencies: List of dependency tool names
        """
        self._tool_dependencies[tool_name] = dependencies

    def _check_dependencies(self, tool_name: str) -> bool:
        """Check if all dependencies for a tool are satisfied.

        Args:
            tool_name: Name of tool

        Returns:
            True if all dependencies are satisfied
        """
        dependencies = self._tool_dependencies.get(tool_name, [])

        for dep_name in dependencies:
            dep_state = self._tool_states.get(dep_name, ToolState.UNLOADED)
            if dep_state != ToolState.INITIALIZED:
                return False

        return True

    def _sort_tools_by_dependencies(self, tools: list[Tool]) -> list[Tool]:
        """Sort tools by dependency order (topological sort).

        Args:
            tools: List of tools to sort

        Returns:
            List of tools sorted by dependency order
        """
        # Build dependency graph
        graph = {}
        tool_names = {tool.name: tool for tool in tools}

        for tool in tools:
            deps = self._tool_dependencies.get(tool.name, [])
            # Only include dependencies that are in our tool list
            graph[tool.name] = [dep for dep in deps if dep in tool_names]

        # Topological sort
        result = []
        visited = set()
        temp_visited = set()

        def visit(node):
            """TODO: Document visit."""
            if node in temp_visited:
                raise ToolLifecycleError(
                    f"Circular dependency detected: {node}"
                )
            if node not in visited:
                temp_visited.add(node)
                for dep in graph.get(node, []):
                    visit(dep)
                temp_visited.remove(node)
                visited.add(node)
                result.append(tool_names[node])

        for tool in tools:
            if tool.name not in visited:
                visit(tool.name)

        return result


def create_lifecycle_manager(
    registry: Optional[ToolRegistry] = None,
) -> ToolLifecycleManager:
    """Create a tool lifecycle manager instance.

    Args:
        registry: Optional tool registry instance

    Returns:
        ToolLifecycleManager instance
    """
    return ToolLifecycleManager(registry)
