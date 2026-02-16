# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tool Registry.

Singleton registry for managing system tools (formerly tools).
"""

from typing import List, Optional, Any
from .base import Tool


class ToolRegistry:
    """Singleton registry for managing system tools."""

    _instance: Optional['ToolRegistry'] = None
    _tools: dict[str, Tool]
    _initialized: bool
    _container: Any

    def __new__(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        # Check for accessibility compliance before registering
        from .api.codes import ActionCode
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if the tool implements accessibility features
        from .base import AccessibleTool
        if isinstance(tool, AccessibleTool):
            logger.info(f"[{ActionCode.ACC_ISO_CMP}] Registering ISO accessibility compliant tool: {tool.name}")
        else:
            logger.info(f"[{ActionCode.ACC_FEATURE_DISABLED}] Registering tool without accessibility features: {tool.name}")

        self._tools[tool.name] = tool
        if hasattr(self, '_container') and self._container:
            tool.initialize(self._container)

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name not in self._tools:
            raise KeyError(f"Tool {name} not found")

        tool = self._tools[name]
        tool.shutdown()
        del self._tools[name]

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()

    def shutdown(self) -> None:
        """Shutdown all tools."""
        for tool in self._tools.values():
            try:
                tool.shutdown()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error shutting down tool {tool.name}: {e}")

        self._tools.clear()
        self._container = None
        self._initialized = False

    def initialize(self, container: Any) -> None:
        """Initialize the registry with a dependency container."""
        self._container = container
        self._initialized = True

    @property
    def container(self):
        """Get the service container."""
        return getattr(self, '_container', None)

    @classmethod
    def _reset_instance(cls):
        """Reset the singleton instance (primarily for testing)."""
        cls._instance = None
