# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Network Capabilities Tool for NoDupeLabs.

Provides network and remote storage capabilities as a tool.
"""

from typing import Any, Callable

from nodupe.core.tool_system.base import Tool

from . import get_network_manager


class NetworkTool(Tool):
    """Network capabilities tool."""

    @property
    def name(self) -> str:
        return "network_tool"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            "upload_file": self.manager.upload_file,
            "download_file": self.manager.download_file,
            "list_files": self.manager.list_files,
            "delete_file": self.manager.delete_file,
        }

    def __init__(self):
        """Initialize the tool."""
        self.manager = get_network_manager()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service("network_manager", self.manager)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            "storage_backend": self.manager.storage_backend.__class__.__name__,
            "available": True,
        }


def register_tool():
    """Register the network tool."""
    return NetworkTool()
