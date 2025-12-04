# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Similarity search subsystem.

This package provides a pluggable framework for vector similarity search.
It abstracts the underlying implementation (e.g., FAISS, brute-force)
behind a common interface, allowing for flexible backend selection and
easy extension.

Key Components:
    - index: Factory and persistence logic
    - backends: Plugin discovery and loading
    - cli: High-level CLI operations

Exports:
    - make_index: Create a new index
    - list_backends: List available plugins
    - default_backend_name: Get the preferred backend
    - save/load/update functions for index persistence
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
