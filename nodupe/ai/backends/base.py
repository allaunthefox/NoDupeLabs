# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Abstract base class for AI backends.

Defines the interface that all AI backends must implement. This ensures
consistency across different implementations (CPU, ONNX, etc.).

Classes:
    - BaseBackend: Abstract interface for prediction and embedding
"""
from __future__ import annotations
from pathlib import Path
from typing import Tuple, List


class BaseBackend:
    """Abstract simple interface used by NSFWClassifier.

    Methods:
    - available() -> bool
    - predict(path: Path) -> Tuple[int, str]  # score 0-3, reason
    - compute_embedding(path: Path, dim: int) -> List[float]
    """

    def available(self) -> bool:
        """Check if backend is available (dependencies installed)."""
        return False

    def predict(self, path: Path) -> Tuple[int, str]:
        """Predict NSFW score for a file.

        Args:
            path: Path to the file (image or video)

        Returns:
            Tuple of (score, reason) where score is 0-3
        """
        raise NotImplementedError()

    def compute_embedding(self, path: Path, dim: int = 16) -> List[float]:
        """Compute vector embedding for a file.

        Args:
            path: Path to the file
            dim: Dimension of the embedding vector

        Returns:
            List of floats representing the embedding
        """
        raise NotImplementedError()
