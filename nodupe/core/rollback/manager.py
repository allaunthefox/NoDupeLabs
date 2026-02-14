"""Rollback manager for NoDupeLabs."""

from typing import Any, Callable, List, Optional

from .snapshot import Snapshot, SnapshotManager
from .transaction import Operation, TransactionLog


class RollbackManager:
    """High-level rollback orchestration."""

    def __init__(self, snapshot_manager: SnapshotManager, transaction_log: TransactionLog):
        """Initialize rollback manager.

        Args:
            snapshot_manager: Snapshot manager instance
            transaction_log: Transaction log instance
        """
        self.snapshots = snapshot_manager
        self.transactions = transaction_log

    def execute_with_protection(self, paths: List[str], operation: Callable) -> Any:
        """Execute an operation with rollback protection.

        Creates snapshot before, logs operations, rollback on failure.

        Args:
            paths: List of file paths to protect
            operation: Callable to execute

        Returns:
            Result of operation

        Raises:
            Exception: Re-raises any exception from operation
        """
        # Create snapshot before operation
        snapshot = self.snapshots.create_snapshot(paths)

        # Begin transaction
        tx_id = self.transactions.begin_transaction()

        try:
            result = operation()
            # Commit transaction on success
            self.transactions.commit_transaction()
            return result
        except Exception as e:
            # Rollback on failure
            self.transactions.rollback_transaction(tx_id)
            # Try to restore from snapshot
            self.snapshots.restore_snapshot(snapshot.snapshot_id)
            raise e

    def restore_to_snapshot(self, snapshot_id: str) -> bool:
        """Restore entire state to a snapshot.

        Args:
            snapshot_id: ID of snapshot to restore

        Returns:
            True if successful
        """
        return self.snapshots.restore_snapshot(snapshot_id)

    def undo_last_operation(self) -> bool:
        """Undo the most recent operation.

        Returns:
            True if successful
        """
        transactions = self.transactions.list_transactions()
        if not transactions:
            return False

        # Find most recent completed transaction
        for tx in transactions:
            if tx["status"] == "completed":
                return self.transactions.rollback_transaction(tx["transaction_id"])

        return False

    def list_snapshots(self) -> List[dict]:
        """List all available snapshots.

        Returns:
            List of snapshots
        """
        return self.snapshots.list_snapshots()

    def list_transactions(self) -> List[dict]:
        """List all transactions.

        Returns:
            List of transactions
        """
        return self.transactions.list_transactions()
