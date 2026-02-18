import hashlib

from nodupe.tools.hashing.hasher_logic import FileHasher


def test_hash_string_and_bytes_consistency():
    h = FileHasher()
    s = "hello world"
    assert h.hash_string(s) == h.hash_bytes(s.encode())


def test_hash_file_and_progress_callback(tmp_path):
    content = b"abc123" * 100
    f = tmp_path / "data.bin"
    f.write_bytes(content)

    h = FileHasher()
    events = []

    def on_progress(p):
        events.append(p)

    got = h.hash_file(str(f), on_progress=on_progress)
    expected = hashlib.new(h.get_algorithm())
    expected.update(content)
    assert got == expected.hexdigest()
    # progress should have been reported and final percent_complete should be ~100
    assert any((e.get("percent_complete", 0) >= 99.9) for e in events)


def test_hash_files_skips_missing(tmp_path):
    f1 = tmp_path / "one.txt"
    f1.write_text("x")
    f2 = tmp_path / "missing.txt"

    h = FileHasher()
    res = h.hash_files([str(f1), str(f2)])
    assert str(f1) in res
    assert str(f2) not in res


def test_set_algorithm_and_buffer_validation():
    h = FileHasher()
    # invalid algorithm
    try:
        h.set_algorithm("sha256")
    except Exception:
        pytest.skip("platform does not support sha256")

    import pytest as _pytest

    with _pytest.raises(ValueError):
        h.set_algorithm("not_an_algo")

    with _pytest.raises(ValueError):
        h.set_buffer_size(0)
