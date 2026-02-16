"""Example Accessible Tool.

This is an example of how to implement an accessible tool that follows
the accessibility standards and supports users with visual impairments.
"""

from typing import List, Dict, Any, Callable
from nodupe.core.tool_system.accessible_base import AccessibleTool


class ExampleAccessibleTool(AccessibleTool):
    """Example accessible tool demonstrating accessibility features."""
    
    def __init__(self):
        super().__init__()  # Initialize accessibility features
        self._name = "ExampleAccessibleTool"
        self._version = "1.0.0"
        self._dependencies = []
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    def initialize(self, container: Any) -> None:
        """Initialize the accessible tool."""
        from .api.codes import ActionCode
        self._initialized = True
        # Accessibility is core requirement - always available even if external libraries fail
        self.announce_to_assistive_tech(f"Initializing {self.name} v{self.version}")
        self.log_accessible_message(f"{self.name} initialized successfully", "info")
        print(f"[{ActionCode.ACC_ISO_COMPLIANT}] Tool is ISO accessibility compliant")

    def shutdown(self) -> None:
        """Shutdown the accessible tool."""
        self.announce_to_assistive_tech(f"Shutting down {self.name}")
        self._initialized = False
        self.log_accessible_message(f"{self.name} shutdown complete", "info")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        return {
            "name": self.name,
            "version": self.version,
            "description": "An example accessible tool that demonstrates accessibility features",
            "capabilities": [
                "accessible_operations",
                "screen_reader_support",
                "braille_display_support"
            ],
            "iso_stakeholders": ["developer", "end_user", "accessibility_advocate"],
            "iso_concerns": ["functionality", "usability", "accessibility"]
        }

    def get_ipc_socket_documentation(self) -> Dict[str, Any]:
        """Document IPC socket interfaces for assistive technology integration."""
        return {
            "socket_endpoints": {
                "status": {
                    "path": "/api/v1/status",
                    "method": "GET",
                    "description": "Current tool status and health information",
                    "accessible_output": True,
                    "returns": {
                        "status": "Current operational status",
                        "progress": "Current progress percentage",
                        "errors": "Any current errors or warnings",
                        "estimated_completion": "Estimated time to completion"
                    }
                },
                "process": {
                    "path": "/api/v1/process",
                    "method": "POST",
                    "description": "Process data with accessibility features",
                    "accessible_output": True,
                    "parameters": {
                        "data": "Input data to process",
                        "format": "Output format preference"
                    }
                }
            },
            "accessibility_features": {
                "text_only_mode": True,
                "structured_output": True,
                "progress_reporting": True,
                "error_explanation": True,
                "screen_reader_integration": True,
                "braille_api_support": True
            }
        }

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        """Dictionary of methods exposed via programmatic API (Socket/IPC)."""
        return {
            'get_status': self.get_accessible_status,
            'process_data': self.process_accessible_data,
            'get_help': self.get_accessible_help
        }

    def run_standalone(self, args: List[str]) -> int:
        """Execute the tool in stand-alone mode without the core engine."""
        self.announce_to_assistive_tech(f"Running {self.name} in standalone mode")
        
        # Process arguments if provided
        if args:
            self.announce_to_assistive_tech(f"Arguments received: {', '.join(args)}")
        
        self.announce_to_assistive_tech(f"{self.name} standalone execution completed")
        return 0

    def describe_usage(self) -> str:
        """Return human-readable, jargon-free instructions for this component."""
        return (
            "This tool demonstrates accessibility features for users with visual impairments. "
            "It provides output suitable for screen readers and braille displays. "
            "All operations are accessible via keyboard and command-line interface."
        )

    def process_accessible_data(self, data: Any, format: str = "auto") -> str:
        """Process data with accessibility considerations."""
        self.announce_to_assistive_tech(f"Starting to process data of type: {type(data).__name__}")
        
        # Format the data for accessibility
        accessible_data = self.format_for_accessibility(data)
        self.announce_to_assistive_tech(f"Formatted data for accessibility: {accessible_data[:100]}...")
        
        # Simulate processing
        if isinstance(data, dict):
            result = f"Processed dictionary with {len(data)} keys"
        elif isinstance(data, list):
            result = f"Processed list with {len(data)} items"
        else:
            result = f"Processed {len(str(data))} characters of data"
        
        self.announce_to_assistive_tech(f"Processing complete: {result}")
        return result

    def get_accessible_help(self) -> str:
        """Get accessible help information."""
        help_text = (
            "Example Accessible Tool Help:\n"
            "- Use 'process_data' to process information with accessibility features\n"
            "- Use 'get_status' to get current tool status\n"
            "- All output is designed for screen readers and braille displays\n"
            "- Keyboard navigation is fully supported\n"
        )
        self.announce_to_assistive_tech(help_text)
        return help_text

    def get_architecture_rationale(self) -> Dict[str, str]:
        """Get architectural rationale following ISO/IEC/IEEE 42010."""
        return {
            "design_decision": "Created as an accessible tool to demonstrate accessibility-first design",
            "alternatives_considered": "Considered standard tool vs. accessible tool implementation",
            "tradeoffs": "Added accessibility library dependencies vs. gained inclusive design",
            "stakeholder_impact": "Enables users with visual impairments to use the tool effectively"
        }