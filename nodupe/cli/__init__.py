# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI package.

Provides the command-line interface components.

Public API:
    - CLIBootstrapper: Handles startup/shutdown tasks
    - ArgumentBuilder: Builds argument parser
    - CommandRouter: Dispatches commands
    - check_scan_requirements: Re-exported for backwards compatibility
"""
from .bootstrapper import CLIBootstrapper
from .parser import ArgumentBuilder
from .router import CommandRouter

# Re-export for backwards compatibility (tests import from nodupe.cli)
from ..commands import check_scan_requirements  # noqa: F401

__all__ = [
    "CLIBootstrapper",
    "ArgumentBuilder",
    "CommandRouter",
    "check_scan_requirements",
]
