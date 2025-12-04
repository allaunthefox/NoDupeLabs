# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Rollback command for reversing deduplication operations.

This module implements the 'rollback' command, which reverses the file
moves performed by a previous 'apply' command using its checkpoint file.
It restores files to their original locations.

Key Features:
    - Reverse file moves using checkpoint manifest
    - Restore original directory structure
    - Verify restoration success

Dependencies:
    - pathlib: Path handling
    - ..rollback: Core rollback logic

Example:
    >>> # CLI usage
    >>> $ nodupe rollback --checkpoint .nodupe/checkpoints/cp_123.json
    >>> [rollback] {'restored': 15, 'errors': 0}
"""

from pathlib import Path
from ..rollback import rollback_from_checkpoint


def cmd_rollback(args, _cfg):
    """Revert a previous apply operation.

    Args:
        args: Argparse Namespace with attributes:
            - checkpoint (str): Path to checkpoint JSON file
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for errors)
    """
    res = rollback_from_checkpoint(Path(args.checkpoint))
    print(f"[rollback] {res}")
    return 0 if res["errors"] == 0 else 1
