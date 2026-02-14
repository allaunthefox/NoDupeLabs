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

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |

## Configuration

See [Getting Started](../Getting-Started.md#configuration) for config file options.
