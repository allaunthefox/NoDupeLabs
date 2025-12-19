# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Enhanced Error Handling for Plugin System.

This module provides enhanced error handling capabilities for the plugin system,
including detailed error logging, user-friendly error messages, and comprehensive
error recovery mechanisms.
"""

import logging
import traceback
import sys
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import datetime

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PluginErrorDetails:
    """Detailed information about a plugin error."""
    error_id: str
    timestamp: str
    plugin_name: str
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    severity: str
    recovery_suggestions: List[str]

class EnhancedPluginErrorHandler:
    """Enhanced error handler for plugin system with detailed logging and recovery."""

    def __init__(self):
        """Initialize the enhanced error handler."""
        self.error_counter = 0
        self.error_log = []

    def log_error(self, plugin_name: str, error: Exception, context: Dict[str, Any] = None,
                  severity: str = "ERROR") -> PluginErrorDetails:
        """Log a plugin error with detailed information.

        Args:
            plugin_name: Name of the plugin that encountered the error
            error: Exception object containing error information
            context: Additional context about the error
            severity: Severity level of the error

        Returns:
            PluginErrorDetails object with comprehensive error information
        """
        if context is None:
            context = {}

        self.error_counter += 1
        error_id = f"PLUGIN-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{self.error_counter:04d}"

        # Get stack trace
        stack_trace = self._get_stack_trace(error)

        # Create error details
        error_details = PluginErrorDetails(
            error_id=error_id,
            timestamp=datetime.datetime.now().isoformat(),
            plugin_name=plugin_name,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=stack_trace,
            context=context,
            severity=severity,
            recovery_suggestions=self._get_recovery_suggestions(error, context)
        )

        # Log to internal error log
        self.error_log.append(error_details)

        # Log to logging system
        self._log_to_logging_system(error_details)

        return error_details

    def _get_stack_trace(self, error: Exception) -> str:
        """Get formatted stack trace from exception."""
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if exc_type and exc_value and exc_traceback:
                stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
                return "".join(stack_trace)
            else:
                return traceback.format_exc()
        except:
            return "Stack trace unavailable"

    def _get_recovery_suggestions(self, error: Exception, context: Dict[str, Any]) -> List[str]:
        """Generate recovery suggestions based on error type and context."""
        suggestions = []
        error_type = type(error).__name__

        # Common recovery suggestions
        suggestions.append("Check plugin configuration and dependencies")
        suggestions.append("Verify file permissions and access rights")
        suggestions.append("Review plugin logs for additional details")
        suggestions.append("Restart the application if the error persists")

        # Specific suggestions based on error type
        if error_type == "ImportError":
            suggestions.append("Check that all required dependencies are installed")
            suggestions.append("Verify Python path and module availability")
            suggestions.append("Reinstall the plugin if dependency issues persist")

        elif error_type == "PermissionError":
            suggestions.append("Check file and directory permissions")
            suggestions.append("Run the application with appropriate privileges")
            suggestions.append("Verify that the application has access to required resources")

        elif error_type == "FileNotFoundError":
            suggestions.append("Verify that all required files exist")
            suggestions.append("Check file paths and configurations")
            suggestions.append("Ensure that the application has access to the specified locations")

        elif error_type == "TypeError":
            suggestions.append("Review plugin method signatures and parameters")
            suggestions.append("Check for incompatible data types")
            suggestions.append("Verify that all required methods are implemented")

        elif error_type == "ValueError":
            suggestions.append("Validate input parameters and configurations")
            suggestions.append("Check for invalid or unexpected values")
            suggestions.append("Review data validation logic")

        elif error_type == "RuntimeError":
            suggestions.append("Investigate runtime conditions and state")
            suggestions.append("Check for resource availability and constraints")
            suggestions.append("Review error handling and recovery logic")

        # Context-specific suggestions
        if context.get("operation") == "initialize":
            suggestions.append("Check plugin initialization parameters")
            suggestions.append("Verify dependency container availability")

        elif context.get("operation") == "execute":
            suggestions.append("Review command arguments and options")
            suggestions.append("Check for invalid or missing parameters")

        return suggestions

    def _log_to_logging_system(self, error_details: PluginErrorDetails):
        """Log error details to the logging system."""
        error_msg = (
            f"[{error_details.severity}] {error_details.error_id} - "
            f"Plugin '{error_details.plugin_name}' encountered {error_details.error_type}: "
            f"{error_details.error_message}"
        )

        if error_details.severity == "ERROR":
            logger.error(error_msg)
        elif error_details.severity == "WARNING":
            logger.warning(error_msg)
        elif error_details.severity == "INFO":
            logger.info(error_msg)
        else:
            logger.debug(error_msg)

        # Log additional details
        logger.debug(f"Error ID: {error_details.error_id}")
        logger.debug(f"Timestamp: {error_details.timestamp}")
        logger.debug(f"Context: {error_details.context}")

        if error_details.stack_trace:
            logger.debug(f"Stack Trace:\n{error_details.stack_trace}")

        if error_details.recovery_suggestions:
            logger.info(f"Recovery Suggestions for {error_details.error_id}:")
            for suggestion in error_details.recovery_suggestions:
                logger.info(f"  - {suggestion}")

    def get_error_report(self, error_id: str = None) -> Dict[str, Any]:
        """Get a comprehensive error report.

        Args:
            error_id: Specific error ID to report, or None for all errors

        Returns:
            Dictionary containing error report information
        """
        if error_id:
            # Find specific error
            errors = [e for e in self.error_log if e.error_id == error_id]
        else:
            # Return all errors
            errors = self.error_log

        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_errors": len(errors),
            "errors": []
        }

        for error in errors:
            error_report = {
                "error_id": error.error_id,
                "timestamp": error.timestamp,
                "plugin_name": error.plugin_name,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "severity": error.severity,
                "context": error.context,
                "recovery_suggestions": error.recovery_suggestions
            }
            report["errors"].append(error_report)

        return report

    def get_user_friendly_error_message(self, error_details: PluginErrorDetails) -> str:
        """Generate a user-friendly error message.

        Args:
            error_details: PluginErrorDetails object

        Returns:
            User-friendly error message string
        """
        message = (
            f"🚨 Plugin Error: {error_details.error_id}\n\n"
            f"Plugin '{error_details.plugin_name}' encountered an issue:\n"
            f"  Type: {error_details.error_type}\n"
            f"  Message: {error_details.error_message}\n\n"
            f"📅 When: {error_details.timestamp}\n"
            f"📊 Severity: {error_details.severity}\n\n"
        )

        if error_details.context:
            message += "📝 Context:\n"
            for key, value in error_details.context.items():
                message += f"  • {key}: {value}\n"
            message += "\n"

        message += "💡 Recovery Suggestions:\n"
        for i, suggestion in enumerate(error_details.recovery_suggestions, 1):
            message += f"  {i}. {suggestion}\n"

        message += "\n🔍 For more details, check the logs or use the error ID for support.\n"

        return message

    def handle_plugin_error(self, plugin_name: str, method_name: str, error: Exception,
                           context: Dict[str, Any] = None) -> Any:
        """Handle a plugin error with enhanced error handling.

        Args:
            plugin_name: Name of the plugin
            method_name: Name of the method that failed
            error: Exception that was raised
            context: Additional context information

        Returns:
            Appropriate return value for the failed method
        """
        if context is None:
            context = {}

        context["operation"] = method_name

        # Log the error
        error_details = self.log_error(plugin_name, error, context)

        # Generate user-friendly message
        user_message = self.get_user_friendly_error_message(error_details)

        # Print to console
        print(f"\n{user_message}")

        # Return appropriate error code or value based on method
        if method_name in ["execute_scan", "execute_verify", "execute_command"]:
            return 1  # Error code for command execution

        elif method_name in ["initialize", "shutdown", "teardown"]:
            return False  # False for lifecycle methods

        elif method_name == "get_capabilities":
            return {}  # Empty dict for capabilities

        else:
            return None  # None for other methods

    def clear_error_log(self):
        """Clear the error log."""
        self.error_log = []
        self.error_counter = 0

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about logged errors."""
        stats = {
            "total_errors": len(self.error_log),
            "errors_by_severity": {},
            "errors_by_plugin": {},
            "errors_by_type": {}
        }

        for error in self.error_log:
            # Count by severity
            severity = error.severity
            stats["errors_by_severity"][severity] = stats["errors_by_severity"].get(severity, 0) + 1

            # Count by plugin
            plugin = error.plugin_name
            stats["errors_by_plugin"][plugin] = stats["errors_by_plugin"].get(plugin, 0) + 1

            # Count by type
            error_type = error.error_type
            stats["errors_by_type"][error_type] = stats["errors_by_type"].get(error_type, 0) + 1

        return stats

