# Plugin: nsfw_logger
# On scan_complete, run a quick NSFW summary (best-effort, uses NSFWClassifier if available)


def on_scan_complete(records=None, **kwargs):
    try:
        from nodupe.nsfw_classifier import NSFWClassifier
        from nodupe.utils.filesystem import get_mime_safe
        from pathlib import Path
        c = NSFWClassifier(threshold=2)
        # pick up to 20 files to sample classification
        sample = []
        if records:
            for r in records[:20]:
                sample.append((r[0], r[4]))

        res = c.batch_classify([(Path(p), m) for p, m in sample])
        flagged = [p for p, v in res.items() if v['flagged']]
        print(f"[plugins.nsfw_logger] sample flagged: {len(flagged)} / {len(sample)}")
    except Exception as e:
        print(f"[plugins.nsfw_logger] plugin failed gracefully: {e}")

pm.register("scan_complete", on_scan_complete)
