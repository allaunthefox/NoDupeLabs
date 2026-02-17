import hashlib
import os

import pytest

from nodupe.tools.hashing.hasher_logic import FileHasher


def test_hash_file_raises_on_missing():
    h = FileHasher()
    with pytest.raises(FileNotFoundError):
        h.hash_file("/nonexistent/does_not_exist.bin")


def test_verify_hash_true_and_false(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")

    h = FileHasher()
    expected = h.hash_file(str(f))
    assert h.verify_hash(str(f), expected) is True
    assert h.verify_hash(str(f), "wronghash") is False


def test_get_available_algorithms_contains_sha256():
    h = FileHasher()
    algos = h.get_available_algorithms()
    assert "sha256" in algos
