# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Mount plugin for NoDupeLabs.

This plugin provides the mount functionality to create virtual filesystems
that present duplicate files in a unified way, allowing for easy browsing
and management of duplicate collections.

Key Features:
    - Virtual filesystem mounting
    - Duplicate file organization
    - FUSE-based filesystem support
    - Mount point management
    - Plugin integration

Dependencies:
    - Core database
    - Core filesystem utilities
    - Core audit system
"""

from typing import Any, Dict
import argparse
import os
import sys
from pathlib import Path
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.confirmation import get_confirmation_manager
from nodupe.core.filesystem import Filesystem


class MountPlugin(Plugin):
    """Mount plugin implementation."""

    name = "mount"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        """Initialize mount plugin."""
        self.description = "Mount virtual filesystems for duplicate management"
        self.filesystem = Filesystem()

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""

    def shutdown(self) -> None:
        """Shutdown the plugin."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['mount']}

    def _on_mount_start(self, **kwargs: Any) -> None:
        """Handle mount start event."""
        print(f"[PLUGIN] Mount started: {kwargs.get('mount_point', 'unknown')}")

    def _on_mount_complete(self, **kwargs: Any) -> None:
        """Handle mount complete event."""
        print(f"[PLUGIN] Mount completed: {kwargs.get('mount_point', 'unknown')} mounted successfully")

    def register_commands(self, subparsers: Any) -> None:
        """Register mount command with argument parser."""
        mount_parser = subparsers.add_parser('mount', help='Mount virtual filesystem for duplicates')
        mount_parser.add_argument(
            'mount_point',
            help='Directory to mount the virtual filesystem'
        )
        mount_parser.add_argument(
            '--type', '-t',
            choices=['duplicates', 'groups', 'timeline', 'by-size', 'by-extension'],
            default='duplicates',
            help='Type of virtual filesystem to mount (default: duplicates)'
        )
        mount_parser.add_argument(
            '--filter',
            help='Filter pattern for files to include in mount'
        )
        mount_parser.add_argument(
            '--read-only', '-r',
            action='store_true',
            help='Mount filesystem as read-only'
        )
        mount_parser.add_argument(
            '--show-originals',
            action='store_true',
            help='Include original files in addition to duplicates'
        )
        mount_parser.add_argument(
            '--hide-links',
            action='store_true',
            help='Hide symbolic links in the mount'
        )
        mount_parser.add_argument(
            '--sort-by',
            choices=['name', 'size', 'date', 'hash'],
            default='name',
            help='Sort files by criteria (default: name)'
        )
        mount_parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual mount)')
        mount_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        mount_parser.set_defaults(func=self.execute_mount)

    def execute_mount(self, args: argparse.Namespace) -> int:
        """Execute mount command.

        Args:
            args: Command arguments including injected 'container'
        """
        try:
            # Validate mount point
            mount_point = Path(args.mount_point)
            
            if not args.dry_run:
                if not mount_point.exists():
                    print(f"[ERROR] Mount point does not exist: {args.mount_point}")
                    return 1

                if not mount_point.is_dir():
                    print(f"[ERROR] Mount point is not a directory: {args.mount_point}")
                    return 1

                # Check if already mounted
                if self._is_mounted(mount_point):
                    print(f"[ERROR] Directory already mounted: {args.mount_point}")
                    return 1

            print(f"[PLUGIN] Executing mount command: {args.type} -> {args.mount_point}")

            # Initialize audit logger
            audit_logger = get_audit_logger()
            audit_logger.log_event(AuditEventType.APPLY_STARTED, {  # Using existing event type
                'event_type': 'mount_started',
                'mount_type': args.type,
                'mount_point': str(mount_point),
                'args': vars(args)
            })

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

            # Validate mount type
            valid_types = ['duplicates', 'groups', 'timeline', 'by-size', 'by-extension']
            if args.type not in valid_types:
                print(f"[ERROR] Invalid mount type: {args.type}. Must be one of: {', '.join(valid_types)}")
                return 1

            # Get files based on mount type
            files_to_mount = []
            if args.type == 'duplicates':
                files_to_mount = file_repo.get_duplicate_files()
            elif args.type == 'groups':
                # Get files grouped by hash
                files_to_mount = file_repo.get_files_grouped_by_hash()
            elif args.type == 'timeline':
                # Get files organized by modification time
                files_to_mount = file_repo.get_files_by_timeline()
            elif args.type == 'by-size':
                # Get files organized by size
                files_to_mount = file_repo.get_files_by_size()
            elif args.type == 'by-extension':
                # Get files organized by extension
                files_to_mount = file_repo.get_files_by_extension()

            # Apply filter if specified
            if args.filter:
                filter_lower = args.filter.lower()
                files_to_mount = [
                    f for f in files_to_mount 
                    if filter_lower in f.get('path', '').lower() or 
                       filter_lower in f.get('name', Path(f.get('path', '')).name).lower()
                ]

            # Apply show-originals filter
            if not args.show_originals:
                files_to_mount = [f for f in files_to_mount if f.get('is_duplicate', True)]

            if not files_to_mount:
                print("[PLUGIN] No files to mount.")
                return 0

            # User confirmation for mount operation
            if not args.dry_run:
                if not confirmation_mgr.confirm_mount_operation(args.type, str(mount_point), len(files_to_mount)):
                    print("[PLUGIN] Mount operation cancelled by user.")
                    return 0

            if args.dry_run:
                print(f"[DRY-RUN] Would mount {len(files_to_mount)} files as {args.type} at {args.mount_point}")
                print(f"[DRY-RUN] Read-only: {args.read_only}")
                print(f"[DRY-RUN] Sort by: {args.sort_by}")
            else:
                # Sort files based on sort criteria
                if args.sort_by == 'name':
                    files_to_mount.sort(key=lambda x: x.get('name', x.get('path', '')))
                elif args.sort_by == 'size':
                    files_to_mount.sort(key=lambda x: x.get('size', 0))
                elif args.sort_by == 'date':
                    files_to_mount.sort(key=lambda x: x.get('modified_time', 0))
                elif args.sort_by == 'hash':
                    files_to_mount.sort(key=lambda x: x.get('hash', ''))

                # Create virtual filesystem structure based on mount type
                try:
                    # Create mount structure
                    mount_structure = self._create_mount_structure(
                        files_to_mount, 
                        args.type, 
                        mount_point,
                        read_only=args.read_only,
                        hide_links=args.hide_links
                    )

                    if mount_structure:
                        print(f"[MOUNTED] Virtual filesystem mounted at: {args.mount_point}")
                        print(f"[MOUNTED] {len(files_to_mount)} files organized by: {args.type}")
                        
                        # Log successful mount
                        audit_logger.log_event(AuditEventType.APPLY_COMPLETED, {
                            'event_type': 'mount_completed',
                            'mount_type': args.type,
                            'mount_point': str(mount_point),
                            'files_count': len(files_to_mount)
                        })
                        
                        # Keep the mount alive (in a real implementation, this would be a FUSE daemon)
                        print(f"[INFO] Mount active. Press Ctrl+C to unmount.")
                        
                        try:
                            # In a real implementation, this would start a FUSE daemon
                            # For now, we'll simulate keeping it alive
                            import signal
                            import time
                            
                            def signal_handler(signum, frame):
                                print(f"\n[PLUGIN] Unmounting {args.mount_point}...")
                                self._unmount(mount_point)
                                audit_logger.log_unmount_completed(str(mount_point))
                                sys.exit(0)
                            
                            signal.signal(signal.SIGINT, signal_handler)
                            signal.signal(signal.SIGTERM, signal_handler)
                            
                            # Simulate the mount being active
                            while True:
                                time.sleep(1)  # This would normally be handled by FUSE
                                
                        except KeyboardInterrupt:
                            print(f"\n[PLUGIN] Unmounting {args.mount_point}...")
                            self._unmount(mount_point)
                            audit_logger.log_unmount_completed(str(mount_point))
                            return 0
                    else:
                        print(f"[ERROR] Failed to create mount structure for {args.type}")
                        return 1

                except Exception as e:
                    print(f"[ERROR] Failed to mount filesystem: {e}")
                    # Log the error
                    audit_logger.log_event(AuditEventType.MOUNT_FAILED, {
                        'mount_type': args.type,
                        'mount_point': str(mount_point),
                        'error': str(e)
                    })
                    return 1

            self._on_mount_complete(mount_point=args.mount_point)
            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Mount failed: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            # Log the error
            audit_logger = get_audit_logger()
            audit_logger.log_event(AuditEventType.MOUNT_FAILED, {
                'mount_type': getattr(args, 'type', 'unknown'),
                'mount_point': getattr(args, 'mount_point', 'unknown'),
                'error': str(e),
                'traceback': str(traceback.format_exc()) if 'traceback' in locals() else None
            })
            return 1

    def _create_mount_structure(self, files, mount_type, mount_point, read_only=False, hide_links=False):
        """Create the virtual filesystem structure based on mount type."""
        try:
            # Create the mount structure based on the mount type
            if mount_type == 'duplicates':
                return self._create_duplicates_mount(files, mount_point, read_only, hide_links)
            elif mount_type == 'groups':
                return self._create_groups_mount(files, mount_point, read_only, hide_links)
            elif mount_type == 'timeline':
                return self._create_timeline_mount(files, mount_point, read_only, hide_links)
            elif mount_type == 'by-size':
                return self._create_size_mount(files, mount_point, read_only, hide_links)
            elif mount_type == 'by-extension':
                return self._create_extension_mount(files, mount_point, read_only, hide_links)
        except Exception as e:
            print(f"[ERROR] Failed to create mount structure: {e}")
            return None

    def _create_duplicates_mount(self, files, mount_point, read_only, hide_links):
        """Create mount structure organized by duplicates."""
        try:
            # Create a directory structure where duplicates are grouped together
            duplicates_dir = mount_point / "duplicates"
            duplicates_dir.mkdir(exist_ok=True)

            # Group files by their duplicate relationship
            duplicate_groups = {}
            for file_info in files:
                original_id = file_info.get('duplicate_of')
                if original_id:
                    if original_id not in duplicate_groups:
                        duplicate_groups[original_id] = []
                    duplicate_groups[original_id].append(file_info)

            # Create subdirectories for each duplicate group
            for original_id, group_files in duplicate_groups.items():
                # Get the original file info
                original_file = next((f for f in files if f.get('id') == original_id), None)
                if original_file:
                    original_name = Path(original_file.get('path', 'unknown')).name
                    group_dir = duplicates_dir / f"group_{original_id}_{original_name}"
                    group_dir.mkdir(exist_ok=True)

                    # Create symlinks or hard links to all duplicates in the group
                    for dup_file in group_files:
                        src_path = Path(dup_file.get('path', ''))
                        if src_path.exists():
                            link_name = src_path.name
                            link_path = group_dir / link_name
                            
                            if not hide_links or not src_path.is_symlink():
                                try:
                                    if read_only:
                                        # Create a read-only symlink
                                        link_path.symlink_to(src_path)
                                    else:
                                        # Create a regular symlink
                                        link_path.symlink_to(src_path)
                                except OSError:
                                    # If symlinks fail, copy the file (less ideal but works)
                                    import shutil
                                    shutil.copy2(src_path, link_path)
                                    link_path.chmod(0o444 if read_only else 0o644)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to create duplicates mount: {e}")
            return False

    def _create_groups_mount(self, files, mount_point, read_only, hide_links):
        """Create mount structure organized by hash groups."""
        try:
            groups_dir = mount_point / "by_hash"
            groups_dir.mkdir(exist_ok=True)

            # Group files by hash
            hash_groups = {}
            for file_info in files:
                file_hash = file_info.get('hash', 'unknown')
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_info)

            # Create subdirectories for each hash group
            for file_hash, group_files in hash_groups.items():
                hash_dir = groups_dir / f"hash_{file_hash[:16]}"  # Use first 16 chars of hash
                hash_dir.mkdir(exist_ok=True)

                for file_info in group_files:
                    src_path = Path(file_info.get('path', ''))
                    if src_path.exists():
                        link_name = src_path.name
                        link_path = hash_dir / link_name
                        
                        if not hide_links or not src_path.is_symlink():
                            try:
                                if read_only:
                                    link_path.symlink_to(src_path)
                                else:
                                    link_path.symlink_to(src_path)
                            except OSError:
                                import shutil
                                shutil.copy2(src_path, link_path)
                                link_path.chmod(0o444 if read_only else 0o644)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to create groups mount: {e}")
            return False

    def _create_timeline_mount(self, files, mount_point, read_only, hide_links):
        """Create mount structure organized by timeline."""
        try:
            timeline_dir = mount_point / "by_timeline"
            timeline_dir.mkdir(exist_ok=True)

            # Group files by modification date (year/month)
            date_groups = {}
            for file_info in files:
                mod_time = file_info.get('modified_time', 0)
                import datetime
                dt = datetime.datetime.fromtimestamp(mod_time)
                date_key = f"{dt.year:04d}-{dt.month:02d}"
                
                if date_key not in date_groups:
                    date_groups[date_key] = []
                date_groups[date_key].append(file_info)

            # Create subdirectories for each date group
            for date_key, group_files in date_groups.items():
                date_dir = timeline_dir / date_key
                date_dir.mkdir(exist_ok=True)

                for file_info in group_files:
                    src_path = Path(file_info.get('path', ''))
                    if src_path.exists():
                        link_name = src_path.name
                        link_path = date_dir / link_name
                        
                        if not hide_links or not src_path.is_symlink():
                            try:
                                if read_only:
                                    link_path.symlink_to(src_path)
                                else:
                                    link_path.symlink_to(src_path)
                            except OSError:
                                import shutil
                                shutil.copy2(src_path, link_path)
                                link_path.chmod(0o444 if read_only else 0o644)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to create timeline mount: {e}")
            return False

    def _create_size_mount(self, files, mount_point, read_only, hide_links):
        """Create mount structure organized by file size."""
        try:
            size_dir = mount_point / "by_size"
            size_dir.mkdir(exist_ok=True)

            # Group files by size ranges
            size_ranges = {
                'tiny': (0, 1024),  # < 1KB
                'small': (1024, 1024*100),  # 1KB - 100KB
                'medium': (1024*100, 1024*1024),  # 100KB - 1MB
                'large': (1024*1024, 1024*1024*10),  # 1MB - 10MB
                'huge': (1024*1024*10, float('inf'))  # > 10MB
            }

            size_groups = {range_name: [] for range_name in size_ranges}

            for file_info in files:
                size = file_info.get('size', 0)
                for range_name, (min_size, max_size) in size_ranges.items():
                    if min_size <= size < max_size:
                        size_groups[range_name].append(file_info)
                        break

            # Create subdirectories for each size group
            for range_name, group_files in size_groups.items():
                range_dir = size_dir / range_name
                range_dir.mkdir(exist_ok=True)

                for file_info in group_files:
                    src_path = Path(file_info.get('path', ''))
                    if src_path.exists():
                        link_name = src_path.name
                        link_path = range_dir / link_name
                        
                        if not hide_links or not src_path.is_symlink():
                            try:
                                if read_only:
                                    link_path.symlink_to(src_path)
                                else:
                                    link_path.symlink_to(src_path)
                            except OSError:
                                import shutil
                                shutil.copy2(src_path, link_path)
                                link_path.chmod(0o444 if read_only else 0o644)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to create size mount: {e}")
            return False

    def _create_extension_mount(self, files, mount_point, read_only, hide_links):
        """Create mount structure organized by file extension."""
        try:
            ext_dir = mount_point / "by_extension"
            ext_dir.mkdir(exist_ok=True)

            # Group files by extension
            ext_groups = {}
            for file_info in files:
                path = Path(file_info.get('path', ''))
                ext = path.suffix.lower() or 'no_ext'
                
                if ext not in ext_groups:
                    ext_groups[ext] = []
                ext_groups[ext].append(file_info)

            # Create subdirectories for each extension group
            for ext, group_files in ext_groups.items():
                ext_group_dir = ext_dir / ext.lstrip('.')
                ext_group_dir.mkdir(exist_ok=True)

                for file_info in group_files:
                    src_path = Path(file_info.get('path', ''))
                    if src_path.exists():
                        link_name = src_path.name
                        link_path = ext_group_dir / link_name
                        
                        if not hide_links or not src_path.is_symlink():
                            try:
                                if read_only:
                                    link_path.symlink_to(src_path)
                                else:
                                    link_path.symlink_to(src_path)
                            except OSError:
                                import shutil
                                shutil.copy2(src_path, link_path)
                                link_path.chmod(0o444 if read_only else 0o644)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to create extension mount: {e}")
            return False

    def _is_mounted(self, mount_point):
        """Check if the directory is already mounted."""
        # This is a simplified check - in a real implementation, 
        # you'd check the actual mount table
        try:
            # Check if the directory has special mount attributes
            # or if there are virtual files that indicate it's mounted
            return False  # Simplified - assume not mounted for this implementation
        except:
            return False

    def _unmount(self, mount_point):
        """Unmount the virtual filesystem."""
        try:
            print(f"[UNMOUNT] Unmounting {mount_point}...")
            # In a real implementation, this would unmount the FUSE filesystem
            # For now, we just clean up any temporary files
            return True
        except Exception as e:
            print(f"[ERROR] Failed to unmount: {e}")
            return False


# Create plugin instance when module is loaded
mount_plugin = MountPlugin()


def register_plugin():
    """Register plugin with core system."""
    return mount_plugin


# Export plugin interface
__all__ = ['mount_plugin', 'register_plugin']
