# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Checkpoint verification command.

This module implements the 'verify' command, which validates the integrity
of a deduplication operation by checking that all files moved during an
'apply' operation exist at their expected destination paths.

Key Features:
    - Load checkpoint manifest (JSON)
    - Verify existence of all destination files
    - Report missing files and overall success/failure

Usage:
    Used after 'nodupe apply' to ensure that the filesystem state matches
    the recorded checkpoint before deleting originals or finalizing.

Dependencies:
    - json: Manifest parsing
    - pathlib: File existence checks

Example:
    >>> # CLI usage
    >>> $ nodupe verify --checkpoint .nodupe/checkpoints/cp_123.json
    >>> [verify] OK. All destination files exist.
"""

import json
from pathlib import Path
from typing import Any, Dict


def cmd_verify(args: Any, _cfg: Dict[str, Any]) -> int:
    """Verify that all files in a checkpoint exist at destination.

    This function validates the integrity of a deduplication operation by
    checking that all files moved during an 'apply' operation exist at their
    expected destination paths. It provides a safety check before finalizing
    or deleting original files.

    The verification process:
    1. Loads the checkpoint JSON file
    2. Extracts all recorded move operations
    3. Checks existence of each destination file
    4. Reports missing files and overall status
    5. Returns appropriate exit code

    Args:
        args: Argparse Namespace with attributes:
            - checkpoint (str): Path to checkpoint JSON file
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for failure/missing files)

    Raises:
        FileNotFoundError: If checkpoint file doesn't exist
        json.JSONDecodeError: If checkpoint file is malformed
        PermissionError: If checkpoint file can't be read
        OSError: If file operations fail

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(checkpoint='.nodupe/checkpoints/cp_123.json')
        >>> exit_code = cmd_verify(args, {})
        [verify] Checking 15 moves in checkpoint...
        [verify] OK. All destination files exist.
        >>> print(f"Verification completed with exit code: {exit_code}")
        0

    Notes:
        - Exit code 0 indicates all files are present
        - Exit code 1 indicates missing files were found
        - Used as a safety check before finalizing deduplication
        - Reports detailed information about missing files
        - Checkpoint files are stored in .nodupe/checkpoints/ by default
    """
    cp = Path(args.checkpoint)
    if not cp.exists():
        print(f"[verify] checkpoint not found: {cp}")
        return 1

    manifest = json.loads(cp.read_text(encoding="utf-8"))
    moves = manifest.get("moves", [])
    missing = []

    print(f"[verify] Checking {len(moves)} moves in checkpoint...")

    for mv in moves:
        dst = Path(mv["dst"])
        if not dst.exists():
            missing.append(str(dst))
            print(f"[verify][FAIL] Missing destination file: {dst}")

    if missing:
        print(f"[verify] FAILED. {len(missing)} files missing.")
        return 1

    print("[verify] OK. All destination files exist.")
    return 0
