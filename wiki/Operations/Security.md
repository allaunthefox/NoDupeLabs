# Security

## Overview

NoDupeLabs implements several security measures to protect your data.

## File Safety

- **Read-only scanning**: By default, only reads files to compute hashes
- **Dry-run mode**: Preview changes before applying
- **Backup support**: Automatic backups before modifications

## Database Security

- Local SQLite database (no cloud)
- Database path configurable
- File integrity verification

## Plugin Security

- Plugins run in isolated context
- Plugin discovery from trusted directories only
- API stability markers for core functions

## Best Practices

1. Always review plans before applying
2. Keep backups of important data
3. Use `--dry-run` to preview changes
4. Verify file integrity regularly

## Vulnerability Reporting

Report security issues via GitHub Issues.
