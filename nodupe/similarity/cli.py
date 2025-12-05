# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""High-level similarity operations for CLI.

This module implements the core logic for similarity-related CLI commands.
It orchestrates the interaction between the database, AI backends, and
similarity indices to perform build, search, and update operations.

Key Features:
    - Build index from database embeddings
    - Compute missing embeddings on-the-fly
    - Search for nearest neighbors
    - Update existing indices

Functions:
    - build_index_from_db: Create and optionally save an index
    - find_near_duplicates: Search for similar files
    - update_index_from_db: Sync persisted index with DB

Dependencies:
    - .index: Index factory and persistence
    - ..ai.backends: Embedding computation
    - ..db: Database access
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from .index import make_index
from ..ai.backends import choose_backend
from ..db import DB


def build_index_from_db(
    db_path: Path, dim: int = 16, out_path: Optional[str] = None
) -> dict:
    """Build a similarity index from database embeddings.

    This function reads embeddings from the DB, computes any missing
    embeddings using the chosen AI backend, builds an in-memory index and
    optionally persists it to disk.

    Args:
        db_path: Path to the database file.
        dim: Embedding dimensionality to use.
        out_path: Optional path to persist the resulting index.

    Returns:
        Dict containing index metadata (e.g. index_count).
    """
    db = DB(db_path)
    # Use precomputed embeddings when available,
    # compute missing ones optionally
    be = choose_backend()
    idx = make_index(dim)

    embeddings = db.get_all_embeddings()
    vectors = []
    ids = []
    ids_set = set()

    for p, d, vec, _ in embeddings:
        if d != dim:
            # dimension mismatch — skip or convert? skip for now
            continue
        if not vec:
            continue
        vectors.append(vec)
        ids.append(p)
        ids_set.add(p)

    # Compute embeddings for images missing embeddings
    for r in db.iter_files():
        p_str = r[0]
        p = Path(p_str)
        mime = r[4]
        if not mime or not mime.startswith('image/'):
            continue
        if p_str in ids_set:
            continue
        # try to compute and store
        try:
            vec = be.compute_embedding(p, dim=dim)
            if vec:
                db.upsert_embedding(str(p), vec, dim, int(r[2]))
                vectors.append(vec)
                ids.append(str(p))
                ids_set.add(str(p))
        except Exception:  # pylint: disable=broad-except
            continue

    idx.add(vectors, ids=ids)

    if out_path:
        # persist to disk if requested: choose format based on extension
        try:
            from .index import save_index_to_file
            save_index_to_file(idx, out_path)
        except Exception as e:
            raise RuntimeError(f"Failed to save index: {e}") from e

    return {"index_count": len(ids)}


def find_near_duplicates(
    db_path: Path, target: Path, k: int = 5,
    dim: int = 16, index_path: Optional[str] = None
) -> List[tuple]:
    """Find files similar to the target file using a vector index.

    If ``index_path`` is provided the function will load a persisted
    index for fast searching. Otherwise it will build a temporary index
    from database embeddings and perform the search.

    Args:
        db_path: Path to the database file containing embeddings.
        target: Path to the file to search for near-duplicates.
        k: Number of nearest neighbors to return.
        dim: Expected embedding dimensionality.
        index_path: Optional persisted index path to load and search.

    Returns:
        List[Tuple[str, float]]: List of (file_path, distance) pairs.
    """
    # If an index file is provided, load it (fast).
    # Otherwise build from DB embeddings in memory.
    if index_path:
        from .index import load_index_from_file
        idx = load_index_from_file(index_path)
        be = choose_backend()
        vec = be.compute_embedding(target, dim=dim)
        return idx.search(vec, k=k)

    be = choose_backend()
    vec = be.compute_embedding(target, dim=dim)
    idx = make_index(dim)

    # Build from DB embeddings
    db = DB(db_path)
    embeddings = db.get_all_embeddings()
    vectors = []
    ids = []
    for p, d, vecv, _ in embeddings:
        if d != dim or not vecv:
            continue
        vectors.append(vecv)
        ids.append(p)

    idx.add(vectors, ids=ids)
    res = idx.search(vec, k=k)
    return res


def update_index_from_db(
    db_path: Path, index_path: str, remove_missing: bool = False
) -> dict:
    """Update an existing persisted index by appending embeddings from DB.

    Args:
        db_path: Path to the database file used as provenance for
            computing embeddings.
        index_path: Path to the persisted index to update.
        remove_missing: If True, remove index entries that no longer have
            corresponding DB records.

    Returns:
        Dict containing update metrics (e.g. counts of added/removed items).
    """
    db = DB(db_path)
    from .index import update_index_from_db as _upd
    return _upd(index_path, db, remove_missing=remove_missing)
