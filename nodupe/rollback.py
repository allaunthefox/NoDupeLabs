# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Rollback functionality for undoing deduplication operations.

This module provides safe rollback of file moves using checkpoint manifests
generated during the apply phase. It reverses operations in the correct
order and validates paths before restoring.

Rollback Strategy:
    - Process moves in reverse order (LIFO)
    - Validate current file exists at destination
    - Verify original location is vacant
    - Restore parent directory structure as needed
    - Report errors but continue with remaining restorations

Safety Requirements:
    - Checkpoint must exist and contain valid JSON
    - Current file must exist at destination
    - Original location must be vacant (not overwritten)
    - Parent directories created automatically

Key Features:
    - Safe reverse operation with validation
    - Detailed error reporting
    - Partial rollback support (continues on individual failures)
    - Preserves directory structure

Dependencies:
    - shutil: File operations
    - json: Checkpoint parsing
    - pathlib: Path manipulation

Example:
    >>> from pathlib import Path
    >>> checkpoint = Path('output/checkpoints/chk_01.json')
    >>> results = rollback_from_checkpoint(checkpoint)
    >>> print(f"Restored {results['restored']} files")
    Restored 10 files
"""

import shutil
import json
from pathlib import Path
from typing import Dict


def rollback_from_checkpoint(checkpoint_path: Path) -> Dict:
    """Undo file moves using checkpoint manifest.

    Reads the checkpoint JSON created during apply phase and reverses
    all file moves in reverse order (LIFO). Validates that files exist
    at current locations and original locations are vacant before moving.

    Args:
        checkpoint_path: Path to checkpoint JSON file from apply operation

    Returns:
        Dict with rollback results:
            - restored: Number of successfully restored files
            - errors: Number of errors encountered
            - msg: Error message (only if checkpoint invalid)

    Example:
        >>> checkpoint = Path('output/checkpoints/chk_20251203.json')
        >>> results = rollback_from_checkpoint(checkpoint)
        >>> if results['errors'] == 0:
        ...     print(f"Successfully restored {results['restored']} files")
        Successfully restored 15 files
    """
    if not checkpoint_path.exists():
        return {"errors": 1, "msg": "Checkpoint not found"}

    try:
        manifest = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"errors": 1, "msg": "Invalid checkpoint JSON"}

    moves = manifest.get("moves", [])
    # Reverse order for rollback
    moves.reverse()

    results = {"restored": 0, "errors": 0}

    for mv in moves:
        src_orig = Path(mv["src"])  # Where it was
        dst_curr = Path(mv["dst"])  # Where it is now

        if not dst_curr.exists():
            print(f"[rollback][WARN] Current file missing: {dst_curr}")
            results["errors"] += 1
            continue

        if src_orig.exists():
            print(f"[rollback][WARN] Original location occupied: {src_orig}")
            results["errors"] += 1
            continue

        try:
            src_orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst_curr), str(src_orig))
            results["restored"] += 1
        except OSError as e:
            print(
                f"[rollback][ERROR] Failed to restore {dst_curr} -> "
                f"{src_orig}: {e}"
            )
            results["errors"] += 1

    return results
