# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

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
    """Check if minimal requirements for scanning are met."""
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
    """Scan command."""
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
                    if not (existing and
                            existing.get("mtime") == int(mtime) and
                            existing.get("dim") == sim_dim):
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
