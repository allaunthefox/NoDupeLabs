# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Deduplication plan generation and conflict resolution.

This module generates human-readable CSV plans for deduplication operations.
Plans specify which files to keep and which to move, with automatic conflict
resolution for filename collisions.

Deduplication Strategy:
    - Keep first occurrence of each file (by hash)
    - Move subsequent duplicates to .nodupe_duplicates folder
    - Automatically resolve filename conflicts by appending -1, -2, etc.

CSV Plan Format:
    The generated CSV contains columns:
    - src_path: Original file path
    - dst_path: Destination path for move operation
    - op: Operation type ('move' or 'keep')
    - reason: Reason for operation (e.g., 'duplicate')
    - file_hash: Hash identifying the file
    - size: File size in bytes

Key Features:
    - Human-readable CSV output for review before execution
    - Automatic filename collision resolution
    - Preserves first occurrence by default
    - Safe destination path generation

Dependencies:
    - csv: CSV file generation
    - pathlib: Path manipulation

Example:
    >>> from pathlib import Path
    >>> rows = [
    ...     {'src_path': '/data/dup1.jpg',
    ...      'dst_path': '/data/.nodupe_duplicates/dup1.jpg',
    ...      'op': 'move', 'reason': 'duplicate',
    ...      'file_hash': 'abc123', 'size': 1024},
    ...     {'src_path': '/data/original.jpg',
    ...      'dst_path': '/data/original.jpg',
    ...      'op': 'keep', 'reason': 'first_occurrence',
    ...      'file_hash': 'abc123', 'size': 1024}
    ... ]
    >>> write_plan_csv(rows, Path('plan.csv'))
"""

from pathlib import Path
import csv
from typing import Dict, Iterable


def ensure_unique(p: Path) -> Path:
    """Resolve filename collision by appending counter.

    If the given path exists, appends -1, -2, etc. to the filename
    (before extension) until a non-existing path is found.

    Args:
        p: Path that may have collision

    Returns:
        Path guaranteed not to exist (either original or with counter)

    Example:
        >>> from pathlib import Path
        >>> # If /data/file.txt exists
        >>> result = ensure_unique(Path('/data/file.txt'))
        >>> print(result)
        /data/file-1.txt
    """
    p = Path(p)
    if not p.exists():
        return p
    base = p.stem
    suffix = p.suffix
    parent = p.parent
    i = 1
    while True:
        cand = parent / f"{base}-{i}{suffix}"
        if not cand.exists():
            return cand
        i += 1


def write_plan_csv(rows: Iterable[Dict], out_path: Path) -> None:
    """Write deduplication plan to CSV file.

    Generates a human-readable CSV file containing all planned operations.
    The CSV can be reviewed and edited before execution. Column order is
    preserved based on first occurrence in the row dicts.

    Args:
        rows: Iterable of dicts, each representing a planned operation
            with keys like 'src_path', 'dst_path', 'op', 'reason', etc.
        out_path: Destination path for CSV file

    Returns:
        None

    Example:
        >>> rows = [
        ...     {'src_path': '/a.jpg', 'dst_path': '/dup/a.jpg',
        ...      'op': 'move', 'reason': 'duplicate'}
        ... ]
        >>> write_plan_csv(rows, Path('plan.csv'))
        # Creates plan.csv with header and 1 row
    """
    rows = list(rows)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return

    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
