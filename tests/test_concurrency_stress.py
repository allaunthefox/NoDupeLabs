import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from nodupe.db import DB
from nodupe.plugins.manager import PluginManager


@pytest.mark.slow
def test_db_stress_concurrent_writes_reads(tmp_path):
    """Stress test DB with concurrent writers and readers.

    This test simulates many threads concurrently writing batches of
    records and readers iterating over the DB while writes are ongoing.
    """
    db_path = tmp_path / "stress.db"
    db = DB(db_path)

    WRITERS = 30
    BATCH = 200

    def writer_thread(idx):
        for b in range(BATCH):
            base = idx * WRITERS * BATCH + b
            rows = [
                (f"/tmp/stf{base+i}", (base + i) * 10, base + i, f"h{base+i}", "application/octet-stream", "unarchived", "sha512", "0")
                for i in range(5)
            ]
            db.upsert_files(rows)

    with ThreadPoolExecutor(max_workers=WRITERS) as ex:
        futures = [ex.submit(writer_thread, i) for i in range(WRITERS)]
        # Also spawn some readers while writes are active
        reader_futures = []
        def reader():
            # do a few reads
            for _ in range(50):
                list(db.iter_files())
                time.sleep(0.01)

        with ThreadPoolExecutor(max_workers=10) as rex:
            reader_futures = [rex.submit(reader) for _ in range(10)]

        # Wait for writers to finish
        for f in futures:
            f.result(timeout=120)

        for r in reader_futures:
            r.result(timeout=60)

    # Basic sanity: ensure DB has some rows
    rows = list(db.iter_files())
    assert len(rows) > 0


@pytest.mark.slow
def test_plugin_async_dispatch_stress():
    """Stress test plugin manager with many async callbacks and emits."""
    pm = PluginManager()

    CALLERS = 60
    PER_CALL = 200

    # register many async callbacks
    events = [threading.Event() for _ in range(CALLERS)]

    for i in range(CALLERS):
        ev = events[i]

        async def cb(i=i, ev=ev, **kwargs):
            # short non-blocking work
            await __import__('asyncio').sleep(0)
            ev.set()

        pm.register('stress_ev', cb)

    # Emit from multiple threads concurrently
    def emitter(n):
        for _ in range(n):
            pm.emit('stress_ev', val=_) 

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(emitter, PER_CALL) for _ in range(12)]
        for f in futures:
            f.result(timeout=120)

    # Ensure at least some callbacks executed (events set)
    assert any(e.is_set() for e in events)
    pm.stop()
