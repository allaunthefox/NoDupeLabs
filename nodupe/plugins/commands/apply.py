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
from pathlib import Path
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.filesystem import Filesystem
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection


class ApplyPlugin(Plugin):
    """Apply plugin implementation."""

    name = "apply"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        """Initialize apply plugin."""
        self.description = "Apply actions to duplicate files"

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""

    def shutdown(self) -> None:
        """Shutdown the plugin."""

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
            print(f"[PLUGIN] Executing apply command: {args.action}")

            # Validation
            if args.action in ['move', 'copy'] and not args.destination:
                print("[ERROR] --destination is required for move/copy actions")
                return 1

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
                            Filesystem.remove_file(path)
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
                                Filesystem.ensure_directory(dest_dir)
                                Filesystem.move_file(path, dest_path)
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
                                Filesystem.ensure_directory(dest_dir)
                                Filesystem.copy_file(path, dest_path)
                                print(f"[COPIED] {path} -> {dest_path}")

                    files_processed += 1

                except Exception as e:
                    print(f"[ERROR] Failed to process {path}: {e}")

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
            return 1


# Create plugin instance when module is loaded
apply_plugin = ApplyPlugin()

# Register plugin with core system


def register_plugin():
    """Register plugin with core system."""
    return apply_plugin


# Export plugin interface
__all__ = ['apply_plugin', 'register_plugin']
