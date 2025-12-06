

from nodupe.db import DB


def make_row(i):
    return (
        f"/tmp/r{i}",  # path
        100 + i,  # size
        1600000000 + i,  # mtime
        f"h{i}",  # hash
        "application/octet-stream",
        "unarchived",
        "sha512",
        "0",
    )


def test_db_writer_thread_mode(tmp_path):
    db_path = tmp_path / "db_thread.db"
    db = DB(db_path)

    # enable writer thread
    db.connection.start_writer(mode="thread", batch_size=2)

    records = [make_row(i) for i in range(6)]

    # issue many upserts (these should enqueue)
    for r in records:
        db.upsert_files([r])

    # allow background worker to run
    db.connection.stop_writer(flush=True, timeout=10.0)

    rows = list(db.iter_files())
    assert len(rows) >= 6
    db.close()


def test_db_writer_process_mode(tmp_path):
    db_path = tmp_path / "db_proc.db"
    db = DB(db_path)

    db.connection.start_writer(mode="process", batch_size=3)

    records = [make_row(i) for i in range(9)]
    for r in records:
        db.upsert_files([r])

    # Stop and flush
    db.connection.stop_writer(flush=True, timeout=10.0)

    rows = list(db.iter_files())
    assert len(rows) >= 9

    db.close()


def test_db_writer_constructor_arg(tmp_path):
    db_path = tmp_path / "db_ctor.db"
    # Pass writer_mode in constructor
    db = DB(db_path, writer_mode="thread", writer_batch_size=2)
    records = [make_row(i) for i in range(4)]
    for r in records:
        db.upsert_files([r])

    db.connection.stop_writer(flush=True, timeout=5.0)
    assert len(list(db.iter_files())) >= 4
    db.close()


def test_db_writer_env_opt_in(tmp_path, monkeypatch):
    db_path = tmp_path / "db_env.db"
    monkeypatch.setenv("NODUPE_DB_WRITER_MODE", "thread")
    monkeypatch.setenv("NODUPE_DB_WRITER_BATCH", "3")

    db = DB(db_path)
    records = [make_row(i) for i in range(5)]
    for r in records:
        db.upsert_files([r])

    db.connection.stop_writer(flush=True, timeout=5.0)
    rows = list(db.iter_files())
    assert len(rows) >= 5
    db.close()
