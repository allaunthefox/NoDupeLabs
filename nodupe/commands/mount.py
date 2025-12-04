# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""FUSE filesystem mount command.

This module implements the 'mount' command, which exposes the deduplicated
content database as a read-only FUSE filesystem. This allows users to
browse the file index as a virtual directory structure.

Key Features:
    - Mount SQLite database as virtual filesystem
    - Read-only access to indexed files
    - Custom directory structure views (by hash, by type, etc.)

Dependencies:
    - pathlib: Path handling
    - ..mount: FUSE implementation

Example:
    >>> # CLI usage
    >>> $ nodupe mount /mnt/nodupe
"""

from pathlib import Path
from ..mount import mount_fs


def cmd_mount(args, cfg):
    """Mount the database as a FUSE filesystem.

    Args:
        args: Argparse Namespace with attributes:
            - mountpoint (str): Directory to mount the filesystem
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success)
    """
    mount_fs(Path(cfg["db_path"]), Path(args.mountpoint))
    return 0
