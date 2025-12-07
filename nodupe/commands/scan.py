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

from ..utils.hashing import validate_hash_algo
from ..scan import ScanValidator


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

    # Validate hash algorithm
    try:
        hash_algo = validate_hash_algo(cfg.get("hash_algo", "sha512"))
    except ValueError as e:
        print(f"[fatal] Configuration error: {e}", file=sys.stderr)
        return 1

    # Initialize container with config
    from ..container import get_container
    container = get_container()
    # Force config update if needed (container loads config lazily)

    # Create orchestrator (dependency injection!)
    orchestrator = container.get_scanner()

    # If CLI requested an explicit progress mode, expose it as env var
    if getattr(args, 'progress', None) is not None:
        os.environ['NO_DUPE_PROGRESS'] = args.progress

    # Execute scan
    try:
        # Extract arguments for ScanOrchestrator
        roots = args.root
        ignore = cfg.get("ignore_patterns", [])
        workers = cfg.get("parallelism", 4)
        follow_symlinks = cfg.get("follow_symlinks", False)
        heartbeat_interval = cfg.get("heartbeat_interval", 10)
        stall_timeout = cfg.get("stall_timeout", 300)
        max_idle_time = cfg.get("max_idle_time", 60)
        show_eta = cfg.get("show_eta", True)

        # Execute scan
        results = orchestrator.scan(
            roots=roots,
            hash_algo=hash_algo,
            workers=workers,
            ignore_patterns=ignore,
            follow_symlinks=follow_symlinks,
            heartbeat_interval=heartbeat_interval,
            stall_timeout=stall_timeout,
            max_idle_time=max_idle_time,
            show_eta=show_eta
        )

        # Print summary
        if not args.json:
            print(
                f"\nScan complete. "
                f"Processed {results.get('processed', 0)} files."
            )
            print(f"Found {results.get('duplicates', 0)} duplicates.")
            print(
                f"Total size: "
                f"{results.get('total_size', 0) / 1024 / 1024:.2f} MB"
            )
            print(f"Time taken: {results.get('duration', 0):.2f} seconds")

            if results.get('errors'):
                print(f"\nEncountered {len(results['errors'])} errors:")
            for err in results['errors'][:10]:
                print(f"  - {err}")
            if len(results['errors']) > 10:
                print(f"  ... and {len(results['errors']) - 10} more.")

    except KeyboardInterrupt:
        print("\n[SCAN] Interrupted by user")
        return 130

    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    return 0
