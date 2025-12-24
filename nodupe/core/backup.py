# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Backup management system for NoDupeLabs.

This module provides backup creation and restoration functionality
for protecting against destructive operations.
"""

import shutil
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import zipfile
import hashlib


class BackupError(Exception):
    """Exception raised for backup-related errors."""
    pass


class BackupManager:
    """Manager for creating and restoring backups before destructive operations."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups. If None, uses default location.
        """
        self.backup_dir = backup_dir or Path(".nodupe-backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, operation: str, description: str,
                       files_to_backup: Optional[List[Path]] = None) -> Path:
        """Create a backup snapshot of database and optionally specified files.

        Args:
            operation: Name of the operation being backed up (e.g., 'apply', 'delete')
            description: Description of what's being backed up
            files_to_backup: Optional list of specific files to backup

        Returns:
            Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{operation}_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            # Backup database if it exists
            db_path = Path("nodupe.db")
            if db_path.exists():
                backup_zip.write(str(db_path), f"database/{db_path.name}")

            # Backup specific files if provided
            if files_to_backup:
                for file_path in files_to_backup:
                    if file_path.exists():
                        # Use relative path to avoid absolute path issues
                        arc_path = f"files/{file_path.name}"
                        backup_zip.write(str(file_path), arc_path)

            # Create backup manifest
            manifest = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "description": description,
                "files_backed_up": [str(f) for f in files_to_backup] if files_to_backup else [],
                "database_backed_up": Path("nodupe.db").exists(),
                "file_count": len(files_to_backup) if files_to_backup else 0
            }

            backup_zip.writestr("manifest.json", json.dumps(manifest, indent=2))

        return backup_path

    def create_database_backup(self, operation: str, description: str) -> Path:
        """Create a backup of just the database.

        Args:
            operation: Name of the operation
            description: Description of the backup

        Returns:
            Path to the created backup file
        """
        return self.create_snapshot(operation, description)

    def create_file_backup(self, operation: str, description: str,
                          files: List[Path]) -> Path:
        """Create a backup of specific files.

        Args:
            operation: Name of the operation
            description: Description of the backup
            files: List of files to backup

        Returns:
            Path to the created backup file
        """
        return self.create_snapshot(operation, description, files)

    def restore_from_backup(self, backup_path: Path, restore_database: bool = True,
                           restore_files: bool = True) -> bool:
        """Restore from a backup file.

        Args:
            backup_path: Path to backup file to restore
            restore_database: Whether to restore database
            restore_files: Whether to restore files

        Returns:
            True if restore was successful, False otherwise
        """
        try:
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Extract manifest first
                manifest_data = backup_zip.read("manifest.json")
                manifest = json.loads(manifest_data.decode('utf-8'))

                # Extract database if requested
                if restore_database and manifest.get("database_backed_up"):
                    for file_info in backup_zip.filelist:
                        if file_info.filename.startswith("database/"):
                            backup_zip.extract(file_info, ".")
                            # Move from database/ subdirectory to current directory
                            extracted_path = Path(file_info.filename)
                            if extracted_path.exists():
                                shutil.move(str(extracted_path), str(extracted_path.name))

                # Extract files if requested
                if restore_files:
                    temp_dir = Path(tempfile.mkdtemp())
                    try:
                        # Extract all files to temp directory first
                        backup_zip.extractall(str(temp_dir))

                        # Move files back to their original locations
                        files_dir = temp_dir / "files"
                        if files_dir.exists():
                            for file_path in files_dir.iterdir():
                                # Move file back to original location
                                original_path = Path(file_path.name)
                                if original_path.exists():
                                    original_path.unlink()  # Remove existing file
                                shutil.move(str(file_path), str(original_path))

                    finally:
                        # Clean up temp directory
                        shutil.rmtree(str(temp_dir))

            return True

        except Exception as e:
            print(f"[ERROR] Failed to restore backup {backup_path}: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                    try:
                        manifest_data = backup_zip.read("manifest.json")
                        manifest = json.loads(manifest_data.decode('utf-8'))
                        manifest["backup_file"] = str(backup_file)
                        manifest["size"] = backup_file.stat().st_size
                        backups.append(manifest)
                    except KeyError:
                        # No manifest, create basic info
                        backups.append({
                            "backup_file": str(backup_file),
                            "timestamp": backup_file.stem.split("_")[-2],
                            "size": backup_file.stat().st_size,
                            "description": "Backup without manifest"
                        })
            except zipfile.BadZipFile:
                continue  # Skip corrupted files

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return backups

    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """Remove old backups, keeping only the most recent ones.

        Args:
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        if len(backups) <= keep_count:
            return 0

        backups_to_delete = backups[keep_count:]
        deleted_count = 0

        for backup_info in backups_to_delete:
            try:
                backup_path = Path(backup_info["backup_file"])
                backup_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to delete backup {backup_info['backup_file']}: {e}")

        return deleted_count

    def verify_backup(self, backup_path: Path) -> bool:
        """Verify that a backup file is valid and can be restored.

        Args:
            backup_path: Path to backup file to verify

        Returns:
            True if backup is valid, False otherwise
        """
        try:
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Test if we can read the manifest
                backup_zip.read("manifest.json")
                # Test if we can read all files
                backup_zip.testzip()
                return True
        except Exception:
            return False


# Global backup manager instance
_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """Get the global backup manager instance."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


def create_backup_before_operation(operation: str, description: str,
                                 files: Optional[List[Path]] = None) -> Optional[Path]:
    """Create a backup before a potentially destructive operation.

    Args:
        operation: Name of the operation
        description: Description of what's being backed up
        files: Optional list of files to backup

    Returns:
        Path to backup file, or None if backup failed
    """
    try:
        backup_mgr = get_backup_manager()
        if files:
            return backup_mgr.create_file_backup(operation, description, files)
        else:
            return backup_mgr.create_database_backup(operation, description)
    except Exception as e:
        print(f"[ERROR] Failed to create backup: {e}")
        return None


__all__ = [
    'BackupManager',
    'get_backup_manager',
    'create_backup_before_operation',
    'BackupError'
]
