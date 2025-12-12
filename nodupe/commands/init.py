# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Configuration initialization command.

This module implements the 'init' command, which bootstraps a new
configuration file for the NoDupeLabs environment. It supports
various presets to tailor the configuration for different use cases.

Key Features:
    - Create new configuration file (nodupe.yml)
    - Support for configuration presets (default, minimal, etc.)
    - Safe creation (fails if exists unless --force is used)

Dependencies:
    - pathlib: Path handling
    - ..config: Configuration generation logic

Example:
    >>> # CLI usage
    >>> $ nodupe init --preset default
    >>> [init] Created nodupe.yml using 'default' preset.
"""

import sys
from pathlib import Path
from typing import Any, Dict
from ..config import ensure_config


def cmd_init(args: Any, _cfg: Dict[str, Any]) -> int:
    """Initialize configuration with a preset.

    This function creates a new 'nodupe.yml' configuration file in the current
    directory using the specified preset. It handles both new configurations and
    existing file scenarios with proper error handling and user feedback.

    Args:
        args: Argparse Namespace with attributes:
            - preset (str): Configuration preset name (default: 'default')
            - force (bool): Overwrite existing file if True
        _cfg: Configuration dictionary (unused, as we are creating it)

    Returns:
        int: Exit code (0 for success, 1 for error)

    Raises:
        PermissionError: If file cannot be created due to permissions
        OSError: If file operations fail
        Exception: For unexpected errors during configuration generation

    Example:
        >>> from nodupe.commands.init import cmd_init
        >>> import argparse
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--preset', default='default')
        >>> parser.add_argument('--force', action='store_true')
        >>> args = parser.parse_args(['--preset', 'minimal'])
        >>> exit_code = cmd_init(args, {})
        >>> print(f"Initialization completed with exit code: {exit_code}")
    """
    p = Path("nodupe.yml")
    if p.exists() and not args.force:
        print(
            f"[init] Config file {p} already exists. Use --force to "
            f"overwrite.",
            file=sys.stderr
        )
        return 1

    if args.force and p.exists():
        p.unlink()

    ensure_config("nodupe.yml", preset=args.preset)
    print(f"[init] Created nodupe.yml using '{args.preset}' preset.")
    return 0
