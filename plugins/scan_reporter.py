# Plugin: scan_reporter
# Reports basic scan lifecycle events and metrics

def on_scan_start(roots, db=None, **kwargs):
    print(f"[plugins.scan_reporter] Scan starting on: {roots}")


def on_scan_complete(records=None, duration=None, metrics=None, **kwargs):
    n = len(records) if records is not None else 0
    print(f"[plugins.scan_reporter] Scan complete: {n} records, duration={duration:.3f}s")
    try:
        # print a short metrics summary if present
        if metrics is not None and hasattr(metrics, 'data'):
            print(f"[plugins.scan_reporter] metrics: files_scanned={metrics.data.get('files_scanned')}, bytes={metrics.data.get('bytes_scanned')}")
    except Exception:
        pass

pm.register("scan_start", on_scan_start)
pm.register("scan_complete", on_scan_complete)
