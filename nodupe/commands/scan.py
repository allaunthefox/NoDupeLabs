# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan command implementation.

Thin CLI wrapper that creates dependencies and delegates to
ScanOrchestrator for actual work.
"""
import sys
import os
from pathlib import Path
from typing import Dict

from ..db import DB
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..utils.hashing import validate_hash_algo
from ..ai.backends import choose_backend
from ..plugins import pm
from ..scan import ScanValidator, ScanOrchestrator


def check_scan_requirements(roots: list, cfg: Dict) -> bool:
    """Validate scan preconditions.

    Args:
        roots: List of root paths
        cfg: Configuration dict

    Returns:
        True if valid, False if errors
    """
    validator = ScanValidator()

    # Extract paths from cfg, handling potential missing keys
    db_path = Path(cfg.get("db_path", "nodupe.db"))
    log_dir = Path(cfg.get("log_dir", "logs"))
    metrics_path = Path(cfg.get("metrics_path", "metrics.json"))

    is_valid, errors = validator.validate(
        roots=roots,
        db_path=db_path,
        log_dir=log_dir,
        metrics_path=metrics_path
    )

    if not is_valid:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return False

    return True


def cmd_scan(args, cfg: Dict) -> int:
    """Execute scan command.

    Args:
        args: Parsed CLI arguments
        cfg: Configuration dict

    Returns:
        Exit code (0 = success)
    """
    # Validate preconditions
    if not check_scan_requirements(args.root, cfg):
        return 1

    # Create dependencies
    db = DB(Path(cfg["db_path"]))
    logger = JsonlLogger(Path(cfg["log_dir"]))
    metrics = Metrics(Path(cfg["metrics_path"]))

    try:
        hash_algo = validate_hash_algo(cfg.get("hash_algo", "sha512"))
    except ValueError as e:
        print(f"[fatal] Configuration error: {e}", file=sys.stderr)
        return 1

    # Initialize AI backend
    model_hint = cfg.get("ai", {}).get("model_path")
    try:
        backend = choose_backend(model_hint)
    except Exception as e:
        print(f"[scan][WARN] AI backend init failed: {e}", file=sys.stderr)
        backend = None

    # Create orchestrator (dependency injection!)
    orchestrator = ScanOrchestrator(
        db=db,
        logger=logger,
        metrics=metrics,
        backend=backend,
        plugin_manager=pm
    )

    # If CLI requested an explicit progress mode, expose it as env var
    if getattr(args, 'progress', None) is not None:
        os.environ['NO_DUPE_PROGRESS'] = args.progress

    # Execute scan
    try:
        results = orchestrator.scan(
            roots=args.root,
            hash_algo=hash_algo,
            workers=cfg.get("parallelism", 4),
            ignore_patterns=cfg.get("ignore_patterns", []),
            follow_symlinks=cfg.get("follow_symlinks", False),
            similarity_dim=int(cfg.get("similarity", {}).get("dim", 16)),
            export_folder_meta=cfg.get("export_folder_meta", False),
            meta_pretty=cfg.get("meta_pretty", False)
        )

        # Print summary
        print(f"[scan] files={results['files_scanned']} "
              f"bytes={results['bytes_scanned']} "
              f"dur_s={results['duration_sec']:.1f} "
              f"-> {cfg['db_path']}")

        return 0

    except KeyboardInterrupt:
        print("\n[SCAN] Interrupted by user")
        return 130

    except Exception as e:
        print(f"[SCAN][ERROR] {e}")
        return 1