class PluginErrorFormatter:
    """Formatter for plugin error messages with different output formats."""

    @staticmethod
    def format_error_console(error_details: PluginErrorDetails) -> str:
        """Format error for console output."""
        return (
            f"🚨 {error_details.severity}: {error_details.error_id}\n"
            f"📦 Plugin: {error_details.plugin_name}\n"
            f"🔧 Error: {error_details.error_type} - {error_details.error_message}\n"
            f"🕒 Time: {error_details.timestamp}\n"
        )

    @staticmethod
    def format_error_json(error_details: PluginErrorDetails) -> Dict[str, Any]:
        """Format error as JSON-serializable dictionary."""
        return {
            "error_id": error_details.error_id,
            "timestamp": error_details.timestamp,
            "plugin_name": error_details.plugin_name,
            "error_type": error_details.error_type,
            "error_message": error_details.error_message,
            "severity": error_details.severity,
            "context": error_details.context,
            "recovery_suggestions": error_details.recovery_suggestions
        }

    @staticmethod
    def format_error_markdown(error_details: PluginErrorDetails) -> str:
        """Format error as Markdown."""
        md = f"## Plugin Error: {error_details.error_id}\n\n"
        md += f"**Plugin**: `{error_details.plugin_name}`  \n"
        md += f"**Type**: `{error_details.error_type}`  \n"
        md += f"**Message**: `{error_details.error_message}`  \n"
        md += f"**Severity**: `{error_details.severity}`  \n"
        md += f"**Time**: `{error_details.timestamp}`  \n\n"

        if error_details.context:
            md += "**Context:**\n"
            for key, value in error_details.context.items():
                md += f"- `{key}`: `{value}`\n"
            md += "\n"

        if error_details.recovery_suggestions:
            md += "**Recovery Suggestions:**\n"
            for suggestion in error_details.recovery_suggestions:
                md += f"- {suggestion}\n"

        return md

