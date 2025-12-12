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
from typing import Any, Dict, List, Tuple, Optional
from ..similarity.cli import build_index_from_db, find_near_duplicates


def cmd_similarity_build(args: Any, cfg: Dict[str, Any]) -> int:
    """Build similarity index from database embeddings.

    This function extracts all embeddings from the SQLite database
    and constructs
    a searchable vector index for similarity search. It supports multiple index
    types (FAISS, Brute-force) based on the output file extension.

    The build process:
    1. Loads all embeddings from the database
    2. Validates embedding dimensions
    3. Constructs the appropriate index type
    4. Saves index to the specified output path
    5. Reports statistics

    Args:
        args: Argparse Namespace with attributes:
            - dim (int): Vector dimension (default: 16)
            - out (str): Output index file path
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success)

    Raises:
        FileNotFoundError: If database file doesn't exist
        ValueError: If invalid dimension or no embeddings found
        OSError: If index file can't be written
        Exception: For unexpected errors during index building

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(dim=128, out='index.faiss')
        >>> cfg = {'db_path': 'nodupe.db'}
        >>> exit_code = cmd_similarity_build(args, cfg)
        [similarity] index_count=1000
        >>> print(f"Build completed with exit code: {exit_code}")
        0

    Notes:
        - Index type determined by file extension (.faiss, .brute, etc.)
        - Higher dimensions provide better accuracy but require more memory
        - Index can be used for efficient similarity search
        - Reports number of embeddings indexed
    """
    db_path = Path(cfg['db_path'])
    res: Dict[str, int] = build_index_from_db(
        db_path, dim=args.dim, out_path=args.out
    )
    print(f"[similarity] index_count={res['index_count']}")
    return 0


def cmd_similarity_query(args: Any, cfg: Dict[str, Any]) -> int:
    """Find similar files to a target file.

    This function computes the embedding for a target file and queries
    the similarity index for nearest neighbors. It supports finding
    near-duplicate files based on
    vector similarity using AI embeddings.

    The query process:
    1. Loads or computes embedding for target file
    2. Queries the similarity index for nearest neighbors
    3. Returns results sorted by similarity score
    4. Displays results with distance scores

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

    Raises:
        FileNotFoundError: If target file or database doesn't exist
        ValueError: If invalid dimension or file type
        OSError: If file operations fail
        Exception: For unexpected errors during query

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(file='target.jpg', k=5, dim=128,
        ...                  index_file='index.faiss')
        >>> cfg = {'db_path': 'nodupe.db'}
        >>> exit_code = cmd_similarity_query(args, cfg)
        0.012345 /path/to/similar1.jpg
        0.045678 /path/to/similar2.jpg
        >>> print(f"Query completed with exit code: {exit_code}")
        0

    Notes:
        - Lower scores indicate higher similarity (0.0 = identical)
        - Results are sorted by similarity score (ascending)
        - Can use pre-built index or build on-the-fly
        - Supports multiple file types (images, videos, etc.)
        - Distance metric depends on index type
    """
    db_path = Path(cfg['db_path'])
    target = Path(args.file)
    res: List[Tuple[str, float]] = find_near_duplicates(
        db_path, target, k=args.k, dim=args.dim, index_path=args.index_file
    )
    for path, score in res:
        print(f"{score:>12.6f} {path}")
    return 0


def cmd_similarity_update(args: Any, cfg: Dict[str, Any]) -> int:
    """Update existing index with new embeddings.

    This function synchronizes an existing similarity index with the latest
    embeddings from the database. It supports both incremental updates and
    full rebuilds to maintain index accuracy.

    The update process:
    1. Loads existing index file
    2. Checks for new embeddings in database
    3. Adds new embeddings to index (or rebuilds if requested)
    4. Removes stale entries if rebuild is enabled
    5. Saves updated index
    6. Reports update statistics

    Args:
        args: Argparse Namespace with attributes:
            - index_file (str): Path to index file to update
            - rebuild (bool): If True, fully rebuild instead of incremental add
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success, 2 for missing args)

    Raises:
        FileNotFoundError: If index file or database doesn't exist
        ValueError: If invalid index format
        OSError: If file operations fail
        Exception: For unexpected errors during update

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(index_file='index.faiss', rebuild=False)
        >>> cfg = {'db_path': 'nodupe.db'}
        >>> exit_code = cmd_similarity_update(args, cfg)
        [similarity][update] added=10 index_count=1010
        >>> print(f"Update completed with exit code: {exit_code}")
        0

    Notes:
        - Incremental update is faster but may leave stale entries
        - Full rebuild removes stale entries but takes longer
        - Reports number of new embeddings added
        - Reports total index count after update
        - Exit code 2 indicates missing required arguments
    """
    from ..similarity.cli import update_index_from_db as _update
    db_path = Path(cfg['db_path'])
    if not args.index_file:
        print("[similarity][update] --index-file is required", file=sys.stderr)
        return 2
    res: Dict[str, Optional[int]] = _update(
        db_path, args.index_file, remove_missing=args.rebuild
    )
    print(
        f"[similarity][update] added={res.get('added')} "
        f"index_count={res.get('index_count')}"
    )
    return 0
