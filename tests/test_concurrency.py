import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from nodupe.db import DB
from nodupe.logger import JsonlLogger
from nodupe.plugins.manager import PluginManager


def test_db_concurrent_writes_reads(tmp_path):
    db_path = tmp_path / "test.db"
    db = DB(db_path)

    def writer(start, count):
        rows = []
        for i in range(start, start + count):
            # simple deterministic record
            rows.append((
                f"/tmp/f{i}", i * 10, i, f"h{i}",
                "application/octet-stream", "unarchived", "sha512", "0"
            ))
        db.upsert_files(rows)

    # spawn concurrent writers
    workers = 6
    batch = 50
    with ThreadPoolExecutor(max_workers=workers) as ex:
        tasks = [ex.submit(writer, i * batch, batch) for i in range(workers)]
        for t in tasks:
            t.result(timeout=10)

    # Concurrent reader
    with ThreadPoolExecutor(max_workers=3) as rex:
        futures = [rex.submit(list, db.iter_files()) for _ in range(3)]
        results = [f.result(timeout=5) for f in futures]

    # Check that at least one reader saw all records
    all_counts = [len(r) for r in results]
    assert any(c >= workers * batch for c in all_counts)


def test_logger_concurrent_writes_and_rotation(tmp_path):
    logdir = tmp_path / "logs"
    # small rotate size to force rotation during test
    logger = JsonlLogger(logdir, rotate_mb=0)

    def write_many(id_):
        for i in range(200):
            logger.log("INFO", "concurrency_test", worker=id_, i=i)

    threads = [threading.Thread(target=write_many, args=(i,))
               for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Allow any background rotations to complete
    time.sleep(0.5)

    files = sorted(logdir.glob("*.jsonl"))
    assert files, "No log files created"

    # Validate JSON integrity
    total = 0
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                # ensure valid json
                obj = json.loads(line)
                assert obj.get("event") in (
                    "concurrency_test",), "Unexpected event"
                total += 1

    # we expect at least the number of writes
    assert total >= 8 * 200


def test_plugin_manager_concurrent_register_and_emit(tmp_path):
    pm = PluginManager()

    lock = threading.Lock()
    sync_calls = []
    async_calls = []

    # Use events for both sync and async to properly wait
    sync_events = [threading.Event() for _ in range(5)]
    async_events = [threading.Event() for _ in range(5)]

    def make_sync(cb_id, ev: threading.Event):
        def cb(**kwargs):
            with lock:
                sync_calls.append((cb_id, kwargs.get("val")))
            ev.set()

        return cb

    def make_async(cb_id, ev: threading.Event):
        async def cb(**kwargs):
            import asyncio

            await asyncio.sleep(0)
            with lock:
                async_calls.append((cb_id, kwargs.get("val")))
            ev.set()

        return cb

    # Register callbacks - even IDs are sync, odd are async
    for i in range(10):
        if i % 2 == 0:
            pm.register("ev", make_sync(i, sync_events[i // 2]))
        else:
            pm.register("ev", make_async(i, async_events[i // 2]))

    # Emit a single event to trigger all callbacks
    pm.emit("ev", val=42)

    # Wait for sync callbacks (they run in executor)
    for ev in sync_events:
        ev.wait(timeout=5)

    # Wait for async callbacks
    for ev in async_events:
        ev.wait(timeout=5)

    # verify callbacks were called
    assert sync_calls, "No sync callbacks invoked"
    assert async_calls, "No async callbacks invoked"

    # shutdown background loop
    pm.stop()
