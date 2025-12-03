"""Similarity plugin package.

Expose a simple factory `make_index(dim, preferred=None)` and backend
discovery helpers.
"""
from .index import (
    make_index, save_index_to_file, load_index_from_file,
    update_index_file_from_vectors, update_index_from_db
)
from .backends import list_backends, default_backend_name, get_factory

__all__ = [
    "make_index",
    "list_backends",
    "default_backend_name",
    "get_factory",
    "save_index_to_file",
    "load_index_from_file",
    "update_index_file_from_vectors",
    "update_index_from_db",
]
