# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Undo/Reversible operations system for NoDupeLabs.

This module provides reversible operations with undo stack functionality
for safe file management operations.
"""

import shutil
from pathlib import Path
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime
from nodupe.core.audit import get_audit_logger, AuditEventType


class ReversibleOperation(Protocol):
    """Protocol for operations that can be undone."""

    def execute(self) -> None:
        """Execute the operation."""
        ...

    def undo(self) -> None:
        """Undo the operation."""
        ...

    def description(self) -> str:
        """Get description of the operation."""
        ...


class DeleteFileOperation:
    """Reversible file deletion (moves to trash directory)."""

    def __init__(self, file_path: Path, trash_dir: Optional[Path] = None):
        """Initialize delete operation.
        
        Args:
            file_path: Path to file to delete
            trash_dir: Directory to move file to (defaults to .nodupe-trash)
        """
        self.file_path = file_path
        self.trash_dir = trash_dir or Path(".nodupe-trash")
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique trash path to avoid conflicts
        self.trash_path = self.trash_dir / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.original_exists = file_path.exists()

    def execute(self) -> None:
        """Execute file deletion by moving to trash."""
        if self.file_path.exists():
            shutil.move(str(self.file_path), str(self.trash_path))
            # Log the deletion
            audit_logger = get_audit_logger()
            audit_logger.log_file_deleted(self.file_path, self.file_path.stat().st_size)

    def undo(self) -> None:
        """Restore file from trash."""
        if self.trash_path.exists():
            shutil.move(str(self.trash_path), str(self.file_path))
            # Log the restoration
            audit_logger = get_audit_logger()
            audit_logger.log_event(AuditEventType.FILE_DELETED, {
                'file_path': str(self.file_path),
                'size': self.file_path.stat().st_size,
                'action': 'restore'
            })

    def description(self) -> str:
        """Get operation description."""
        return f"Delete file: {self.file_path}"


class MoveFileOperation:
    """Reversible file move operation."""

    def __init__(self, source_path: Path, dest_path: Path):
        """Initialize move operation.
        
        Args:
            source_path: Original file path
            dest_path: Destination path
        """
        self.source_path = source_path
        self.dest_path = dest_path
        self.original_source_exists = source_path.exists()
        self.original_dest_exists = dest_path.exists()
        self.original_dest_backup: Optional[Path] = None

    def execute(self) -> None:
        """Execute file move."""
        if self.dest_path.exists():
            # Backup destination if it exists
            backup_path = self.dest_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(self.dest_path, backup_path)
            self.original_dest_backup = backup_path

        if self.source_path.exists():
            shutil.move(str(self.source_path), str(self.dest_path))
            # Log the move
            audit_logger = get_audit_logger()
            if self.source_path.exists():
                audit_logger.log_file_moved(self.source_path, self.dest_path, self.source_path.stat().st_size)

    def undo(self) -> None:
        """Restore file to original location."""
        if self.dest_path.exists():
            shutil.move(str(self.dest_path), str(self.source_path))
            
        # Restore backup if it existed
        if self.original_dest_backup and self.original_dest_backup.exists():
            shutil.move(str(self.original_dest_backup), str(self.dest_path))

    def description(self) -> str:
        """Get operation description."""
        return f"Move file: {self.source_path} -> {self.dest_path}"


class CopyFileOperation:
    """Reversible file copy operation (removes copied file)."""

    def __init__(self, source_path: Path, dest_path: Path):
        """Initialize copy operation.
        
        Args:
            source_path: Source file path
            dest_path: Destination path
        """
        self.source_path = source_path
        self.dest_path = dest_path
        self.original_dest_exists = dest_path.exists()
        self.original_dest_backup: Optional[Path] = None

    def execute(self) -> None:
        """Execute file copy."""
        if self.dest_path.exists():
            # Backup destination if it exists
            backup_path = self.dest_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(self.dest_path, backup_path)
            self.original_dest_backup = backup_path

        if self.source_path.exists():
            shutil.copy2(self.source_path, self.dest_path)
            # Log the copy
            audit_logger = get_audit_logger()
            audit_logger.log_file_copied(self.source_path, self.dest_path, self.source_path.stat().st_size)

    def undo(self) -> None:
        """Remove copied file."""
        if self.dest_path.exists():
            self.dest_path.unlink()
            
        # Restore backup if it existed
        if self.original_dest_backup and self.original_dest_backup.exists():
            shutil.move(str(self.original_dest_backup), str(self.dest_path))

    def description(self) -> str:
        """Get operation description."""
        return f"Copy file: {self.source_path} -> {self.dest_path}"


class OperationStack:
    """Stack of reversible operations with undo support."""

    def __init__(self, max_size: int = 100):
        """Initialize operation stack.
        
        Args:
            max_size: Maximum number of operations to keep in stack
        """
        self.stack: List[ReversibleOperation] = []
        self.max_size = max_size
        self.audit_logger = get_audit_logger()

    def execute(self, operation: ReversibleOperation) -> None:
        """Execute operation and add to stack.
        
        Args:
            operation: Operation to execute
        """
        operation.execute()
        self.stack.append(operation)

        # Log the operation
        self.audit_logger.log_event(AuditEventType.APPLY_STARTED, {
            'operation': operation.__class__.__name__,
            'description': operation.description(),
            'timestamp': datetime.now().isoformat()
        })

        # Limit stack size
        if len(self.stack) > self.max_size:
            removed_op = self.stack.pop(0)
            # Log that operation was removed from history
            self.audit_logger.log_event(AuditEventType.SYSTEM_ERROR, {
                'operation': 'history_cleanup',
                'removed_operation': removed_op.description()
            })

    def __len__(self) -> int:
        """Get number of operations in stack."""
        return len(self.stack)

    def pop(self) -> ReversibleOperation:
        """Pop the last operation from stack.
        
        Returns:
            The last operation in the stack
            
        Raises:
            IndexError: If stack is empty
        """
        if not self.stack:
            raise IndexError("pop from empty operation stack")
        return self.stack.pop()

    def append(self, operation: ReversibleOperation) -> None:
        """Append an operation to the stack."""
        self.stack.append(operation)

    def undo_last(self) -> bool:
        """Undo the last operation.
        
        Returns:
            True if undo was successful, False if no operations to undo
        """
        if not self.stack:
            return False

        operation = self.stack.pop()
        try:
            operation.undo()
            self.audit_logger.log_event(AuditEventType.APPLY_COMPLETED, {
                'operation': f"undo_{operation.__class__.__name__}",
                'description': f"Undo: {operation.description()}",
                'timestamp': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            self.audit_logger.log_event(AuditEventType.SYSTEM_ERROR, {
                'operation': 'undo_failed',
                'description': operation.description(),
                'error': str(e)
            })
            raise

    def undo_all(self) -> int:
        """Undo all operations in reverse order.
        
        Returns:
            Number of operations successfully undone
        """
        count = 0
        while self.stack:
            try:
                if self.undo_last():
                    count += 1
            except Exception:
                # Continue with other operations even if one fails
                continue
        return count

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get operation history.
        
        Returns:
            List of operation descriptions and timestamps
        """
        return [
            {
                'operation': op.__class__.__name__,
                'description': op.description(),
                'timestamp': datetime.now().isoformat()  # In real implementation, store actual timestamp
            }
            for op in self.stack
        ]

    def clear(self) -> None:
        """Clear all operations from stack."""
        self.stack.clear()


# Global operation stack instance
_operation_stack: Optional[OperationStack] = None


def get_operation_stack() -> OperationStack:
    """Get the global operation stack instance."""
    global _operation_stack
    if _operation_stack is None:
        _operation_stack = OperationStack()
    return _operation_stack


def execute_reversible_operation(operation: ReversibleOperation) -> None:
    """Execute a reversible operation and add to stack."""
    stack = get_operation_stack()
    stack.execute(operation)


def undo_last_operation() -> bool:
    """Undo the last operation."""
    stack = get_operation_stack()
    return stack.undo_last()


def undo_all_operations() -> int:
    """Undo all operations."""
    stack = get_operation_stack()
    return stack.undo_all()


__all__ = [
    'ReversibleOperation',
    'DeleteFileOperation',
    'MoveFileOperation', 
    'CopyFileOperation',
    'OperationStack',
    'get_operation_stack',
    'execute_reversible_operation',
    'undo_last_operation',
    'undo_all_operations'
]
