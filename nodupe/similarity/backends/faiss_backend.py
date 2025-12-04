# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""FAISS similarity search backend.

This module provides an interface to the Facebook AI Similarity Search
(FAISS) library. It offers highly optimized vector search capabilities,
suitable for large datasets.

Key Features:
    - High-performance vector search (IndexFlatL2)
    - Efficient persistence (native FAISS format + JSON IDs)
    - Scalable to large vector counts

Classes:
    - FaissIndex: Wrapper around faiss.Index

Functions:
    - create: Factory function
    - available: Check if backend can be used (requires faiss-cpu/gpu)
"""
try:
    import faiss  # type: ignore # pylint: disable=import-error
except Exception:  # pylint: disable=broad-except
    faiss = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None

from typing import List, Optional, Tuple


class FaissIndex:
    def __init__(self, dim: int):
        if not faiss:
            raise RuntimeError("faiss not available")
        if np is None:
            raise RuntimeError("numpy not available")
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.ids: List[str] = []

    def add(
        self, vectors: List[List[float]], ids: Optional[List[str]] = None
    ) -> None:
        arr = np.asarray(vectors, dtype='float32')
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError("Invalid vectors shape")
        self.index.add(arr)
        if ids:
            self.ids.extend(ids)
        else:
            self.ids.extend([
                str(i) for i in range(
                    len(self.ids), len(self.ids) + len(vectors)
                )
            ])

    def search(
        self, vector: List[float], k: int = 5
    ) -> List[Tuple[str, float]]:
        q = np.asarray([vector], dtype='float32')
        D, I_idx = self.index.search(q, k)
        results: List[Tuple[str, float]] = []
        for dist, idx in zip(D[0], I_idx[0]):
            if idx < 0:
                continue
            results.append((self.ids[int(idx)], float(dist)))
        return results

    def save(self, path: str) -> None:
        """
        Persist faiss index and ids to disk.
        Writes binary index to `path` and ids to `path + '.ids.json'`.
        """
        import json
        # write FAISS index
        faiss.write_index(self.index, path)
        # write ids
        with open(path + '.ids.json', 'w', encoding='utf-8') as f:
            json.dump(self.ids, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str):
        """Load a faiss index from disk and return a FaissIndex instance."""
        idx_obj = faiss.read_index(path)
        # determine dim
        dim = idx_obj.d
        inst = cls(dim)
        inst.index = idx_obj
        # load ids
        import json
        try:
            with open(path + '.ids.json', 'r', encoding='utf-8') as f:
                inst.ids = json.load(f)
        except Exception:  # pylint: disable=broad-except
            inst.ids = [str(i) for i in range(int(inst.index.ntotal))]
        return inst


def create(dim: int):
    """Factory used by plugin loader."""
    return FaissIndex(dim)


def available() -> bool:
    return faiss is not None and np is not None
