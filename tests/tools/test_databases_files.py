import sqlite3
from datetime import datetime

import pytest

from nodupe.tools.databases.files import FileRepository
from nodupe.tools.databases.connection import DatabaseConnection


@pytest.fixture(autouse=True)
def clear_db_instances():
    # Ensure singleton state does not leak between tests
    DatabaseConnection._instances.clear()
    yield
    DatabaseConnection._instances.clear()


def test_batch_add_and_count_and_clear(tmp_path):
    db_path = str(tmp_path / "test_files.db")
    db_conn = DatabaseConnection.get_instance(db_path)
    # ensure full schema (FileRepository expects extended schema)
    from nodupe.tools.databases.schema import DatabaseSchema

    DatabaseSchema(db_conn.get_connection()).create_schema()

    repo = FileRepository(db_conn)

    files = [
        {"path": "/tmp/a.txt", "size": 10, "modified_time": 1, "hash": "h1"},
        {"path": "/tmp/b.txt", "size": 20, "modified_time": 2, "hash": "h2"},
    ]

    added = repo.batch_add_files(files)
    assert added == 2
    assert repo.count_files() == 2

    repo.clear_all_files()
    assert repo.count_files() == 0


def test_add_get_update_mark_and_delete(tmp_path):
    db_path = str(tmp_path / "test_files2.db")
    db_conn = DatabaseConnection.get_instance(db_path)
    # ensure full schema (FileRepository expects extended schema)
    from nodupe.tools.databases.schema import DatabaseSchema

    DatabaseSchema(db_conn.get_connection()).create_schema()
    repo = FileRepository(db_conn)

    fid = repo.add_file("/tmp/x.txt", 123, 999, "abc")
    assert fid is not None and fid > 0

    rec = repo.get_file_by_path("/tmp/x.txt")
    assert rec is not None
    assert rec["path"] == "/tmp/x.txt"

    # update hash
    ok = repo.update_file(rec["id"], hash="def")
    assert ok is True
    updated = repo.get_file(rec["id"])
    assert updated["hash"] == "def"

    # mark duplicate
    fid2 = repo.add_file("/tmp/y.txt", 123, 1000, "def")
    assert repo.mark_as_duplicate(fid2, rec["id"]) is True

    dups = repo.get_duplicate_files()
    assert any(d["id"] == fid2 for d in dups)

    # delete file
    assert repo.delete_file(rec["id"]) is True
    assert repo.get_file(rec["id"]) is None


def test_find_duplicates_by_hash_and_size(tmp_path):
    db_path = str(tmp_path / "test_files3.db")
    db_conn = DatabaseConnection.get_instance(db_path)
    # ensure full schema (FileRepository expects extended schema)
    from nodupe.tools.databases.schema import DatabaseSchema

    DatabaseSchema(db_conn.get_connection()).create_schema()
    repo = FileRepository(db_conn)

    id1 = repo.add_file("/tmp/a.txt", 100, 1000, "samehash")
    id2 = repo.add_file("/tmp/b.txt", 100, 1001, "samehash")
    id3 = repo.add_file("/tmp/c.txt", 200, 1002, "otherhash")

    by_hash = repo.find_duplicates_by_hash("samehash")
    assert len(by_hash) >= 2

    by_size = repo.find_duplicates_by_size(100)
    assert any(r["id"] == id1 for r in by_size)
    assert any(r["id"] == id2 for r in by_size)

    assert repo.count_duplicates() >= 0
