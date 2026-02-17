# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Video Processing Tool for NoDupeLabs.

Provides video analysis capabilities as a tool.
"""

from typing import Any, Callable

from nodupe.core.tool_system.base import Tool

from . import get_video_backend_manager


class VideoTool(Tool):
    """Video processing capabilities tool."""

    @property
    def name(self) -> str:
        return "video_tool"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            "extract_frames": self.manager.extract_frames,
            "get_metadata": self.manager.get_video_metadata,
            "compute_phash": self.manager.compute_perceptual_hash,
        }

    def __init__(self):
        """Initialize the tool."""
        self.manager = get_video_backend_manager()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service("video_manager", self.manager)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            "backends": [b.__class__.__name__ for b in self.manager.backends],
            "available": len(self.manager.backends) > 0,
        }


def register_tool():
    """Register the video tool."""
    return VideoTool()
