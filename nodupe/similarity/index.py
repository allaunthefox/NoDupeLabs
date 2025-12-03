"""Pluggable similarity index factory.

This module exposes make_index(dim, preferred=None) which will attempt to
use a plugin backend found under `nodupe.similarity.backends`. Backends may
be added or removed by creating/removing files under the `backends` package.
"""
from __future__ import annotations
from typing import Optional
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
