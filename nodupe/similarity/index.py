"""Pluggable similarity index factory.

This module exposes make_index(dim, preferred=None) which will attempt to
use a plugin backend found under `nodupe.similarity.backends`. Backends may
be added or removed by creating/removing files under the `backends` package.
"""
from __future__ import annotations
from typing import Optional, List, Any, Dict
from pathlib import Path
from .backends import list_backends, get_factory, default_backend_name


def make_index(dim: int, preferred: Optional[str] = None):
    """Create an index instance using the preferred backend or the default.

    preferred may be the backend module name (e.g. 'faiss_backend' or 'bruteforce_backend').
    If preferred is not available we fall back to the default backend determined
    by `default_backend_name()`.
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
    """Persist index to disk using backend-specific methods.

    File extensions:
    - .index/.faiss -> FAISS index + ids
    - .npz          -> brute-force npz
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

    if ext in ('.npz',):
        # bruteforce style save()
        # backend module exposes save(index_obj, path)
        # call bruteforce_backend.save
        try:
            # import module
            import importlib
            mod = importlib.import_module('nodupe.similarity.backends.bruteforce_backend')
            if hasattr(mod, 'save'):
                mod.save(index_obj, str(path))
                return
        except Exception as e:
            raise RuntimeError(f'Failed to save index: {e}') from e

    raise RuntimeError('Unsupported index file extension')


def load_index_from_file(path: str):
    p = Path(path)
    ext = p.suffix.lower()
    if ext in ('.index', '.faiss'):
        # use faiss backend loader
        try:
            import importlib
            mod = importlib.import_module('nodupe.similarity.backends.faiss_backend')
            if hasattr(mod, 'load'):
                return mod.load(str(path))
        except Exception as e:
            raise RuntimeError(f'Failed to load faiss index: {e}') from e

    if ext in ('.npz',):
        try:
            import importlib
            mod = importlib.import_module('nodupe.similarity.backends.bruteforce_backend')
            if hasattr(mod, 'load'):
                return mod.load(str(path))
        except Exception as e:
            raise RuntimeError(f'Failed to load bruteforce index: {e}') from e

    raise RuntimeError('Unsupported index file extension')


def update_index_file_from_vectors(path: str, vectors: List[List[float]], ids: List[str]) -> None:
    """Load existing index file, append new vectors and ids, then save back.

    This supports the same file extensions as save/load: .index/.faiss and .npz
    """
    # Load existing index (or raise)
    idx = load_index_from_file(path)
    # add new vectors
    idx.add(vectors, ids=ids)
    # save back
    save_index_to_file(idx, path)


def update_index_from_db(index_path: str, db_obj: Any, remove_missing: bool = False) -> Dict[str, int]:
    """Append new embeddings from a DB-like object to an existing index file.

    db_obj is expected to provide get_all_embeddings() which yields
    (path, dim, vector, mtime) rows (same shape as nodupe.db.DB.get_all_embeddings).

    Returns a dict { 'added': n_added, 'index_count': total_after }
    """
    # load existing index
    idx_dim = None
    try:
        idx = load_index_from_file(index_path)
        idx_dim = getattr(idx, 'dim', None)
        existing_ids = getattr(idx, 'ids', [])
    except Exception as e:  # pylint: disable=broad-except
        # Index not present or couldn't be loaded - if remove_missing is True we will attempt to
        # construct a fresh index from DB (inferring dim from DB); otherwise re-raise.
        if not remove_missing:
            raise
        # infer dim from DB entries
        rows = db_obj.get_all_embeddings()
        if not rows:
            raise RuntimeError("Index not found and DB has no embeddings to build from") from e
        # pick dim from first row that has a vector
        for _, d, vec, _ in rows:
            if vec:
                idx_dim = d
                break
        if idx_dim is None:
            raise RuntimeError("Cannot infer embedding dimension to build index") from e
        # create fresh index
        idx = make_index(idx_dim)
        existing_ids = []

    # collect missing embeddings from DB
    added = 0
    vectors: List[List[float]] = []
    ids: List[str] = []
    for p, d, vec, _ in db_obj.get_all_embeddings():
        if not vec:
            continue
        if idx_dim is not None and d != idx_dim:
            continue
        if p in existing_ids:
            continue
        vectors.append(vec)
        ids.append(p)

    if remove_missing:
        # rebuild full index from DB: include all embeddings that match idx_dim
        vectors = []
        ids = []
        for p, d, vec, _ in db_obj.get_all_embeddings():
            if not vec:
                continue
            if d != idx_dim:
                continue
            vectors.append(vec)
            ids.append(p)

        if vectors:
            # recreate index
            assert idx_dim is not None
            idx = make_index(idx_dim)
            idx.add(vectors, ids=ids)
            save_index_to_file(idx, index_path)
            added = len(ids)
        else:
            added = 0
    else:
        if vectors:
            idx.add(vectors, ids=ids)
            save_index_to_file(idx, index_path)
            added = len(ids)
        added = len(ids)

    return {"added": added, "index_count": len(getattr(idx, 'ids', []))}
