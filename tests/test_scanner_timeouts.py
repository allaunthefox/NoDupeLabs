import os
import time

import pytest

from nodupe import scanner


def _make_files(tmpdir, count=6):
    paths = []
    for i in range(count):
        p = tmpdir.join(f"f{i}.txt")
        p.write("x" * 32)
        paths.append(str(p))
    return paths


def test_threaded_hash_times_out_when_no_progress(tmp_path):
    # Create enough files so pending reaches MAX_PENDING for worker=1
    roots = [str(tmp_path)]
    for i in range(6):
        (tmp_path / f"f{i}.txt").write_text("x" * 64)

    # Monkeypatch process_file to sleep (simulate a hung task)
    import threading
    block_event = threading.Event()

    def slow_process_file(p, algo, known_hash=None):
        # Block on an event so the future never completes within the test's short timeouts
        block_event.wait(5)
        # return same shape as original
        st = os.stat(p)
        return (str(p), st.st_size, int(st.st_mtime), "deadbeef", None, None, algo, None)

    orig = scanner.process_file
    scanner.process_file = slow_process_file
    try:
        gen = scanner.threaded_hash(
            roots, ignore=[], workers=1, stall_timeout=0.02, max_idle_time=0.01, show_eta=False)
        with pytest.raises(TimeoutError):
            # consume generator - should raise due to max_idle_time
            list(gen)
    finally:
        scanner.process_file = orig


def test_threaded_hash_prints_stall_and_eta(tmp_path, capsys):
    # Create files
    roots = [str(tmp_path)]
    for i in range(8):
        (tmp_path / f"f{i}.txt").write_text("x" * 64)

    # Simulate some long tasks (the first batch) and some quick ones so we get
    # a stall message and then some completions to allow an ETA to be produced.
    call_count = {"n": 0}

    import threading
    block_event2 = threading.Event()

    def varied_process_file(p, algo, known_hash=None):
        call_count["n"] += 1
        # first few calls are slower
        # make the first several calls slow so the pending pool is fully occupied
        if call_count["n"] <= 5:
            # Block the first several tasks so they don't complete quickly
            block_event2.wait(5)
        else:
            time.sleep(0.01)
        st = os.stat(p)
        return (str(p), st.st_size, int(st.st_mtime), "deadbeef", None, None, algo, None)

    import sys
    import types
    orig = scanner.process_file
    # Prevent the progress bar (tqdm) from being used by the function so we can
    # reliably capture stderr messages produced by the stall/ETA prints.
    tqdm_prev = sys.modules.get('tqdm')
    sys.modules['tqdm'] = types.ModuleType('tqdm')
    scanner.process_file = varied_process_file
    try:
        gen = scanner.threaded_hash(
            roots, ignore=[], workers=1, stall_timeout=0.05, max_idle_time=0.5, show_eta=True)
        # consume a few results but don't trigger overall timeout
        results = []
        for i, rec in enumerate(gen):
            results.append(rec)
            if i >= 5:
                break

        stderr = capsys.readouterr().err
        # We should see at least one stall/ETA line
        assert ("[scanner][STALL]" in stderr) or ("[scanner][ETA]" in stderr)
        assert len(results) >= 1
    finally:
        scanner.process_file = orig
        if tqdm_prev is None:
            del sys.modules['tqdm']
        else:
            sys.modules['tqdm'] = tqdm_prev
