# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Rollback plugin for NoDupeLabs.

This plugin provides the rollback functionality to undo operations
performed by the apply command and restore system to previous states.

Key Features:
    - Operation history tracking
    - Reversible operations
    - Backup restoration
    - Safe undo functionality
    - Plugin integration

Dependencies:
    - Core undo system
    - Core backup system
    - Core audit system
"""

from typing import Any, Dict
import argparse
import json
from pathlib import Path
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.undo import get_operation_stack, execute_reversible_operation
from nodupe.core.backup import get_backup_manager
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.confirmation import get_confirmation_manager


class RollbackPlugin(Plugin):
    """Rollback plugin implementation."""

    name = "rollback"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        """Initialize rollback plugin."""
        self.description = "Rollback operations and restore system state"

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""

    def shutdown(self) -> None:
        """Shutdown the plugin."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {
            'commands': ['rollback'],
            'operations': ['last', 'all', 'to-point']
        }

    def _on_rollback_start(self, **kwargs: Any) -> None:
        """Handle rollback start event."""
        print(f"[PLUGIN] Rollback started: {kwargs.get('operation', 'unknown')}")

    def _on_rollback_complete(self, **kwargs: Any) -> None:
        """Handle rollback complete event."""
        print(f"[PLUGIN] Rollback completed: {kwargs.get('operations_undone', 0)} operations undone")

    def register_commands(self, subparsers: Any) -> None:
        """Register rollback command with argument parser."""
        rollback_parser = subparsers.add_parser('rollback', help='Rollback operations and restore state')
        rollback_parser.add_argument(
            'operation',
            choices=['last', 'all', 'to-point'],
            help='What to rollback: last operation, all operations, or to a specific point'
        )
        rollback_parser.add_argument(
            '--point',
            help='Specific operation point to rollback to (for to-point operation)'
        )
        rollback_parser.add_argument(
            '--steps',
            type=int,
            default=1,
            help='Number of operations to rollback (for last operation)'
        )
        rollback_parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
        rollback_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        rollback_parser.set_defaults(func=self.execute_rollback)

    def execute_rollback(self, args: argparse.Namespace) -> int:
        """Execute rollback command.

        Args:
            args: Command arguments including injected 'container'
        """
        try:
            print(f"[PLUGIN] Executing rollback command: {args.operation}")

            # Initialize audit logger
            audit_logger = get_audit_logger()
            audit_logger.log_rollback_started(args.operation, vars(args))

            # Initialize confirmation manager
            confirmation_mgr = get_confirmation_manager()

            # Initialize backup manager
            backup_manager = get_backup_manager()

            # Get operation stack
            operation_stack = get_operation_stack()

            # Validate operation type
            if args.operation not in ['last', 'all', 'to-point']:
                print(f"[ERROR] Invalid operation: {args.operation}. Must be 'last', 'all', or 'to-point'")
                return 1

            # User confirmation for rollback operations
            if not args.dry_run:
                if not confirmation_mgr.confirm_rollback_operation(args.operation, args.steps if hasattr(args, 'steps') else 1):
                    print("[PLUGIN] Rollback operation cancelled by user.")
                    return 0

            operations_undone = 0

            if args.operation == 'last':
                # Rollback last N operations
                steps = getattr(args, 'steps', 1)
                print(f"[PLUGIN] Rolling back last {steps} operations...")
                
                for i in range(min(steps, len(operation_stack))):
                    if operation_stack:
                        operation = operation_stack.pop()
                        if args.dry_run:
                            print(f"[DRY-RUN] Would rollback: {operation.__class__.__name__}")
                        else:
                            try:
                                # Execute the undo operation
                                execute_reversible_operation(operation)
                                print(f"[UNDONE] {operation.__class__.__name__}: {operation}")
                                operations_undone += 1
                            except Exception as e:
                                print(f"[ERROR] Failed to rollback operation {operation}: {e}")
                                # Log the error
                                audit_logger.log_event(AuditEventType.SYSTEM_ERROR, {
                                    'operation': str(operation),
                                    'error': str(e),
                                    'rollback_step': i + 1
                                })
                    else:
                        print("[PLUGIN] No more operations to rollback.")
                        break

            elif args.operation == 'all':
                # Rollback all operations
                print(f"[PLUGIN] Rolling back all {len(operation_stack)} operations...")
                
                while operation_stack:
                    operation = operation_stack.pop()
                    if args.dry_run:
                        print(f"[DRY-RUN] Would rollback: {operation.__class__.__name__}")
                    else:
                        try:
                            execute_reversible_operation(operation)
                            print(f"[UNDONE] {operation.__class__.__name__}: {operation}")
                            operations_undone += 1
                        except Exception as e:
                            print(f"[ERROR] Failed to rollback operation {operation}: {e}")
                            # Log the error
                            audit_logger.log_event(AuditEventType.SYSTEM_ERROR, {
                                'operation': str(operation),
                                'error': str(e),
                                'rollback_all': True
                            })

            elif args.operation == 'to-point':
                # Rollback to a specific point
                if not args.point:
                    print("[ERROR] --point is required for 'to-point' operation")
                    return 1
                
                print(f"[PLUGIN] Rolling back to operation point: {args.point}")
                
                # Find the target operation in the stack
                operations_to_keep = []
                operations_to_rollback = []
                
                while operation_stack:
                    op = operation_stack.pop()
                    if str(op) == args.point or hasattr(op, 'id') and str(getattr(op, 'id')) == args.point:
                        # Found the target, keep this operation and put others back
                        operations_to_keep.append(op)
                        break
                    else:
                        operations_to_rollback.append(op)
                
                # Rollback the operations
                for op in reversed(operations_to_rollback):
                    if args.dry_run:
                        print(f"[DRY-RUN] Would rollback: {op.__class__.__name__}")
                    else:
                        try:
                            execute_reversible_operation(op)
                            print(f"[UNDONE] {op.__class__.__name__}: {op}")
                            operations_undone += 1
                        except Exception as e:
                            print(f"[ERROR] Failed to rollback operation {op}: {e}")
                            # Log the error
                            audit_logger.log_event(AuditEventType.SYSTEM_ERROR, {
                                'operation': str(op),
                                'error': str(e),
                                'rollback_to_point': args.point
                            })
                
                # Put the kept operations back on the stack
                for op in reversed(operations_to_keep):
                    operation_stack.append(op)

            if args.dry_run:
                print(f"\n[PLUGIN] Dry run complete. Would rollback {operations_undone} operations.")
            else:
                print(f"\n[PLUGIN] Rollback complete. Undid {operations_undone} operations.")

            # Log rollback completion
            audit_logger.log_rollback_completed(
                operations_undone=operations_undone,
                operation_type=args.operation
            )

            self._on_rollback_complete(operations_undone=operations_undone)
            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Rollback failed: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            # Log the error
            audit_logger = get_audit_logger()
            audit_logger.log_event(AuditEventType.ROLLBACK_FAILED, {
                'operation': getattr(args, 'operation', 'unknown'),
                'error': str(e),
                'traceback': str(traceback.format_exc()) if 'traceback' in locals() else None
            })
            return 1

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., '1.0 KB', '2.5 MB')
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{int(size_bytes)} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., '1.0 KB', '2.5 MB')
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{int(size_bytes)} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


# Create plugin instance when module is loaded
rollback_plugin = RollbackPlugin()


def register_plugin():
    """Register plugin with core system."""
    return rollback_plugin


# Export plugin interface
__all__ = ['rollback_plugin', 'register_plugin']
