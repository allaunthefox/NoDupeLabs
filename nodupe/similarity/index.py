"""Pluggable similarity index factory.

This module exposes make_index(dim, preferred=None) which will attempt to
use a plugin backend found under `nodupe.similarity.backends`. Backends may
be added or removed by creating/removing files under the `backends` package.
"""
from __future__ import annotations
from typing import Optional
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


def save_index_to_file(index_obj, path: str) -> None:
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
        from .backends import get_factory
        # find brutal backend
        from .backends import get_factory as _get
        # call bruteforce_backend.save
        try:
            # import module
            import importlib
            mod = importlib.import_module('nodupe.similarity.backends.bruteforce_backend')
            if hasattr(mod, 'save'):
                mod.save(index_obj, str(path))
                return
        except Exception as e:
            raise RuntimeError(f'Failed to save index: {e}')

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
            raise RuntimeError(f'Failed to load faiss index: {e}')

    if ext in ('.npz',):
        try:
            import importlib
            mod = importlib.import_module('nodupe.similarity.backends.bruteforce_backend')
            if hasattr(mod, 'load'):
                return mod.load(str(path))
        except Exception as e:
            raise RuntimeError(f'Failed to load bruteforce index: {e}')

    raise RuntimeError('Unsupported index file extension')
