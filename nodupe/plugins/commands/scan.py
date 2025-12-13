# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan plugin for NoDupeLabs.

This plugin provides the scan functionality as a plugin that can be
loaded by the core system. It demonstrates how to convert existing
modules to plugins.

Key Features:
    - Directory scanning
    - File processing
    - Duplicate detection
    - Progress tracking
    - Plugin integration

Dependencies:
    - Core modules
"""

from typing import Any
import argparse

# Plugin manager is injected by the core system
PM = None

class ScanPlugin:
    """Scan plugin implementation.

    Responsibilities:
    - Register with plugin manager
    - Provide scan functionality
    - Handle plugin lifecycle
    - Error handling
    """

    def __init__(self):
        """Initialize scan plugin."""
        self.name = "scan"
        self.description = "Scan directories for duplicate files"

        # Register plugin with manager
        if PM:
            PM.register_hook("scan_start", self._on_scan_start)
            PM.register_hook("scan_complete", self._on_scan_complete)

    def _on_scan_start(self, **kwargs: Any) -> None:
        """Handle scan start event."""
        print(f"[PLUGIN] Scan started: {kwargs.get('path', 'unknown')}")

    def _on_scan_complete(self, **kwargs: Any) -> None:
        """Handle scan complete event."""
        print(f"[PLUGIN] Scan completed: {kwargs.get('files_processed', 0)} files processed")

    def register_commands(self, subparsers: Any) -> None:
        """Register scan command with argument parser.

        Args:
            subparsers: Argument parser subparsers
        """
        scan_parser = subparsers.add_parser('scan', help='Scan directories for duplicates')
        scan_parser.add_argument('paths', nargs='+', help='Directories to scan')
        scan_parser.add_argument('--min-size', type=int, default=0, help='Minimum file size')
        scan_parser.add_argument('--max-size', type=int, help='Maximum file size')
        scan_parser.add_argument('--extensions', nargs='+', help='File extensions to include')
        scan_parser.add_argument('--exclude', nargs='+', help='Directories to exclude')
        scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        scan_parser.set_defaults(func=self.execute_scan)

    def execute_scan(self, args: argparse.Namespace) -> int:
        """Execute scan command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code
        """
        try:
            print(f"[PLUGIN] Executing scan command: {args.paths}")

            # Emit scan start event
            if PM:
                PM.emit_event("scan_start", path=args.paths)

            # Here you would implement the actual scan logic
            # For now, we'll simulate a scan
            files_processed = 0
            for path in args.paths:
                print(f"[PLUGIN] Scanning: {path}")
                files_processed += 10  # Simulate finding files

            # Emit scan complete event
            if PM:
                PM.emit_event("scan_complete", files_processed=files_processed)

            print(f"[PLUGIN] Scan completed: {files_processed} files processed")
            return 0

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[PLUGIN ERROR] Scan failed: {e}")
            return 1

# Create plugin instance when module is loaded
scan_plugin = ScanPlugin()

# Register plugin with core system
def register_plugin():
    """Register plugin with core system."""
    return scan_plugin

# Export plugin interface
__all__ = ['scan_plugin', 'register_plugin']
