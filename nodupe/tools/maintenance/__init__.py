"""Rollback System for NoDupeLabs.

This module provides transaction logging and snapshot capabilities
to ensure data safety during deduplication operations.

Key Features:
    - Snapshot creation and restoration
    - Transaction logging
    - Rollback capabilities
    - CLI integration

Classes:
    Snapshot: Represents a point-in-time capture of file metadata
    SnapshotManager: Manages file snapshots for rollback
    TransactionLog: Logs operations for rollback capability
    RollbackManager: High-level rollback orchestration
"""

from .manager import RollbackManager
from .snapshot import (
    HASH_ALGORITHMS,
    Snapshot,
    SnapshotFile,
    SnapshotManager,
    get_hasher,
)
from .transaction import Operation, TransactionLog

__all__ = [
    "Snapshot",
    "SnapshotFile",
    "SnapshotManager",
    "TransactionLog",
    "Operation",
    "RollbackManager",
    "HASH_ALGORITHMS",
    "get_hasher",
]
