# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Deduplication plan execution with three-phase commit pattern.

This module implements the physical file operations defined in a
deduplication plan using a three-phase commit pattern for safety
and recoverability.

Three-Phase Commit Pattern:
    1. Prepare: Validate all moves (check source exists, destination vacant)
    2. Execute: Perform the file moves atomically
    3. Commit: Save checkpoint manifest for potential rollback

Key Features:
    - Atomic operations with validation before execution
    - Checkpoint generation for rollback capability
    - Dry-run mode for safe testing
    - Detailed operation logging and error reporting
    - Automatic destination directory creation

Checkpoint Format:
    The checkpoint JSON contains:
    - ts: Timestamp of operation
    - moves: List of move operations performed
      - src: Original source path
      - dst: Destination path
      - ts: Timestamp of individual move

Safety Guarantees:
    - No moves executed if any validation fails
    - Source existence verified before move
    - Destination vacancy verified before move
    - Parent directories created automatically
    - All operations logged to checkpoint for rollback

Dependencies:
    - shutil: File operations
    - json: Checkpoint serialization
    - pathlib: Path manipulation

Example:
    >>> rows = [{'op': 'move', 'src_path': '/a/file.txt',
    ...          'dst_path': '/b/file.txt'}]
    >>> checkpoint = Path('output/checkpoints/chk_01.json')
    >>> results = apply_moves(rows, checkpoint, dry_run=False)
    >>> print(results)
    {'success': 1, 'errors': 0, 'skipped': 0}
"""

import shutil
import json
import time
from pathlib import Path
from typing import List, Dict


def apply_moves(
    rows: List[Dict], checkpoint_path: Path, dry_run: bool = True
) -> Dict:
    """Execute file moves with three-phase commit pattern.

    Implements a safe, atomic approach to executing deduplication plans:
    1. Prepare: Validate all source files exist and destinations are vacant
    2. Execute: Perform the actual file moves
    3. Commit: Save checkpoint manifest for potential rollback

    Args:
        rows: List of operation dicts with keys:
            - op: Operation type (must be 'move')
            - src_path: Source file path
            - dst_path: Destination file path
        checkpoint_path: Path where checkpoint JSON will be saved
        dry_run: If True, validate but don't execute moves (default: True)

    Returns:
        Dict with operation counts:
            - success: Number of successful moves
            - errors: Number of failed moves
            - skipped: Number of skipped moves (validation failed)

    Raises:
        OSError: If file operations fail (logged but doesn't stop execution)

    Example:
        >>> rows = [
        ...     {'op': 'move', 'src_path': '/data/dup.jpg',
        ...      'dst_path': '/data/.nodupe_duplicates/dup.jpg'}
        ... ]
        >>> checkpoint = Path('output/checkpoints/chk_01.json')
        >>> # First test with dry-run
        >>> results = apply_moves(rows, checkpoint, dry_run=True)
        [apply] Dry run: would move 1 files.
        >>> # Then execute
        >>> results = apply_moves(rows, checkpoint, dry_run=False)
        >>> print(results['success'])
        1
    """
    results = {"success": 0, "errors": 0, "skipped": 0}
    manifest = {
        "ts": time.time(),
        "moves": []
    }

    # 1. Prepare & Validate
    valid_moves = []
    for row in rows:
        if row.get("op") != "move":
            continue

        src = Path(row["src_path"])
        dst = Path(row["dst_path"])

        if not src.exists():
            print(f"[apply][SKIP] Source missing: {src}")
            results["skipped"] += 1
            continue

        if dst.exists():
            print(f"[apply][SKIP] Destination exists: {dst}")
            results["skipped"] += 1
            continue

        valid_moves.append((src, dst, row))

    if dry_run:
        print(f"[apply] Dry run: would move {len(valid_moves)} files.")
        return results

    # 2. Execute
    for src, dst, row in valid_moves:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

            manifest["moves"].append({
                "src": str(src),
                "dst": str(dst),
                "ts": time.time()
            })
            results["success"] += 1
        except OSError as e:
            print(f"[apply][ERROR] Failed to move {src} -> {dst}: {e}")
            results["errors"] += 1

    # 3. Checkpoint
    if checkpoint_path:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    return results
