# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""User confirmation system for NoDupeLabs.

This module provides user confirmation prompts for destructive operations.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to import rich for enhanced formatting, fall back to basic if not available
try:
    from rich.console import Console
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    # Fallback implementations
    Console = None
    Confirm = None
    Prompt = None
    Table = None
    rprint = print
    RICH_AVAILABLE = False


class ConfirmationManager:
    """Manager for user confirmation prompts."""

    def __init__(self):
        """Initialize confirmation manager."""
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            # Create a simple console-like interface for basic printing
            class SimpleConsole:
                def print(self, text, **kwargs):
                    print(text)
            
            self.console = SimpleConsole()

    def confirm_deletion(self, files: List[Path],
                        total_size: int,
                        operation: str = "delete") -> bool:
        """Request user confirmation before deletion.

        Args:
            files: List of files to be deleted
            total_size: Total size of files in bytes
            operation: Type of operation ('delete', 'move', 'copy')

        Returns:
            True if user confirmed, False otherwise
        """
        self.console.print(f"\n[bold red]WARNING:[/bold red] About to {operation} {len(files)} files")
        self.console.print(f"Total size: {self.format_size(total_size)}")

        # Show sample of files to be processed
        self.console.print("\n[yellow]Sample files:[/yellow]")
        for file in files[:10]:
            self.console.print(f"  • {file}")
        if len(files) > 10:
            self.console.print(f"  ... and {len(files) - 10} more")

        # Check if this is a large operation
        large_operation = total_size > 1_000  # > 1GB
        if large_operation:
            self.console.print("\n[bold red]This will affect over 1GB of data![/bold red]")

        # Get user confirmation
        if large_operation:
            confirmation = Prompt.ask(
                f"\nType 'CONFIRM {operation.upper()}' to proceed with {operation}",
                default="cancel"
            )
            confirmed = confirmation.upper() == f"CONFIRM {operation.upper()}"
        else:
            confirmed = Confirm.ask(
                f"\n[bold]Are you sure you want to {operation} these files?[/bold]"
            )

        # Log the confirmation
        from nodupe.core.audit import log_user_confirmation
        log_user_confirmation(
            action=operation,
            confirmed=confirmed,
            details={
                'file_count': len(files),
                'total_size': total_size,
                'large_operation': large_operation
            }
        )

        return confirmed

    def confirm_apply_action(self, action: str, files: List[Dict[str, Any]]) -> bool:
        """Request user confirmation before applying an action.

        Args:
            action: Action to be applied ('delete', 'move', 'copy', etc.)
            files: List of file dictionaries with path and size info

        Returns:
            True if user confirmed, False otherwise
        """
        if not files:
            return True

        total_size = sum(f.get('size', 0) for f in files)
        file_paths = [Path(f['path']) for f in files]

        return self.confirm_deletion(file_paths, total_size, action)

    def confirm_rollback_operation(self, operation: str, steps: int) -> bool:
        """Request user confirmation before rollback operation.

        Args:
            operation: Type of rollback operation ('last', 'all', 'to-point')
            steps: Number of operations to rollback (for 'last' operation)

        Returns:
            True if user confirmed, False otherwise
        """
        self.console.print(f"\n[bold red]WARNING:[/bold red] About to perform rollback operation: {operation}")
        
        if operation == 'last':
            self.console.print(f"Rolling back last {steps} operation(s)")
        elif operation == 'all':
            self.console.print("Rolling back ALL operations")
        elif operation == 'to-point':
            self.console.print(f"Rolling back to specific point: {steps}")
        else:
            self.console.print(f"Rolling back {operation} operations")

        # Get user confirmation
        confirmed = Confirm.ask(
            f"\n[bold]Are you sure you want to proceed with this rollback operation?[/bold]"
        )

        # Log the confirmation
        from nodupe.core.audit import log_user_confirmation
        log_user_confirmation(
            action="rollback",
            confirmed=confirmed,
            details={
                'operation_type': operation,
                'steps': steps if operation == 'last' else None,
                'target_point': steps if operation == 'to-point' else None
            }
        )

        return confirmed

    def confirm_scan_operation(self, paths: List[Path], recursive: bool = True) -> bool:
        """Request user confirmation before scan operation.

        Args:
            paths: List of paths to scan
            recursive: Whether scan is recursive

        Returns:
            True if user confirmed, False otherwise
        """
        self.console.print(f"\n[bold blue]SCAN OPERATION:[/bold blue] About to scan {len(paths)} directory paths")
        
        self.console.print("\n[blue]Directories to scan:[/blue]")
        for path in paths:
            self.console.print(f"  • {path}")

        if recursive:
            self.console.print("\n[yellow]Note:[/yellow] Recursive scan enabled (will include subdirectories)")

        confirmed = Confirm.ask(
            f"\n[bold]Proceed with scan operation?[/bold]"
        )

        # Log the confirmation
        from nodupe.core.audit import log_user_confirmation
        log_user_confirmation(
            action="scan",
            confirmed=confirmed,
            details={
                'directory_count': len(paths),
                'recursive': recursive
            }
        )

        return confirmed

    def confirm_dry_run(self, action: str, files: List[Dict[str, Any]]) -> bool:
        """Show dry run results and ask if user wants to proceed with actual operation.

        Args:
            action: Action that would be performed
            files: List of files that would be affected

        Returns:
            True if user wants to proceed with actual operation, False if should cancel
        """
        if not files:
            self.console.print("[green]No files would be affected by this operation.[/green]")
            return False

        total_size = sum(f.get('size', 0) for f in files)
        
        self.console.print(f"\n[bold yellow]DRY RUN RESULTS:[/bold yellow]")
        self.console.print(f"Action: {action}")
        self.console.print(f"Files affected: {len(files)}")
        self.console.print(f"Total size: {self.format_size(total_size)}")

        if len(files) <= 20:
            self.console.print("\n[yellow]Files that would be affected:[/yellow]")
            for f in files:
                path = Path(f['path'])
                size = f.get('size', 0)
                self.console.print(f"  • {path} ({self.format_size(size)})")
        else:
            self.console.print(f"\n[yellow]First 20 files that would be affected:[/yellow]")
            for f in files[:20]:
                path = Path(f['path'])
                size = f.get('size', 0)
                self.console.print(f" • {path} ({self.format_size(size)})")
            self.console.print(f"  ... and {len(files) - 20} more")

        confirmed = Confirm.ask(
            f"\n[bold]Would you like to proceed with the actual {action} operation?[/bold]"
        )

        # Log the confirmation
        from nodupe.core.audit import log_user_confirmation
        log_user_confirmation(
            action=f"{action}_proceed_from_dry_run",
            confirmed=confirmed,
            details={
                'file_count': len(files),
                'total_size': total_size
            }
        )

        return confirmed

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{int(size_bytes)} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