class PluginErrorRecovery:
    """Plugin error recovery utilities."""

    @staticmethod
    def can_recover_from_error(error_details: PluginErrorDetails) -> bool:
        """Determine if recovery from the error is possible."""
        recoverable_errors = [
            "FileNotFoundError",
            "PermissionError",
            "ConnectionError",
            "TimeoutError",
            "ValueError"
        ]

        return error_details.error_type in recoverable_errors

    @staticmethod
    def get_recovery_strategy(error_details: PluginErrorDetails) -> Dict[str, Any]:
        """Get recovery strategy for the error."""
        strategy = {
            "recoverable": False,
            "strategy": "manual_intervention",
            "automatic_actions": [],
            "manual_actions": []
        }

        if error_details.error_type == "FileNotFoundError":
            strategy.update({
                "recoverable": True,
                "strategy": "retry_with_validation",
                "automatic_actions": [
                    "Validate file paths",
                    "Check file existence",
                    "Retry operation with corrected paths"
                ],
                "manual_actions": [
                    "Create missing files if appropriate",
                    "Update configuration with correct paths",
                    "Verify file system permissions"
                ]
            })

        elif error_details.error_type == "PermissionError":
            strategy.update({
                "recoverable": True,
                "strategy": "permission_recovery",
                "automatic_actions": [
                    "Log detailed permission information",
                    "Attempt operation with elevated privileges if available"
                ],
                "manual_actions": [
                    "Adjust file/directory permissions",
                    "Run application with appropriate privileges",
                    "Review security policies"
                ]
            })

        elif error_details.error_type == "ConnectionError":
            strategy.update({
                "recoverable": True,
                "strategy": "retry_with_backoff",
                "automatic_actions": [
                    "Implement exponential backoff",
                    "Retry connection with delay",
                    "Log connection attempts"
                ],
                "manual_actions": [
                    "Check network connectivity",
                    "Verify service availability",
                    "Review connection configurations"
                ]
            })

        return strategy

# Global instance for easy access
enhanced_error_handler = EnhancedPluginErrorHandler()

def setup_enhanced_error_handling():
    """Setup enhanced error handling for the plugin system."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('plugin_errors.log')
        ]
    )

    logger.info("Enhanced plugin error handling initialized")
    return enhanced_error_handler

# Export public interface
__all__ = [
    'EnhancedPluginErrorHandler',
    'PluginErrorDetails',
    'PluginErrorFormatter',
    'PluginErrorRecovery',
    'enhanced_error_handler',
    'setup_enhanced_error_handling'
]
