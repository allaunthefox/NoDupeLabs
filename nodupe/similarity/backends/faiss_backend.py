# SPDX-License-Identifier: Apache-2.0
try:
    import faiss  # type: ignore
except Exception:
    faiss = None  # type: ignore

import numpy as np
from typing import List, Optional, Tuple


class FaissIndex:
    def __init__(self, dim: int):
        if not faiss:
            raise RuntimeError("faiss not available")
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.ids: List[str] = []

    def add(self, vectors: List[List[float]], ids: Optional[List[str]] = None) -> None:
        arr = np.asarray(vectors, dtype='float32')
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError("Invalid vectors shape")
        self.index.add(arr)
        if ids:
            self.ids.extend(ids)
        else:
            self.ids.extend([str(i) for i in range(len(self.ids), len(self.ids) + len(vectors))])

    def search(self, vector: List[float], k: int = 5) -> List[Tuple[str, float]]:
        q = np.asarray([vector], dtype='float32')
        D, I = self.index.search(q, k)
        results: List[Tuple[str, float]] = []
        for dist, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            results.append((self.ids[int(idx)], float(dist)))
        return results


def create(dim: int):
    """Factory used by plugin loader."""
    return FaissIndex(dim)


def available() -> bool:
    return faiss is not None
