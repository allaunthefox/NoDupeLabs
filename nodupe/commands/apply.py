# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Deduplication plan execution command.

This module implements the 'apply' command, which executes the file
operations defined in a deduplication plan CSV. It handles the actual
moving of files, creation of checkpoints for rollback, and dry-run
simulation.

Key Features:
    - Execute moves defined in plan CSV
    - Create JSON checkpoint for safety and rollback
    - Support dry-run mode (default) and force execution
    - Report success/failure statistics

Dependencies:
    - csv: Plan parsing
    - pathlib: Path handling
    - ..applier: Core application logic

Example:
    >>> # CLI usage
    >>> $ nodupe apply --plan plan.csv --checkpoint cp.json --force
    >>> [apply] {'moved': 15, 'errors': 0}
"""

import csv
from pathlib import Path
from typing import Any, Dict
from ..applier import apply_moves


def cmd_apply(args: Any, cfg: Dict[str, Any]) -> int:
    """Execute deduplication plan.

    This function reads the deduplication plan CSV and performs the specified
    file operations. It generates a checkpoint file to allow for future rollback
    and supports both dry-run mode (default) and actual file operations.

    The function handles the complete workflow:
    1. Parse the plan CSV file
    2. Validate the operations
    3. Execute moves (or simulate in dry-run mode)
    4. Create checkpoint file for rollback capability
    5. Report success/failure statistics

    Args:
        args: Argparse Namespace with attributes:
            - plan (str): Path to plan CSV file
            - checkpoint (str): Path to output checkpoint JSON file
            - force (bool): Execute actual moves (disable dry-run)
        cfg: Configuration dictionary with keys:
            - dry_run (bool): Global dry-run setting (overridden by args.force)

    Returns:
        int: Exit code (0 for success, 1 for errors)

    Raises:
        FileNotFoundError: If plan file doesn't exist
        PermissionError: If files can't be moved due to permissions
        OSError: If file operations fail
        Exception: For unexpected errors during execution

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(plan='plan.csv', checkpoint='cp.json', force=False)
        >>> cfg = {'dry_run': True}
        >>> exit_code = cmd_apply(args, cfg)
        [apply] {'moved': 15, 'errors': 0}
        >>> print(f"Exit code: {exit_code}")
        0

    Notes:
        - Dry-run mode is enabled by default (args.force=False)
        - Checkpoint file is always created for rollback capability
        - Exit code 0 indicates all operations completed successfully
        - Exit code 1 indicates some operations failed
        - Statistics are printed to stdout in JSON format
    """
    # Re-implement CSV reading here since applier expects list of dicts
    rows = []
    with Path(args.plan).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    res = apply_moves(
        rows, Path(args.checkpoint),
        dry_run=(cfg["dry_run"] and not args.force)
    )
    print(f"[apply] {res}")
    return 0 if res["errors"] == 0 else 1
