from nodupe.db import DB  # type: ignore # pylint: disable=import-error
# type: ignore # pylint: disable=import-error
from nodupe.similarity import make_index, load_index_from_file, save_index_to_file, update_index_from_db, update_index_file_from_vectors  # noqa: E501
import tempfile
import pytest
try:
    import numpy as np
    has_numpy = True
except ImportError:
    np = None  # type: ignore
    has_numpy = False
from pathlib import Path

pytestmark = pytest.mark.skipif(not has_numpy, reason="numpy not available")


def test_update_npz_index_from_db():
    # Setup DB with two embeddings
    with tempfile.TemporaryDirectory() as td:
        db_file = Path(td) / "test.db"
        db = DB(db_file)

        dim = 4
        db.upsert_embedding("/a.png", [0, 0, 0, 0], dim, 1)
        db.upsert_embedding("/b.png", [1, 1, 1, 1], dim, 1)

        # Create initial index file with one of the embeddings only
        idx = make_index(dim=dim)
        idx.add([[0, 0, 0, 0]], ids=["/a.png"])

        index_path = Path(td) / "nd_index.npz"
        save_index_to_file(idx, str(index_path))

        # Add new embedding to DB
        db.upsert_embedding("/c.png", [0.9, 0.9, 0.9, 0.9], dim, 2)

        # Update index file from DB
        res = update_index_from_db(str(index_path), db)

        # After update, index should contain '/a.png', '/b.png' and '/c.png'
        # (b was in DB too)
        idx2 = load_index_from_file(str(index_path))
        assert res["added"] >= 1
        assert isinstance(idx2.ids, list)
        assert "/c.png" in idx2.ids
        assert "/b.png" in idx2.ids


def test_update_file_vectors_append():
    # Ensure update_index_file_from_vectors appends correctly to .npz
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test_append.npz"
        idx = make_index(dim=4)
        idx.add([[0, 0, 0, 0]], ids=["/a.png"])
        save_index_to_file(idx, str(p))

        # append via function
        update_index_file_from_vectors(str(p), [[1, 1, 1, 1]], ["/b.png"])

        idx2 = load_index_from_file(str(p))
        assert "/a.png" in idx2.ids
        assert "/b.png" in idx2.ids


def test_rebuild_index_removes_stale():
    with tempfile.TemporaryDirectory() as td:
        db_file = Path(td) / "test.db"
        db = DB(db_file)

        dim = 4
        # DB contains a and b
        db.upsert_embedding("/a.png", [0, 0, 0, 0], dim, 1)
        db.upsert_embedding("/b.png", [1, 1, 1, 1], dim, 1)

        # Index file contains a and a stale x
        idx = make_index(dim=dim)
        idx.add([[0, 0, 0, 0], [9, 9, 9, 9]], ids=["/a.png", "/x.png"])
        p = Path(td) / "test_rebuild.npz"
        save_index_to_file(idx, str(p))

        # Rebuild index from DB
        # Rebuild index from DB
        _ = update_index_from_db(str(p), db, remove_missing=True)
        idx2 = load_index_from_file(str(p))
        # stale entry should be removed; db entries should be present
        assert "/x.png" not in idx2.ids
        assert "/a.png" in idx2.ids
        assert "/b.png" in idx2.ids
