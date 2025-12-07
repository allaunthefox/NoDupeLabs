import time
from pathlib import Path


import nodupe.scanner as scanner


def _fake_process_file_sleep(p, algo, known_hash=None):
    # Simulate expensive hashing for a file
    time.sleep(0.2)
    st = Path(p).stat()
    return (
        str(p), st.st_size, int(st.st_mtime), '0' * 64,
        'application/octet-stream', 'unknown', algo, ''
    )


def test_stalled_tasks_emit_eta(capsys, tmp_path, monkeypatch):
    # Create multiple files so worker queue will build up
    for i in range(12):
        p = tmp_path / f"f{i}.dat"
        p.write_bytes(b"x" * 1024)

    def slow(p, algo, known_hash=None):
        # slower so it's easier to catch
        time.sleep(0.4)
        return _fake_process_file_sleep(p, algo, known_hash)

    monkeypatch.setattr(scanner, 'process_file', slow)

    # Run with small heartbeat to trigger progress warnings
    _ = list(  # noqa: F841
        scanner.threaded_hash(
            [str(tmp_path)], [], workers=1,
            heartbeat_interval=0.02, stalled_timeout=0.1
        )
    )

    out, err = capsys.readouterr()
    combined = out + err
    assert (
        "[scanner][INFO] No progress in" in combined
        or "[scanner][WARN] Task stalled" in combined
    ), "Expected scanner to emit a stalled/ETA message when work stalls"
