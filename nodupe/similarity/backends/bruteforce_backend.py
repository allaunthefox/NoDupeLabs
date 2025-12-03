# SPDX-License-Identifier: Apache-2.0
try:
    import numpy as np
except ImportError:
    np = None

from typing import List, Optional, Tuple


class BruteForceIndex:
    def __init__(self, dim: int):
        if np is None:
            raise ImportError("numpy is required for BruteForceIndex")
        self.dim = dim
        self.vectors = np.zeros((0, dim), dtype='float32')
        self.ids: List[str] = []

    def add(self, vectors: List[List[float]], ids: Optional[List[str]] = None) -> None:
        arr = np.asarray(vectors, dtype='float32')
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError("Invalid vectors shape for brute-force")
        self.vectors = np.vstack([self.vectors, arr]) if self.vectors.size else arr
        if ids:
            self.ids.extend(ids)
        else:
            self.ids.extend([str(i) for i in range(len(self.ids), len(self.ids) + len(vectors))])

    def search(self, vector: List[float], k: int = 5) -> List[Tuple[str, float]]:
        if self.vectors.size == 0:
            return []
        q = np.asarray(vector, dtype='float32')
        dif = self.vectors - q
        dists = np.sum(dif * dif, axis=1)
        idxs = np.argsort(dists)[:k]
        return [(self.ids[int(i)], float(dists[int(i)])) for i in idxs]


def create(dim: int):
    return BruteForceIndex(dim)


def available() -> bool:
    return np is not None


# Persistence helpers
def load(path: str):
    npz = np.load(path, allow_pickle=True)
    vectors = npz['vectors']
    ids = npz['ids'].tolist() if 'ids' in npz else [str(i) for i in range(vectors.shape[0])]
    dim = vectors.shape[1]
    inst = BruteForceIndex(dim)
    inst.vectors = vectors.astype('float32')
    inst.ids = ids
    return inst


def save(index_obj, path: str):
    # assume index_obj has attributes vectors and ids
    np.savez_compressed(path, vectors=np.asarray(index_obj.vectors), ids=np.asarray(index_obj.ids, dtype=object))
