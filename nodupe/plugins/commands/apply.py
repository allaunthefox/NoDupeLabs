# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Apply plugin for NoDupeLabs.

This plugin provides the apply functionality as a plugin that can be
loaded by the core system. It demonstrates how to convert existing
modules to plugins.

Key Features:
    - File management actions
    - Duplicate handling
    - Progress tracking
    - Plugin integration

Dependencies:
    - Core modules
"""

from typing import Any, Dict
import argparse
import os
from pathlib import Path
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.filesystem import Filesystem
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.backup import create_backup_before_operation
from nodupe.core.confirmation import get_confirmation_manager
from nodupe.core.undo import execute_reversible_operation, DeleteFileOperation, MoveFileOperation, CopyFileOperation
from nodupe.core.hash_progressive import ProgressiveHasher, get_progressive_hasher

# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {
    "uuid": "a1b2c3d4-e5f6-4490-8bc4-ef1234567890",
    "name": "apply",
    "display_name": "File Apply Plugin",
    "version": "v1.0.0",
    "description": "Apply actions to duplicate files",
    "author": "NoDupeLabs Team",
    "category": "utility",
    "dependencies": [],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["file-management", "duplicate-handling", "apply-actions"],
    "marketplace_id": "apply_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}


class ApplyPlugin(Plugin):
    """Apply plugin implementation."""

    def __init__(self):
        """Initialize apply plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['apply']}

    def _on_apply_start(self, **kwargs: Any) -> None:
        """Handle apply start event."""
        print(f"[PLUGIN] Apply started: {kwargs.get('action', 'unknown')}")

    def _on_apply_complete(self, **kwargs: Any) -> None:
        """Handle apply complete event."""
        print(f"[PLUGIN] Apply completed: {kwargs.get('files_processed', 0)} files processed")

    def register_commands(self, subparsers: Any) -> None:
        """Register apply command with argument parser."""
        apply_parser = subparsers.add_parser('apply', help='Apply actions to duplicates')
        apply_parser.add_argument(
            'action',
            choices=['delete', 'move', 'copy', 'list'],
            help='Action to perform'
        )
        apply_parser.add_argument(
            '--destination', '-d',
            help='Destination directory (required for move/copy)'
        )
        apply_parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
        apply_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        apply_parser.set_defaults(func=self.execute_apply)

    def execute_apply(self, args: argparse.Namespace) -> int:
        """Execute apply command.

        Args:
            args: Command arguments including injected 'container'
        """
        try:
            # Validation
            # Check if input is provided (for compatibility with tests)
            if hasattr(args, 'input') and args.input is None:
                print("[ERROR] Input file is required")
                return 1
            
            # Validate input file exists
            if hasattr(args, 'input') and args.input:
                import os
                if not os.path.exists(args.input):
                    print(f"[ERROR] Input file does not exist: {args.input}")
                    return 1
            
            # Validate action is one of the allowed choices
            valid_actions = ['delete', 'move', 'copy', 'list']
            if args.action not in valid_actions:
                print(f"[ERROR] Invalid action: {args.action}. Must be one of: {', '.join(valid_actions)}")
                return 1
            
            # Validate destination for move/copy actions
            if args.action in ['move', 'copy'] and not args.destination:
                print("[ERROR] --destination is required for move/copy actions")
                return 1
            
            # Validate target directory for move/copy
            if args.action in ['move', 'copy']:
                if hasattr(args, 'destination') and args.destination:
                    import os
                    if not os.path.exists(args.destination):
                        print(f"[ERROR] Target directory does not exist: {args.destination}")
                        return 1
            
            print(f"[PLUGIN] Executing apply command: {args.action}")

            # Initialize audit logger
            audit_logger = get_audit_logger()
            audit_logger.log_apply_started(args.action, vars(args))

            # 1. Get services
            container = getattr(args, 'container', None)
            if not container:
                print("[ERROR] Dependency container not available")
                return 1

            db_connection = container.get_service('database')
            if not db_connection:
                print("[ERROR] Database service not available")
                # Fallback to default
                db_connection = DatabaseConnection.get_instance()

            file_repo = FileRepository(db_connection)

            # 2. Get duplicates
            duplicates = file_repo.get_duplicate_files()
            if not duplicates:
                print("[PLUGIN] No items marked as duplicates in database.")
                print("         (Did you run 'scan' and 'sim' commands first?)")
                return 0

            print(f"[PLUGIN] Found {len(duplicates)} duplicate files identified in database")

            files_processed = 0

            if args.action == 'list':
                print("\nIdentified Duplicates:")
                for dup in duplicates:
                    original_id = dup['duplicate_of']
                    original = file_repo.get_file(original_id)
                    orig_path = original['path'] if original else "?"
                    print(f"  {dup['path']} (Duplicate of: {orig_path})")
                return 0

            # Prepare file information for confirmation and backup
            files_to_process = []
            for dup in duplicates:
                path = Path(dup['path'])
                if path.exists():
                    files_to_process.append({
                        'path': str(path),
                        'size': path.stat().st_size,
                        'id': dup['id']
                    })

            # User confirmation for destructive operations
            if args.action in ['delete', 'move'] and not args.dry_run:
                confirmation_mgr = get_confirmation_manager()
                if not confirmation_mgr.confirm_apply_action(args.action, files_to_process):
                    print("[PLUGIN] Operation cancelled by user.")
                    return 0

            # Create backup before destructive operations
            if args.action in ['delete', 'move'] and not args.dry_run:
                backup_files = [Path(f['path']) for f in files_to_process]
                backup_path = create_backup_before_operation(
                    operation=args.action,
                    description=f"Before {args.action} operation",
                    files=backup_files
                )
                if backup_path:
                    print(f"[PLUGIN] Backup created: {backup_path}")
                    audit_logger.log_backup_created(backup_path, args.action, len(backup_files))
                else:
                    print("[WARNING] Failed to create backup, but proceeding with operation.")

            # 3. Process Actions
            for dup in duplicates:
                path = Path(dup['path'])

                try:
                    if not path.exists():
                        print(f"[WARN] File not found: {path} (skipping)")
                        continue

                    if args.action == 'delete':
                        if args.dry_run:
                            print(f"[DRY-RUN] Would delete: {path}")
                        else:
                            # Use reversible delete operation
                            delete_op = DeleteFileOperation(path)
                            execute_reversible_operation(delete_op)
                            file_repo.delete_file(dup['id'])
                            print(f"[DELETED] {path}")

                    elif args.action in ['move', 'copy']:
                        if not args.destination:  # Should verify logic above
                            continue

                        dest_dir = Path(args.destination)
                        dest_path = dest_dir / path.name

                        # Handle collision
                        if dest_path.exists():
                            # Simple rename logic
                            stem = dest_path.stem
                            suffix = dest_path.suffix
                            dest_path = dest_dir / f"{stem}_{dup['id']}{suffix}"

                        if args.action == 'move':
                            if args.dry_run:
                                print(f"[DRY-RUN] Would move: {path} -> {dest_path}")
                            else:
                                # Use reversible move operation
                                move_op = MoveFileOperation(path, dest_path)
                                execute_reversible_operation(move_op)
                                # Update DB to point to new location or just delete entry?
                                # Usually duplicates are processed to get rid of them or archive them.
                                # If moved, we might update the path in DB or remove if 'archived' implies removal from active working set.
                                # Let's remove from DB as "processed duplicate".
                                file_repo.delete_file(dup['id'])
                                print(f"[MOVED] {path} -> {dest_path}")

                        elif args.action == 'copy':
                            if args.dry_run:
                                print(f"[DRY-RUN] Would copy: {path} -> {dest_path}")
                            else:
                                # Use reversible copy operation
                                copy_op = CopyFileOperation(path, dest_path)
                                execute_reversible_operation(copy_op)
                                print(f"[COPIED] {path} -> {dest_path}")

                    files_processed += 1

                except Exception as e:
                    print(f"[ERROR] Failed to process {path}: {e}")
                    audit_logger.log_event(AuditEventType.SYSTEM_ERROR, {
                        'file_path': str(path),
                        'error': str(e),
                        'operation': args.action
                    })

            if args.dry_run:
                print(f"\n[PLUGIN] Dry run complete. Would process {files_processed} files.")
            else:
                print(f"\n[PLUGIN] Apply complete. Processed {files_processed} files.")

            self._on_apply_complete(files_processed=files_processed)
            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Apply failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            # Log the error
            audit_logger = get_audit_logger()
            audit_logger.log_event(AuditEventType.APPLY_FAILED, {
                'action': getattr(args, 'action', 'unknown'),
                'error': str(e),
                'traceback': str(traceback.format_exc()) if 'traceback' in locals() else None
            })
            return 1


# Create plugin instance when module is loaded
apply_plugin = ApplyPlugin()

# Register plugin with core system


def register_plugin():
    """Register plugin with core system."""
    return apply_plugin


# Export plugin interface
__all__ = ['apply_plugin', 'register_plugin']
