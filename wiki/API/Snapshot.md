# Snapshot API

## SnapshotManager

Manages file snapshots for rollback capability.

### Constructor

```python
SnapshotManager(backup_dir: str = ".nodupe/backups")
```

### Methods

#### create_snapshot

```python
def create_snapshot(self, paths: list[str]) -> Snapshot
```

Create a snapshot of specified paths.

**Parameters:**
- `paths`: List of file paths to snapshot

**Returns:** `Snapshot` object with metadata

**Example:**
```python
from nodupe.core.rollback import SnapshotManager

mgr = SnapshotManager()
snapshot = mgr.create_snapshot(["/data/file1.txt", "/data/file2.txt"])
print(f"Created: {snapshot.snapshot_id}")
```

#### restore_snapshot

```python
def restore_snapshot(self, snapshot_id: str) -> bool
```

Restore files from a snapshot.

**Parameters:**
- `snapshot_id`: ID of snapshot to restore

**Returns:** `True` if successful

#### list_snapshots

```python
def list_snapshots(self) -> list[dict]
```

List all available snapshots.

**Returns:** List of snapshot summaries

#### delete_snapshot

```python
def delete_snapshot(self, snapshot_id: str) -> bool
```

Delete a snapshot.

**Parameters:**
- `snapshot_id`: ID of snapshot to delete

**Returns:** `True` if successful
