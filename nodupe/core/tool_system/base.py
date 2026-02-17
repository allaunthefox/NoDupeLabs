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
    license: str      # SPDX License Identifier (RFC standard)
    dependencies: list[str]
    tags: list[str]
    persistent_id: Optional[str] = None
    entitlement_key: Optional[str] = None


class Tool(ABC):
    """Abstract base class for all NoDupeLabs tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""

    @property
    @abstractmethod
    def version(self) -> str:
        """Tool version"""

    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """List of tool dependencies"""

    @abstractmethod
    def initialize(self, container: Any) -> None:
        """Initialize the tool"""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the tool"""

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities"""

    @property
    @abstractmethod
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        """Dictionary of methods exposed via programmatic API (Socket/IPC)"""

    @abstractmethod
    def run_standalone(self, args: list[str]) -> int:
        """Execute the tool in stand-alone mode without the core engine."""

    @abstractmethod
    def describe_usage(self) -> str:
        """Return human-readable, jargon-free instructions for this component.
        """


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
