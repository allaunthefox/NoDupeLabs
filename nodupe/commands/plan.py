# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Deduplication plan generation command.

This module implements the 'plan' command, which generates a CSV plan
for deduplicating files by moving duplicates into .nodupe_duplicates
subdirectories. The plan can be reviewed before execution and is used
by the 'apply' command to perform the actual file operations.

Key Features:
    - Query database for duplicate file groups (by hash + context)
    - Generate move operations for duplicates (keep first, move rest)
    - Create .nodupe_duplicates subdirectories in source locations
    - Assign unique rollback keys for tracking
    - Write operations to CSV for review and execution

Deduplication Strategy:
    - Group files by: content hash + context_tag
    - Keep: First file (sorted alphabetically)
    - Move: All other duplicates to .nodupe_duplicates/

CSV Output Columns:
    - status: 'planned' (initial state)
    - op: 'move' (operation type)
    - src_path: Original file path
    - dst_path: Destination path in .nodupe_duplicates/
    - content_id: Unique identifier (nd:hash:{sha}:ctx:{context})
    - reason: 'dedup' (operation reason)
    - rollback_key: Unique key for rollback tracking (rbk:000000)
    - ts: ISO 8601 timestamp (UTC)

Dependencies:
    - pathlib: Path handling
    - datetime: Timestamp generation
    - ..db: Database queries for duplicates
    - ..planner: CSV writing and path uniqueness

Example:
    >>> # CLI usage
    >>> $ nodupe plan --out dedup_plan.csv
    >>> [plan] duplicate_groups=42 planned_ops=156 -> dedup_plan.csv
    >>>
    >>> # CSV output sample
    >>> status,op,src_path,dst_path,content_id,reason,rollback_key,ts
    >>> planned,move,/a/photo.jpg,/a/.nodupe_duplicates/photo.jpg,...

Notes:
    - Plan is deterministic (same database = same plan)
    - Destination paths use ensure_unique to avoid collisions
    - Plan should be reviewed before applying
    - Rollback keys allow reversing operations later
"""

from pathlib import Path
from datetime import datetime, timezone
from ..db import DB
from ..planner import ensure_unique, write_plan_csv


def cmd_plan(args, cfg):
    """Generate deduplication plan from database duplicates.

    Queries the database for duplicate file groups (by content hash and
    context tag), generates move operations to relocate duplicates into
    .nodupe_duplicates subdirectories, and writes the plan to a CSV file.

    For each duplicate group, keeps the first file (alphabetically sorted)
    and plans to move all others. Each operation gets a unique rollback
    key for tracking and potential reversal.

    Args:
        args: Argparse Namespace with attributes:
            - out (str): Output CSV file path for the plan (required)
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success)

    Workflow:
        1. Open database connection
        2. Query duplicate groups (hash + context_tag)
        3. For each duplicate group:
           - Sort paths alphabetically
           - Keep first path unchanged
           - Generate move ops for remaining duplicates
           - Assign unique rollback keys
        4. Write all operations to CSV
        5. Print summary statistics

    Duplicate Resolution:
        - Files grouped by: SHA hash + context_tag
        - Sorting: Alphabetical (deterministic)
        - Kept file: First in sorted list
        - Moved files: Remaining duplicates
        - Destination: .nodupe_duplicates/ in source directory

    CSV Row Format:
        {
            'status': 'planned',
            'op': 'move',
            'src_path': '/original/path/file.jpg',
            'dst_path': '/original/path/.nodupe_duplicates/file.jpg',
            'content_id': 'nd:hash:abc123...:ctx:photos',
            'reason': 'dedup',
            'rollback_key': 'rbk:000042',
            'ts': '2025-12-03T22:50:00+00:00'
        }

    Side Effects:
        - Writes CSV file to args.out path
        - Prints summary to stdout

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(out='plan.csv')
        >>> cfg = {'db_path': 'nodupe.db'}
        >>> exit_code = cmd_plan(args, cfg)
        [plan] duplicate_groups=10 planned_ops=25 -> plan.csv
        >>> print(exit_code)
        0

    Notes:
        - Plan is deterministic (same DB = same plan output)
        - No files are modified (read-only operation)
        - Plan should be reviewed before applying
        - Destination directories are not created by this command
        - Path collisions are handled by ensure_unique
    """
    db = DB(Path(cfg["db_path"]))
    dups = db.get_duplicates()
    ts = datetime.now(timezone.utc).isoformat()
    rows = []
    rbk = 0

    for sha, context_tag, paths_csv in dups:
        paths = sorted(paths_csv.split("|"))
        # Keep first, move rest
        for src in paths[1:]:
            srcp = Path(src)
            dup_dir = srcp.parent / ".nodupe_duplicates"
            dst = ensure_unique(dup_dir / srcp.name)

            rows.append({
                "status": "planned",
                "op": "move",
                "src_path": src,
                "dst_path": str(dst),
                "content_id": f"nd:hash:{sha}:ctx:{context_tag}",
                "reason": "dedup",
                "rollback_key": f"rbk:{rbk:06d}",
                "ts": ts
            })
            rbk += 1

    write_plan_csv(rows, Path(args.out))
    print(
        f"[plan] duplicate_groups={len(dups)} planned_ops={len(rows)} -> "
        f"{args.out}"
    )
    return 0
