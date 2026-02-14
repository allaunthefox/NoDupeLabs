"""Transaction logging for rollback system."""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class OperationType(Enum):
    """Types of operations that can be logged."""

    DELETE = "delete"
    MODIFY = "modify"
    MOVE = "move"
    COPY = "copy"
    RESTORE = "restore"


@dataclass
class Operation:
    """Represents a single operation in a transaction."""

    operation_type: str
    path: str
    original_hash: Optional[str] = None
    backup_path: Optional[str] = None
    new_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """Create from dictionary."""
        return cls(**data)


class TransactionLog:
    """Logs operations for rollback capability."""

    def __init__(self, log_dir: str = ".nodupe/backups"):
        """Initialize transaction log.

        Args:
            log_dir: Directory to store transaction logs
        """
        self.log_dir = Path(log_dir)
        self.transaction_dir = self.log_dir / "transactions"
        self.transaction_dir.mkdir(parents=True, exist_ok=True)
        self.current_transaction: Optional[str] = None
        self.current_operations: List[Operation] = []

    def begin_transaction(self) -> str:
        """Start a new transaction.

        Returns:
            Transaction ID
        """
        self.current_transaction = str(uuid.uuid4())[:8]
        self.current_operations = []
        return self.current_transaction

    def log_operation(self, operation: Operation) -> None:
        """Log an operation in the current transaction.

        Args:
            operation: Operation to log
        """
        if self.current_transaction is None:
            raise RuntimeError("No active transaction. Call begin_transaction() first.")
        self.current_operations.append(operation)

    def commit_transaction(self) -> str:
        """Commit the transaction.

        Returns:
            Final status
        """
        if self.current_transaction is None:
            raise RuntimeError("No active transaction.")

        transaction_data = {
            "transaction_id": self.current_transaction,
            "timestamp": datetime.now().isoformat(),
            "operations": [op.to_dict() for op in self.current_operations],
            "status": "completed",
        }

        tx_path = self.transaction_dir / f"{self.current_transaction}.json"
        with open(tx_path, "w") as f:
            json.dump(transaction_data, f, indent=2)

        committed_id = self.current_transaction
        self.current_transaction = None
        self.current_operations = []

        return committed_id

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback all operations in a transaction.

        Args:
            transaction_id: ID of transaction to rollback

        Returns:
            True if successful
        """
        tx_path = self.transaction_dir / f"{transaction_id}.json"
        if not tx_path.exists():
            return False

        with open(tx_path, "r") as f:
            data = json.load(f)

        # Reverse operations for rollback
        for op_data in reversed(data.get("operations", [])):
            op = Operation.from_dict(op_data)
            # Restore from backup if available
            if op.backup_path and Path(op.backup_path).exists():
                import shutil

                shutil.copy2(op.backup_path, op.path)

        # Update transaction status
        data["status"] = "rolled_back"
        with open(tx_path, "w") as f:
            json.dump(data, f, indent=2)

        return True

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction details.

        Args:
            transaction_id: ID of transaction

        Returns:
            Transaction data or None
        """
        tx_path = self.transaction_dir / f"{transaction_id}.json"
        if not tx_path.exists():
            return None

        with open(tx_path, "r") as f:
            data = json.load(f)
            return dict(data)

    def list_transactions(self) -> List[Dict[str, Any]]:
        """List all transactions.

        Returns:
            List of transaction summaries
        """
        transactions = []
        for tx_file in self.transaction_dir.glob("*.json"):
            with open(tx_file, "r") as f:
                data = json.load(f)
                transactions.append(
                    {
                        "transaction_id": data["transaction_id"],
                        "timestamp": data["timestamp"],
                        "status": data["status"],
                        "operation_count": len(data.get("operations", [])),
                    }
                )
        return sorted(transactions, key=lambda x: x["timestamp"], reverse=True)
