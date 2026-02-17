import os
from unittest.mock import Mock

import pytest

from nodupe.tools.scanner_engine.processor import (
    FileProcessor,
    _get_default_hasher,
)
from nodupe.core.container import container as global_container


class DummyHasher:
    def __init__(self, rv="deadbeef"):
        self._rv = rv

    def hash_file(self, path):
        return self._rv

    def set_algorithm(self, algo):
        self._algo = algo


class FakeWalker:
    def __init__(self, files):
        self._files = files

    def walk(self, root_path, file_filter=None, on_progress=None):
        return self._files


def test_get_default_hasher_prefers_container(monkeypatch):
    dummy = DummyHasher("from_container")
    global_container.register_service("hasher_service", dummy)

    hasher = _get_default_hasher()
    assert hasher is dummy

    # cleanup
    global_container.services.pop("hasher_service", None)


def test_process_files_and_detect_duplicates(tmp_path):
    # create fake files
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("one")
    f2.write_text("two")

    files = [
        {"path": str(f1), "size": f1.stat().st_size},
        {"path": str(f2), "size": f2.stat().st_size},
    ]

    # hasher returns same hash for both to force duplicates
    hasher = DummyHasher("dup-hash")
    walker = FakeWalker(files)
    proc = FileProcessor(file_walker=walker, hasher=hasher)

    processed = proc.process_files(str(tmp_path))
    assert len(processed) == 2
    # mark duplicates
    updated = proc.detect_duplicates(processed)

    # one should be marked duplicate_of the other
    dups = [f for f in updated if f.get("is_duplicate")]
    assert len(dups) == 1
    assert dups[0]["duplicate_of"] in (str(f1), str(f2))


def test_batch_process_files_skips_non_files(tmp_path):
    f = tmp_path / "only.txt"
    f.write_text("x")

    proc = FileProcessor()
    res = proc.batch_process_files([str(f), str(tmp_path / "nope.txt")])

    assert any(r["path"] == str(f) for r in res)


def test_set_hash_algorithm_and_buffer_validation_in_processor():
    proc = FileProcessor(hasher=DummyHasher())

    with pytest.raises(ValueError):
        proc.set_hash_algorithm("not-an-algo")

    with pytest.raises(ValueError):
        proc.set_hash_buffer_size(0)
