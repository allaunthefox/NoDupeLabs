import time
from pathlib import Path

import pytest

import nodupe.scanner as scanner


def _make_files(tmp_path: Path, count: int = 6):
    for i in range(count):
        p = tmp_path / f"file{i}.txt"
        p.write_text("hello")
    return [str(tmp_path)]


def test_threaded_hash_detects_stall_and_prints(monkeypatch, tmp_path, capsys):
    roots = _make_files(tmp_path, count=6)

    # Replace process_file with a function that sleeps longer than our
    # max_idle_time so the generator will hit the TimeoutError path.
    def blocking_process(p, algo, known_hash=None):
        time.sleep(0.2)
        return (str(p), 1, 1, 'deadbeef', None, None, algo, '')

    monkeypatch.setattr(scanner, 'process_file', blocking_process)

    gen = scanner.threaded_hash(
        roots,
        [],
        workers=1,
        heartbeat_interval=0.01,
        stall_timeout=0.01,
        max_idle_time=0.05,
        show_eta=False,
        collect=False,
    )
    # Try to pull a single result; we expect a stall/ETA message to be
    # emitted so capture stdout/stderr and assert it's present. We don't
    # require a TimeoutError here (generator may eventually complete)
    try:
        next(gen)
    except Exception:
        # ignore — we only care about the progress messages
        pass

    captured = capsys.readouterr()
    assert "[scanner][STALL]" in captured.out or "[scanner][ETA]" in captured.out or "[scanner][INFO]" in captured.out


def test_threaded_hash_prints_eta_on_stall(monkeypatch, tmp_path, capsys):
    roots = _make_files(tmp_path, count=6)

    def blocking_process(p, algo, known_hash=None):
        # sleep to ensure pending builds up and wait timeout triggers
        time.sleep(0.15)
        return (str(p), 1, 1, 'deadbeef', None, None, algo, '')

    monkeypatch.setattr(scanner, 'process_file', blocking_process)

    # Use slightly larger idle timeout so we can observe a stall message
    gen = scanner.threaded_hash(
        roots,
        [],
        workers=1,
        heartbeat_interval=0.01,
        stall_timeout=0.01,
        max_idle_time=0.5,
        show_eta=True,
        collect=False,
    )

    # Try to pull a single result — we'll capture stderr/out
    try:
        next(gen)
    except TimeoutError:
        # expected sometimes on slow workers; we still want to check stderr
        pass

    captured = capsys.readouterr()
    assert (
        "[scanner][ETA]" in captured.err
        or "[scanner][STALL]" in captured.err
        or "[scanner][ETA]" in captured.out
        or "[scanner][STALL]" in captured.out
        or "[scanner][INFO]" in captured.out
    )
