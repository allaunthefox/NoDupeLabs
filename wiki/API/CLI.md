# CLI Reference

## Commands

### scan

Scan a directory for files.

```bash
nodupe scan <directory> [options]
```

Options:
- `--threads N` - Number of threads
- `--hash-size N` - Hash chunk size

### apply

Apply changes from a plan.

```bash
nodupe apply --plan <plan.json>
```

### similarity

Find similar files.

```bash
nodupe similarity --file <file>
```

### verify

Verify file integrity.

```bash
nodupe verify --database <db>
```

### version

Show version information.

```bash
nodupe version
```

### Rollback Commands

#### rollback list

List snapshots or transactions.

```bash
nodupe rollback --list
nodupe rollback --snapshots
nodupe rollback --transactions
```

#### rollback create

Create a snapshot of specified paths.

```bash
nodupe rollback create <path1> [path2 ...]
```

#### rollback restore

Restore files from a snapshot.

```bash
nodupe rollback restore <snapshot_id>
```

#### rollback delete

Delete a snapshot.

```bash
nodupe rollback delete <snapshot_id>
```

#### rollback undo

Undo the last transaction.

```bash
nodupe rollback undo
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |

## Configuration

See [Getting Started](../Getting-Started.md#configuration) for config file options.
