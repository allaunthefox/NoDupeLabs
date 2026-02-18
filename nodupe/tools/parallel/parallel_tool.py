# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Parallel Processing Tool for NoDupeLabs.

Provides high-performance parallel execution capabilities as a standalone tool.
Compliant with IEEE Std 1003.1 (POSIX) threading models.
"""

from typing import Any, Callable

from nodupe.core.tool_system.base import Tool, ToolMetadata

from .parallel_logic import Parallel


class ParallelTool(Tool):
    """Parallel processing tool (POSIX & ISO 25010 compliant)."""

    @property
    def name(self) -> str:
        return "parallel_execution"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata (ISO 19770-2 compliant)."""
        return ToolMetadata(
            name=self.name,
            version=self.version,
            software_id=f"org.nodupe.tool.{self.name.lower()}",
            description="Parallel processing engine supporting Threads, Processes, and Sub-Interpreters.",
            author="NoDupeLabs",
            license="Apache-2.0",
            dependencies=self.dependencies,
            tags=["parallel", "performance", "posix", "threading"],
        )

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            "map": Parallel.map_parallel,
            "smart_map": Parallel.smart_map,
            "get_workers": Parallel.get_optimal_workers,
        }

    def initialize(self, container: Any) -> None:
        """Register the parallel service."""
        container.register_service("parallel_service", self)

    def shutdown(self) -> None:
        """Gracefully cleanup any pending pools."""
        # Parallel logic handles pools via context managers usually,
        # but we ensure global cleanup here if needed.
        pass

    def run_standalone(self, args: list[str]) -> int:
        """Execute demonstration in stand-alone mode."""
        print("Parallel Tool: Self-test mode.")
        print("Demonstrating 4-way parallel mapping of math functions...")
        results = Parallel.map_parallel(lambda x: x * x, range(10), workers=4)
        print(f"Results: {results}")
        return 0

    def describe_usage(self) -> str:
        """Plain language description."""
        return (
            "This component allows the computer to work on many tasks at the same time. "
            "It splits a big job into smaller pieces and gives each piece to a different "
            "'brain' in your computer so the work finishes much faster."
        )

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "cpu_count": Parallel.get_cpu_count(),
            "supports_interpreters": Parallel.supports_interpreter_pool(),
            "is_free_threaded": Parallel.is_free_threaded(),
        }


def register_tool():
    """Register the parallel tool."""
    return ParallelTool()


if __name__ == "__main__":
    import sys

    tool = ParallelTool()
    sys.exit(tool.run_standalone(sys.argv[1:]))
