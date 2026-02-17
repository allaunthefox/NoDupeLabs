# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Machine Learning Tool for NoDupeLabs.

Provides ML capabilities as a tool.
"""

from typing import Any, Callable

from nodupe.core.tool_system.base import Tool

from . import get_ml_backend


class MLTool(Tool):
    """Machine learning capabilities tool."""

    @property
    def name(self) -> str:
        return "ml_tool"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            'generate_embeddings': self.backend.generate_embeddings,
            'get_dimensions': self.backend.get_embedding_dimensions,
            'is_available': self.backend.is_available
        }

    def __init__(self):
        """Initialize the tool."""
        self.backend = get_ml_backend()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service('ml_backend', self.backend)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            'dimensions': self.backend.get_embedding_dimensions(),
            'available': self.backend.is_available()
        }

def register_tool():
    """Register the ML tool."""
    return MLTool()
