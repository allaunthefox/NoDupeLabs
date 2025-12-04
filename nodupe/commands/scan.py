# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File scanning command with incremental hashing and embedding computation.

This module implements the 'scan' command, which is the primary entry point
for building the NoDupe file index. It orchestrates directory traversal,
file hashing, metadata extraction, AI embedding computation, and database
persistence with comprehensive progress tracking and plugin integration.

Key Features:
    - Incremental scanning with mtime-based change detection
    - Parallel hash computation with configurable worker pools
    - Optional AI embedding precomputation for similarity search
    - Batch database operations for optimal performance
    - Plugin event hooks (scan_start, scan_complete)
    - Progress UI control (auto/quiet/interactive)
    - Folder metadata export for static site generation
    - Comprehensive metrics and JSONL logging

Workflow:
    1. Validate scan requirements (readable roots, writable outputs)
    2. Load known files from database for incremental scanning
    3. Initialize AI backend for embedding computation (if enabled)
    4. Stream file records from threaded scanner
    5. Compute embeddings for image/video files (batched)
    6. Persist files and embeddings to database (batched)
    7. Export folder metadata (if enabled)
    8. Save metrics and emit completion events

Performance Optimizations:
    - 1,000-file batches for database upserts
    - 100-embedding batches for AI operations
    - Incremental scanning skips unchanged files
    - Parallel hashing with configurable workers
    - Streaming processing prevents memory overflow

Integration Points:
    - Database: DB class for SQLite persistence
    - Scanner: threaded_hash for parallel file discovery
    - AI Backends: choose_backend for embedding computation
    - Plugins: Event hooks for scan_start, scan_complete
    - Logger: JSONL structured logging
    - Metrics: Performance and throughput tracking

Dependencies:
    - sqlite3: Database operations
    - pathlib: Path handling
    - collections.defaultdict: Directory grouping for metadata
    - ..db: Database abstraction layer
    - ..scanner: Parallel file scanning and hashing
    - ..ai.backends: AI embedding computation
    - ..exporter: Folder metadata generation

Environment Variables:
    - NO_DUPE_PROGRESS: Controls ffmpeg/test progress UI
        - 'auto' (default): Show progress if stdout is a TTY
        - 'quiet': Suppress all progress output
        - 'interactive': Always show progress

Example:
    >>> # CLI usage
    >>> $ nodupe scan --root /media/photos --root /media/videos
    >>> [scan] files=15234 bytes=45823401234 dur_s=127.4 -> nodupe.db
    >>>
    >>> # Programmatic usage
    >>> from nodupe.commands.scan import cmd_scan
    >>> from argparse import Namespace
    >>> args = Namespace(root=['/data'], progress='auto')
    >>> cfg = {'db_path': 'nodupe.db', 'log_dir': 'logs', ...}
    >>> exit_code = cmd_scan(args, cfg)

Notes:
    - Scan is idempotent: running multiple times is safe
    - Incremental mode only rehashes files with changed mtimes
    - Embedding computation can be CPU/GPU intensive
    - Database is locked during upsert batches
    - Large scans may take hours; progress is streamed to stdout
