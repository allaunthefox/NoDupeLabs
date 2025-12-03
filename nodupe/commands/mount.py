# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from pathlib import Path
from ..mount import mount_fs


def cmd_mount(args, cfg):
    """Mount command."""
    mount_fs(Path(cfg["db_path"]), Path(args.mountpoint))
    return 0
