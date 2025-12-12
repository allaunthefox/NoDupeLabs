# NoDupeLabs Advanced Usage Guide

This guide provides advanced usage patterns, integration examples, and best practices for using NoDupeLabs in complex scenarios.

## Table of Contents

- [Advanced Scanning Techniques](#advanced-scanning-techniques)
- [Custom Configuration Profiles](#custom-configuration-profiles)
- [Integration with Other Tools](#integration-with-other-tools)
- [Automation and Scripting](#automation-and-scripting)
- [Performance Optimization](#performance-optimization)
- [Custom Plugin Development](#custom-plugin-development)
- [Advanced Similarity Search](#advanced-similarity-search)
- [Troubleshooting Complex Issues](#troubleshooting-complex-issues)

## Advanced Scanning Techniques

### Multi-Root Scanning with Custom Settings

```bash
# Scan multiple directories with custom hash algorithm and increased parallelism
nodupe scan \
  --root /data/photos \
  --root /data/documents \
  --root /data/videos \
  --hash-algo blake2b \
  --parallelism 8 \
  --ignore-patterns ".git,*.tmp,*.log"
```

### Incremental Scanning with Custom Database

```bash
# Use a custom database location and enable verbose logging
nodupe scan \
  --root /large/dataset \
  --db-path /custom/location/index.db \
  --verbose \
  --heartbeat-interval 30 \
  --stall-timeout 600
```

### Scanning with NSFW Classification

```bash
# Enable NSFW classification with custom threshold
nodupe scan \
  --root /user/uploads \
  --nsfw-enabled true \
  --nsfw-threshold 2 \
  --ai-backend onnx
```

## Custom Configuration Profiles

### Creating Custom Presets

Add custom presets to `nodupe/config/presets.py`:

```python
CUSTOM_PRESETS = {
    "video_archive": {
        "hash_algo": "sha512",
        "parallelism": 4,
        "ignore_patterns": [
            ".git", "node_modules", "*.tmp", "*.log",
            "thumbnails", "__MACOSX"
        ],
        "ai": {
            "enabled": True,
            "model_path": "models/nsfw_video.onnx",
            "backend": "onnx"
        },
        "video": {
            "extract_frames": True,
            "frame_quality": 85,
            "frame_size": "1280x720"
        }
    }
}
```

### Using Custom Configuration

```yaml
# nodupe.yml - Custom configuration
hash_algo: blake2b
dedup_strategy: content_hash
parallelism: 8
dry_run: false

ignore_patterns:
  - ".git"
  - "node_modules"
  - "*.tmp"
  - "*.log"
  - "thumbnails"
  - "__MACOSX"

ai:
  enabled: true
  backend: onnx
  model_path: models/nsfw_small_compat.onnx
  threshold: 2

video:
  extract_frames: true
  frame_quality: 85
  frame_size: "1280x720"

database:
  path: /custom/location/index.db
  wal_mode: true
  timeout: 30
```

## Integration with Other Tools

### Integration with Rclone

```bash
# Sync files to cloud storage after deduplication
nodupe plan --out dedup_plan.csv
nodupe apply --plan dedup_plan.csv --checkpoint checkpoint.json

# Upload deduplicated files to cloud storage
rclone sync /data/.nodupe_duplicates remote:backup/duplicates

# Clean up local duplicates after successful upload
rm -rf /data/.nodupe_duplicates
```

### Integration with FFmpeg

```bash
# Convert videos before scanning
find /data/videos -name "*.mov" -exec ffmpeg -i {} -c:v libx264 -crf 23 -c:a aac -b:a 128k {}.mp4 \;

# Scan converted videos
nodupe scan --root /data/videos --ignore-patterns "*.mov"
```

### Integration with ImageMagick

```bash
# Optimize images before scanning
find /data/photos -name "*.jpg" -exec convert {} -quality 85 -strip {} \;

# Scan optimized images
nodupe scan --root /data/photos
```

## Automation and Scripting

### Python Script for Automated Workflow

```python
#!/usr/bin/env python3
"""Automated NoDupeLabs workflow."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, shell=True, check=check,
                              capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def main():
    # Configuration
    data_dir = "/data/photos"
    output_dir = "output"
    plan_file = "dedup_plan.csv"
    checkpoint_file = "checkpoint.json"

    # Step 1: Initialize configuration
    print("Initializing configuration...")
    run_command(f"nodupe init --preset media --force")

    # Step 2: Scan files
    print("Scanning files...")
    run_command(f"nodupe scan --root {data_dir} --parallelism 8")

    # Step 3: Generate deduplication plan
    print("Generating deduplication plan...")
    run_command(f"nodupe plan --out {plan_file}")

    # Step 4: Review plan (manual step)
    print("Please review the plan before continuing...")
    input("Press Enter to continue or Ctrl+C to abort...")

    # Step 5: Apply deduplication
    print("Applying deduplication...")
    run_command(f"nodupe apply --plan {plan_file} --checkpoint {checkpoint_file}")

    # Step 6: Build similarity index
    print("Building similarity index...")
    run_command(f"nodupe similarity build --out index.npz --dim 16")

    print("Workflow completed successfully!")

if __name__ == "__main__":
    main()
```

### Cron Job for Regular Scanning

```bash
# Add to crontab for weekly scanning
0 2 * * 0 /usr/bin/nodupe scan --root /data/photos --parallelism 4 >> /var/log/nodupe_weekly.log 2>&1
```

### Systemd Service for Continuous Monitoring

```ini
# /etc/systemd/system/nodupe-monitor.service
[Unit]
Description=NoDupeLabs Continuous Monitoring
After=network.target

[Service]
User=nodupe
Group=nodupe
WorkingDirectory=/opt/nodupe
ExecStart=/usr/bin/nodupe scan --root /data/photos --parallelism 2 --heartbeat-interval 60 --stall-timeout 3600
Restart=on-failure
RestartSec=30s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Performance Optimization

### Optimizing for Large Datasets

```bash
# Use BLAKE2b for faster hashing on large datasets
nodupe scan --root /large/dataset --hash-algo blake2b --parallelism 16

# Increase timeout settings for slow storage
nodupe scan --root /network/drive --stall-timeout 1200 --max-idle-time 300
```

### Memory Management

```bash
# Limit parallelism for memory-constrained environments
nodupe scan --root /data --parallelism 2

# Use chunked processing for very large files
nodupe scan --root /data --chunk-size 8192
```

### Database Optimization

```bash
# Vacuum and optimize the database
sqlite3 output/index.db "VACUUM;"
sqlite3 output/index.db "ANALYZE;"

# Rebuild database with optimized settings
nodupe scan --root /data --db-path optimized.db --parallelism 8
```

## Custom Plugin Development

### Creating a Custom Plugin

```python
# plugins/custom_logger.py
from nodupe.plugins import pm

@pm.hook
def on_scan_start(roots, cfg):
    """Log scan start event."""
    print(f"[CUSTOM] Scan started: {roots}")
    print(f"[CUSTOM] Config: {cfg.get('hash_algo', 'sha512')}")

@pm.hook
def on_file_scanned(path, hash_value, mime_type):
    """Log each scanned file."""
    print(f"[CUSTOM] Scanned: {path} -> {hash_value} ({mime_type})")

@pm.hook
def on_scan_complete(results):
    """Log scan completion."""
    print(f"[CUSTOM] Scan complete: {results.get('processed', 0)} files")
    print(f"[CUSTOM] Duplicates found: {results.get('duplicates', 0)}")
```

### Using Custom Plugins

```bash
# Create plugins directory
mkdir -p plugins

# Add custom plugin
cp custom_logger.py plugins/

# Run scan with custom plugins
nodupe scan --root /data
```

## Advanced Similarity Search

### Building Multiple Indexes

```bash
# Build indexes with different dimensions
nodupe similarity build --out index_16.npz --dim 16
nodupe similarity build --out index_32.npz --dim 32
nodupe similarity build --out index_64.npz --dim 64

# Query with different indexes
nodupe similarity query photo.jpg --index-file index_16.npz -k 10
nodupe similarity query photo.jpg --index-file index_64.npz -k 5
```

### Incremental Index Updates

```bash
# Initial build
nodupe similarity build --out index.npz --dim 16

# Add new files to existing index
nodupe scan --root /new_files
nodupe similarity update --index-file index.npz

# Rebuild index completely
nodupe similarity update --index-file index.npz --rebuild
```

### Similarity Search with Different Backends

```bash
# Use brute-force backend
nodupe similarity build --out index_bf.json --backend bruteforce

# Use FAISS backend (if available)
nodupe similarity build --out index_faiss.faiss --backend faiss

# Query with different backends
nodupe similarity query photo.jpg --index-file index_bf.json -k 10
nodupe similarity query photo.jpg --index-file index_faiss.faiss -k 10
```

## Troubleshooting Complex Issues

### Debugging Performance Problems

```bash
# Enable verbose logging
export NO_DUPE_DEBUG=1

# Run with performance monitoring
nodupe scan --root /data --verbose --parallelism 4

# Analyze logs
grep "PERF:" output/logs/scan.log
```

### Database Corruption Recovery

```bash
# Backup corrupted database
cp output/index.db output/index.db.corrupt

# Export data from corrupted database
sqlite3 output/index.db.corrupt ".dump" > database_dump.sql

# Create new database and import data
rm output/index.db
sqlite3 output/index.db < database_dump.sql

# Rebuild indexes
nodupe scan --root /data --rebuild-indexes
```

### Memory Leak Investigation

```bash
# Monitor memory usage
while true; do
    ps aux | grep nodupe | grep -v grep
    sleep 5
done

# Run with memory profiling
python -m memory_profiler nodupe scan --root /data
```

## Best Practices

### Backup and Recovery

```bash
# Regular backup strategy
tar czvf nodupe_backup_$(date +%Y%m%d).tar.gz output/ plugins/ nodupe.yml

# Restore from backup
tar xzvf nodupe_backup_20251201.tar.gz
```

### Configuration Management

```bash
# Version control for configuration
git init
git add nodupe.yml plugins/
git commit -m "Initial configuration"

# Environment-specific configurations
cp nodupe.yml nodupe.yml.production
cp nodupe.yml nodupe.yml.development
```

### Security Best Practices

```bash
# Set proper permissions
chmod 600 nodupe.yml
chmod 700 output/
chmod 600 output/index.db

# Use read-only mode for sensitive data
nodupe scan --root /sensitive/data --read-only
```

## Integration Guides

### Integration with Nextcloud

```bash
# Scan Nextcloud data directory
nodupe scan --root /var/www/nextcloud/data

# Create deduplication plan
nodupe plan --out nextcloud_dedup.csv

# Apply deduplication with Nextcloud maintenance mode
sudo -u www-data php /var/www/nextcloud/occ maintenance:mode --on
nodupe apply --plan nextcloud_dedup.csv
sudo -u www-data php /var/www/nextcloud/occ maintenance:mode --off
```

### Integration with Plex Media Server

```bash
# Scan Plex media library
nodupe scan --root /var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/Media

# Exclude Plex metadata
nodupe scan --root /media --ignore-patterns "*.bundle,*.db,*.xml"
```

### Integration with PhotoPrism

```bash
# Scan PhotoPrism originals
nodupe scan --root /photoprism/storage/originals

# Use PhotoPrism-compatible hashing
nodupe scan --root /photoprism/storage/originals --hash-algo sha256
```

## Advanced Examples

### Custom Metadata Extraction

```python
# Extract custom metadata and add to database
import sqlite3
from pathlib import Path

def add_custom_metadata(db_path, file_path):
    """Add custom metadata to database."""
    conn = sqlite3.connect(db_path)

    # Get file info
    stat = file_path.stat()
    mime = "image/jpeg"  # Get from actual file

    # Insert or update metadata
    conn.execute("""
        INSERT OR REPLACE INTO files
        (path, size, mime, custom_metadata)
        VALUES (?, ?, ?, ?)
    """, (str(file_path), stat.st_size, mime, "custom_data"))

    conn.commit()
    conn.close()
```

### Batch Processing with API

```python
# Use NoDupeLabs as a Python library
from nodupe.container import get_container
from nodupe.scan import ScanOrchestrator

def batch_process(directories):
    """Process multiple directories programmatically."""
    container = get_container()
    orchestrator = container.get_scanner()

    for directory in directories:
        print(f"Processing {directory}...")
        results = orchestrator.scan(
            roots=[directory],
            hash_algo="sha512",
            workers=4
        )
        print(f"Processed {results['processed']} files")

    return results
```

## Conclusion

This advanced usage guide provides comprehensive examples and best practices for using NoDupeLabs in complex scenarios. The examples are designed to be **clear, reproducible, and practical** for real-world use cases.

For more information, refer to:
- [Beginner's Guide](BEGINNERS_GUIDE.md) for basic usage
- [Documentation Guide](DOCUMENTATION_GUIDE.md) for documentation standards
- [Contributing Guide](CONTRIBUTING.md) for development guidelines
