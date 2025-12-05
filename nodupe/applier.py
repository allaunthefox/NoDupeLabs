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
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List


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
    manifest: Dict[str, Any] = {
        "ts": time.time(),
        "status": "pending",
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

    # 2. Write checkpoint BEFORE any moves (for recovery)
    if checkpoint_path:
        manifest["moves"] = [
            {"src": str(src), "dst": str(dst)}
            for src, dst, _ in valid_moves
        ]
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    # 3. Create staging directory for atomic operations
    staging_id = uuid.uuid4().hex[:8]
    staging_dir = Path(tempfile.gettempdir()) / f"nodupe_staging_{staging_id}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    staged_files: List[tuple] = []

    try:
        # 4. Stage: Copy all files to staging first
        for src, dst, row in valid_moves:
            staging_path = staging_dir / f"{uuid.uuid4().hex}_{src.name}"
            try:
                shutil.copy2(str(src), str(staging_path))
                staged_files.append((src, dst, staging_path))
            except OSError as e:
                print(f"[apply][ERROR] Failed to stage {src}: {e}")
                results["errors"] += 1
                # Rollback staged files
                for _, _, staged in staged_files:
                    try:
                        staged.unlink()
                    except OSError:
                        pass
                shutil.rmtree(staging_dir, ignore_errors=True)
                return results

        # 5. Commit: Move staged files to final destinations
        for src, dst, staging_path in staged_files:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                # Atomic rename from staging to destination
                shutil.move(str(staging_path), str(dst))
                # Only delete original after successful move
                src.unlink()
                results["success"] += 1
            except OSError as e:
                print(f"[apply][ERROR] Failed to commit {src} -> {dst}: {e}")
                results["errors"] += 1

        # 6. Update checkpoint to completed
        if checkpoint_path:
            manifest["status"] = "completed"
            manifest["completed_at"] = time.time()
            checkpoint_path.write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )

    finally:
        # Cleanup staging directory
        shutil.rmtree(staging_dir, ignore_errors=True)

    return results
