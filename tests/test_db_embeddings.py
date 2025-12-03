import tempfile
from pathlib import Path
from nodupe.db import DB


def test_db_embedding_upsert_and_get():
    with tempfile.TemporaryDirectory() as td:
        dbpath = Path(td) / 'test.db'
        db = DB(dbpath)
        vec = [0.1, 0.2, 0.3]
        db.upsert_embedding('a/b/c.jpg', vec, dim=3, mtime=123456)
        got = db.get_embedding('a/b/c.jpg')
        assert got is not None
        assert got['dim'] == 3
        assert isinstance(got['vector'], list)
        assert got['mtime'] == 123456
        all_emb = db.get_all_embeddings()
        assert len(all_emb) == 1
