"""Similarity plugin package.

Expose a simple factory `make_index(dim, preferred=None)` and backend discovery helpers.
"""
from .index import make_index
from .backends import list_backends, default_backend_name, get_factory

__all__ = ["make_index", "list_backends", "default_backend_name", "get_factory"]
