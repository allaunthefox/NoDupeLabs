import threading
from nodupe.logger import JsonlLogger


def test_logger_queue_concurrent_writes_and_rotation(tmp_path):
    logdir = tmp_path / "qlogs"
    # small rotate size to force rotation during test
    logger = JsonlLogger(logdir, rotate_mb=0.1, use_queue=True)

    def write_many(id_):
        for i in range(200):
            logger.log("INFO", "concurrency_test", worker=id_, i=i)

    threads = [threading.Thread(target=write_many, args=(i,))
               for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # allow the writer to flush
    logger.stop(flush=True, timeout=10.0)

    files = sorted(logdir.glob("*.jsonl"))
    assert files, "No log files created"

    total = 0
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total += 1

    assert total >= 8 * 200
