# Rollback System

**Status:** Design Document  
**Phase:** 3.1

## Overview

The rollback system provides transaction logging and snapshot capabilities to ensure data safety during deduplication operations. If an operation fails, the system can restore the original state.

## Architecture: Content-Addressable Storage (CAS)

The rollback system uses **Content-Addressable Storage**, an industry-standard pattern also used by:
- **Git** - content-addressed by SHA-1 hash
- **Docker** - image layers by digest
- **IPFS** - content-addressed filesystem
- **S3** - etag/content-hash versioning
- **Enterprise backup systems** - deduplication

This provides:
- **Idempotent backups** - same content = same hash = stored once
- **Deduplication** - backup sizes shrink over time
- **Verifiable integrity** - hash proves content correctness

### How It Works

1. **Content hashing**: Files are hashed using configurable algorithm (default: SHA-256)
2. **Content-addressable storage**: Backup stored at `.nodupe/backups/content/{hash}`
3. **Idempotent**: Same content is only stored once, referenced by hash
4. **Restore**: Copy from content-addressable storage back to original path

### Configurable Hash Algorithms

The system supports multiple hash algorithms:

| Algorithm | Use Case |
|-----------|----------|
| `sha256` | Default, good balance of speed/security |
| `sha512` | Higher security, slower |
| `sha3_256` | Alternative to SHA-256 |
| `blake2b` | Fast, cryptographically secure |
| `blake2s` | Fast, smaller output |

**Configuration:**
```python
# Default SHA-256
mgr = SnapshotManager()

# Use BLAKE2b for speed
mgr = SnapshotManager(hash_algorithm="blake2b")

# Use SHA3-512 for max security
mgr = SnapshotManager(hash_algorithm="sha3_512")
```

```toml
[rollback]
hash_algorithm = "blake2b"
```

## Core Concepts

### Transaction Log

A record of all changes made during a deduplication session.

```json
{
  "transaction_id": "uuid",
  "timestamp": "ISO8601",
  "operations": [
    {
      "type": "delete",
      "path": "/data/file.txt",
      "original_hash": "abc123",
      "backup_path": "/.nodupe/backup/abc123"
    }
  ],
  "status": "completed|failed|rolled_back"
}
```

### Snapshot

A point-in-time capture of file metadata before changes.

```json
{
  "snapshot_id": "uuid",
  "timestamp": "ISO8601",
  "files": [
    {
      "path": "/data/file.txt",
      "hash": "abc123",
      "size": 1024,
      "modified": "ISO8601"
    }
  ]
}
```

## API Design

### SnapshotManager

```python
class SnapshotManager:
    """Manages file snapshots for rollback."""
    
    def create_snapshot(self, paths: list[str]) -> Snapshot:
        """Create a snapshot of specified paths.
        
        Returns:
            Snapshot object with metadata
        """
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore files from a snapshot.
        
        Returns:
            True if successful
        """
    
    def list_snapshots(self) -> list[SnapshotSummary]:
        """List all available snapshots."""
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
```

### TransactionLog

```python
class TransactionLog:
    """Logs operations for rollback capability."""
    
    def begin_transaction(self) -> str:
        """Start a new transaction.
        
        Returns:
            Transaction ID
        """
    
    def log_operation(self, operation: Operation) -> None:
        """Log an operation in the current transaction."""
    
    def commit_transaction(self) -> str:
        """Commit the transaction.
        
        Returns:
            Final status
        """
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback all operations in a transaction.
        
        Returns:
            True if successful
        """
```

### RollbackManager

```python
class RollbackManager:
    """High-level rollback orchestration."""
    
    def __init__(self, snapshot_manager: SnapshotManager, 
                 transaction_log: TransactionLog):
        self.snapshots = snapshot_manager
        self.transactions = transaction_log
    
    def execute_with_protection(self, operation: callable) -> Result:
        """Execute an operation with rollback protection.
        
        Creates snapshot before, logs operations, rollback on failure.
        """
    
    def restore_to_snapshot(self, snapshot_id: str) -> bool:
        """Restore entire state to a snapshot."""
    
    def undo_last_operation(self) -> bool:
        """Undo the most recent operation."""
```

## Rollback Scenarios

### 1. Full Rollback
Restore all files from a snapshot.

**Steps:**
1. Load snapshot metadata
2. For each file in snapshot:
   - Check if current file differs
   - Restore from backup if needed
3. Verify restoration
4. Clean up backups

### 2. Partial Rollback
Restore only specific files.

**Steps:**
1. Load transaction log
2. Filter operations for target paths
3. Restore only those files
4. Verify restoration

### 3. Point-in-Time Recovery
Restore to a specific transaction.

**Steps:**
1. Find snapshot before transaction
2. Load transaction log
3. Identify files changed in transaction
4. Restore only changed files

## CLI Commands

```bash
# List snapshots
nodupe rollback --list

# Create snapshot
nodupe snapshot create --paths /data

# Restore snapshot
nodupe snapshot restore --id <snapshot_id>

# Show transaction log
nodupe rollback --log

# Rollback transaction
nodupe rollback --transaction <transaction_id>

# Undo last operation
nodupe rollback --undo
```

## Configuration

```toml
[rollback]
# Enable rollback system
enabled = true

# Backup directory
backup_dir = ".nodupe/backups"

# Max snapshots to keep
max_snapshots = 10

# Auto-snapshot before operations
auto_snapshot = true

# Snapshot retention days
retention_days = 30
```

## Implementation Checklist

- [x] SnapshotManager class
- [x] TransactionLog class
- [x] RollbackManager class
- [x] CLI commands
- [x] Tests (100% coverage)
