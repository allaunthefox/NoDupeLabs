# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Pluggable similarity index factory and persistence.

This module provides a unified interface for creating, saving, and loading
similarity indices. It supports multiple backends (e.g., FAISS, BruteForce)
and handles format-specific persistence logic.

Key Features:
    - Factory pattern for index creation (make_index)
    - Backend plugin discovery
    - Unified save/load interface supporting multiple formats (.index, .npz)
    - Incremental index updates from database records

Functions:
    - make_index: Create a new index instance
    - save_index_to_file: Persist index to disk
    - load_index_from_file: Load index from disk
    - update_index_from_db: Sync index with database embeddings

Dependencies:
    - .backends: Backend implementations
    - pathlib: File handling
"""
from __future__ import annotations
from typing import Optional, List, Any, Dict
from pathlib import Path
from .backends import list_backends, get_factory, default_backend_name


def make_index(dim: int, preferred: Optional[str] = None):
    """Create and return a similarity index instance.

    The function will attempt to use the named `preferred` backend. If
    that backend is unavailable the implementation falls back to the
    default backend determined by :func:`default_backend_name` and, if
    necessary, to the first available backend.

    Args:
        dim: Dimensionality of the embeddings the index will store.
        preferred: Optional backend name hint (eg. 'faiss_backend').

    Returns:
        A backend-specific index instance supporting an ``add`` method
        and other backend-specific operations.

    Raises:
        RuntimeError: If no similarity backend factories are available.
    """
    names = list_backends()
    if not names:
        raise RuntimeError("No similarity backends available")

    # if preferred is provided, try it first
    cand = None
    if preferred:
        cand = get_factory(preferred)

    if not cand:
        # try default
        default_name = default_backend_name()
        cand = get_factory(default_name)

    if not cand:
        # pick the first available
        cand = get_factory(names[0])

    if not cand:
        raise RuntimeError("No usable similarity backend factory found")

    return cand(dim)


def save_index_to_file(index_obj: Any, path: str) -> None:
    """Persist an index to disk using backend-specific logic.

    The method chooses a storage format based on the filename suffix and
    delegates to the appropriate backend implementation.

    Args:
        index_obj: Backend index object or structure to persist.
        path: Destination path where the index should be stored.

    Raises:
        RuntimeError: When the backend doesn't support the requested
            storage operation or the file extension is not supported.
    """
    p = Path(path)
    ext = p.suffix.lower()
    # prefer faiss for .index/.faiss
    if ext in ('.index', '.faiss'):
        # expect faiss backend instance
        if hasattr(index_obj, 'save'):
            index_obj.save(str(path))
            return
        raise RuntimeError('Backend does not support save to .index')

    if ext in ('.npz', '.json', '.jsonl'):
        # bruteforce style save()
        # backend module exposes save(index_obj, path)
        # call bruteforce_backend.save
        try:
            # import module
            import importlib
            mod = importlib.import_module(
                'nodupe.similarity.backends.bruteforce_backend'
            )
            if hasattr(mod, 'save'):
                mod.save(index_obj, str(path))
                return
        except Exception as e:
            raise RuntimeError(f'Failed to save index: {e}') from e

    raise RuntimeError('Unsupported index file extension')


def load_index_from_file(path: str):
    """Load and return a similarity index from disk.

    The loader will select a suitable backend based on the file
    extension and call the backend-specific ``load`` function.

    Args:
        path: Path of the index file to load.

    Returns:
        A backend-specific index instance.

    Raises:
        RuntimeError: When the backend loader fails or the file extension
            is unsupported.
    """
    p = Path(path)
    ext = p.suffix.lower()
    if ext in ('.index', '.faiss'):
        # use faiss backend loader
        try:
            import importlib
            mod = importlib.import_module(
                'nodupe.similarity.backends.faiss_backend'
            )
            if hasattr(mod, 'load'):
                return mod.load(str(path))
        except Exception as e:
            raise RuntimeError(f'Failed to load faiss index: {e}') from e

    if ext in ('.npz', '.json', '.jsonl'):
        try:
            import importlib
            mod = importlib.import_module(
                'nodupe.similarity.backends.bruteforce_backend'
            )
            if hasattr(mod, 'load'):
                return mod.load(str(path))
        except Exception as e:
            raise RuntimeError(f'Failed to load bruteforce index: {e}') from e

    raise RuntimeError('Unsupported index file extension')


def update_index_file_from_vectors(
    path: str, vectors: List[List[float]], ids: List[str]
) -> None:
    """Append a collection of vectors/ids to an existing index file.

    The function will load the existing index file, add the provided
    vectors and ids, and then persist the updated index back to `path`.

    Args:
        path: Path to the existing index file.
        vectors: Sequence of embedding vectors to append.
        ids: Sequence of string identifiers corresponding to `vectors`.
    """
    # Load existing index (or raise)
    idx = load_index_from_file(path)
    # add new vectors
    idx.add(vectors, ids=ids)
    # save back
    save_index_to_file(idx, path)


def update_index_from_db(
    index_path: str, db_obj: Any, remove_missing: bool = False
) -> Dict[str, int]:
    """Append new embeddings from a DB-like object to an existing index file.

    db_obj is expected to provide get_all_embeddings() which yields
    (path, dim, vector, mtime) rows (same shape as
    nodupe.db.DB.get_all_embeddings).

    Returns:
        A mapping with statistics about the update: {'added': n_added,
        'index_count': total_after}.
    """
    # load existing index
    idx_dim = None
    try:
        idx = load_index_from_file(index_path)
        idx_dim = getattr(idx, 'dim', None)
        existing_ids = getattr(idx, 'ids', [])
    except (OSError, ValueError, RuntimeError):
        # Index not present or couldn't be loaded - if remove_missing is True
        # we will attempt to construct a fresh index from DB (inferring dim
        # from DB); otherwise re-raise.
        if not remove_missing:
            raise
        # infer dim from DB entries
        rows = db_obj.get_all_embeddings()
        # We need to peek at the first item to get dim, but rows is a
        # generator. We can't just check "if not rows".
        try:
            first_row = next(rows)
        except StopIteration:
            raise RuntimeError(
                "Index not found and DB has no embeddings to build from"
            )

        # Put it back or handle it. Since we can't put it back easily without
        # itertools.chain, let's just use it.
        p, d, vec, _ = first_row
        if vec:
            idx_dim = d
        else:
            # If first row has no vector, we might be in trouble if we need to
            # infer dim. But let's assume we can find one.
            # Actually, let's just restart the generator if possible, or
            # collect a few. Since we changed get_all_embeddings to be a
            # generator, we can't iterate it twice easily unless we make a new
            # call.
            # But db_obj is passed in. If it's a DB instance, we can call
            # get_all_embeddings() again.
            pass

        # Better approach: just call get_all_embeddings() again since it's a
        # method on DB. But db_obj is typed as Any.

        # Let's assume we can call it again.
        rows = db_obj.get_all_embeddings()
        for _, d, vec, _ in rows:
            if vec:
                idx_dim = d
                break

        if idx_dim is None:
            raise RuntimeError(
                "Cannot infer embedding dimension to build index"
            )
        # create fresh index
        idx = make_index(idx_dim)
        existing_ids = []

    # collect missing embeddings from DB
    # collect missing embeddings from DB
    added = 0

    # Convert existing_ids to set for O(1) lookup
    existing_ids_set = set(existing_ids)

    BATCH_SIZE = 10000
    vectors_batch: List[List[float]] = []
    ids_batch: List[str] = []

    def flush_batch():
        """Flush the current vectors/ids batch into the index.

        This helper appends the accumulated vectors_batch/ids_batch into
        the index and resets the batch buffers. It's used for both
        incremental updates and full rebuilds.
        """
        nonlocal added, vectors_batch, ids_batch
        if vectors_batch:
            idx.add(vectors_batch, ids=ids_batch)
            added += len(ids_batch)
            vectors_batch = []
            ids_batch = []

    if remove_missing:
        # rebuild full index from DB: include all embeddings that match idx_dim
        # For rebuild, we create a new index, so existing_ids is irrelevant
        # (empty)
        if idx_dim is not None:
            idx = make_index(idx_dim)

        for p, d, vec, _ in db_obj.get_all_embeddings():
            if not vec:
                continue
            if d != idx_dim:
                continue
            vectors_batch.append(vec)
            ids_batch.append(p)
            if len(vectors_batch) >= BATCH_SIZE:
                flush_batch()
        flush_batch()
        save_index_to_file(idx, index_path)

    else:
        # Incremental update
        for p, d, vec, _ in db_obj.get_all_embeddings():
            if not vec:
                continue
            if idx_dim is not None and d != idx_dim:
                continue
            if p in existing_ids_set:
                continue

            vectors_batch.append(vec)
            ids_batch.append(p)
            if len(vectors_batch) >= BATCH_SIZE:
                flush_batch()

        flush_batch()
        if added > 0:
            save_index_to_file(idx, index_path)

    return {"added": added, "index_count": len(getattr(idx, 'ids', []))}
