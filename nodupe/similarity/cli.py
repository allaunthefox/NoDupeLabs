# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from pathlib import Path
from typing import List
from .index import make_index
from ..ai.backends import choose_backend
from ..db import DB


def build_index_from_db(db_path: Path, dim: int = 16) -> dict:
    db = DB(db_path)
    rows = db.get_all()
    # rows: path, size, mtime, file_hash, mime, context_tag, hash_algo, permissions
    items = [r for r in rows if r[4] and r[4].startswith('image/')]

    be = choose_backend()
    idx = make_index(dim)

    vectors = []
    ids = []
    for r in items:
        p = Path(r[0])
        try:
            vec = be.compute_embedding(p, dim=dim)
            vectors.append(vec)
            ids.append(r[0])
        except Exception:
            # skip
            continue

    idx.add(vectors, ids=ids)
    return {"index_count": len(ids)}


def find_near_duplicates(db_path: Path, target: Path, k: int = 5, dim: int = 16) -> List[tuple]:
    be = choose_backend()
    vec = be.compute_embedding(target, dim=dim)
    idx = make_index(dim)

    # Build from DB (in-memory) — for production you'd persist this
    db = DB(db_path)
    rows = db.get_all()
    items = [r for r in rows if r[4] and r[4].startswith('image/')]

    vectors = []
    ids = []
    for r in items:
        p = Path(r[0])
        try:
            v = be.compute_embedding(p, dim=dim)
            vectors.append(v)
            ids.append(r[0])
        except Exception:
            continue

    idx.add(vectors, ids=ids)
    res = idx.search(vec, k=k)
    # return list of (path, score)
    return res