# Global confirmation manager instance
_confirmation_manager: Optional[ConfirmationManager] = None


def get_confirmation_manager() -> ConfirmationManager:
    """Get the global confirmation manager instance."""
    global _confirmation_manager
    if _confirmation_manager is None:
        _confirmation_manager = ConfirmationManager()
    return _confirmation_manager


def confirm_operation(operation: str, files: List[Dict[str, Any]], **kwargs) -> bool:
    """Convenience function to confirm an operation.

    Args:
        operation: Type of operation ('delete', 'move', 'copy', 'scan', etc.)
        files: List of files to operate on (can be empty for some operations)
        **kwargs: Additional operation-specific arguments

    Returns:
        True if confirmed, False otherwise
    """
    conf_mgr = get_confirmation_manager()
    
    if operation == 'delete':
        return conf_mgr.confirm_deletion(
            [Path(f['path']) for f in files],
            sum(f.get('size', 0) for f in files)
        )
    elif operation in ['move', 'copy']:
        return conf_mgr.confirm_deletion(
            [Path(f['path']) for f in files],
            sum(f.get('size', 0) for f in files),
            operation
        )
    elif operation == 'scan':
        paths = kwargs.get('paths', [])
        recursive = kwargs.get('recursive', True)
        return conf_mgr.confirm_scan_operation([Path(p) for p in paths], recursive)
    else:
        # For other operations, use generic confirmation
        return conf_mgr.confirm_apply_action(operation, files)


def confirm_dry_run_proceed(action: str, files: List[Dict[str, Any]]) -> bool:
    """Ask user if they want to proceed after showing dry run results."""
    conf_mgr = get_confirmation_manager()
    return conf_mgr.confirm_dry_run(action, files)


__all__ = [
    'ConfirmationManager',
    'get_confirmation_manager',
    'confirm_operation',
    'confirm_dry_run_proceed'
]
