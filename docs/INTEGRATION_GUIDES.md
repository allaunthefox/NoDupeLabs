# NoDupeLabs Integration Guides

This guide provides detailed integration examples for common use cases and popular software platforms.

## Table of Contents

- [Cloud Storage Integration](#cloud-storage-integration)
- [Media Server Integration](#media-server-integration)
- [Photo Management Integration](#photo-management-integration)
- [Backup Solutions Integration](#backup-solutions-integration)
- [CI/CD Pipeline Integration](#cicd-pipeline-integration)
- [Custom Application Integration](#custom-application-integration)

## Cloud Storage Integration

### Amazon S3 Integration

```bash
# Sync deduplicated files to S3
aws s3 sync /data/.nodupe_duplicates s3://my-bucket/duplicates

# Use AWS CLI with NoDupeLabs
nodupe scan --root /data
nodupe plan --out plan.csv
nodupe apply --plan plan.csv
aws s3 sync /data/.nodupe_duplicates s3://my-bucket/duplicates
```

### Google Cloud Storage Integration

```bash
# Use gcloud CLI with NoDupeLabs
nodupe scan --root /data
nodupe plan --out plan.csv
nodupe apply --plan plan.csv
gcloud storage cp -r /data/.nodupe_duplicates gs://my-bucket/duplicates
```

### Azure Blob Storage Integration

```bash
# Use Azure CLI with NoDupeLabs
nodupe scan --root /data
nodupe plan --out plan.csv
nodupe apply --plan plan.csv
az storage blob upload-batch --destination my-container --source /data/.nodupe_duplicates
```

## Media Server Integration

### Plex Media Server Integration

```bash
# Scan Plex media library
nodupe scan --root "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Media"

# Exclude Plex metadata and temporary files
nodupe scan --root /media --ignore-patterns "*.bundle,*.db,*.xml,*.tmp,*.log"

# Automated Plex integration script
#!/bin/bash
# plex_integration.sh

# Stop Plex service
sudo systemctl stop plexmediaserver

# Scan and deduplicate
nodupe scan --root /media
nodupe plan --out plex_plan.csv
nodupe apply --plan plex_plan.csv

# Start Plex service
sudo systemctl start plexmediaserver

# Update Plex library
sudo -u plex plexmediaserver update_library
```

### Emby Media Server Integration

```bash
# Scan Emby media library
nodupe scan --root /var/lib/emby

# Exclude Emby metadata
nodupe scan --root /media --ignore-patterns "*.db,*.xml,*.tmp"

# Automated Emby integration
nodupe scan --root /media
nodupe plan --out emby_plan.csv
nodupe apply --plan emby_plan.csv
sudo systemctl restart emby-server
```

### Jellyfin Media Server Integration

```bash
# Scan Jellyfin media library
nodupe scan --root /var/lib/jellyfin

# Exclude Jellyfin metadata
nodupe scan --root /media --ignore-patterns "*.db,*.xml,*.tmp"

# Automated Jellyfin integration
nodupe scan --root /media
nodupe plan --out jellyfin_plan.csv
nodupe apply --plan jellyfin_plan.csv
sudo systemctl restart jellyfin
```

## Photo Management Integration

### Nextcloud Integration

```bash
# Scan Nextcloud data directory
nodupe scan --root /var/www/nextcloud/data

# Exclude Nextcloud files
nodupe scan --root /data --ignore-patterns "*.db,*.xml,*.tmp,*.log"

# Automated Nextcloud integration
sudo -u www-data php /var/www/nextcloud/occ maintenance:mode --on
nodupe scan --root /var/www/nextcloud/data
nodupe plan --out nextcloud_plan.csv
nodupe apply --plan nextcloud_plan.csv
sudo -u www-data php /var/www/nextcloud/occ maintenance:mode --off
```

### PhotoPrism Integration

```bash
# Scan PhotoPrism originals
nodupe scan --root /photoprism/storage/originals

# Use PhotoPrism-compatible settings
nodupe scan --root /photoprism/storage/originals --hash-algo sha256

# Automated PhotoPrism integration
sudo systemctl stop photoprism
nodupe scan --root /photoprism/storage/originals
nodupe plan --out photoprism_plan.csv
nodupe apply --plan photoprism_plan.csv
sudo systemctl start photoprism
```

### Digikam Integration

```bash
# Scan Digikam collections
nodupe scan --root ~/.local/share/digikam

# Exclude Digikam database files
nodupe scan --root /photos --ignore-patterns "*.db,*.xml,*.tmp"

# Automated Digikam integration
nodupe scan --root /photos
nodupe plan --out digikam_plan.csv
nodupe apply --plan digikam_plan.csv
```

## Backup Solutions Integration

### Rclone Integration

```bash
# Backup deduplicated files with Rclone
nodupe scan --root /data
nodupe plan --out backup_plan.csv
nodupe apply --plan backup_plan.csv
rclone sync /data/.nodupe_duplicates remote:backup/duplicates

# Automated backup script
#!/bin/bash
# automated_backup.sh

# Scan and deduplicate
nodupe scan --root /data
nodupe plan --out backup_plan.csv
nodupe apply --plan backup_plan.csv

# Backup to multiple destinations
rclone sync /data/.nodupe_duplicates remote1:backup/duplicates
rclone sync /data/.nodupe_duplicates remote2:backup/duplicates
rclone sync /data/.nodupe_duplicates remote3:backup/duplicates

# Clean up local duplicates
rm -rf /data/.nodupe_duplicates
```

### Duplicati Integration

```bash
# Use Duplicati with NoDupeLabs
nodupe scan --root /data
nodupe plan --out duplicati_plan.csv
nodupe apply --plan duplicati_plan.csv

# Configure Duplicati to backup deduplicated files
duplicati add backup --name "NoDupe Backup" \
  --source /data/.nodupe_duplicates \
  --destination "remote://backup/duplicates" \
  --schedule "1D"
```

### Borg Backup Integration

```bash
# Use Borg Backup with NoDupeLabs
nodupe scan --root /data
nodupe plan --out borg_plan.csv
nodupe apply --plan borg_plan.csv

# Create Borg backup
borg init --encryption=repokey /backup/nodupe_repo
borg create /backup/nodupe_repo::duplicates-{now} /data/.nodupe_duplicates
```

## CI/CD Pipeline Integration

### GitHub Actions Integration

```yaml
# .github/workflows/nodupe.yml
name: NoDupeLabs CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install NoDupeLabs
      run: |
        python -m pip install --upgrade pip
        pip install -e .

    - name: Run scan
      run: |
        nodupe scan --root test_data

    - name: Generate plan
      run: |
        nodupe plan --out test_plan.csv

    - name: Run tests
      run: |
        pytest tests/ -v -m "not slow and not integration"
```

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - test
  - scan
  - deploy

variables:
  PYTHON_VERSION: "3.9"

test:
  stage: test
  image: python:$PYTHON_VERSION
  script:
    - pip install -e .
    - pytest tests/ -v -m "not slow and not integration"

scan:
  stage: scan
  image: python:$PYTHON_VERSION
  script:
    - pip install -e .
    - nodupe scan --root test_data
    - nodupe plan --out test_plan.csv
  artifacts:
    paths:
      - test_plan.csv
    expire_in: 1 week

deploy:
  stage: deploy
  image: python:$PYTHON_VERSION
  script:
    - pip install -e .
    - nodupe apply --plan test_plan.csv
  only:
    - main
```

### Jenkins Integration

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'python -m venv .venv'
                sh '. .venv/bin/activate && pip install -e .'
            }
        }

        stage('Test') {
            steps {
                sh '. .venv/bin/activate && pytest tests/ -v -m "not slow and not integration"'
            }
        }

        stage('Scan') {
            steps {
                sh '. .venv/bin/activate && nodupe scan --root test_data'
                sh '. .venv/bin/activate && nodupe plan --out test_plan.csv'
            }
        }

        stage('Deploy') {
            steps {
                sh '. .venv/bin/activate && nodupe apply --plan test_plan.csv'
            }
        }
    }
}
```

## Custom Application Integration

### Python Library Integration

```python
# Use NoDupeLabs as a Python library
from nodupe.container import get_container
from nodupe.scan import ScanOrchestrator
from nodupe.db import DB

def integrate_nodupe(data_directory):
    """Integrate NoDupeLabs into custom application."""
    # Initialize container
    container = get_container()

    # Get scanner
    orchestrator = container.get_scanner()

    # Scan directory
    results = orchestrator.scan(
        roots=[data_directory],
        hash_algo="sha512",
        workers=4
    )

    # Get database
    db = container.get_db()

    # Query duplicates
    duplicates = db.get_duplicates()

    return {
        "scan_results": results,
        "duplicates": duplicates
    }
```

### REST API Integration

```python
# Flask REST API integration
from flask import Flask, request, jsonify
from nodupe.container import get_container

app = Flask(__name__)

@app.route('/scan', methods=['POST'])
def scan():
    """Scan directory via REST API."""
    data = request.json
    directory = data.get('directory')

    if not directory:
        return jsonify({"error": "Directory required"}), 400

    container = get_container()
    orchestrator = container.get_scanner()

    results = orchestrator.scan(
        roots=[directory],
        hash_algo="sha512",
        workers=4
    )

    return jsonify(results)

@app.route('/duplicates', methods=['GET'])
def get_duplicates():
    """Get duplicates via REST API."""
    container = get_container()
    db = container.get_db()

    duplicates = db.get_duplicates()

    return jsonify({
        "duplicates": duplicates,
        "count": len(duplicates)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Django Integration

```python
# Django management command integration
from django.core.management.base import BaseCommand
from nodupe.container import get_container

class Command(BaseCommand):
    help = 'Run NoDupeLabs scan'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Directory to scan')

    def handle(self, *args, **options):
        directory = options['directory']

        container = get_container()
        orchestrator = container.get_scanner()

        results = orchestrator.scan(
            roots=[directory],
            hash_algo="sha512",
            workers=4
        )

        self.stdout.write(self.style.SUCCESS(f"Scanned {results['processed']} files"))
        self.stdout.write(self.style.SUCCESS(f"Found {results['duplicates']} duplicates"))
```

## Advanced Integration Patterns

### Event-Driven Integration

```python
# Event-driven integration with custom events
from nodupe.plugins import pm

@pm.hook
def on_file_scanned(path, hash_value, mime_type):
    """Custom event handler for file scanned."""
    # Send to external system
    send_to_external_system({
        "event": "file_scanned",
        "path": path,
        "hash": hash_value,
        "mime": mime_type
    })

@pm.hook
def on_duplicate_found(original, duplicate, hash_value):
    """Custom event handler for duplicate found."""
    # Log to external system
    log_duplicate({
        "original": original,
        "duplicate": duplicate,
        "hash": hash_value
    })
```

### Database Integration

```python
# Custom database integration
import sqlite3
from nodupe.db import DB

def sync_with_custom_db(nodupe_db_path, custom_db_path):
    """Sync NoDupeLabs data with custom database."""
    # Connect to both databases
    nodupe_db = DB(nodupe_db_path)
    custom_conn = sqlite3.connect(custom_db_path)

    # Get files from NoDupeLabs
    files = nodupe_db.get_all()

    # Sync with custom database
    for file in files:
        custom_conn.execute("""
            INSERT OR REPLACE INTO files
            (path, hash, size, mime)
            VALUES (?, ?, ?, ?)
        """, (file['path'], file['hash'], file['size'], file['mime']))

    custom_conn.commit()
    custom_conn.close()
```

### Webhook Integration

```python
# Webhook integration for notifications
import requests
from nodupe.plugins import pm

@pm.hook
def on_scan_complete(results):
    """Send webhook notification on scan completion."""
    webhook_url = "https://example.com/webhook"

    payload = {
        "event": "scan_complete",
        "files_processed": results.get('processed', 0),
        "duplicates_found": results.get('duplicates', 0),
        "timestamp": results.get('timestamp', '')
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Webhook failed: {e}")
```

## Best Practices for Integration

### Error Handling

```python
# Robust error handling for integrations
import logging
from nodupe.container import get_container

def safe_integration():
    """Safe integration with error handling."""
    try:
        container = get_container()
        orchestrator = container.get_scanner()

        results = orchestrator.scan(
            roots=["/data"],
            hash_algo="sha512",
            workers=4
        )

        return results
    except Exception as e:
        logging.error(f"Integration error: {e}")
        # Fallback behavior
        return {"error": str(e), "fallback": "default_behavior"}
```

### Configuration Management

```python
# Configuration management for integrations
import os
from pathlib import Path

def get_integration_config():
    """Get integration configuration."""
    config = {
        "api_url": os.getenv("NODUPE_API_URL", "http://localhost:5000"),
        "api_key": os.getenv("NODUPE_API_KEY", ""),
        "log_level": os.getenv("NODUPE_LOG_LEVEL", "INFO"),
        "data_dir": os.getenv("NODUPE_DATA_DIR", "/data")
    }

    # Validate configuration
    if not Path(config["data_dir"]).exists():
        raise ValueError(f"Data directory does not exist: {config['data_dir']}")

    return config
```

### Performance Monitoring

```python
# Performance monitoring for integrations
import time
from nodupe.container import get_container

def monitor_performance():
    """Monitor integration performance."""
    start_time = time.time()

    container = get_container()
    orchestrator = container.get_scanner()

    results = orchestrator.scan(
        roots=["/data"],
        hash_algo="sha512",
        workers=4
    )

    end_time = time.time()
    duration = end_time - start_time

    # Log performance metrics
    log_metrics({
        "operation": "scan",
        "duration": duration,
        "files_processed": results.get('processed', 0),
        "throughput": results.get('processed', 0) / duration
    })

    return results
```

## Conclusion

This integration guide provides comprehensive examples for integrating NoDupeLabs with various platforms and tools. The examples are designed to be **clear, reproducible, and practical** for real-world use cases.

For more information, refer to:
- [Advanced Usage Guide](ADVANCED_USAGE.md) for advanced patterns
- [Documentation Guide](DOCUMENTATION_GUIDE.md) for documentation standards
- [Contributing Guide](CONTRIBUTING.md) for development guidelines
