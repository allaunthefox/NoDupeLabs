# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Similarity plugin for NoDupeLabs.

This plugin provides the similarity search functionality as a plugin that can be
loaded by the core system. It demonstrates how to convert existing
modules to plugins.

Key Features:
    - Similarity search
    - Multiple metrics
    - Result formatting
    - Plugin integration

Dependencies:
    - Core modules
"""

import argparse
from typing import Any

# Plugin manager is injected by the core system
pm: Any = None


class SimilarityPlugin:
    """Similarity plugin implementation.

    Responsibilities:
    - Register with plugin manager
    - Provide similarity functionality
    - Handle plugin lifecycle
    - Error handling
    """

    def __init__(self):
        """Initialize similarity plugin."""
        self.name = "similarity"
        self.description = "Find similar files using various metrics"

        # Register plugin with manager
        if pm:
            pm.register_hook("similarity_start", self._on_similarity_start)
            pm.register_hook("similarity_complete",
                             self._on_similarity_complete)

    def _on_similarity_start(self, **kwargs: Any) -> None:
        """Handle similarity start event."""
        print(
            f"[PLUGIN] Similarity search started: {kwargs.get('metric', 'unknown')}")

    def _on_similarity_complete(self, **kwargs: Any) -> None:
        """Handle similarity complete event."""
        print(
            f"[PLUGIN] Similarity search completed: {kwargs.get('pairs_found', 0)} similar pairs found")

    def register_commands(self, subparsers: Any) -> None:
        """Register similarity command with argument parser.

        Args:
            subparsers: Argument parser subparsers
        """
        similarity_parser = subparsers.add_parser(
            'similarity', help='Find similar files')
        similarity_parser.add_argument(
            '--metric',
            choices=['name', 'size', 'hash', 'content'],
            default='name',
            help='Similarity metric'
        )
        similarity_parser.add_argument(
            '--threshold',
            type=float,
            default=0.8,
            help='Similarity threshold'
        )
        similarity_parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum results per file'
        )
        similarity_parser.add_argument(
            '--output',
            choices=['text', 'json', 'csv'],
            default='text',
            help='Output format'
        )
        similarity_parser.add_argument(
            '--verbose', '-v', action='store_true', help='Verbose output')
        similarity_parser.set_defaults(func=self.execute_similarity)

    def execute_similarity(self, args: argparse.Namespace) -> int:
        """Execute similarity command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code
        """
        try:
            print(
                f"[PLUGIN] Executing similarity command: {args.metric} metric")

            # Emit similarity start event
            if pm:
                pm.emit_event("similarity_start", metric=args.metric)

            # Here you would implement the actual similarity logic
            # For now, we'll simulate a similarity search
            pairs_found = 3  # Simulate finding similar pairs

            print(
                f"[PLUGIN] Found {pairs_found} similar file pairs using {args.metric} metric")

            # Emit similarity complete event
            if pm:
                pm.emit_event("similarity_complete", pairs_found=pairs_found)

            print(
                f"[PLUGIN] Similarity search completed: {pairs_found} pairs found")
            return 0

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[PLUGIN ERROR] Similarity search failed: {e}")
            return 1


# Create plugin instance when module is loaded
similarity_plugin = SimilarityPlugin()

# Register plugin with core system


def register_plugin():
    """Register plugin with core system."""
    return similarity_plugin


# Export plugin interface
__all__ = ['similarity_plugin', 'register_plugin']
