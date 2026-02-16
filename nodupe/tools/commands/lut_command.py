# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""LUT Command Tool for NoDupeLabs.

Provides access to the ISO standard Action Code registry (LUT).
"""

from typing import List, Dict, Any, Optional, Callable
from nodupe.core.tool_system.base import Tool
from nodupe.core.api.codes import ActionCode

class LUTTool(Tool):
    """Action Code Registry (LUT) tool."""

    @property
    def name(self) -> str:
        return "lut_service"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """Tool dependencies."""
        return []

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        from nodupe.core.container import container
        return {
            'get_codes': ActionCode.get_lut,
            'describe_code': ActionCode.get_description,
            'check_iso_compliance': container.check_compliance
        }

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service('lut_service', self)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def describe_usage(self) -> str:
        """Plain language description."""
        return (
            "This component is a dictionary of all system events. "
            "It explains what the different codes in the logs mean in plain language."
        )

    def run_standalone(self, args: List[str]) -> int:
        """Execute in stand-alone mode."""
        import argparse
        parser = argparse.ArgumentParser(description=self.describe_usage())
        parser.add_argument("--code", type=int, help="The code number you want to look up")
        
        if not args:
            parser.print_help()
            return 0

        parsed = parser.parse_args(args)
        if parsed.code:
            desc = ActionCode.get_description(parsed.code)
            print(f"Code {parsed.code}: {desc}")
        return 0

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        return {
            'specification': 'ISO-8000-110:2021',
            'features': ['code_lookup', 'description_retrieval']
        }

def register_tool():
    """Register the LUT tool."""
    return LUTTool()
