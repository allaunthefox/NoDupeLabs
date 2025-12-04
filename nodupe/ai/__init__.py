# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""AI subsystem for NSFW classification and embeddings.

This package provides AI-powered functionality including NSFW content
classification and embedding computation. It uses a pluggable backend
system that supports both ONNX Runtime and CPU-based inference.

Subpackages:
    - backends: AI backend implementations (ONNX, CPU)

Public API:
    From backends:
        - choose_backend: Select the best available AI backend
        - BaseBackend: Base class for AI backends
"""

from .backends import choose_backend, BaseBackend

__all__ = ["choose_backend", "BaseBackend"]
