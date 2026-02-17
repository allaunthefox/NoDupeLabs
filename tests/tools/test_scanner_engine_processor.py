import os

from nodupe.tools.scanner_engine.processor import FileProcessor


def _make_file(p, content=b"x"):
    p.write_bytes(content)
    return str(p)


def test_batch_process_and_detect_duplicates(tmp_path):
    # create three files, two identical
    p1 = tmp_path / "a.txt"
    p2 = tmp_path / "b.txt"
    p3 = tmp_path / "c.txt"

    _make_file(p1, b"same")
    _make_file(p2, b"same")
    _make_file(p3, b"different")

    processor = FileProcessor()
    results = processor.batch_process_files([str(p1), str(p2), str(p3)])

    # must contain hashes and sizes
    paths = {r["path"]: r for r in results}
    assert str(p1) in paths and str(p2) in paths and str(p3) in paths
    assert paths[str(p1)]["hash"] == paths[str(p2)]["hash"]

    # detect duplicates
    updated = processor.detect_duplicates(results)
    dups = [r for r in updated if r.get("is_duplicate")]
    assert any(r.get("duplicate_of") for r in dups)


def test_set_hash_algorithm_validation():
    processor = FileProcessor()
    import pytest

    with pytest.raises(ValueError):
        processor.set_hash_algorithm("no-such-algo")

    with pytest.raises(ValueError):
        processor.set_hash_buffer_size(0)
