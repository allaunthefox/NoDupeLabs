"""Compatibility shim for legacy `nodupe.core.rollback` imports.

Re-exports rollback/snapshot related classes from the `nodupe.tools.maintenance`
package where the implementation now lives.
"""

from nodupe.tools.maintenance.manager import RollbackManager
from nodupe.tools.maintenance.snapshot import SnapshotManager
from nodupe.tools.maintenance.transaction import TransactionLog

__all__ = ["RollbackManager", "SnapshotManager", "TransactionLog"]
