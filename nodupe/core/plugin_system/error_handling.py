"""Plugin System Error Handling.

Enhanced error handling for plugin operations.
"""

import logging
from typing import Optional, Dict, Any
from .base import PluginOperationResult

logger = logging.getLogger(__name__)

def handle_plugin_error(e: Exception, plugin_id: str, operation: str) -> PluginOperationResult:
    """Handle plugin errors with logging and user-friendly messages.

    This function provides structured error handling for plugin operations by:
    1. Logging detailed technical information
    2. Creating user-friendly error messages
    3. Returning structured error results

    Args:
        e: The exception that occurred
        plugin_id: ID of the plugin involved
        operation: Description of the operation being performed

    Returns:
        PluginOperationResult with error details
    """
    # Log technical details
    logger.exception(f"Plugin {operation} failed for {plugin_id}")

    # User-friendly message
    user_message = f"Failed to {operation} plugin: {str(e)}"

    # Technical details for logging
    details = {
        "operation": operation,
        "plugin_id": plugin_id,
        "error_type": type(e).__name__,
        "error_message": str(e),
        "timestamp": __import__('time').time()
    }

    return PluginOperationResult(
        ok=False,
        message=user_message,
        plugin_id=plugin_id,
        details=details
    )

def log_plugin_operation_success(plugin_id: str, operation: str, message: str) -> None:
    """Log successful plugin operations.

    Args:
        plugin_id: ID of the plugin
        operation: Description of the operation
        message: Success message
    """
    logger.info(f"Plugin {operation} successful for {plugin_id}: {message}")

def create_user_friendly_error(error_result: PluginOperationResult) -> str:
    """Create user-friendly error message from PluginOperationResult.

    Args:
        error_result: PluginOperationResult containing error details

    Returns:
        User-friendly error message
    """
    if error_result.ok:
        return error_result.message

    # Extract relevant information
    plugin_id = error_result.plugin_id or "unknown"
    operation = error_result.details.get('operation', 'operation') if error_result.details else 'operation'

    # Create user-friendly message
    user_message = f"Error: {error_result.message}"

    # Add suggestions if available
    if error_result.details and 'suggestion' in error_result.details:
        user_message += f"\nSuggestion: {error_result.details['suggestion']}"

    return user_message

def handle_database_error(e: Exception, operation: str) -> str:
    """Handle database-specific errors.

    Args:
        e: The database exception
        operation: Description of the database operation

    Returns:
        User-friendly error message
    """
    logger.exception(f"Database {operation} failed: {e}")

    error_type = type(e).__name__
    error_message = str(e)

    # Create user-friendly message based on error type
    if "no such table" in error_message.lower():
        return f"Database error: Required table not found. Please run database migrations."
    elif "constraint failed" in error_message.lower():
        return f"Database error: Constraint violation. Please check your data."
    elif "locked" in error_message.lower():
        return f"Database error: Database is locked. Please try again later."
    else:
        return f"Database error: {error_message}"

def validate_plugin_identifier(identifier: str) -> bool:
    """Validate plugin identifier format.

    Args:
        identifier: Plugin name or ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not identifier or not isinstance(identifier, str):
        return False

    # Check if it's a valid UUID (as string)
    if len(identifier) == 36 and identifier.count('-') == 4:
        return True

    # Check if it's a valid plugin name
    if len(identifier) > 0 and len(identifier) <= 100:
        return True

    return False