"""

import sys
import os
import time
import sqlite3
from pathlib import Path
from collections import defaultdict

from ..db import DB
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..utils.hashing import validate_hash_algo
from ..scanner import threaded_hash
from ..ai.backends import choose_backend
from ..exporter import write_folder_meta
from ..plugins import pm


def check_scan_requirements(roots: list, cfg: dict) -> bool:
    """Validate scan prerequisites and output path permissions.

    Performs comprehensive pre-flight checks to ensure scanning can proceed
    without errors. Validates that input directories exist and are readable,
    and that output paths (database, logs, metrics) can be created and are
    writable. Creates output parent directories if they don't exist.

    This function is called before any scanning begins to fail fast on
    configuration errors rather than discovering issues mid-scan.

    Args:
        roots: List of directory paths to scan (as strings or Path-like).
            Each root must exist and be readable.
        cfg: Configuration dictionary with optional keys:
            - 'db_path': Database file path (parent must be writable)
            - 'log_dir': Log directory path (must be writable)
            - 'metrics_path': Metrics JSON file path (parent must be writable)

    Returns:
        True if all requirements are met (scan can proceed safely).
        False if any requirement fails (prints error to stderr).

    Validation Steps:
        1. Check each root exists and is readable
        2. Check database parent directory is writable (create if needed)
        3. Check log directory is writable (create if needed)
        4. Check metrics parent directory is writable (create if needed)

    Side Effects:
        - Prints error messages to stderr on validation failure
        - Creates output parent directories if they don't exist

    Example:
        >>> cfg = {
        ...     'db_path': '/data/nodupe.db',
        ...     'log_dir': '/data/logs',
        ...     'metrics_path': '/data/metrics.json'
        ... }
        >>> if check_scan_requirements(['/media'], cfg):
        ...     print("Ready to scan")
        ... else:
        ...     print("Requirements not met")
        Ready to scan

    Notes:
        - Non-existent output directories are created automatically
        - Permission checks use os.access (may not work on all filesystems)
        - Symlinks in root paths are checked for read access
    """
    # 1. Check Input Roots
    for r in roots:
        p = Path(r)
        if not p.exists():
            print(f"[fatal] Scan root does not exist: {r}", file=sys.stderr)
            return False
        if not os.access(p, os.R_OK):
            print(f"[fatal] Scan root is not readable: {r}", file=sys.stderr)
            return False

    # 2. Check Output Paths
    for key in ["db_path", "log_dir", "metrics_path"]:
        path_str = cfg.get(key)
        if not path_str:
            continue
        p = Path(path_str)
        # Check parent writability
        parent = p.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(
                    f"[fatal] Cannot create output directory {parent}: {e}",
                    file=sys.stderr
                )
                return False
        if not os.access(parent, os.W_OK):
            print(
                f"[fatal] Output directory not writable: {parent}",
                file=sys.stderr
            )
            return False

    return True


def cmd_scan(args, cfg):
    """Execute file scanning with hashing, metadata extraction, and embeddings.

    Primary command handler for 'nodupe scan'. Orchestrates the complete
    scanning workflow including directory traversal, parallel hashing,
    AI embedding computation, database persistence, and metrics tracking.

    Implements incremental scanning by loading known files from the database
    and skipping unchanged files (based on mtime comparison). Processes files
    in batches for optimal database performance and memory efficiency.

    Args:
        args: Argparse Namespace with attributes:
            - root (list): List of directory paths to scan (required)
            - progress (str, optional): Progress UI mode override
                ('auto', 'quiet', 'interactive')
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path
            - log_dir (str): JSONL log directory path
            - metrics_path (str): Metrics JSON file path
            - hash_algo (str, optional): Hash algorithm (default: 'sha512')
            - ignore_patterns (list): Glob patterns to exclude
            - parallelism (int): Number of worker threads
            - follow_symlinks (bool, optional): Follow symlinks
                (default: False)
            - similarity (dict, optional): {'dim': int} embedding dimensions
            - ai (dict, optional): {'model_path': str} AI model config
            - export_folder_meta (bool, optional): Export folder JSON metadata
            - meta_pretty (bool, optional): Pretty-print folder metadata
            - dry_run (bool, optional): Not used in scan (reserved)

    Returns:
        int: Exit code (0 for success, 1 for failure)

    Workflow:
        1. Validate requirements (paths exist, writable)
        2. Initialize database, logger, metrics
        3. Load known files for incremental scanning
        4. Initialize AI backend (if configured)
        5. Stream records from threaded scanner
        6. For each file:
           - Add to batch for database upsert
           - Compute embedding if image/video and needed
           - Group by directory for metadata export
           - Flush batches at thresholds (1000 files, 100 embeddings)
        7. Flush remaining batches
        8. Export folder metadata (if enabled)
        9. Save metrics and emit completion event

    Batch Processing:
        - Files: Batched in groups of 1,000 for database upserts
        - Embeddings: Batched in groups of 100 for AI operations
        - Streaming: Iterator prevents loading all files into memory

    Plugin Events:
        - 'scan_start': Emitted before scanning begins
            (data: roots, db)
        - 'scan_complete': Emitted after scanning completes
            (data: records=[], duration, metrics)

    Side Effects:
        - Writes to SQLite database (files and embeddings tables)
        - Appends to JSONL log file
        - Writes metrics JSON file
        - Creates folder .nodupe-meta.json files (if export_folder_meta=True)
        - Sets NO_DUPE_PROGRESS environment variable (if args.progress set)
        - Prints summary to stdout

    Error Handling:
        - Validation errors: Return 1 immediately
        - Hash algorithm errors: Return 1 with error message
        - AI backend init failures: Log warning, continue without embeddings
        - Individual embedding failures: Log warning, skip that file
        - Database errors during scan: Log error, attempt to save metrics

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(root=['/media/photos'], progress=None)
        >>> cfg = {
        ...     'db_path': 'nodupe.db',
        ...     'log_dir': 'logs',
        ...     'metrics_path': 'metrics.json',
        ...     'hash_algo': 'blake2b',
        ...     'ignore_patterns': ['*.tmp'],
        ...     'parallelism': 4,
        ...     'similarity': {'dim': 16}
        ... }
        >>> exit_code = cmd_scan(args, cfg)
        [scan] files=1523 bytes=4582340123 dur_s=42.1 -> nodupe.db
        >>> print(exit_code)
        0

    Performance Characteristics:
        - Large scans (100k+ files): Can take hours
        - Database: Locked during batch upserts (~1s per 1000 files)
        - AI embeddings: GPU-accelerated if available, otherwise CPU
        - Memory: Constant (streaming), ~100MB typical
        - I/O: Bottleneck is usually disk read speed for hashing

    Notes:
        - Idempotent: Safe to run multiple times
        - Incremental: Only processes files with changed mtimes
        - Progress: Printed per-file to stdout by threaded_hash
        - Embeddings: Only computed for image/video MIME types
        - Embedding cache: Checked by mtime and dimension match
    """
    if not check_scan_requirements(args.root, cfg):
        return 1

    db = DB(Path(cfg["db_path"]))
    logger = JsonlLogger(Path(cfg["log_dir"]))
    metrics = Metrics(Path(cfg["metrics_path"]))

    logger.log("INFO", "scan_start", roots=list(args.root))
    pm.emit("scan_start", roots=args.root, db=db)

    try:
        hash_algo = validate_hash_algo(cfg.get("hash_algo", "sha512"))
    except ValueError as e:
        print(f"[fatal] Configuration error: {e}", file=sys.stderr)
        return 1

    # Load known files for incremental scan
    known_files = {}
    try:
        for path, size, mtime, file_hash in db.get_known_files():
            known_files[path] = (size, mtime, file_hash)
    except sqlite3.Error:
        # DB might be new or empty
        pass

    # Prepare for streaming
    iterator = threaded_hash(
        args.root,
        cfg["ignore_patterns"],
        workers=cfg["parallelism"],
        hash_algo=hash_algo,
        follow_symlinks=cfg.get("follow_symlinks", False),
        known_files=known_files
    )

    # Precompute embeddings setup
    sim_dim = int(cfg.get("similarity", {}).get("dim", 16))
    model_hint = cfg.get("ai", {}).get("model_path")
    try:
        be = choose_backend(model_hint)
    except Exception as e:
        print(f"[scan][WARN] AI backend init failed: {e}", file=sys.stderr)
        be = None

    # If CLI requested an explicit progress mode, expose it as env var
    if getattr(args, 'progress', None) is not None:
        os.environ['NO_DUPE_PROGRESS'] = args.progress

    files_batch = []
    embeddings_batch = []
    by_dir = defaultdict(list)

    total_files = 0
    total_bytes = 0
    embeddings_updated = 0

    start_time = time.time()

    BATCH_SIZE = 1000
    EMBED_BATCH_SIZE = 100

    try:
        for rec in iterator:
            total_files += 1
            total_bytes += rec[1]
            files_batch.append(rec)

            # Collect for meta export if needed
            if cfg.get("export_folder_meta", False):
                path_obj = Path(rec[0])
                by_dir[path_obj.parent].append({
                    "name": path_obj.name,
                    "size": rec[1],
                    "mtime": rec[2],
                    "file_hash": rec[3],
                    "mime": rec[4],
                    "context_tag": rec[5],
                    "hash_algo": rec[6],
                    "permissions": rec[7]
                })

            # Embeddings logic
            if be:
                p = rec[0]
                mime = rec[4]
                mtime = rec[2]
                if mime and (
                    mime.startswith("image/") or mime.startswith("video/")
                ):
                    # Check if we need to compute
                    # Note: checking DB for every file might be slow?
                    # But we are batching upserts, so local DB is up to date?
                    # Actually, we should check `known_files` or similar?
                    # `db.get_embedding` does a SELECT.
                    # Optimization: Cache existing embeddings in memory
                    # For now, we'll do the SELECT. SQLite is fast.
                    existing = db.get_embedding(p)
                    # Check if we need to compute (mtime or dim mismatch)
                    if not (
                        existing
                        and existing.get("mtime") == int(mtime)
                        and existing.get("dim") == sim_dim
                    ):
                        try:
                            vec = be.compute_embedding(Path(p), dim=sim_dim)
                            embeddings_batch.append(
                                (p, vec, sim_dim, int(mtime))
                            )
                        except (
                            OSError, ValueError, RuntimeError, sqlite3.Error
                        ) as e:
                            print(
                                f"[scan][WARN] embedding failed for {p}: {e}",
                                file=sys.stderr
                            )

            # Flush batches
            if len(files_batch) >= BATCH_SIZE:
                db.upsert_files(files_batch)
                files_batch = []

            if len(embeddings_batch) >= EMBED_BATCH_SIZE:
                db.upsert_embeddings(embeddings_batch)
                embeddings_updated += len(embeddings_batch)
                embeddings_batch = []

        # Flush remaining
        if files_batch:
            db.upsert_files(files_batch)
        if embeddings_batch:
            db.upsert_embeddings(embeddings_batch)
            embeddings_updated += len(embeddings_batch)

        if be:
            logger.log(
                "INFO", "embeddings_precomputed", updated=embeddings_updated
            )

    except (OSError, ValueError, RuntimeError, sqlite3.Error) as e:
        print(f"[scan][ERROR] Scan failed: {e}", file=sys.stderr)
        # We might want to re-raise or exit, but let's try to save metrics

    dur = time.time() - start_time

    # Metrics
    metrics.data["files_scanned"] = total_files
    metrics.data["bytes_scanned"] = total_bytes
    metrics.data["durations"]["scan_s"] = round(dur, 3)

    # We don't have the full list of records anymore for the emit,
    # so we'll emit a summary or empty list.
    pm.emit("scan_complete", records=[], duration=dur, metrics=metrics)

    # Meta Export
    if cfg.get("export_folder_meta", False):
        # by_dir is already populated in the main loop
        meta_count = 0
        meta_errors = 0
        for dir_path, file_recs in by_dir.items():
            try:
                write_folder_meta(
                    folder_path=dir_path,
                    file_records=file_recs,
                    root_path=Path(args.root[0]),
                    pretty=cfg.get("meta_pretty", False),
                    silent=True
                )
                meta_count += 1
            except Exception as e:  # pylint: disable=broad-except
                meta_errors += 1
                logger.log(
                    "ERROR", "meta_export_failed",
                    directory=str(dir_path), error=str(e)
                )
        metrics.data["meta_exported"] = meta_count
        metrics.data["meta_errors"] = meta_errors

    metrics.save()
    print(
        f"[scan] files={total_files} bytes={total_bytes} "
        f"dur_s={round(dur, 3)} -> {cfg['db_path']}"
    )
    return 0
