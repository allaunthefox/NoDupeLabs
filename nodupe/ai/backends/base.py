# SPDX-License-Identifier: Apache-2.0
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
        return False

    def predict(self, path: Path) -> Tuple[int, str]:
        raise NotImplementedError()

    def compute_embedding(self, path: Path, dim: int = 16) -> List[float]:
        raise NotImplementedError()
