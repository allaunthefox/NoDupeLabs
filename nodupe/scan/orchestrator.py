# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan workflow orchestration.

Coordinates all subsystems involved in a scan operation:
- Database persistence
- Event logging
- Metrics collection
- File scanning
- Metadata export
- Plugin notifications
"""
import time
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ..db import DB
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..scanner import threaded_hash
from ..ai.backends import BaseBackend
from ..exporter import write_folder_meta


class ScanOrchestrator:
    """Orchestrates a complete scan operation.

    This class coordinates all subsystems without directly depending
    on their creation. All dependencies are injected via constructor,
    making the class testable and loosely coupled.
    """

    def __init__(
        self,
        db: DB,
        logger: JsonlLogger,
        metrics: Metrics,
        backend: Optional[BaseBackend],
        plugin_manager: Any
    ):
        """Initialize orchestrator with dependencies.

        Args:
            db: Database for persistence
            logger: Event logger
            metrics: Metrics collector
            backend: AI backend for embeddings (optional)
            plugin_manager: Plugin event dispatcher
        """
        self.db = db
        self.logger = logger
        self.metrics = metrics
        self.backend = backend
        self.pm = plugin_manager

    def scan(
        self,
        roots: List[str],
        hash_algo: str,
        workers: int,
        ignore_patterns: List[str],
        follow_symlinks: bool = False,
        similarity_dim: int = 16,
        export_folder_meta: bool = False,
        meta_pretty: bool = False
    ) -> Dict[str, Any]:
        """Execute complete scan workflow.

        Args:
            roots: Root directories to scan
            hash_algo: Hash algorithm (sha256, sha512, etc.)
            workers: Number of worker threads
            ignore_patterns: Glob patterns to ignore
            follow_symlinks: Whether to follow symlinks
            similarity_dim: Dimension for embeddings
            export_folder_meta: Whether to export folder metadata
            meta_pretty: Whether to pretty-print metadata

        Returns:
            Scan results summary
        """
        # Emit scan start event
        self.logger.log("INFO", "scan_start", roots=roots)
        self.pm.emit("scan_start", roots=roots, db=self.db)

        # Get known files for incremental scan
        known_files = {}
        try:
            for path, size, mtime, file_hash in self.db.get_known_files():
                known_files[path] = (size, mtime, file_hash)
        except sqlite3.Error:
            # DB might be new or empty
            pass

        # Execute threaded scan
        iterator = threaded_hash(
            roots=roots,
            ignore=ignore_patterns,
            workers=workers,
            hash_algo=hash_algo,
            follow_symlinks=follow_symlinks,
            known_files=known_files
        )

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
                if export_folder_meta:
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
                if self.backend:
                    p = rec[0]
                    mime = rec[4]
                    mtime = rec[2]
                    if mime and (
                        mime.startswith("image/") or mime.startswith("video/")
                    ):
                        existing = self.db.get_embedding(p)
                        # Check if we need to compute (mtime or dim mismatch)
                        if not (
                            existing
                            and existing.get("mtime") == int(mtime)
                            and existing.get("dim") == similarity_dim
                        ):
                            try:
                                vec = self.backend.compute_embedding(
                                    Path(p), dim=similarity_dim)
                                embeddings_batch.append(
                                    (p, vec, similarity_dim, int(mtime))
                                )
                            except Exception as e:
                                print(
                                    f"[scan][WARN] embedding failed for {p}: {e}")

                # Flush batches
                if len(files_batch) >= BATCH_SIZE:
                    self.db.upsert_files(files_batch)
                    files_batch = []

                if len(embeddings_batch) >= EMBED_BATCH_SIZE:
                    self.db.upsert_embeddings(embeddings_batch)
                    embeddings_updated += len(embeddings_batch)
                    embeddings_batch = []

            # Flush remaining
            if files_batch:
                self.db.upsert_files(files_batch)
            if embeddings_batch:
                self.db.upsert_embeddings(embeddings_batch)
                embeddings_updated += len(embeddings_batch)

            if self.backend:
                self.logger.log(
                    "INFO", "embeddings_precomputed", updated=embeddings_updated
                )

        except Exception as e:
            print(f"[scan][ERROR] Scan failed: {e}")
            # We might want to re-raise, but let's try to save metrics

        duration = time.time() - start_time

        # Record metrics
        self.metrics.data["files_scanned"] = total_files
        self.metrics.data["bytes_scanned"] = total_bytes
        self.metrics.data["durations"]["scan_s"] = round(duration, 3)

        # Meta Export
        if export_folder_meta:
            meta_count = 0
            meta_errors = 0
            for dir_path, file_recs in by_dir.items():
                try:
                    write_folder_meta(
                        folder_path=dir_path,
                        file_records=file_recs,
                        root_path=Path(roots[0]),  # Approximation
                        pretty=meta_pretty,
                        silent=True
                    )
                    meta_count += 1
                except Exception as e:
                    meta_errors += 1
                    self.logger.log(
                        "ERROR", "meta_export_failed",
                        directory=str(dir_path), error=str(e)
                    )
            self.metrics.data["meta_exported"] = meta_count
            self.metrics.data["meta_errors"] = meta_errors

        self.metrics.save()

        # Emit scan complete event
        self.pm.emit("scan_complete", records=[],
                     duration=duration, metrics=self.metrics)

        return {
            "files_scanned": total_files,
            "bytes_scanned": total_bytes,
            "duration_sec": duration,
            "files_per_sec": total_files / duration if duration > 0 else 0
        }
