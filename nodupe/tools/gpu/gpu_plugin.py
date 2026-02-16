# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""GPU Acceleration Tool for NoDupeLabs.

Provides hardware acceleration capabilities as a tool.
"""

from typing import List, Dict, Any, Optional, Callable
from nodupe.core.tool_system.base import Tool
from . import get_gpu_backend

class GPUBackendTool(Tool):
    """Hardware acceleration tool."""

    @property
    def name(self) -> str:
        return "gpu_acceleration"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        return []

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        return {
            'compute_embeddings': self.backend.compute_embeddings,
            'matrix_multiply': self.backend.matrix_multiply,
            'get_device_info': self.backend.get_device_info,
            'is_available': self.backend.is_available
        }

    def __init__(self):
        """Initialize the tool."""
        self.backend = get_gpu_backend()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service('gpu_backend', self.backend)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        info = self.backend.get_device_info()
        return {
            'device_type': info.get('type', 'unknown'),
            'device_name': info.get('name', 'unknown'),
            'available': self.backend.is_available()
        }

def register_tool():
    """Register the GPU tool."""
    return GPUBackendTool()
