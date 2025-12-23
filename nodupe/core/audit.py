# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Audit logging system for NoDupeLabs.

This module provides comprehensive audit logging for all operations,
including file operations, deletions, modifications, and system events.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum


class AuditEventType(Enum):
    """Audit event types."""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    FILE_PROCESSED = "file_processed"
    DUPLICATE_FOUND = "duplicate_found"
    APPLY_STARTED = "apply_started"
    APPLY_COMPLETED = "apply_completed"
    APPLY_FAILED = "apply_failed"
    ROLLBACK_STARTED = "rollback_started"
    ROLLBACK_COMPLETED = "rollback_completed"
    ROLLBACK_FAILED = "rollback_failed"
    ROLLBACK_OPERATION_FAILED = "rollback_operation_failed"
    ROLLBACK_OPERATION_STARTED = "rollback_operation_started"
    OPERATION_STARTED = "operation_started"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    FILE_COPIED = "file_copied"
    FILE_HARDLINKED = "file_hardlinked"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    BACKUP_FAILED = "backup_failed"
    PLAN_CREATED = "plan_created"
    PLAN_EXECUTED = "plan_executed"
    USER_CONFIRMATION = "user_confirmation"
    SYSTEM_ERROR = "system_error"
    ARCHIVE_STARTED = "archive_started"
    ARCHIVE_COMPLETED = "archive_completed"
    ARCHIVE_FAILED = "archive_failed"
    MOUNT_STARTED = "mount_started"
    MOUNT_COMPLETED = "mount_completed"
    MOUNT_FAILED = "mount_failed"


