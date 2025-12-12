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
from typing import Any, Dict
from ..rollback import rollback_from_checkpoint


def cmd_rollback(args: Any, _cfg: Dict[str, Any]) -> int:
    """Revert a previous apply operation.

    This function reverses the file operations performed by a previous 'apply'
    command using its checkpoint file. It restores files to their original
    locations and verifies the restoration success.

    The rollback process:
    1. Loads the checkpoint file containing original file locations
    2. Validates that source files exist in .nodupe_duplicates/
    3. Moves files back to their original locations
    4. Verifies restoration success
    5. Reports statistics

    Args:
        args: Argparse Namespace with attributes:
            - checkpoint (str): Path to checkpoint JSON file
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for errors)

    Raises:
        FileNotFoundError: If checkpoint file doesn't exist
        PermissionError: If files can't be moved due to permissions
        OSError: If file operations fail
        Exception: For unexpected errors during rollback

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(checkpoint='.nodupe/checkpoints/cp_123.json')
        >>> exit_code = cmd_rollback(args, {})
        [rollback] {'restored': 15, 'errors': 0}
        >>> print(f"Rollback completed with exit code: {exit_code}")
        0

    Notes:
        - Exit code 0 indicates all files were restored successfully
        - Exit code 1 indicates some files failed to restore
        - Statistics are printed to stdout in JSON format
        - Checkpoint files are stored in .nodupe/checkpoints/ by default
        - Rollback is idempotent (can be run multiple times safely)
    """
    res = rollback_from_checkpoint(Path(args.checkpoint))
    print(f"[rollback] {res}")
    return 0 if res["errors"] == 0 else 1
