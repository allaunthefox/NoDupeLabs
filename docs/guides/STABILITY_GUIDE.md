# Long-Term Stability Guide

This document outlines additional measures taken to ensure long-term stability of the NoDupeLabs database layer.

## Version Management

### Schema Versioning

Each database schema version is tracked to enable safe migrations:

```python
SCHEMA_VERSION = "1.0.0"

def get_schema_version():
    """Get current schema version."""
    return SCHEMA_VERSION
```

### Module Versioning

All core modules follow semantic versioning (SemVer):

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── Bug fixes
  │     └──────── New features (backward compatible)
  └────────────── Breaking changes
```

## Deprecation Policy

### Deprecated APIs

APIs marked for deprecation follow this pattern:

```python
import warnings

def deprecated_function():
    """Deprecated: Use new_function() instead.

    Deprecated since version 1.2.0, will be removed in 2.0.0.
    """
    warnings.warn(
        "deprecated_function() is deprecated, use new_function() instead",
        DeprecationWarning,
        stacklevel=2
    )
```

### Deprecation Timeline

| Feature | Deprecated In | Removed In | Replacement |
|---------|--------------|------------|-------------|
| `db.transaction` | 1.0.0 | 2.0.0 | `db.transaction_manager` |

## Error Handling

### Custom Exception Hierarchy

```python
class DatabaseError(Exception):
    """Base exception for database errors."""
    pass

class ConnectionError(DatabaseError):
    """Database connection errors."""
    pass

class QueryError(DatabaseError):
    """Query execution errors."""
    pass

class IntegrityError(DatabaseError):
    """Data integrity violations."""
    pass
```

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| DB001 | Connection failed | Check database file path |
| DB002 | Query syntax error | Validate SQL syntax |
| DB003 | Constraint violation | Check data constraints |
| DB004 | Transaction failed | Retry with fresh transaction |

## Backup and Recovery

### Automated Backup

```python
def create_backup(db_path: str, backup_dir: str) -> str:
    """Create timestamped database backup.

    Args:
        db_path: Path to source database
        backup_dir: Directory for backup files

    Returns:
        Path to created backup file
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/backup_{timestamp}.db"
    # Implementation...
    return backup_path
```

### Recovery Procedures

1. **Full Restore**: Restore from most recent backup
2. **Point-in-Time**: Restore to specific transaction
3. **Schema Rollback**: Revert to previous schema version

## Security Measures

### SQL Injection Prevention

- Always use parameterized queries
- Validate all user input
- Use allowlist for table/column names

```python
# ✅ Safe - parameterized query
cursor.execute("SELECT * FROM files WHERE id = ?", (id_value,))

# ❌ Unsafe - string concatenation
cursor.execute(f"SELECT * FROM files WHERE id = {id_value}")
```

### Access Control

- File permissions: 0600 (owner read/write only)
- Database directory: 0700 (owner only)
- No remote database access (local files only)

## Performance Guidelines

### Query Optimization

| Operation | Expected Time | Threshold |
|-----------|--------------|-----------|
| Single row lookup | < 1ms | 10ms |
| Batch insert (1000 rows) | < 100ms | 500ms |
| Full table scan | < 1s | 5s |
| Database vacuum | < 10s | 30s |

### Index Usage

Always index:
- Foreign keys
- Columns used in WHERE clauses
- Columns used in ORDER BY

## Testing Strategy

### Test Coverage Requirements

- **Unit tests**: 80% minimum
- **Integration tests**: All database operations
- **Performance tests**: Regression detection

### Test Categories

```
tests/
├── unit/              # Individual component tests
├── integration/       # Multi-component tests
├── performance/       # Benchmark tests
├── security/         # Penetration tests
└── regression/        # Bug fix verification
```

## Maintenance Windows

### Routine Maintenance

| Task | Frequency | Duration |
|------|-----------|----------|
| VACUUM | Weekly | < 1 min |
| ANALYZE | Weekly | < 1 min |
| Integrity Check | Monthly | < 5 min |
| Full Backup | Daily | < 10 min |

## Monitoring

### Health Checks

```python
def health_check(db_path: str) -> Dict[str, Any]:
    """Perform database health check.

    Returns:
        Dictionary with health status, issues, and recommendations
    """
    return {
        "status": "healthy",
        "schema_version": SCHEMA_VERSION,
        "file_size_mb": get_file_size(db_path),
        "page_count": get_page_count(db_path),
        "free_pages": get_free_pages(db_path),
        "integrity": check_integrity(db_path),
        "recommendations": []
    }
}
```

## Change Log

All significant changes must be documented in CHANGELOG.md following Keep a Changelog format:

```markdown
## [1.1.0] - 2026-02-14

### Added
- New DatabaseCleanup class for maintenance
- New DatabaseCache class for query caching

### Changed
- Refactored Database wrapper for better component organization

### Fixed
- Fixed transaction attribute conflict (transaction -> transaction_manager)
```

## Support and Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Database locked | Concurrent writes | Use transaction context manager |
| Slow queries | Missing indexes | Add indexes to frequently queried columns |
| Corruption | Improper shutdown | Restore from backup, run integrity check |
| Disk full | No VACUUM | Run VACUUM to reclaim space |

### Getting Help

1. Check CHANGELOG.md for recent changes
2. Run health_check() for diagnostics
3. Review logs in database db_logs table
4. Consult ISO_STANDARDS_COMPLIANCE.md for standards
