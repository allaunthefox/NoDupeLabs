import time


from nodupe.plugins.manager import PluginManager


def test_plugin_manager_executor_bounding_and_metrics():
    pm = PluginManager()

    # Start with a small executor so we can reliably saturate it
    pm.set_executor_max_workers(3)

    RUNS = 8
    SLEEP_SECS = 0.15

    # register a blocking (sync) callback
    def slow_cb(**_):
        # blocking work to occupy an executor thread
        time.sleep(SLEEP_SECS)

    pm.register("bounded_ev", slow_cb)

    # quickly schedule a bunch of blocking tasks
    for _ in range(RUNS):
        pm.emit("bounded_ev")

    # Ensure bookkeeping recorded the scheduled tasks
    m = pm.metrics()
    assert m.get("executor_max_workers") == 3
    assert m.get("scheduled") == RUNS

    # Wait a little so some tasks have a chance to start and verify
    # running <= max
    saw_running = False
    for _ in range(20):
        m = pm.metrics()
        if m.get("running", 0) > 0:
            saw_running = True
            assert m["running"] <= m["executor_max_workers"]
            # when we've scheduled more than the allowed workers we expect
            # there to be items pending in the queue.
            if RUNS > m["executor_max_workers"]:
                assert m["pending"] >= RUNS - m["executor_max_workers"]
            break
        time.sleep(0.01)

    # We should have observed work being executed
    assert saw_running

    # Wait until work completes (or timeout) and then validate counts
    deadline = time.time() + 5.0
    while time.time() < deadline:
        m = pm.metrics()
        if m.get("completed") == m.get("scheduled"):
            break
        time.sleep(0.02)

    m = pm.metrics()
    assert m.get("completed") == RUNS
    assert m.get("failed") == 0
    assert m.get("pending") == 0
    assert m.get("running") == 0

    pm.stop()


def test_plugin_manager_metrics_failure_count():
    pm = PluginManager()

    # failing callback
    def bad_cb(**_):
        raise RuntimeError("boom")

    pm.register("bad_ev", bad_cb)
    pm.emit("bad_ev")

    # Wait until the scheduler processed the item
    deadline = time.time() + 2.0
    while time.time() < deadline:
        m = pm.metrics()
        if m.get("scheduled", 0) >= 1 and m.get("pending", 0) == 0:
            break
        time.sleep(0.01)

    m = pm.metrics()
    assert m.get("scheduled") >= 1
    # verify the failed count incremented
    assert m.get("failed") >= 1

    pm.stop()