class AuditLogger:
    """Comprehensive audit logger for tracking all operations."""

    def __init__(self, log_path: Optional[Path] = None):
        """Initialize audit logger.

        Args:
            log_path: Path to audit log file. If None, uses default location.
        """
        self.log_path = log_path or Path("nodupe_audit.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup file logger
        self.logger = logging.getLogger('nodupe.audit')
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_path)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(self, event_type: AuditEventType, details: Dict[str, Any]) -> None:
        """Log an audit event.

        Args:
            event_type: Type of audit event
            details: Event details dictionary
        """
        timestamp = datetime.now().isoformat()
        event_data = {
            'timestamp': timestamp,
            'event_type': event_type.value,
            'details': details
        }

        # Log to file
        message = f"{event_type.value} | {json.dumps(details)}"
        self.logger.info(message)

        # Also write structured JSON for easy parsing
        json_log_path = self.log_path.with_suffix('.json')
        with open(json_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_data) + '\n')

    def log_scan_started(self, paths: list, args: Dict[str, Any]) -> None:
        """Log scan operation started."""
        self.log_event(AuditEventType.SCAN_STARTED, {
            'paths': [str(p) for p in paths],
            'args': args
        })

    def log_scan_completed(self, files_processed: int, duplicates_found: int) -> None:
        """Log scan operation completed."""
        self.log_event(AuditEventType.SCAN_COMPLETED, {
            'files_processed': files_processed,
            'duplicates_found': duplicates_found
        })

    def log_file_processed(self, file_path: Path, size: int, hash_value: str) -> None:
        """Log file processing."""
        self.log_event(AuditEventType.FILE_PROCESSED, {
            'file_path': str(file_path),
            'size': size,
            'hash': hash_value
        })

    def log_duplicate_found(self, original_path: Path, duplicate_path: Path) -> None:
        """Log duplicate file found."""
        self.log_event(AuditEventType.DUPLICATE_FOUND, {
            'original_path': str(original_path),
            'duplicate_path': str(duplicate_path)
        })

    def log_apply_started(self, action: str, args: Dict[str, Any]) -> None:
        """Log apply operation started."""
        self.log_event(AuditEventType.APPLY_STARTED, {
            'action': action,
            'args': args
        })

    def log_file_deleted(self, file_path: Path, size: int) -> None:
        """Log file deletion."""
        self.log_event(AuditEventType.FILE_DELETED, {
            'file_path': str(file_path),
            'size': size
        })

    def log_file_moved(self, source_path: Path, dest_path: Path, size: int) -> None:
        """Log file move operation."""
        self.log_event(AuditEventType.FILE_MOVED, {
            'source_path': str(source_path),
            'dest_path': str(dest_path),
            'size': size
        })

    def log_file_copied(self, source_path: Path, dest_path: Path, size: int) -> None:
        """Log file copy operation."""
        self.log_event(AuditEventType.FILE_COPIED, {
            'source_path': str(source_path),
            'dest_path': str(dest_path),
            'size': size
        })

    def log_backup_created(self, backup_path: Path, operation: str, files_affected: int) -> None:
        """Log backup creation."""
        self.log_event(AuditEventType.BACKUP_CREATED, {
            'backup_path': str(backup_path),
            'operation': operation,
            'files_affected': files_affected
        })

    def log_user_confirmation(self, action: str, confirmed: bool, details: Dict[str, Any]) -> None:
        """Log user confirmation."""
        self.log_event(AuditEventType.USER_CONFIRMATION, {
            'action': action,
            'confirmed': confirmed,
            'details': details
        })

    def log_plan_created(self, strategy: str, duplicate_groups: int, files_affected: int) -> None:
        """Log plan creation."""
        self.log_event(AuditEventType.PLAN_CREATED, {
            'strategy': strategy,
            'duplicate_groups': duplicate_groups,
            'files_affected': files_affected
        })

    def log_rollback_started(self, operation: str, params: Dict[str, Any]) -> None:
        """Log rollback operation started."""
        self.log_event(AuditEventType.ROLLBACK_STARTED, {
            'operation': operation,
            'params': params
        })

    def log_rollback_completed(self, operations_undone: int, operation_type: str) -> None:
        """Log rollback operation completed."""
        self.log_event(AuditEventType.ROLLBACK_COMPLETED, {
            'operations_undone': operations_undone,
            'operation_type': operation_type
        })

    def log_rollback_failed(self, operation: str, error: str, traceback: Optional[str] = None) -> None:
        """Log rollback operation failed."""
        self.log_event(AuditEventType.ROLLBACK_FAILED, {
            'operation': operation,
            'error': error,
            'traceback': traceback
        })

    def log_rollback_operation_failed(self, operation: str, error: str, traceback: Optional[str] = None) -> None:
        """Log rollback operation failure."""
        self.log_event(AuditEventType.ROLLBACK_FAILED, {
            'operation': operation,
            'error': error,
            'traceback': traceback
        })

    def log_archive_started(self, action: str, args: Dict[str, Any]) -> None:
        """Log archive operation started."""
        self.log_event(AuditEventType.ARCHIVE_STARTED, {
            'action': action,
            'args': args
        })

    def log_archive_completed(self, action: str, files_processed: int) -> None:
        """Log archive operation completed."""
        self.log_event(AuditEventType.ARCHIVE_COMPLETED, {
            'action': action,
            'files_processed': files_processed
        })

    def log_mount_started(self, action: str, args: Dict[str, Any]) -> None:
        """Log mount operation started."""
        self.log_event(AuditEventType.MOUNT_STARTED, {
            'action': action,
            'args': args
        })

    def log_mount_completed(self, action: str, files_mounted: int) -> None:
        """Log mount operation completed."""
        self.log_event(AuditEventType.MOUNT_COMPLETED, {
            'action': action,
            'files_mounted': files_mounted
        })


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_event(event_type: AuditEventType, details: Dict[str, Any]) -> None:
    """Convenience function to log audit events."""
    logger = get_audit_logger()
    logger.log_event(event_type, details)


def log_user_confirmation(action: str, confirmed: bool, details: Dict[str, Any]) -> None:
    """Log user confirmation event."""
    audit_event(AuditEventType.USER_CONFIRMATION, {
        'action': action,
        'confirmed': confirmed,
        'details': details
    })


__all__ = [
    'AuditEventType',
    'AuditLogger',
    'get_audit_logger',
    'audit_event',
    'log_user_confirmation'
]
