from nodupe.scanner import threaded_hash


def _make_files(tmp_path, count=8, size=1024):
    for i in range(count):
        p = tmp_path / f"file_{i}.bin"
        with p.open("wb") as fh:
            fh.write(b"x" * size)


def test_threaded_hash_with_process_executor(tmp_path):
    _make_files(tmp_path, count=8, size=1024)
    roots = [str(tmp_path)]

    # Use processes explicitly
    results, duration, total = threaded_hash(
        roots, ignore=[], workers=4, executor="process", collect=True
    )
    assert total == 8
    assert len(results) == 8


def test_threaded_hash_with_thread_executor(tmp_path):
    _make_files(tmp_path, count=6, size=512)
    roots = [str(tmp_path)]

    results, duration, total = threaded_hash(
        roots, ignore=[], workers=3, executor="thread", collect=True
    )
    assert total == 6
    assert len(results) == 6
