# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Brute-force similarity search backend.

This module implements a simple, exact nearest neighbor search using
NumPy. It calculates Euclidean distances between the query vector and
all indexed vectors. While not scalable to millions of items, it is
accurate and requires no complex dependencies beyond NumPy.

Key Features:
    - Exact nearest neighbor search (L2 distance)
    - Full persistence support (.npz, .json, .jsonl)
    - No external C++ dependencies (unlike FAISS)

Classes:
    - BruteForceIndex: In-memory index implementation

Functions:
    - create: Factory function
    - available: Check if backend can be used (requires numpy)
    - load/save: Persistence helpers
"""
try:
    import numpy as np
except ImportError:
    np = None

from typing import List, Optional, Tuple
from pathlib import Path
import json


class BruteForceIndex:
    """In-memory brute-force similarity index.

    Stores vectors and IDs, performs exact L2 nearest neighbor search.

    Attributes:
        dim: Dimension of vectors
        vectors: NumPy array of stored vectors
        ids: List of string IDs corresponding to vectors
    """

    def __init__(self, dim: int):
        """Initialize index with given dimension."""
        if np is None:
            raise ImportError("numpy is required for BruteForceIndex")
        self.dim = dim
        self.vectors = np.zeros((0, dim), dtype='float32')
        self.ids: List[str] = []

    def add(
        self, vectors: List[List[float]], ids: Optional[List[str]] = None
    ) -> None:
        """Add vectors to the index."""
        arr = np.asarray(vectors, dtype='float32')
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError("Invalid vectors shape for brute-force")
        if self.vectors.size:
            self.vectors = np.vstack([self.vectors, arr])
        else:
            self.vectors = arr
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
        """Search for k nearest neighbors."""
        if self.vectors.size == 0:
            return []
        q = np.asarray(vector, dtype='float32')
        dif = self.vectors - q
        dists = np.sum(dif * dif, axis=1)
        idxs = np.argsort(dists)[:k]
        return [
            (self.ids[int(i)], float(dists[int(i)])) for i in idxs
        ]


def create(dim: int):
    """Create a new brute-force index with given dimension."""
    return BruteForceIndex(dim)


def available() -> bool:
    """Check if numpy is available for brute-force backend."""
    return np is not None


# Persistence helpers
def load(path: str):
    """Load index from file (.npz, .json, or .jsonl)."""
    # Support multiple persistence formats: .npz, .json, .jsonl
    p = Path(path)
    ext = p.suffix.lower()
    if ext == '.npz':
        npz = np.load(path, allow_pickle=True)
        vectors = npz['vectors']
        ids = npz['ids'].tolist() if 'ids' in npz else [
            str(i) for i in range(vectors.shape[0])
        ]
        dim = vectors.shape[1]
    elif ext == '.json':
        # Strict JSON format validation
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        # Required keys
        if not isinstance(data, dict):
            raise RuntimeError('JSON index must be an object')
        if data.get('format') != 'nodupe.similarity.index':
            raise RuntimeError('JSON index missing required "format" field')
        if 'dim' not in data or 'ids' not in data or 'vectors' not in data:
            raise RuntimeError(
                'JSON index missing required keys (dim, ids, vectors)'
            )
        dim = int(data['dim'])
        ids = data['ids']
        vectors = np.asarray(data['vectors'], dtype='float32')
        # Validate shapes
        if not isinstance(ids, list) or not all(
            isinstance(i, str) for i in ids
        ):
            raise RuntimeError('JSON index "ids" must be a list of strings')
        if vectors.size and vectors.shape[1] != dim:
            raise RuntimeError('JSON index vectors dimension mismatch')
        if len(ids) != vectors.shape[0]:
            raise RuntimeError('JSON index ids and vectors length mismatch')
    elif ext == '.jsonl':
        rows = []
        ids = []
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                if not line.strip():
                    continue
                obj = json.loads(line)
                # strict record validation
                if not isinstance(obj, dict):
                    raise RuntimeError(
                        'JSONL index records must be JSON objects'
                    )
                if 'id' not in obj or 'vector' not in obj:
                    raise RuntimeError(
                        'JSONL record missing required fields (id, vector)'
                    )
                if not isinstance(obj['id'], str):
                    raise RuntimeError('JSONL record id must be a string')
                if not isinstance(obj['vector'], list):
                    raise RuntimeError('JSONL record vector must be a list')
                ids.append(obj.get('id'))
                rows.append(obj.get('vector'))
        vectors = np.asarray(rows, dtype='float32') if rows else np.zeros(
            (0, 0), dtype='float32'
        )
        dim = vectors.shape[1] if vectors.size else 0
    else:
        raise RuntimeError('Unsupported format for bruteforce index: ' + ext)
    inst = BruteForceIndex(dim)
    inst.vectors = vectors.astype('float32')
    inst.ids = ids
    return inst


def save(index_obj, path: str):
    """Save index to file (.npz, .json, or .jsonl)."""
    # assume index_obj has attributes vectors and ids
    p = Path(path)
    ext = p.suffix.lower()
    if ext == '.npz':
        np.savez_compressed(
            path, vectors=np.asarray(index_obj.vectors),
            ids=np.asarray(index_obj.ids, dtype=object)
        )
        return

    if ext == '.json':
        # Write a portable, schema-compatible JSON object
        data = {
            'format': 'nodupe.similarity.index',
            'format_version': '1.0',
            'dim': int(getattr(index_obj, 'dim', 0)),
            'ids': list(getattr(index_obj, 'ids', [])),
            'vectors': np.asarray(
                getattr(index_obj, 'vectors', [])
            ).astype('float64').tolist(),
        }
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        return

    if ext == '.jsonl':
        vectors = np.asarray(getattr(index_obj, 'vectors', []))
        ids = list(getattr(index_obj, 'ids', []))
        with open(path, 'w', encoding='utf-8') as fh:
            for i, v in enumerate(vectors):
                entry = {
                    'id': ids[i] if i < len(ids) else str(i),
                    'vector': np.asarray(v).astype('float64').tolist(),
                }
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return

    raise RuntimeError('Unsupported format for bruteforce index save: ' + ext)
