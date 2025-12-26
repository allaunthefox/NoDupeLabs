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

from nodupe.core.plugin_system.base import Plugin
import argparse
from typing import Any, Dict

# Plugin manager is injected by the core system
PM: Any = None

# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {
    "uuid": "07a94075-6cb0-437c-9bf1-4a284b13e7ac",
    "name": "similarity_command",
    "display_name": "Similarity Search Plugin",
    "version": "v1.0.0",
    "description": "Find similar files using various metrics",
    "author": "NoDupeLabs Team",
    "category": "ml",
    "dependencies": ["similarity_backend"],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["similarity", "ml", "search", "duplicate-detection"],
    "marketplace_id": "similarity_command_07a94075-6cb0-437c-9bf1-4a284b13e7ac"
}


class SimilarityCommandPlugin(Plugin):
    """Similarity command plugin implementation."""

    def __init__(self):
        """Initialize similarity plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['similarity']}

    def _on_similarity_start(self, **kwargs: Any) -> None:
        """Handle similarity start event."""
        print(f"[PLUGIN] Similarity search started: {kwargs.get('metric', 'unknown')}")

    def _on_similarity_complete(self, **kwargs: Any) -> None:
        """Handle similarity complete event."""
        print(
            f"[PLUGIN] Similarity search completed: {kwargs.get('pairs_found', 0)} similar pairs found")

    def register_commands(self, subparsers: Any) -> None:
        """Register similarity command with argument parser."""
        similarity_parser = subparsers.add_parser(
            'similarity', help='Find similar files')
        similarity_parser.add_argument(
            '--metric',
            choices=['name', 'size', 'hash', 'content', 'vector'],
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
        similarity_parser.set_defaults(func=self.execute_similarity)

    def execute_similarity(self, args: argparse.Namespace) -> int:
        """Execute similarity command."""
        try:
            # Validation
            # Check if query_file is provided (for compatibility with tests)
            if hasattr(args, 'query_file') and args.query_file is None:
                print("[ERROR] Query file is required")
                return 1
            
            # Validate threshold is in range 0.0-1.0
            if hasattr(args, 'threshold'):
                if args.threshold < 0.0 or args.threshold > 1.0:
                    print(f"[ERROR] Threshold must be between 0.0 and 1.0, got {args.threshold}")
                    return 1
            
            # Validate k/limit is positive integer
            if hasattr(args, 'k'):
                if args.k <= 0:
                    print(f"[ERROR] k must be a positive integer, got {args.k}")
                    return 1
            elif hasattr(args, 'limit'):
                if args.limit <= 0:
                    print(f"[ERROR] limit must be a positive integer, got {args.limit}")
                    return 1
            
            # Validate metric is one of the allowed choices
            valid_metrics = ['name', 'size', 'hash', 'content', 'vector']
            if args.metric not in valid_metrics:
                print(f"[ERROR] Invalid metric: {args.metric}. Must be one of: {', '.join(valid_metrics)}")
                return 1
            
            print(f"[PLUGIN] Executing similarity command: {args.metric} metric")

            # 1. Get services
            container = getattr(args, 'container', None)
            if not container:
                # Fallback to global if arg injection fail
                from nodupe.core.container import container as global_container
                container = global_container

            db = container.get_service('database')
            if not db:
                print("[ERROR] Database service not available (required for file access)")
                # Attempt default connection?
                from nodupe.core.database.connection import DatabaseConnection
                db = DatabaseConnection.get_instance()

            # Import needed classes locally to avoid circular top-level imports if any
            from nodupe.core.database.files import FileRepository

            repo = FileRepository(db)
            files = repo.get_all_files()

            if not files:
                print("[PLUGIN] No files in database to analyze.")
                return 0

            print(f"[PLUGIN] Analyzing {len(files)} files using metric: {args.metric}")

            pairs_found = 0

            if args.metric in ['hash', 'size', 'name']:
                # Use in-memory grouping for exact matches
                field_map = {'hash': 'hash', 'size': 'size', 'name': 'name'}
                field = field_map.get(args.metric)

                # Grouping
                groups = {}
                for f in files:
                    val = f.get(field)
                    if not val:
                        continue
                    if val not in groups:
                        groups[val] = []
                    groups[val].append(f)

                # Detect
                for val, group in groups.items():
                    if len(group) > 1:
                        # Found duplicates
                        pairs_found += len(group) - 1

                        # Sort by path length (shorter is "original" usually, or random)
                        group.sort(key=lambda x: len(x['path']))
                        # Or sort by time? group.sort(key=lambda x: x['created_time'])
                        # Let's keep it simple: first found (id) or shortest path is original.

                        original = group[0]
                        duplicates = group[1:]

                        # Update DB
                        for dup in duplicates:
                            repo.mark_as_duplicate(dup['id'], original['id'])
                            if hasattr(args, 'verbose') and args.verbose:
                                print(f"  [DUP] {dup['path']} == {original['path']}")

            elif args.metric == 'vector':
                print("[PLUGIN] Vector similarity search not yet implemented (requires embedding generation)")
                # Future: Use SimilarityManager here

            print(f"[PLUGIN] Analysis complete.")
            print(f"[PLUGIN] Marked {pairs_found} files as duplicates.")

            self._on_similarity_complete(pairs_found=pairs_found)
            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Similarity search failed: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            return 1


# Create plugin instance when module is loaded
similarity_plugin = SimilarityCommandPlugin()


def register_plugin():
    """Register plugin with core system."""
    return similarity_plugin


# Export plugin interface
__all__ = ['similarity_plugin', 'register_plugin']
