# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tool Base Class.

Abstract base class for all system tools (formerly tools).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ToolMetadata:
    """Metadata for a tool (ISO 19770-2 / SWID tag compliant)."""

    name: str
    version: str
    software_id: str  # SWID Tag ID (e.g. org.nodupe.tool.name)
    description: str
    author: str
    license: str  # SPDX License Identifier (RFC standard)
    dependencies: list[str]
    tags: list[str]
    persistent_id: Optional[str] = None
    entitlement_key: Optional[str] = None


class Tool(ABC):
    """Abstract base class for all NoDupeLabs tools"""

    @property
    def name(self) -> str:
        """Tool name.

        Default implementation reads instance attribute `name` when present so
        legacy test/tool subclasses that set `self.name` in __init__ continue
        to work. Subclasses SHOULD override this to provide a static property.
        """
        # Allow instance attribute fallback for backwards compatibility
        name_attr = self.__dict__.get("name")
        if isinstance(name_attr, str) and name_attr:
            return name_attr
        raise NotImplementedError("Tool subclasses must provide a `name`")

    @name.setter
    def name(self, value: str) -> None:
        """Allow tests and legacy code to set `self.name` in __init__."""
        if not isinstance(value, str):
            raise TypeError("Tool.name must be a string")
        self.__dict__["name"] = value

    @property
    def version(self) -> str:
        """Tool version.

        Default implementation reads instance attribute `version` when present.
        """
        version_attr = self.__dict__.get("version")
        if isinstance(version_attr, str) and version_attr:
            return version_attr
        raise NotImplementedError("Tool subclasses must provide a `version`")

    @version.setter
    def version(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Tool.version must be a string")
        self.__dict__["version"] = value

    @property
    def dependencies(self) -> list[str]:
        """List of tool dependencies.

        Default implementation reads instance attribute `dependencies` if set,
        otherwise returns an empty list.
        """
        deps = self.__dict__.get("dependencies")
        if isinstance(deps, list):
            return deps
        return []

    @dependencies.setter
    def dependencies(self, value: list[str]) -> None:
        if not isinstance(value, list):
            raise TypeError("Tool.dependencies must be a list")
        self.__dict__["dependencies"] = value

    def initialize(self, container: Any = None) -> None:
        """Initialize the tool.

        Default no-op implementation is provided for backwards compatibility so
        test stubs that don't implement `initialize` can still be instantiated.
        Subclasses SHOULD override this to perform real initialization.
        """
        return None

    def shutdown(self, container: Any = None) -> None:
        """Shutdown the tool.

        Default no-op implementation; subclasses SHOULD override to cleanup
        resources when necessary.
        """
        return None

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities.

        Default implementation returns an empty capabilities mapping.
        """
        return {}

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        """Dictionary of methods exposed via programmatic API (Socket/IPC).

        Default implementation returns an empty mapping so legacy Tool
        subclasses that don't expose programmatic methods continue to work.
        """
        return {}

    def run_standalone(self, args: list[str]) -> int:
        """Execute the tool in stand-alone mode without the core engine.

        Default implementation returns 0 to allow simple tools to be
        instantiated in tests without providing a CLI entrypoint.
        """
        return 0

    def describe_usage(self) -> str:
        """Return human-readable, jargon-free instructions for this component.

        Default implementation returns an empty string.
        """
        return ""

# Note: The full AccessibleTool implementation is in accessible_base.py
# This is just the interface definition
class AccessibleTool(Tool):
    """
    Abstract base class for accessible tools that support users with visual impairments.

    This class extends the basic Tool interface with accessibility features that
    support assistive technologies like screen readers and braille displays.

    **CRITICAL REQUIREMENT**: Accessibility is a core requirement, not optional.
    All implementations MUST provide basic accessibility through console output
    even if external accessibility libraries are not available.
    """

    def announce_to_assistive_tech(self, message: str, interrupt: bool = True):
        """
        Announce a message to assistive technologies when available.

        Args:
            message: The message to announce
            interrupt: Whether to interrupt current speech (default True)
        """
        pass

    def format_for_accessibility(self, data: Any) -> str:
        """
        Format data for accessibility with screen readers and braille displays.

        Args:
            data: Data to format for accessibility

        Returns:
            String formatted for accessibility
        """
        pass

    def get_ipc_socket_documentation(self) -> dict[str, Any]:
        """
        Document IPC socket interfaces for assistive technology integration.

        Returns:
            Dictionary describing available IPC endpoints and their accessibility features
        """
        pass

    def get_accessible_status(self) -> str:
        """
        Get tool status in an accessible format.

        Returns:
            Human-readable status information suitable for screen readers
        """
        pass

    def log_accessible_message(self, message: str, level: str = "info"):
        """
        Log a message with accessibility consideration.

        Args:
            message: The message to log
            level: The logging level ('info', 'warning', 'error', 'debug')
        """
        pass
