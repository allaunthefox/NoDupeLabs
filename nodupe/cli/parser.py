# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Argument parser builder.

Constructs the CLI argument parser with all subcommands.
"""
import argparse
from typing import Callable, Dict, List, Optional


class ArgumentBuilder:
    """Builds the CLI argument parser.

    Constructs argparse parser with all subcommands and their arguments.
    Separates parser construction from command dispatch.
    """

    def __init__(
        self,
        prog: str = "nodupe",
        version: str = "0.1.0",
        presets: Optional[List[str]] = None
    ):
        """Initialize argument builder.

        Args:
            prog: Program name
            version: Version string
            presets: Available configuration presets
        """
        self.prog = prog
        self.version = version
        self.presets = presets or ["default"]

    def build(self, commands: Dict[str, Callable]) -> argparse.ArgumentParser:
        """Build the argument parser.

        Args:
            commands: Dict mapping command names to handlers

        Returns:
            Configured ArgumentParser
        """
        parser = argparse.ArgumentParser(prog=self.prog)
        parser.add_argument(
            '--version', action='version',
            version=f'%(prog)s {self.version}'
        )
        sub = parser.add_subparsers(dest="cmd", required=True)

        # Init
        self._add_init_parser(sub, commands)

        # Scan
        self._add_scan_parser(sub, commands)

        # Plan
        self._add_plan_parser(sub, commands)

        # Apply
        self._add_apply_parser(sub, commands)

        # Rollback
        self._add_rollback_parser(sub, commands)

        # Verify
        self._add_verify_parser(sub, commands)

        # Mount
        self._add_mount_parser(sub, commands)

        # Archive
        self._add_archive_parser(sub, commands)

        # Similarity
        self._add_similarity_parser(sub, commands)

        return parser

    def _add_init_parser(self, sub, commands):
        """Add init subcommand."""
        p = sub.add_parser("init", help="Initialize configuration")
        p.add_argument(
            "--preset", choices=self.presets, default="default",
            help="Configuration preset"
        )
        p.add_argument(
            "--force", action="store_true", help="Overwrite existing config"
        )
        p.set_defaults(_run=commands["init"])

    def _add_scan_parser(self, sub, commands):
        """Add scan subcommand."""
        p = sub.add_parser("scan")
        p.add_argument("--root", action="append", required=True)
        p.add_argument(
            "--progress", choices=("auto", "quiet", "interactive"),
            default=None,
            help="Control progress UI (auto|quiet|interactive)"
        )
        p.set_defaults(_run=commands["scan"])

    def _add_plan_parser(self, sub, commands):
        """Add plan subcommand."""
        p = sub.add_parser("plan")
        p.add_argument("--out", required=True)
        p.set_defaults(_run=commands["plan"])

    def _add_apply_parser(self, sub, commands):
        """Add apply subcommand."""
        p = sub.add_parser("apply")
        p.add_argument("--plan", required=True)
        p.add_argument("--checkpoint", required=True)
        p.add_argument("--force", action="store_true")
        p.set_defaults(_run=commands["apply"])

    def _add_rollback_parser(self, sub, commands):
        """Add rollback subcommand."""
        p = sub.add_parser("rollback")
        p.add_argument("--checkpoint", required=True)
        p.set_defaults(_run=commands["rollback"])

    def _add_verify_parser(self, sub, commands):
        """Add verify subcommand."""
        p = sub.add_parser("verify")
        p.add_argument("--checkpoint", required=True)
        p.set_defaults(_run=commands["verify"])

    def _add_mount_parser(self, sub, commands):
        """Add mount subcommand."""
        p = sub.add_parser("mount")
        p.add_argument("mountpoint", help="Directory to mount")
        p.set_defaults(_run=commands["mount"])

    def _add_archive_parser(self, sub, commands):
        """Add archive subcommand."""
        p = sub.add_parser("archive")
        p_sub = p.add_subparsers(dest="archive_cmd", required=True)

        p_l = p_sub.add_parser("list")
        p_l.add_argument("file")
        p_l.set_defaults(_run=commands["archive:list"])

        p_e = p_sub.add_parser("extract")
        p_e.add_argument("file")
        p_e.add_argument("--dest", required=True)
        p_e.set_defaults(_run=commands["archive:extract"])

    def _add_similarity_parser(self, sub, commands):
        """Add similarity subcommand."""
        p = sub.add_parser("similarity")
        p_sub = p.add_subparsers(dest="sim_cmd", required=True)

        p_build = p_sub.add_parser("build")
        p_build.add_argument("--dim", type=int, default=16)
        p_build.add_argument("--out", help="Output index file")
        p_build.set_defaults(_run=commands["similarity:build"])

        p_query = p_sub.add_parser("query")
        p_query.add_argument("file")
        p_query.add_argument("--dim", type=int, default=16)
        p_query.add_argument("-k", type=int, default=5)
        p_query.add_argument("--index-file", help="Index file to load")
        p_query.set_defaults(_run=commands["similarity:query"])

        p_update = p_sub.add_parser("update")
        p_update.add_argument("--index-file", required=True)
        p_update.add_argument("--rebuild", action="store_true")
        p_update.set_defaults(_run=commands["similarity:update"])
