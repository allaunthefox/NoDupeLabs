# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Similarity search command interface.

This module implements the 'similarity' command group, providing tools for
building, querying, and updating vector similarity indices. It enables
finding near-duplicate files (e.g., resized images, transcoded videos)
using AI embeddings.

Key Features:
    - Build FAISS/Brute-force indices from database embeddings
    - Query indices for similar files with distance metrics
    - Update existing indices with new database entries
    - Support for multiple backend types (FAISS, Brute-force)

Commands:
    - build: Create a new similarity index from DB
    - query: Find nearest neighbors for a target file
    - update: Add new embeddings to an existing index

Dependencies:
    - pathlib: Path handling
    - ..similarity.cli: Core implementation of index operations

Example:
    >>> # CLI usage
    >>> $ nodupe similarity build --dim 128 --out index.faiss
    >>> $ nodupe similarity query target.jpg --index-file index.faiss
    >>> $ nodupe similarity update --index-file index.faiss
"""

import sys
from pathlib import Path
from ..similarity.cli import build_index_from_db, find_near_duplicates


def cmd_similarity_build(args, cfg):
    """Build similarity index from database embeddings.

    Extracts all embeddings from the SQLite database and constructs a
    searchable vector index. The index type depends on the output filename
    extension or configuration.

    Args:
        args: Argparse Namespace with attributes:
            - dim (int): Vector dimension (default: 16)
            - out (str): Output index file path
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success)
    """
    db_path = Path(cfg['db_path'])
    res = build_index_from_db(db_path, dim=args.dim, out_path=args.out)
    print(f"[similarity] index_count={res['index_count']}")
    return 0


def cmd_similarity_query(args, cfg):
    """Find similar files to a target file.

    Computes embedding for the target file (or retrieves from DB) and
    queries the index for nearest neighbors.

    Args:
        args: Argparse Namespace with attributes:
            - file (str): Path to target file
            - k (int): Number of neighbors to retrieve (default: 5)
            - dim (int): Vector dimension (default: 16)
            - index_file (str, optional): Path to pre-built index
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success)
    """
    db_path = Path(cfg['db_path'])
    target = Path(args.file)
    res = find_near_duplicates(
        db_path, target, k=args.k, dim=args.dim, index_path=args.index_file
    )
    for path, score in res:
        print(f"{score:>12.6f} {path}")
    return 0


def cmd_similarity_update(args, cfg):
    """Update existing index with new embeddings.

    Syncs an existing index file with the latest embeddings from the
    database. Can optionally rebuild the entire index to remove stale entries.

    Args:
        args: Argparse Namespace with attributes:
            - index_file (str): Path to index file to update
            - rebuild (bool): If True, fully rebuild instead of incremental add
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success, 2 for missing args)
    """
    from ..similarity.cli import update_index_from_db as _update
    db_path = Path(cfg['db_path'])
    if not args.index_file:
        print("[similarity][update] --index-file is required", file=sys.stderr)
        return 2
    res = _update(db_path, args.index_file, remove_missing=args.rebuild)
    print(
        f"[similarity][update] added={res.get('added')} "
        f"index_count={res.get('index_count')}"
    )
    return 0
