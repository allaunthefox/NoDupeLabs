# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Archive plugin for NoDupeLabs.

This plugin provides the archive functionality to package and manage
duplicate files in archives, allowing for safe storage and retrieval.

Key Features:
    - File archiving and compression
    - Archive format support (ZIP, TAR, etc.)
    - Archive management and listing
    - Archive verification and integrity checks
    - Plugin integration

Dependencies:
    - Core archive handler
    - Core database
    - Core audit system
"""

from typing import Any, Dict
import argparse
import os
from pathlib import Path
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.archive_handler import ArchiveHandler
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.confirmation import get_confirmation_manager
from nodupe.core.backup import create_backup_before_operation


class ArchivePlugin(Plugin):
    """Archive plugin implementation."""

    name = "archive"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        """Initialize archive plugin."""
        self.description = "Archive and manage duplicate files"
        self.archive_handler = ArchiveHandler()

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""

    def shutdown(self) -> None:
        """Shutdown the plugin."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['archive']}

    def _on_archive_start(self, **kwargs: Any) -> None:
        """Handle archive start event."""
        print(f"[PLUGIN] Archive started: {kwargs.get('action', 'unknown')}")

    def _on_archive_complete(self, **kwargs: Any) -> None:
        """Handle archive complete event."""
        print(f"[PLUGIN] Archive completed: {kwargs.get('files_processed', 0)} files archived")

    def register_commands(self, subparsers: Any) -> None:
        """Register archive command with argument parser."""
        archive_parser = subparsers.add_parser('archive', help='Archive duplicate files')
        archive_parser.add_argument(
            'action',
            choices=['create', 'extract', 'list', 'verify', 'remove'],
            help='Action to perform: create archive, extract archive, list contents, verify integrity, or remove duplicates'
        )
        archive_parser.add_argument(
            'source',
            help='Source file or directory for archive operations'
        )
        archive_parser.add_argument(
            '--destination', '-d',
            help='Destination for archive operations'
        )
        archive_parser.add_argument(
            '--format', '-f',
            choices=['zip', 'tar', 'tar.gz', 'tar.bz2'],
            default='zip',
            help='Archive format (default: zip)'
        )
        archive_parser.add_argument(
            '--compress', '-c',
            choices=['none', 'fast', 'best'],
            default='fast',
            help='Compression level (default: fast)'
        )
        archive_parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
        archive_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        archive_parser.add_argument(
            '--include-duplicates',
            action='store_true',
            help='Include duplicate files in archive'
        )
        archive_parser.set_defaults(func=self.execute_archive)

    def execute_archive(self, args: argparse.Namespace) -> int:
        """Execute archive command.

        Args:
            args: Command arguments including injected 'container'
        """
        try:
            # Validate inputs
            if not os.path.exists(args.source):
                print(f"[ERROR] Source path does not exist: {args.source}")
                return 1

            if args.destination and os.path.exists(args.destination) and not args.dry_run:
                if os.path.isdir(args.destination):
                    print(f"[ERROR] Destination directory already exists: {args.destination}")
                    return 1

            print(f"[PLUGIN] Executing archive command: {args.action} on {args.source}")

            # Initialize audit logger
            audit_logger = get_audit_logger()
            audit_logger.log_archive_started(args.action, vars(args))

            # Initialize confirmation manager
            confirmation_mgr = get_confirmation_manager()

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

            # Validate action
            valid_actions = ['create', 'extract', 'list', 'verify', 'remove']
            if args.action not in valid_actions:
                print(f"[ERROR] Invalid action: {args.action}. Must be one of: {', '.join(valid_actions)}")
                return 1

            files_processed = 0

            if args.action == 'create':
                # Create archive
                if not args.destination:
                    print("[ERROR] --destination is required for create action")
                    return 1

                source_path = Path(args.source)
                dest_path = Path(args.destination)

                # Get files to archive
                files_to_archive = []
                
                if args.include_duplicates:
                    # Get duplicate files from database
                    duplicate_files = file_repo.get_duplicate_files()
                    files_to_archive = [Path(f['path']) for f in duplicate_files if Path(f['path']).exists()]
                    print(f"[PLUGIN] Found {len(files_to_archive)} duplicate files to archive")
                else:
                    # Archive all files in source directory
                    if source_path.is_file():
                        files_to_archive = [source_path]
                    else:
                        for root, dirs, files in os.walk(source_path):
                            for file in files:
                                files_to_archive.append(Path(root) / file)

                if not files_to_archive:
                    print("[PLUGIN] No files to archive.")
                    return 0

                # User confirmation for archive creation
                if not args.dry_run:
                    if not confirmation_mgr.confirm_archive_operation('create', files_to_archive):
                        print("[PLUGIN] Archive operation cancelled by user.")
                        return 0

                if args.dry_run:
                    print(f"[DRY-RUN] Would create archive {dest_path} with {len(files_to_archive)} files")
                else:
                    # Create backup before archive operation
                    backup_path = create_backup_before_operation(
                        operation='archive_create',
                        description=f"Before creating archive {dest_path}",
                        files=files_to_archive
                    )
                    if backup_path:
                        print(f"[PLUGIN] Backup created: {backup_path}")
                        audit_logger.log_backup_created(backup_path, 'archive_create', len(files_to_archive))

                    # Create archive
                    try:
                        # Set compression level based on args
                        compression_map = {
                            'none': 0,
                            'fast': 6,
                            'best': 9
                        }
                        compression_level = compression_map.get(args.compress, 6)

                        self.archive_handler.create_archive(
                            files=files_to_archive,
                            archive_path=dest_path,
                            archive_format=args.format,
                            compression=compression_level
                        )
                        print(f"[ARCHIVED] Created archive: {dest_path}")
                        files_processed = len(files_to_archive)

                        # Update database to mark files as archived
                        for file_path in files_to_archive:
                            file_info = file_repo.get_file_by_path(file_path)
                            if file_info:
                                file_repo.mark_as_archived(file_info['id'], str(dest_path))

                    except Exception as e:
                        print(f"[ERROR] Failed to create archive: {e}")
                        return 1

            elif args.action == 'extract':
                # Extract archive
                if not args.destination:
                    print("[ERROR] --destination is required for extract action")
                    return 1

                archive_path = Path(args.source)
                dest_path = Path(args.destination)

                # User confirmation for extraction
                if not args.dry_run:
                    if not confirmation_mgr.confirm_archive_operation('extract', [archive_path]):
                        print("[PLUGIN] Archive extraction cancelled by user.")
                        return 0

                if args.dry_run:
                    print(f"[DRY-RUN] Would extract archive {archive_path} to {dest_path}")
                else:
                    # Create destination directory if it doesn't exist
                    dest_path.mkdir(parents=True, exist_ok=True)

                    # Extract archive
                    try:
                        extracted_files = self.archive_handler.extract_archive(
                            archive_path=archive_path,
                            output_dir=dest_path
                        )
                        print(f"[EXTRACTED] {len(extracted_files)} files from archive: {archive_path}")
                        files_processed = len(extracted_files)

                        # Update database with extracted files
                        for file_path in extracted_files:
                            # Add extracted file to database
                            stat = file_path.stat()
                            file_repo.add_file(
                                str(file_path),
                                stat.st_size,
                                stat.st_mtime,
                                ''  # hash will be calculated later
                            )

                    except Exception as e:
                        print(f"[ERROR] Failed to extract archive: {e}")
                        return 1

            elif args.action == 'list':
                # List archive contents
                archive_path = Path(args.source)

                if args.dry_run:
                    print(f"[DRY-RUN] Would list contents of archive: {archive_path}")
                else:
                    try:
                        contents = self.archive_handler.list_archive_contents(archive_path)
                        print(f"Contents of {archive_path}:")
                        for item in contents:
                            print(f"  {item}")
                        files_processed = len(contents)
                    except Exception as e:
                        print(f"[ERROR] Failed to list archive contents: {e}")
                        return 1

            elif args.action == 'verify':
                # Verify archive integrity
                archive_path = Path(args.source)

                if args.dry_run:
                    print(f"[DRY-RUN] Would verify archive: {archive_path}")
                else:
                    try:
                        is_valid = self.archive_handler.verify_archive_integrity(archive_path)
                        if is_valid:
                            print(f"[VERIFIED] Archive is valid: {archive_path}")
                        else:
                            print(f"[INVALID] Archive is corrupted: {archive_path}")
                        files_processed = 1
                    except Exception as e:
                        print(f"[ERROR] Failed to verify archive: {e}")
                        return 1

            elif args.action == 'remove':
                # Remove duplicates and archive them
                if not args.destination:
                    print("[ERROR] --destination is required for remove action")
                    return 1

                # Get duplicate files from database
                duplicate_files = file_repo.get_duplicate_files()
                files_to_remove = [Path(f['path']) for f in duplicate_files if Path(f['path']).exists()]

                if not files_to_remove:
                    print("[PLUGIN] No duplicate files to remove and archive.")
                    return 0

                # User confirmation for removal
                if not args.dry_run:
                    if not confirmation_mgr.confirm_archive_operation('remove', files_to_remove):
                        print("[PLUGIN] Remove operation cancelled by user.")
                        return 0

                if args.dry_run:
                    print(f"[DRY-RUN] Would remove and archive {len(files_to_remove)} duplicate files to {args.destination}")
                else:
                    # Create backup before removal
                    backup_path = create_backup_before_operation(
                        operation='archive_remove',
                        description=f"Before removing duplicates and archiving to {args.destination}",
                        files=files_to_remove
                    )
                    if backup_path:
                        print(f"[PLUGIN] Backup created: {backup_path}")
                        audit_logger.log_backup_created(backup_path, 'archive_remove', len(files_to_remove))

                    # Create archive of duplicates
                    dest_path = Path(args.destination)
                    try:
                        self.archive_handler.create_archive(
                            files=files_to_remove,
                            archive_path=dest_path,
                            archive_format=args.format,
                            compression=6  # default compression
                        )
                        print(f"[ARCHIVED] Created archive of duplicates: {dest_path}")

                        # Remove original files
                        for file_path in files_to_remove:
                            try:
                                file_path.unlink()  # Delete file
                                # Update database to mark as removed/archived
                                file_info = file_repo.get_file_by_path(file_path)
                                if file_info:
                                    file_repo.mark_as_archived(file_info['id'], str(dest_path))
                                print(f"[REMOVED] {file_path}")
                                files_processed += 1
                            except Exception as e:
                                print(f"[ERROR] Failed to remove {file_path}: {e}")

                    except Exception as e:
                        print(f"[ERROR] Failed to archive and remove duplicates: {e}")
                        return 1

            if args.dry_run:
                print(f"\n[PLUGIN] Dry run complete. Would process {files_processed} files.")
            else:
                print(f"\n[PLUGIN] Archive operation complete. Processed {files_processed} files.")

            # Log archive completion
            audit_logger.log_archive_completed(
                action=args.action,
                files_processed=files_processed
            )

            self._on_archive_complete(files_processed=files_processed)
            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Archive failed: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            # Log the error
            audit_logger = get_audit_logger()
            audit_logger.log_event(AuditEventType.ARCHIVE_FAILED, {
                'action': getattr(args, 'action', 'unknown'),
                'error': str(e),
                'traceback': str(traceback.format_exc()) if 'traceback' in locals() else None
            })
            return 1


# Create plugin instance when module is loaded
archive_plugin = ArchivePlugin()


def register_plugin():
    """Register plugin with core system."""
    return archive_plugin


# Export plugin interface
__all__ = ['archive_plugin', 'register_plugin']
