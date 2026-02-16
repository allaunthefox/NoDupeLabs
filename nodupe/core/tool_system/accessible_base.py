"""Accessible Tool Base Class.

Abstract base class for all system tools with built-in accessibility support.
Extends the standard Tool base class with accessibility features.
"""

from abc import abstractmethod
from typing import List, Dict, Any, Callable
from .base import Tool, ToolMetadata
import logging


class AccessibleTool(Tool):
    """Abstract base class for all accessible NoDupeLabs tools with accessibility support."""

    def __init__(self):
        """Initialize accessible tool with accessibility features."""
        super().__init__()
        self.accessible_output = self._initialize_accessibility_features()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _initialize_accessibility_features(self):
        """Initialize accessibility libraries with fallbacks.
        
        Accessibility is a core requirement, not optional. Even if external
        libraries fail, basic accessibility through console output must remain.
        """
        from .api.codes import ActionCode
        
        class AccessibleOutput:
            def __init__(self):
                self.screen_reader_available = False
                self.braille_available = False
                self.outputter = None
                self.braille_client = None
                
                # Try to initialize screen reader support
                try:
                    from accessible_output2.outputs.auto import Auto
                    self.outputter = Auto()
                    self.screen_reader_available = True
                    print(f"[{ActionCode.ACC_SCREEN_READER_INIT}] Screen reader initialized successfully")
                except ImportError:
                    # Even if external library not available, we still have basic accessibility
                    self.screen_reader_available = False
                    print(f"[{ActionCode.ACC_SCREEN_READER_UNAVAIL}] Screen reader support unavailable, using console fallback")
                
                # Try to initialize braille support
                try:
                    import brlapi
                    self.braille_client = brlapi.Connection()
                    self.braille_available = True
                    print(f"[{ActionCode.ACC_BRAILLE_INIT}] Braille display initialized successfully")
                except (ImportError, Exception):
                    # Even if braille not available, we still have basic accessibility
                    self.braille_available = False
                    print(f"[{ActionCode.ACC_BRAILLE_UNAVAIL}] Braille display support unavailable, using console fallback")
            
            def output(self, text: str, interrupt: bool = True):
                """Output text to all available accessibility channels.
                
                Core accessibility requirement: Always output to console as minimum viable option.
                Additional accessibility channels are enhancements.
                """
                # CORE REQUIREMENT: Always output to console as minimum accessibility
                print(text)
                
                # ENHANCEMENT: Screen reader output if available
                if self.screen_reader_available and self.outputter:
                    try:
                        self.outputter.output(text, interrupt=interrupt)
                        print(f"[{ActionCode.ACC_OUTPUT_SENT}] Screen reader output sent")
                    except Exception as e:
                        # Log the error but don't fail the core accessibility
                        print(f"[{ActionCode.ACC_OUTPUT_FAILED}] Screen reader output failed: {e}")
                
                # ENHANCEMENT: Braille output if available
                if self.braille_available and self.braille_client:
                    try:
                        self.braille_client.writeText(text[:40])  # Limit to display size
                        print(f"[{ActionCode.ACC_OUTPUT_SENT}] Braille output sent")
                    except Exception as e:
                        # Log the error but don't fail the core accessibility
                        print(f"[{ActionCode.ACC_OUTPUT_FAILED}] Braille output failed: {e}")
        
        return AccessibleOutput()

    def announce_to_assistive_tech(self, message: str, interrupt: bool = True):
        """Announce a message to assistive technologies when available."""
        if self.accessible_output:
            self.accessible_output.output(message, interrupt)
        else:
            print(message)

    def format_for_accessibility(self, data: Any) -> str:
        """
        Format data for accessibility with screen readers and braille displays.
        
        Args:
            data: Data to format for accessibility
            
        Returns:
            String formatted for accessibility
        """
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{key}:")
                    lines.append(self.format_for_accessibility(value))
                else:
                    lines.append(f"{key}: {self.describe_value(value)}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data):
                lines.append(f"Item {i + 1}: {self.describe_value(item)}")
            return "\n".join(lines)
        else:
            return str(data)

    def describe_value(self, value: Any) -> str:
        """Describe a value in an accessible way."""
        if value is None:
            return "Not set"
        elif isinstance(value, bool):
            return "Enabled" if value else "Disabled"
        elif isinstance(value, (int, float)):
            return f"{value}"
        elif isinstance(value, str):
            return f"'{value}'" if value else "Empty"
        elif isinstance(value, list):
            return f"List with {len(value)} items"
        elif isinstance(value, dict):
            return f"Dictionary with {len(value)} keys"
        else:
            return f"{type(value).__name__} object"

    @abstractmethod
    def get_ipc_socket_documentation(self) -> Dict[str, Any]:
        """
        Document IPC socket interfaces for assistive technology integration.
        
        Returns:
            Dictionary describing available IPC endpoints and their accessibility features
        """
        return {
            "socket_endpoints": {},
            "accessibility_features": {
                "text_only_mode": True,
                "structured_output": True,
                "progress_reporting": True,
                "error_explanation": True,
                "screen_reader_integration": True,
                "braille_api_support": True
            }
        }

    def get_accessible_status(self) -> str:
        """
        Get tool status in an accessible format.
        
        Returns:
            Human-readable status information suitable for screen readers
        """
        capabilities = self.get_capabilities()
        status_info = {
            "name": self.name,
            "version": self.version,
            "status": "ready" if hasattr(self, '_initialized') and self._initialized else "not initialized",
            "capabilities": capabilities.get('capabilities', []),
            "description": capabilities.get('description', 'No description available')
        }
        
        return self.format_for_accessibility(status_info)

    def log_accessible_message(self, message: str, level: str = "info"):
        """
        Log a message with accessibility consideration.
        
        Args:
            message: The message to log
            level: The logging level ('info', 'warning', 'error', 'debug')
        """
        from .api.codes import ActionCode
        
        # Determine the appropriate action code based on level
        if level.lower() == 'error':
            code = ActionCode.ERR_INTERNAL
        elif level.lower() == 'warning':
            code = ActionCode.FPT_FLS_FAIL
        elif level.lower() == 'debug':
            code = ActionCode.FIA_UAU_INIT  # Generic info code
        else:
            code = ActionCode.FIA_UAU_INIT  # Generic info code
        
        # Log to standard logger with action code
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{code}] {message}")
        
        # Optionally announce to assistive tech if it's an important message
        if level.lower() in ['warning', 'error']:
            self.announce_to_assistive_tech(f"Alert: {message}")
        else:
            self.announce_to_assistive_tech(message, interrupt=False)