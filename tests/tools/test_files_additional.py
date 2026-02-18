# SPDX-License-Identifier: Apache-2.0
"""Additional unit tests for FileRepository behaviors.
"""
from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.files import FileRepository


def _make_repo():
    db = DatabaseConnection.get_instance(":memory:")
    db.initialize_database()
    repo = FileRepository(db)
    repo.clear_all_files()
    return repo


def test_batch_add_and_get_all_files():
    repo = _make_repo()
    files = [
        {"path": "/tmp/a.txt", "size": 10, "modified_time": 1},
        {"path": "/tmp/b.txt", "size": 20, "modified_time": 2},
    ]
    added = repo.batch_add_files(files)
    assert added == 2

    all_files = repo.get_all_files()
    paths = [f['path'] for f in all_files]
    assert "/tmp/a.txt" in paths and "/tmp/b.txt" in paths


def test_clear_all_files_and_count():
    repo = _make_repo()
    repo.add_file("/tmp/x.txt", size=5, modified_time=1)
    assert repo.count_files() >= 1
    repo.clear_all_files()
    assert repo.count_files() == 0


def test_mark_as_duplicate_and_original():
    repo = _make_repo()
    a = repo.add_file("/tmp/a.txt", size=1, modified_time=1, hash_value="h1")
    b = repo.add_file("/tmp/b.txt", size=1, modified_time=2, hash_value="h1")

    assert repo.mark_as_duplicate(b, a) is True
    fb = repo.get_file(b)
    assert fb['is_duplicate'] is True and fb['duplicate_of'] == a

    assert repo.mark_as_original(a) is True
    fa = repo.get_file(a)
    assert fa['is_duplicate'] is False and fa['duplicate_of'] is None
