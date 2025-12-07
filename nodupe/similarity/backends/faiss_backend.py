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
    """FAISS-based similarity index.

    Uses IndexFlatL2 for exact L2 distance search.
    """

    def __init__(self, dim: int):
        """Initialize FAISS index with given dimension."""
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
        """Add vectors (and optional ids) to the FAISS-backed index.

        Args:
            vectors: Sequence of vectors to add (shape N x dim).
            ids: Optional list of string ids to associate with the stored
                vectors. If omitted, integer-string ids will be assigned.
        """
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
        """Search for k nearest neighbors to a query vector using FAISS.

        Args:
            vector: Query vector (length must match index dim).
            k: Number of neighbors to return.

        Returns:
            List of (id, distance) pairs. Distance semantics follow FAISS
            (squared L2 distance for IndexFlatL2).
        """
        q = np.asarray([vector], dtype='float32')
        D, I_idx = self.index.search(q, k)
        results: List[Tuple[str, float]] = []
        for dist, idx in zip(D[0], I_idx[0]):
            if idx < 0:
                continue
            results.append((self.ids[int(idx)], float(dist)))
        return results

    def save(self, path: str) -> None:
        """Persist the FAISS index and associated ids to disk.

        Args:
            path: File path for the FAISS binary index. The id list is
                written to <path>.ids.json alongside the binary index.
        """
        import json
        # write FAISS index
        faiss.write_index(self.index, path)
        # write ids
        with open(path + '.ids.json', 'w', encoding='utf-8') as f:
            json.dump(self.ids, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str):
        """Load a FAISS index and return a populated FaissIndex instance.

        Args:
            path: Path to the FAISS binary index file. If a sidecar
                <path>.ids.json exists the id list will be loaded from it.

        Returns:
            FaissIndex: Reconstructed index instance.
        """
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
    """Factory used by the plugin loader to create a new FaissIndex.

    Args:
        dim: Vector dimensionality for the index.

    Returns:
        FaissIndex: Initialized index instance.
    """
    return FaissIndex(dim)


def available() -> bool:
    """Return True if the FAISS backend dependencies are importable.

    Returns:
        bool: True when both FAISS and NumPy are available.
    """
    return faiss is not None and np is not None
